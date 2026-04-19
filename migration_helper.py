
import sqlite3
import config
from database import DataManager
import datetime

def main():
    print("Starting Sales Agent Migration & Cleanup Helper...")
    dm = DataManager()
    
    # 1. Run DB Init to ensure all columns exist (DataManager._init_db handles this)
    print("Ensuring schema is up to date...")
    dm._init_db()
    
    # 2. Recalculate all lead scores
    print("Recalculating lead scores...")
    dm.update_all_lead_scores()
    
    # 3. Cleanup stale leads (older than 30 days)
    print("Cleaning up stale leads...")
    stale_count = dm.cleanup_stale_leads(days=30)
    print(f"Marked {stale_count} leads as stale.")
    
    # 4. Data Integrity Checks
    conn = dm.get_connection()
    cursor = conn.cursor()
    
    # Find leads missing crucial info
    cursor.execute("SELECT count(*) FROM leads WHERE email IS NULL AND phone IS NULL AND website IS NULL")
    useless_count = cursor.fetchone()[0]
    if useless_count > 0:
        print(f"Found {useless_count} leads with no contact method or website. Removing...")
        cursor.execute("DELETE FROM leads WHERE email IS NULL AND phone IS NULL AND website IS NULL")
        conn.commit()
    
    # Normalize niche names (simple example)
    print("Normalizing niche names...")
    cursor.execute("UPDATE leads SET niche = 'HVAC' WHERE lower(niche) = 'hvac'")
    cursor.execute("UPDATE leads SET niche = 'Plumber' WHERE lower(niche) = 'plumbing' OR lower(niche) = 'plumber'")
    conn.commit()
    
    # 5. Conversion Summary
    print("\n--- Conversion Performance Summary ---")
    attribution = dm.get_conversion_attribution(group_by="persona")
    for persona, stats in attribution.items():
        sent = stats['sent']
        conv = stats['conversions']
        rate = (conv / sent * 100) if sent > 0 else 0
        print(f"Persona: {persona:20} | Sent: {sent:4} | Conversions: {conv:4} | Rate: {rate:5.1f}%")

    print("\n--- Industry Performance Summary ---")
    attribution = dm.get_conversion_attribution(group_by="industry")
    for industry, stats in attribution.items():
        sent = stats['sent']
        conv = stats['conversions']
        rate = (conv / sent * 100) if sent > 0 else 0
        print(f"Industry: {industry:20} | Sent: {sent:4} | Conversions: {conv:4} | Rate: {rate:5.1f}%")

    conn.close()
    print("\nMigration and cleanup finished.")

if __name__ == "__main__":
    main()
