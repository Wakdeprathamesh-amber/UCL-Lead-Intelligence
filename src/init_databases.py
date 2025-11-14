"""
Database Initialization Module
Automatically creates and populates databases on first run
"""

import os
import sys

def ensure_databases_exist():
    """Ensure both databases exist and are populated"""
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Check detailed database
    detailed_db = "data/leads.db"
    if not os.path.exists(detailed_db):
        print("📊 Initializing detailed database...")
        try:
            from data_ingestion import LeadDataIngestion
            
            # Find CSV file (try multiple possible paths)
            csv_files = [
                "Data/UCL Leads Data  - 20 Leads.csv",
                "Data/UCL Leads Data - Sheet1.csv",
                "UCL Leads Data  - 20 Leads.csv",
                "UCL Leads Data - Sheet1.csv"
            ]
            
            csv_path = None
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    csv_path = csv_file
                    break
            
            if csv_path:
                ingestion = LeadDataIngestion(db_path=detailed_db)
                ingestion.parse_csv(csv_path)
                ingestion.close()
                print("✅ Detailed database initialized")
            else:
                print("⚠️  CSV file not found, creating empty database...")
                # Create empty database with schema
                ingestion = LeadDataIngestion(db_path=detailed_db)
                ingestion.close()
        except Exception as e:
            print(f"⚠️  Error initializing detailed database: {str(e)}")
            # Create empty database anyway
            try:
                from data_ingestion import LeadDataIngestion
                ingestion = LeadDataIngestion(db_path=detailed_db)
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

