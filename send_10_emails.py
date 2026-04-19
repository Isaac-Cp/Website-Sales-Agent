"""
send_10_emails.py
-----------------
Sends up to 10 real sales emails to leads already stored in leads.db.
Uses the existing Mailer + llm_helper + config infrastructure.
Run with: python send_10_emails.py
"""
import sys
import sqlite3
import time
import random
import json

print("--- SEND 10 EMAILS STARTING ---")

# try:
#     sys.stdout.reconfigure(encoding="utf-8")
# except Exception:
#     pass

print("--- SYS STDOUT RECONFIGURED (skipped) ---")

import config
from mailer import build_smtp_pool
import llm_helper

TARGET_COUNT = 10
DB_FILE = "leads.db"

# ── 1. Load SMTP accounts ────────────────────────────────────────────────────
smtp_accounts = config.get_smtp_accounts()
if not smtp_accounts:
    print("[ERROR] No SMTP accounts found in .env. Aborting.")
    sys.exit(1)

smtp_pool = build_smtp_pool(smtp_accounts)
mailers = list(smtp_pool.mailers)
print(f"[SMTP] Loaded {len(mailers)} SMTP account(s).")

# ── 2. Test first connection ─────────────────────────────────────────────────
print("[SMTP] Testing connection...")
working_mailer = smtp_pool.get_working_mailer(test_login=True)
if not working_mailer:
    print("[SMTP] Connection test FAILED. Check credentials in .env and retry.")
    sys.exit(1)

# ── 3. Fetch candidate leads from DB ────────────────────────────────────────
conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, business_name, email, phone, website, niche, city, strategy,
           audit_issues, description, rating, review_count, sample_reviews,
           website_signals, pagespeed_score, opportunity_score, competitors,
           service_offerings, review_excerpt, review_sentiment,
           local_market_signal, competitor_references, homepage_cta_quality,
           open_count, last_opened_at, status, sequence_stage, follow_up_attempts,
           next_action_due, last_persona, last_hook_type, blacklisted
    FROM leads
    WHERE email IS NOT NULL
      AND email != ''
      AND email NOT LIKE 'wght@%'
      AND email NOT LIKE 'aos@%'
      AND COALESCE(sequence_stage, 'initial') = 'initial'
      AND COALESCE(status, 'scraped') NOT IN ('emailed', 'manual_queue', 'low_priority', 'no_contact', 'not_interested', 'bounced', 'appointment_booked', 'sale_closed', 'blacklisted', 'completed')
      AND (next_action_due IS NULL OR next_action_due <= datetime('now'))
    LIMIT 50
""")
candidates = [dict(row) for row in cur.fetchall()]
conn.close()

print(f"[DB] Found {len(candidates)} candidate lead(s) with emails not yet sent.")

if not candidates:
    print("[INFO] No unsent leads with emails in the database.")
    print("       Run the main scraper first to populate leads, then rerun this script.")
    sys.exit(0)

# ── 4. Send loop ─────────────────────────────────────────────────────────────
from database import DataManager
dm = DataManager()

def get_unique_emailed_today():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT count(DISTINCT lead_id) FROM actions_log WHERE action_type = 'email_sent' AND date(timestamp) = date('now')")
    count = cur.fetchone()[0]
    conn.close()
    return count

unique_daily_count = get_unique_emailed_today()
print(f"Unique businesses emailed today: {unique_daily_count}")

sent_count = 0

for lead in candidates:
    if unique_daily_count + sent_count >= 25:
        print("Reached target of 25 unique businesses emailed today. Stopping.")
        break

    if sent_count >= TARGET_COUNT:
        break

    name        = lead["business_name"]
    email       = lead["email"]
    phone       = lead["phone"]
    website     = lead["website"]
    niche       = lead["niche"] or "local business"
    city        = lead["city"] or ""
    strategy    = lead["strategy"] or "audit"
    email_domain = email.split("@")[-1].lower() if email and "@" in email else ""
    if email_domain in config.BLACKLISTED_DOMAINS or email.lower() in config.BLACKLISTED_EMAILS:
        print(f"Skipping blacklisted lead: {name} <{email}>")
        continue
    if email_domain and dm.count_daily_actions_for_domain(email_domain) >= config.MAX_DOMAIN_SENDS_PER_DAY:
        print(f"Skipping {name}: reached daily domain throttle for {email_domain}.")
        continue
    if city and dm.count_daily_actions_for_city(city) >= config.MAX_CITY_SENDS_PER_DAY:
        print(f"Skipping {name}: reached daily city throttle for {city}.")
        continue
    last_persona = lead.get("last_persona")
    if last_persona and dm.count_daily_actions_for_persona(last_persona) >= config.MAX_PERSONA_SENDS_PER_DAY:
        print(f"Skipping {name}: reached daily persona throttle for {last_persona}.")
        continue
    audit_raw   = lead["audit_issues"] or ""
    description = lead["description"] or ""
    rating      = lead["rating"] or 0
    review_count = lead["review_count"] or 0
    reviews_raw = lead["sample_reviews"] or ""
    website_signals_raw = lead["website_signals"] or ""
    page_speed_score = lead["pagespeed_score"]
    opportunity_score = lead["opportunity_score"]
    competitors_raw = lead["competitors"] or ""

    audit_issues = [i.strip() for i in audit_raw.split(";") if i.strip()]
    reviews = []
    if reviews_raw:
        try:
            parsed_reviews = json.loads(reviews_raw)
            if isinstance(parsed_reviews, list):
                reviews = [str(item).strip() for item in parsed_reviews if str(item).strip()]
            elif parsed_reviews:
                reviews = [str(parsed_reviews).strip()]
        except Exception:
            reviews = [str(reviews_raw).strip()]

    try:
        website_signals = json.loads(website_signals_raw) if website_signals_raw else {}
    except Exception:
        website_signals = {}
    competitors = [item.strip() for item in competitors_raw.split(",") if item.strip()]
    service_offerings = lead.get("service_offerings") or ", ".join([str(item).strip() for item in website_signals.get("services", [])[:4] if str(item).strip()])
    review_snippet = reviews[0] if reviews else ""
    review_excerpt = lead.get("review_excerpt") or review_snippet
    review_sentiment = lead.get("review_sentiment") or (f"{rating}-star average from {review_count} reviews" if rating and review_count else (
        f"{rating}-star average" if rating else (f"{review_count} reviews" if review_count else "")
    ))
    local_market_signal = lead.get("local_market_signal") or (
        f"Local customers around {city or 'your area'} are likely comparing {', '.join(competitors[:3])}." if competitors else (
            f"In {city}, nearby businesses are often chosen by whoever makes the first message easiest to act on." if city else ""
        )
    )
    competitor_references = lead.get("competitor_references") or ", ".join(competitors[:4])
    homepage_cta_quality = lead.get("homepage_cta_quality") or (
        "Homepage CTA appears unclear or buried." if website_signals.get("cta_visibility") == "unclear" else "Homepage CTA appears visible and direct." if website_signals.get("cta_visibility") else ""
    )
    past_outcomes = dm.get_recent_outcomes(name)
    recent_personas = dm.get_recent_personas(name)
    website_issue = audit_issues[0] if audit_issues else ""
    good_fit_reason = (
        f"Because {name} already has local momentum in {city}, this outreach can help turn more Maps interest into booked work."
        if city else f"Because {name} already has local momentum, this outreach can help turn more Maps interest into booked work."
    )
    unique_value = (
        f"Helping {name} convert Google Maps visits into booked jobs with a single website or listing improvement."
        if website else f"Helping {name} capture local demand even without a website by making the first contact path clearer and faster."
    )

    sequence_stage = (lead.get("sequence_stage") or "initial").lower()
    is_followup = sequence_stage in ("followup_1", "followup_2", "followup_final")
    hook_type = lead.get("last_hook_type") or "followup"
    persona = lead.get("last_persona") or "followup"
    provider = "followup" if is_followup else "llm"
    subject = None
    body = None
    meta_sequence_stage = sequence_stage

    lead_context = {
        "business_name": name,
        "first_name": None,
        "industry": niche,
        "city": city,
        "lead_type": "has_website" if website else "no_website",
        "website": website,
        "email": email,
        "phone": phone,
        "rating": rating,
        "review_count": review_count,
        "description": description,
        "audit_issues": audit_issues,
        "reviews": reviews,
        "review_snippet": review_snippet,
        "review_sentiment": review_sentiment,
        "service_offerings": service_offerings,
        "review_excerpt": review_excerpt,
        "local_market_signal": local_market_signal,
        "competitor_references": competitor_references,
        "homepage_cta_quality": homepage_cta_quality,
        "website_issue": website_issue,
        "good_fit_reason": good_fit_reason,
        "unique_value": unique_value,
        "competitors": competitors,
        "website_signals": website_signals,
        "pagespeed_score": page_speed_score,
        "opportunity_score": opportunity_score,
        "open_count": lead.get("open_count") or 0,
        "last_opened_at": lead.get("last_opened_at"),
        "past_outcomes": past_outcomes,
        "persona_history": recent_personas,
    }

    if is_followup:
        print(f"\n[{sent_count+1}/{TARGET_COUNT}] Preparing follow-up email to: {name} <{email}>")
        if sequence_stage == "followup_1":
            subject, body = llm_helper.generate_followup_1(name, None, niche, city, secondary_observation=website_issue)
        elif sequence_stage == "followup_2":
            subject, body = llm_helper.generate_followup_2(name, None, niche, city)
        else:
            subject, body = llm_helper.generate_followup_3(name, None, niche, city)
        if not body.strip():
            print(f"  [FOLLOWUP] Follow-up generation failed for stage {sequence_stage}. Skipping lead.")
            dm.record_email_event(name, "followup_generation_failed", {"sequence_stage": sequence_stage})
            continue
        dm.record_email_event(name, "email_generated", {
            "provider": provider,
            "persona": persona,
            "hook_type": hook_type,
            "sequence_stage": sequence_stage,
            "subject": subject,
            "industry": niche,
            "location": city,
        })
    else:
        print(f"\n[{sent_count+1}/{TARGET_COUNT}] Preparing email to: {name} <{email}>")
        print(f"  [LLM] Generating content for {name}...")
        dm.record_email_event(name, "prompt_payload", {"prompt_payload": lead_context})
        outreach_result = None
        provider = "unknown"
        persona = "unknown"
        for attempt in range(3):
            try:
                outreach_result = llm_helper.generate_maps_cold_email(lead_context)
                provider = outreach_result.get("provider") or "unknown"
                persona = outreach_result.get("persona") or "unknown"
                hook_type = outreach_result.get("hook_type") or "cold"
                subject = outreach_result.get("subject") or (f"Quick note about {name}" if website else f"Quick idea for {name}")
                body = outreach_result.get("email") or ""
                if not body.strip():
                    raise ValueError("LLM returned an empty email body")
                print(f"  [LLM] provider={provider} persona={persona}")
                print(f"  [LLM] Content generated successfully.")
                dm.record_email_event(name, "persona_selected", {"provider": provider, "persona": persona, "lead_type": "has_website" if website else "no_website"})
                dm.record_email_event(name, "email_generated", {
                    "provider": provider,
                    "persona": persona,
                    "subject": subject,
                    "lead_type": "has_website" if website else "no_website",
                    "hook_type": hook_type,
                    "sequence_stage": "initial",
                    "industry": niche,
                    "location": city,
                })
                break
            except Exception as e:
                if attempt < 2:
                    print(f"  [LLM] generation failed attempt {attempt+1}/3: {e}. Retrying...")
                    time.sleep(2)
                    continue
                error_type = type(e).__name__
                print(f"  [LLM] Generation failed ({error_type}): {e}. Keeping lead for retry later.")
                dm.record_email_event(name, "llm_generation_failed", {"error": str(e), "attempts": 3})
                outreach_result = None
        if outreach_result is None:
            continue

        quality_result = llm_helper.evaluate_structured_email_quality(body, lead_context, bool(website), persona_name=persona)
        if quality_result.get("issues"):
            print(f"  [LLM] Quality warnings: {quality_result.get('issues')}")
            dm.record_email_event(name, "llm_quality_warning", {
                "provider": provider,
                "persona": persona,
                "score": quality_result.get("score"),
                "issues": quality_result.get("issues"),
            })

    # ── Pick SMTP account (round-robin) ────────────────────────────────────
    mailer = smtp_pool.peek_mailer() or mailers[0]

    print(f"  Subject : {subject}")
    print(f"  From    : {mailer.email}")

    # ── Send ───────────────────────────────────────────────────────────────
    # We do a local validation without SMTP probe to avoid hangs in sandbox
    v_res = mailer.assess_email(email, smtp_probe=False, allow_risky=True, check_catch_all=False)
    if v_res.get("classification") == "INVALID":
        print(f"  [VALIDATOR] Email marked INVALID (reasons: {v_res.get('reasons', [])}). Skipping.")
        dm.record_email_event(name, "email_validation_failed", {"to": email, "classification": v_res.get("classification"), "reasons": v_res.get("reasons", [])})
        continue
    sent = smtp_pool.send_email(
        email,
        subject,
        body,
        validation_result=v_res,
        preferred_mailer=mailer,
        retries_per_account=1,
    )

    dm.record_email_event(name, "email_send_attempt", {"to": email, "provider": provider, "persona": persona, "hook_type": hook_type, "industry": niche, "location": city, "sent": bool(sent)})

    if sent:
        sent_count += 1
        dm.record_email_event(name, "sent", {
            "to": email,
            "provider": provider,
            "persona": persona,
            "hook_type": hook_type,
            "industry": niche,
            "location": city,
        })
        dm.log_action(name, "email_sent", {
            "sequence_stage": meta_sequence_stage,
            "persona": persona,
            "hook_type": hook_type,
        })
        print(f"  [OK] Sent ({sent_count}/{TARGET_COUNT})")

        # Small human-like delay between sends (2–5 s)
        if sent_count < TARGET_COUNT:
            delay = random.uniform(2, 5)
            print(f"  Waiting {delay:.1f}s before next send...")
            time.sleep(delay)
    else:
        dm.record_email_event(name, "failed", {
            "to": email,
            "provider": provider,
            "persona": persona,
            "hook_type": hook_type,
            "industry": niche,
            "location": city,
        })
        print(f"  [FAIL] Could not send to {email}. Moving to next lead.")

# ── 5. Summary ───────────────────────────────────────────────────────────────
print("\n" + "="*60)
print(f"  DONE - Sent {sent_count} / {TARGET_COUNT} emails.")
print("="*60)
