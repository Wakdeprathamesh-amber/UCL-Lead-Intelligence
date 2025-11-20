"""
Comprehensive Query Testing
Tests all queries including analytical ones for accuracy and expected behavior
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_agent import LeadIntelligenceAgent
import time

def test_query(agent, query, expected_keywords=None, min_length=50):
    """Test a single query and check results"""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print('-'*70)
    
    start_time = time.time()
    result = agent.query(query, user_id="test_user", session_id="test_session")
    elapsed = time.time() - start_time
    
    if result['success']:
        answer = result['answer']
        print(f"✅ Success ({elapsed:.2f}s)")
        print(f"Response length: {len(answer)} chars")
        
        # Check minimum length
        if len(answer) < min_length:
            print(f"⚠️  WARNING: Response too short ({len(answer)} < {min_length})")
        
        # Check for expected keywords
        if expected_keywords:
            found = []
            missing = []
            answer_lower = answer.lower()
            for keyword in expected_keywords:
                if keyword.lower() in answer_lower:
                    found.append(keyword)
                else:
                    missing.append(keyword)
            
            if found:
                print(f"✅ Found keywords: {', '.join(found)}")
            if missing:
                print(f"⚠️  Missing keywords: {', '.join(missing)}")
        
        # Show preview
        preview = answer[:200] + "..." if len(answer) > 200 else answer
        print(f"\nPreview:\n{preview}\n")
        
        return True, answer, elapsed
    else:
        print(f"❌ Failed ({elapsed:.2f}s)")
        print(f"Error: {result.get('error', 'Unknown error')}")
        return False, None, elapsed

def main():
    print("🧪 COMPREHENSIVE QUERY TESTING")
    print("="*70)
    print("Testing all queries for accuracy and expected behavior\n")
    
    # Initialize agent
    print("Initializing AI Agent...")
    agent = LeadIntelligenceAgent(mode='detailed')
    print("✅ Agent initialized\n")
    
    results = []
    
    # Standard Test Queries
    print("\n" + "="*70)
    print("STANDARD TEST QUERIES")
    print("="*70)
    
    standard_queries = [
        {
            "query": "How many total leads do we have?",
            "expected_keywords": ["402", "leads", "total"],
            "min_length": 50
        },
        {
            "query": "Show me all Won leads",
            "expected_keywords": ["Won", "lead"],
            "min_length": 100
        },
        {
            "query": "What are the most popular properties?",
            "expected_keywords": ["property", "popular"],
            "min_length": 100
        },
        {
            "query": "What amenities do students want?",
            "expected_keywords": ["amenit"],
            "min_length": 100
        },
        {
            "query": "Show me leads with budget less than 400",
            "expected_keywords": ["budget", "400", "lead"],
            "min_length": 100
        },
        {
            "query": "What tasks are pending?",
            "expected_keywords": ["task", "pending"],
            "min_length": 50
        },
        {
            "query": "What are common objections?",
            "expected_keywords": ["objection", "concern"],
            "min_length": 50
        }
    ]
    
    for test in standard_queries:
        success, answer, elapsed = test_query(
            agent, 
            test["query"],
            test.get("expected_keywords"),
            test.get("min_length", 50)
        )
        results.append({
            "query": test["query"],
            "success": success,
            "elapsed": elapsed,
            "category": "standard"
        })
    
    # Analytical Queries
    print("\n" + "="*70)
    print("ANALYTICAL QUERIES")
    print("="*70)
    
    analytical_queries = [
        {
            "query": "Lost reason grouped by source country",
            "expected_keywords": ["lost", "country", "reason"],
            "min_length": 100,
            "description": "Should show lost reasons broken down by country"
        },
        {
            "query": "Top room types chosen grouped by source country",
            "expected_keywords": ["room", "country", "type"],
            "min_length": 100,
            "description": "Should show room type preferences by country"
        },
        {
            "query": "How many percent enquiries are leading to lost and top reasons",
            "expected_keywords": ["percent", "%", "lost", "reason"],
            "min_length": 100,
            "description": "Should show conversion rate and top lost reasons"
        },
        {
            "query": "How many percent bookings get cancelled and possible reasons",
            "expected_keywords": ["percent", "%", "cancel", "reason"],
            "min_length": 100,
            "description": "Should show cancellation rate and reasons"
        }
    ]
    
    for test in analytical_queries:
        print(f"\n📊 Testing: {test.get('description', 'Analytical query')}")
        success, answer, elapsed = test_query(
            agent,
            test["query"],
            test.get("expected_keywords"),
            test.get("min_length", 100)
        )
        results.append({
            "query": test["query"],
            "success": success,
            "elapsed": elapsed,
            "category": "analytical"
        })
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    standard_success = sum(1 for r in results if r["category"] == "standard" and r["success"])
    analytical_success = sum(1 for r in results if r["category"] == "analytical" and r["success"])
    
    avg_time = sum(r["elapsed"] for r in results) / total if total > 0 else 0
    
    print(f"\n📊 Overall Results:")
    print(f"   Total queries: {total}")
    print(f"   ✅ Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"   ❌ Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"   ⏱️  Average time: {avg_time:.2f}s")
    
    print(f"\n📋 By Category:")
    print(f"   Standard queries: {standard_success}/{len([r for r in results if r['category'] == 'standard'])} successful")
    print(f"   Analytical queries: {analytical_success}/{len([r for r in results if r['category'] == 'analytical'])} successful")
    
    print(f"\n📝 Failed Queries:")
    for r in results:
        if not r["success"]:
            print(f"   ❌ {r['query']}")
    
    print("\n" + "="*70)
    
    if successful == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {failed} test(s) failed. Review above for details.")
    
    print("="*70)

if __name__ == "__main__":
    main()

