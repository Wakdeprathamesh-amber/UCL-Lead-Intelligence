"""
Aggregate Query Tools Module
MCP-style tools for querying aggregate lead data (1,525 leads)
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter


class AggregateQueryTools:
    """Tools for querying aggregate lead data"""
    
    def __init__(self, db_path: str = "data/leads_aggregate.db"):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_lead_by_id(self, lead_id: str) -> Optional[Dict]:
        """Get aggregate lead information by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM aggregate_leads WHERE lead_id = ?
        """, (lead_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "lead_id": row[0],
            "lead_date": row[1],
            "partner_id": row[2],
            "subpartner_name": row[4],
            "lost_reason": row[5],
            "source_country": row[7],
            "state": row[8],
            "city_name": row[10],
            "country_name": row[11],
            "partner_state": row[12],
            "repeat": bool(row[13]),
            "repeat_all": bool(row[14])
        }
    
    def filter_leads(
        self,
        state: Optional[str] = None,
        source_country: Optional[str] = None,
        city_name: Optional[str] = None,
        lost_reason: Optional[str] = None,
        repeat: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Filter aggregate leads by various criteria"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM aggregate_leads WHERE 1=1"
        params = []
        
        if state:
            query += " AND state = ?"
            params.append(state)
        
        if source_country:
            query += " AND source_country = ?"
            params.append(source_country)
        
        if city_name:
            query += " AND city_name = ?"
            params.append(city_name)
        
        if lost_reason:
            query += " AND lost_reason = ?"
            params.append(lost_reason)
        
        if repeat is not None:
            query += " AND repeat = ?"
            params.append(1 if repeat else 0)
        
        query += f" LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "lead_id": row[0],
                "lead_date": row[1],
                "subpartner_name": row[4],
                "lost_reason": row[5],
                "source_country": row[7],
                "state": row[8],
                "city_name": row[10],
                "country_name": row[11],
                "repeat": bool(row[13])
            })
        
        return results
    
    def get_aggregations(self) -> Dict[str, Any]:
        """Get comprehensive KPIs and statistics about aggregate leads"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total leads
        cursor.execute("SELECT COUNT(*) FROM aggregate_leads")
        total_leads = cursor.fetchone()[0]
        
        # Status breakdown
        cursor.execute("""
            SELECT state, COUNT(*) as cnt
            FROM aggregate_leads 
            GROUP BY state 
            ORDER BY cnt DESC
        """)
        status_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        won_count = status_breakdown.get('won', 0)
        lost_count = status_breakdown.get('lost', 0)
        conversion_rate = (won_count / total_leads * 100) if total_leads > 0 else 0
        
        # Lost reasons breakdown
        cursor.execute("""
            SELECT lost_reason, COUNT(*) as count 
            FROM aggregate_leads 
            WHERE lost_reason IS NOT NULL AND lost_reason != ''
            GROUP BY lost_reason 
            ORDER BY count DESC
            LIMIT 20
        """)
        lost_reasons = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Country breakdown
        cursor.execute("""
            SELECT source_country, COUNT(*) as count 
            FROM aggregate_leads 
            WHERE source_country IS NOT NULL AND source_country != ''
            GROUP BY source_country 
            ORDER BY count DESC
            LIMIT 20
        """)
        country_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        # City breakdown
        cursor.execute("""
            SELECT city_name, COUNT(*) as count 
            FROM aggregate_leads 
            WHERE city_name IS NOT NULL AND city_name != ''
            GROUP BY city_name 
            ORDER BY count DESC
            LIMIT 20
        """)
        city_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Repeat leads
        cursor.execute("SELECT COUNT(*) FROM aggregate_leads WHERE repeat = 1")
        repeat_count = cursor.fetchone()[0]
        repeat_rate = (repeat_count / total_leads * 100) if total_leads > 0 else 0
        
        # Monthly trends
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', lead_date) as month,
                COUNT(*) as count
            FROM aggregate_leads
            WHERE lead_date IS NOT NULL AND lead_date != ''
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """)
        monthly_trends = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "total_leads": total_leads,
            "status_breakdown": status_breakdown,
            "won_count": won_count,
            "lost_count": lost_count,
            "conversion_rate": round(conversion_rate, 2),
            "lost_reasons": lost_reasons,
            "country_breakdown": country_breakdown,
            "city_breakdown": city_breakdown,
            "repeat_count": repeat_count,
            "repeat_rate": round(repeat_rate, 2),
            "monthly_trends": monthly_trends
        }
    
    def get_leads_by_status(self, status: str) -> List[Dict]:
        """Get all leads with a specific status"""
        return self.filter_leads(state=status, limit=100)
    
    def get_top_lost_reasons(self, limit: int = 10) -> List[Dict]:
        """Get top lost reasons"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT lost_reason, COUNT(*) as count 
            FROM aggregate_leads 
            WHERE lost_reason IS NOT NULL AND lost_reason != ''
            GROUP BY lost_reason 
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        
        results = [{"reason": row[0], "count": row[1]} for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_country_statistics(self) -> Dict[str, Any]:
        """Get detailed country statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                source_country,
                COUNT(*) as total,
                SUM(CASE WHEN state = 'won' THEN 1 ELSE 0 END) as won,
                SUM(CASE WHEN state = 'lost' THEN 1 ELSE 0 END) as lost
            FROM aggregate_leads
            WHERE source_country IS NOT NULL AND source_country != ''
            GROUP BY source_country
            ORDER BY total DESC
            LIMIT 20
        """)
        
        countries = []
        for row in cursor.fetchall():
            countries.append({
                "country": row[0],
                "total": row[1],
                "won": row[2],
                "lost": row[3],
                "conversion_rate": round((row[2] / row[1] * 100) if row[1] > 0 else 0, 2)
            })
        
        conn.close()
        
        return {"countries": countries}
    
    def search_leads_by_country(self, country: str, limit: int = 50) -> List[Dict]:
        """Search leads by source country"""
        return self.filter_leads(source_country=country, limit=limit)

