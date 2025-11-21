"""
Test Script for Simplified Agent
Tests all query types to ensure simplified architecture works
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_agent_simple import SimpleLeadIntelligenceAgent
import time

def test_query(agent, query, expected_keywords=None):
    """Test a single query"""
    print(f"\n📋 Query: {query}")
    start = time.time()
    result = agent.query(query)
    elapsed = (time.time() - start) * 1000
    
    if result['success']:
        print(f"   ✅ Success ({elapsed:.0f}ms)")
        if expected_keywords:
            answer_lower = result['answer'].lower()
            found = [kw for kw in expected_keywords if kw.lower() in answer_lower]
            if found:
                print(f"   ✅ Found keywords: {', '.join(found)}")
            else:
                print(f"   ⚠️  Missing keywords: {', '.join(expected_keywords)}")
        print(f"   Preview: {result['answer'][:150]}...")
        return True
    else:
        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        return False

def main():
    print("="*70)
    print("  SIMPLIFIED AGENT TEST SUITE")
    print("="*70)
    
    # Initialize agent
    print("\n🔧 Initializing simplified agent...")
    agent = SimpleLeadIntelligenceAgent()
    print(f"✅ Agent initialized with {len(agent.tools)} tools")
    print(f"   Tools: {', '.join([t.name for t in agent.tools])}")
    
    # Test queries
    tests = [
        # Simple structured queries
        ("How many total leads?", ["402", "leads", "total"]),
        ("What is the average budget?", ["budget", "average"]),
        ("Show me all Won leads", ["Won", "lead"]),
        
        # Complex structured queries
        ("What are room types by source country?", ["room type", "country"]),
        ("What is the minimum and maximum budget?", ["minimum", "maximum", "budget"]),
        ("How many Won leads have ensuite room type?", ["Won", "ensuite"]),
        
        # Semantic queries
        ("What concerns do leads have?", ["concern", "lead"]),
        ("What are common objections?", ["objection", "common"]),
        
        # Combined queries
        ("What are behavioral differences between Won and Lost leads?", ["Won", "Lost", "behavioral"]),
    ]
    
    print("\n" + "="*70)
    print("  RUNNING TESTS")
    print("="*70)
    
    results = []
    for query, keywords in tests:
        success = test_query(agent, query, keywords)
        results.append((query, success))
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed < total:
        print("\n❌ Failed Tests:")
        for query, success in results:
            if not success:
                print(f"   - {query}")
    
    print("\n" + "="*70)
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    print("="*70)

if __name__ == "__main__":
    main()

