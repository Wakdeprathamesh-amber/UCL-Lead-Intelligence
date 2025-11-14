"""
Aggregate Data Ingestion Module
Handles ingestion of high-level aggregate lead data (1,525 leads)
Separate from detailed conversation data
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import os


class AggregateDataIngestion:
    """Handles ingestion of aggregate lead data from CSV into SQLite"""
    
    def __init__(self, db_path: str = "data/leads_aggregate.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema for aggregate data"""
        
        # Main aggregate leads table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS aggregate_leads (
                lead_id TEXT PRIMARY KEY,
                lead_date TEXT,
                partner_id TEXT,
                subpartner_id TEXT,
                subpartner_name TEXT,
                lost_reason TEXT,
                source_country_short_name TEXT,
                source_country TEXT,
                state TEXT,
                state_updated TEXT,
                city_name TEXT,
                country_name TEXT,
                partner_state TEXT,
                repeat INTEGER DEFAULT 0,
                repeat_all INTEGER DEFAULT 0,
                singular_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indexes for common queries
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_aggregate_state 
            ON aggregate_leads(state)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_aggregate_lost_reason 
            ON aggregate_leads(lost_reason)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_aggregate_country 
            ON aggregate_leads(source_country)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_aggregate_city 
            ON aggregate_leads(city_name)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_aggregate_date 
            ON aggregate_leads(lead_date)
        """)
        
        self.conn.commit()
    
    def parse_csv(self, csv_path: str):
        """Parse aggregate CSV and insert into database"""
        print(f"📊 Reading aggregate CSV from {csv_path}...")
        
        # Read CSV
        df = pd.read_csv(csv_path, dtype=str)
        
        print(f"✅ Found {len(df)} aggregate leads")
        
        # Clear existing data
        self.cursor.execute("DELETE FROM aggregate_leads")
        print("🗑️  Cleared existing aggregate data")
        
        inserted = 0
        errors = 0
        
        for idx, row in df.iterrows():
            try:
                # Clean lead_id (remove commas)
                lead_id = str(row['lead_id']).replace(',', '').strip()
                
                # Parse repeat flags
                repeat = 1 if str(row.get('repeat', 'false')).lower() == 'true' else 0
                repeat_all = 1 if str(row.get('repeat_all', 'false')).lower() == 'true' else 0
                
                # Insert lead
                self.cursor.execute("""
                    INSERT INTO aggregate_leads 
                    (lead_id, lead_date, partner_id, subpartner_id, subpartner_name,
                     lost_reason, source_country_short_name, source_country, state,
                     state_updated, city_name, country_name, partner_state,
                     repeat, repeat_all, singular_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead_id,
                    str(row.get('lead_date', '')),
                    str(row.get('partner_id', '')).replace(',', '').strip(),
                    str(row.get('subpartner_id', '')).replace(',', '').strip(),
                    str(row.get('subpartner_name', '')),
                    str(row.get('lost_reason', '')),
                    str(row.get('source_country_short_name', '')),
                    str(row.get('source_country', '')),
                    str(row.get('state', '')),
                    str(row.get('state_updated', '')),
                    str(row.get('city_name', '')),
                    str(row.get('country_name', '')),
                    str(row.get('partner_state', '')),
                    repeat,
                    repeat_all,
                    str(row.get('singular_id', ''))
                ))
                
                inserted += 1
                
                if (idx + 1) % 100 == 0:
                    print(f"   ✅ Processed {idx + 1}/{len(df)} leads...")
                    self.conn.commit()
                
            except Exception as e:
                errors += 1
                if errors <= 5:  # Only show first 5 errors
                    print(f"   ❌ Error processing row {idx+1}: {str(e)}")
                continue
        
        self.conn.commit()
        print(f"\n🎉 Aggregate data ingestion complete!")
        print(f"   ✅ Inserted: {inserted} leads")
        print(f"   ❌ Errors: {errors} leads")
        self._print_stats()
    
    def _print_stats(self):
        """Print statistics about ingested data"""
        print("\n" + "="*80)
        print("📊 AGGREGATE DATA STATISTICS")
        print("="*80)
        
        # Total leads
        self.cursor.execute("SELECT COUNT(*) FROM aggregate_leads")
        total = self.cursor.fetchone()[0]
        print(f"\n📈 Total Aggregate Leads: {total}")
        
        # Status breakdown
        self.cursor.execute("""
            SELECT state, COUNT(*) as count 
            FROM aggregate_leads 
            GROUP BY state 
            ORDER BY count DESC
        """)
        print("\n📊 Status Breakdown:")
        for status, count in self.cursor.fetchall():
            pct = (count / total * 100) if total > 0 else 0
            print(f"   • {status}: {count} ({pct:.1f}%)")
        
        # Lost reasons
        self.cursor.execute("""
            SELECT lost_reason, COUNT(*) as count 
            FROM aggregate_leads 
            WHERE lost_reason IS NOT NULL AND lost_reason != ''
            GROUP BY lost_reason 
            ORDER BY count DESC
            LIMIT 10
        """)
        print("\n❌ Top Lost Reasons:")
        for reason, count in self.cursor.fetchall():
            print(f"   • {reason}: {count}")
        
        # Country breakdown
        self.cursor.execute("""
            SELECT source_country, COUNT(*) as count 
            FROM aggregate_leads 
            WHERE source_country IS NOT NULL AND source_country != ''
            GROUP BY source_country 
            ORDER BY count DESC
            LIMIT 10
        """)
        print("\n🌍 Top Source Countries:")
        for country, count in self.cursor.fetchall():
            print(f"   • {country}: {count}")
        
        # Repeat leads
        self.cursor.execute("SELECT COUNT(*) FROM aggregate_leads WHERE repeat = 1")
        repeat_count = self.cursor.fetchone()[0]
        print(f"\n🔄 Repeat Leads: {repeat_count} ({repeat_count/total*100:.1f}%)")
        
        print("="*80)
    
    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    # Run aggregate ingestion
    ingestion = AggregateDataIngestion(db_path="data/leads_aggregate.db")
    ingestion.parse_csv("Data/UCL overall leads data.csv")
    ingestion.close()
    print("✅ Aggregate data ingestion complete!")

