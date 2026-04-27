
import unittest
from unittest.mock import MagicMock, patch
import json
import datetime as dt
from dashboard_service import DashboardService

class TestDashboardService(unittest.TestCase):
    def setUp(self):
        self.mock_dm = MagicMock()
        self.service = DashboardService(self.mock_dm)

    def test_stats_overview_caching(self):
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        self.mock_dm.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchone.side_effect = [(100,), (50,), (500,), (25,)]
        mock_cursor.fetchall.return_value = [('scraped', 40), ('emailed', 60)]
        
        # First call should hit DB
        stats1 = self.service.get_stats_overview()
        self.assertEqual(stats1['total_leads'], 100)
        self.assertEqual(self.mock_dm.get_connection.call_count, 1)
        
        # Second call should hit cache
        stats2 = self.service.get_stats_overview()
        self.assertEqual(stats2['total_leads'], 100)
        self.assertEqual(self.mock_dm.get_connection.call_count, 1) # Still 1

    def test_get_recent_activity(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        self.mock_dm.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            (1, 'sent', '2024-01-01 10:00:00', '{"to": "test@test.com"}', 'Test Business')
        ]
        
        activity = self.service.get_recent_activity(limit=1)
        self.assertEqual(len(activity), 1)
        self.assertEqual(activity[0]['business_name'], 'Test Business')
        self.assertEqual(activity[0]['meta']['to'], 'test@test.com')

    def test_get_lead_funnel(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        self.mock_dm.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = (10,)
        
        funnel = self.service.get_lead_funnel()
        self.assertEqual(len(funnel), 6) # 6 stages
        for stage in funnel:
            self.assertEqual(stage['count'], 10)

    def test_get_daily_volume(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        self.mock_dm.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = (5,)
        
        volume = self.service.get_daily_volume(days=3)
        self.assertEqual(len(volume), 3)
        self.assertEqual(volume[0]['sent'], 5)

if __name__ == '__main__':
    unittest.main()
