"""
Unit Tests for Query Tools
Comprehensive unit tests for query_tools module
"""

import unittest
import sqlite3
import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from query_tools import LeadQueryTools


class TestLeadQueryTools(unittest.TestCase):
    """Unit tests for LeadQueryTools"""
    
    def setUp(self):
        """Set up test database"""
        # Create temporary database
        self.test_db = tempfile.mktemp(suffix='.db')
        self.tools = LeadQueryTools(db_path=self.test_db)
        
        # Create schema
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        # Create tables
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
                university TEXT,
                move_in_date TEXT,
                budget_max REAL,
                budget_currency TEXT,
                room_type TEXT,
                lease_duration_weeks INTEGER,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # Insert test data
        cursor.execute("""
            INSERT INTO leads (lead_id, name, mobile_number, status)
            VALUES ('1', 'Test Lead', '1234567890', 'Won')
        """)
        
        cursor.execute("""
            INSERT INTO lead_requirements 
            (lead_id, nationality, location, university, move_in_date, budget_max, budget_currency, room_type, lease_duration_weeks)
            VALUES ('1', 'UK', 'London', 'UCL', '2026-01-01', 400.0, 'GBP', 'Studio', 52)
        """)
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_get_lead_by_id_valid(self):
        """Test getting lead by valid ID"""
        result = self.tools.get_lead_by_id('1')
        self.assertIsNotNone(result)
        self.assertEqual(result['lead_id'], '1')
        self.assertEqual(result['name'], 'Test Lead')
        self.assertEqual(result['status'], 'Won')
    
    def test_get_lead_by_id_invalid(self):
        """Test getting lead by invalid ID"""
        result = self.tools.get_lead_by_id('999')
        self.assertIsNone(result)
    
    def test_get_lead_by_id_empty(self):
        """Test getting lead with empty ID"""
        with self.assertRaises(ValueError):
            self.tools.get_lead_by_id('')
    
    def test_filter_leads_by_status(self):
        """Test filtering leads by status"""
        results = self.tools.filter_leads(status='Won')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'Won')
    
    def test_filter_leads_by_budget(self):
        """Test filtering leads by budget"""
        results = self.tools.filter_leads(budget_max=500)
        self.assertEqual(len(results), 1)
        self.assertLessEqual(results[0]['budget_max'], 500)
    
    def test_filter_leads_invalid_status(self):
        """Test filtering with invalid status"""
        with self.assertRaises(ValueError):
            self.tools.filter_leads(status='InvalidStatus')
    
    def test_filter_leads_invalid_budget(self):
        """Test filtering with invalid budget"""
        with self.assertRaises(ValueError):
            self.tools.filter_leads(budget_max=-100)
    
    def test_filter_leads_budget_range_invalid(self):
        """Test filtering with invalid budget range"""
        with self.assertRaises(ValueError):
            self.tools.filter_leads(budget_min=500, budget_max=400)
    
    def test_get_aggregations(self):
        """Test getting aggregations"""
        aggs = self.tools.get_aggregations()
        self.assertIn('total_leads', aggs)
        self.assertIn('status_breakdown', aggs)
        self.assertEqual(aggs['total_leads'], 1)
    
    def test_database_not_found(self):
        """Test error handling when database not found"""
        tools = LeadQueryTools(db_path='nonexistent.db')
        with self.assertRaises(RuntimeError):
            tools.get_lead_by_id('1')


class TestErrorHandling(unittest.TestCase):
    """Test error handling utilities"""
    
    def setUp(self):
        """Set up test"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        try:
            from error_handling import validate_lead_id, validate_status, validate_budget
            self.validate_lead_id = validate_lead_id
            self.validate_status = validate_status
            self.validate_budget = validate_budget
        except ImportError:
            self.skipTest("Error handling module not available")
    
    def test_validate_lead_id(self):
        """Test lead ID validation"""
        self.assertTrue(self.validate_lead_id('123'))
        self.assertTrue(self.validate_lead_id('#123'))
        self.assertFalse(self.validate_lead_id(''))
        self.assertFalse(self.validate_lead_id(None))
    
    def test_validate_status(self):
        """Test status validation"""
        self.assertTrue(self.validate_status('Won'))
        self.assertTrue(self.validate_status('Lost'))
        self.assertFalse(self.validate_status('Invalid'))
        self.assertFalse(self.validate_status(''))
    
    def test_validate_budget(self):
        """Test budget validation"""
        self.assertTrue(self.validate_budget(100))
        self.assertTrue(self.validate_budget(100.5))
        self.assertFalse(self.validate_budget(-100))
        self.assertFalse(self.validate_budget('invalid'))


if __name__ == '__main__':
    unittest.main()

