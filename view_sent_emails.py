"""
Email Monitoring Script
Run this to see all emails that have been sent/logged in the database.
"""
import sqlite3
from datetime import datetime

db_path = "leads.db"

def view_sent_emails():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("SENT EMAILS LOG")
    print("=" * 80)
    
    # Get all emailed leads with their details
    cursor.execute("""
        SELECT 
            l.business_name,
            l.email,
            l.city,
            l.niche,
            l.strategy,
            l.rating,
            l.review_count,
            l.updated_at,
            l.status
        FROM leads l
        WHERE l.status = 'emailed'
        ORDER BY l.updated_at DESC
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("\nNo emails sent yet.\n")
    else:
        print(f"\nTotal Emails Sent: {len(results)}\n")
        
        for i, row in enumerate(results, 1):
            name, email, city, niche, strategy, rating, reviews, sent_at, status = row
            print(f"\n[{i}] {name}")
            print(f"    To: {email}")
            print(f"    Location: {city}")
            print(f"    Type: {niche}")
            print(f"    Strategy: {strategy}")
            print(f"    Rating: {rating}* ({reviews} reviews)")
            print(f"    Sent: {sent_at}")
            print(f"    Status: {status}")
            print("-" * 80)
    
    # Show daily count
    cursor.execute("""
        SELECT COUNT(*) 
        FROM actions_log 
        WHERE date(timestamp) = date('now') 
        AND action_type = 'email_sent'
    """)
    today_count = cursor.fetchone()[0]
    
    print(f"\n📊 Emails sent TODAY: {today_count}")
    print(f"📊 Total emails sent ALL TIME: {len(results)}")
    
    conn.close()

if __name__ == "__main__":
    view_sent_emails()
