import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import config


TERMINAL_STATUSES = {
    "completed",
    "sale_closed",
    "appointment_booked",
    "unsubscribed",
    "bounced",
    "blacklisted",
    "not_interested",
}


def _parse_json(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def _split_values(value, delimiter=","):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in text.split(delimiter) if item.strip()]


def _split_issues(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in text.split(";") if item.strip()]


def _utc_now_iso():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _rate(numerator, denominator):
    if not denominator:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 1)


def _truncate(text, limit=180):
    value = "" if text is None else str(text).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _row_dict(description, row):
    columns = [col[0] for col in description]
    return dict(zip(columns, row))


def _fetch_one_dict(cursor, query, params=()):
    cursor.execute(query, params)
    row = cursor.fetchone()
    if not row:
        return {}
    return _row_dict(cursor.description, row)


def _fetch_all_dicts(cursor, query, params=()):
    cursor.execute(query, params)
    rows = cursor.fetchall()
    description = cursor.description or []
    return [_row_dict(description, row) for row in rows]


def _count_where(cursor, query, params=()):
    cursor.execute(query, params)
    row = cursor.fetchone()
    if not row:
        return 0
    return _safe_int(row[0], 0)


def _coalesce_text(value, fallback="Unknown"):
    text = "" if value is None else str(value).strip()
    return text or fallback


def _sql_limit_clause(data_manager, size):
    if data_manager.is_postgres:
        return f" LIMIT {data_manager.placeholder}", (size,)
    return f" LIMIT {data_manager.placeholder}", (size,)


def _database_target_summary():
    if not getattr(config, "DATABASE_URL", None):
        db_path = Path(getattr(config, "DB_FILE", "leads.db"))
        return {"backend": "sqlite", "target": db_path.name}

    parsed = urlparse(config.DATABASE_URL)
    host = parsed.hostname or "unknown-host"
    db_name = parsed.path.rsplit("/", 1)[-1] if parsed.path else "database"
    return {"backend": "postgres", "target": f"{host}/{db_name}"}


def _database_size_bytes():
    if getattr(config, "DATABASE_URL", None):
        return None
    try:
        return Path(getattr(config, "DB_FILE", "leads.db")).stat().st_size
    except Exception:
        return None


def _email_window_state():
    start_text = getattr(config, "EMAIL_WINDOW_START", "00:00")
    end_text = getattr(config, "EMAIL_WINDOW_END", "23:59")
    now = dt.datetime.now().time()

    try:
        start_time = dt.datetime.strptime(start_text, "%H:%M").time()
        end_time = dt.datetime.strptime(end_text, "%H:%M").time()
    except Exception:
        return {"start": start_text, "end": end_text, "is_open": None}

    if start_time <= end_time:
        is_open = start_time <= now <= end_time
    else:
        is_open = now >= start_time or now <= end_time
    return {"start": start_text, "end": end_text, "is_open": is_open}


def _integration_summary():
    smtp_accounts = config.get_smtp_accounts()
    return {
        "smtp_accounts": len(smtp_accounts),
        "smtp_ready": bool(smtp_accounts),
        "imap_ready": bool(config.IMAP_HOST and config.IMAP_EMAIL and config.IMAP_PASSWORD),
        "groq": bool(getattr(config, "GROQ_API_KEY", None)),
        "openai": bool(getattr(config, "OPENAI_API_KEY", None)),
        "serpapi": bool(getattr(config, "SERPAPI_API_KEY", None)),
        "hunter": bool(getattr(config, "HUNTER_API_KEY", None)),
        "builtwith": bool(getattr(config, "BUILTWITH_API_KEY", None)),
        "proxycurl": bool(getattr(config, "PROXYCURL_API_KEY", None)),
        "yelp": bool(getattr(config, "YELP_API_KEY", None)),
        "pagespeed": bool(getattr(config, "PAGESPEED_API_KEY", None)),
        "capsolver": bool(getattr(config, "CAPSOLVER_API_KEY", None)),
    }


def _runtime_summary(boot_timestamp):
    database_summary = _database_target_summary()
    return {
        "service": "website-sales-agent",
        "mode": "web-dashboard",
        "booted_at": dt.datetime.utcfromtimestamp(boot_timestamp).replace(microsecond=0).isoformat() + "Z",
        "uptime_seconds": max(0, int(dt.datetime.utcnow().timestamp() - boot_timestamp)),
        "database": database_summary,
        "database_size_bytes": _database_size_bytes(),
        "dry_run": bool(getattr(config, "DRY_RUN", False)),
        "headless": bool(getattr(config, "HEADLESS", True)),
        "parallel_workers": _safe_int(getattr(config, "PARALLEL_WORKERS", 0), 0),
        "batch_size": _safe_int(getattr(config, "BATCH_SIZE", 0), 0),
        "max_daily_actions": _safe_int(getattr(config, "MAX_DAILY_ACTIONS", 0), 0),
        "max_domain_sends_per_day": _safe_int(getattr(config, "MAX_DOMAIN_SENDS_PER_DAY", 0), 0),
        "max_city_sends_per_day": _safe_int(getattr(config, "MAX_CITY_SENDS_PER_DAY", 0), 0),
        "max_persona_sends_per_day": _safe_int(getattr(config, "MAX_PERSONA_SENDS_PER_DAY", 0), 0),
        "default_tech": getattr(config, "DEFAULT_TECH", None),
        "queue_phone_only_leads": bool(getattr(config, "QUEUE_PHONE_ONLY_LEADS", False)),
        "validation_provider": getattr(config, "VALIDATION_PROVIDER", None),
        "email_window": _email_window_state(),
        "integrations": _integration_summary(),
        "execution_note": "This web service monitors stored bot activity. Scraping and sending still require the bot loop to run in a worker or manual session.",
        "log_file": getattr(config, "LOG_FILE", None),
    }


def _normalize_lead_row(row):
    website_signals = _parse_json(row.get("website_signals")) or {}
    sample_reviews = _parse_json(row.get("sample_reviews"))
    open_meta = _parse_json(row.get("open_meta"))

    normalized = {
        "id": row.get("id"),
        "business_name": row.get("business_name"),
        "website": row.get("website"),
        "email": row.get("email"),
        "phone": row.get("phone"),
        "city": row.get("city"),
        "niche": row.get("niche"),
        "status": row.get("status"),
        "sequence_stage": row.get("sequence_stage"),
        "lead_score": _safe_float(row.get("lead_score")),
        "opportunity_score": _safe_float(row.get("opportunity_score")),
        "pagespeed_score": _safe_float(row.get("pagespeed_score")),
        "rating": _safe_float(row.get("rating")),
        "review_count": _safe_int(row.get("review_count"), 0),
        "open_count": _safe_int(row.get("open_count"), 0),
        "follow_up_attempts": _safe_int(row.get("follow_up_attempts"), 0),
        "high_value": bool(row.get("high_value")),
        "blacklisted": bool(row.get("blacklisted")),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "next_action_due": row.get("next_action_due"),
        "last_email_type": row.get("last_email_type"),
        "last_persona": row.get("last_persona"),
        "last_hook_type": row.get("last_hook_type"),
        "review_sentiment": row.get("review_sentiment"),
        "homepage_cta_quality": row.get("homepage_cta_quality"),
        "local_market_signal": row.get("local_market_signal"),
        "google_business_profile_status": row.get("google_business_profile_status"),
        "pricing_mention": row.get("pricing_mention"),
        "booking_widget": row.get("booking_widget"),
        "operating_hours": row.get("operating_hours"),
        "business_size": row.get("business_size"),
        "staff_count": row.get("staff_count"),
        "location_count": row.get("location_count"),
        "audit_issues": _split_issues(row.get("audit_issues")),
        "services": _split_values(row.get("service_offerings")),
        "service_pages": _split_values(row.get("service_pages")),
        "competitors": _split_values(row.get("competitors")),
        "keyword_usage": _split_values(row.get("keyword_usage")),
        "secondary_emails": _split_values(row.get("secondary_emails")),
        "phone_numbers": _split_values(row.get("phone_numbers")),
        "whatsapp_links": _split_values(row.get("whatsapp_links")),
        "website_signals": website_signals,
        "sample_reviews": sample_reviews if isinstance(sample_reviews, list) else [],
        "open_meta": open_meta or {},
        "description": row.get("description"),
        "review_excerpt": row.get("review_excerpt"),
        "strategy": row.get("strategy"),
        "spf_status": row.get("spf_status"),
        "dmarc_status": row.get("dmarc_status"),
        "email_quality": row.get("email_quality"),
    }
    normalized["contact_summary"] = {
        "has_website": bool(normalized["website"]),
        "has_email": bool(normalized["email"]),
        "has_phone": bool(normalized["phone"]),
    }
    return normalized


def _event_summary(event_type, meta):
    meta = meta or {}
    snippets = []

    if meta.get("to"):
        snippets.append(f"To: {meta.get('to')}")
    if meta.get("subject"):
        snippets.append(f"Subject: {_truncate(meta.get('subject'), 90)}")
    if meta.get("persona"):
        snippets.append(f"Persona: {meta.get('persona')}")
    if meta.get("hook_type"):
        snippets.append(f"Hook: {meta.get('hook_type')}")
    if meta.get("score") is not None:
        snippets.append(f"Score: {meta.get('score')}")

    reply_intent = meta.get("reply_intent")
    if isinstance(reply_intent, dict):
        intent_label = reply_intent.get("intent") or reply_intent.get("label")
        if intent_label:
            snippets.append(f"Intent: {intent_label}")
    elif reply_intent:
        snippets.append(f"Intent: {reply_intent}")

    if meta.get("reason"):
        snippets.append(f"Reason: {_truncate(meta.get('reason'), 90)}")
    if meta.get("error"):
        snippets.append(f"Error: {_truncate(meta.get('error'), 90)}")
    if meta.get("from"):
        snippets.append(f"From: {meta.get('from')}")

    if not snippets and meta:
        first_key = sorted(meta.keys())[0]
        snippets.append(f"{first_key}: {_truncate(meta.get(first_key), 90)}")

    if not snippets:
        return event_type.replace("_", " ").title()

    return " | ".join(snippets[:3])


def _sort_named_counts(items, count_key="count"):
    return sorted(items, key=lambda item: item.get(count_key, 0), reverse=True)


def _attribution_rows(stats, limit=8):
    rows = []
    for label, values in (stats or {}).items():
        sent = _safe_int(values.get("sent"), 0)
        replies = _safe_int(values.get("replies"), 0)
        conversions = _safe_int(values.get("conversions"), 0)
        clicks = _safe_int(values.get("clicks"), 0)
        rows.append(
            {
                "label": label,
                "sent": sent,
                "replies": replies,
                "clicks": clicks,
                "conversions": conversions,
                "reply_rate": _rate(replies, sent),
                "conversion_rate": _rate(conversions, sent),
            }
        )
    return _sort_named_counts(rows, "sent")[:limit]


def build_dashboard_payload(data_manager, boot_timestamp, recent_limit=12, event_limit=18, due_limit=10, top_limit=8):
    connection = data_manager.get_connection()
    cursor = connection.cursor()
    columns = {name for name, _type in data_manager.get_lead_columns()}
    limit_clause, limit_params = _sql_limit_clause(data_manager, recent_limit)
    event_limit_clause, event_limit_params = _sql_limit_clause(data_manager, event_limit)
    due_limit_clause, due_limit_params = _sql_limit_clause(data_manager, due_limit)
    top_limit_clause, top_limit_params = _sql_limit_clause(data_manager, top_limit)

    try:
        total_leads = _count_where(cursor, "SELECT COUNT(*) FROM leads")
        with_website = _count_where(cursor, "SELECT COUNT(*) FROM leads WHERE website IS NOT NULL AND TRIM(website) != ''")
        with_email = _count_where(cursor, "SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND TRIM(email) != ''")
        with_phone = _count_where(cursor, "SELECT COUNT(*) FROM leads WHERE phone IS NOT NULL AND TRIM(phone) != ''")
        no_website = max(0, total_leads - with_website)
        high_value = _count_where(cursor, "SELECT COUNT(*) FROM leads WHERE high_value = 1") if "high_value" in columns else 0
        blacklisted = _count_where(cursor, "SELECT COUNT(*) FROM leads WHERE blacklisted = 1") if "blacklisted" in columns else 0
        parent_companies = _count_where(cursor, "SELECT COUNT(*) FROM parent_companies")
        due_followups_count = _count_where(
            cursor,
            """
            SELECT COUNT(*) FROM leads
            WHERE next_action_due IS NOT NULL
              AND next_action_due <= CURRENT_TIMESTAMP
              AND COALESCE(status, 'new') NOT IN ('completed', 'sale_closed', 'appointment_booked', 'unsubscribed', 'bounced', 'blacklisted', 'not_interested')
            """,
        )

        daily_actions = data_manager.count_daily_actions()
        daily_remaining = max(0, _safe_int(getattr(config, "MAX_DAILY_ACTIONS", 0), 0) - daily_actions)

        avg_lead_expr = "AVG(lead_score) AS avg_lead_score" if "lead_score" in columns else "NULL AS avg_lead_score"
        avg_query = (
            "SELECT AVG(pagespeed_score) AS avg_pagespeed, "
            "AVG(opportunity_score) AS avg_opportunity, "
            f"{avg_lead_expr} FROM leads"
        )
        avg_row = _fetch_one_dict(cursor, avg_query)
        avg_quality = {
            "pagespeed_score": _safe_float(avg_row.get("avg_pagespeed")),
            "opportunity_score": _safe_float(avg_row.get("avg_opportunity")),
            "lead_score": _safe_float(avg_row.get("avg_lead_score")) if "lead_score" in columns else None,
        }

        status_distribution = _fetch_all_dicts(
            cursor,
            """
            SELECT COALESCE(status, 'new') AS label, COUNT(*) AS count
            FROM leads
            GROUP BY COALESCE(status, 'new')
            ORDER BY count DESC
            """,
        )
        stage_distribution = _fetch_all_dicts(
            cursor,
            """
            SELECT COALESCE(sequence_stage, 'initial') AS label, COUNT(*) AS count
            FROM leads
            GROUP BY COALESCE(sequence_stage, 'initial')
            ORDER BY count DESC
            """,
        )
        top_cities = _fetch_all_dicts(
            cursor,
            f"""
            SELECT city AS label, COUNT(*) AS count
            FROM leads
            WHERE city IS NOT NULL AND TRIM(city) != ''
            GROUP BY city
            ORDER BY count DESC
            {top_limit_clause}
            """,
            top_limit_params,
        )
        top_niches = _fetch_all_dicts(
            cursor,
            f"""
            SELECT niche AS label, COUNT(*) AS count
            FROM leads
            WHERE niche IS NOT NULL AND TRIM(niche) != ''
            GROUP BY niche
            ORDER BY count DESC
            {top_limit_clause}
            """,
            top_limit_params,
        )

        recent_lead_rows = _fetch_all_dicts(
            cursor,
            f"SELECT * FROM leads ORDER BY updated_at DESC {limit_clause}",
            limit_params,
        )
        recent_leads = [_normalize_lead_row(row) for row in recent_lead_rows]

        due_followup_rows = _fetch_all_dicts(
            cursor,
            f"""
            SELECT * FROM leads
            WHERE next_action_due IS NOT NULL
              AND next_action_due <= CURRENT_TIMESTAMP
              AND COALESCE(status, 'new') NOT IN ('completed', 'sale_closed', 'appointment_booked', 'unsubscribed', 'bounced', 'blacklisted', 'not_interested')
            ORDER BY next_action_due ASC
            {due_limit_clause}
            """,
            due_limit_params,
        )
        due_followups = [_normalize_lead_row(row) for row in due_followup_rows]

        recent_event_rows = _fetch_all_dicts(
            cursor,
            f"""
            SELECT
                e.id,
                e.event_type,
                e.timestamp,
                e.meta,
                l.id AS lead_id,
                l.business_name,
                l.status,
                l.sequence_stage,
                l.city,
                l.niche
            FROM email_events e
            LEFT JOIN leads l ON l.id = e.lead_id
            ORDER BY e.timestamp DESC
            {event_limit_clause}
            """,
            event_limit_params,
        )
        recent_events = []
        for row in recent_event_rows:
            meta = _parse_json(row.get("meta")) or {}
            recent_events.append(
                {
                    "id": row.get("id"),
                    "event_type": row.get("event_type"),
                    "timestamp": row.get("timestamp"),
                    "lead_id": row.get("lead_id"),
                    "business_name": row.get("business_name"),
                    "status": row.get("status"),
                    "sequence_stage": row.get("sequence_stage"),
                    "city": row.get("city"),
                    "niche": row.get("niche"),
                    "summary": _event_summary(row.get("event_type"), meta),
                    "meta": meta,
                }
            )

        top_lead_order = "lead_score DESC, opportunity_score DESC, updated_at DESC" if "lead_score" in columns else "opportunity_score DESC, updated_at DESC"
        top_lead_rows = _fetch_all_dicts(
            cursor,
            f"""
            SELECT * FROM leads
            WHERE COALESCE(status, 'new') NOT IN ('blacklisted', 'bounced')
            ORDER BY {top_lead_order}
            {top_limit_clause}
            """,
            top_limit_params,
        )
        top_leads = [_normalize_lead_row(row) for row in top_lead_rows]

    finally:
        connection.close()

    event_counts = data_manager.get_persona_performance()
    sent_total = _safe_int(event_counts.get("sent"), 0)
    reply_total = _safe_int(event_counts.get("reply"), 0)
    open_total = _safe_int(event_counts.get("opened"), 0)
    click_total = _safe_int(event_counts.get("click"), 0)
    conversion_total = (
        _safe_int(event_counts.get("appointment_requested"), 0)
        + _safe_int(event_counts.get("appointment_booked"), 0)
        + _safe_int(event_counts.get("sale_closed"), 0)
        + _safe_int(event_counts.get("deal_closed"), 0)
    )
    risky_total = _safe_int(event_counts.get("unsubscribe"), 0) + _safe_int(event_counts.get("bounce"), 0)

    training_examples = []
    for subject, body, persona, strategy, insight, outcome_type in data_manager.get_top_performing_examples(limit=6):
        training_examples.append(
            {
                "subject": subject,
                "body_preview": _truncate(body, 220),
                "persona": persona,
                "strategy": strategy,
                "insight": insight,
                "outcome_type": outcome_type,
            }
        )

    payload = {
        "generated_at": _utc_now_iso(),
        "runtime": _runtime_summary(boot_timestamp),
        "overview": {
            "total_leads": total_leads,
            "with_website": with_website,
            "no_website": no_website,
            "with_email": with_email,
            "with_phone": with_phone,
            "high_value": high_value,
            "blacklisted": blacklisted,
            "parent_companies": parent_companies,
            "daily_actions": daily_actions,
            "daily_remaining": daily_remaining,
            "due_followups": due_followups_count,
        },
        "health": {
            "sent_total": sent_total,
            "opened_total": open_total,
            "click_total": click_total,
            "reply_total": reply_total,
            "conversion_total": conversion_total,
            "risk_total": risky_total,
            "open_rate": _rate(open_total, sent_total),
            "reply_rate": _rate(reply_total, sent_total),
            "conversion_rate": _rate(conversion_total, sent_total),
        },
        "quality": avg_quality,
        "pipeline": {
            "statuses": _sort_named_counts(status_distribution),
            "stages": _sort_named_counts(stage_distribution),
        },
        "distributions": {
            "cities": _sort_named_counts(top_cities),
            "niches": _sort_named_counts(top_niches),
        },
        "recent_leads": recent_leads,
        "due_followups": due_followups,
        "top_leads": top_leads,
        "recent_events": recent_events,
        "training_examples": training_examples,
        "attribution": {
            "personas": _attribution_rows(data_manager.get_conversion_attribution("persona")),
            "hooks": _attribution_rows(data_manager.get_conversion_attribution("hook_type")),
            "cities": _attribution_rows(data_manager.get_conversion_attribution("city"), limit=6),
            "niches": _attribution_rows(data_manager.get_conversion_attribution("niche"), limit=6),
        },
    }
    return payload


def get_dashboard_lead_detail(data_manager, lead_id):
    connection = data_manager.get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT * FROM leads WHERE id = {data_manager.placeholder}", (lead_id,))
        row = cursor.fetchone()
        if not row:
            return None
        lead = _normalize_lead_row(_row_dict(cursor.description, row))
    finally:
        connection.close()

    business_name = lead.get("business_name")
    timeline = []
    for item in data_manager.get_lead_timeline(business_name):
        meta = item.get("meta") or {}
        timeline.append(
            {
                "event": item.get("event"),
                "timestamp": item.get("timestamp"),
                "summary": _event_summary(item.get("event"), meta),
                "meta": meta,
            }
        )

    recent_outcomes = []
    for item in data_manager.get_recent_outcomes(business_name, limit=10):
        meta = item.get("meta") or {}
        recent_outcomes.append(
            {
                "type": item.get("type"),
                "timestamp": item.get("timestamp"),
                "summary": _event_summary(item.get("type"), meta),
                "meta": meta,
            }
        )

    last_generated = data_manager.get_last_event_meta(
        business_name,
        event_types=("email_generated", "email_send_attempt", "sent", "dry_preview"),
    )
    last_prompt = data_manager.get_last_event_meta(business_name, event_types=("prompt_payload",))

    return {
        "lead": lead,
        "timeline": timeline,
        "recent_personas": data_manager.get_recent_personas(business_name, limit=8),
        "recent_outcomes": recent_outcomes,
        "last_generated_email": {
            "subject": last_generated.get("subject"),
            "body_preview": _truncate(last_generated.get("body"), 500),
            "persona": last_generated.get("persona"),
            "hook_type": last_generated.get("hook_type"),
            "score": last_generated.get("score"),
            "to": last_generated.get("to"),
        },
        "last_prompt_payload": _truncate(last_prompt.get("prompt_payload"), 700) if last_prompt else None,
    }
