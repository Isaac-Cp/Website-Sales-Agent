import socket
import ssl
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
EMAIL = os.getenv("SMTP_EMAIL")
PASSWORD = os.getenv("SMTP_PASSWORD")

def test_port(port, use_ssl=False):
    print(f"\n--- Testing Port {port} ({'SSL' if use_ssl else 'STARTTLS'}) ---")
    try:
        # 1. Socket Connection
        sock = socket.create_connection((SMTP_SERVER, port), timeout=5)
        print(f"✅ Socket connected to {SMTP_SERVER}:{port}")
        
        # 2. Protocol Handshake
        if use_ssl:
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=SMTP_SERVER)
            print("✅ SSL Handshake complete")
            
            # SMTP Greeting
            server = smtplib.SMTP_SSL(SMTP_SERVER, port)
        else:
            server = smtplib.SMTP(SMTP_SERVER, port)
            
        server.ehlo()
        print("✅ EHLO successful")
        
        if not use_ssl:
            server.starttls()
            print("✅ STARTTLS successful")
            server.ehlo()
            
        # 3. Login
        try:
            server.login(EMAIL, PASSWORD)
            print("✅ LOGIN SUCCESSFUL!")
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ LOGIN FAILED: {e}")
        except Exception as e:
            print(f"❌ LOGIN ERROR: {e}")
            
        server.quit()
        
    except Exception as e:
        print(f"❌ CRITICAL FAILURE: {e}")

if __name__ == "__main__":
    test_port(587, use_ssl=False)
    test_port(465, use_ssl=True)
