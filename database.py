import sqlite3
import datetime
import config
import json
from typing import Optional, List, Any
try:
    from pydantic import BaseModel, validator
except Exception:
    BaseModel = object
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

class DataManager:
    """
    Manages lead data storage and retrieval using SQLite.
    Handles deduplication, status updates, and daily limit tracking.
    """
    def __init__(self, db_file=None):
        self.db_file = db_file if db_file else config.DB_FILE
        self.is_postgres = bool(getattr(config, "DATABASE_URL", None))
        self.placeholder = "%s" if self.is_postgres else "?"
        self._init_db()

    def get_connection(self):
        if self.is_postgres:
            import psycopg2

            return psycopg2.connect(config.DATABASE_URL)
        return sqlite3.connect(self.db_file)

    def _init_db(self):
        """Initialize the database tables if they doesn't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Handle SQLite vs Postgres differences
        auto_inc = "SERIAL" if self.is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        primary_key = "id " + auto_inc
        timestamp_default = "CURRENT_TIMESTAMP"

        # Leads Table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS leads (
                {primary_key if self.is_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"},
                business_name TEXT NOT NULL,
                website TEXT,
                email TEXT,
                first_name TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                niche TEXT,
                rating REAL,
                review_count INTEGER,
                description TEXT,
                sample_reviews TEXT,
                strategy TEXT,
                audit_issues TEXT,
                website_signals TEXT,
                service_offerings TEXT,
                review_excerpt TEXT,
                review_sentiment TEXT,
                local_market_signal TEXT,
                competitor_references TEXT,
                homepage_cta_quality TEXT,
                competitors TEXT,
                pagespeed_score REAL,
                opportunity_score REAL,
                open_count INTEGER DEFAULT 0,
                last_opened_at TIMESTAMP,
                open_meta TEXT,
                status TEXT DEFAULT 'new',
                sequence_stage TEXT DEFAULT 'initial',
                follow_up_attempts INTEGER DEFAULT 0,
                next_action_due TIMESTAMP,
                last_email_type TEXT,
                last_persona TEXT,
                last_hook_type TEXT,
                blacklisted BOOLEAN DEFAULT FALSE,
                bounced_at TIMESTAMP,
                parent_company_id INTEGER,
                created_at TIMESTAMP DEFAULT {timestamp_default},
                updated_at TIMESTAMP DEFAULT {timestamp_default},
                UNIQUE(business_name, website)
            )
        """)

        # Parent Companies
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS parent_companies (
                {primary_key if self.is_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"},
                parent_name TEXT,
                shared_website TEXT UNIQUE,
                business_count INTEGER DEFAULT 1,
                analyzed BOOLEAN DEFAULT FALSE,
                email_sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT {timestamp_default}
            )
        """)

        # Actions Log
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS actions_log (
                {primary_key if self.is_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"},
                lead_id INTEGER,
                action_type TEXT,
                timestamp TIMESTAMP DEFAULT {timestamp_default}
            )
        """)

        # Email Events
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS email_events (
                {primary_key if self.is_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"},
                lead_id INTEGER,
                event_type TEXT,
                meta TEXT,
                timestamp TIMESTAMP DEFAULT {timestamp_default}
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS training_examples (
                {primary_key if self.is_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"},
                lead_id INTEGER,
                subject TEXT,
                body TEXT,
                score REAL,
                tone TEXT,
                outcome_type TEXT,
                persona TEXT,
                strategy TEXT,
                insight TEXT,
                timestamp TIMESTAMP DEFAULT {timestamp_default}
            )
        """)

        if not self.is_postgres:
            for column_def in [
                ("first_name", "TEXT"),
                ("website_signals", "TEXT"),
                ("service_offerings", "TEXT"),
                ("review_excerpt", "TEXT"),
                ("review_sentiment", "TEXT"),
                ("local_market_signal", "TEXT"),
                ("competitor_references", "TEXT"),
                ("homepage_cta_quality", "TEXT"),
                ("competitors", "TEXT"),
                ("pagespeed_score", "REAL"),
                ("opportunity_score", "REAL"),
                ("spf_status", "TEXT"),
                ("dmarc_status", "TEXT"),
                ("email_quality", "TEXT"),
                ("service_pages", "TEXT"),
                ("pricing_mention", "TEXT"),
                ("booking_widget", "TEXT"),
                ("operating_hours", "TEXT"),
                ("location_count", "INTEGER"),
                ("staff_count", "INTEGER"),
                ("business_size", "TEXT"),
                ("google_business_profile_status", "TEXT"),
                ("review_velocity", "TEXT"),
                ("keyword_usage", "TEXT"),
                ("secondary_emails", "TEXT"),
                ("phone_numbers", "TEXT"),
                ("whatsapp_links", "TEXT"),
                ("duplicate_of_id", "INTEGER"),
                ("duplicate_reason", "TEXT"),
                ("open_count", "INTEGER DEFAULT 0"),
                ("last_opened_at", "TIMESTAMP"),
                ("open_meta", "TEXT"),
                ("sequence_stage", "TEXT"),
                ("follow_up_attempts", "INTEGER DEFAULT 0"),
                ("next_action_due", "TIMESTAMP"),
                ("last_email_type", "TEXT"),
                ("last_persona", "TEXT"),
                ("last_hook_type", "TEXT"),
                ("lead_score", "REAL"),
                ("high_value", "BOOLEAN DEFAULT FALSE"),
                ("blacklisted", "BOOLEAN DEFAULT FALSE"),
                ("bounced_at", "TIMESTAMP"),
            ]:
                try:
                    cursor.execute(f"ALTER TABLE leads ADD COLUMN {column_def[0]} {column_def[1]}")
                except Exception:
                    pass

        # Create indexes for faster queries (critical on free tier)
        # These speed up dashboard filters by 10-50x
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_city ON leads(city)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_niche ON leads(niche)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_updated_at ON leads(updated_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_next_action_due ON leads(next_action_due)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON email_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_lead_id ON email_events(lead_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_lead_id ON actions_log(lead_id)")
        except Exception:
            pass  # Indexes may already exist

        conn.commit()
        conn.close()
    class LeadModel(BaseModel):
        business_name: str
        website: Optional[str] = None
        email: Optional[str] = None
        phone: Optional[str] = None
        address: Optional[str] = None
        city: Optional[str] = None
        niche: Optional[str] = None
        rating: float = 0.0
        review_count: int = 0
        description: Optional[str] = None
        sample_reviews: Optional[str] = None
        strategy: Optional[str] = None
        audit_issues: Optional[str] = None
        website_signals: Optional[str] = None
        service_offerings: Optional[str] = None
        review_excerpt: Optional[str] = None
        review_sentiment: Optional[str] = None
        local_market_signal: Optional[str] = None
        competitor_references: Optional[str] = None
        homepage_cta_quality: Optional[str] = None
        pagespeed_score: Optional[float] = None
        opportunity_score: Optional[float] = None
        lead_score: Optional[float] = None
        high_value: Optional[bool] = False
        open_count: Optional[int] = 0
        last_opened_at: Optional[str] = None
        open_meta: Optional[str] = None
        sequence_stage: Optional[str] = None
        follow_up_attempts: Optional[int] = 0
        next_action_due: Optional[str] = None
        last_email_type: Optional[str] = None
        last_persona: Optional[str] = None
        last_hook_type: Optional[str] = None
        blacklisted: Optional[bool] = False
        bounced_at: Optional[str] = None
        competitors: Optional[str] = None
        parent_company_id: Optional[int] = None
        status: Optional[str] = None
        duplicate_of_id: Optional[int] = None
        duplicate_reason: Optional[str] = None
        spf_status: Optional[str] = None
        dmarc_status: Optional[str] = None
        email_quality: Optional[str] = None
        service_pages: Optional[str] = None
        pricing_mention: Optional[str] = None
        booking_widget: Optional[str] = None
        operating_hours: Optional[str] = None
        location_count: Optional[int] = 0
        staff_count: Optional[int] = 0
        business_size: Optional[str] = None
        google_business_profile_status: Optional[str] = None
        review_velocity: Optional[str] = None
        keyword_usage: Optional[str] = None
        secondary_emails: Optional[str] = None
        phone_numbers: Optional[str] = None
        whatsapp_links: Optional[str] = None

        @validator('*', pre=True)
        def normalize_text_fields(cls, v: Any):
            if v is None:
                return None
            if isinstance(v, (dict, list)):
                return json.dumps(v)
            return v

        @validator('phone', pre=True)
        def normalize_phone(cls, v: Any):
            if v is None:
                return None
            if isinstance(v, dict):
                return v.get('phone_number') or v.get('display')
            if isinstance(v, (list, tuple)):
                return v[0] if v else None
            return str(v)

        @validator('sample_reviews', pre=True)
        def ensure_json(cls, v: Any):
            if v is None:
                return None
            if isinstance(v, (list, tuple)):
                return json.dumps(v)
            return v

        @validator('website_signals', pre=True)
        def normalize_website_signals(cls, v: Any):
            if v is None:
                return None
            if isinstance(v, (dict, list)):
                return json.dumps(v)
            return v

        @validator('competitors', pre=True)
        def normalize_competitors(cls, v: Any):
            if v is None:
                return None
            if isinstance(v, list):
                return ", ".join(str(item).strip() for item in v if str(item).strip())
            return v

        @validator('competitor_references', pre=True)
        def normalize_competitor_references(cls, v: Any):
            if v is None:
                return None
            if isinstance(v, list):
                return ", ".join(str(item).strip() for item in v if str(item).strip())
            return v

        @validator('open_meta', pre=True)
        def normalize_open_meta(cls, v: Any):
            if v is None:
                return None
            if isinstance(v, (dict, list)):
                return json.dumps(v)
            return v
    def lead_exists(self, business_name, website=None):
        """
        Check if a lead exists by website (strong match) or name (exact name match).
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Strong check by Website
        if website:
            cursor.execute(f"SELECT id FROM leads WHERE website = {self.placeholder}", (website,))
            if cursor.fetchone():
                conn.close()
                return True

        # 2. Check by Name
        cursor.execute(f"SELECT id FROM leads WHERE business_name = {self.placeholder}", (business_name,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_lead_by_email(self, email):
        if not email:
            return None
        normalized = str(email).strip().lower()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM leads WHERE LOWER(email) = {self.placeholder}", (normalized,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_lead_by_website(self, website):
        if not website:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM leads WHERE website = {self.placeholder}", (website,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def find_duplicate_lead(self, lead_data):
        website = lead_data.get('website')
        email = lead_data.get('email')
        if website:
            existing_id = self.get_lead_by_website(website)
            if existing_id:
                return {"lead_id": existing_id, "reason": "website_match"}

        if email:
            existing_id = self.get_lead_by_email(email)
            if existing_id:
                return {"lead_id": existing_id, "reason": "email_match"}

        return None

    def _update_lead_record(self, lead_id, payload):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            update_cols = [
                "email",
                "first_name",
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
                "open_count",
                "last_opened_at",
                "open_meta",
                "status",
                "parent_company_id",
                "service_pages",
                "pricing_mention",
                "booking_widget",
                "operating_hours",
                "location_count",
                "staff_count",
                "business_size",
                "google_business_profile_status",
                "review_velocity",
                "keyword_usage",
                "secondary_emails",
                "phone_numbers",
                "whatsapp_links",
                "spf_status",
                "dmarc_status",
                "email_quality",
                "duplicate_reason",
            ]
            params = []
            for col in update_cols:
                val = payload.get(col)
                if isinstance(val, (dict, list)):
                    val = json.dumps(val)
                params.append(val)
            params.append(lead_id)
            set_clause = ", ".join(
                [f"{col} = COALESCE({self.placeholder}, {col})" for col in update_cols]
            )
            cursor.execute(
                f"UPDATE leads SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = {self.placeholder}",
                params,
            )
            conn.commit()
            print(f"[DB] Updated existing lead id={lead_id} (merged duplicate)")
        except Exception as e:
            print(f"[DB] Error updating duplicate lead: {e}")
        finally:
            conn.close()

    def save_lead(self, lead_data):
        """Save a new lead to the database. Ignores duplicates silently."""
        duplicate = self.find_duplicate_lead(lead_data)
        if duplicate and duplicate.get("lead_id"):
            lead_data["duplicate_reason"] = duplicate.get("reason")
            lead_data["duplicate_of_id"] = duplicate.get("lead_id")
            self._update_lead_record(duplicate["lead_id"], lead_data)
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            normalized = None
            try:
                if hasattr(self, "LeadModel") and issubclass(self.LeadModel, BaseModel):
                    normalized = self.LeadModel(**lead_data).dict()
            except Exception:
                normalized = None
            payload = normalized or {
                "business_name": lead_data.get("business_name"),
                "website": lead_data.get("website"),
                "email": lead_data.get("email"),
                "first_name": lead_data.get("first_name"),
                "phone": lead_data.get("phone"),
                "address": lead_data.get("address"),
                "city": lead_data.get("city"),
                "niche": lead_data.get("niche"),
                "rating": lead_data.get("rating", 0),
                "review_count": lead_data.get("review_count", 0),
                "description": lead_data.get("description"),
                "sample_reviews": lead_data.get("sample_reviews"),
                "strategy": lead_data.get("strategy"),
                "audit_issues": lead_data.get("audit_issues"),
                "website_signals": lead_data.get("website_signals"),
                "pagespeed_score": lead_data.get("pagespeed_score"),
                "opportunity_score": lead_data.get("opportunity_score"),
                "lead_score": lead_data.get("lead_score"),
                "high_value": lead_data.get("high_value"),
                "competitors": lead_data.get("competitors"),
                "sequence_stage": lead_data.get("sequence_stage"),
                "follow_up_attempts": lead_data.get("follow_up_attempts"),
                "next_action_due": lead_data.get("next_action_due"),
                "last_email_type": lead_data.get("last_email_type"),
                "last_persona": lead_data.get("last_persona"),
                "last_hook_type": lead_data.get("last_hook_type"),
                "blacklisted": lead_data.get("blacklisted"),
                "bounced_at": lead_data.get("bounced_at"),
                "parent_company_id": lead_data.get("parent_company_id"),
                "status": lead_data.get("status"),
            }

            cols = [
                "business_name",
                "website",
                "email",
                "first_name",
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
                "spf_status",
                "dmarc_status",
                "email_quality",
                "service_pages",
                "pricing_mention",
                "booking_widget",
                "operating_hours",
                "location_count",
                "staff_count",
                "business_size",
                "google_business_profile_status",
                "review_velocity",
                "keyword_usage",
                "secondary_emails",
                "phone_numbers",
                "whatsapp_links",
                "duplicate_of_id",
                "duplicate_reason",
                "open_count",
                "last_opened_at",
                "open_meta",
                "sequence_stage",
                "follow_up_attempts",
                "next_action_due",
                "last_email_type",
                "last_persona",
                "last_hook_type",
                "blacklisted",
                "bounced_at",
                "parent_company_id",
                "status",
            ]
            vals = []
            for col in cols:
                val = payload.get(col)
                if isinstance(val, (dict, list)):
                    val = json.dumps(val)
                vals.append(val)

            insert_sql = f"INSERT INTO leads ({', '.join(cols)}) VALUES ({', '.join([self.placeholder] * len(cols))})"
            if self.is_postgres:
                update_clause = ", ".join(
                    [
                        f"{col}=COALESCE(EXCLUDED.{col}, leads.{col})" if col != "status" else "status=COALESCE(EXCLUDED.status, leads.status)"
                        for col in cols if col not in ("business_name", "website")
                    ]
                )
                insert_sql += f" ON CONFLICT (business_name, website) DO UPDATE SET {update_clause}, updated_at=CURRENT_TIMESTAMP"
            else:
                update_clause = ", ".join(
                    [
                        f"{col}=COALESCE(excluded.{col}, leads.{col})" if col != "status" else "status=COALESCE(excluded.status, leads.status)"
                        for col in cols if col not in ("business_name", "website")
                    ]
                )
                insert_sql += f" ON CONFLICT(business_name, website) DO UPDATE SET {update_clause}, updated_at=CURRENT_TIMESTAMP"

            cursor.execute(insert_sql, vals)
            conn.commit()
            if cursor.rowcount > 0:
                print(f"[DB] Saved new lead: {lead_data.get('business_name')}")
        except Exception as e:
            print(f"[DB] Error saving lead: {e}")
        finally:
            conn.close()

            
    def get_lead_id(self, business_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM leads WHERE business_name = {self.placeholder}", (business_name,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None

    def log_action(self, business_name, action_type="email_sent", meta=None):
        """Log an action for daily limits and update lead status."""
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        def _format_timestamp(dt):
            return dt.strftime("%Y-%m-%d %H:%M:%S")

        def _get_followup_attempts(current_id):
            cursor.execute(f"SELECT follow_up_attempts FROM leads WHERE id = {self.placeholder}", (current_id,))
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else 0

        try:
            # Add to log
            cursor.execute(
                f"INSERT INTO actions_log (lead_id, action_type) VALUES ({self.placeholder}, {self.placeholder})",
                (lead_id, action_type),
            )

            now = datetime.datetime.utcnow()
            next_action_due = None
            sequence_stage = None
            follow_up_attempts = None
            last_email_type = None
            last_persona = None
            last_hook_type = None
            blacklisted = None
            bounced_at = None

            if isinstance(meta, dict):
                sequence_stage = meta.get("sequence_stage")
                last_email_type = meta.get("sequence_stage")
                last_persona = meta.get("persona") or meta.get("last_persona")
                last_hook_type = meta.get("hook_type") or meta.get("last_hook_type")

            if action_type == 'email_sent':
                current_stage = (sequence_stage or 'initial').lower()
                if current_stage == 'initial':
                    next_action_due = now + datetime.timedelta(days=getattr(config, 'FOLLOWUP_DELAY_DAYS', 3))
                    sequence_stage = 'followup_1'
                    follow_up_attempts = 0
                    new_status = 'emailed'
                elif current_stage == 'followup_1':
                    next_action_due = now + datetime.timedelta(days=getattr(config, 'FOLLOWUP_1_DELAY_DAYS', 5))
                    sequence_stage = 'followup_2'
                    follow_up_attempts = _get_followup_attempts(lead_id) + 1
                    new_status = 'followup_sent'
                elif current_stage == 'followup_2':
                    next_action_due = now + datetime.timedelta(days=getattr(config, 'FOLLOWUP_2_DELAY_DAYS', 7))
                    sequence_stage = 'followup_final'
                    follow_up_attempts = _get_followup_attempts(lead_id) + 1
                    new_status = 'followup_sent'
                elif current_stage == 'followup_final':
                    sequence_stage = 'completed'
                    follow_up_attempts = _get_followup_attempts(lead_id) + 1
                    new_status = 'completed'
                else:
                    next_action_due = now + datetime.timedelta(days=getattr(config, 'FOLLOWUP_DELAY_DAYS', 3))
                    sequence_stage = 'followup_1'
                    follow_up_attempts = _get_followup_attempts(lead_id)
                    new_status = 'emailed'
                last_email_type = current_stage
            elif action_type == 'opened':
                cursor.execute(f"SELECT status, sequence_stage FROM leads WHERE id = {self.placeholder}", (lead_id,))
                row = cursor.fetchone()
                current_status = row[0] if row else None
                stored_stage = row[1] if row and len(row) > 1 else None
                if current_status in ('replied', 'appointment_booked', 'sale_closed', 'bounced', 'interested', 'not_interested'):
                    new_status = current_status
                else:
                    new_status = 'opened'
                sequence_stage = stored_stage if stored_stage and stored_stage != 'initial' else 'followup_1'
                next_action_due = now + datetime.timedelta(days=getattr(config, 'OPENED_FOLLOWUP_DELAY_DAYS', 2))
                last_persona = last_persona or stored_stage
            elif action_type == 'reply':
                intent = None
                if isinstance(meta, dict):
                    intent = (meta.get('reply_intent') or {}).get('intent') if isinstance(meta.get('reply_intent'), dict) else meta.get('reply_intent')
                    if isinstance(intent, str):
                        intent = intent.upper().strip()
                if intent == 'YES':
                    new_status = 'interested'
                    sequence_stage = 'completed'
                elif intent == 'NO':
                    new_status = 'not_interested'
                    sequence_stage = 'completed'
                elif intent in ('LATER', 'OBJECTION', 'OTHER'):
                    new_status = 'needs_follow_up'
                    sequence_stage = sequence_stage if sequence_stage and sequence_stage.startswith('followup_') else 'followup_1'
                    next_action_due = now + datetime.timedelta(days=getattr(config, 'FOLLOWUP_DELAY_DAYS', 3))
                else:
                    new_status = 'replied'
                    sequence_stage = 'followup_1'
                    next_action_due = now + datetime.timedelta(days=getattr(config, 'FOLLOWUP_DELAY_DAYS', 3))
            elif action_type == 'appointment_requested':
                new_status = 'appointment_requested'
                sequence_stage = 'completed'
            elif action_type == 'appointment_booked':
                new_status = 'appointment_booked'
                sequence_stage = 'completed'
            elif action_type == 'deal_closed':
                new_status = 'sale_closed'
                sequence_stage = 'completed'
            elif action_type == 'sale_closed':
                new_status = 'sale_closed'
                sequence_stage = 'completed'
            elif action_type == 'click':
                new_status = 'clicked'
                sequence_stage = sequence_stage if sequence_stage and sequence_stage.startswith('followup_') else 'followup_1'
                next_action_due = now + datetime.timedelta(days=getattr(config, 'FOLLOWUP_DELAY_DAYS', 3))
            elif action_type == 'unsubscribe':
                new_status = 'unsubscribed'
                sequence_stage = 'completed'
                blacklisted = True
                next_action_due = None
            elif action_type == 'bounce':
                new_status = 'bounced'
                sequence_stage = 'completed'
                blacklisted = True
                bounced_at = now
            else:
                new_status = 'processed'

            if action_type == 'opened':
                cursor.execute(
                    f"UPDATE leads SET open_count = COALESCE(open_count, 0) + 1, last_opened_at = CURRENT_TIMESTAMP, open_meta = {self.placeholder}, status = {self.placeholder}, updated_at = CURRENT_TIMESTAMP WHERE id = {self.placeholder}",
                    (json.dumps(meta or {}), new_status, lead_id),
                )
                update_columns = []
                update_values = []
                if sequence_stage is not None:
                    update_columns.append(f"sequence_stage = {self.placeholder}")
                    update_values.append(sequence_stage)
                if next_action_due is not None:
                    update_columns.append(f"next_action_due = {self.placeholder}")
                    update_values.append(_format_timestamp(next_action_due))
                if last_persona is not None:
                    update_columns.append(f"last_persona = {self.placeholder}")
                    update_values.append(last_persona)
                if last_hook_type is not None:
                    update_columns.append(f"last_hook_type = {self.placeholder}")
                    update_values.append(last_hook_type)
                if update_columns:
                    query = f"UPDATE leads SET {', '.join(update_columns)}, updated_at = CURRENT_TIMESTAMP WHERE id = {self.placeholder}"
                    cursor.execute(query, (*update_values, lead_id))
            else:
                if new_status == 'opened':
                    cursor.execute(f"SELECT status FROM leads WHERE id = {self.placeholder}", (lead_id,))
                    current_status = cursor.fetchone()
                    current_status = current_status[0] if current_status else None
                    if current_status in ('replied', 'appointment_requested', 'appointment_booked', 'sale_closed', 'unsubscribed', 'bounced'):
                        new_status = current_status
                update_columns = [f"status = {self.placeholder}"]
                update_values = [new_status]
                if sequence_stage is not None:
                    update_columns.append(f"sequence_stage = {self.placeholder}")
                    update_values.append(sequence_stage)
                if isinstance(meta, dict) and meta.get("sequence_stage"):
                    update_columns.append(f"last_email_type = {self.placeholder}")
                    update_values.append(last_email_type)
                if next_action_due is not None:
                    update_columns.append(f"next_action_due = {self.placeholder}")
                    update_values.append(_format_timestamp(next_action_due))
                elif action_type in ('reply', 'bounce'):
                    update_columns.append("next_action_due = NULL")
                if follow_up_attempts is not None:
                    update_columns.append(f"follow_up_attempts = {self.placeholder}")
                    update_values.append(follow_up_attempts)
                if last_persona is not None:
                    update_columns.append(f"last_persona = {self.placeholder}")
                    update_values.append(last_persona)
                if last_hook_type is not None:
                    update_columns.append(f"last_hook_type = {self.placeholder}")
                    update_values.append(last_hook_type)
                if blacklisted is not None:
                    update_columns.append(f"blacklisted = {self.placeholder}")
                    update_values.append(1 if blacklisted else 0)
                if bounced_at is not None:
                    update_columns.append(f"bounced_at = {self.placeholder}")
                    update_values.append(_format_timestamp(bounced_at))
                query = f"UPDATE leads SET {', '.join(update_columns)}, updated_at = CURRENT_TIMESTAMP WHERE id = {self.placeholder}"
                cursor.execute(query, (*update_values, lead_id))

            conn.commit()
            print(f"[DB] Logged action '{action_type}' for {business_name}")
        except Exception as e:
            print(f"[DB] Error logging action: {e}")
        finally:
            conn.close()

    def count_daily_actions(self):
        """Count how many emails were sent TODAY."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Handle SQLite vs Postgres date differences
        date_expr = "timestamp::date = CURRENT_DATE" if self.is_postgres else "date(timestamp) = date('now')"
        query = f"SELECT count(*) FROM actions_log WHERE {date_expr} AND action_type = 'email_sent'"

        cursor.execute(query)
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def _today_date_expr(self):
        return "timestamp::date = CURRENT_DATE" if self.is_postgres else "date(timestamp) = date('now')"

    def count_daily_actions_for_domain(self, domain, action_type='email_sent'):
        if not domain:
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        date_expr = self._today_date_expr()
        if self.is_postgres:
            domain_expr = f"split_part(lower(email), '@', 2) = lower({self.placeholder})"
        else:
            domain_expr = f"lower(substr(email, instr(email, '@') + 1)) = lower({self.placeholder})"
        query = f"SELECT count(*) FROM actions_log al JOIN leads l ON al.lead_id = l.id WHERE {date_expr} AND action_type = {self.placeholder} AND {domain_expr}"
        cursor.execute(query, (action_type, domain))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def count_daily_actions_for_city(self, city, action_type='email_sent'):
        if not city:
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        date_expr = self._today_date_expr()
        query = f"SELECT count(*) FROM actions_log al JOIN leads l ON al.lead_id = l.id WHERE {date_expr} AND action_type = {self.placeholder} AND lower(coalesce(l.city, '')) = lower({self.placeholder})"
        cursor.execute(query, (action_type, city))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def count_daily_actions_for_persona(self, persona, event_type='sent'):
        if not persona:
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        date_expr = self._today_date_expr()
        query = f"SELECT meta FROM email_events WHERE event_type = {self.placeholder} AND {date_expr}"
        cursor.execute(query, (event_type,))
        rows = cursor.fetchall()
        conn.close()
        count = 0
        for row in rows:
            try:
                meta = json.loads(row[0] or "{}")
                if (meta.get('persona') or '').lower() == persona.lower():
                    count += 1
            except Exception:
                continue
        return count

    def blacklist_lead(self, business_name, reason=None):
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                f"UPDATE leads SET blacklisted = 1, status = 'bounced', bounced_at = {self.placeholder}, next_action_due = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = {self.placeholder}",
                (now, lead_id),
            )
            self.record_email_event(business_name, "blacklisted", {"reason": reason} if reason else {"reason": "bounce"})
            conn.commit()
        except Exception as e:
            print(f"[DB] Error blacklisting lead: {e}")
        finally:
            conn.close()

    def get_recent_personas(self, business_name, limit=5):
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return []

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT meta FROM email_events WHERE lead_id = {self.placeholder} AND event_type IN ('email_generated', 'email_send_attempt', 'sent', 'failed') ORDER BY timestamp DESC LIMIT {limit}",
            (lead_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        personas = []
        for row in rows:
            try:
                event_meta = json.loads(row[0] or "{}")
                persona = event_meta.get("persona")
                if persona:
                    personas.append(persona)
            except Exception:
                continue
        return personas

    def get_recent_outcomes(self, business_name, limit=8):
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return []

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT event_type, meta, timestamp FROM email_events WHERE lead_id = {self.placeholder} ORDER BY timestamp DESC LIMIT {limit}",
            (lead_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        outcomes = []
        for event_type, meta_json, ts in rows:
            try:
                meta = json.loads(meta_json or "{}")
            except Exception:
                meta = {}
            outcomes.append({"type": event_type, "meta": meta, "timestamp": ts})
        return outcomes

    def get_last_event_meta(self, business_name, event_types=None):
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return {}

        conn = self.get_connection()
        cursor = conn.cursor()
        params = [lead_id]
        query = f"SELECT meta FROM email_events WHERE lead_id = {self.placeholder}"
        if event_types:
            placeholders = ", ".join([self.placeholder] * len(event_types))
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_types)
        query += " ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return {}

        try:
            return json.loads(row[0] or "{}")
        except Exception:
            return {}

    def get_lead_columns(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        columns = []
        if self.is_postgres:
            cursor.execute(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'leads' ORDER BY ordinal_position"
            )
            rows = cursor.fetchall()
            columns = [(row[0], row[1]) for row in rows]
        else:
            cursor.execute("PRAGMA table_info(leads)")
            rows = cursor.fetchall()
            columns = [(row[1], row[2]) for row in rows]
        conn.close()
        return columns

    def get_daily_summary(self, days=1):
        conn = self.get_connection()
        cursor = conn.cursor()
        if self.is_postgres:
            date_expr = f"timestamp >= NOW() - INTERVAL '{days} days'"
        else:
            date_expr = f"date(timestamp) >= date('now', '-{days} day')"
        cursor.execute(
            f"SELECT action_type, count(*) FROM actions_log WHERE {date_expr} GROUP BY action_type"
        )
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def get_persona_performance(self, persona=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT event_type, meta FROM email_events")
        rows = cursor.fetchall()
        conn.close()

        counts = {"sent": 0, "opened": 0, "click": 0, "reply": 0, "appointment_requested": 0, "appointment_booked": 0, "sale_closed": 0, "deal_closed": 0, "unsubscribe": 0, "bounce": 0}
        for event_type, meta_text in rows:
            try:
                meta = json.loads(meta_text or "{}")
            except Exception:
                meta = {}
            event_persona = (meta.get("persona") or "").strip()
            if persona and event_persona != persona:
                continue
            if event_type in counts:
                counts[event_type] += 1
        return counts

    def record_conversion_event(self, business_name, event_type, meta=None):
        self.record_email_event(business_name, event_type, meta)

    def is_parent_company(self, website):
        """Check if a website is already registered as a parent company."""
        if not website:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM parent_companies WHERE shared_website = {self.placeholder}", (website,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_parent_company_id(self, website):
        """Get parent company ID by website."""
        if not website:
            return None

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM parent_companies WHERE shared_website = {self.placeholder}", (website,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def create_parent_company(self, website, business_name):
        """Create a new parent company entry for businesses sharing a website."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f'''
                INSERT INTO parent_companies (parent_name, shared_website, business_count)
                VALUES ({self.placeholder}, {self.placeholder}, 1)
            ''', (business_name, website))
            conn.commit()
            parent_id = cursor.lastrowid if not self.is_postgres else cursor.execute("SELECT LASTVAL()").fetchone()[0]
            # Actually for Postgres we should use RETURNING id
            if self.is_postgres:
                 # Redo with returning if possible, or just use another query
                 cursor.execute(f"SELECT id FROM parent_companies WHERE shared_website = {self.placeholder}", (website,))
                 parent_id = cursor.fetchone()[0]

            print(f"[DB] Created parent company: {business_name} ({website})")
            return parent_id
        except Exception as e:
            print(f"[DB] Error creating parent company: {e}")
            return None
        finally:
            conn.close()
    
    def get_business_name_by_email(self, email):
        if not email:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT business_name FROM leads WHERE email = {self.placeholder}", (email,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None

    def record_email_event(self, business_name, event_type, meta=None):
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"INSERT INTO email_events (lead_id, event_type, meta) VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder})",
                (lead_id, event_type, json.dumps(meta or {}))
            )
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()

    def record_training_example(
        self,
        business_name,
        subject,
        body,
        score,
        tone,
        outcome_type,
        persona=None,
        strategy_text=None,
        insight=None,
    ):
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                INSERT INTO training_examples (
                    lead_id, subject, body, score, tone, outcome_type, persona, strategy, insight
                ) VALUES (
                    {self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder},
                    {self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder},
                    {self.placeholder}
                )
                """,
                (
                    lead_id,
                    subject,
                    body,
                    score,
                    tone,
                    outcome_type,
                    persona,
                    strategy_text,
                    insight,
                ),
            )
            conn.commit()
        except Exception as e:
            print(f"[DB] Error recording training example: {e}")
        finally:
            conn.close()

    def set_training_outcome(self, business_name, outcome_type):
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                SELECT id FROM training_examples
                WHERE lead_id = {self.placeholder}
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (lead_id,),
            )
            row = cursor.fetchone()
            if not row:
                return

            cursor.execute(
                f"""
                UPDATE training_examples
                SET outcome_type = {self.placeholder}
                WHERE id = {self.placeholder}
                """,
                (outcome_type, row[0]),
            )
            conn.commit()
        except Exception as e:
            print(f"[DB] Error updating training outcome: {e}")
        finally:
            conn.close()
    
    def increment_parent_company_count(self, website):
        """Increment the business count for a parent company."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f'''
                UPDATE parent_companies 
                SET business_count = business_count + 1 
                WHERE shared_website = {self.placeholder}
            ''', (website,))
            conn.commit()
        except Exception as e:
            print(f"[DB] Error incrementing parent count: {e}")
        finally:
            conn.close()

    def mark_parent_company_emailed(self, website):
        """Mark a parent company as having been emailed."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f'''
                UPDATE parent_companies 
                SET email_sent = TRUE, analyzed = TRUE 
                WHERE shared_website = {self.placeholder}
            ''', (website,))
            conn.commit()
            print(f"[DB] Marked parent company as emailed: {website}")
        except Exception as e:
            print(f"[DB] Error marking parent emailed: {e}")
        finally:
            conn.close()

    def capture_successful_outreach(self, business_name):
        """Capture the successful email for training."""
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get the last email sent and its outcome
            cursor.execute(
                f"""
                SELECT meta, event_type, timestamp FROM email_events 
                WHERE lead_id = {self.placeholder} AND event_type IN ('sent', 'reply', 'click', 'appointment_requested', 'appointment_booked', 'sale_closed')
                ORDER BY timestamp DESC LIMIT 5
                """,
                (lead_id,)
            )
            rows = cursor.fetchall()
            
            # Find the 'sent' event that led to success
            sent_meta = {}
            outcome = "unknown"
            for event_type, meta_text, ts in rows:
                if event_type in ('reply', 'click', 'appointment_requested', 'appointment_booked', 'sale_closed'):
                    outcome = event_type
                if event_type == 'sent':
                    sent_meta = json.loads(meta_text or "{}")
                    break
            
            if sent_meta and sent_meta.get("body"):
                self.record_training_example(
                    business_name,
                    sent_meta.get("subject", ""),
                    sent_meta.get("body", ""),
                    100.0,
                    sent_meta.get("persona", "default"),
                    outcome,
                    persona=sent_meta.get("persona"),
                    strategy_text=sent_meta.get("strategy"),
                    insight=sent_meta.get("hook_type")
                )
                print(f"[DB] Captured successful outreach for {business_name} as training example.")
        except Exception as e:
            print(f"[DB] Error capturing success: {e}")
        finally:
            conn.close()

    def get_top_performing_examples(self, limit=10):
        """Get best subject/body pairs based on outcomes."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT subject, body, persona, strategy, insight, outcome_type 
            FROM training_examples 
            WHERE outcome_type IN ('reply', 'appointment_requested', 'appointment_booked', 'sale_closed')
            ORDER BY score DESC LIMIT {self.placeholder}
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_lead_timeline(self, business_name):
        """Reconstruct the event timeline for a lead."""
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return []
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT event_type, timestamp, meta FROM email_events WHERE lead_id = {self.placeholder} ORDER BY timestamp ASC",
            (lead_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        timeline = []
        for row in rows:
            timeline.append({
                "event": row[0],
                "timestamp": row[1],
                "meta": json.loads(row[2] or "{}")
            })
        return timeline

    def calculate_lead_score(self, lead_id):
        """
        Calculates a lead score (0-100) based on:
        - site issues (40%)
        - review quality (20%)
        - engagement/open behavior (30%)
        - performance/pagespeed (10%)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT audit_issues, rating, review_count, open_count, status, pagespeed_score FROM leads WHERE id = {self.placeholder}",
            (lead_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row: return 0.0
        
        audit_issues, rating, review_count, open_count, status, pagespeed = row
        score = 0.0
        
        # 1. Site issues (max 40)
        if audit_issues:
            issues_list = [i.strip() for i in str(audit_issues).split(";") if i.strip()]
            score += min(len(issues_list) * 10, 40)
        
        # 2. Low rating / Review quality (max 20)
        if rating and float(rating) < 4.0:
            score += 15
        if review_count and int(review_count) < 10:
            score += 5
            
        # 3. Engagement (max 30)
        if open_count:
            score += min(int(open_count) * 10, 30)
            
        # 4. PageSpeed (max 10)
        if pagespeed and float(pagespeed) < 0.5:
            score += 10
            
        return score

    def update_all_lead_scores(self):
        """Recalculate and update scores for all leads."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM leads")
        ids = [r[0] for r in cursor.fetchall()]
        for lid in ids:
            score = self.calculate_lead_score(lid)
            high_value = 1 if score >= 70 else 0
            cursor.execute(
                f"UPDATE leads SET lead_score = {self.placeholder}, high_value = {self.placeholder} WHERE id = {self.placeholder}",
                (score, high_value, lid)
            )
        conn.commit()
        conn.close()
        print(f"[DB] Updated scores for {len(ids)} leads.")

    def get_conversion_attribution(self, group_by="persona"):
        """Get conversion stats grouped by persona, hook, industry, or city."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Valid group_by options
        valid_cols = ("persona", "hook_type", "industry", "city", "niche")
        if group_by not in valid_cols and group_by != "persona":
            group_by = "persona"

        # We look at email_events for 'sent' vs conversion events
        cursor.execute("SELECT event_type, meta FROM email_events WHERE event_type IN ('sent', 'reply', 'click', 'appointment_requested', 'appointment_booked', 'sale_closed')")
        rows = cursor.fetchall()
        conn.close()
        
        stats = {}
        for event_type, meta_text in rows:
            try:
                meta = json.loads(meta_text or "{}")
            except:
                continue
            
            key = meta.get(group_by) or meta.get(f"last_{group_by}")
            if not key: continue
            
            if key not in stats:
                stats[key] = {"sent": 0, "conversions": 0, "replies": 0, "clicks": 0}
            
            if event_type == "sent":
                stats[key]["sent"] += 1
            elif event_type == "reply":
                stats[key]["replies"] += 1
                stats[key]["conversions"] += 1
            elif event_type == "click":
                stats[key]["clicks"] += 1
            elif event_type in ("appointment_requested", "appointment_booked", "sale_closed"):
                stats[key]["conversions"] += 1
        
        return stats

    def cleanup_stale_leads(self, days=30):
        """Mark leads as stale if no action for X days."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if self.is_postgres:
            date_expr = f"updated_at < NOW() - INTERVAL '{days} days'"
        else:
            date_expr = f"date(updated_at) < date('now', '-{days} day')"
            
        cursor.execute(f"UPDATE leads SET status = 'stale' WHERE {date_expr} AND status NOT IN ('sale_closed', 'blacklisted', 'unsubscribed')")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def get_leads_count(self, filters=None):
        """Get total count of leads matching filters - for pagination."""
        conn = self.get_connection()
        cursor = conn.cursor()
        where_clauses = []
        params = []
        
        if filters:
            if filters.get("status"):
                where_clauses.append("status = {}")
                params.append(filters["status"])
            if filters.get("city"):
                where_clauses.append("city = {}")
                params.append(filters["city"])
            if filters.get("niche"):
                where_clauses.append("niche = {}")
                params.append(filters["niche"])
        
        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        query = f"SELECT COUNT(*) FROM leads{where_sql}"
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_leads_paginated(self, offset=0, limit=50, filters=None, order_by="updated_at"):
        """Fetch paginated leads - key for free tier memory efficiency."""
        conn = self.get_connection()
        cursor = conn.cursor()
        where_clauses = []
        params = []
        
        if filters:
            if filters.get("status"):
                where_clauses.append("status = {}")
                params.append(filters["status"])
            if filters.get("city"):
                where_clauses.append("city = {}")
                params.append(filters["city"])
            if filters.get("niche"):
                where_clauses.append("niche = {}")
                params.append(filters["niche"])
        
        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        query = f"SELECT * FROM leads{where_sql} ORDER BY {order_by} DESC LIMIT {self.placeholder} OFFSET {self.placeholder}"
        
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) if isinstance(row, dict) else row for row in rows]

    def iter_leads(self, batch_size=100):
        """Generator function to iterate leads without loading all in memory."""
        total = self.get_leads_count()
        for offset in range(0, total, batch_size):
            for lead in self.get_leads_paginated(offset=offset, limit=batch_size):
                yield lead
