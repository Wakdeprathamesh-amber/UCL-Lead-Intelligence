"""
SQL Executor Module
Safe SQL query execution with validation and error handling
"""

import sqlite3
import json
from typing import Dict, Any, Optional, List
import os
import sys

# Add error handling utilities
sys.path.insert(0, os.path.dirname(__file__))
try:
    from error_handling import ErrorHandler
    from connection_pool import get_connection_pool
except ImportError:
    # Fallback if not available
    class ErrorHandler:
        @staticmethod
        def handle_database_error(func):
            return func
    def get_connection_pool(db_path, max_connections=5):
        return None


class SQLExecutor:
    """Safe SQL query executor with validation"""
    
    def __init__(self, db_path: str = "data/leads.db", use_pool: bool = True):
        self.db_path = db_path
        self.use_pool = use_pool
        
        # Initialize connection pool if enabled
        if use_pool:
            try:
                self.pool = get_connection_pool(db_path, max_connections=5)
            except ImportError:
                self.use_pool = False
                self.pool = None
        else:
            self.pool = None
    
    def _get_connection(self):
        """Get database connection"""
        if self.use_pool and self.pool:
            return self.pool.get_connection()
        
        try:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database file not found: {self.db_path}")
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to connect to database: {str(e)}")
    
    def _return_connection(self, conn):
        """Return connection to pool"""
        if self.use_pool and self.pool and conn:
            self.pool.return_connection(conn)
        elif conn:
            conn.close()
    
    def _validate_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query for safety
        
        Returns:
            (is_valid, error_message)
        """
        query_upper = query.strip().upper()
        
        # Only allow SELECT queries
        if not query_upper.startswith('SELECT'):
            return False, "Only SELECT queries are allowed for safety"
        
        # Block dangerous operations (only as standalone keywords, not in column names)
        # Use word boundaries to avoid false positives (e.g., "created_at" should be allowed)
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
            'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE', 'REPLACE'
        ]
        
        import re
        for keyword in dangerous_keywords:
            # Match only as standalone word (not part of column names like "created_at")
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, query_upper):
                return False, f"Query contains forbidden keyword: {keyword}"
        
        # Block comments that might hide malicious code
        if '--' in query or '/*' in query:
            return False, "Comments are not allowed in queries"
        
        return True, None
    
    @ErrorHandler.handle_database_error
    def execute(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Execute a SQL SELECT query safely
        
        Args:
            query: SQL SELECT query string
            params: Optional tuple of parameters for parameterized queries
            
        Returns:
            Dict with 'columns', 'rows' (list of dicts), 'row_count', and 'error' (if any)
        """
        # Validate query
        is_valid, error_msg = self._validate_query(query)
        if not is_valid:
            return {
                "error": error_msg,
                "columns": [],
                "rows": [],
                "row_count": 0
            }
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert rows to list of dicts
            result_rows = []
            for row in rows:
                result_rows.append(dict(zip(columns, row)))
            
            return {
                "columns": columns,
                "rows": result_rows,
                "row_count": len(result_rows),
                "error": None
            }
        except sqlite3.Error as e:
            return {
                "error": f"SQL Error: {str(e)}",
                "columns": [],
                "rows": [],
                "row_count": 0
            }
        except Exception as e:
            return {
                "error": f"Error executing query: {str(e)}",
                "columns": [],
                "rows": [],
                "row_count": 0
            }
        finally:
            if conn:
                self._return_connection(conn)
    
    def execute_multi(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple SQL queries
        
        Args:
            queries: List of SQL SELECT query strings
            
        Returns:
            List of result dicts
        """
        results = []
        for query in queries:
            result = self.execute(query)
            results.append(result)
        return results


# Convenience function for backward compatibility
def execute_sql_query(query: str, params: Optional[tuple] = None, db_path: str = "data/leads.db") -> Dict[str, Any]:
    """Convenience function to execute SQL query"""
    executor = SQLExecutor(db_path=db_path)
    return executor.execute(query, params)

