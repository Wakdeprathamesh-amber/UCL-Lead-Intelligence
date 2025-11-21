#!/usr/bin/env python3
"""
Comprehensive Test Suite - ALL Query Types
Tests the complete system with all queries from all test files
"""

import sys
import time
import json
from datetime import datetime
from src.ai_agent_simple import SimpleLeadIntelligenceAgent

class ComprehensiveTestSuite:
    def __init__(self):
        self.agent = SimpleLeadIntelligenceAgent(db_path="data/leads.db")
        self.results = []
        self.start_time = time.time()
        
    def test_query(self, category, query, expected_keywords=None, min_length=50):
        """Test a single query"""
        print(f"\n{'='*80}")
        print(f"Category: {category}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        start = time.time()
        result = self.agent.query(query)
        elapsed = time.time() - start
        
        success = result['success']
        answer = result.get('answer', '')
        
        # Check expected keywords
        has_keywords = True
        if expected_keywords and success:
            has_keywords = any(kw.lower() in answer.lower() for kw in expected_keywords)
        
        # Check answer length
        sufficient_length = len(answer) >= min_length if success else True
        
        status = "✅ PASS" if (success and has_keywords and sufficient_length) else "❌ FAIL"
        
        print(f"\nStatus: {status}")
        print(f"Time: {elapsed:.2f}s")
        if success:
            print(f"Answer Length: {len(answer)} chars")
            print(f"Has Keywords: {has_keywords}")
            print(f"\nAnswer Preview:\n{answer[:500]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown')}")
        
        self.results.append({
            'category': category,
            'query': query,
            'success': success,
            'has_keywords': has_keywords,
            'sufficient_length': sufficient_length,
            'time': elapsed,
            'answer': answer[:1000] if answer else None,
            'error': result.get('error')
        })
        
        return success and has_keywords and sufficient_length
    
    def run_all_tests(self):
        """Run all test categories"""
        
        print("="*80)
        print("🧪 COMPREHENSIVE TEST SUITE - ALL QUERY TYPES")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Agent: SimpleLeadIntelligenceAgent (Phase 2)")
        print("="*80)
        
        # Category 1: Basic Lead Queries
        print("\n\n" + "="*80)
        print("📊 CATEGORY 1: BASIC LEAD QUERIES")
        print("="*80)
        
        basic_queries = [
            ("How many total leads do we have?", ["402", "lead"]),
            ("Show me all Won leads", ["won", "lead"]),
            ("What's the status breakdown?", ["status", "won", "lost"]),
            ("How many leads from India?", ["india", "lead"]),
            ("Show me Lost leads", ["lost", "lead"]),
            ("What are the different lead statuses?", ["status", "won", "lost"]),
        ]
        
        for query, keywords in basic_queries:
            self.test_query("Basic Lead Queries", query, keywords)
            time.sleep(1)
        
        # Category 2: Geographic Analysis
        print("\n\n" + "="*80)
        print("🌍 CATEGORY 2: GEOGRAPHIC ANALYSIS")
        print("="*80)
        
        geographic_queries = [
            ("Leads by source country", ["country", "lead"]),
            ("Room types preferred by source country", ["room", "country"]),
            ("Budget distribution by nationality", ["budget", "country"]),
            ("Which countries have the most leads?", ["country", "lead"]),
            ("Lost reasons by source country", ["lost", "country"]),
        ]
        
        for query, keywords in geographic_queries:
            self.test_query("Geographic Analysis", query, keywords)
            time.sleep(1)
        
        # Category 3: Budget & Financial
        print("\n\n" + "="*80)
        print("💰 CATEGORY 3: BUDGET & FINANCIAL")
        print("="*80)
        
        budget_queries = [
            ("What's the average budget?", ["budget", "average"]),
            ("Show me high budget leads (>£300)", ["budget", "lead"]),
            ("Minimum and maximum property prices", ["min", "max", "price"]),
            ("Budget ranges by room type", ["budget", "room"]),
        ]
        
        for query, keywords in budget_queries:
            self.test_query("Budget & Financial", query, keywords)
            time.sleep(1)
        
        # Category 4: Property & Room Analysis
        print("\n\n" + "="*80)
        print("🏠 CATEGORY 4: PROPERTY & ROOM ANALYSIS")
        print("="*80)
        
        property_queries = [
            ("What are the most popular properties?", ["property", "popular"]),
            ("Room types available", ["room", "type"]),
            ("Most booked room types", ["room", "book"]),
            ("Properties by price range", ["property", "price"]),
        ]
        
        for query, keywords in property_queries:
            self.test_query("Property & Room Analysis", query, keywords)
            time.sleep(1)
        
        # Category 5: Tasks & Operations
        print("\n\n" + "="*80)
        print("📋 CATEGORY 5: TASKS & OPERATIONS")
        print("="*80)
        
        task_queries = [
            ("What tasks are pending?", ["task", "pending"]),
            ("How many completed tasks?", ["task", "complete"]),
            ("Show me in-progress tasks", ["task", "progress"]),
        ]
        
        for query, keywords in task_queries:
            self.test_query("Tasks & Operations", query, keywords)
            time.sleep(1)
        
        # Category 6: Conversation Analysis (Phase 2 - Aggregation)
        print("\n\n" + "="*80)
        print("💬 CATEGORY 6: CONVERSATION ANALYSIS (AGGREGATION)")
        print("="*80)
        
        aggregation_queries = [
            ("What are the top queries from students?", ["budget", "message", "student"]),
            ("Most common concerns students have", ["concern", "student"]),
            ("What amenities are most frequently mentioned?", ["amenity", "wifi"]),
            ("Top 5 most asked questions", ["question", "top"]),
            ("Most mentioned topics in WhatsApp", ["whatsapp", "topic"]),
        ]
        
        for query, keywords in aggregation_queries:
            self.test_query("Conversation Analysis", query, keywords)
            time.sleep(1)
        
        # Category 7: Semantic Search (Examples)
        print("\n\n" + "="*80)
        print("🔍 CATEGORY 7: SEMANTIC SEARCH (EXAMPLES)")
        print("="*80)
        
        semantic_queries = [
            ("Show me examples of budget questions", ["budget", "example"]),
            ("Give me examples of students asking about WiFi", ["wifi", "example"]),
            ("What do students say about move-in dates?", ["move", "date"]),
            ("Show me concerns about location", ["location", "concern"]),
        ]
        
        for query, keywords in semantic_queries:
            self.test_query("Semantic Search", query, keywords)
            time.sleep(1)
        
        # Category 8: Complex Analytical
        print("\n\n" + "="*80)
        print("📈 CATEGORY 8: COMPLEX ANALYTICAL QUERIES")
        print("="*80)
        
        complex_queries = [
            ("Compare Won vs Lost leads", ["won", "lost", "compare"]),
            ("What patterns do you see in successful bookings?", ["pattern", "success"]),
            ("Analyze leads by source country and status", ["country", "status"]),
            ("What factors contribute to lead loss?", ["lost", "reason"]),
        ]
        
        for query, keywords in complex_queries:
            self.test_query("Complex Analytical", query, keywords)
            time.sleep(1)
        
        # Category 9: Behavioral Insights
        print("\n\n" + "="*80)
        print("🧠 CATEGORY 9: BEHAVIORAL INSIGHTS")
        print("="*80)
        
        behavioral_queries = [
            ("How do Won leads communicate differently than Lost leads?", ["won", "lost", "communication"]),
            ("What objections do we face most?", ["objection", "concern"]),
            ("Communication patterns by status", ["communication", "status"]),
        ]
        
        for query, keywords in behavioral_queries:
            self.test_query("Behavioral Insights", query, keywords)
            time.sleep(1)
        
        # Category 10: Specific Data Points
        print("\n\n" + "="*80)
        print("🎯 CATEGORY 10: SPECIFIC DATA POINTS")
        print("="*80)
        
        specific_queries = [
            ("How many students asked about WiFi?", ["wifi", "student"]),
            ("Percentage of leads asking about parking", ["parking", "percent"]),
            ("How many leads mentioned gym facilities?", ["gym", "lead"]),
        ]
        
        for query, keywords in specific_queries:
            self.test_query("Specific Data Points", query, keywords)
            time.sleep(1)
        
        # Category 11: Time-based (if available)
        print("\n\n" + "="*80)
        print("📅 CATEGORY 11: TEMPORAL QUERIES")
        print("="*80)
        
        temporal_queries = [
            ("When do most students plan to move in?", ["move", "date"]),
            ("What's the typical inquiry to booking timeline?", ["timeline", "booking"]),
        ]
        
        for query, keywords in temporal_queries:
            self.test_query("Temporal Queries", query, keywords)
            time.sleep(1)
        
        # Category 12: Multi-step Reasoning
        print("\n\n" + "="*80)
        print("🔗 CATEGORY 12: MULTI-STEP REASONING")
        print("="*80)
        
        reasoning_queries = [
            ("Which source countries have the highest budget and what do they prefer?", ["country", "budget", "prefer"]),
            ("For high-budget leads, what are their main concerns?", ["budget", "concern", "high"]),
            ("What room types do students from India prefer and why?", ["india", "room", "prefer"]),
        ]
        
        for query, keywords in reasoning_queries:
            self.test_query("Multi-step Reasoning", query, keywords)
            time.sleep(1)
        
        # Generate Summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        
        total_time = time.time() - self.start_time
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r['success'] and r['has_keywords'] and r['sufficient_length'])
        failed = total_tests - passed
        
        # Group by category
        by_category = {}
        for r in self.results:
            cat = r['category']
            if cat not in by_category:
                by_category[cat] = {'total': 0, 'passed': 0, 'failed': 0}
            by_category[cat]['total'] += 1
            if r['success'] and r['has_keywords'] and r['sufficient_length']:
                by_category[cat]['passed'] += 1
            else:
                by_category[cat]['failed'] += 1
        
        # Calculate avg time
        successful_times = [r['time'] for r in self.results if r['success']]
        avg_time = sum(successful_times) / len(successful_times) if successful_times else 0
        
        print("\n\n" + "="*80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        print(f"\n⏱️  Total Execution Time: {total_time/60:.2f} minutes ({total_time:.1f}s)")
        print(f"📝 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed} ({passed/total_tests*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total_tests*100:.1f}%)")
        print(f"⚡ Average Response Time: {avg_time:.2f}s")
        
        print(f"\n\n{'='*80}")
        print("📋 RESULTS BY CATEGORY")
        print(f"{'='*80}")
        
        for cat, stats in by_category.items():
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
            print(f"\n{status} {cat}:")
            print(f"   Total: {stats['total']}")
            print(f"   Passed: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
            if stats['failed'] > 0:
                print(f"   Failed: {stats['failed']}")
        
        print(f"\n\n{'='*80}")
        print("❌ FAILED QUERIES (if any)")
        print(f"{'='*80}")
        
        failed_queries = [r for r in self.results if not (r['success'] and r['has_keywords'] and r['sufficient_length'])]
        
        if failed_queries:
            for i, r in enumerate(failed_queries, 1):
                print(f"\n{i}. {r['category']}: {r['query']}")
                if not r['success']:
                    print(f"   Error: {r['error']}")
                elif not r['has_keywords']:
                    print(f"   Issue: Missing expected keywords")
                elif not r['sufficient_length']:
                    print(f"   Issue: Answer too short")
        else:
            print("\n🎉 NO FAILURES - ALL TESTS PASSED!")
        
        print(f"\n\n{'='*80}")
        print("🎯 OVERALL ASSESSMENT")
        print(f"{'='*80}")
        
        if passed / total_tests >= 0.9:
            grade = "A (Excellent)"
            assessment = "System is production-ready with excellent performance"
        elif passed / total_tests >= 0.8:
            grade = "B (Good)"
            assessment = "System is production-ready with good performance"
        elif passed / total_tests >= 0.7:
            grade = "C (Acceptable)"
            assessment = "System is functional but needs improvements"
        else:
            grade = "D (Needs Work)"
            assessment = "System needs significant improvements"
        
        print(f"\n✅ Success Rate: {passed/total_tests*100:.1f}%")
        print(f"🏆 Grade: {grade}")
        print(f"📝 Assessment: {assessment}")
        print(f"⚡ Performance: Average {avg_time:.2f}s per query")
        
        print(f"\n{'='*80}")
        print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        # Save detailed results
        self.save_results()
    
    def save_results(self):
        """Save detailed results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_results_comprehensive_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: {filename}")


def main():
    suite = ComprehensiveTestSuite()
    suite.run_all_tests()


if __name__ == "__main__":
    main()

