import imaplib
import email
import re
import time
import json
import config

def _log(event, **fields):
    try:
        print(json.dumps({"event": event, "ts": int(time.time()), **fields}))
    except Exception:
        pass

def fetch_outcomes(since_seconds=3600, mailbox="INBOX"):
    events = []
    if not (config.IMAP_HOST and config.IMAP_EMAIL and config.IMAP_PASSWORD):
        return events
    try:
        M = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
        M.login(config.IMAP_EMAIL, config.IMAP_PASSWORD)
        M.select(mailbox)
        typ, data = M.search(None, "(UNSEEN)")
        ids = data[0].split()
        for num in ids:
            try:
                typ, msg_data = M.fetch(num, "(RFC822)")
                if typ != "OK":
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                from_addr = email.utils.parseaddr(msg.get("From"))[1] or ""
                subject = msg.get("Subject") or ""
                payload_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        if ctype in ("text/plain", "message/delivery-status"):
                            try:
                                payload_text += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                            except Exception:
                                pass
                else:
                    try:
                        payload_text = msg.get_payload(decode=True).decode(errors="ignore")
                    except Exception:
                        payload_text = str(msg.get_payload())
                # Bounce detection
                is_bounce = ("mailer-daemon" in from_addr.lower()) or \
                           ("delivery status" in subject.lower()) or \
                           ("undeliver" in subject.lower()) or \
                           ("delivery incomplete" in subject.lower()) or \
                           ("failure" in subject.lower())
                # Extract target email
                target_email = None
                m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", payload_text or "")
                if m:
                    target_email = m.group(0)
                if is_bounce and target_email:
                    events.append({"type": "bounce", "email": target_email, "meta": {"subject": subject}})
                    continue
                # Reply detection (not from ourselves)
                if config.IMAP_EMAIL and from_addr.lower() != (config.IMAP_EMAIL.lower()):
                    # Prefer Reply-To or From as the sender; we try to find our original recipient in quoted text
                    if target_email:
                        events.append({"type": "reply", "email": target_email, "meta": {"from": from_addr, "subject": subject}})
                        continue
                M.store(num, "+FLAGS", "\\Seen")
            except Exception as e:
                _log("imap_parse_error", error=str(e))
                continue
        M.logout()
    except Exception as e:
        _log("imap_error", error=str(e))
    return events
