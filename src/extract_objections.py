"""
Extract Objections from Conversations
Extracts objections and concerns from lead conversations and populates lead_objections table
"""

import sqlite3
import json
import re
from typing import List, Dict, Any
import os


class ObjectionExtractor:
    """Extract objections from lead conversations"""
    
    def __init__(self, db_path: str = "data/leads.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def _ensure_table_exists(self):
        """Ensure lead_objections table exists"""
        # Check if table exists and has correct schema
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='lead_objections'
        """)
        
        if not self.cursor.fetchone():
            # Create table
            self.cursor.execute("""
                CREATE TABLE lead_objections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT,
                    objection_text TEXT,
                    objection_type TEXT,
                    source TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
                )
            """)
        else:
            # Check if source column exists
            self.cursor.execute("PRAGMA table_info(lead_objections)")
            columns = [col[1] for col in self.cursor.fetchall()]
            if 'source' not in columns:
                # Add source column
                self.cursor.execute("""
                    ALTER TABLE lead_objections ADD COLUMN source TEXT
                """)
        
        # Add index
        try:
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_objections_lead_id 
                ON lead_objections(lead_id)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_objections_type 
                ON lead_objections(objection_type)
            """)
        except:
            pass  # Indexes may already exist
        
        self.conn.commit()
    
    def _extract_from_structured_data(self, lead_id: str, structured_data: Dict) -> List[Dict]:
        """Extract objections from structured data"""
        objections = []
        
        # Check conversation summary
        if 'conversation_summary' in structured_data:
            summary = structured_data['conversation_summary']
            
            # Look for objections section
            if isinstance(summary, dict):
                # Check for explicit objections
                if 'objections' in summary:
                    for obj in summary.get('objections', []):
                        if isinstance(obj, dict):
                            objections.append({
                                'lead_id': lead_id,
                                'objection_text': obj.get('objection', obj.get('text', '')),
                                'objection_type': obj.get('type', 'general'),
                                'source': 'conversation_summary'
                            })
                        elif isinstance(obj, str):
                            objections.append({
                                'lead_id': lead_id,
                                'objection_text': obj,
                                'objection_type': 'general',
                                'source': 'conversation_summary'
                            })
                
                # Check for concerns
                if 'concerns' in summary:
                    for concern in summary.get('concerns', []):
                        if isinstance(concern, dict):
                            objections.append({
                                'lead_id': lead_id,
                                'objection_text': concern.get('concern', concern.get('text', '')),
                                'objection_type': concern.get('type', 'concern'),
                                'source': 'conversation_summary'
                            })
                        elif isinstance(concern, str):
                            objections.append({
                                'lead_id': lead_id,
                                'objection_text': concern,
                                'objection_type': 'concern',
                                'source': 'conversation_summary'
                            })
                
                # Check for key concerns in student overview
                if 'student_overview' in summary:
                    overview = summary['student_overview']
                    if isinstance(overview, dict) and 'key_concerns' in overview:
                        for concern in overview.get('key_concerns', []):
                            objections.append({
                                'lead_id': lead_id,
                                'objection_text': concern if isinstance(concern, str) else str(concern),
                                'objection_type': 'key_concern',
                                'source': 'student_overview'
                            })
        
        # Check conversation insights
        if 'conversation_insights' in structured_data:
            insights = structured_data['conversation_insights']
            if isinstance(insights, dict):
                # Check for objections_and_concerns
                if 'objections_and_concerns' in insights:
                    concerns = insights['objections_and_concerns']
                    if isinstance(concerns, list):
                        for concern in concerns:
                            objections.append({
                                'lead_id': lead_id,
                                'objection_text': concern if isinstance(concern, str) else str(concern),
                                'objection_type': 'insight_concern',
                                'source': 'conversation_insights'
                            })
                    elif isinstance(concerns, str):
                        objections.append({
                            'lead_id': lead_id,
                            'objection_text': concerns,
                            'objection_type': 'insight_concern',
                            'source': 'conversation_insights'
                        })
        
        return objections
    
    def _extract_from_text(self, lead_id: str, text: str, source: str) -> List[Dict]:
        """Extract objections from raw text using pattern matching"""
        objections = []
        
        if not text or len(text) < 20:
            return objections
        
        # Common objection patterns
        objection_patterns = [
            (r'(?:concern|worried|worries|anxious|anxiety|hesitant|hesitation).*?(?:about|regarding|with|that)\s+([^.!?]+)', 'concern'),
            (r'(?:objection|object|against|opposed).*?(?:to|about|regarding)\s+([^.!?]+)', 'objection'),
            (r'(?:issue|problem|difficulty|challenge).*?(?:with|regarding|about)\s+([^.!?]+)', 'issue'),
            (r'(?:too\s+)?(?:expensive|costly|price|pricing|budget).*?(?:concern|issue|problem)', 'budget'),
            (r'(?:location|area|neighborhood|safety|security).*?(?:concern|worried|issue)', 'location'),
            (r'(?:room|accommodation|property).*?(?:not|doesn\'t|isn\'t).*?(?:suitable|good|right|appropriate)', 'property'),
        ]
        
        text_lower = text.lower()
        
        for pattern, obj_type in objection_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                objection_text = match.group(0).strip()
                if len(objection_text) > 20 and len(objection_text) < 500:
                    objections.append({
                        'lead_id': lead_id,
                        'objection_text': objection_text,
                        'objection_type': obj_type,
                        'source': source
                    })
        
        return objections
    
    def extract_all_objections(self):
        """Extract objections from all leads"""
        self._ensure_table_exists()
        
        print("🔍 Extracting objections from lead conversations...")
        print("="*60)
        
        # Clear existing objections (optional - comment out to keep existing)
        # self.cursor.execute("DELETE FROM lead_objections")
        # self.conn.commit()
        
        # Get all leads with structured data
        self.cursor.execute("""
            SELECT lead_id, structured_data, communication_timeline, crm_conversation_details
            FROM leads
            WHERE structured_data IS NOT NULL AND structured_data != ''
        """)
        
        leads = self.cursor.fetchall()
        print(f"📊 Processing {len(leads)} leads...")
        
        total_objections = 0
        
        for lead_id, structured_data_json, timeline, crm_details in leads:
            try:
                structured_data = json.loads(structured_data_json) if structured_data_json else {}
                
                # Extract from structured data
                objections = self._extract_from_structured_data(lead_id, structured_data)
                
                # Extract from timeline text
                if timeline:
                    timeline_objections = self._extract_from_text(lead_id, timeline, 'communication_timeline')
                    objections.extend(timeline_objections)
                
                # Extract from CRM details
                if crm_details:
                    crm_objections = self._extract_from_text(lead_id, crm_details, 'crm_conversation_details')
                    objections.extend(crm_objections)
                
                # Insert objections
                for obj in objections:
                    if obj['objection_text'] and len(obj['objection_text'].strip()) > 10:
                        # Check if already exists (avoid duplicates)
                        self.cursor.execute("""
                            SELECT COUNT(*) FROM lead_objections
                            WHERE lead_id = ? AND objection_text = ?
                        """, (lead_id, obj['objection_text'][:500]))
                        
                        if self.cursor.fetchone()[0] == 0:
                            self.cursor.execute("""
                                INSERT INTO lead_objections 
                                (lead_id, objection_text, objection_type, source)
                                VALUES (?, ?, ?, ?)
                            """, (
                                obj['lead_id'],
                                obj['objection_text'][:500],  # Limit length
                                obj['objection_type'],
                                obj['source']
                            ))
                            total_objections += 1
                
            except Exception as e:
                print(f"   ⚠️  Error processing lead {lead_id}: {str(e)}")
                continue
        
        self.conn.commit()
        
        # Get statistics
        self.cursor.execute("SELECT COUNT(*) FROM lead_objections")
        total_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT objection_type, COUNT(*) 
            FROM lead_objections 
            GROUP BY objection_type
        """)
        type_counts = dict(self.cursor.fetchall())
        
        print("="*60)
        print(f"✅ Extracted {total_objections} new objections")
        print(f"📊 Total objections in database: {total_count}")
        print(f"📋 By type:")
        for obj_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {obj_type}: {count}")
        
        self.conn.close()
        return total_objections


if __name__ == "__main__":
    print("🚀 Extracting Objections from Conversations")
    print("="*60)
    
    extractor = ObjectionExtractor()
    extractor.extract_all_objections()
    
    print("\n✅ Objection extraction complete!")

