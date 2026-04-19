#!/usr/bin/env python3
import sqlite3


def main():
    with sqlite3.connect('leads.db') as conn:
        c = conn.cursor()

        c.execute('''
            SELECT id, business_name, website, email
    FROM leads
    WHERE website IS NOT NULL
    AND website != ""
    AND (email IS NULL OR email = "")
    LIMIT 5
''')

        rows = c.fetchall()

    print('Leads to process:')
    for row in rows:
        lead_id, name, website, email = row
        print(f'{lead_id}: {name} - {website} (email: {email or "None"})')


if __name__ == "__main__":
    main()