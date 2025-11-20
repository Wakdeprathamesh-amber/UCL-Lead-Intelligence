"""
Add Missing Database Indexes
Adds performance-critical indexes that are missing
"""

import sqlite3
import os


def add_missing_indexes(db_path: str = "data/leads.db"):
    """Add missing indexes for performance optimization"""
    
    if not os.path.exists(db_path):
        print(f"⚠️  Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Adding missing database indexes...")
    print("="*60)
    
    indexes_to_add = [
        {
            "name": "idx_leads_status",
            "table": "leads",
            "column": "status",
            "description": "Index on leads.status for fast status filtering"
        },
        {
            "name": "idx_requirements_budget_max",
            "table": "lead_requirements",
            "column": "budget_max",
            "description": "Index on budget_max for fast budget filtering"
        },
        {
            "name": "idx_requirements_location",
            "table": "lead_requirements",
            "column": "location",
            "description": "Index on location for fast location filtering"
        },
        {
            "name": "idx_requirements_move_in_date",
            "table": "lead_requirements",
            "column": "move_in_date",
            "description": "Index on move_in_date for fast date filtering"
        },
        {
            "name": "idx_requirements_university",
            "table": "lead_requirements",
            "column": "university",
            "description": "Index on university for fast university filtering"
        },
        {
            "name": "idx_leads_name",
            "table": "leads",
            "column": "name",
            "description": "Index on name for fast name searches"
        },
        {
            "name": "idx_leads_mobile_number",
            "table": "leads",
            "column": "mobile_number",
            "description": "Index on mobile_number for fast phone lookups"
        },
        {
            "name": "idx_properties_lead_id",
            "table": "lead_properties",
            "column": "lead_id",
            "description": "Index on lead_properties.lead_id for fast property queries"
        },
        {
            "name": "idx_properties_property_name",
            "table": "lead_properties",
            "column": "property_name",
            "description": "Index on property_name for fast property lookups"
        },
        {
            "name": "idx_tasks_lead_id",
            "table": "lead_tasks",
            "column": "lead_id",
            "description": "Index on lead_tasks.lead_id for fast task queries"
        },
        {
            "name": "idx_tasks_status",
            "table": "lead_tasks",
            "column": "status",
            "description": "Index on task status for fast status filtering"
        },
        {
            "name": "idx_rag_documents_lead_id",
            "table": "rag_documents",
            "column": "lead_id",
            "description": "Index on rag_documents.lead_id for fast joins"
        },
        {
            "name": "idx_rag_documents_chunk_type",
            "table": "rag_documents",
            "column": "chunk_type",
            "description": "Index on rag_documents.chunk_type for fast filtering"
        },
        {
            "name": "idx_amenities_amenity",
            "table": "lead_amenities",
            "column": "amenity",
            "description": "Index on amenity for fast amenity queries"
        }
    ]
    
    added = 0
    skipped = 0
    
    for idx in indexes_to_add:
        try:
            # Check if index already exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name=?
            """, (idx["name"],))
            
            if cursor.fetchone():
                print(f"   ⏭️  {idx['name']} already exists")
                skipped += 1
                continue
            
            # Create index
            # Note: SQLite doesn't support parameterized DDL statements
            # Safe: All values come from predefined list in code, not user input
            index_name = idx['name']
            table_name = idx['table']
            column_name = idx['column']
            
            # Additional validation: Only alphanumeric and underscore allowed
            if not all(c.isalnum() or c == '_' for c in index_name + table_name + column_name):
                print(f"   ⚠️  Skipping {index_name}: Invalid characters detected")
                continue
            
            # Safe to use f-string here: values are from predefined list, validated above
            cursor.execute(f"""
                CREATE INDEX {index_name} 
                ON {table_name}({column_name})
            """)
            
            print(f"   ✅ Created {idx['name']} on {idx['table']}.{idx['column']}")
            added += 1
            
        except Exception as e:
            print(f"   ❌ Error creating {idx['name']}: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    print("="*60)
    print(f"✅ Added {added} new indexes")
    print(f"⏭️  Skipped {skipped} existing indexes")
    
    return True


if __name__ == "__main__":
    print("🚀 Adding Missing Database Indexes")
    print("="*60)
    
    # Add indexes to main database
    if add_missing_indexes("data/leads.db"):
        print("\n✅ Index creation complete!")
    else:
        print("\n❌ Index creation failed!")
    
    # Also add to aggregate database if it exists
    if os.path.exists("data/leads_aggregate.db"):
        print("\n🔧 Adding indexes to aggregate database...")
        add_missing_indexes("data/leads_aggregate.db")

