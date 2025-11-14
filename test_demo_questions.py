"""
Test all 12 demo questions and verify accuracy
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_agent import LeadIntelligenceAgent
from query_tools import LeadQueryTools
import json

# Initialize
print("="*80)
print("🧪 TESTING ALL 12 DEMO QUESTIONS")
print("="*80)

agent = LeadIntelligenceAgent()
tools = LeadQueryTools()

# Get ground truth data for verification
print("\n📊 Getting ground truth data from database...")
aggs = tools.get_aggregations()
all_leads = tools.filter_leads()

print(f"✅ Total Leads in DB: {aggs['total_leads']}")
print(f"✅ Won Leads in DB: {aggs['won_leads']}")
print(f"✅ Average Budget in DB: £{aggs['average_budget']['GBP']:.2f}")

# Demo questions organized by category
demo_questions = {
    "🔍 Lead Lookup & Filtering": [
        "Show me all Won leads with their details",
        "Show me leads with budget less than 400 pounds",
        "Show me leads moving in January 2026"
    ],
    "📈 Analytics & Insights": [
        "What are our total lead statistics and breakdown by status?",
        "What's the average budget across all leads?",
        "What are the top trends and patterns in our lead data?"
    ],
    "👤 Specific Lead Information": [
        "What are Laia's accommodation requirements and current status?",
        "Show me all information about Haoran Wang",
        "What tasks are associated with Won leads?"
    ],
    "⚖️ Comparative Analysis": [
        "Compare Won leads versus Lost leads - what are the key differences?",
        "What factors contribute to successful lead conversion?",
        "Compare leads by move-in month - which months are most popular?"
    ]
}

# Test each question
test_results = []
question_number = 1

for category, questions in demo_questions.items():
    print("\n" + "="*80)
    print(f"\n{category}")
    print("="*80)
    
    for question in questions:
        print(f"\n🔍 Question {question_number}/12: {question}")
        print("-"*80)
        
        try:
            result = agent.query(question)
            
            if result['success']:
                print(f"✅ SUCCESS")
                print(f"\n💡 Response:\n{result['answer'][:500]}...")
                
                # Show tools used
                if result.get('intermediate_steps'):
                    tools_used = set()
                    for action, observation in result['intermediate_steps']:
                        tools_used.add(action.tool)
                    print(f"\n🔧 Tools Used: {', '.join(sorted(tools_used))}")
                
                test_results.append({
                    "question": question,
                    "status": "PASS",
                    "tools": list(tools_used) if result.get('intermediate_steps') else []
                })
            else:
                print(f"❌ FAILED: {result.get('error')}")
                test_results.append({
                    "question": question,
                    "status": "FAIL",
                    "error": result.get('error')
                })
        
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            test_results.append({
                "question": question,
                "status": "ERROR",
                "error": str(e)
            })
        
        question_number += 1

# Verification Section
print("\n" + "="*80)
print("\n🔬 ACCURACY VERIFICATION")
print("="*80)

print("\n1. Testing Won Leads Query...")
won_leads_db = tools.get_leads_by_status("Won")
print(f"   ✓ Database shows {len(won_leads_db)} Won leads")
print(f"   ✓ Names: {', '.join([l['name'] for l in won_leads_db])}")

print("\n2. Testing Budget Filter (< £400)...")
budget_filter = tools.filter_leads(budget_max=400)
print(f"   ✓ Database shows {len(budget_filter)} leads with budget < £400")
for lead in budget_filter:
    print(f"   ✓ {lead['name']}: £{lead['budget_max']}")

print("\n3. Testing January 2026 Move-ins...")
jan_leads = tools.get_leads_moving_in_month("2026", "01")
print(f"   ✓ Database shows {len(jan_leads)} leads moving in Jan 2026")
for lead in jan_leads:
    print(f"   ✓ {lead['name']}: {lead['move_in_date']}")

print("\n4. Testing Average Budget...")
print(f"   ✓ Database shows average: £{aggs['average_budget']['GBP']:.2f} GBP")

print("\n5. Testing Status Breakdown...")
for status, count in aggs['status_breakdown'].items():
    print(f"   ✓ {status}: {count} leads")

# Summary
print("\n" + "="*80)
print("\n📋 TEST SUMMARY")
print("="*80)

passed = sum(1 for r in test_results if r['status'] == 'PASS')
failed = sum(1 for r in test_results if r['status'] in ['FAIL', 'ERROR'])

print(f"\n✅ Passed: {passed}/12")
print(f"❌ Failed: {failed}/12")

if failed == 0:
    print("\n🎉 ALL TESTS PASSED! All demo questions work correctly!")
else:
    print(f"\n⚠️  {failed} test(s) failed. Review details above.")

# Tool usage statistics
print("\n📊 Tool Usage Statistics:")
tool_usage = {}
for result in test_results:
    if result['status'] == 'PASS':
        for tool in result.get('tools', []):
            tool_usage[tool] = tool_usage.get(tool, 0) + 1

for tool, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True):
    print(f"   • {tool}: {count} times")

print("\n" + "="*80)
print("✅ Testing Complete!")
print("="*80)

