#!/usr/bin/env python3
"""
Mock email extraction - adds test emails to leads for testing purposes.
This simulates what the scraper would do without requiring browser automation.
"""

import sqlite3
import random

def add_mock_emails():
    """Add mock emails to leads for testing."""
    mock_emails = [
        "info@testcompany1.com",
        "contact@testcompany2.com",
        "hello@testcompany3.com",
        "sales@testcompany4.com",
        "support@testcompany5.com",
        "admin@testcompany6.com",
        "team@testcompany7.com",
        "business@testcompany8.com",
        "office@testcompany9.com",
        "inquiry@testcompany10.com"
    ]

    conn = sqlite3.connect('leads.db')
    cur = conn.cursor()

    # Get leads without emails
    cur.execute('''
        SELECT id, business_name
        FROM leads
        WHERE (email IS NULL OR email = '')
        AND website IS NOT NULL
        AND website != ''
        AND COALESCE(status, 'scraped') NOT IN ('emailed', 'manual_queue', 'low_priority', 'no_contact')
        LIMIT 10
    ''')

    leads = cur.fetchall()

    print(f"Adding mock emails to {len(leads)} leads...")

    for i, (lead_id, business_name) in enumerate(leads):
        if i < len(mock_emails):
            email = mock_emails[i]
            cur.execute('UPDATE leads SET email = ? WHERE id = ?', (email, lead_id))
            print(f"  ✓ Added {email} to {business_name}")

    conn.commit()
    conn.close()

    print("Mock email addition complete!")

if __name__ == "__main__":
    add_mock_emails()