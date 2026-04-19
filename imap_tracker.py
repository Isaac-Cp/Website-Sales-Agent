import imaplib
import email
import re
import time
import json
import config
from llm_helper import classify_reply_intent

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

                lower_text = f"{subject}\n{payload_text}".lower()
                # Open receipt detection (read receipt / disposition notification)
                if target_email and from_addr.lower() != (config.IMAP_EMAIL.lower()) and (
                    "read receipt" in lower_text
                    or "disposition-notification" in lower_text
                    or "this is a read receipt" in lower_text
                    or subject.lower().startswith("read:")
                ):
                    events.append({
                        "type": "opened",
                        "email": target_email,
                        "meta": {
                            "from": from_addr,
                            "subject": subject,
                        },
                    })
                    M.store(num, "+FLAGS", "\\Seen")
                    continue

                # Reply detection (not from ourselves)
                if config.IMAP_EMAIL and from_addr.lower() != (config.IMAP_EMAIL.lower()):
                    if target_email:
                        event_meta = {"from": from_addr, "subject": subject}
                        reply_text = f"{subject}\n{payload_text}"
                        reply_intent = classify_reply_intent(reply_text)
                        event_meta["reply_intent"] = reply_intent

                        if any(keyword in lower_text for keyword in ["unsubscribe", "stop emailing", "remove me", "do not email", "opt out"]):
                            outcome_type = "unsubscribe"
                        elif any(keyword in lower_text for keyword in ["clicked", "link", "visited", "went to", "checked out"]):
                            outcome_type = "click"
                        elif any(keyword in lower_text for keyword in ["appointment", "booked", "schedule", "meeting", "call", "availability"]):
                            outcome_type = "appointment_requested"
                        elif any(keyword in lower_text for keyword in ["signed", "hired", "purchase", "contract", "pay", "invoice", "paid", "deal", "booked"]):
                            outcome_type = "deal_closed"
                        else:
                            outcome_type = "reply"

                        if event_meta.get("reply_intent") is None:
                            event_meta["reply_intent"] = classify_reply_intent(reply_text)

                        events.append({"type": outcome_type, "email": target_email, "meta": event_meta})
                        continue
                M.store(num, "+FLAGS", "\\Seen")
            except Exception as e:
                _log("imap_parse_error", error=str(e))
                continue
        M.logout()
    except Exception as e:
        _log("imap_error", error=str(e))
    return events
