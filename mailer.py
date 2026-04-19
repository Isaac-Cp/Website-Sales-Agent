import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
import validator


ACCOUNT_FAILURE_KINDS = {
    "auth",
    "connection",
    "missing_credentials",
    "ssl",
    "unexpected",
}


class Mailer:
    def __init__(self, email, password, server, port):
        self.email = email
        self.password = password
        self.server = server
        self.port = port
        self.last_error_kind = None
        self.last_error_message = None

    def _set_last_error(self, kind=None, message=None):
        self.last_error_kind = kind
        self.last_error_message = str(message) if message else None

    def _ssl_bypass_allowed(self):
        bypass_hosts = getattr(config, "SMTP_SSL_BYPASS_HOSTS", [])
        server = (self.server or "").strip().lower()
        for host in bypass_hosts:
            candidate = (host or "").strip().lower()
            if not candidate:
                continue
            if server == candidate or server.endswith(f".{candidate}"):
                return True
        return False

    def _create_ssl_context(self):
        context = ssl.create_default_context()
        if self._ssl_bypass_allowed():
            print(f"[SMTP] [!] SSL verification bypass enabled for {self.server}")
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context

    def _open_smtp_connection(self, timeout=None):
        """Open an SMTP connection using SSL or STARTTLS based on the configured port."""
        timeout = timeout or getattr(config, "SMTP_TIMEOUT", 12)
        context = self._create_ssl_context()

        if self.port == 465:
            return smtplib.SMTP_SSL(self.server, self.port, context=context, timeout=timeout)

        server = smtplib.SMTP(self.server, self.port, timeout=timeout)
        server.ehlo()
        if self.port in (25, 587):
            server.starttls(context=context)
            server.ehlo()
        return server

    def validate_email(self, email):
        """Validate email format."""
        return validator.get_email_validator().is_valid_syntax(email)

    def assess_email(self, email, smtp_probe=False, allow_risky=False, check_catch_all=None):
        """Return a structured validation result for the email."""
        if check_catch_all is None:
            check_catch_all = smtp_probe
        return validator.validate_email_local(
            email,
            sender_email=self.email,
            smtp_probe=smtp_probe,
            check_catch_all=check_catch_all,
            allow_risky=allow_risky,
        )

    def validate_email_deep(self, email, smtp_probe=False):
        """Compatibility wrapper around the layered validation engine."""
        result = self.assess_email(
            email,
            smtp_probe=smtp_probe,
            allow_risky=True,
            check_catch_all=smtp_probe,
        )
        if smtp_probe:
            return bool(result.get("can_send"))

        checks = result.get("checks", {})
        return bool(
            checks.get("syntax_valid")
            and checks.get("domain_valid", checks.get("domain_exists"))
            and checks.get("mx_valid", checks.get("has_mx_record"))
            and not checks.get("disposable", checks.get("is_disposable"))
        )

    def test_connection(self):
        """Test SMTP connection and credentials."""
        if not self.email or not self.password:
            self._set_last_error("missing_credentials", "Missing SMTP credentials.")
            print("[SMTP] [X] Missing SMTP credentials.")
            return False
        try:
            print(f"[SMTP] Testing connection to {self.server}:{self.port} as {self.email}...")
            with self._open_smtp_connection(timeout=getattr(config, "SMTP_TIMEOUT", 12)) as server:
                server.login(self.email, self.password)
            self._set_last_error(None, None)
            print("[SMTP] [OK] Connection successful!")
            return True
        except smtplib.SMTPAuthenticationError as e:
            self._set_last_error("auth", e)
            print("[SMTP] [X] Authentication failed. Check email/password.")
            return False
        except ssl.SSLError as e:
            self._set_last_error("ssl", e)
            print(f"[SMTP] [X] SSL error: {e}")
            return False
        except (smtplib.SMTPException, ConnectionError, TimeoutError, OSError) as e:
            self._set_last_error("connection", e)
            print(f"[SMTP] [X] SMTP error: {e}")
            return False
        except Exception as e:
            self._set_last_error("unexpected", e)
            print(f"[SMTP] [X] Connection error: {e}")
            return False

    def send_email(self, to_email, subject, body, attachment_paths=None, validation_result=None, retries=2):
        """Send email with validation, retry logic, and optional attachments."""
        print(f"  [DEBUG] Starting send_email to {to_email} from {self.email}...")
        if not self.email or not self.password:
            self._set_last_error("missing_credentials", "Missing sender credentials.")
            print("[SMTP] [X] Missing sender credentials.")
            return False

        validation_result = validation_result or self.assess_email(
            to_email,
            smtp_probe=False,
            allow_risky=True,
            check_catch_all=False,
        )
        classification = validation_result.get("classification") or validation_result.get("status")
        print(
            f"  [DEBUG] Validation result: {classification} "
            f"(score={validation_result.get('score')}, can_send={validation_result.get('can_send')})"
        )
        if not validator.should_send(validation_result):
            self._set_last_error("validation", f"{classification}:{validation_result.get('score')}")
            print(
                f"[SMTP] [X] Skipping {to_email} "
                f"(classification={classification}, score={validation_result.get('score')})."
            )
            return False

        msg = MIMEMultipart()
        msg["From"] = f"{self.email}"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if attachment_paths:
            if isinstance(attachment_paths, str):
                attachment_paths = [attachment_paths]

            import os
            from email import encoders
            from email.mime.base import MIMEBase

            for path in attachment_paths:
                if not path or not os.path.exists(path):
                    continue
                try:
                    with open(path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(path)}",
                    )
                    msg.attach(part)
                except Exception as e:
                    print(f"[SMTP] Error attaching {path}: {e}")

        timeout = getattr(config, "SMTP_TIMEOUT", 12)
        for attempt in range(retries + 1):
            try:
                with self._open_smtp_connection(timeout=timeout) as server:
                    server.login(self.email, self.password)
                    server.sendmail(self.email, to_email, msg.as_string())

                self._set_last_error(None, None)
                print(f"[SMTP] [OK] Email sent to {to_email}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                self._set_last_error("auth", e)
                print(f"[SMTP] [X] Authentication failed: {e}")
                return False

            except smtplib.SMTPRecipientsRefused:
                self._set_last_error("recipient", to_email)
                print(f"[SMTP] [X] Recipient refused: {to_email}")
                return False

            except ssl.SSLError as e:
                self._set_last_error("ssl", e)
                print(f"[SMTP] [X] SSL failure: {e}")
                return False

            except (smtplib.SMTPException, ConnectionError, TimeoutError, OSError) as e:
                self._set_last_error("connection", e)
                if attempt < retries:
                    print(f"[SMTP] [!] Attempt {attempt + 1} failed on {self.email}: {e}. Retrying...")
                    time.sleep(2)
                else:
                    print(f"[SMTP] [X] Failed after {retries + 1} attempts on {self.email}: {e}")
                    return False

            except Exception as e:
                self._set_last_error("unexpected", e)
                if attempt < retries:
                    print(f"[SMTP] [!] Unexpected error on {self.email}: {e}. Retrying...")
                    time.sleep(2)
                else:
                    print(f"[SMTP] [X] Unexpected error on {self.email}: {e}")
                    return False

        return False


class SMTPPool:
    def __init__(self, accounts=None, mailers=None):
        if mailers is None:
            mailers = [
                Mailer(account["email"], account["password"], account["server"], account["port"])
                for account in (accounts or [])
            ]
        self.mailers = mailers or []
        self.bad_accounts = set()
        self._rotation_index = 0
        self.last_used_mailer = None

    def _mailer_key(self, mailer):
        return f"{mailer.email}|{mailer.server}|{mailer.port}"

    def _advance_rotation(self, mailer):
        if not self.mailers:
            self._rotation_index = 0
            return
        try:
            idx = self.mailers.index(mailer)
        except ValueError:
            idx = -1
        self._rotation_index = (idx + 1) % len(self.mailers)

    def _ordered_mailers(self, preferred_mailer=None):
        active_mailers = [
            mailer for mailer in self.mailers if self._mailer_key(mailer) not in self.bad_accounts
        ]
        if not active_mailers:
            return []

        if preferred_mailer in active_mailers:
            idx = active_mailers.index(preferred_mailer)
            return active_mailers[idx:] + active_mailers[:idx]

        idx = self._rotation_index % len(active_mailers)
        return active_mailers[idx:] + active_mailers[:idx]

    def mark_account_bad(self, mailer, reason=None):
        if not mailer:
            return
        self.bad_accounts.add(self._mailer_key(mailer))
        if reason:
            print(f"[SMTP] [!] Marked account bad: {mailer.email} ({reason})")
        else:
            print(f"[SMTP] [!] Marked account bad: {mailer.email}")

    def get_working_mailer(self, preferred_mailer=None, test_login=False):
        for mailer in self._ordered_mailers(preferred_mailer=preferred_mailer):
            if test_login and not mailer.test_connection():
                self.mark_account_bad(mailer, reason=mailer.last_error_kind or "connection")
                continue
            self.last_used_mailer = mailer
            self._advance_rotation(mailer)
            return mailer
        return None

    def peek_mailer(self):
        ordered = self._ordered_mailers()
        if ordered:
            return ordered[0]
        return self.mailers[0] if self.mailers else None

    def send_email(
        self,
        to_email,
        subject,
        body,
        attachment_paths=None,
        validation_result=None,
        preferred_mailer=None,
        retries_per_account=1,
    ):
        validation_result = validation_result or validator.validate_email_local(
            to_email,
            smtp_probe=False,
            check_catch_all=False,
            allow_risky=True,
        )
        if not validator.should_send(validation_result):
            print(
                f"[SMTP] [X] No send attempt for {to_email} "
                f"(classification={validation_result.get('classification')}, score={validation_result.get('score')})."
            )
            return False

        candidates = self._ordered_mailers(preferred_mailer=preferred_mailer)
        if not candidates:
            print("[SMTP] [X] No healthy SMTP accounts available.")
            return False

        for mailer in candidates:
            sent = mailer.send_email(
                to_email,
                subject,
                body,
                attachment_paths=attachment_paths,
                validation_result=validation_result,
                retries=retries_per_account,
            )
            if sent:
                self.last_used_mailer = mailer
                self._advance_rotation(mailer)
                return True

            if mailer.last_error_kind in ACCOUNT_FAILURE_KINDS:
                self.mark_account_bad(mailer, reason=mailer.last_error_kind)
                continue

            if mailer.last_error_kind in {"recipient", "validation"}:
                return False

            self.mark_account_bad(mailer, reason=mailer.last_error_kind or "send_failure")

        print(f"[SMTP] [X] All SMTP accounts failed for {to_email}.")
        return False


def build_smtp_pool(accounts=None):
    accounts = accounts if accounts is not None else config.get_smtp_accounts()
    return SMTPPool(accounts=accounts)


def get_working_smtp(accounts=None):
    smtp_pool = build_smtp_pool(accounts=accounts)
    return smtp_pool.get_working_mailer(test_login=True)
