#!/usr/bin/env python3
import argparse
import json
from database import DataManager

EXPECTED_LEAD_COLUMNS = [
    "id",
    "business_name",
    "website",
    "email",
    "phone",
    "address",
    "city",
    "niche",
    "rating",
    "review_count",
    "description",
    "sample_reviews",
    "strategy",
    "audit_issues",
    "website_signals",
    "service_offerings",
    "review_excerpt",
    "review_sentiment",
    "local_market_signal",
    "competitor_references",
    "homepage_cta_quality",
    "competitors",
    "pagespeed_score",
    "opportunity_score",
    "lead_score",
    "high_value",
    "open_count",
    "last_opened_at",
    "open_meta",
    "status",
    "sequence_stage",
    "follow_up_attempts",
    "next_action_due",
    "last_email_type",
    "last_persona",
    "last_hook_type",
    "blacklisted",
    "bounced_at",
    "parent_company_id",
    "created_at",
    "updated_at",
]

EXPECTED_TABLES = [
    "leads",
    "parent_companies",
    "actions_log",
    "email_events",
    "training_examples",
]


def print_columns(dm):
    columns = dm.get_lead_columns()
    print("Lead table columns:")
    for name, dtype in columns:
        print(f"  - {name} ({dtype})")
    return [name for name, _ in columns]


def verify_columns(dm):
    existing = set(print_columns(dm))
    missing = [col for col in EXPECTED_LEAD_COLUMNS if col not in existing]
    if missing:
        print("\nMissing lead columns:")
        for col in missing:
            print(f"  - {col}")
    else:
        print("\nAll expected lead columns are present.")
    return missing


def print_summary(dm, days=1):
    summary = dm.get_daily_summary(days=days)
    print(f"\nDaily actions summary (last {days} day{'s' if days != 1 else ''}):")
    for action, count in summary.items():
        print(f"  - {action}: {count}")


def print_persona_performance(dm, persona=None):
    perf = dm.get_persona_performance(persona=persona)
    print(f"\nPersona performance{' for ' + persona if persona else ''}:")
    for event_type, count in perf.items():
        print(f"  - {event_type}: {count}")


def print_recent_leads(dm, limit=5):
    conn = dm.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, business_name, website, email, status, audit_issues, website_signals FROM leads ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()

    print(f"\nMost recent {limit} leads:")
    for row in rows:
        print(json.dumps({
            "id": row[0],
            "business_name": row[1],
            "website": row[2],
            "email": row[3],
            "status": row[4],
            "audit_issues": row[5],
            "website_signals": row[6],
        }, indent=2, default=str))


def repair_missing_defaults(dm):
    conn = dm.get_connection()
    cursor = conn.cursor()
    updates = [
        ("UPDATE leads SET status = 'new' WHERE status IS NULL", []),
        ("UPDATE leads SET sequence_stage = 'initial' WHERE sequence_stage IS NULL", []),
        ("UPDATE leads SET follow_up_attempts = 0 WHERE follow_up_attempts IS NULL", []),
        ("UPDATE leads SET blacklisted = 0 WHERE blacklisted IS NULL", []),
        ("UPDATE leads SET lead_score = 0 WHERE lead_score IS NULL", []),
        ("UPDATE leads SET high_value = 0 WHERE high_value IS NULL", []),
    ]
    for sql, params in updates:
        cursor.execute(sql, params)
    conn.commit()
    conn.close()
    print("Repaired missing lead defaults: status, sequence_stage, follow_up_attempts, blacklisted.")


def cleanup_stale_leads(dm, days=90):
    conn = dm.get_connection()
    cursor = conn.cursor()
    if dm.is_postgres:
        age_clause = f"updated_at <= NOW() - INTERVAL '{days} days'"
    else:
        age_clause = f"date(updated_at) <= date('now', '-{days} days')"
    cursor.execute(
        f"UPDATE leads SET status = 'low_priority', next_action_due = NULL WHERE {age_clause} "
        "AND COALESCE(status, 'new') IN ('new', 'emailed', 'followup_sent', 'opened', 'needs_follow_up')"
    )
    count = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"Cleaned up {count} stale lead(s) not updated in {days} days.")


def main():
    parser = argparse.ArgumentParser(description="Verify leads database schema and event tracking.")
    parser.add_argument("--migrate", action="store_true", help="Apply schema migrations to the leads database.")
    parser.add_argument("--check", action="store_true", help="Check the leads schema and print missing columns.")
    parser.add_argument("--fix-missing", action="store_true", help="Repair missing lead default values.")
    parser.add_argument("--cleanup-stale", action="store_true", help="Mark stale leads as low_priority.")
    parser.add_argument("--stale-days", type=int, default=90, help="Number of days before a lead is considered stale.")
    parser.add_argument("--summary", action="store_true", help="Show a daily actions summary.")
    parser.add_argument("--persona", type=str, help="Show persona performance counts.")
    parser.add_argument("--recent", type=int, default=5, help="Show recent lead records.")
    args = parser.parse_args()

    dm = DataManager()

    if args.migrate:
        print("Applying migrations and ensuring schema is up to date...")
        dm._init_db()

    if args.check or args.migrate:
        print("\nChecking leads table schema...")
        missing = verify_columns(dm)
        if missing and not args.migrate:
            print("\nHint: run with --migrate to add missing columns.")

    if args.fix_missing:
        print("\nRepairing missing lead defaults...")
        repair_missing_defaults(dm)

    if args.cleanup_stale:
        print(f"\nCleaning up stale leads older than {args.stale_days} days...")
        cleanup_stale_leads(dm, days=args.stale_days)

    if args.summary:
        print_summary(dm)

    if args.persona is not None:
        print_persona_performance(dm, persona=args.persona)
    else:
        print_persona_performance(dm)

    if args.recent:
        print_recent_leads(dm)

    if not (args.check or args.summary or args.persona or args.recent or args.migrate or args.fix_missing or args.cleanup_stale):
        parser.print_help()


if __name__ == "__main__":
    main()
