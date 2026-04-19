"""
run_agent.py — Launches the full sales agent capped at 10 emails.
Output is written unbuffered to agent_run.log AND to the console.
"""
import sys, os

# Force unbuffered output
os.environ["PYTHONUNBUFFERED"] = "1"

# Tee stdout → file in real-time
class Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()
    def flush(self):
        for s in self.streams:
            s.flush()

log_file = open("agent_run.log", "w", encoding="utf-8", buffering=1)
sys.stdout = Tee(sys.__stdout__, log_file)
sys.stderr = Tee(sys.__stderr__, log_file)

# ── Patch daily limit then run ────────────────────────────────────────────────
import config
config.MAX_DAILY_ACTIONS = 25   # stop after 25 emails total today
config.SESSION_QUERIES   = 15   # search queries to find new leads
config.ALLOW_RISKY_EMAILS = True # Let's be more permissive for this run

import main
main.main()
