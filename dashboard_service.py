
import datetime as dt
import json
import os
import logging
from typing import Dict, List, Any
from database import DataManager
import config

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self, dm: DataManager):
        self.dm = dm
        self._cache = {}
        self._cache_expiry = 30 # seconds

    def _get_cached_data(self, key: str):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (dt.datetime.now() - timestamp).total_seconds() < self._cache_expiry:
                return data
        return None

    def _set_cached_data(self, key: str, data: Any):
        self._cache[key] = (data, dt.datetime.now())

    def get_stats_overview(self) -> Dict[str, Any]:
        """Get high-level statistics for the dashboard."""
        cached = self._get_cached_data("stats_overview")
        if cached: return cached

        try:
            conn = self.dm.get_connection()
            cursor = conn.cursor()
            
            # Total leads
            cursor.execute("SELECT COUNT(*) FROM leads")
            total_leads = cursor.fetchone()[0]
            
            # Leads by status
            cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            # Emails sent today
            today = dt.date.today().isoformat()
            cursor.execute("SELECT COUNT(*) FROM email_events WHERE event_type = 'sent' AND timestamp LIKE ?", (f"{today}%",))
            sent_today = cursor.fetchone()[0]
            
            # Success rate (replies / sent)
            cursor.execute("SELECT COUNT(*) FROM email_events WHERE event_type = 'sent'")
            total_sent = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM email_events WHERE event_type = 'reply'")
            total_replies = cursor.fetchone()[0]
            
            success_rate = (total_replies / total_sent * 100) if total_sent > 0 else 0
            
            conn.close()
            
            data = {
                "total_leads": total_leads,
                "status_distribution": status_counts,
                "sent_today": sent_today,
                "success_rate": round(success_rate, 2),
                "total_sent": total_sent,
                "total_replies": total_replies
            }
            self._set_cached_data("stats_overview", data)
            return data
        except Exception as e:
            logger.error(f"Error getting stats overview: {e}")
            return {}

    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent email events."""
        cached = self._get_cached_data(f"recent_activity_{limit}")
        if cached: return cached

        try:
            conn = self.dm.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT e.id, e.event_type, e.timestamp, e.meta, l.business_name 
                FROM email_events e
                JOIN leads l ON e.lead_id = l.id
                ORDER BY e.timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            activity = []
            for row in rows:
                activity.append({
                    "id": row[0],
                    "type": row[1],
                    "timestamp": row[2],
                    "meta": json.loads(row[3]) if row[3] else {},
                    "business_name": row[4]
                })
                
            conn.close()
            self._set_cached_data(f"recent_activity_{limit}", activity)
            return activity
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []

    def get_lead_funnel(self) -> List[Dict[str, Any]]:
        """Get lead progression through the funnel."""
        cached = self._get_cached_data("lead_funnel")
        if cached: return cached

        # Simple funnel representation
        stages = ["scraped", "audited", "emailed", "replied", "appointment_booked", "sale_closed"]
        funnel = []
        
        try:
            conn = self.dm.get_connection()
            cursor = conn.cursor()
            
            for stage in stages:
                if stage == "emailed":
                    # Special case: check status or events
                    cursor.execute("SELECT COUNT(*) FROM leads WHERE status IN ('emailed', 'followup_1', 'followup_2', 'followup_final')")
                elif stage == "replied":
                    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'interested' OR id IN (SELECT lead_id FROM email_events WHERE event_type = 'reply')")
                else:
                    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = ?", (stage,))
                
                count = cursor.fetchone()[0]
                funnel.append({"stage": stage, "count": count})
                
            conn.close()
            self._set_cached_data("lead_funnel", funnel)
            return funnel
        except Exception as e:
            logger.error(f"Error getting lead funnel: {e}")
            return []

    def get_daily_volume(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get email volume per day for the last N days."""
        cached = self._get_cached_data(f"daily_volume_{days}")
        if cached: return cached

        try:
            conn = self.dm.get_connection()
            cursor = conn.cursor()
            
            daily_data = []
            for i in range(days):
                date = (dt.date.today() - dt.timedelta(days=i)).isoformat()
                cursor.execute("SELECT COUNT(*) FROM email_events WHERE event_type = 'sent' AND timestamp LIKE ?", (f"{date}%",))
                count = cursor.fetchone()[0]
                daily_data.append({"date": date, "sent": count})
                
            conn.close()
            data = sorted(daily_data, key=lambda x: x["date"])
            self._set_cached_data(f"daily_volume_{days}", data)
            return data
        except Exception as e:
            logger.error(f"Error getting daily volume: {e}")
            return []
