
import datetime
import time
import json
import argparse
import config
from database import DataManager
from mailer import Mailer, build_smtp_pool
import llm_helper
from core.pipeline import run_pipeline

def parse_args():
    parser = argparse.ArgumentParser(description="Send scheduled follow-ups for Sales Agent.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of follow-ups to send.")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually send emails.")
    return parser.parse_args()

def main():
    args = parse_args()
    if args.dry_run:
        config.DRY_RUN = True
        print("[DRY RUN] Mode enabled. No emails will be sent.")

    dm = DataManager()
    smtp_accounts = config.get_smtp_accounts()
    smtp_pool = build_smtp_pool(smtp_accounts)
    
    if not smtp_pool or not smtp_pool.mailers:
        print("[SMTP] No SMTP accounts configured. Stopping.")
        return

    # 1. Get leads due for follow-up
    conn = dm.get_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    placeholder = dm.placeholder
    
    query = f"""
        SELECT id, business_name, website, email, first_name, niche, city, sequence_stage, 
               follow_up_attempts, last_persona, last_hook_type, audit_issues, website_signals
        FROM leads 
        WHERE next_action_due <= {placeholder} 
        AND status NOT IN ('sale_closed', 'blacklisted', 'unsubscribed', 'bounced', 'interested', 'not_interested', 'stale')
        AND email IS NOT NULL
        ORDER BY next_action_due ASC
        LIMIT {placeholder}
    """
    
    cursor.execute(query, (now, args.limit))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No follow-ups due at this time.")
        return

    print(f"Found {len(rows)} follow-ups due. Processing...")

    for row in rows:
        lead_id, name, website, email, first_name, niche, city, stage, attempts, persona, hook, audit, signals = row
        
        print(f"\nProcessing follow-up for: {name} ({email}) - Stage: {stage}")
        
        # Determine next stage and generate email
        subject = ""
        body = ""
        
        try:
            # We use the existing sequence logic from log_action
            # sequence_stage: 'followup_1', 'followup_2', 'followup_final'
            
            if stage == 'followup_1':
                subject, body = llm_helper.generate_followup_1(name, first_name or "there", niche, city)
            elif stage == 'followup_2':
                subject, body = llm_helper.generate_followup_2(name, first_name or "there", niche, city)
            elif stage == 'followup_final' or stage == 'followup_3':
                subject, body = llm_helper.generate_followup_3(name, first_name or "there", niche, city)
            else:
                print(f"  -> Unknown stage '{stage}'. Skipping.")
                continue

            if not subject or not body:
                print(f"  -> Failed to generate follow-up email for {name}. Skipping.")
                continue

            # 2. Send the email
            mailer = smtp_pool.peek_mailer()
            if config.DRY_RUN:
                print(f"  -> [DRY RUN] Would send to {email}: {subject}")
                dm.record_email_event(name, "dry_preview", {"to": email, "subject": subject, "stage": stage})
            else:
                sent = smtp_pool.send_email(email, subject, body, preferred_mailer=mailer)
                if sent:
                    print(f"  -> Follow-up sent to {email}")
                    # Update lead state in DB
                    dm.log_action(name, "email_sent", meta={
                        "sequence_stage": stage,
                        "persona": persona,
                        "hook_type": hook
                    })
                else:
                    print(f"  -> Failed to send follow-up to {email}")

        except Exception as e:
            print(f"  -> Error processing follow-up for {name}: {e}")
            continue

        # Avoid aggressive sending
        time.sleep(2)

    print("\nFollow-up session finished.")

if __name__ == "__main__":
    main()
