"""
Query Tools Module
MCP-style tools for structured queries and aggregations
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter


class LeadQueryTools:
    """Tools for querying structured lead data"""
    
    def __init__(self, db_path: str = "data/leads.db"):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_lead_by_id(self, lead_id: str) -> Optional[Dict]:
        """Get complete lead information by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.*, lr.*
            FROM leads l
            LEFT JOIN lead_requirements lr ON l.lead_id = lr.lead_id
            WHERE l.lead_id = ?
        """, (lead_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "lead_id": row[0],
            "name": row[1],
            "mobile_number": row[2],
            "status": row[3],
            "nationality": row[8],
            "location": row[9],
            "university": row[10],
            "move_in_date": row[11],
            "budget_max": row[12],
            "budget_currency": row[13],
            "room_type": row[14],
            "lease_duration_weeks": row[15],
            "visa_status": row[16],
            "university_acceptance": row[17]
        }
    
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
        """Filter leads by various criteria"""
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
        conn.close()
        
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
    
    def get_lead_tasks(self, lead_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get tasks for a specific lead"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM lead_tasks WHERE lead_id = ?"
        params = [lead_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
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
    
    def get_aggregations(self) -> Dict[str, Any]:
        """Get pre-computed KPIs and aggregations"""
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
        
        conn.close()
        
        return {
            "total_leads": total_leads,
            "status_breakdown": status_breakdown,
            "won_leads": status_breakdown.get("Won", 0),
            "lost_leads": status_breakdown.get("Lost", 0),
            "opportunity_leads": status_breakdown.get("Oppurtunity", 0),
            "contacted_leads": status_breakdown.get("Contacted", 0),
            "location_breakdown": location_breakdown,
            "university_breakdown": university_breakdown,
            "average_budget": {curr: round(avg, 2) for avg, curr in avg_budget},
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
        conn.close()
        
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
        conn.close()
        
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
        conn.close()
        
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
        conn.close()
        
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
        conn.close()
        
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
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "amenity": row[0],
                "lead_count": row[1]
            })
        
        return results


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

