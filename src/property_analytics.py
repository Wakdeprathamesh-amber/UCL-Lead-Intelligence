"""
Property Analytics Module
Comprehensive property analytics including popularity, conversion rates, and performance metrics
"""

import sqlite3
from typing import List, Dict, Any, Optional
from collections import Counter
import sys
import os

# Add error handling
sys.path.insert(0, os.path.dirname(__file__))
try:
    from error_handling import ErrorHandler, validate_lead_id
except ImportError:
    class ErrorHandler:
        @staticmethod
        def handle_database_error(func):
            return func
    def validate_lead_id(lead_id):
        return bool(lead_id)


class PropertyAnalytics:
    """Comprehensive property analytics and insights"""
    
    def __init__(self, db_path: str = "data/leads.db"):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        try:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database file not found: {self.db_path}")
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to connect to database: {str(e)}")
    
    @ErrorHandler.handle_database_error
    def get_property_analytics(self, property_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive analytics for properties
        
        Args:
            property_name: Optional property name to filter by specific property
        
        Returns:
            Dictionary with property analytics including:
            - Most popular properties
            - Conversion rates by property
            - Property performance metrics
            - Lead distribution by property
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            analytics = {}
            
            # 1. Most Popular Properties (by lead count)
            if property_name:
                cursor.execute("""
                    SELECT property_name, COUNT(DISTINCT lp.lead_id) as lead_count
                    FROM lead_properties lp
                    WHERE lp.property_name = ?
                    GROUP BY property_name
                    ORDER BY lead_count DESC
                """, (property_name,))
            else:
                cursor.execute("""
                    SELECT property_name, COUNT(DISTINCT lp.lead_id) as lead_count
                    FROM lead_properties lp
                    WHERE lp.property_name IS NOT NULL AND lp.property_name != ''
                    GROUP BY property_name
                    ORDER BY lead_count DESC
                    LIMIT 20
                """)
            
            popular_properties = []
            for row in cursor.fetchall():
                popular_properties.append({
                    "property_name": row[0],
                    "lead_count": row[1]
                })
            analytics["popular_properties"] = popular_properties
            
            # 2. Conversion Rates by Property
            cursor.execute("""
                SELECT 
                    lp.property_name,
                    COUNT(DISTINCT lp.lead_id) as total_leads,
                    COUNT(DISTINCT CASE WHEN l.status = 'Won' THEN lp.lead_id END) as won_leads,
                    COUNT(DISTINCT CASE WHEN l.status = 'Lost' THEN lp.lead_id END) as lost_leads,
                    COUNT(DISTINCT CASE WHEN l.status = 'Oppurtunity' THEN lp.lead_id END) as opportunity_leads
                FROM lead_properties lp
                JOIN leads l ON lp.lead_id = l.lead_id
                WHERE lp.property_name IS NOT NULL AND lp.property_name != ''
                GROUP BY lp.property_name
                HAVING total_leads >= 2
                ORDER BY total_leads DESC
                LIMIT 20
            """)
            
            conversion_rates = []
            for row in cursor.fetchall():
                prop_name, total, won, lost, opp = row
                conversion_rate = (won / total * 100) if total > 0 else 0
                conversion_rates.append({
                    "property_name": prop_name,
                    "total_leads": total,
                    "won_leads": won,
                    "lost_leads": lost,
                    "opportunity_leads": opp,
                    "conversion_rate": round(conversion_rate, 1),
                    "win_rate": round((won / total * 100) if total > 0 else 0, 1),
                    "loss_rate": round((lost / total * 100) if total > 0 else 0, 1)
                })
            analytics["conversion_rates"] = conversion_rates
            
            # 3. Property Performance Metrics
            cursor.execute("""
                SELECT 
                    lp.property_name,
                    AVG(lr.budget_max) as avg_budget,
                    COUNT(DISTINCT lr.lead_id) as leads_with_budget,
                    COUNT(DISTINCT lp.lead_id) as total_considerations
                FROM lead_properties lp
                LEFT JOIN lead_requirements lr ON lp.lead_id = lr.lead_id
                WHERE lp.property_name IS NOT NULL AND lp.property_name != ''
                GROUP BY lp.property_name
                HAVING total_considerations >= 2
                ORDER BY total_considerations DESC
                LIMIT 20
            """)
            
            performance_metrics = []
            for row in cursor.fetchall():
                prop_name, avg_budget, leads_with_budget, total = row
                performance_metrics.append({
                    "property_name": prop_name,
                    "avg_budget": round(avg_budget, 2) if avg_budget else None,
                    "leads_with_budget": leads_with_budget,
                    "total_considerations": total
                })
            analytics["performance_metrics"] = performance_metrics
            
            # 4. Room Type Distribution by Property
            cursor.execute("""
                SELECT 
                    lp.property_name,
                    lp.room_type,
                    COUNT(*) as count
                FROM lead_properties lp
                WHERE lp.property_name IS NOT NULL AND lp.property_name != ''
                  AND lp.room_type IS NOT NULL AND lp.room_type != ''
                GROUP BY lp.property_name, lp.room_type
                ORDER BY lp.property_name, count DESC
            """)
            
            room_type_distribution = {}
            for row in cursor.fetchall():
                prop_name, room_type, count = row
                if prop_name not in room_type_distribution:
                    room_type_distribution[prop_name] = []
                room_type_distribution[prop_name].append({
                    "room_type": room_type,
                    "count": count
                })
            analytics["room_type_distribution"] = room_type_distribution
            
            # 5. Property by Status Distribution
            cursor.execute("""
                SELECT 
                    lp.property_name,
                    l.status,
                    COUNT(DISTINCT lp.lead_id) as lead_count
                FROM lead_properties lp
                JOIN leads l ON lp.lead_id = l.lead_id
                WHERE lp.property_name IS NOT NULL AND lp.property_name != ''
                GROUP BY lp.property_name, l.status
                ORDER BY lp.property_name, lead_count DESC
            """)
            
            status_distribution = {}
            for row in cursor.fetchall():
                prop_name, status, count = row
                if prop_name not in status_distribution:
                    status_distribution[prop_name] = {}
                status_distribution[prop_name][status] = count
            analytics["status_distribution"] = status_distribution
            
            # 6. Top Properties Summary
            if popular_properties:
                top_properties = []
                for prop in popular_properties[:10]:
                    prop_name = prop["property_name"]
                    # Get conversion rate for this property
                    conv_data = next((c for c in conversion_rates if c["property_name"] == prop_name), None)
                    top_properties.append({
                        "property_name": prop_name,
                        "lead_count": prop["lead_count"],
                        "conversion_rate": conv_data["conversion_rate"] if conv_data else 0,
                        "won_leads": conv_data["won_leads"] if conv_data else 0,
                        "total_leads": conv_data["total_leads"] if conv_data else prop["lead_count"]
                    })
                analytics["top_properties_summary"] = top_properties
            
            return analytics
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error in property analytics: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in property analytics: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    @ErrorHandler.handle_database_error
    def get_property_details(self, property_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific property"""
        if not property_name or not isinstance(property_name, str):
            raise ValueError("Property name must be a non-empty string")
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all leads considering this property
            cursor.execute("""
                SELECT DISTINCT l.lead_id, l.name, l.status, lr.budget_max, lr.budget_currency,
                       lp.room_type, lr.location, lr.university
                FROM lead_properties lp
                JOIN leads l ON lp.lead_id = l.lead_id
                LEFT JOIN lead_requirements lr ON l.lead_id = lr.lead_id
                WHERE lp.property_name = ?
                ORDER BY l.status, l.name
            """, (property_name,))
            
            leads = []
            for row in cursor.fetchall():
                leads.append({
                    "lead_id": row[0],
                    "name": row[1],
                    "status": row[2],
                    "budget_max": row[3],
                    "budget_currency": row[4],
                    "room_type": row[5],
                    "location": row[6],
                    "university": row[7]
                })
            
            # Get statistics
            total_leads = len(leads)
            won_leads = sum(1 for l in leads if l["status"] == "Won")
            lost_leads = sum(1 for l in leads if l["status"] == "Lost")
            conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0
            
            # Get room types
            room_types = list(set(l["room_type"] for l in leads if l["room_type"]))
            
            # Get average budget
            budgets = [l["budget_max"] for l in leads if l["budget_max"]]
            avg_budget = sum(budgets) / len(budgets) if budgets else None
            
            return {
                "property_name": property_name,
                "total_leads": total_leads,
                "won_leads": won_leads,
                "lost_leads": lost_leads,
                "conversion_rate": round(conversion_rate, 1),
                "room_types": room_types,
                "average_budget": round(avg_budget, 2) if avg_budget else None,
                "leads": leads
            }
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error getting property details: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error getting property details: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    @ErrorHandler.handle_database_error
    def compare_properties(self, property_names: List[str]) -> Dict[str, Any]:
        """Compare multiple properties side by side"""
        if not property_names or len(property_names) < 2:
            raise ValueError("Must provide at least 2 property names to compare")
        
        comparison = {}
        
        for prop_name in property_names:
            details = self.get_property_details(prop_name)
            comparison[prop_name] = {
                "total_leads": details["total_leads"],
                "won_leads": details["won_leads"],
                "conversion_rate": details["conversion_rate"],
                "average_budget": details["average_budget"],
                "room_types_count": len(details["room_types"])
            }
        
        return {
            "properties": comparison,
            "summary": {
                "total_properties": len(property_names),
                "highest_conversion": max(comparison.items(), key=lambda x: x[1]["conversion_rate"])[0] if comparison else None,
                "most_leads": max(comparison.items(), key=lambda x: x[1]["total_leads"])[0] if comparison else None
            }
        }


if __name__ == "__main__":
    # Test property analytics
    analytics = PropertyAnalytics()
    
    print("="*60)
    print("🏢 PROPERTY ANALYTICS TEST")
    print("="*60)
    
    # Get all analytics
    print("\n📊 Getting property analytics...")
    results = analytics.get_property_analytics()
    
    print(f"\n✅ Popular Properties: {len(results['popular_properties'])}")
    if results['popular_properties']:
        print("\nTop 5 Properties:")
        for i, prop in enumerate(results['popular_properties'][:5], 1):
            print(f"   {i}. {prop['property_name']}: {prop['lead_count']} leads")
    
    print(f"\n✅ Conversion Rates: {len(results['conversion_rates'])} properties")
    if results['conversion_rates']:
        print("\nTop 5 by Conversion Rate:")
        sorted_by_conv = sorted(results['conversion_rates'], key=lambda x: x['conversion_rate'], reverse=True)[:5]
        for i, prop in enumerate(sorted_by_conv, 1):
            print(f"   {i}. {prop['property_name']}: {prop['conversion_rate']}% ({prop['won_leads']}/{prop['total_leads']})")
    
    print("\n" + "="*60)
    print("✅ Property Analytics Working!")
    print("="*60)

