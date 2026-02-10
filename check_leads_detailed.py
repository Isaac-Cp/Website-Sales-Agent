import sqlite3
import os

db_path = "leads.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check table schema
    cur.execute("PRAGMA table_info(leads)")
    columns = [row[1] for row in cur.fetchall()]
    print(f"Columns: {columns}")
    
    # Check for leads with emails or audit data
    query = f"SELECT business_name, email, audit_score, email_sent FROM leads WHERE niche='Plumber' AND (email IS NOT NULL OR audit_score IS NOT NULL OR email_sent != 0) LIMIT 5"
    if 'audit_score' not in columns:
        # Try generic selection
        query = "SELECT business_name, email, website, strategy, email_sent FROM leads WHERE niche='Plumber' ORDER BY id DESC LIMIT 5"
        
    cur.execute(query)
    rows = cur.fetchall()
    print(f"--- Processed Leads Check ---")
    for r in rows:
        print(r)
    
    conn.close()
