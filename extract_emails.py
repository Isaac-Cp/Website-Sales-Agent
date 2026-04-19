#!/usr/bin/env python3
"""
Simple email extraction script for existing leads.
Processes leads in database and extracts emails from their websites.
"""

import sqlite3
import sys
import time
import json
from scraper import Scraper
from database import DataManager


def init_scraper():
    """Create a headless Scraper instance and initialize the browser driver."""
    scraper = Scraper(headless=True)
    try:
        driver = scraper.get_driver()
        scraper.driver = driver
        return scraper
    except Exception as e:
        print(f"Failed to initialize browser driver: {e}")
        return None

def extract_emails_from_leads(limit=20):
    """Extract emails from existing leads in database."""
    print(f"Starting email extraction for {limit} leads...")

    scraper = init_scraper()
    if not scraper:
        print("Failed to setup scraper. Exiting.")
        return

    dm = DataManager()

    with sqlite3.connect('leads.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, business_name, website
            FROM leads
            WHERE website IS NOT NULL
            AND website != ''
            AND (email IS NULL OR email = '')
            AND COALESCE(status, 'scraped') NOT IN ('emailed', 'manual_queue', 'low_priority', 'no_contact')
            LIMIT ?
        ''', (limit,))
        leads = cur.fetchall()

    print(f"Found {len(leads)} leads to process for email extraction.")

    processed = 0
    emails_found = 0

    for lead_id, name, website in leads:
        print(f"[{processed+1}/{len(leads)}] Processing: {name} - {website}")

        try:
            email, audit_issues, signals = scraper.process_website(website)
            audit_text = "; ".join(audit_issues or [])
            service_offerings = ", ".join([str(item).strip() for item in (signals or {}).get('services', [])[:4] if str(item).strip()]) or None
            homepage_cta_quality = (
                "Homepage CTA appears unclear or buried." if (signals or {}).get('cta_visibility') == 'unclear' else
                "Homepage CTA appears visible and direct." if (signals or {}).get('cta_visibility') else None
            )
            lead_payload = {
                "business_name": name,
                "website": website,
                "email": email.strip() if email else None,
                "audit_issues": audit_text,
                "website_signals": signals or {},
                "service_offerings": service_offerings,
                "homepage_cta_quality": homepage_cta_quality,
                "service_pages": ", ".join(signals.get('service_pages', [])[:6]) if signals else None,
                "pricing_mention": signals.get('pricing_mention'),
                "booking_widget": signals.get('booking_widget'),
                "operating_hours": signals.get('operating_hours'),
                "location_count": signals.get('location_count'),
                "staff_count": signals.get('staff_count'),
                "business_size": signals.get('business_size'),
                "google_business_profile_status": signals.get('google_business_profile_status'),
                "review_velocity": signals.get('review_velocity'),
                "keyword_usage": ", ".join(signals.get('keyword_usage', [])[:8]) if signals else None,
                "secondary_emails": ", ".join(signals.get('secondary_emails', [])[:3]) if signals else None,
                "phone_numbers": ", ".join(signals.get('phone_numbers', [])[:3]) if signals else None,
                "whatsapp_links": ", ".join(signals.get('whatsapp_links', [])[:3]) if signals else None,
            }
            dm.save_lead(lead_payload)

            if email and email.strip():
                print(f"  ✓ Found email: {email}")
                emails_found += 1
            else:
                print("  ✗ No email found")
        except Exception as e:
            print(f"  ✗ Error processing {website}: {e}")

        processed += 1
        time.sleep(1)

    if getattr(scraper, 'driver', None):
        try:
            scraper.driver.quit()
        except Exception:
            pass

    print(f"\nCompleted! Processed {processed} leads, found {emails_found} emails.")

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    extract_emails_from_leads(limit)