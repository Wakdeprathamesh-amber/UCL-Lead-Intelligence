#!/bin/bash
# Cleanup script to remove old data and deprecated code

echo "🧹 CLEANING UP OLD FILES..."
echo "================================"

# Old data files
echo ""
echo "📊 Removing old CSV data files..."
git rm "Data/UCL Leads Data  - 20 Leads.csv" 2>/dev/null
git rm "Data/UCL Leads Data - Sheet1.csv" 2>/dev/null
rm -f "Data/UCL Leads Data  - 20 Leads.csv"
rm -f "Data/UCL Leads Data - Sheet1.csv"

# Old code files (deprecated)
echo ""
echo "🔧 Removing deprecated code files..."
git rm src/query_tools.py 2>/dev/null
git rm src/ai_agent.py 2>/dev/null
git rm src/aggregate_query_tools.py 2>/dev/null
rm -f src/query_tools.py
rm -f src/ai_agent.py
rm -f src/aggregate_query_tools.py

# Old test files
echo ""
echo "📄 Removing old test files..."
git rm tests/test_unit_query_tools.py 2>/dev/null
rm -f tests/test_unit_query_tools.py

# Remove old test files (not in git, just local)
rm -f test_all_queries.py
rm -f test_comprehensive.py
rm -f test_conversation_queries.py
rm -f test_demo_questions.py
rm -f test_e2e_comprehensive.py
rm -f test_end_to_end.py
rm -f test_integration.py
rm -f test_new_features.py
rm -f test_phase2_aggregation.py
rm -f test_simple_sql.py
rm -f test_smart_prompting.py
rm -f test_suite.py
rm -f test_top_queries_direct.py

# Remove old log files
echo ""
echo "📋 Removing old log files..."
rm -f comprehensive_test_with_guardrail.log
rm -f streamlit.log
rm -f *.log

# Remove old JSON test results
echo ""
echo "📊 Removing old test result files..."
rm -f test_results_comprehensive_*.json

echo ""
echo "✅ Cleanup complete!"
echo "================================"

