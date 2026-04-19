
import sqlite3
import datetime

def main():
    conn = sqlite3.connect('leads.db')
    cur = conn.cursor()
    
    # Total sent today
    cur.execute("SELECT count(*) FROM actions_log WHERE action_type = 'email_sent' AND date(timestamp) = date('now')")
    sent = cur.fetchone()[0]
    
    # Total failed today
    cur.execute("SELECT count(*) FROM actions_log WHERE action_type = 'failed' AND date(timestamp) = date('now')")
    failed = cur.fetchone()[0]
    
    total = sent + failed
    if total == 0:
        print("No emails sent today yet.")
        return
        
    rate = (sent / total) * 100
    print(f"Emails Sent: {sent}")
    print(f"Emails Failed: {failed}")
    print(f"Success Rate: {rate:.1f}%")
    
    conn.close()

if __name__ == "__main__":
    main()
