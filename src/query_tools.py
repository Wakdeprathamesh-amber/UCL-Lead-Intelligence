"""
Query Tools Module
MCP-style tools for structured queries and aggregations
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter
import sys
import os

# Add error handling utilities
sys.path.insert(0, os.path.dirname(__file__))
try:
    from error_handling import ErrorHandler, format_error_message, validate_lead_id, validate_status, validate_budget
    from query_cache import cached
except ImportError:
    # Fallback if error_handling not available
    class ErrorHandler:
        @staticmethod
        def handle_database_error(func):
            return func
    def format_error_message(error, context=""):
        return str(error)
    def validate_lead_id(lead_id):
        return bool(lead_id)
    def validate_status(status):
        return True
    def validate_budget(budget):
        return isinstance(budget, (int, float)) and budget >= 0


class LeadQueryTools:
    """Tools for querying structured lead data"""
    
    def __init__(self, db_path: str = "data/leads.db", use_pool: bool = True):
        self.db_path = db_path
        self.use_pool = use_pool
        
        # Initialize connection pool if enabled
        if use_pool:
            try:
                from connection_pool import get_connection_pool
                self.pool = get_connection_pool(db_path, max_connections=5)
            except ImportError:
                self.use_pool = False
                self.pool = None
        else:
            self.pool = None
    
    def _get_connection(self):
        """Get database connection with error handling (uses pool if enabled)"""
        if self.use_pool and self.pool:
            return self.pool.get_connection()
        
        try:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database file not found: {self.db_path}")
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to connect to database: {str(e)}")
    
    def _return_connection(self, conn):
        """Return connection to pool if using pool"""
        if self.use_pool and self.pool and conn:
            self.pool.return_connection(conn)
        elif conn:
            conn.close()
    
    @ErrorHandler.handle_database_error
    def get_lead_by_id(self, lead_id: str) -> Optional[Dict]:
        """Get complete lead information by ID with validation and error handling"""
        if not validate_lead_id(lead_id):
            raise ValueError(f"Invalid lead_id: {lead_id}")
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT l.*, lr.*
                FROM leads l
                LEFT JOIN lead_requirements lr ON l.lead_id = lr.lead_id
                WHERE l.lead_id = ?
            """, (lead_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                "lead_id": row[0],
                "name": row[1],
                "mobile_number": row[2],
                "status": row[3],
                "nationality": row[8] if len(row) > 8 else None,
                "location": row[9] if len(row) > 9 else None,
                "university": row[10] if len(row) > 10 else None,
                "move_in_date": row[11] if len(row) > 11 else None,
                "budget_max": row[12] if len(row) > 12 else None,
                "budget_currency": row[13] if len(row) > 13 else None,
                "room_type": row[14] if len(row) > 14 else None,
                "lease_duration_weeks": row[15] if len(row) > 15 else None,
                "visa_status": row[16] if len(row) > 16 else None,
                "university_acceptance": row[17] if len(row) > 17 else None
            }
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error while fetching lead {lead_id}: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error while fetching lead {lead_id}: {str(e)}")
        finally:
            if conn:
                self._return_connection(conn)
    
    @ErrorHandler.handle_database_error
    def filter_leads(
        self,
        status: Optional[str] = None,
        nationality: Optional[str] = None,
        location: Optional[str] = None,
        university: Optional[str] = None,
        budget_max: Optional[float] = None,
        budget_min: Optional[float] = None,
        move_in_month: Optional[str] = None,
        room_type: Optional[str] = None,
        lease_duration_min: Optional[int] = None,
        lease_duration_max: Optional[int] = None
    ) -> List[Dict]:
        """Filter leads by various criteria with validation and error handling"""
        # Validate inputs
        if status and not validate_status(status):
            raise ValueError(f"Invalid status: {status}. Valid values: Won, Lost, Contacted, Oppurtunity, Disputed")
        
        if budget_max is not None and not validate_budget(budget_max):
            raise ValueError(f"Invalid budget_max: {budget_max}. Must be a non-negative number")
        
        if budget_min is not None and not validate_budget(budget_min):
            raise ValueError(f"Invalid budget_min: {budget_min}. Must be a non-negative number")
        
        if budget_max is not None and budget_min is not None and budget_min > budget_max:
            raise ValueError(f"budget_min ({budget_min}) cannot be greater than budget_max ({budget_max})")
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT l.lead_id, l.name, l.status, lr.nationality, lr.location, 
                       lr.university, lr.move_in_date, lr.budget_max, lr.budget_currency,
                       lr.room_type, lr.lease_duration_weeks
                FROM leads l
                LEFT JOIN lead_requirements lr ON l.lead_id = lr.lead_id
                WHERE 1=1
            """
            
            params = []
            
            if status:
                query += " AND l.status = ?"
                params.append(status)
            
            if nationality:
                query += " AND lr.nationality LIKE ?"
                params.append(f"%{nationality}%")
            
            if location:
                query += " AND lr.location LIKE ?"
                params.append(f"%{location}%")
            
            if university:
                query += " AND lr.university LIKE ?"
                params.append(f"%{university}%")
            
            if budget_max:
                query += " AND lr.budget_max <= ?"
                params.append(budget_max)
            
            if budget_min:
                query += " AND lr.budget_max >= ?"
                params.append(budget_min)
            
            if move_in_month:
                query += " AND lr.move_in_date LIKE ?"
                params.append(f"%{move_in_month}%")
            
            if room_type:
                query += " AND lr.room_type = ?"
                params.append(room_type)
            
            if lease_duration_min:
                query += " AND lr.lease_duration_weeks >= ?"
                params.append(lease_duration_min)
            
            if lease_duration_max:
                query += " AND lr.lease_duration_weeks <= ?"
                params.append(lease_duration_max)
        
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "lead_id": row[0],
                    "name": row[1],
                    "status": row[2],
                    "nationality": row[3],
                    "location": row[4],
                    "university": row[5],
                    "move_in_date": row[6],
                    "budget_max": row[7],
                    "budget_currency": row[8],
                    "room_type": row[9],
                    "lease_duration_weeks": row[10]
                })
            
            return results
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error while filtering leads: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error while filtering leads: {str(e)}")
        finally:
            if conn:
                self._return_connection(conn)
    
    def get_lead_tasks(self, lead_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get tasks for a specific lead"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM lead_tasks WHERE lead_id = ?"
            params = [lead_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                tasks.append({
                    "task_type": row[2],
                    "description": row[3],
                    "status": row[4],
                    "due_date": row[5],
                    "task_for": row[6]
                })
            
            return tasks
        finally:
            if conn:
                self._return_connection(conn)
    
    @cached(ttl=600)  # Cache for 10 minutes
    def get_aggregations(self) -> Dict[str, Any]:
        """Get pre-computed KPIs and aggregations (cached for 10 minutes)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total leads
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        
        # Status breakdown
        cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
        status_breakdown = dict(cursor.fetchall())
        
        # Location breakdown
        cursor.execute("""
            SELECT location, COUNT(*) 
            FROM lead_requirements 
            WHERE location IS NOT NULL 
            GROUP BY location
        """)
        location_breakdown = dict(cursor.fetchall())
        
        # University breakdown
        cursor.execute("""
            SELECT university, COUNT(*) 
            FROM lead_requirements 
            WHERE university IS NOT NULL 
            GROUP BY university
        """)
        university_breakdown = dict(cursor.fetchall())
        
        # Average budget
        cursor.execute("SELECT AVG(budget_max), budget_currency FROM lead_requirements WHERE budget_max IS NOT NULL GROUP BY budget_currency")
        avg_budget = cursor.fetchall()
        
        # Room type preferences
        cursor.execute("""
            SELECT room_type, COUNT(*) 
            FROM lead_requirements 
            WHERE room_type IS NOT NULL 
            GROUP BY room_type
        """)
        room_type_breakdown = dict(cursor.fetchall())
        
        # Move-in date distribution (by month)
        cursor.execute("""
            SELECT move_in_date 
            FROM lead_requirements 
            WHERE move_in_date IS NOT NULL
        """)
        move_in_dates = [row[0] for row in cursor.fetchall()]
        
        # Extract months
        move_in_months = []
        for date_str in move_in_dates:
            try:
                if date_str:
                    # Try to parse date
                    parts = date_str.split('-')
                    if len(parts) >= 2:
                        move_in_months.append(f"{parts[0]}-{parts[1]}")  # YYYY-MM
            except:
                pass
        
        month_breakdown = dict(Counter(move_in_months))
        
        # Nationality breakdown
        cursor.execute("""
            SELECT nationality, COUNT(*) 
            FROM lead_requirements 
            WHERE nationality IS NOT NULL 
            GROUP BY nationality
        """)
        nationality_breakdown = dict(cursor.fetchall())
        
        # Lease duration statistics
        cursor.execute("""
            SELECT AVG(lease_duration_weeks), MIN(lease_duration_weeks), MAX(lease_duration_weeks)
            FROM lead_requirements 
            WHERE lease_duration_weeks IS NOT NULL
        """)
        duration_stats = cursor.fetchone()
        avg_duration, min_duration, max_duration = duration_stats if duration_stats else (None, None, None)
        
        self._return_connection(conn)
        
        return {
            "total_leads": total_leads,
            "status_breakdown": status_breakdown,
            "won_leads": status_breakdown.get("Won", 0),
            "lost_leads": status_breakdown.get("Lost", 0),
            "opportunity_leads": status_breakdown.get("Oppurtunity", 0),
            "contacted_leads": status_breakdown.get("Contacted", 0),
            "location_breakdown": location_breakdown,
            "university_breakdown": university_breakdown,
            "average_budget": avg_budget,
            "min_budget": min_budget,
            "max_budget": max_budget,
            "room_type_breakdown": room_type_breakdown,
            "move_in_month_breakdown": month_breakdown,
            "nationality_breakdown": nationality_breakdown,
            "average_lease_duration_weeks": round(avg_duration, 1) if avg_duration else None,
            "min_lease_duration_weeks": min_duration,
            "max_lease_duration_weeks": max_duration
        }
    
    def get_leads_by_status(self, status: str) -> List[Dict]:
        """Get all leads with specific status"""
        return self.filter_leads(status=status)
    
    def get_leads_moving_in_month(self, year: str, month: str) -> List[Dict]:
        """Get leads moving in a specific month"""
        move_in_pattern = f"{year}-{month.zfill(2)}"
        return self.filter_leads(move_in_month=move_in_pattern)
    
    def get_conversation_summary(self, lead_id: str) -> Optional[Dict]:
        """Get conversation summary for a lead"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT structured_data 
            FROM leads 
            WHERE lead_id = ?
        """, (lead_id,))
        
        row = cursor.fetchone()
        self._return_connection(conn)
        
        if not row:
            return None
        
        try:
            data = json.loads(row[0])
            return data.get('conversation_summary', {})
        except:
            return None
    
    def search_leads_by_name(self, name_query: str) -> List[Dict]:
        """Search leads by name"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.lead_id, l.name, l.status, lr.university, lr.location
            FROM leads l
            LEFT JOIN lead_requirements lr ON l.lead_id = lr.lead_id
            WHERE l.name LIKE ?
        """, (f"%{name_query}%",))
        
        rows = cursor.fetchall()
        self._return_connection(conn)
        
        results = []
        for row in rows:
            results.append({
                "lead_id": row[0],
                "name": row[1],
                "status": row[2],
                "university": row[3],
                "location": row[4]
            })
        
        return results
    
    def get_lead_properties(self, lead_id: str) -> List[Dict]:
        """Get properties a lead is considering"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT property_name, room_type
            FROM lead_properties
            WHERE lead_id = ?
        """, (lead_id,))
        
        rows = cursor.fetchall()
        self._return_connection(conn)
        
        results = []
        for row in rows:
            results.append({
                "property_name": row[0],
                "room_type": row[1]
            })
        
        return results
    
    def get_popular_properties(self) -> List[Dict]:
        """Get most popular properties across all leads"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT property_name, COUNT(*) as count
            FROM lead_properties
            WHERE property_name IS NOT NULL
            GROUP BY property_name
            ORDER BY count DESC
        """)
        
        rows = cursor.fetchall()
        self._return_connection(conn)
        
        results = []
        for row in rows:
            results.append({
                "property_name": row[0],
                "lead_count": row[1]
            })
        
        return results
    
    def get_lead_amenities(self, lead_id: str) -> List[str]:
        """Get amenities requested by a lead"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT amenity
            FROM lead_amenities
            WHERE lead_id = ?
        """, (lead_id,))
        
        rows = cursor.fetchall()
        self._return_connection(conn)
        
        return [row[0] for row in rows]
    
    def get_popular_amenities(self) -> List[Dict]:
        """Get most requested amenities across all leads"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT amenity, COUNT(*) as count
            FROM lead_amenities
            GROUP BY amenity
            ORDER BY count DESC
        """)
        
        rows = cursor.fetchall()
        self._return_connection(conn)
        
        results = []
        for row in rows:
            results.append({
                "amenity": row[0],
                "lead_count": row[1]
            })
        
        return results
    
    def get_lead_timeline(self, lead_id: str, event_type: Optional[str] = None) -> List[Dict]:
        """Get timeline events for a specific lead"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if event_type:
            cursor.execute("""
                SELECT event_id, event_type, timestamp, content, source, direction, agent_id
                FROM timeline_events
                WHERE lead_id = ? AND event_type = ?
                ORDER BY timestamp ASC
            """, (lead_id, event_type))
        else:
            cursor.execute("""
                SELECT event_id, event_type, timestamp, content, source, direction, agent_id
                FROM timeline_events
                WHERE lead_id = ?
                ORDER BY timestamp ASC
            """, (lead_id,))
        
        rows = cursor.fetchall()
        self._return_connection(conn)
        
        results = []
        for row in rows:
            results.append({
                "event_id": row[0],
                "event_type": row[1],
                "timestamp": row[2],
                "content": row[3],
                "source": row[4],
                "direction": row[5],
                "agent_id": row[6]
            })
        
        return results
    
    def get_call_transcripts(self, lead_id: Optional[str] = None) -> List[Dict]:
        """Get call transcripts, optionally filtered by lead_id"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if lead_id:
            cursor.execute("""
                SELECT lead_id, call_id, transcript_text, record_url, transcription_status
                FROM call_transcripts
                WHERE lead_id = ?
                ORDER BY call_id ASC
            """, (lead_id,))
        else:
            cursor.execute("""
                SELECT lead_id, call_id, transcript_text, record_url, transcription_status
                FROM call_transcripts
                ORDER BY lead_id, call_id ASC
            """)
        
        rows = cursor.fetchall()
        self._return_connection(conn)
        
        results = []
        for row in rows:
            results.append({
                "lead_id": row[0],
                "call_id": row[1],
                "transcript_text": row[2],
                "record_url": row[3],
                "transcription_status": row[4]
            })
        
        return results
    
    def search_timeline_events(self, query_text: str, event_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Search timeline events by content (simple text search)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if event_type:
            cursor.execute("""
                SELECT te.lead_id, te.event_id, te.event_type, te.timestamp, te.content, 
                       te.source, te.direction, l.name
                FROM timeline_events te
                JOIN leads l ON te.lead_id = l.lead_id
                WHERE te.content LIKE ? AND te.event_type = ?
                ORDER BY te.timestamp DESC
                LIMIT ?
            """, (f'%{query_text}%', event_type, limit))
        else:
            cursor.execute("""
                SELECT te.lead_id, te.event_id, te.event_type, te.timestamp, te.content, 
                       te.source, te.direction, l.name
                FROM timeline_events te
                JOIN leads l ON te.lead_id = l.lead_id
                WHERE te.content LIKE ?
                ORDER BY te.timestamp DESC
                LIMIT ?
            """, (f'%{query_text}%', limit))
        
        rows = cursor.fetchall()
        self._return_connection(conn)
        
        results = []
        for row in rows:
            results.append({
                "lead_id": row[0],
                "lead_name": row[7],
                "event_id": row[1],
                "event_type": row[2],
                "timestamp": row[3],
                "content": row[4],
                "source": row[5],
                "direction": row[6]
            })
        
        return results
    
    def get_crm_data(self, lead_id: Optional[str] = None, filters: Optional[Dict] = None) -> List[Dict]:
        """Get CRM data for leads - includes lost reasons, country, property info, etc.
        
        Args:
            lead_id: Optional specific lead ID to filter
            filters: Optional dict with filters like {'lost_reason': 'Not responded', 'location_country': 'United Kingdom'}
        
        Returns:
            List of CRM records with all available fields
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT c.*, l.name as lead_name, l.status as lead_status
                FROM crm_data c
                LEFT JOIN leads l ON c.lead_id = l.lead_id
                WHERE 1=1
            """
            params = []
            
            if lead_id:
                query += " AND c.lead_id = ?"
                params.append(lead_id)
            
            if filters:
                if 'lost_reason' in filters:
                    query += " AND c.lost_reason = ?"
                    params.append(filters['lost_reason'])
                if 'location_country' in filters:
                    query += " AND c.location_country = ?"
                    params.append(filters['location_country'])
                if 'phone_country' in filters:
                    query += " AND c.phone_country = ?"
                    params.append(filters['phone_country'])
                if 'state' in filters:
                    query += " AND c.state = ?"
                    params.append(filters['state'])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Get column names
            col_names = [desc[0] for desc in cursor.description]
            
            results = []
            for row in rows:
                record = dict(zip(col_names, row))
                results.append(record)
            
            return results
        finally:
            if conn:
                self._return_connection(conn)
    
    def get_lost_reasons_analysis(self) -> Dict[str, Any]:
        """Get comprehensive lost reasons analysis - can be grouped by country, etc.
        
        Returns:
            Dict with lost reasons breakdown, by country, top reasons, etc.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Overall lost reasons
            cursor.execute("""
                SELECT lost_reason, COUNT(*) as count
                FROM crm_data
                WHERE lost_reason IS NOT NULL AND lost_reason != ''
                GROUP BY lost_reason
                ORDER BY count DESC
            """)
            top_reasons = [{"reason": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            # Lost reasons by country
            cursor.execute("""
                SELECT location_country, lost_reason, COUNT(*) as count
                FROM crm_data
                WHERE lost_reason IS NOT NULL 
                  AND lost_reason != ''
                  AND location_country IS NOT NULL
                GROUP BY location_country, lost_reason
                ORDER BY location_country, count DESC
            """)
            reasons_by_country = {}
            for country, reason, count in cursor.fetchall():
                if country not in reasons_by_country:
                    reasons_by_country[country] = []
                reasons_by_country[country].append({"reason": reason, "count": count})
            
            # Lost reasons by phone country
            cursor.execute("""
                SELECT phone_country, lost_reason, COUNT(*) as count
                FROM crm_data
                WHERE lost_reason IS NOT NULL 
                  AND lost_reason != ''
                  AND phone_country IS NOT NULL
                GROUP BY phone_country, lost_reason
                ORDER BY phone_country, count DESC
            """)
            reasons_by_phone_country = {}
            for country, reason, count in cursor.fetchall():
                if country not in reasons_by_phone_country:
                    reasons_by_phone_country[country] = []
                reasons_by_phone_country[country].append({"reason": reason, "count": count})
            
            return {
                "top_reasons": top_reasons,
                "by_location_country": reasons_by_country,
                "by_phone_country": reasons_by_phone_country,
                "total_with_reasons": sum(r["count"] for r in top_reasons)
            }
        finally:
            if conn:
                self._return_connection(conn)
    
    def get_room_types_by_country(self) -> Dict[str, Any]:
        """Get room type preferences grouped by country
        
        Returns:
            Dict with room types by country
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Join crm_data -> leads -> lead_requirements
            cursor.execute("""
                SELECT c.location_country, lr.room_type, COUNT(*) as count
                FROM crm_data c
                JOIN leads l ON c.lead_id = l.lead_id
                JOIN lead_requirements lr ON l.lead_id = lr.lead_id
                WHERE c.location_country IS NOT NULL
                  AND lr.room_type IS NOT NULL
                  AND lr.room_type != ''
                GROUP BY c.location_country, lr.room_type
                ORDER BY c.location_country, count DESC
            """)
            
            room_types_by_country = {}
            for country, room_type, count in cursor.fetchall():
                if country not in room_types_by_country:
                    room_types_by_country[country] = []
                room_types_by_country[country].append({"room_type": room_type, "count": count})
            
            return room_types_by_country
        finally:
            if conn:
                self._return_connection(conn)
    
    def get_booked_room_types_by_country(self) -> Dict[str, Any]:
        """Get booked (Won) room types grouped by source country (where leads are from)
        
        Uses phone_country from CRM data (source country) or nationality from lead_requirements as fallback.
        location_country is the destination country (where they're moving to), not source.
        
        Returns:
            Dict with booked room types by source country, showing only Won leads
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Use phone_country (source country) from CRM data, fallback to nationality from lead_requirements
            # Join crm_data -> leads -> lead_requirements, filter by Won status
            cursor.execute("""
                SELECT 
                    COALESCE(c.phone_country, lr.nationality, 'Unknown') as source_country,
                    lr.room_type, 
                    COUNT(*) as count
                FROM crm_data c
                JOIN leads l ON c.lead_id = l.lead_id
                JOIN lead_requirements lr ON l.lead_id = lr.lead_id
                WHERE l.status = 'Won'
                  AND lr.room_type IS NOT NULL
                  AND lr.room_type != ''
                  AND (c.phone_country IS NOT NULL OR lr.nationality IS NOT NULL)
                GROUP BY source_country, lr.room_type
                ORDER BY source_country, count DESC
            """)
            
            booked_room_types_by_country = {}
            for country, room_type, count in cursor.fetchall():
                if country not in booked_room_types_by_country:
                    booked_room_types_by_country[country] = []
                booked_room_types_by_country[country].append({"room_type": room_type, "count": count})
            
            return booked_room_types_by_country
        finally:
            if conn:
                self._return_connection(conn)
    
    def get_all_pending_tasks(self, format: str = "summary", limit: int = 200) -> Dict[str, Any]:
        """Get pending and in-progress tasks - returns summary by default, list if format='list'
        
        Args:
            format: "summary" (default) returns aggregated statistics, "list" returns raw tasks
            limit: Maximum number of tasks to return when format='list' (default 200)
        
        Returns:
            If format='summary': Dict with task statistics and sample urgent tasks
            If format='list': List of tasks with lead information (limited to 'limit')
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if format == "summary":
                # Get aggregation statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN lt.status IN ('pending', 'Pending') THEN 1 ELSE 0 END) as pending_count,
                        SUM(CASE WHEN lt.status IN ('in_progress', 'In Progress') THEN 1 ELSE 0 END) as in_progress_count,
                        SUM(CASE WHEN lt.due_date < date('now') THEN 1 ELSE 0 END) as overdue_count,
                        SUM(CASE WHEN lt.due_date = date('now') THEN 1 ELSE 0 END) as due_today_count,
                        SUM(CASE WHEN lt.due_date BETWEEN date('now') AND date('now', '+7 days') 
                            THEN 1 ELSE 0 END) as due_this_week_count
                    FROM lead_tasks lt
                    WHERE lt.status IN ('pending', 'in_progress', 'Pending', 'In Progress')
                """)
                
                agg_row = cursor.fetchone()
                total = agg_row[0] if agg_row else 0
                pending_count = agg_row[1] if agg_row else 0
                in_progress_count = agg_row[2] if agg_row else 0
                overdue_count = agg_row[3] if agg_row else 0
                due_today_count = agg_row[4] if agg_row else 0
                due_this_week_count = agg_row[5] if agg_row else 0
                
                # Get task type breakdown
                cursor.execute("""
                    SELECT task_type, COUNT(*) as count
                    FROM lead_tasks lt
                    WHERE lt.status IN ('pending', 'in_progress', 'Pending', 'In Progress')
                    GROUP BY task_type
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                task_type_rows = cursor.fetchall()
                by_task_type = {row[0] or "unspecified": row[1] for row in task_type_rows}
                
                # Get sample urgent tasks (overdue first, then due today, then this week)
                cursor.execute("""
                    SELECT lt.*, l.name as lead_name, l.status as lead_status
                    FROM lead_tasks lt
                    JOIN leads l ON lt.lead_id = l.lead_id
                    WHERE lt.status IN ('pending', 'in_progress', 'Pending', 'In Progress')
                    ORDER BY 
                        CASE WHEN lt.due_date < date('now') THEN 0 ELSE 1 END,
                        CASE WHEN lt.due_date = date('now') THEN 0 ELSE 1 END,
                        CASE WHEN lt.due_date BETWEEN date('now') AND date('now', '+7 days') THEN 0 ELSE 1 END,
                        lt.due_date ASC,
                        lt.lead_id
                    LIMIT 10
                """)
                
                sample_rows = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]
                sample_tasks = [dict(zip(col_names, row)) for row in sample_rows]
                
                return {
                    "total": total,
                    "by_status": {
                        "pending": pending_count,
                        "in_progress": in_progress_count
                    },
                    "by_urgency": {
                        "overdue": overdue_count,
                        "due_today": due_today_count,
                        "due_this_week": due_this_week_count
                    },
                    "by_task_type": by_task_type,
                    "sample_urgent_tasks": sample_tasks
                }
            else:
                # Return raw list (with limit)
                cursor.execute("""
                    SELECT lt.*, l.name as lead_name, l.status as lead_status
                    FROM lead_tasks lt
                    JOIN leads l ON lt.lead_id = l.lead_id
                    WHERE lt.status IN ('pending', 'in_progress', 'Pending', 'In Progress')
                    ORDER BY lt.due_date ASC, lt.lead_id
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]
                
                tasks = []
                for row in rows:
                    task = dict(zip(col_names, row))
                    tasks.append(task)
                
                return tasks
        finally:
            if conn:
                self._return_connection(conn)
    
    def get_all_objections(self) -> List[Dict]:
        """Get all objections from the lead_objections table
        
        Returns:
            List of objections with lead information
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT lo.*, l.name as lead_name, l.status as lead_status
                FROM lead_objections lo
                JOIN leads l ON lo.lead_id = l.lead_id
                ORDER BY lo.id DESC
            """)
            
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            
            objections = []
            for row in rows:
                obj = dict(zip(col_names, row))
                objections.append(obj)
            
            return objections
        finally:
            if conn:
                self._return_connection(conn)


if __name__ == "__main__":
    # Test query tools
    tools = LeadQueryTools()
    
    print("="*60)
    print("🧪 TESTING QUERY TOOLS")
    print("="*60)
    
    # Test aggregations
    print("\n📊 Aggregations:")
    aggs = tools.get_aggregations()
    print(json.dumps(aggs, indent=2))
    
    # Test filter
    print("\n🔍 Leads moving in Jan 2026 with budget < 400:")
    results = tools.filter_leads(move_in_month="2026-01", budget_max=400)
    for lead in results:
        print(f"   {lead['name']} - {lead['budget_max']} {lead['budget_currency']}")
    
    # Test by status
    print("\n🎯 Won Leads:")
    won_leads = tools.get_leads_by_status("Won")
    for lead in won_leads:
        print(f"   {lead['name']} - {lead['university']}")
    
    print("\n" + "="*60)
    print("✅ Query Tools Ready")
    print("="*60)

