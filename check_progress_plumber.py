import sqlite3
import os

db_path = "leads.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check for recent Plumber leads
    cur.execute("SELECT business_name, website, strategy, created_at FROM leads WHERE niche='Plumber' ORDER BY id DESC LIMIT 10")
    leads = cur.fetchall()
    
    print(f"--- Recent 'Plumber' Leads Found in leads.db: {len(leads)} ---")
    for l in leads:
        print(l)
    
    conn.close()
