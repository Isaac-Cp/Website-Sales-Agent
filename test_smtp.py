import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

def test_connection():
    print(f"Testing connection for: {SMTP_EMAIL}")
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        print("✅ SUCCESS: Login successful!")
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ ERROR: Authentication failed. Credentials incorrect or account blocked.")
        return False
    except Exception as e:
        print(f"❌ ERROR: Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
