#!/usr/bin/env python3
"""
Test StructuredTool Fix
Verify that the aggregate_conversations tool now works with complex parameters
"""

import time
from src.ai_agent_simple import SimpleLeadIntelligenceAgent

def test_query(agent, query, description):
    """Test a single query"""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"Expected: {description}")
    print(f"{'='*80}")
    
    start = time.time()
    result = agent.query(query)
    elapsed = time.time() - start
    
    success = result['success']
    answer = result.get('answer', '')
    error = result.get('error', '')
    
    if success:
        print(f"\n✅ SUCCESS ({elapsed:.2f}s)")
        print(f"\nAnswer Preview:\n{answer[:500]}...")
        return True
    else:
        print(f"\n❌ FAILED ({elapsed:.2f}s)")
        print(f"Error: {error}")
        return False


def main():
    print("="*80)
    print("🔧 TESTING STRUCTUREDTOOL FIX")
    print("="*80)
    print("\nThese queries previously failed with 'Too many arguments' error")
    print("Testing if StructuredTool migration fixed them...")
    print("="*80)
    
    agent = SimpleLeadIntelligenceAgent(db_path="data/leads.db")
    
    # Queries that previously failed due to StructuredTool issue
    failing_queries = [
        ("Most mentioned topics in WhatsApp", "Should use aggregate_conversations with query_type='whatsapp'"),
        ("What factors contribute to lead loss?", "Should use aggregate_conversations for concerns"),
        ("How do Won leads communicate differently than Lost leads?", "Should analyze by status"),
        ("How many students asked about WiFi?", "Should use aggregate_conversations with keywords=['wifi']"),
        ("Percentage of leads asking about parking", "Should use aggregate_conversations with keywords=['parking']"),
        ("How many leads mentioned gym facilities?", "Should use aggregate_conversations with keywords=['gym']"),
        ("When do most students plan to move in?", "Should analyze move-in queries"),
        ("What's the typical inquiry to booking timeline?", "Should analyze booking timeline"),
    ]
    
    results = []
    for query, description in failing_queries:
        success = test_query(agent, query, description)
        results.append({'query': query, 'success': success})
        time.sleep(1)  # Brief pause between queries
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 STRUCTUREDTOOL FIX RESULTS")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"❌ Failed: {total-passed}/{total}")
    
    if passed == total:
        print(f"\n🎉 PERFECT! All previously failing queries now work!")
        print(f"   StructuredTool fix is COMPLETE.")
    elif passed >= total * 0.75:
        print(f"\n✅ GOOD! Most queries now work ({passed/total*100:.1f}%)")
        print(f"   StructuredTool fix is MOSTLY successful.")
    else:
        print(f"\n⚠️  PARTIAL: Only {passed/total*100:.1f}% working")
        print(f"   May need additional debugging.")
    
    # List any remaining failures
    failures = [r for r in results if not r['success']]
    if failures:
        print(f"\n\nRemaining Failures:")
        for f in failures:
            print(f"   - {f['query']}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()

