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
    
    # Check detailed database
    detailed_db = "data/leads.db"
    needs_ingestion = False
    
    if not os.path.exists(detailed_db):
        print("📊 Database not found, will initialize...")
        needs_ingestion = True
    else:
        # Check if database has old data (less than 400 leads)
        try:
            conn = sqlite3.connect(detailed_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM leads")
            lead_count = cursor.fetchone()[0]
            conn.close()
            
            if lead_count < 400:
                print(f"📊 Database has only {lead_count} leads, will re-initialize with full dataset...")
                needs_ingestion = True
            else:
                print(f"✅ Database already has {lead_count} leads")
        except Exception as e:
            print(f"⚠️  Error checking database: {str(e)}, will re-initialize...")
            needs_ingestion = True
    
    if needs_ingestion:
        print("📊 Initializing detailed database with exported dataset...")
        try:
            from exported_data_ingestion import ExportedDataIngestion
            
            # Check for exported dataset files
            summaries_path = "Data/exported_dataset/summaries.json"
            rag_dataset_path = "Data/exported_dataset/rag_dataset.json"
            mcp_folder = "Data/exported_dataset/mcp"
            crm_csv_path = "Data/exported_dataset/CRM data of those leads.csv"
            
            if not os.path.exists(summaries_path):
                print(f"⚠️  Exported dataset not found at {summaries_path}")
                print("   Trying alternative paths...")
                # Try alternative paths
                alt_paths = [
                    "exported_dataset/summaries.json",
                    "Data/exported_dataset/summaries.json",
                    "../Data/exported_dataset/summaries.json"
                ]
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        summaries_path = alt_path
                        rag_dataset_path = alt_path.replace("summaries.json", "rag_dataset.json")
                        mcp_folder = alt_path.replace("summaries.json", "mcp")
                        crm_csv_path = alt_path.replace("summaries.json", "CRM data of those leads.csv")
                        break
            
            if os.path.exists(summaries_path):
                ingestion = ExportedDataIngestion(db_path=detailed_db)
                
                # Ingest summaries (main lead data)
                ingestion.ingest_summaries(summaries_path)
                
                # Ingest timeline events
                if os.path.exists(rag_dataset_path):
                    ingestion.ingest_timeline_events(rag_dataset_path)
                
                # Ingest call transcripts
                if os.path.exists(mcp_folder):
                    ingestion.ingest_transcripts(mcp_folder)
                
                # Ingest CRM data
                if os.path.exists(crm_csv_path):
                    ingestion.ingest_crm_data(crm_csv_path)
                
                ingestion.close()
                print("✅ Detailed database initialized with exported dataset")
            else:
                print("⚠️  Exported dataset files not found, creating empty database...")
                # Create empty database with schema
                from exported_data_ingestion import ExportedDataIngestion
                ingestion = ExportedDataIngestion(db_path=detailed_db)
                ingestion.close()
        except Exception as e:
            print(f"⚠️  Error initializing detailed database: {str(e)}")
            import traceback
            traceback.print_exc()
            # Create empty database anyway
            try:
                from exported_data_ingestion import ExportedDataIngestion
                ingestion = ExportedDataIngestion(db_path=detailed_db)
                ingestion.close()
            except:
                pass
    
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

