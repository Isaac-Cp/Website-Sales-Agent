import sqlite3
import datetime
import config
import json
from typing import Optional, List, Any
try:
    from pydantic import BaseModel, validator
except Exception:
    BaseModel = object

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
                status TEXT DEFAULT 'new',
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
        parent_company_id: Optional[int] = None
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
    def lead_exists(self, business_name, website=None):
        """
        Check if a lead exists by website (strong match) or name (fuzzy match).
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

    def save_lead(self, lead_data):
        """Save a new lead to the database. Ignores duplicates silently."""
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
                "parent_company_id": lead_data.get("parent_company_id"),
            }

            cols = [
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
                "parent_company_id",
                "status",
            ]
            vals = [
                payload.get("business_name"),
                payload.get("website"),
                payload.get("email"),
                payload.get("phone"),
                payload.get("address"),
                payload.get("city"),
                payload.get("niche"),
                payload.get("rating", 0),
                payload.get("review_count", 0),
                payload.get("description"),
                payload.get("sample_reviews"),
                payload.get("strategy"),
                payload.get("audit_issues"),
                payload.get("parent_company_id"),
                "scraped",
            ]

            insert_sql = f"INSERT INTO leads ({', '.join(cols)}) VALUES ({', '.join([self.placeholder] * len(cols))})"
            if self.is_postgres:
                insert_sql += " ON CONFLICT (business_name, website) DO NOTHING"
            else:
                insert_sql = insert_sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")

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

    def log_action(self, business_name, action_type="email_sent"):
        """Log an action for daily limits and update lead status."""
        lead_id = self.get_lead_id(business_name)
        if not lead_id:
            return

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Add to log
            cursor.execute(f"INSERT INTO actions_log (lead_id, action_type) VALUES ({self.placeholder}, {self.placeholder})", (lead_id, action_type))

            # Update lead status
            new_status = 'emailed' if action_type == 'email_sent' else 'processed'
            cursor.execute(f"UPDATE leads SET status = {self.placeholder}, updated_at = CURRENT_TIMESTAMP WHERE id = {self.placeholder}", (new_status, lead_id))

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

    def lead_age_days_by_website(self, website):
        if not website:
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT created_at FROM leads WHERE website = {self.placeholder} ORDER BY created_at ASC LIMIT 1", (website,))
            row = cursor.fetchone()
            if not row or not row[0]:
                conn.close()
                return 0
            try:
                dt = datetime.datetime.fromisoformat(str(row[0]))
            except Exception:
                conn.close()
                return 0
            delta = datetime.datetime.now() - dt
            conn.close()
            return max(0, delta.days)
        except Exception:
            conn.close()
            return 0
