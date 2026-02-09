import smtplib
import ssl
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import socket
try:
    import dns.resolver
except Exception:
    dns = None

class Mailer:
    def __init__(self, email, password, server, port):
        self.email = email
        self.password = password
        self.server = server
        self.port = port
        self.context = ssl.create_default_context()
    
    def validate_email(self, email):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_email_deep(self, email, smtp_probe=False):
        """Validate email deliverability using DNS MX lookup and optional SMTP RCPT probe.
        smtp_probe uses the recipient's MX. Many servers block VRFY; RCPT may still be rejected.
        """
        if not self.validate_email(email):
            return False
        try:
            domain = email.split('@')[1]
        except Exception:
            return False
        # MX lookup
        mx_hosts = []
        try:
            if dns and hasattr(dns, 'resolver'):
                answers = dns.resolver.resolve(domain, 'MX')
                mx_hosts = [str(r.exchange).rstrip('.') for r in answers]
        except Exception:
            mx_hosts = []
        if not mx_hosts:
            # Fallback: try A record resolution
            try:
                socket.gethostbyname(domain)
            except Exception:
                return False
        if not smtp_probe:
            return True
        # Optional SMTP RCPT probe (best-effort, time-limited)
        target_host = mx_hosts[0] if mx_hosts else domain
        try:
            with smtplib.SMTP(target_host, 25, timeout=8) as server:
                sender_domain = self.email.split('@')[1] if '@' in self.email else 'gmail.com'
                server.helo(sender_domain)
                server.mail(self.email)
                code, _ = server.rcpt(email)
                return 200 <= code < 300
        except Exception:
            return False
    
    def test_connection(self):
        """Test SMTP connection and credentials."""
        try:
            print(f"[SMTP] Testing connection to {self.server}:{self.port}...")
            with smtplib.SMTP_SSL(self.server, self.port, context=self.context, timeout=10) as server:
                server.login(self.email, self.password)
            print("[SMTP] [OK] Connection successful!")
            return True
        except smtplib.SMTPAuthenticationError:
            print("[SMTP] [X] Authentication failed. Check email/password.")
            return False
        except smtplib.SMTPException as e:
            print(f"[SMTP] [X] SMTP error: {e}")
            return False
        except Exception as e:
            print(f"[SMTP] [X] Connection error: {e}")
            return False

    def send_email(self, to_email, subject, body, attachment_paths=None, retries=2):
        """Send email with validation, retry logic, and optional attachments."""
        
        # Validate recipient email
        if not self.validate_email_deep(to_email, smtp_probe=False):
            print(f"[SMTP] [X] Invalid email format: {to_email}")
            return False
        
        msg = MIMEMultipart()
        msg["From"] = f"{self.email}"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        # Attachments
        if attachment_paths:
            if isinstance(attachment_paths, str):
                attachment_paths = [attachment_paths]
                
            import os
            from email.mime.base import MIMEBase
            from email import encoders
            
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
                        f"attachment; filename= {os.path.basename(path)}",
                    )
                    msg.attach(part)
                except Exception as e:
                    print(f"[SMTP] Error attaching {path}: {e}")

        
        # Retry logic
        for attempt in range(retries + 1):
            try:
                with smtplib.SMTP_SSL(self.server, self.port, context=self.context, timeout=15) as server:
                    server.login(self.email, self.password)
                    server.sendmail(self.email, to_email, msg.as_string())
                
                print(f"[SMTP] [OK] Email sent to {to_email}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                print(f"[SMTP] [X] Authentication failed: {e}")
                return False  # Don't retry auth errors
                
            except smtplib.SMTPRecipientsRefused:
                print(f"[SMTP] [X] Recipient refused: {to_email}")
                return False  # Don't retry invalid recipients
                
            except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
                if attempt < retries:
                    print(f"[SMTP] [!] Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(2)  # Wait before retry
                else:
                    print(f"[SMTP] [X] Failed after {retries + 1} attempts: {e}")
                    return False
                    
            except Exception as e:
                print(f"[SMTP] [X] Unexpected error: {e}")
                return False
        
        return False
