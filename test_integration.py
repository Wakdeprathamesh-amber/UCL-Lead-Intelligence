"""
Integration Test Script
Tests all functionality with the new exported dataset
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from query_tools import LeadQueryTools
from rag_system import LeadRAGSystem
from ai_agent import LeadIntelligenceAgent
import json


def test_data_ingestion():
    """Test 1: Verify data was ingested correctly"""
    print("\n" + "="*60)
    print("TEST 1: Data Ingestion Verification")
    print("="*60)
    
    tools = LeadQueryTools()
    aggs = tools.get_aggregations()
    
    print(f"✅ Total Leads: {aggs['total_leads']}")
    print(f"✅ Status Breakdown: {aggs['status_breakdown']}")
    
    # Check timeline events
    import sqlite3
    conn = sqlite3.connect("data/leads.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM timeline_events")
    event_count = cursor.fetchone()[0]
    print(f"✅ Timeline Events: {event_count}")
    
    cursor.execute("SELECT COUNT(*) FROM call_transcripts")
    transcript_count = cursor.fetchone()[0]
    print(f"✅ Call Transcripts: {transcript_count}")
    
    conn.close()
    
    return event_count > 0 and transcript_count > 0


def test_basic_queries():
    """Test 2: Basic query functionality"""
    print("\n" + "="*60)
    print("TEST 2: Basic Query Functionality")
    print("="*60)
    
    tools = LeadQueryTools()
    
    # Test aggregations
    aggs = tools.get_aggregations()
    assert aggs['total_leads'] > 0, "Should have leads"
    print("✅ Aggregations working")
    
    # Test filter
    results = tools.filter_leads(status="Won")
    assert len(results) > 0, "Should have Won leads"
    print(f"✅ Filter by status: Found {len(results)} Won leads")
    
    # Test get by ID
    if results:
        lead = tools.get_lead_by_id(results[0]['lead_id'])
        assert lead is not None, "Should find lead by ID"
        print(f"✅ Get lead by ID: {lead.get('name', 'Unknown')}")
    
    return True


def test_timeline_queries():
    """Test 3: Timeline event queries"""
    print("\n" + "="*60)
    print("TEST 3: Timeline Event Queries")
    print("="*60)
    
    tools = LeadQueryTools()
    
    # Get a lead ID
    aggs = tools.get_aggregations()
    if aggs['total_leads'] == 0:
        print("⚠️  No leads to test")
        return False
    
    # Get first lead
    all_leads = tools.filter_leads()
    if not all_leads:
        print("⚠️  No leads found")
        return False
    
    lead_id = all_leads[0]['lead_id']
    
    # Test get timeline
    timeline = tools.get_lead_timeline(lead_id)
    print(f"✅ Get timeline for lead {lead_id}: {len(timeline)} events")
    
    # Test filter by event type
    whatsapp_events = tools.get_lead_timeline(lead_id, event_type="whatsapp")
    print(f"✅ WhatsApp events: {len(whatsapp_events)}")
    
    # Test search timeline
    search_results = tools.search_timeline_events("Hello", limit=5)
    print(f"✅ Search timeline events: Found {len(search_results)} matches")
    
    return True


def test_transcript_queries():
    """Test 4: Call transcript queries"""
    print("\n" + "="*60)
    print("TEST 4: Call Transcript Queries")
    print("="*60)
    
    tools = LeadQueryTools()
    
    # Get all transcripts
    transcripts = tools.get_call_transcripts()
    print(f"✅ Total transcripts: {len(transcripts)}")
    
    if transcripts:
        # Get transcripts for specific lead
        lead_id = transcripts[0]['lead_id']
        lead_transcripts = tools.get_call_transcripts(lead_id=lead_id)
        print(f"✅ Transcripts for lead {lead_id}: {len(lead_transcripts)}")
        
        # Show sample transcript
        if lead_transcripts:
            sample = lead_transcripts[0]
            print(f"   Sample: {sample['transcript_text'][:100]}...")
    
    return True


def test_rag_system():
    """Test 5: RAG system with new data"""
    print("\n" + "="*60)
    print("TEST 5: RAG System")
    print("="*60)
    
    try:
        rag = LeadRAGSystem()
        stats = rag.get_stats()
        print(f"✅ RAG documents: {stats['total_documents']}")
        
        # Test search
        results = rag.semantic_search("students concerned about budget", n_results=3)
        print(f"✅ Semantic search: Found {len(results)} results")
        
        if results:
            print(f"   Top result: {results[0]['metadata'].get('lead_name', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"⚠️  RAG system test failed: {str(e)}")
        return False


def test_ai_agent():
    """Test 6: AI Agent with new tools"""
    print("\n" + "="*60)
    print("TEST 6: AI Agent Integration")
    print("="*60)
    
    try:
        agent = LeadIntelligenceAgent(mode="detailed")
        
        # Test basic query
        result = agent.query("How many total leads do we have?")
        print(f"✅ Agent query successful: {result['success']}")
        if result['success']:
            print(f"   Answer: {result['answer'][:100]}...")
        
        # Test timeline query
        result = agent.query("Show me timeline events for a lead")
        print(f"✅ Timeline query: {result['success']}")
        
        return True
    except Exception as e:
        print(f"⚠️  AI Agent test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("🧪 INTEGRATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Data Ingestion", test_data_ingestion),
        ("Basic Queries", test_basic_queries),
        ("Timeline Queries", test_timeline_queries),
        ("Transcript Queries", test_transcript_queries),
        ("RAG System", test_rag_system),
        ("AI Agent", test_ai_agent),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n✅ Passed: {passed}/{total}")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

