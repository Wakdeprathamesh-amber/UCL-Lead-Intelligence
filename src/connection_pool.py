"""
Connection Pooling Module
Thread-safe connection pool for SQLite database connections
"""

import sqlite3
import threading
from queue import Queue, Empty
from typing import Optional
import time
import os


class SQLiteConnectionPool:
    """Thread-safe connection pool for SQLite"""
    
    def __init__(self, db_path: str, max_connections: int = 5, timeout: int = 5):
        """
        Initialize connection pool
        
        Args:
            db_path: Path to SQLite database
            max_connections: Maximum number of connections in pool
            timeout: Timeout in seconds for getting connection from pool
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created_connections = 0
        
        # Don't pre-create connections - create them lazily on first use
        # This allows agent initialization even if database doesn't exist yet
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        # Check if database exists, try both lowercase and uppercase paths
        if not os.path.exists(self.db_path):
            # Try alternative path (case-sensitive filesystems)
            alt_path = "Data/leads.db" if self.db_path == "data/leads.db" else "data/leads.db"
            if os.path.exists(alt_path):
                self.db_path = alt_path
            else:
                raise FileNotFoundError(
                    f"Database file not found: {self.db_path}\n"
                    f"Tried: {self.db_path} and {alt_path}\n"
                    f"Please ensure the database is initialized by running ensure_databases_exist()"
                )
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        self._created_connections += 1
        return conn
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a connection from the pool
        
        Returns:
            SQLite connection object
        """
        try:
            # Try to get from pool
            conn = self._pool.get(timeout=self.timeout)
            
            # Check if connection is still valid
            try:
                conn.execute("SELECT 1")
            except sqlite3.Error:
                # Connection is dead, create new one
                conn = self._create_connection()
            
            return conn
            
        except Empty:
            # Pool is empty, create new connection if under limit
            with self._lock:
                if self._created_connections < self.max_connections:
                    return self._create_connection()
                else:
                    # Wait for connection to become available
                    return self._pool.get(timeout=self.timeout)
    
    def return_connection(self, conn: sqlite3.Connection) -> None:
        """
        Return a connection to the pool
        
        Args:
            conn: Connection to return
        """
        if conn:
            try:
                # Reset connection state
                conn.rollback()
                self._pool.put(conn, block=False)
            except:
                # Pool is full or connection is bad, just close it
                try:
                    conn.close()
                except:
                    pass
                with self._lock:
                    self._created_connections -= 1
    
    def close_all(self) -> None:
        """Close all connections in the pool"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except:
                pass
        
        with self._lock:
            self._created_connections = 0
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        return {
            "pool_size": self._pool.qsize(),
            "max_connections": self.max_connections,
            "created_connections": self._created_connections,
            "available_connections": self._pool.qsize()
        }


# Context manager for connection pool usage
class ConnectionContext:
    """Context manager for using connection pool"""
    
    def __init__(self, pool: SQLiteConnectionPool):
        self.pool = pool
        self.conn = None
    
    def __enter__(self) -> sqlite3.Connection:
        self.conn = self.pool.get_connection()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.pool.return_connection(self.conn)
        return False  # Don't suppress exceptions


# Global connection pool (lazy initialization)
_global_pool: Optional[SQLiteConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool(db_path: str = "data/leads.db", max_connections: int = 5) -> SQLiteConnectionPool:
    """Get or create global connection pool"""
    global _global_pool
    
    if _global_pool is None:
        with _pool_lock:
            if _global_pool is None:
                _global_pool = SQLiteConnectionPool(db_path, max_connections)
    
    return _global_pool


def get_connection(db_path: str = "data/leads.db") -> ConnectionContext:
    """Get a connection from the global pool (context manager)"""
    pool = get_connection_pool(db_path)
    return ConnectionContext(pool)


if __name__ == "__main__":
    # Test connection pool
    print("Testing Connection Pool...")
    
    pool = SQLiteConnectionPool("data/leads.db", max_connections=3)
    
    # Test getting/returning connections
    conn1 = pool.get_connection()
    conn2 = pool.get_connection()
    conn3 = pool.get_connection()
    
    print(f"✅ Got 3 connections")
    print(f"   Pool stats: {pool.get_stats()}")
    
    pool.return_connection(conn1)
    pool.return_connection(conn2)
    pool.return_connection(conn3)
    
    print(f"✅ Returned 3 connections")
    print(f"   Pool stats: {pool.get_stats()}")
    
    # Test context manager
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads")
        count = cursor.fetchone()[0]
        print(f"✅ Context manager working: {count} leads")
    
    print("\n✅ All connection pool tests passed!")

