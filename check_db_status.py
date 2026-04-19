#!/usr/bin/env python3
import sqlite3


def main():
    with sqlite3.connect('leads.db') as conn:
        c = conn.cursor()

        # Count unsent leads
        c.execute('''
            SELECT COUNT(*) FROM leads 
            WHERE COALESCE(status, 'scraped') NOT IN ('emailed', 'manual_queue', 'low_priority', 'no_contact')
        ''')
        unsent = c.fetchone()[0]

        # Count leads with valid emails
        c.execute('''
            SELECT COUNT(*) FROM leads 
            WHERE email IS NOT NULL 
            AND email != ''
            AND email NOT LIKE 'wght@%'
            AND email NOT LIKE 'aos@%'
            AND COALESCE(status, 'scraped') NOT IN ('emailed', 'manual_queue', 'low_priority', 'no_contact')
        ''')
        valid_emails = c.fetchone()[0]

        # Total leads
        c.execute('SELECT COUNT(*) FROM leads')
        total = c.fetchone()[0]

        # Emailed count
        c.execute("SELECT COUNT(*) FROM leads WHERE status = 'emailed'")
        emailed = c.fetchone()[0]

    print("Database Status:")
    print(f"  Total leads: {total}")
    print(f"  Emailed: {emailed}")
    print(f"  Unsent (scraped/new): {unsent}")
    print(f"  With valid emails: {valid_emails}")


if __name__ == "__main__":
    main()
