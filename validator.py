import random
import re
import smtplib
import socket
import string
from typing import Dict, List, Optional

import requests

import config

try:
    import dns.resolver
except Exception:
    dns = None


DISPOSABLE_DOMAINS = {
    "10minutemail.com",
    "guerrillamail.com",
    "mailinator.com",
    "tempmail.com",
    "tempmailo.com",
    "trashmail.com",
    "yopmail.com",
}

HIGH_RISK_DOMAINS = (
    "tempmail",
    "10min",
    "guerrilla",
)


def _get_result_check(result: Dict[str, object], *keys: str):
    checks = result.get("checks", {}) or {}
    for key in keys:
        if key in result:
            return result.get(key)
        if key in checks:
            return checks.get(key)
    return None


def score_email(result: Dict[str, object]) -> int:
    score = 0

    if _get_result_check(result, "syntax_valid"):
        score += 30

    if _get_result_check(result, "domain_valid", "domain_exists"):
        score += 30

    if _get_result_check(result, "mx_valid", "has_mx_record"):
        score += 30

    if _get_result_check(result, "smtp_valid", "smtp_mailbox_exists") is True:
        score += 10

    return score


def classify(score: int) -> str:
    if score >= 80:
        return "SAFE"
    if score >= 60:
        return "LIKELY_VALID"
    if score >= 50:
        return "RISKY"  # Lowered threshold to reduce false rejections
    return "INVALID"


def should_send(email_result: Dict[str, object]) -> bool:
    classification = (
        email_result.get("classification")
        or email_result.get("status")
        or classify(int(email_result.get("score") or 0))
    )
    disposable = _get_result_check(email_result, "disposable", "is_disposable")

    if classification == "INVALID":
        return False

    if disposable:
        return False

    return True


def _clean_txt_records(txt_records):
    if not txt_records:
        return []
    cleaned = []
    for record in txt_records:
        if isinstance(record, bytes):
            try:
                record = record.decode("utf-8", errors="ignore")
            except Exception:
                record = str(record)
        if isinstance(record, str):
            cleaned.append(record.strip())
    return cleaned


class EmailValidator:
    """
    Local "worth trying" validator:
    syntax -> domain -> MX -> optional SMTP -> reputation/disposable filters.
    """

    def __init__(self, smtp_timeout: int = 12, dns_timeout: int = 5):
        self.smtp_timeout = smtp_timeout
        self.dns_timeout = dns_timeout
        self._domain_cache: Dict[str, bool] = {}
        self._mx_cache: Dict[str, List[str]] = {}
        self._catch_all_cache: Dict[str, Optional[bool]] = {}

        if dns and hasattr(dns, "resolver"):
            try:
                dns.resolver.default_resolver.lifetime = dns_timeout
                dns.resolver.default_resolver.timeout = dns_timeout
            except Exception:
                pass

    def normalize_email(self, email: str) -> str:
        return (email or "").strip().lower()

    def is_valid_syntax(self, email: str) -> bool:
        email = self.normalize_email(email)
        if not email or "@" not in email or email.count("@") != 1:
            return False

        pattern = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
        if re.match(pattern, email) is None:
            return False

        local_part, domain = email.rsplit("@", 1)
        if ".." in local_part or ".." in domain:
            return False
        if local_part.startswith(".") or local_part.endswith("."):
            return False
        if domain.startswith("-") or domain.endswith("-"):
            return False

        labels = domain.split(".")
        if any(not label or label.startswith("-") or label.endswith("-") for label in labels):
            return False

        return True

    def domain_exists(self, email_or_domain: str) -> bool:
        domain = self._extract_domain(email_or_domain)
        if not domain:
            return False
        if domain in self._domain_cache:
            return self._domain_cache[domain]

        exists = False
        try:
            socket.getaddrinfo(domain, None)
            exists = True
        except Exception:
            exists = False

        self._domain_cache[domain] = exists
        return exists

    def get_mx_records(self, email_or_domain: str) -> List[str]:
        domain = self._extract_domain(email_or_domain)
        if not domain:
            return []
        if domain in self._mx_cache:
            return list(self._mx_cache[domain])

        mx_hosts: List[str] = []
        if dns and hasattr(dns, "resolver"):
            try:
                records = dns.resolver.resolve(domain, "MX")
                sorted_records = sorted(records, key=lambda record: getattr(record, "preference", 0))
                mx_hosts = [str(record.exchange).rstrip(".") for record in sorted_records]
            except Exception:
                mx_hosts = []

        self._mx_cache[domain] = list(mx_hosts)
        return mx_hosts

    def has_mx_record(self, email_or_domain: str) -> bool:
        return bool(self.get_mx_records(email_or_domain))

    def is_disposable(self, email_or_domain: str) -> bool:
        domain = self._extract_domain(email_or_domain)
        return domain in DISPOSABLE_DOMAINS if domain else False

    def is_suspicious(self, email_or_domain: str) -> bool:
        domain = self._extract_domain(email_or_domain)
        if not domain:
            return False
        return any(marker in domain for marker in HIGH_RISK_DOMAINS)

    def smtp_check(self, email: str, sender_email: Optional[str] = None) -> Dict[str, Optional[object]]:
        domain = self._extract_domain(email)
        if not domain:
            return {"ok": False, "code": None, "message": "missing domain"}

        hosts = self.get_mx_records(domain)
        if not hosts:
            return {"ok": None, "code": None, "message": "no mx record"}

        helo_name = self._smtp_helo_name(sender_email)
        mail_from = sender_email if sender_email and "@" in sender_email else f"validator@{helo_name}"
        last_response = {"ok": None, "code": None, "message": "smtp probe inconclusive"}

        for host in hosts[:3]:
            server = None
            try:
                server = smtplib.SMTP(timeout=self.smtp_timeout)
                server.connect(host, 25)
                server.helo(helo_name)
                server.mail(mail_from)
                code, message = server.rcpt(email)
                msg_text = self._decode_smtp_message(message)

                if 200 <= code < 300:
                    return {"ok": True, "code": code, "message": msg_text or "recipient accepted"}
                if code in (450, 451, 452, 421):
                    last_response = {"ok": None, "code": code, "message": msg_text or "temporary smtp response"}
                    continue
                if code >= 500:
                    return {"ok": False, "code": code, "message": msg_text or "recipient rejected"}

                last_response = {"ok": None, "code": code, "message": msg_text or "unknown smtp response"}
            except Exception as e:
                last_response = {"ok": None, "code": None, "message": str(e)}
            finally:
                try:
                    if server is not None:
                        server.quit()
                except Exception:
                    pass

        return last_response

    def is_catch_all(self, domain: str, sender_email: Optional[str] = None) -> Optional[bool]:
        domain = self._extract_domain(domain)
        if not domain:
            return None
        if domain in self._catch_all_cache:
            return self._catch_all_cache[domain]

        fake_local = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        fake_email = f"{fake_local}@{domain}"
        probe = self.smtp_check(fake_email, sender_email=sender_email)

        catch_all = True if probe.get("ok") is True else False if probe.get("ok") is False else None
        self._catch_all_cache[domain] = catch_all
        return catch_all

    def get_txt_records(self, domain: str) -> List[str]:
        if not domain or dns is None:
            return []

        records = []
        try:
            answers = dns.resolver.resolve(domain, "TXT")
            for record in answers:
                records.extend(_clean_txt_records(record.strings if hasattr(record, 'strings') else [str(record)]))
        except Exception:
            pass
        return records

    def has_spf_record(self, email_or_domain: str) -> Optional[bool]:
        domain = self._extract_domain(email_or_domain)
        if not domain:
            return None

        try:
            records = self.get_txt_records(domain)
            for record in records:
                if "v=spf1" in record.lower():
                    return True
        except Exception:
            return None
        return False

    def get_dmarc_policy(self, email_or_domain: str) -> Optional[str]:
        domain = self._extract_domain(email_or_domain)
        if not domain:
            return None

        dmarc_domain = f"_dmarc.{domain}"
        try:
            records = self.get_txt_records(dmarc_domain)
            for record in records:
                lower = record.lower()
                if "v=dmarc1" in lower:
                    match = re.search(r"p\s*=\s*(none|quarantine|reject)", lower)
                    return match.group(1) if match else "unknown"
        except Exception:
            pass
        return None

    def validate(
        self,
        email: str,
        sender_email: Optional[str] = None,
        smtp_probe: bool = False,
        check_catch_all: Optional[bool] = None,
        allow_risky: bool = False,
    ) -> Dict[str, object]:
        email = self.normalize_email(email)
        if check_catch_all is None:
            check_catch_all = smtp_probe

        result = {
            "email": email,
            "score": 0,
            "classification": "INVALID",
            "status": "INVALID",
            "can_send": False,
            "worth_trying": False,
            "reasons": [],
            "syntax_valid": False,
            "domain_valid": False,
            "mx_valid": False,
            "spf_valid": None,
            "dmarc_policy": None,
            "smtp_valid": None,
            "disposable": False,
            "suspicious_domain": False,
            "checks": {
                "syntax_valid": False,
                "domain_valid": False,
                "domain_exists": False,
                "mx_valid": False,
                "has_mx_record": False,
                "spf_valid": None,
                "smtp_valid": None,
                "smtp_mailbox_exists": None,
                "disposable": False,
                "catch_all": None,
                "is_disposable": False,
                "disposable_domain_match": False,
                "suspicious_domain": False,
            },
            "smtp": {
                "code": None,
                "message": None,
            },
        }

        def set_check(primary_key: str, value, *aliases: str) -> None:
            result[primary_key] = value
            result["checks"][primary_key] = value
            for alias in aliases:
                result["checks"][alias] = value

        if not self.is_valid_syntax(email):
            result["reasons"].append("invalid syntax")
            result["score"] = score_email(result)
            result["classification"] = classify(result["score"])
            result["status"] = result["classification"]
            result["can_send"] = should_send(result)
            result["worth_trying"] = result["can_send"]
            return result

        set_check("syntax_valid", True)

        domain = self._extract_domain(email)
        if self.domain_exists(domain):
            set_check("domain_valid", True, "domain_exists")
        else:
            result["reasons"].append("domain does not resolve")

        if self.has_mx_record(domain):
            set_check("mx_valid", True, "has_mx_record")
        else:
            result["reasons"].append("mx record missing")

        spf = self.has_spf_record(domain)
        set_check("spf_valid", spf is True)
        result["spf_valid"] = spf
        result["checks"]["spf_valid"] = spf
        result["dmarc_policy"] = self.get_dmarc_policy(domain)

        disposable_match = self.is_disposable(email)
        suspicious_domain = self.is_suspicious(email)
        disposable = disposable_match or suspicious_domain
        result["checks"]["disposable_domain_match"] = disposable_match
        set_check("suspicious_domain", suspicious_domain)
        set_check("disposable", disposable, "is_disposable")
        if disposable_match:
            result["reasons"].append("disposable domain")
        if suspicious_domain and not disposable_match:
            result["reasons"].append("high-risk domain pattern")

        if smtp_probe and result["checks"]["has_mx_record"]:
            smtp_result = self.smtp_check(email, sender_email=sender_email)
            set_check("smtp_valid", smtp_result.get("ok"), "smtp_mailbox_exists")
            result["smtp"]["code"] = smtp_result.get("code")
            result["smtp"]["message"] = smtp_result.get("message")

            if smtp_result.get("ok") is False:
                result["reasons"].append("smtp recipient rejected")
            elif smtp_result.get("ok") is None:
                result["reasons"].append("smtp check inconclusive")

        if check_catch_all and result["checks"]["has_mx_record"]:
            catch_all = self.is_catch_all(domain, sender_email=sender_email)
            result["checks"]["catch_all"] = catch_all
            if catch_all is True:
                result["reasons"].append("domain appears catch-all")
            elif catch_all is None:
                result["reasons"].append("catch-all check inconclusive")

        result["score"] = max(0, min(100, int(score_email(result))))
        result["classification"] = classify(result["score"])
        result["status"] = result["classification"]
        result["can_send"] = should_send(result)
        result["worth_trying"] = result["can_send"]
        return result

    def quick_check(self, email: str) -> bool:
        result = self.validate(email, smtp_probe=False, check_catch_all=False, allow_risky=True)
        return (
            result["checks"]["syntax_valid"]
            and result["checks"]["domain_valid"]
            and result["checks"]["mx_valid"]
            and not result["checks"]["disposable"]
        )

    def _extract_domain(self, email_or_domain: str) -> str:
        text = self.normalize_email(email_or_domain)
        if "@" in text:
            return text.rsplit("@", 1)[1]
        return text

    def _smtp_helo_name(self, sender_email: Optional[str]) -> str:
        sender_domain = self._extract_domain(sender_email or "")
        return sender_domain or "localhost"

    def _decode_smtp_message(self, message) -> str:
        if isinstance(message, bytes):
            try:
                return message.decode("utf-8", errors="ignore")
            except Exception:
                return repr(message)
        return str(message) if message is not None else ""


_LOCAL_VALIDATOR = EmailValidator(smtp_timeout=getattr(config, "SMTP_TIMEOUT", 12))


def get_email_validator() -> EmailValidator:
    return _LOCAL_VALIDATOR


def validate_email_local(
    email: str,
    sender_email: Optional[str] = None,
    smtp_probe: bool = False,
    check_catch_all: Optional[bool] = None,
    allow_risky: bool = False,
) -> Dict[str, object]:
    return _LOCAL_VALIDATOR.validate(
        email,
        sender_email=sender_email,
        smtp_probe=smtp_probe,
        check_catch_all=check_catch_all,
        allow_risky=allow_risky,
    )


def validate_email_api(email):
    """
    Optional third-party validator kept for backwards compatibility.
    Returns:
        True: Valid / Deliverable
        False: Invalid / Undeliverable
        None: Unknown / Error
    """
    provider = config.VALIDATION_PROVIDER.lower()

    if provider == "hunter":
        return _validate_hunter(email)
    elif provider == "zerobounce":
        return _validate_zerobounce(email)

    return None


def _validate_hunter(email):
    if not config.HUNTER_API_KEY:
        print("[Validator] Hunter API Key missing.")
        return None

    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={config.HUNTER_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "data" in data:
            status = data["data"]["status"]
            if status == "valid":
                return True
            if status == "invalid":
                return False
            print(f"[Validator] Hunter status: {status} for {email}")
            return None
    except Exception as e:
        print(f"[Validator] Hunter API error: {e}")
        return None


def _validate_zerobounce(email):
    return None
