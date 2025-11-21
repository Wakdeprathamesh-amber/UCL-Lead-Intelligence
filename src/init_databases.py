"""
Database Initialization Module
Automatically creates and populates databases on first run
"""

import os
import sys
import sqlite3

def ensure_databases_exist():
    """Ensure both databases exist and are populated"""
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Check detailed database (handle both data/ and Data/ for case-sensitive systems)
    # Priority: Check uppercase Data/ first (where pre-built DB is), then lowercase data/
    detailed_db = None
    possible_db_paths = ["Data/leads.db", "data/leads.db"]
    
    for db_path in possible_db_paths:
        if os.path.exists(db_path):
            detailed_db = db_path
            print(f"✅ Found database at: {db_path}")
            break
    
    needs_ingestion = False
    
    if not detailed_db:
        print("📊 Database not found at Data/leads.db or data/leads.db, will initialize...")
        detailed_db = "data/leads.db"  # Will create in lowercase
        needs_ingestion = True
    else:
        # Check if database has sufficient data (≥400 leads)
        try:
            conn = sqlite3.connect(detailed_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM leads")
            lead_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"📊 Database at {detailed_db} has {lead_count} leads")
            
            if lead_count < 400:
                print(f"⚠️  Database has only {lead_count} leads (<400), will re-initialize...")
                needs_ingestion = True
            else:
                print(f"✅ Database already has {lead_count} leads (≥400), using existing database")
        except Exception as e:
            print(f"⚠️  Error checking database at {detailed_db}: {str(e)}")
            print("   Will re-initialize...")
            needs_ingestion = True
    
    if needs_ingestion:
        print("📊 Initializing detailed database with exported dataset...")
        try:
            # If database exists but has old/empty data, delete it first
            if os.path.exists(detailed_db):
                print("🗑️  Removing old/empty database to re-initialize...")
                try:
                    os.remove(detailed_db)
                    print("✅ Old database removed")
                except Exception as e:
                    print(f"⚠️  Could not remove old database: {str(e)}")
            
            from exported_data_ingestion import ExportedDataIngestion
            
            # Check for exported dataset files (try both Data/ and data/)
            summaries_path = None
            rag_dataset_path = None
            mcp_folder = None
            crm_csv_path = None
            
            # Try multiple paths (case-sensitive systems)
            possible_paths = [
                ("Data/exported_dataset/summaries.json", "Data/exported_dataset/rag_dataset.json", 
                 "Data/exported_dataset/mcp", "Data/exported_dataset/CRM data of those leads.csv"),
                ("data/exported_dataset/summaries.json", "data/exported_dataset/rag_dataset.json",
                 "data/exported_dataset/mcp", "data/exported_dataset/CRM data of those leads.csv"),
                ("exported_dataset/summaries.json", "exported_dataset/rag_dataset.json",
                 "exported_dataset/mcp", "exported_dataset/CRM data of those leads.csv"),
            ]
            
            for s_path, r_path, m_path, c_path in possible_paths:
                if os.path.exists(s_path):
                    summaries_path = s_path
                    rag_dataset_path = r_path
                    mcp_folder = m_path
                    crm_csv_path = c_path
                    print(f"✅ Found exported dataset at: {s_path}")
                    break
            
            if summaries_path and os.path.exists(summaries_path):
                ingestion = ExportedDataIngestion(db_path=detailed_db)
                
                # Ingest summaries (main lead data)
                print("📥 Ingesting summaries...")
                try:
                    ingestion.ingest_summaries(summaries_path)
                    print("✅ Summaries ingested successfully")
                except Exception as e:
                    print(f"❌ Error ingesting summaries: {str(e)}")
                    raise
                
                # Ingest timeline events
                if os.path.exists(rag_dataset_path):
                    print("📥 Ingesting timeline events...")
                    try:
                        ingestion.ingest_timeline_events(rag_dataset_path)
                        print("✅ Timeline events ingested successfully")
                    except Exception as e:
                        print(f"⚠️  Error ingesting timeline events: {str(e)}")
                else:
                    print(f"⚠️  RAG dataset not found: {rag_dataset_path}")
                
                # Ingest call transcripts
                if os.path.exists(mcp_folder):
                    print("📥 Ingesting call transcripts...")
                    try:
                        ingestion.ingest_transcripts(mcp_folder)
                        print("✅ Call transcripts ingested successfully")
                    except Exception as e:
                        print(f"⚠️  Error ingesting transcripts: {str(e)}")
                else:
                    print(f"⚠️  MCP folder not found: {mcp_folder}")
                
                # Ingest CRM data
                if os.path.exists(crm_csv_path):
                    print("📥 Ingesting CRM data...")
                    try:
                        ingestion.ingest_crm_data(crm_csv_path)
                        print("✅ CRM data ingested successfully")
                    except Exception as e:
                        print(f"⚠️  Error ingesting CRM data: {str(e)}")
                else:
                    print(f"⚠️  CRM CSV not found: {crm_csv_path}")
                
                ingestion.close()
                
                # Verify ingestion was successful
                conn = sqlite3.connect(detailed_db)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM leads")
                final_count = cursor.fetchone()[0]
                conn.close()
                
                if final_count >= 400:
                    print(f"✅ Detailed database initialized successfully with {final_count} leads")
                else:
                    print(f"⚠️  Warning: Database initialized but only has {final_count} leads (expected ≥400)")
            else:
                print("⚠️  Exported dataset files not found at any expected path")
                print("   Tried: Data/exported_dataset/, data/exported_dataset/, exported_dataset/")
                print("   Creating empty database with schema...")
                # Create empty database with schema
                ingestion = ExportedDataIngestion(db_path=detailed_db)
                ingestion.close()
                print("⚠️  Empty database created - no data available")
        except Exception as e:
            print(f"❌ Error initializing detailed database: {str(e)}")
            import traceback
            traceback.print_exc()
            # Create empty database anyway
            try:
                from exported_data_ingestion import ExportedDataIngestion
                ingestion = ExportedDataIngestion(db_path=detailed_db)
                ingestion.close()
                print("⚠️  Created empty database due to initialization error")
            except Exception as e2:
                print(f"❌ Could not even create empty database: {str(e2)}")
    
    # Check aggregate database
    aggregate_db = "data/leads_aggregate.db"
    if not os.path.exists(aggregate_db):
        print("📊 Initializing aggregate database...")
        try:
            from aggregate_data_ingestion import AggregateDataIngestion
            
            # Try multiple possible paths
            csv_files = [
                "Data/UCL overall leads data.csv",
                "UCL overall leads data.csv"
            ]
            
            csv_path = None
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    csv_path = csv_file
                    break
            
            if csv_path:
                ingestion = AggregateDataIngestion(db_path=aggregate_db)
                ingestion.parse_csv(csv_path)
                ingestion.close()
                print("✅ Aggregate database initialized")
            else:
                print("⚠️  Aggregate CSV file not found, creating empty database...")
                # Create empty database with schema
                ingestion = AggregateDataIngestion(db_path=aggregate_db)
                ingestion.close()
        except Exception as e:
            print(f"⚠️  Error initializing aggregate database: {str(e)}")
            # Create empty database anyway
            try:
                from aggregate_data_ingestion import AggregateDataIngestion
                ingestion = AggregateDataIngestion(db_path=aggregate_db)
                ingestion.close()
            except:
                pass
    
    print("✅ All databases ready!")

if __name__ == "__main__":
    ensure_databases_exist()

