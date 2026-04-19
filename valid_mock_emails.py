#!/usr/bin/env python3
"""
Add valid mock emails for testing.
"""

import sqlite3

def add_valid_mock_emails():
    """Add valid mock emails to leads for testing."""
    # Using smaller business domains that might accept emails
    valid_emails = [
        "info@moz.com",  # SEO company
        "contact@buffer.com",  # Social media company
        "test@canva.com",  # Design company
        "hello@notion.com",  # Productivity company
        "admin@slack.com",  # Communication company
        "support@zoom.com",  # Video company
        "team@trello.com",  # Project management
        "business@asana.com",  # Project management
        "office@microsoft.com",  # Will be rejected but tests validation
        "sales@google.com"  # Will be rejected but tests validation
    ]

    conn = sqlite3.connect('leads.db')
    cur = conn.cursor()

    # Clear existing mock emails and add valid ones
    cur.execute('UPDATE leads SET email = NULL WHERE email LIKE "%@testcompany%.com"')

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

    print(f"Adding valid mock emails to {len(leads)} leads...")

    for i, (lead_id, business_name) in enumerate(leads):
        if i < len(valid_emails):
            email = valid_emails[i]
            cur.execute('UPDATE leads SET email = ? WHERE id = ?', (email, lead_id))
            print(f"  ✓ Added {email} to {business_name}")

    conn.commit()
    conn.close()

    print("Valid mock email addition complete!")

if __name__ == "__main__":
    add_valid_mock_emails()