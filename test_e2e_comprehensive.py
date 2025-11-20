"""
Comprehensive End-to-End Test
Tests all query types including edge cases where previous architecture might fail
"""

import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_agent import LeadIntelligenceAgent
from langchain.schema import HumanMessage, AIMessage

# Test results
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test(test_name, query):
    """Print test info"""
    print(f"\n📋 Test: {test_name}")
    print(f"   Query: {query}")

def check_result(result, test_name, query, expected_features=None):
    """Check test result and validate features"""
    global test_results
    
    if result.get('success'):
        # Check for expected features
        issues = []
        
        if expected_features:
            if 'reasoning_steps' in expected_features and not result.get('reasoning_steps'):
                issues.append("Missing reasoning steps")
            if 'tools_used' in expected_features and not result.get('tools_used'):
                issues.append("Missing tools_used")
            if 'validation' in expected_features:
                reasoning_steps = result.get('reasoning_steps', [])
                if reasoning_steps:
                    invalid_steps = [s for s in reasoning_steps if not s.get('validation', {}).get('valid', True)]
                    if invalid_steps:
                        issues.append(f"Found {len(invalid_steps)} invalid reasoning steps")
        
        if issues:
            test_results["warnings"].append({
                "test": test_name,
                "query": query,
                "issues": issues,
                "result": result
            })
            print(f"   ⚠️  PASSED with warnings: {', '.join(issues)}")
        else:
            test_results["passed"].append({
                "test": test_name,
                "query": query,
                "result": result
            })
            print(f"   ✅ PASSED")
        
        # Show summary
        if result.get('tools_used'):
            print(f"   🔧 Tools used: {', '.join(result['tools_used'])}")
        if result.get('reasoning_steps'):
            print(f"   🧠 Reasoning steps: {len(result['reasoning_steps'])}")
        if result.get('execution_time_ms'):
            print(f"   ⏱️  Execution time: {result['execution_time_ms']:.0f}ms")
        
        return True
    else:
        test_results["failed"].append({
            "test": test_name,
            "query": query,
            "error": result.get('error', 'Unknown error'),
            "result": result
        })
        print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
        return False

def test_simple_queries(agent):
    """Test simple queries that should work"""
    print_header("SIMPLE QUERIES (Should work)")
    
    queries = [
        ("Total leads count", "How many total leads do we have?"),
        ("Won leads", "Show me all Won leads"),
        ("Average budget", "What's the average budget?"),
        ("Status breakdown", "What's the status breakdown?"),
    ]
    
    for name, query in queries:
        print_test(name, query)
        result = agent.query(question=query)
        check_result(result, name, query, expected_features=['tools_used', 'reasoning_steps'])

def test_complex_queries(agent):
    """Test complex queries that might have failed before"""
    print_header("COMPLEX QUERIES (Previously might fail)")
    
    queries = [
        ("Booked room types by country", "What are the most booked room types categorized by source country?"),
        ("Lost reasons by country", "Show me lost reasons grouped by source country"),
        ("High-budget concerns", "What concerns do high-budget leads have?"),
        ("Property comparison", "Compare the top 3 properties by conversion rate"),
    ]
    
    for name, query in queries:
        print_test(name, query)
        result = agent.query(question=query)
        check_result(result, name, query, expected_features=['tools_used', 'reasoning_steps', 'validation'])

def test_session_memory(agent):
    """Test session memory - context from previous questions"""
    print_header("SESSION MEMORY TESTS (New feature)")
    
    # First question
    print_test("First question", "Show me all leads with budget over 400")
    result1 = agent.query(question="Show me all leads with budget over 400")
    check_result(result1, "First question", "Show me all leads with budget over 400")
    
    # Build chat history
    chat_history = []
    if result1.get('success'):
        chat_history.append(HumanMessage(content="Show me all leads with budget over 400"))
        chat_history.append(AIMessage(content=result1.get('answer', '')))
    
    # Second question - should use context
    print_test("Context-dependent question", "What concerns do they have?")
    result2 = agent.query(
        question="What concerns do they have?",
        chat_history=chat_history
    )
    
    # Check if agent understood context
    answer = result2.get('answer', '').lower()
    if 'budget' in answer or '400' in answer or 'high' in answer:
        check_result(result2, "Context-dependent question", "What concerns do they have?", 
                    expected_features=['tools_used', 'reasoning_steps'])
    else:
        test_results["warnings"].append({
            "test": "Context-dependent question",
            "query": "What concerns do they have?",
            "issues": ["Agent may not have used context from previous question"],
            "result": result2
        })
        print(f"   ⚠️  WARNING: Agent may not have used context properly")

def test_chain_of_thought(agent):
    """Test chain-of-thought reasoning"""
    print_header("CHAIN-OF-THOUGHT REASONING (New feature)")
    
    queries = [
        ("Multi-step analysis", "Analyze conversion rates by country and identify the top 3 countries with highest conversion"),
        ("Complex filtering", "Find leads from India with budget between 300 and 500 who are moving in January 2026"),
        ("Comparative analysis", "Compare the average budget of Won leads vs Lost leads"),
    ]
    
    for name, query in queries:
        print_test(name, query)
        result = agent.query(question=query)
        
        # Check for reasoning steps
        if result.get('success') and result.get('reasoning_steps'):
            steps = result['reasoning_steps']
            if len(steps) >= 2:
                check_result(result, name, query, expected_features=['reasoning_steps', 'validation'])
            else:
                test_results["warnings"].append({
                    "test": name,
                    "query": query,
                    "issues": [f"Expected multiple reasoning steps, got {len(steps)}"],
                    "result": result
                })
                print(f"   ⚠️  WARNING: Expected multiple reasoning steps, got {len(steps)}")
        else:
            check_result(result, name, query)

def test_reasoning_validation(agent):
    """Test reasoning validation"""
    print_header("REASONING VALIDATION (New feature)")
    
    queries = [
        ("Query with validation", "Show me all leads with status 'InvalidStatus'"),
        ("Empty result query", "Show me leads from Antarctica"),
        ("Calculation query", "What percentage of leads are Won?"),
    ]
    
    for name, query in queries:
        print_test(name, query)
        result = agent.query(question=query)
        
        if result.get('success') and result.get('reasoning_steps'):
            # Check if validation caught issues
            steps = result['reasoning_steps']
            invalid_steps = [s for s in steps if not s.get('validation', {}).get('valid', True)]
            
            if invalid_steps:
                print(f"   ✅ Validation working: Found {len(invalid_steps)} invalid step(s)")
                for step in invalid_steps:
                    print(f"      - {step.get('tool')}: {step.get('validation', {}).get('message', '')}")
            
            check_result(result, name, query, expected_features=['reasoning_steps', 'validation'])
        else:
            check_result(result, name, query)

def test_edge_cases(agent):
    """Test edge cases that might cause failures"""
    print_header("EDGE CASES (Potential failure points)")
    
    queries = [
        ("Ambiguous query", "What about those?"),  # No context - should ask for clarification
        ("Very long query", "Show me all leads with budget over 300 and status Won and location London and university UCL and move in date January 2026 and room type ensuite"),
        ("Empty query", ""),  # Should be caught by validation
        ("Special characters", "Show me leads with name containing 'O'Brien'"),
        ("Non-existent data", "Show me leads from Mars"),
    ]
    
    for name, query in queries:
        print_test(name, query)
        result = agent.query(question=query)
        
        # For ambiguous query, check if agent asks for help
        if name == "Ambiguous query" and result.get('success'):
            answer = result.get('answer', '').lower()
            if 'clarif' in answer or 'help' in answer or 'more information' in answer:
                print(f"   ✅ Agent correctly asked for clarification")
            else:
                test_results["warnings"].append({
                    "test": name,
                    "query": query,
                    "issues": ["Agent should ask for clarification but didn't"],
                    "result": result
                })
        
        check_result(result, name, query)

def test_tool_combination(agent):
    """Test tool combination capabilities"""
    print_header("TOOL COMBINATION (Critical feature)")
    
    queries = [
        ("Multiple tools needed", "What are the top 3 properties by conversion rate and what concerns do leads have about them?"),
        ("Filter + Search", "Find high-budget leads and search their conversations for pricing concerns"),
        ("Aggregate + Detail", "What's the overall conversion rate and show me details of the most recent Won lead"),
    ]
    
    for name, query in queries:
        print_test(name, query)
        result = agent.query(question=query)
        
        if result.get('success') and result.get('tools_used'):
            tools_count = len(result['tools_used'])
            if tools_count >= 2:
                print(f"   ✅ Successfully combined {tools_count} tools")
                check_result(result, name, query, expected_features=['tools_used', 'reasoning_steps'])
            else:
                test_results["warnings"].append({
                    "test": name,
                    "query": query,
                    "issues": [f"Expected multiple tools, got {tools_count}"],
                    "result": result
                })
                print(f"   ⚠️  WARNING: Expected multiple tools, got {tools_count}")
        else:
            check_result(result, name, query)

def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["warnings"])
    
    print(f"\n📊 Results:")
    print(f"   ✅ Passed: {len(test_results['passed'])}")
    print(f"   ⚠️  Warnings: {len(test_results['warnings'])}")
    print(f"   ❌ Failed: {len(test_results['failed'])}")
    print(f"   📈 Total: {total}")
    
    if test_results["failed"]:
        print(f"\n❌ Failed Tests:")
        for test in test_results["failed"]:
            print(f"   - {test['test']}: {test.get('error', 'Unknown error')}")
    
    if test_results["warnings"]:
        print(f"\n⚠️  Tests with Warnings:")
        for test in test_results["warnings"]:
            print(f"   - {test['test']}: {', '.join(test['issues'])}")
    
    # Calculate success rate
    if total > 0:
        success_rate = (len(test_results["passed"]) / total) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("   ✅ Excellent! System is working well.")
        elif success_rate >= 75:
            print("   ⚠️  Good, but some improvements needed.")
        else:
            print("   ❌ Needs significant improvements.")

def main():
    """Run all tests"""
    print_header("COMPREHENSIVE END-TO-END TEST")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize agent
    print("\n🔧 Initializing agent...")
    try:
        agent = LeadIntelligenceAgent(mode="detailed")
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        return
    
    # Run all test suites
    test_simple_queries(agent)
    test_complex_queries(agent)
    test_session_memory(agent)
    test_chain_of_thought(agent)
    test_reasoning_validation(agent)
    test_edge_cases(agent)
    test_tool_combination(agent)
    
    # Print summary
    print_summary()
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Save results to file
    results_file = "test_e2e_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": test_results
        }, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {results_file}")

if __name__ == "__main__":
    main()

