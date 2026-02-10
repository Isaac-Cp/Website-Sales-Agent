import sqlite3
import os

db_path = "database.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check for recent Coffee Shop leads
    cur.execute("SELECT business_name, website, strategy, created_at FROM leads WHERE niche='Coffee Shop' ORDER BY id DESC LIMIT 10")
    leads = cur.fetchall()
    
    print(f"--- Recent 'Coffee Shop' Leads Found: {len(leads)} ---")
    for l in leads:
        print(l)
    
    conn.close()
