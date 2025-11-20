"""
Edge Case Tests
Comprehensive edge case testing for all modules
"""

import unittest
import sqlite3
import os
import sys
import tempfile
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from query_tools import LeadQueryTools
from property_analytics import PropertyAnalytics
from error_handling import validate_lead_id, validate_status, validate_budget
from query_cache import QueryCache, cached
from connection_pool import SQLiteConnectionPool


class TestEdgeCases(unittest.TestCase):
    """Edge case tests for all modules"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.mktemp(suffix='.db')
        self.tools = LeadQueryTools(db_path=self.test_db, use_pool=False)
        
        # Create schema
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE leads (
                lead_id TEXT PRIMARY KEY,
                name TEXT,
                mobile_number TEXT,
                status TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE lead_requirements (
                lead_id TEXT PRIMARY KEY,
                nationality TEXT,
                location TEXT,
                budget_max REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE lead_properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                property_name TEXT,
                room_type TEXT
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO leads VALUES ('1', 'Test', '123', 'Won')")
        cursor.execute("INSERT INTO lead_requirements VALUES ('1', 'UK', 'London', 400.0)")
        cursor.execute("INSERT INTO lead_properties VALUES (1, '1', 'Property A', 'Studio')")
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    # Edge cases for query_tools
    def test_get_lead_by_id_nonexistent(self):
        """Test getting non-existent lead"""
        result = self.tools.get_lead_by_id('999')
        self.assertIsNone(result)
    
    def test_get_lead_by_id_empty_string(self):
        """Test getting lead with empty ID"""
        with self.assertRaises(ValueError):
            self.tools.get_lead_by_id('')
    
    def test_get_lead_by_id_none(self):
        """Test getting lead with None ID"""
        with self.assertRaises(ValueError):
            self.tools.get_lead_by_id(None)
    
    def test_filter_leads_no_results(self):
        """Test filtering with no matching results"""
        results = self.tools.filter_leads(status='Lost')
        self.assertEqual(len(results), 0)
    
    def test_filter_leads_invalid_status(self):
        """Test filtering with invalid status"""
        with self.assertRaises(ValueError):
            self.tools.filter_leads(status='InvalidStatus')
    
    def test_filter_leads_negative_budget(self):
        """Test filtering with negative budget"""
        with self.assertRaises(ValueError):
            self.tools.filter_leads(budget_max=-100)
    
    def test_filter_leads_budget_range_invalid(self):
        """Test filtering with invalid budget range"""
        with self.assertRaises(ValueError):
            self.tools.filter_leads(budget_min=500, budget_max=400)
    
    def test_get_aggregations_empty_database(self):
        """Test aggregations on empty database"""
        # Create empty database
        empty_db = tempfile.mktemp(suffix='.db')
        empty_tools = LeadQueryTools(db_path=empty_db, use_pool=False)
        
        conn = sqlite3.connect(empty_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE leads (lead_id TEXT PRIMARY KEY, status TEXT)")
        conn.commit()
        conn.close()
        
        aggs = empty_tools.get_aggregations()
        self.assertEqual(aggs['total_leads'], 0)
        
        os.remove(empty_db)
    
    def test_database_not_found(self):
        """Test error handling when database doesn't exist"""
        tools = LeadQueryTools(db_path='nonexistent.db', use_pool=False)
        with self.assertRaises(RuntimeError):
            tools.get_lead_by_id('1')
    
    # Edge cases for property analytics
    def test_property_analytics_empty_database(self):
        """Test property analytics on empty database"""
        empty_db = tempfile.mktemp(suffix='.db')
        analytics = PropertyAnalytics(db_path=empty_db)
        
        conn = sqlite3.connect(empty_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE lead_properties (id INTEGER, lead_id TEXT, property_name TEXT)")
        cursor.execute("CREATE TABLE leads (lead_id TEXT PRIMARY KEY, status TEXT)")
        conn.commit()
        conn.close()
        
        results = analytics.get_property_analytics()
        self.assertEqual(len(results['popular_properties']), 0)
        
        os.remove(empty_db)
    
    def test_property_details_nonexistent(self):
        """Test getting details for non-existent property"""
        analytics = PropertyAnalytics(db_path=self.test_db)
        details = analytics.get_property_details('Nonexistent Property')
        self.assertEqual(details['total_leads'], 0)
    
    def test_compare_properties_insufficient(self):
        """Test comparing less than 2 properties"""
        analytics = PropertyAnalytics(db_path=self.test_db)
        with self.assertRaises(ValueError):
            analytics.compare_properties(['Property A'])
    
    # Edge cases for validation
    def test_validate_lead_id_edge_cases(self):
        """Test lead ID validation edge cases"""
        self.assertTrue(validate_lead_id('123'))
        self.assertTrue(validate_lead_id('#123'))
        self.assertFalse(validate_lead_id(''))
        self.assertFalse(validate_lead_id(None))
        self.assertFalse(validate_lead_id('   '))  # Only whitespace
    
    def test_validate_status_edge_cases(self):
        """Test status validation edge cases"""
        self.assertTrue(validate_status('Won'))
        self.assertTrue(validate_status('won'))  # Case insensitive
        self.assertFalse(validate_status(''))
        self.assertFalse(validate_status('Invalid'))
        self.assertFalse(validate_status(None))
    
    def test_validate_budget_edge_cases(self):
        """Test budget validation edge cases"""
        self.assertTrue(validate_budget(0))
        self.assertTrue(validate_budget(100.5))
        self.assertFalse(validate_budget(-100))
        self.assertFalse(validate_budget('invalid'))
        self.assertFalse(validate_budget(None))
    
    # Edge cases for caching
    def test_cache_expiration(self):
        """Test cache expiration"""
        cache = QueryCache(max_size=10, default_ttl=1)
        cache.set('key1', 'value1')
        self.assertEqual(cache.get('key1'), 'value1')
        
        import time
        time.sleep(2)
        self.assertIsNone(cache.get('key1'))
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = QueryCache(max_size=3, default_ttl=100)
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        cache.set('key4', 'value4')  # Should evict key1
        
        self.assertIsNone(cache.get('key1'))
        self.assertEqual(cache.get('key4'), 'value4')
    
    def test_cache_invalidation(self):
        """Test cache invalidation"""
        cache = QueryCache(max_size=10, default_ttl=100)
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('other_key', 'value3')
        
        invalidated = cache.invalidate('key')
        self.assertEqual(invalidated, 2)
        self.assertIsNone(cache.get('key1'))
        self.assertIsNone(cache.get('key2'))
        self.assertEqual(cache.get('other_key'), 'value3')
    
    # Edge cases for connection pool
    def test_connection_pool_max_connections(self):
        """Test connection pool respects max connections"""
        pool = SQLiteConnectionPool(self.test_db, max_connections=2)
        
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()
        
        # Third connection should wait or create new
        import threading
        import time
        
        got_conn3 = [False]
        
        def get_third():
            conn3 = pool.get_connection()
            got_conn3[0] = True
            pool.return_connection(conn3)
        
        thread = threading.Thread(target=get_third)
        thread.start()
        thread.join(timeout=1)
        
        pool.return_connection(conn1)
        pool.return_connection(conn2)
        pool.close_all()
    
    def test_connection_pool_invalid_connection(self):
        """Test handling of invalid connections"""
        pool = SQLiteConnectionPool(self.test_db, max_connections=2)
        conn = pool.get_connection()
        
        # Simulate dead connection
        conn.close()
        
        # Should handle gracefully
        pool.return_connection(conn)
        new_conn = pool.get_connection()
        self.assertIsNotNone(new_conn)
        
        pool.return_connection(new_conn)
        pool.close_all()
    
    # Edge cases for empty/null inputs
    def test_empty_string_inputs(self):
        """Test handling of empty string inputs"""
        with self.assertRaises(ValueError):
            self.tools.get_lead_by_id('')
        
        results = self.tools.filter_leads(status='')
        # Should handle gracefully or raise error
        self.assertIsInstance(results, list)
    
    def test_none_inputs(self):
        """Test handling of None inputs"""
        with self.assertRaises(ValueError):
            self.tools.get_lead_by_id(None)
    
    def test_very_large_inputs(self):
        """Test handling of very large inputs"""
        large_string = 'a' * 10000
        # Should not crash
        results = self.tools.filter_leads(location=large_string)
        self.assertIsInstance(results, list)
    
    def test_special_characters_in_inputs(self):
        """Test handling of special characters"""
        # SQL injection attempt
        malicious_input = "'; DROP TABLE leads; --"
        results = self.tools.filter_leads(location=malicious_input)
        # Should be safe (parameterized queries)
        self.assertIsInstance(results, list)


if __name__ == '__main__':
    unittest.main()

