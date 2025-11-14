"""
Comprehensive Test Suite for UCL Lead Intelligence AI
Tests both Detailed and Aggregate modes with edge cases
"""

import sys
sys.path.insert(0, 'src')

from ai_agent import LeadIntelligenceAgent
from query_tools import LeadQueryTools
from aggregate_query_tools import AggregateQueryTools
import json


class TestSuite:
    """Comprehensive test suite"""
    
    def __init__(self):
        self.detailed_agent = LeadIntelligenceAgent(mode="detailed")
        self.aggregate_agent = LeadIntelligenceAgent(mode="aggregate")
        self.detailed_tools = LeadQueryTools()
        self.aggregate_tools = AggregateQueryTools()
        
        self.results = {
            "detailed": {"passed": 0, "failed": 0, "errors": []},
            "aggregate": {"passed": 0, "failed": 0, "errors": []},
            "edge_cases": {"passed": 0, "failed": 0, "errors": []}
        }
    
    def test(self, mode, category, query, expected_keywords=None, should_fail=False):
        """Run a single test"""
        agent = self.detailed_agent if mode == "detailed" else self.aggregate_agent
        
        try:
            result = agent.query(query)
            
            if should_fail:
                if not result['success']:
                    self.results[mode]["passed"] += 1
                    print(f"  ✅ PASS (Expected failure)")
                    return True
                else:
                    self.results[mode]["failed"] += 1
                    error = f"Expected failure but query succeeded: {query}"
                    self.results[mode]["errors"].append(error)
                    print(f"  ❌ FAIL: {error}")
                    return False
            
            if not result['success']:
                self.results[mode]["failed"] += 1
                error = f"Query failed: {query} - {result.get('error', 'Unknown')}"
                self.results[mode]["errors"].append(error)
                print(f"  ❌ FAIL: {error}")
                return False
            
            # Check for expected keywords if provided
            if expected_keywords:
                answer_lower = result['answer'].lower()
                # Check for any keyword match (case-insensitive, handles plurals)
                found = any(keyword.lower() in answer_lower or keyword.lower() + 's' in answer_lower or keyword.lower() + 'es' in answer_lower for keyword in expected_keywords)
                if not found:
                    self.results[mode]["failed"] += 1
                    error = f"Expected keywords not found: {expected_keywords}"
                    self.results[mode]["errors"].append(error)
                    print(f"  ❌ FAIL: {error}")
                    print(f"     Response: {result['answer'][:200]}...")
                    return False
            
            self.results[mode]["passed"] += 1
            print(f"  ✅ PASS")
            return True
            
        except Exception as e:
            self.results[mode]["failed"] += 1
            error = f"Exception: {str(e)}"
            self.results[mode]["errors"].append(error)
            print(f"  ❌ EXCEPTION: {error}")
            return False
    
    def run_detailed_mode_tests(self):
        """Test Detailed Mode (19 leads)"""
        print("\n" + "="*80)
        print("📊 DETAILED MODE TESTS (19 Leads)")
        print("="*80)
        
        tests = [
            # Basic Queries
            ("Basic", "How many total leads do we have?", ["19"]),
            ("Basic", "What's our conversion rate?", ["31", "32", "6", "19"]),
            ("Basic", "Show me all Won leads", ["Won", "6"]),
            ("Basic", "How many Lost leads?", ["7", "Lost"]),
            
            # Property Queries
            ("Property", "Which property is Laia booking?", ["GoBritanya", "Sterling"]),
            ("Property", "What are the most popular properties?", ["property", "Portobello"]),
            ("Property", "Show me all properties", ["property"]),
            ("Property", "Which properties do Won leads prefer?", ["property"]),
            
            # Budget Queries
            ("Budget", "What's the average budget?", ["343", "£"]),
            ("Budget", "Show leads with budget between £300 and £400", ["budget", "£"]),
            ("Budget", "Compare Won vs Lost budgets", ["budget", "compare"]),
            
            # Lease Duration
            ("Duration", "What's the average lease duration?", ["33.6", "weeks"]),
            ("Duration", "Show me leads with lease duration over 40 weeks", ["weeks", "42"]),
            ("Duration", "What's the shortest and longest duration?", ["5", "51"]),
            
            # Amenity Queries
            ("Amenity", "What amenities do students want?", ["amenity", "WiFi"]),
            ("Amenity", "What amenities does Laia want?", ["WiFi", "study"]),
            
            # Geography
            ("Geography", "Which cities are students moving to?", ["London", "Wembley"]),
            ("Geography", "Show location breakdown", ["London", "15"]),
            
            # Conversion Analysis
            ("Conversion", "Why did we lose leads?", ["don't have", "communication"]),
            ("Conversion", "What do Won leads have in common?", ["London", "UCL"]),
            
            # Lead Search
            ("Search", "Tell me about Laia", ["Laia", "Vilatersana"]),
            ("Search", "Find lead #10245302799", ["10245302799"]),
        ]
        
        for category, query, keywords in tests:
            print(f"\n🔍 [{category}] {query}")
            self.test("detailed", category, query, keywords)
    
    def run_aggregate_mode_tests(self):
        """Test Aggregate Mode (1,525 leads)"""
        print("\n" + "="*80)
        print("📊 AGGREGATE MODE TESTS (1,525 Leads)")
        print("="*80)
        
        tests = [
            # Basic Queries
            ("Basic", "How many total leads do we have?", ["1525", "1,525"]),
            ("Basic", "What's our conversion rate?", ["6", "conversion"]),
            ("Basic", "Show me all Won leads", ["won", "94"]),
            ("Basic", "How many Lost leads?", ["1423", "lost"]),
            
            # Lost Reasons
            ("Lost Reasons", "What are the top lost reasons?", ["Parent lead", "1050"]),
            ("Lost Reasons", "Why are we losing leads?", ["Parent lead", "Not responded"]),
            ("Lost Reasons", "Show me top 5 lost reasons", ["Parent", "Not responded"]),
            
            # Country Analytics
            ("Country", "Which countries send the most leads?", ["United Kingdom", "527"]),
            ("Country", "Show me leads from Japan", ["Japan", "78"]),
            ("Country", "What's the country breakdown?", ["United Kingdom", "United States"]),
            ("Country", "Which country has the highest conversion rate?", ["country", "conversion"]),
            
            # Geography
            ("Geography", "Which cities have the most leads?", ["London"]),
            ("Geography", "Show city breakdown", ["city"]),
            
            # Trends
            ("Trends", "Show me monthly lead trends", ["month", "trend"]),
            ("Trends", "What are the lead trends over time?", ["month", "2025"]),
            
            # Repeat Leads
            ("Repeat", "How many repeat leads do we have?", ["repeat", "1050"]),
            ("Repeat", "What's the repeat rate?", ["68.9", "repeat"]),
            
            # Status Filtering
            ("Status", "Show me all lost leads", ["lost", "1423"]),
            ("Status", "Filter leads by status won", ["won", "94"]),
        ]
        
        for category, query, keywords in tests:
            print(f"\n🔍 [{category}] {query}")
            self.test("aggregate", category, query, keywords)
    
    def run_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n" + "="*80)
        print("⚠️  EDGE CASES & ERROR HANDLING")
        print("="*80)
        
        edge_tests = [
            # Invalid Lead IDs (Should handle gracefully, not fail)
            ("Invalid ID", "detailed", "Tell me about lead #99999999999", ["don't have", "not exist", "does not exist"], False),
            ("Invalid ID", "aggregate", "Get lead #99999999999", ["don't have", "not available", "aggregate mode"], False),
            
            # Empty/Invalid Queries
            ("Empty Query", "detailed", "", None, False),
            ("Nonsense Query", "detailed", "asdfghjkl qwerty", None, False),
            
            # Out of Range Filters
            ("High Budget", "detailed", "Show leads with budget > £10000", None, False),
            ("Future Date", "detailed", "Show leads moving in 2030", None, False),
            
            # Missing Data Queries
            ("Missing Data", "detailed", "What's the credit score for leads?", ["don't have", "information"], False),
            ("Missing Data", "aggregate", "What amenities do students want?", ["don't have", "amenity"], False),
            
            # Boundary Conditions
            ("Zero Results", "detailed", "Show leads with budget < £10", None, False),
            ("Zero Results", "aggregate", "Show leads from Antarctica", None, False),
            
            # Special Characters
            ("Special Chars", "detailed", "Find leads with name containing '&' or '@'", None, False),
            
            # Case Sensitivity
            ("Case Insensitive", "detailed", "show me WON leads", ["Won", "6"], False),
            ("Case Insensitive", "aggregate", "SHOW LOST LEADS", ["lost"], False),
        ]
        
        for test_name, mode, query, keywords, should_fail in edge_tests:
            print(f"\n🔍 [{test_name}] {query}")
            if mode == "detailed":
                self.test("detailed", "edge", query, keywords, should_fail)
            else:
                self.test("aggregate", "edge", query, keywords, should_fail)
    
    def run_data_isolation_tests(self):
        """Verify data isolation between modes"""
        print("\n" + "="*80)
        print("🔒 DATA ISOLATION TESTS")
        print("="*80)
        
        # Test that detailed mode shows 19, aggregate shows 1,525
        print("\n🔍 Testing lead count isolation...")
        det_result = self.detailed_agent.query("How many total leads?")
        agg_result = self.aggregate_agent.query("How many total leads?")
        
        det_has_19 = "19" in det_result['answer'] and "1525" not in det_result['answer']
        agg_has_1525 = "1525" in agg_result['answer'] or "1,525" in agg_result['answer']
        
        if det_has_19 and agg_has_1525:
            print("  ✅ PASS: Data isolation verified")
            self.results["detailed"]["passed"] += 1
            self.results["aggregate"]["passed"] += 1
        else:
            print("  ❌ FAIL: Data mixing detected!")
            print(f"     Detailed: {det_result['answer'][:100]}")
            print(f"     Aggregate: {agg_result['answer'][:100]}")
            self.results["detailed"]["failed"] += 1
            self.results["aggregate"]["failed"] += 1
        
        # Test that aggregate mode doesn't have property data
        print("\n🔍 Testing property query in aggregate mode...")
        agg_result = self.aggregate_agent.query("Which property is Laia booking?")
        answer_lower = agg_result['answer'].lower()
        has_dont_have = "don't have" in answer_lower or "not available" in answer_lower or "aggregate mode" in answer_lower or "don't have access" in answer_lower
        if has_dont_have:
            print("  ✅ PASS: Aggregate correctly says no property data")
            self.results["aggregate"]["passed"] += 1
        else:
            print("  ❌ FAIL: Aggregate mode returned property data!")
            print(f"     Response: {agg_result['answer'][:200]}")
            self.results["aggregate"]["failed"] += 1
        
        # Test that detailed mode doesn't have lost reasons
        print("\n🔍 Testing lost reasons in detailed mode...")
        det_result = self.detailed_agent.query("What are the top lost reasons?")
        if "don't have" in det_result['answer'].lower() or "not available" in det_result['answer'].lower() or "Parent lead" not in det_result['answer']:
            print("  ✅ PASS: Detailed mode correctly handles lost reasons")
            self.results["detailed"]["passed"] += 1
        else:
            print("  ⚠️  WARN: Detailed mode may be mixing data")
            print(f"     Response: {det_result['answer'][:200]}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        total_passed = sum(r["passed"] for r in self.results.values())
        total_failed = sum(r["failed"] for r in self.results.values())
        total_tests = total_passed + total_failed
        
        print(f"\n📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_failed}")
        print(f"   Pass Rate: {(total_passed/total_tests*100):.1f}%")
        
        print(f"\n📊 Detailed Mode:")
        det_total = self.results["detailed"]["passed"] + self.results["detailed"]["failed"]
        print(f"   Tests: {det_total}")
        print(f"   ✅ Passed: {self.results['detailed']['passed']}")
        print(f"   ❌ Failed: {self.results['detailed']['failed']}")
        if det_total > 0:
            print(f"   Pass Rate: {(self.results['detailed']['passed']/det_total*100):.1f}%")
        
        print(f"\n📊 Aggregate Mode:")
        agg_total = self.results["aggregate"]["passed"] + self.results["aggregate"]["failed"]
        print(f"   Tests: {agg_total}")
        print(f"   ✅ Passed: {self.results['aggregate']['passed']}")
        print(f"   ❌ Failed: {self.results['aggregate']['failed']}")
        if agg_total > 0:
            print(f"   Pass Rate: {(self.results['aggregate']['passed']/agg_total*100):.1f}%")
        
        if total_failed > 0:
            print(f"\n❌ Failed Tests:")
            for mode, data in self.results.items():
                if data["errors"]:
                    print(f"\n   {mode.upper()} Mode Errors:")
                    for error in data["errors"][:10]:  # Show first 10
                        print(f"      • {error}")
        
        print("\n" + "="*80)


def main():
    """Run comprehensive test suite"""
    print("="*80)
    print("🧪 COMPREHENSIVE TEST SUITE - UCL Lead Intelligence AI")
    print("="*80)
    
    suite = TestSuite()
    
    # Run all test categories
    suite.run_detailed_mode_tests()
    suite.run_aggregate_mode_tests()
    suite.run_edge_cases()
    suite.run_data_isolation_tests()
    
    # Print summary
    suite.print_summary()


if __name__ == "__main__":
    main()

