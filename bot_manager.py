import os
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime
from collections import deque
from pathlib import Path


def _env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except Exception:
        return default


def _timestamp_iso(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.utcfromtimestamp(float(value)).replace(microsecond=0).isoformat() + "Z"
    return value


class BotManager:
    def __init__(self, script_path):
        self.script_path = Path(script_path).resolve()
        self.workdir = str(self.script_path.parent)
        self.lock = threading.RLock()
        self.thread = None
        self.stop_event = threading.Event()
        self.run_requested = threading.Event()
        self.process = None
        self.output_tail = deque(maxlen=40)
        self.recent_runs = deque(maxlen=12)
        self.enabled_override = None
        self.loop_interval_override_seconds = None
        self.next_trigger_kind = "startup"
        self.state = {
            "enabled": self._autostart_enabled(),
            "status": "disabled",
            "message": "Bot runner has not started yet.",
            "current_pid": None,
            "last_run_started_at": None,
            "last_run_finished_at": None,
            "last_duration_seconds": None,
            "last_exit_code": None,
            "last_run_emails_sent": 0,
            "last_error": None,
            "next_run_at": None,
            "loop_interval_seconds": self._loop_interval_seconds(),
            "run_timeout_seconds": self._run_timeout_seconds(),
            "command": [],
            "consecutive_failures": 0,
            "output_tail": [],
            "manual_run_available": True,
            "recent_runs": [],
            "schedule_source": "env",
            "paused": not self._autostart_enabled(),
        }

    def _autostart_enabled(self):
        if self.enabled_override is not None:
            return bool(self.enabled_override)
        return _env_bool("BOT_AUTOSTART", default=bool(os.getenv("PORT")))

    def _loop_interval_seconds(self):
        if self.loop_interval_override_seconds is not None:
            return max(60, int(self.loop_interval_override_seconds))
        return max(60, _env_int("BOT_LOOP_INTERVAL_SECONDS", 900))

    def _run_timeout_seconds(self):
        return max(300, _env_int("BOT_RUN_TIMEOUT_SECONDS", 3600))

    def _default_args(self):
        args = ["--audit", "--session-queries", os.getenv("BOT_SESSION_QUERIES", "1")]
        if os.getenv("BOT_QUERY"):
            args.extend(["--query", os.getenv("BOT_QUERY")])
            return args
        if os.getenv("BOT_NICHES"):
            args.extend(["--niches", os.getenv("BOT_NICHES")])
        elif os.getenv("BOT_NICHE"):
            args.extend(["--niche", os.getenv("BOT_NICHE")])
        if os.getenv("BOT_LOCATIONS"):
            args.extend(["--locations", os.getenv("BOT_LOCATIONS")])
        elif os.getenv("BOT_LOCATION"):
            args.extend(["--location", os.getenv("BOT_LOCATION")])
        if _env_bool("BOT_BATCH", default=False):
            args.append("--batch")
        if _env_bool("BOT_SIGNALS", default=False):
            args.append("--signals")
        if _env_bool("BOT_LINKEDIN", default=False):
            args.append("--linkedin")
        if os.getenv("BOT_ROLE"):
            args.extend(["--role", os.getenv("BOT_ROLE")])
        return args

    def _build_command(self):
        custom_args = os.getenv("BOT_ARGS")
        args = shlex.split(custom_args) if custom_args else self._default_args()
        return [sys.executable, str(self.script_path.name), *args]

    def _sent_total(self):
        try:
            from database import DataManager

            dm = DataManager()
            stats = dm.get_persona_performance()
            return int(stats.get("sent", 0) or 0)
        except Exception:
            return 0

    def _update_state(self, **updates):
        with self.lock:
            normalized_updates = {}
            for key, value in updates.items():
                if key.endswith("_at"):
                    normalized_updates[key] = _timestamp_iso(value)
                else:
                    normalized_updates[key] = value
            self.state.update(normalized_updates)
            self.state["enabled"] = self._autostart_enabled()
            self.state["loop_interval_seconds"] = self._loop_interval_seconds()
            self.state["run_timeout_seconds"] = self._run_timeout_seconds()
            self.state["output_tail"] = list(self.output_tail)
            self.state["recent_runs"] = list(self.recent_runs)
            self.state["schedule_source"] = "override" if self.loop_interval_override_seconds is not None or self.enabled_override is not None else "env"
            self.state["paused"] = not self._autostart_enabled()

    def snapshot(self):
        with self.lock:
            snapshot = dict(self.state)
            snapshot["output_tail"] = list(self.output_tail)
            snapshot["enabled"] = self._autostart_enabled()
            snapshot["loop_interval_seconds"] = self._loop_interval_seconds()
            snapshot["run_timeout_seconds"] = self._run_timeout_seconds()
            snapshot["recent_runs"] = list(self.recent_runs)
            snapshot["schedule_source"] = "override" if self.loop_interval_override_seconds is not None or self.enabled_override is not None else "env"
            snapshot["paused"] = not self._autostart_enabled()
            return snapshot

    def start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                return
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._loop, name="bot-manager", daemon=True)
            self.thread.start()

    def pause(self):
        self.enabled_override = False
        with self.lock:
            status = self.state.get("status")
        if status == "running":
            self._update_state(
                message="Pause requested. Current bot session will finish, then the runner will stay paused.",
                next_run_at=None,
            )
        else:
            self._update_state(
                status="disabled",
                message="Bot autostart has been paused from the dashboard.",
                next_run_at=None,
            )
        return {
            "accepted": True,
            "status": self.snapshot().get("status"),
            "message": "Bot autostart paused.",
            "snapshot": self.snapshot(),
        }

    def resume(self):
        self.enabled_override = True
        self.start()
        self.run_requested.set()
        self.next_trigger_kind = "manual"
        self._update_state(
            status="queued",
            message="Bot autostart resumed and a run has been queued.",
            next_run_at=time.time(),
        )
        return {
            "accepted": True,
            "status": "queued",
            "message": "Bot autostart resumed.",
            "snapshot": self.snapshot(),
        }

    def set_loop_interval(self, seconds):
        try:
            seconds = int(seconds)
        except Exception:
            seconds = self._loop_interval_seconds()
        seconds = max(60, seconds)
        self.loop_interval_override_seconds = seconds
        next_run = time.time() + seconds if self.snapshot().get("status") == "sleeping" and self._autostart_enabled() else self.snapshot().get("next_run_at")
        self._update_state(
            loop_interval_seconds=seconds,
            next_run_at=next_run,
            message=f"Bot schedule updated to run every {seconds} seconds.",
        )
        return {
            "accepted": True,
            "status": self.snapshot().get("status"),
            "message": f"Bot interval updated to {seconds} seconds.",
            "snapshot": self.snapshot(),
        }

    def stop(self):
        self.stop_event.set()
        self.run_requested.set()
        with self.lock:
            proc = self.process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def request_run_now(self):
        self.start()
        with self.lock:
            status = self.state.get("status")
            if status == "running":
                return {
                    "accepted": False,
                    "status": status,
                    "message": "Bot run is already in progress.",
                    "snapshot": self.snapshot(),
                }
        self.run_requested.set()
        self.next_trigger_kind = "manual"
        self._update_state(
            status="queued",
            message="Manual bot run requested.",
            next_run_at=time.time(),
        )
        return {
            "accepted": True,
            "status": "queued",
            "message": "Manual bot run has been queued.",
            "snapshot": self.snapshot(),
        }

    def _pump_output(self, stream):
        if stream is None:
            return
        try:
            for line in iter(stream.readline, ""):
                text = str(line).rstrip()
                if text:
                    self.output_tail.append(text)
        except Exception:
            return

    def _record_run(self, trigger_kind, started_at, finished_at, duration, exit_code, sent_delta, status, error=None):
        output_tail = list(self.output_tail)[-8:]
        run = {
            "trigger": trigger_kind,
            "started_at": _timestamp_iso(started_at),
            "finished_at": _timestamp_iso(finished_at),
            "duration_seconds": duration,
            "exit_code": exit_code,
            "emails_sent": sent_delta,
            "status": status,
            "error": error,
            "output_tail": output_tail,
        }
        self.recent_runs.appendleft(run)
        return run

    def _run_once(self):
        command = self._build_command()
        timeout_seconds = self._run_timeout_seconds()
        sent_before = self._sent_total()
        started_at = time.time()
        trigger_kind = self.next_trigger_kind or "scheduled"
        self.next_trigger_kind = "scheduled"

        self.output_tail.clear()
        self._update_state(
            status="running",
            message=f"Bot session is running ({trigger_kind}).",
            current_pid=None,
            last_run_started_at=started_at,
            last_error=None,
            command=command,
            next_run_at=None,
        )

        proc = subprocess.Popen(
            command,
            cwd=self.workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self.process = proc
        self._update_state(current_pid=proc.pid)
        reader = threading.Thread(target=self._pump_output, args=(proc.stdout,), daemon=True)
        reader.start()

        timed_out = False
        exit_code = None
        try:
            exit_code = proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                proc.kill()
            except Exception:
                pass
            exit_code = proc.poll()
        finally:
            try:
                if proc.stdout:
                    proc.stdout.close()
            except Exception:
                pass
            self.process = None

        finished_at = time.time()
        sent_after = self._sent_total()
        sent_delta = max(0, sent_after - sent_before)
        duration = max(0, int(finished_at - started_at))

        if timed_out:
            self._record_run(
                trigger_kind,
                started_at,
                finished_at,
                duration,
                exit_code,
                sent_delta,
                "error",
                error=f"Timed out after {timeout_seconds} seconds.",
            )
            self._update_state(
                status="error",
                message="Bot session timed out.",
                last_run_finished_at=finished_at,
                last_duration_seconds=duration,
                last_exit_code=exit_code,
                last_run_emails_sent=sent_delta,
                current_pid=None,
                last_error=f"Timed out after {timeout_seconds} seconds.",
                consecutive_failures=self.state.get("consecutive_failures", 0) + 1,
            )
            return

        if exit_code and exit_code != 0:
            last_error = list(self.output_tail)[-1] if self.output_tail else f"Exit code {exit_code}"
            self._record_run(
                trigger_kind,
                started_at,
                finished_at,
                duration,
                exit_code,
                sent_delta,
                "error",
                error=last_error,
            )
            self._update_state(
                status="error",
                message="Bot session exited with an error.",
                last_run_finished_at=finished_at,
                last_duration_seconds=duration,
                last_exit_code=exit_code,
                last_run_emails_sent=sent_delta,
                current_pid=None,
                last_error=last_error,
                consecutive_failures=self.state.get("consecutive_failures", 0) + 1,
            )
            return

        self._record_run(
            trigger_kind,
            started_at,
            finished_at,
            duration,
            exit_code or 0,
            sent_delta,
            "success",
        )
        self._update_state(
            status="sleeping",
            message="Bot session finished successfully.",
            last_run_finished_at=finished_at,
            last_duration_seconds=duration,
            last_exit_code=exit_code or 0,
            last_run_emails_sent=sent_delta,
            current_pid=None,
            last_error=None,
            consecutive_failures=0,
        )

    def _sleep_until_next_run(self):
        interval = self._loop_interval_seconds()
        next_run = time.time() + interval
        self._update_state(
            status="sleeping",
            message="Waiting for the next scheduled bot run.",
            next_run_at=next_run,
        )
        while not self.stop_event.is_set():
            remaining = next_run - time.time()
            if remaining <= 0:
                self.next_trigger_kind = "scheduled"
                return True
            if self.run_requested.wait(timeout=min(remaining, 1.0)):
                self.run_requested.clear()
                return True
        return False

    def _wait_for_manual_request(self):
        self._update_state(
            status="disabled",
            message="Bot autostart is disabled. Use Run Bot Now or enable BOT_AUTOSTART.",
            next_run_at=None,
        )
        while not self.stop_event.is_set():
            if self.run_requested.wait(timeout=1.0):
                self.run_requested.clear()
                return True
        return False

    def _loop(self):
        auto_started = self._autostart_enabled()
        self._update_state(
            status="starting" if auto_started else "disabled",
            message="Bot manager booting." if auto_started else "Bot autostart is disabled.",
            next_run_at=time.time() if auto_started else None,
        )

        while not self.stop_event.is_set():
            if not auto_started:
                if not self._wait_for_manual_request():
                    break
            self._run_once()
            if self.stop_event.is_set():
                break
            auto_started = self._autostart_enabled()
            if not auto_started:
                continue
            if not self._sleep_until_next_run():
                break
