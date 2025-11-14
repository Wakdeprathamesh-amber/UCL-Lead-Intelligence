"""
Data Ingestion Module
Parses CSV lead data and stores in SQLite + prepares text for RAG
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import os


class LeadDataIngestion:
    """Handles ingestion of lead data from CSV into SQLite and text extraction for RAG"""
    
    def __init__(self, db_path: str = "data/leads.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema"""
        
        # Main leads table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                name TEXT,
                mobile_number TEXT,
                status TEXT,
                structured_data TEXT,
                communication_timeline TEXT,
                crm_conversation_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Properties table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                property_name TEXT,
                room_type TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # Amenities table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_amenities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                amenity TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # Extracted fields for easy querying
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_requirements (
                lead_id TEXT PRIMARY KEY,
                nationality TEXT,
                location TEXT,
                university TEXT,
                move_in_date TEXT,
                budget_max REAL,
                budget_currency TEXT,
                room_type TEXT,
                lease_duration_weeks INTEGER,
                visa_status TEXT,
                university_acceptance TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # Objections and concerns
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_objections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                objection_type TEXT,
                objection_text TEXT,
                resolved BOOLEAN,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # Tasks and actionables
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                task_type TEXT,
                description TEXT,
                status TEXT,
                due_date TEXT,
                task_for TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # Text chunks for RAG
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                chunk_type TEXT,
                content TEXT,
                metadata TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        self.conn.commit()
        
    def parse_csv(self, csv_path: str):
        """Parse CSV and insert into database"""
        print(f"📊 Reading CSV from {csv_path}...")
        
        # Read CSV with proper handling of large text fields
        df = pd.read_csv(csv_path, dtype=str)
        
        print(f"✅ Found {len(df)} leads")
        
        for idx, row in df.iterrows():
            lead_id = row['Lead id']
            print(f"\n🔄 Processing lead {idx+1}/{len(df)}: {lead_id} - {row['Name']}")
            
            try:
                # Insert main lead data
                self.cursor.execute("""
                    INSERT OR REPLACE INTO leads 
                    (lead_id, name, mobile_number, status, structured_data, 
                     communication_timeline, crm_conversation_details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
                    lead_id,
                    row['Name'],
                    row['Mobile number'],
                    row['Status'],
                    row['Structured Data'],
                    row['Communication Timeline'],
                    row['CRM Conversation Details']
                ))
                
                # Parse structured data
                structured_data = json.loads(row['Structured Data'])
                self._extract_requirements(lead_id, structured_data)
                self._extract_objections(lead_id, structured_data)
                self._extract_tasks(lead_id, structured_data)
                self._extract_properties(lead_id, structured_data)
                self._extract_amenities(lead_id, structured_data)
                self._extract_rag_documents(lead_id, row, structured_data)
                
                self.conn.commit()
                print(f"   ✅ Successfully processed {lead_id}")
                
            except Exception as e:
                print(f"   ❌ Error processing {lead_id}: {str(e)}")
                continue
        
        print("\n🎉 Data ingestion complete!")
        self._print_stats()
    
    def _extract_requirements(self, lead_id: str, data: Dict):
        """Extract key requirements for structured queries"""
        try:
            reqs = data.get('requirements', {})
            persona = reqs.get('user_persona', {})
            accom = reqs.get('accommodation_requirements', {})
            journey = reqs.get('student_journey', {})
            
            budget = accom.get('budget', {})
            location_list = accom.get('location', [])
            location = location_list[0] if location_list else None
            
            visa_status_list = journey.get('visa_status', [])
            visa_status = visa_status_list[0] if visa_status_list else None
            
            acceptance_list = journey.get('university_acceptance', [])
            acceptance = acceptance_list[0] if acceptance_list else None
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO lead_requirements
                (lead_id, nationality, location, university, move_in_date, 
                 budget_max, budget_currency, room_type, lease_duration_weeks,
                 visa_status, university_acceptance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead_id,
                persona.get('nationality'),
                location,
                accom.get('university'),
                accom.get('move_in_date'),
                budget.get('max'),
                budget.get('currency'),
                accom.get('room_type'),
                accom.get('lease_duration_weeks'),
                visa_status,
                acceptance
            ))
        except Exception as e:
            print(f"   ⚠️  Error extracting requirements: {str(e)}")
    
    def _extract_objections(self, lead_id: str, data: Dict):
        """Extract objections and concerns"""
        try:
            objections = data.get('objections_and_concerns', {}).get('objections', [])
            
            for obj in objections:
                if isinstance(obj, dict):
                    self.cursor.execute("""
                        INSERT INTO lead_objections
                        (lead_id, objection_type, objection_text, resolved)
                        VALUES (?, ?, ?, ?)
                    """, (
                        lead_id,
                        obj.get('type', 'unknown'),
                        obj.get('objection', ''),
                        obj.get('resolved', False)
                    ))
        except Exception as e:
            print(f"   ⚠️  Error extracting objections: {str(e)}")
    
    def _extract_tasks(self, lead_id: str, data: Dict):
        """Extract tasks and actionables"""
        try:
            tasks = data.get('tasks_and_actionables', {}).get('tasks', [])
            
            for task in tasks:
                if isinstance(task, dict):
                    self.cursor.execute("""
                        INSERT INTO lead_tasks
                        (lead_id, task_type, description, status, due_date, task_for)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        lead_id,
                        task.get('type', ''),
                        task.get('description', ''),
                        task.get('status', ''),
                        task.get('due', ''),
                        task.get('task_for', '')
                    ))
        except Exception as e:
            print(f"   ⚠️  Error extracting tasks: {str(e)}")
    
    def _extract_properties(self, lead_id: str, data: Dict):
        """Extract properties under consideration"""
        try:
            props = data.get('requirements', {}).get('properties_under_consideration', {})
            
            # Extract property names
            for prop_name in props.get('properties_considered', []):
                if prop_name:
                    self.cursor.execute("""
                        INSERT INTO lead_properties (lead_id, property_name)
                        VALUES (?, ?)
                    """, (lead_id, prop_name))
            
            # Extract room types
            for room_type in props.get('rooms_considered', []):
                if room_type:
                    # Check if property exists
                    self.cursor.execute("""
                        SELECT id FROM lead_properties 
                        WHERE lead_id = ? AND room_type IS NULL
                    """, (lead_id,))
                    
                    existing = self.cursor.fetchone()
                    
                    if existing:
                        # Update existing
                        self.cursor.execute("""
                            UPDATE lead_properties 
                            SET room_type = ?
                            WHERE id = ?
                        """, (room_type, existing[0]))
                    else:
                        # Insert new
                        self.cursor.execute("""
                            INSERT INTO lead_properties (lead_id, room_type)
                            VALUES (?, ?)
                        """, (lead_id, room_type))
                    
        except Exception as e:
            print(f"   ⚠️  Error extracting properties: {str(e)}")
    
    def _extract_amenities(self, lead_id: str, data: Dict):
        """Extract amenities requested"""
        try:
            amenities = data.get('requirements', {}).get('accommodation_requirements', {}).get('amenities', [])
            
            for amenity in amenities:
                if amenity:
                    self.cursor.execute("""
                        INSERT INTO lead_amenities (lead_id, amenity)
                        VALUES (?, ?)
                    """, (lead_id, amenity))
        except Exception as e:
            print(f"   ⚠️  Error extracting amenities: {str(e)}")
    
    def _extract_rag_documents(self, lead_id: str, row: pd.Series, data: Dict):
        """Extract text chunks for RAG embedding"""
        try:
            # 1. Conversation Summary
            conv_summary = data.get('conversation_summary', {})
            if conv_summary:
                summary_text = json.dumps(conv_summary, indent=2)
                self.cursor.execute("""
                    INSERT INTO rag_documents (lead_id, chunk_type, content, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    lead_id,
                    'conversation_summary',
                    summary_text,
                    json.dumps({'lead_name': row['Name'], 'status': row['Status']})
                ))
            
            # 2. Objections
            objections = data.get('objections_and_concerns', {})
            if objections:
                objections_text = json.dumps(objections, indent=2)
                self.cursor.execute("""
                    INSERT INTO rag_documents (lead_id, chunk_type, content, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    lead_id,
                    'objections_and_concerns',
                    objections_text,
                    json.dumps({'lead_name': row['Name'], 'status': row['Status']})
                ))
            
            # 3. Notes and Key Takeaways
            notes = data.get('notes_and_key_takeaways', {})
            if notes:
                notes_text = json.dumps(notes, indent=2)
                self.cursor.execute("""
                    INSERT INTO rag_documents (lead_id, chunk_type, content, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    lead_id,
                    'notes_and_key_takeaways',
                    notes_text,
                    json.dumps({'lead_name': row['Name'], 'status': row['Status']})
                ))
            
            # 4. Key Insights from Conversation Summary
            insights = conv_summary.get('conversation_summary', {}).get('sections', {})
            if insights:
                insights_text = json.dumps(insights, indent=2)
                self.cursor.execute("""
                    INSERT INTO rag_documents (lead_id, chunk_type, content, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    lead_id,
                    'conversation_insights',
                    insights_text,
                    json.dumps({'lead_name': row['Name'], 'status': row['Status']})
                ))
            
            # 5. CRM Conversation Details (contains property booking info)
            if row.get('CRM Conversation Details') and len(str(row['CRM Conversation Details'])) > 50:
                self.cursor.execute("""
                    INSERT INTO rag_documents (lead_id, chunk_type, content, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    lead_id,
                    'crm_conversation_details',
                    row['CRM Conversation Details'],
                    json.dumps({'lead_name': row['Name'], 'status': row['Status']})
                ))
            
        except Exception as e:
            print(f"   ⚠️  Error extracting RAG documents: {str(e)}")
    
    def _print_stats(self):
        """Print ingestion statistics"""
        print("\n" + "="*60)
        print("📈 INGESTION STATISTICS")
        print("="*60)
        
        # Total leads
        self.cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = self.cursor.fetchone()[0]
        print(f"Total Leads: {total_leads}")
        
        # Status breakdown
        self.cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
        print("\nStatus Breakdown:")
        for status, count in self.cursor.fetchall():
            print(f"  {status}: {count}")
        
        # RAG documents
        self.cursor.execute("SELECT COUNT(*) FROM rag_documents")
        total_docs = self.cursor.fetchone()[0]
        print(f"\nRAG Documents: {total_docs}")
        
        # Objections
        self.cursor.execute("SELECT COUNT(*) FROM lead_objections")
        total_objections = self.cursor.fetchone()[0]
        print(f"Total Objections: {total_objections}")
        
        # Tasks
        self.cursor.execute("SELECT COUNT(*) FROM lead_tasks")
        total_tasks = self.cursor.fetchone()[0]
        print(f"Total Tasks: {total_tasks}")
        
        # Properties
        self.cursor.execute("SELECT COUNT(*) FROM lead_properties")
        total_props = self.cursor.fetchone()[0]
        print(f"Total Properties: {total_props}")
        
        # Amenities
        self.cursor.execute("SELECT COUNT(*) FROM lead_amenities")
        total_amenities = self.cursor.fetchone()[0]
        print(f"Total Amenities: {total_amenities}")
        
        print("="*60 + "\n")
    
    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    # Run ingestion
    ingestion = LeadDataIngestion(db_path="data/leads.db")
    ingestion.parse_csv("Data/UCL Leads Data - Sheet1.csv")
    ingestion.close()
    print("✅ Data ingestion complete!")
