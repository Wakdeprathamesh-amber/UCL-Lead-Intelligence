"""
Exported Dataset Ingestion Module
Ingests JSON dataset (401 leads) with timeline events and transcripts
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import glob


class ExportedDataIngestion:
    """Handles ingestion of exported JSON dataset into SQLite"""
    
    def __init__(self, db_path: str = "data/leads.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_enhanced_tables()
    
    def _create_enhanced_tables(self):
        """Create enhanced database schema with timeline events and transcripts"""
        
        # Keep existing tables, add new ones
        # Timeline events (individual messages/calls)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                event_id INTEGER,
                event_type TEXT,
                timestamp TEXT,
                content TEXT,
                source TEXT,
                direction TEXT,
                agent_id INTEGER,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # Call transcripts
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                call_id TEXT,
                transcript_text TEXT,
                record_url TEXT,
                transcription_status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # Enhanced RAG documents (individual events)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                event_id INTEGER,
                document_type TEXT,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # CRM data table (from direct CRM export)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS crm_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crm_id TEXT,
                lead_id TEXT,
                budget_full REAL,
                budget_currency TEXT,
                lost_reason TEXT,
                move_in_date TEXT,
                lease_duration TEXT,
                lease_duration_days INTEGER,
                state TEXT,
                created_at TEXT,
                location_name TEXT,
                location_state TEXT,
                location_country TEXT,
                location_locality TEXT,
                street_number TEXT,
                lead_name TEXT,
                lead_email TEXT,
                lead_phone TEXT,
                phone_country TEXT,
                inventory_id TEXT,
                property_name TEXT,
                source_details TEXT,
                tags TEXT,
                display_name TEXT,
                partner_id TEXT,
                created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
            )
        """)
        
        # Create indexes for performance
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_lead_id ON timeline_events(lead_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_event_type ON timeline_events(event_type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_timestamp ON timeline_events(timestamp)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_lead_id ON call_transcripts(lead_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_rag_events_lead_id ON rag_documents_events(lead_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_rag_events_type ON rag_documents_events(document_type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_lead_id ON crm_data(lead_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_crm_id ON crm_data(crm_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_phone ON crm_data(lead_phone)")
        
        self.conn.commit()
        print("✅ Enhanced database schema created")
    
    def ingest_summaries(self, summaries_path: str):
        """Ingest summaries.json - main lead data"""
        print(f"\n📊 Loading summaries from {summaries_path}...")
        
        with open(summaries_path, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        
        print(f"✅ Found {len(summaries)} leads in summaries.json")
        
        for idx, summary in enumerate(summaries, 1):
            lead_id = str(summary.get('lead_id', ''))
            mobile_number = summary.get('mobile_number', '')
            email = summary.get('email')
            
            if not lead_id:
                print(f"   ⚠️  Skipping lead {idx}: No lead_id")
                continue
            
            try:
                # Extract name from requirements
                name = "Unknown"
                if 'requirements' in summary and 'user_persona' in summary['requirements']:
                    name = summary['requirements']['user_persona'].get('name', 'Unknown')
                
                # Extract status from conversation_summary if available
                status = "Contacted"  # Default status
                if 'conversation_summary' in summary:
                    conv_summary = summary['conversation_summary']
                    # Try to extract from current_status section
                    if isinstance(conv_summary, dict) and 'conversation_summary' in conv_summary:
                        inner = conv_summary['conversation_summary']
                        if isinstance(inner, dict) and 'sections' in inner:
                            sections = inner['sections']
                            if 'current_status' in sections:
                                current_status = sections['current_status']
                                if isinstance(current_status, dict):
                                    booking_stage = current_status.get('booking_stage', '')
                                    # Map booking_stage to status
                                    if 'won' in booking_stage.lower() or 'booked' in booking_stage.lower():
                                        status = "Won"
                                    elif 'lost' in booking_stage.lower():
                                        status = "Lost"
                                    elif 'opportunity' in booking_stage.lower():
                                        status = "Oppurtunity"
                                    elif 'disputed' in booking_stage.lower():
                                        status = "Disputed"
                
                # Also try to get status from aggregate CSV if available
                try:
                    import pandas as pd
                    aggregate_csv = "Data/UCL overall leads data.csv"
                    if os.path.exists(aggregate_csv):
                        agg_df = pd.read_csv(aggregate_csv, dtype=str)
                        matching = agg_df[agg_df['lead_id'].astype(str) == lead_id]
                        if not matching.empty:
                            agg_status = matching.iloc[0]['state']
                            if agg_status and agg_status.lower() not in ['nan', 'none', '']:
                                # Map aggregate states to our status format
                                status_map = {
                                    'won': 'Won',
                                    'lost': 'Lost',
                                    'opportunity': 'Oppurtunity',
                                    'contacted': 'Contacted',
                                    'disputed': 'Disputed'
                                }
                                status_lower = agg_status.lower()
                                if status_lower in status_map:
                                    status = status_map[status_lower]
                                elif status == "Contacted":  # Only override if still default
                                    status = agg_status.capitalize()
                except Exception as e:
                    pass  # Silently fail, use default or extracted status
                
                # Store summary data as JSON
                summary_json = json.dumps(summary)
                
                # Insert or update lead
                self.cursor.execute("""
                    INSERT OR REPLACE INTO leads 
                    (lead_id, name, mobile_number, status, structured_data, 
                     communication_timeline, crm_conversation_details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead_id,
                    name,
                    mobile_number,
                    status,
                    summary_json,  # Store full summary as structured_data
                    "",  # Timeline will be in separate table
                    ""   # CRM details in summary
                ))
                
                # Extract and store requirements
                if 'requirements' in summary:
                    self._extract_requirements(lead_id, summary['requirements'])
                
                # Extract and store tasks
                if 'tasks_actionables' in summary:
                    self._extract_tasks(lead_id, summary['tasks_actionables'])
                
                # Extract conversation summary for RAG
                if 'conversation_summary' in summary:
                    self._extract_conversation_summary(lead_id, summary['conversation_summary'])
                
                if idx % 50 == 0:
                    print(f"   ✅ Processed {idx}/{len(summaries)} leads...")
                
            except Exception as e:
                print(f"   ❌ Error processing lead {lead_id}: {str(e)}")
                continue
        
        self.conn.commit()
        print(f"✅ Successfully ingested {len(summaries)} leads from summaries")
    
    def _extract_requirements(self, lead_id: str, requirements: Dict):
        """Extract requirements from summary"""
        try:
            acc_req = requirements.get('accommodation_requirements', {})
            user_persona = requirements.get('user_persona', {})
            
            location = acc_req.get('location', [])
            location_str = ', '.join(location) if isinstance(location, list) else str(location)
            
            university = acc_req.get('university', '')
            move_in_date = acc_req.get('move_in_date')
            budget = acc_req.get('budget', {})
            budget_max = budget.get('max') if isinstance(budget, dict) else None
            budget_currency = budget.get('currency', 'GBP') if isinstance(budget, dict) else 'GBP'
            room_type = acc_req.get('room_type', '')
            lease_duration = acc_req.get('lease_duration_weeks')
            
            nationality = user_persona.get('nationality')
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO lead_requirements
                (lead_id, nationality, location, university, move_in_date,
                 budget_max, budget_currency, room_type, lease_duration_weeks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead_id, nationality, location_str, university, move_in_date,
                budget_max, budget_currency, room_type, lease_duration
            ))
        except Exception as e:
            print(f"   ⚠️  Error extracting requirements for {lead_id}: {str(e)}")
    
    def _extract_tasks(self, lead_id: str, tasks_data: Dict):
        """Extract tasks from summary"""
        try:
            tasks = tasks_data.get('tasks', [])
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
                        task.get('status', 'pending'),
                        task.get('due', ''),
                        task.get('task_for', 'agent')
                    ))
        except Exception as e:
            print(f"   ⚠️  Error extracting tasks for {lead_id}: {str(e)}")
    
    def _extract_conversation_summary(self, lead_id: str, conversation_summary: Dict):
        """Extract conversation summary for RAG"""
        try:
            summary_text = json.dumps(conversation_summary)
            self.cursor.execute("""
                INSERT INTO rag_documents
                (lead_id, chunk_type, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                lead_id,
                'conversation_summary',
                summary_text,
                json.dumps({'lead_id': lead_id, 'source': 'exported_dataset'})
            ))
        except Exception as e:
            print(f"   ⚠️  Error extracting conversation summary for {lead_id}: {str(e)}")
    
    def ingest_timeline_events(self, rag_dataset_path: str):
        """Ingest timeline events from rag_dataset.json"""
        print(f"\n📊 Loading timeline events from {rag_dataset_path}...")
        
        with open(rag_dataset_path, 'r', encoding='utf-8') as f:
            rag_data = json.load(f)
        
        print(f"✅ Found {len(rag_data)} leads with timeline events")
        
        total_events = 0
        for idx, lead_data in enumerate(rag_data, 1):
            lead_id = str(lead_data.get('lead_id', ''))
            if not lead_id:
                continue
            
            timeline_events = lead_data.get('content', {}).get('timeline_events', [])
            
            for event in timeline_events:
                try:
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO timeline_events
                        (lead_id, event_id, event_type, timestamp, content, source,
                         direction, agent_id, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        lead_id,
                        event.get('id'),
                        event.get('event_type', ''),
                        event.get('timestamp', ''),
                        event.get('content', ''),
                        event.get('source', ''),
                        event.get('direction', ''),
                        event.get('agent_id'),
                        json.dumps(event.get('raw_data', '')) if event.get('raw_data') else None
                    ))
                    
                    # Create RAG document for event
                    if event.get('content'):
                        event_metadata = {
                            'event_type': event.get('event_type', ''),
                            'timestamp': event.get('timestamp', ''),
                            'source': event.get('source', ''),
                            'direction': event.get('direction', ''),
                            'lead_id': lead_id
                        }
                        
                        self.cursor.execute("""
                            INSERT INTO rag_documents_events
                            (lead_id, event_id, document_type, content, metadata)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            lead_id,
                            event.get('id'),
                            event.get('event_type', 'whatsapp'),
                            event.get('content', ''),
                            json.dumps(event_metadata)
                        ))
                    
                    total_events += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Error processing event {event.get('id')} for lead {lead_id}: {str(e)}")
                    continue
            
            if idx % 50 == 0:
                print(f"   ✅ Processed {idx}/{len(rag_data)} leads, {total_events} events...")
        
        self.conn.commit()
        print(f"✅ Successfully ingested {total_events} timeline events")
    
    def ingest_transcripts(self, mcp_folder: str):
        """Ingest call transcripts from mcp folder"""
        print(f"\n📊 Loading call transcripts from {mcp_folder}...")
        
        mcp_files = glob.glob(os.path.join(mcp_folder, "lead_lead_*.json"))
        print(f"✅ Found {len(mcp_files)} MCP files")
        
        total_transcripts = 0
        for idx, file_path in enumerate(mcp_files, 1):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    mcp_data = json.load(f)
                
                lead_id = str(mcp_data.get('id', '').replace('lead_', ''))
                if not lead_id:
                    continue
                
                transcripts = mcp_data.get('transcripts', [])
                for transcript in transcripts:
                    try:
                        self.cursor.execute("""
                            INSERT OR REPLACE INTO call_transcripts
                            (lead_id, call_id, transcript_text, record_url, transcription_status)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            lead_id,
                            transcript.get('call_id', ''),
                            transcript.get('transcript_text', ''),
                            transcript.get('record_url', ''),
                            transcript.get('transcription_status', 'completed')
                        ))
                        
                        # Create RAG document for transcript
                        if transcript.get('transcript_text'):
                            transcript_metadata = {
                                'call_id': transcript.get('call_id', ''),
                                'record_url': transcript.get('record_url', ''),
                                'lead_id': lead_id
                            }
                            
                            self.cursor.execute("""
                                INSERT INTO rag_documents_events
                                (lead_id, event_id, document_type, content, metadata)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                lead_id,
                                transcript.get('id'),
                                'transcript',
                                transcript.get('transcript_text', ''),
                                json.dumps(transcript_metadata)
                            ))
                        
                        total_transcripts += 1
                        
                    except Exception as e:
                        print(f"   ⚠️  Error processing transcript for lead {lead_id}: {str(e)}")
                        continue
                
                if idx % 50 == 0:
                    print(f"   ✅ Processed {idx}/{len(mcp_files)} files, {total_transcripts} transcripts...")
                    
            except Exception as e:
                print(f"   ⚠️  Error processing file {file_path}: {str(e)}")
                continue
        
        self.conn.commit()
        print(f"✅ Successfully ingested {total_transcripts} call transcripts")
    
    def print_stats(self):
        """Print ingestion statistics"""
        print("\n" + "="*60)
        print("📊 INGESTION STATISTICS")
        print("="*60)
        
        # Leads count
        self.cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = self.cursor.fetchone()[0]
        print(f"Total Leads: {total_leads}")
        
        # Status breakdown
        self.cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
        status_breakdown = self.cursor.fetchall()
        print("\nStatus Breakdown:")
        for status, count in status_breakdown:
            print(f"  {status}: {count}")
        
        # Timeline events
        self.cursor.execute("SELECT COUNT(*) FROM timeline_events")
        total_events = self.cursor.fetchone()[0]
        print(f"\nTimeline Events: {total_events}")
        
        # Event type breakdown
        self.cursor.execute("SELECT event_type, COUNT(*) FROM timeline_events GROUP BY event_type")
        event_types = self.cursor.fetchall()
        print("\nEvent Type Breakdown:")
        for event_type, count in event_types:
            print(f"  {event_type}: {count}")
        
        # Call transcripts
        self.cursor.execute("SELECT COUNT(*) FROM call_transcripts")
        total_transcripts = self.cursor.fetchone()[0]
        print(f"\nCall Transcripts: {total_transcripts}")
        
        # RAG documents
        self.cursor.execute("SELECT COUNT(*) FROM rag_documents")
        rag_docs = self.cursor.fetchone()[0]
        print(f"\nRAG Documents (summaries): {rag_docs}")
        
        # RAG event documents
        self.cursor.execute("SELECT COUNT(*) FROM rag_documents_events")
        rag_event_docs = self.cursor.fetchone()[0]
        print(f"RAG Event Documents: {rag_event_docs}")
        
        # CRM data
        self.cursor.execute("SELECT COUNT(*) FROM crm_data")
        crm_count = self.cursor.fetchone()[0]
        print(f"\nCRM Data Records: {crm_count}")
        
        print("="*60 + "\n")
    
    def ingest_crm_data(self, crm_csv_path: str):
        """Ingest CRM data from CSV file"""
        print(f"\n📊 Loading CRM data from {crm_csv_path}...")
        
        if not os.path.exists(crm_csv_path):
            print(f"⚠️  CRM CSV file not found: {crm_csv_path}")
            return
        
        # Read CSV
        df = pd.read_csv(crm_csv_path, dtype=str)
        print(f"✅ Found {len(df)} CRM records")
        
        # Clear existing CRM data
        self.cursor.execute("DELETE FROM crm_data")
        print("🗑️  Cleared existing CRM data")
        
        matched = 0
        updated_status = 0
        inserted = 0
        
        for idx, row in df.iterrows():
            try:
                # Clean CRM ID (remove commas)
                crm_id = str(row['id']).replace(',', '').strip()
                
                # Extract property name from location_name
                property_name = row.get('location_name', '')
                
                # Try to match with existing lead
                lead_id = None
                
                # Method 1: Match by CRM ID (if stored in lead_id)
                if crm_id:
                    self.cursor.execute("SELECT lead_id FROM leads WHERE lead_id = ?", (crm_id,))
                    result = self.cursor.fetchone()
                    if result:
                        lead_id = result[0]
                
                # Method 2: Match by phone number
                if not lead_id and pd.notna(row.get('lead_phone')):
                    phone = str(row['lead_phone']).strip()
                    # Try with and without country code
                    self.cursor.execute("SELECT lead_id FROM leads WHERE mobile_number LIKE ? OR mobile_number LIKE ?", 
                                       (f"%{phone[-10:]}", f"%{phone}"))
                    result = self.cursor.fetchone()
                    if result:
                        lead_id = result[0]
                
                # Method 3: Match by name
                if not lead_id and pd.notna(row.get('lead_name')):
                    name = str(row['lead_name']).strip()
                    self.cursor.execute("SELECT lead_id FROM leads WHERE name = ? OR name LIKE ?", 
                                       (name, f"%{name}%"))
                    result = self.cursor.fetchone()
                    if result:
                        lead_id = result[0]
                
                # Extract status from CRM state
                crm_state = str(row.get('state', '')).strip().lower() if pd.notna(row.get('state')) else ''
                status = None
                if crm_state:
                    status_map = {
                        'won': 'Won',
                        'lost': 'Lost',
                        'opportunity': 'Oppurtunity',
                        'contacted': 'Contacted',
                        'disputed': 'Disputed'
                    }
                    if crm_state in status_map:
                        status = status_map[crm_state]
                    elif 'won' in crm_state or 'booked' in crm_state:
                        status = 'Won'
                    elif 'lost' in crm_state:
                        status = 'Lost'
                
                # Update lead status if we found a match and status
                if lead_id and status:
                    self.cursor.execute("UPDATE leads SET status = ? WHERE lead_id = ?", (status, lead_id))
                    updated_status += 1
                    matched += 1
                
                # Parse budget_full (handle formats like "£292/week" or "292")
                budget_full = None
                if pd.notna(row.get('budget_full')):
                    budget_str = str(row['budget_full']).strip()
                    # Extract number from strings like "£292/week" or "£292"
                    import re
                    match = re.search(r'[\d.]+', budget_str.replace(',', ''))
                    if match:
                        try:
                            budget_full = float(match.group())
                        except:
                            pass
                
                # Insert CRM data
                self.cursor.execute("""
                    INSERT INTO crm_data 
                    (crm_id, lead_id, budget_full, budget_currency, lost_reason, move_in_date,
                     lease_duration, lease_duration_days, state, created_at, location_name,
                     location_state, location_country, location_locality, street_number,
                     lead_name, lead_email, lead_phone, phone_country, inventory_id,
                     property_name, source_details, tags, display_name, partner_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    crm_id,
                    lead_id,
                    budget_full,
                    row.get('budget_currency', ''),
                    row.get('lost_reason', ''),
                    row.get('move_in_date', ''),
                    row.get('lease_duration', ''),
                    int(row['lease_duration_days']) if pd.notna(row.get('lease_duration_days')) else None,
                    row.get('state', ''),
                    row.get('created_at', ''),
                    property_name,
                    row.get('location_state', ''),
                    row.get('location_country', ''),
                    row.get('location_locality', ''),
                    row.get('street_number', ''),
                    row.get('lead_name', ''),
                    row.get('lead_email', ''),
                    row.get('lead_phone', ''),
                    row.get('phone_country', ''),
                    row.get('inventory_id', ''),
                    property_name,
                    row.get('source_details', ''),
                    row.get('tags', ''),
                    row.get('display_name', ''),
                    row.get('partner_id', '').replace(',', '').strip() if pd.notna(row.get('partner_id')) else ''
                ))
                inserted += 1
                
                # Also update lead properties if we have property info
                if lead_id and property_name:
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO lead_properties (lead_id, property_name)
                        VALUES (?, ?)
                    """, (lead_id, property_name))
                
            except Exception as e:
                print(f"   ⚠️  Error processing CRM record {idx+1}: {str(e)}")
                continue
        
        self.conn.commit()
        print(f"✅ Inserted {inserted} CRM records")
        print(f"✅ Matched {matched} CRM records to existing leads")
        print(f"✅ Updated status for {updated_status} leads from CRM data")
    
    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    # Run ingestion
    print("🚀 Starting Exported Dataset Ingestion")
    print("="*60)
    
    ingestion = ExportedDataIngestion(db_path="data/leads.db")
    
    # Ingest summaries (main lead data)
    summaries_path = "Data/exported_dataset/summaries.json"
    if os.path.exists(summaries_path):
        ingestion.ingest_summaries(summaries_path)
    else:
        print(f"⚠️  Summaries file not found: {summaries_path}")
    
    # Ingest timeline events
    rag_dataset_path = "Data/exported_dataset/rag_dataset.json"
    if os.path.exists(rag_dataset_path):
        ingestion.ingest_timeline_events(rag_dataset_path)
    else:
        print(f"⚠️  RAG dataset file not found: {rag_dataset_path}")
    
    # Ingest call transcripts
    mcp_folder = "Data/exported_dataset/mcp"
    if os.path.exists(mcp_folder):
        ingestion.ingest_transcripts(mcp_folder)
    else:
        print(f"⚠️  MCP folder not found: {mcp_folder}")
    
    # Ingest CRM data
    crm_csv_path = "Data/exported_dataset/CRM data of those leads.csv"
    if os.path.exists(crm_csv_path):
        ingestion.ingest_crm_data(crm_csv_path)
    else:
        print(f"⚠️  CRM CSV file not found: {crm_csv_path}")
    
    # Print statistics
    ingestion.print_stats()
    ingestion.close()
    
    print("✅ Data ingestion complete!")

