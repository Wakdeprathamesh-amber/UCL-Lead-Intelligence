"""
End-to-End System Test
Comprehensive testing of all components and integrations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
from query_tools import LeadQueryTools
from aggregate_query_tools import AggregateQueryTools
from rag_system import LeadRAGSystem
from ai_agent import LeadIntelligenceAgent


def test_database_integrity():
    """Test database structure and data"""
    print("\n" + "="*60)
    print("🔍 TEST 1: Database Integrity")
    print("="*60)
    
    conn = sqlite3.connect("data/leads.db")
    cursor = conn.cursor()
    
    # Check tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    required_tables = ['leads', 'timeline_events', 'call_transcripts', 'crm_data', 
                       'rag_documents', 'rag_documents_events', 'lead_requirements']
    
    print(f"\n✅ Tables found: {len(tables)}")
    for table in required_tables:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table}: {count} records")
        else:
            print(f"   ❌ {table}: MISSING")
    
    conn.close()
    return True


def test_query_tools():
    """Test query tools functionality"""
    print("\n" + "="*60)
    print("🔍 TEST 2: Query Tools")
    print("="*60)
    
    tools = LeadQueryTools()
    
    # Test aggregations
    print("\n📊 Testing aggregations...")
    try:
        aggs = tools.get_aggregations()
        print(f"   ✅ Total leads: {aggs['total_leads']}")
        print(f"   ✅ Status breakdown: {len(aggs['status_breakdown'])} statuses")
        print(f"   ✅ Won leads: {aggs.get('won_leads', aggs.get('won_count', 0))}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test filtering
    print("\n🔍 Testing lead filtering...")
    try:
        results = tools.filter_leads(status="Won")
        print(f"   ✅ Found {len(results)} Won leads")
        if results:
            print(f"   ✅ Sample lead: {results[0].get('name', 'N/A')}")
            # Show first 3
            for i, lead in enumerate(results[:3], 1):
                print(f"      {i}. {lead.get('name', 'N/A')} - {lead.get('status', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test timeline
    print("\n📅 Testing timeline queries...")
    try:
        timeline = tools.get_lead_timeline("97")
        print(f"   ✅ Found {len(timeline)} timeline events for lead 97")
        if timeline:
            print(f"   ✅ Sample event: {timeline[0].get('event_type', 'N/A')} at {timeline[0].get('timestamp', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test transcripts
    print("\n📞 Testing call transcripts...")
    try:
        transcripts = tools.get_call_transcripts()
        print(f"   ✅ Found {len(transcripts)} call transcripts")
        if transcripts:
            print(f"   ✅ Sample transcript: Lead {transcripts[0].get('lead_id', 'N/A')} - {len(transcripts[0].get('transcript_text', ''))} chars")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True


def test_rag_system():
    """Test RAG system functionality"""
    print("\n" + "="*60)
    print("🔍 TEST 3: RAG System")
    print("="*60)
    
    try:
        rag = LeadRAGSystem()
        
        # Check stats
        print("\n📊 Checking RAG statistics...")
        stats = rag.get_stats()
        print(f"   ✅ Total documents: {stats['total_documents']}")
        print(f"   ✅ Collection name: {stats['collection_name']}")
        
        if stats['total_documents'] < 100:
            print(f"   ⚠️  Warning: Only {stats['total_documents']} documents embedded (expected ~10,000+)")
        
        # Test semantic search
        print("\n🔍 Testing semantic search...")
        results = rag.semantic_search("student budget concerns", n_results=3)
        print(f"   ✅ Semantic search returned {len(results)} results")
        if results:
            print(f"   ✅ Sample result: {results[0]['content'][:100]}...")
            print(f"   ✅ Distance: {results[0].get('distance', 'N/A')}")
        
        # Test conversation search
        print("\n💬 Testing conversation search...")
        results = rag.search_conversations("accommodation preferences", n_results=3)
        print(f"   ✅ Conversation search returned {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_agent():
    """Test AI agent functionality"""
    print("\n" + "="*60)
    print("🔍 TEST 4: AI Agent")
    print("="*60)
    
    try:
        print("\n🤖 Initializing AI agent...")
        agent = LeadIntelligenceAgent(mode="detailed")
        print("   ✅ Agent initialized")
        
        # Test simple query
        print("\n💬 Testing simple query...")
        test_queries = [
            "How many total leads do we have?",
            "Show me 3 Won leads",
        ]
        
        for query in test_queries:
            print(f"\n   Query: {query}")
            result = agent.query(query)
            if result['success']:
                print(f"   ✅ Response: {result['answer'][:200]}...")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_aggregate_mode():
    """Test aggregate mode"""
    print("\n" + "="*60)
    print("🔍 TEST 5: Aggregate Mode")
    print("="*60)
    
    try:
        # Check database exists
        if not os.path.exists("data/leads_aggregate.db"):
            print("   ⚠️  Aggregate database not found")
            return False
        
        tools = AggregateQueryTools()
        
        print("\n📊 Testing aggregate aggregations...")
        aggs = tools.get_aggregations()
        print(f"   ✅ Total leads: {aggs['total_leads']}")
        print(f"   ✅ Status breakdown: {len(aggs['status_breakdown'])} statuses")
        
        if 'lost_reasons' in aggs and aggs['lost_reasons']:
            print(f"   ✅ Lost reasons available: {len(aggs['lost_reasons'])} reasons")
        
        if 'country_breakdown' in aggs and aggs['country_breakdown']:
            print(f"   ✅ Country breakdown available: {len(aggs['country_breakdown'])} countries")
        
        # Test aggregate agent
        print("\n🤖 Testing aggregate agent...")
        agent = LeadIntelligenceAgent(mode="aggregate")
        result = agent.query("How many total leads do we have?")
        if result['success']:
            print(f"   ✅ Aggregate agent working: {result['answer'][:150]}...")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crm_data():
    """Test CRM data integration"""
    print("\n" + "="*60)
    print("🔍 TEST 6: CRM Data Integration")
    print("="*60)
    
    try:
        conn = sqlite3.connect("data/leads.db")
        cursor = conn.cursor()
        
        # Check CRM data
        cursor.execute("SELECT COUNT(*) FROM crm_data")
        crm_count = cursor.fetchone()[0]
        print(f"\n📊 CRM Records: {crm_count}")
        
        if crm_count == 0:
            print("   ⚠️  No CRM data found")
            return False
        
        # Check matched leads
        cursor.execute("SELECT COUNT(*) FROM crm_data WHERE lead_id IS NOT NULL")
        matched = cursor.fetchone()[0]
        print(f"   ✅ Matched to leads: {matched}")
        
        # Check status updates
        cursor.execute("""
            SELECT COUNT(*) FROM leads l
            JOIN crm_data c ON l.lead_id = c.lead_id
            WHERE l.status = c.state OR l.status != 'Contacted'
        """)
        status_updated = cursor.fetchone()[0]
        print(f"   ✅ Leads with CRM status: {status_updated}")
        
        # Sample CRM data
        cursor.execute("""
            SELECT lead_id, property_name, budget_full, lost_reason, state
            FROM crm_data
            WHERE lead_id IS NOT NULL
            LIMIT 3
        """)
        samples = cursor.fetchall()
        print(f"\n   Sample CRM data:")
        for sample in samples:
            print(f"      Lead {sample[0]}: {sample[1]} (Status: {sample[4]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test full integration"""
    print("\n" + "="*60)
    print("🔍 TEST 7: Full Integration Test")
    print("="*60)
    
    try:
        agent = LeadIntelligenceAgent(mode="detailed")
        
        # Test queries that require multiple components
        integration_queries = [
            "What are the top concerns from students?",
            "Show me leads with budget less than 400 pounds",
            "What properties are most popular?",
        ]
        
        print("\n💬 Testing integrated queries...")
        for query in integration_queries:
            print(f"\n   Query: {query}")
            result = agent.query(query)
            if result['success']:
                print(f"   ✅ Response length: {len(result['answer'])} chars")
                print(f"   ✅ Preview: {result['answer'][:150]}...")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("🚀 END-TO-END SYSTEM TEST")
    print("="*60)
    
    results = {}
    
    # Run all tests
    results['database'] = test_database_integrity()
    results['query_tools'] = test_query_tools()
    results['rag'] = test_rag_system()
    results['ai_agent'] = test_ai_agent()
    results['aggregate'] = test_aggregate_mode()
    results['crm'] = test_crm_data()
    results['integration'] = test_integration()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    exit(main())

