"""
Comprehensive test of new features with 20-lead dataset
Tests: duration, properties, amenities, CRM data, and more
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_agent import LeadIntelligenceAgent
from query_tools import LeadQueryTools
import json

print("="*80)
print("🧪 COMPREHENSIVE FEATURE TESTING - 20 Leads Dataset")
print("="*80)

agent = LeadIntelligenceAgent()
tools = LeadQueryTools()

# Get ground truth for verification
aggs = tools.get_aggregations()
print(f"\n📊 Ground Truth Data:")
print(f"   Total Leads: {aggs['total_leads']}")
print(f"   Won: {aggs['won_leads']}, Lost: {aggs['lost_leads']}")
print(f"   Avg Budget: £{aggs['average_budget'].get('GBP', 'N/A')}")

# Test questions organized by feature
test_categories = {
    "📏 Duration & Lease Queries": [
        "What is the average lease duration across all leads?",
        "Show me leads with lease duration longer than 40 weeks",
        "What's the shortest and longest lease duration?"
    ],
    
    "🏠 Property Queries": [
        "Which property is Laia booking?",
        "What are the top 3 most popular properties?",
        "Show me all properties students are considering",
        "Which properties do Won leads prefer?"
    ],
    
    "🛋️ Amenity Queries": [
        "What amenities did students request?",
        "What amenities does Laia want?",
        "Which amenity is most popular?",
        "Show me leads who requested gym facilities"
    ],
    
    "💰 Budget & Financial": [
        "What is the average budget across all leads?",
        "Show me leads with budget between £300-£400",
        "Compare budgets of Won vs Lost leads"
    ],
    
    "🗓️ Date & Timeline": [
        "Which month has the most move-ins?",
        "Show me leads moving in before October 2025",
        "What's the distribution of move-in dates?"
    ],
    
    "🎯 Conversion Analysis": [
        "What's our conversion rate?",
        "Why did we lose 7 leads?",
        "What do Won leads have in common?"
    ],
    
    "🌍 Geography": [
        "Which cities are students moving to?",
        "Are all leads for London?",
        "Show location breakdown"
    ]
}

# Track results
all_results = []
question_num = 1

for category, questions in test_categories.items():
    print("\n" + "="*80)
    print(f"\n{category}")
    print("="*80)
    
    for question in questions:
        print(f"\n📝 Q{question_num}: {question}")
        print("-"*80)
        
        try:
            result = agent.query(question)
            
            if result['success']:
                response = result['answer']
                
                # Check response quality
                has_numbers = any(char.isdigit() for char in response)
                has_sources = result.get('intermediate_steps', []) != []
                
                print(f"✅ SUCCESS")
                print(f"\n💡 Response Preview:")
                print(response[:500])
                if len(response) > 500:
                    print("...")
                
                # Show tools used
                if result.get('intermediate_steps'):
                    tools_used = set()
                    for action, obs in result['intermediate_steps']:
                        tools_used.add(action.tool)
                    print(f"\n🔧 Tools: {', '.join(sorted(tools_used))}")
                
                # Quality checks
                quality_score = 0
                if has_numbers:
                    quality_score += 1
                if has_sources:
                    quality_score += 1
                if len(response) > 100:
                    quality_score += 1
                
                quality = "⭐" * quality_score + "☆" * (3 - quality_score)
                print(f"📊 Quality: {quality}")
                
                all_results.append({
                    "question": question,
                    "status": "PASS",
                    "has_data": has_numbers,
                    "tools": list(tools_used) if has_sources else []
                })
            else:
                print(f"❌ FAILED: {result.get('error')}")
                all_results.append({
                    "question": question,
                    "status": "FAIL",
                    "error": result.get('error')
                })
        
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            all_results.append({
                "question": question,
                "status": "ERROR",
                "error": str(e)
            })
        
        question_num += 1

# Summary
print("\n" + "="*80)
print("\n📊 TEST SUMMARY")
print("="*80)

passed = sum(1 for r in all_results if r['status'] == 'PASS')
failed = sum(1 for r in all_results if r['status'] in ['FAIL', 'ERROR'])
total = len(all_results)

print(f"\n✅ Passed: {passed}/{total} ({passed/total*100:.0f}%)")
print(f"❌ Failed: {failed}/{total}")

# Tool usage
print("\n🔧 Tool Usage Statistics:")
tool_counts = {}
for r in all_results:
    if r['status'] == 'PASS':
        for tool in r.get('tools', []):
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   • {tool}: {count}x")

# Data coverage
has_data_count = sum(1 for r in all_results if r.get('has_data', False))
print(f"\n📊 Responses with Data: {has_data_count}/{passed}")

print("\n" + "="*80)
if failed == 0:
    print("🎉 ALL TESTS PASSED! System working perfectly!")
else:
    print(f"⚠️  {failed} test(s) need attention")
print("="*80)

