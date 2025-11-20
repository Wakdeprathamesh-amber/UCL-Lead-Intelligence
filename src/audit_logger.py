"""
Audit Logging Module
Logs all queries, access, and system events for compliance
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Lock


class AuditLogger:
    """Thread-safe audit logger for compliance and security"""
    
    def __init__(self, db_path: str = "data/audit_log.db"):
        """Initialize audit logger"""
        self.db_path = db_path
        self.lock = Lock()
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._create_tables()
    
    def _create_tables(self):
        """Create audit log tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                session_id TEXT,
                query_text TEXT,
                query_type TEXT,
                tools_used TEXT,
                success BOOLEAN,
                error_message TEXT,
                response_length INTEGER,
                execution_time_ms REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                session_id TEXT,
                action TEXT,
                resource TEXT,
                success BOOLEAN,
                ip_address TEXT,
                user_agent TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_log_timestamp 
            ON query_log(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_log_user_id 
            ON query_log(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_access_log_timestamp 
            ON access_log(timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def log_query(
        self,
        query_text: str,
        query_type: str = "user_query",
        tools_used: Optional[list] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        response_length: Optional[int] = None,
        execution_time_ms: Optional[float] = None,
        user_id: str = "anonymous",
        session_id: Optional[str] = None
    ):
        """Log a query"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO query_log 
                (user_id, session_id, query_text, query_type, tools_used, 
                 success, error_message, response_length, execution_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                session_id,
                query_text[:1000],  # Limit length
                query_type,
                json.dumps(tools_used) if tools_used else None,
                success,
                error_message[:500] if error_message else None,
                response_length,
                execution_time_ms
            ))
            
            conn.commit()
            conn.close()
    
    def log_access(
        self,
        action: str,
        resource: str,
        success: bool = True,
        user_id: str = "anonymous",
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log access attempt"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO access_log 
                (user_id, session_id, action, resource, success, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                session_id,
                action,
                resource,
                success,
                ip_address,
                user_agent
            ))
            
            conn.commit()
            conn.close()
    
    def get_recent_queries(self, limit: int = 100, user_id: Optional[str] = None):
        """Get recent queries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT * FROM query_log 
                WHERE user_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM query_log 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger"""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger

