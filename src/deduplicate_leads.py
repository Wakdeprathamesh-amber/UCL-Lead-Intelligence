"""
Deduplication Script
Removes duplicate leads from original CSV data that are also in exported dataset
"""

import sqlite3
import json
import os


def find_duplicates():
    """Find duplicate leads by mobile number"""
    conn = sqlite3.connect("data/leads.db")
    cursor = conn.cursor()
    
    # Get original leads (with # prefix)
    cursor.execute("""
        SELECT lead_id, name, mobile_number 
        FROM leads 
        WHERE lead_id LIKE '#%'
    """)
    original_leads = {row[2]: (row[0], row[1]) for row in cursor.fetchall() if row[2]}
    
    # Get exported leads
    with open('Data/exported_dataset/summaries.json', 'r') as f:
        exported = json.load(f)
    
    exported_mobiles = {}
    for item in exported:
        mobile = item.get('mobile_number', '')
        if mobile:
            exported_mobiles[mobile] = (
                str(item.get('lead_id', '')),
                item.get('requirements', {}).get('user_persona', {}).get('name', 'Unknown')
            )
    
    # Find matches
    duplicates = []
    for mobile, (orig_id, orig_name) in original_leads.items():
        if mobile in exported_mobiles:
            exp_id, exp_name = exported_mobiles[mobile]
            duplicates.append({
                'mobile': mobile,
                'original_id': orig_id,
                'original_name': orig_name,
                'exported_id': exp_id,
                'exported_name': exp_name
            })
    
    conn.close()
    return duplicates


def remove_duplicate_leads(duplicates, dry_run=True):
    """Remove duplicate leads from database"""
    conn = sqlite3.connect("data/leads.db")
    cursor = conn.cursor()
    
    print(f"\n{'🔍 DRY RUN - ' if dry_run else '🗑️  REMOVING '}Duplicate Leads")
    print("="*60)
    
    total_deleted = 0
    
    for dup in duplicates:
        orig_id = dup['original_id']
        
        # Count related records
        cursor.execute("SELECT COUNT(*) FROM timeline_events WHERE lead_id = ?", (orig_id,))
        timeline_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM call_transcripts WHERE lead_id = ?", (orig_id,))
        transcript_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rag_documents WHERE lead_id = ?", (orig_id,))
        rag_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rag_documents_events WHERE lead_id = ?", (orig_id,))
        rag_events_count = cursor.fetchone()[0]
        
        print(f"\n📋 {dup['original_name']} ({orig_id})")
        print(f"   Mobile: {dup['mobile']}")
        print(f"   Duplicate of: {dup['exported_name']} ({dup['exported_id']})")
        print(f"   Related records: {timeline_count} events, {transcript_count} transcripts, "
              f"{rag_count} RAG docs, {rag_events_count} RAG events")
        
        if not dry_run:
            # Delete in order (respecting foreign keys)
            cursor.execute("DELETE FROM rag_documents_events WHERE lead_id = ?", (orig_id,))
            cursor.execute("DELETE FROM rag_documents WHERE lead_id = ?", (orig_id,))
            cursor.execute("DELETE FROM timeline_events WHERE lead_id = ?", (orig_id,))
            cursor.execute("DELETE FROM call_transcripts WHERE lead_id = ?", (orig_id,))
            cursor.execute("DELETE FROM lead_tasks WHERE lead_id = ?", (orig_id,))
            cursor.execute("DELETE FROM lead_objections WHERE lead_id = ?", (orig_id,))
            cursor.execute("DELETE FROM lead_amenities WHERE lead_id = ?", (orig_id,))
            cursor.execute("DELETE FROM lead_properties WHERE lead_id = ?", (orig_id,))
            cursor.execute("DELETE FROM lead_requirements WHERE lead_id = ?", (orig_id,))
            cursor.execute("DELETE FROM leads WHERE lead_id = ?", (orig_id,))
            
            total_deleted += 1
            print(f"   ✅ Deleted")
    
    if not dry_run:
        conn.commit()
        print(f"\n✅ Removed {total_deleted} duplicate leads")
    else:
        print(f"\n🔍 DRY RUN: Would remove {len(duplicates)} duplicate leads")
        print("   Run with dry_run=False to actually delete")
    
    conn.close()
    return total_deleted if not dry_run else len(duplicates)


def verify_deduplication():
    """Verify deduplication results"""
    conn = sqlite3.connect("data/leads.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM leads")
    total_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE lead_id LIKE '#%'")
    old_format_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM timeline_events")
    total_events = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM call_transcripts")
    total_transcripts = cursor.fetchone()[0]
    
    print("\n" + "="*60)
    print("📊 VERIFICATION RESULTS")
    print("="*60)
    print(f"Total Leads: {total_leads}")
    print(f"Old Format Leads (with #): {old_format_leads}")
    print(f"Timeline Events: {total_events}")
    print(f"Call Transcripts: {total_transcripts}")
    print("="*60)
    
    conn.close()


if __name__ == "__main__":
    print("🔍 Finding Duplicate Leads")
    print("="*60)
    
    duplicates = find_duplicates()
    
    print(f"\n✅ Found {len(duplicates)} duplicate leads")
    print("\nDuplicate Details:")
    for i, dup in enumerate(duplicates, 1):
        print(f"{i}. {dup['original_name']} ({dup['original_id']}) = {dup['exported_name']} ({dup['exported_id']})")
    
    # Dry run first
    print("\n" + "="*60)
    remove_duplicate_leads(duplicates, dry_run=True)
    
    # Ask for confirmation
    print("\n" + "="*60)
    response = input("Do you want to proceed with deletion? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\n🗑️  Removing duplicates...")
        removed = remove_duplicate_leads(duplicates, dry_run=False)
        verify_deduplication()
        print(f"\n✅ Deduplication complete! Removed {removed} duplicate leads")
    else:
        print("\n❌ Deduplication cancelled")

