import sqlite3
import os
import smtplib
import sys
import config
from database import DataManager
from mailer import Mailer

def check_env():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("--- ENVIRONMENT CHECK ---")
    print(f"DRY_RUN: {config.DRY_RUN}")
    print(f"BOT_AUTOSTART: {config.BOT_AUTOSTART}")
    print(f"SMTP_EMAIL: {config.SMTP_EMAIL}")
    print(f"SMTP_SERVER: {config.SMTP_SERVER}")
    print(f"is_resource_constrained: {config.is_resource_constrained}")
    print(f"SMTP_TIMEOUT: {config.SMTP_TIMEOUT}")
    print("")

def check_db():
    print("--- DATABASE CHECK ---")
    if not os.path.exists("leads.db"):
        print("❌ leads.db not found!")
        return
    
    conn = sqlite3.connect("leads.db")
    cur = conn.cursor()
    
    cur.execute("SELECT status, count(*) FROM leads GROUP BY status")
    stats = cur.fetchall()
    print(f"Lead Stats: {stats}")
    
    # Candidates for cold email
    where_cold = "email IS NOT NULL AND email != '' AND COALESCE(status, 'scraped') NOT IN ('emailed', 'manual_queue', 'low_priority', 'no_contact', 'not_interested', 'bounced', 'appointment_booked', 'sale_closed', 'blacklisted', 'completed')"
    cur.execute(f"SELECT count(*) FROM leads WHERE {where_cold}")
    cold_candidates = cur.fetchone()[0]
    print(f"Cold Email Candidates: {cold_candidates}")
    
    # Candidates for follow-up
    cur.execute("SELECT count(*) FROM leads WHERE status IN ('emailed', 'followup_1', 'followup_2')")
    followup_candidates = cur.fetchone()[0]
    print(f"Follow-up Candidates: {followup_candidates}")
    
    if cold_candidates == 0:
        print("⚠️  No cold email candidates found. You likely need to run the scraper to find new leads.")
    
    cur.execute(f"SELECT business_name, email FROM leads WHERE {where_cold} LIMIT 5")
    samples = cur.fetchall()
    if samples:
        print("Sample Candidates:")
        for name, email in samples:
            print(f"  - {name}: {email}")
            
    conn.close()
    print("")

def check_smtp():
    print("--- SMTP CHECK ---")
    accounts = config.get_smtp_accounts()
    if not accounts:
        print("❌ No SMTP accounts configured!")
        return
    
    for acc in accounts:
        email = acc['email']
        server_addr = acc['server']
        port = acc['port']
        print(f"Testing {email} ({server_addr}:{port})...")
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(server_addr, port, timeout=config.SMTP_TIMEOUT)
            else:
                server = smtplib.SMTP(server_addr, port, timeout=config.SMTP_TIMEOUT)
                server.ehlo()
                server.starttls()
            
            server.ehlo()
            server.login(email, acc['password'])
            print(f"  ✅ SUCCESS: Login successful for {email}")
            server.quit()
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
    print("")

if __name__ == "__main__":
    check_env()
    check_db()
    check_smtp()
    print("--- RECOMMENDATIONS ---")
    print("1. If Cold Candidates is 0: Run 'python main.py --audit --query \"Plumbers in Sydney\"' to find leads.")
    print("2. If SMTP Fails: Check your SMTP credentials and App Passwords.")
    print("3. If DRY_RUN is True: Emails will NOT be sent. Set DRY_RUN=false in your environment.")
    print("4. If BOT_AUTOSTART is False: The background bot won't run automatically on deploy. Set BOT_AUTOSTART=true.")
