"""
AI Agent Module
LangChain agent that orchestrates MCP tools and RAG for intelligent query handling
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from query_tools import LeadQueryTools
from aggregate_query_tools import AggregateQueryTools
from rag_system import LeadRAGSystem

load_dotenv()


class LeadIntelligenceAgent:
    """AI Agent for UCL Lead Intelligence"""
    
    def __init__(self, mode: str = "detailed"):
        """
        Initialize agent with specified mode
        
        Args:
            mode: "detailed" for 19-lead conversation data or "aggregate" for 1,525-lead analytics
        """
        self.mode = mode
        
        if mode == "aggregate":
            self.query_tools = AggregateQueryTools()
            self.rag_enabled = False  # No RAG for aggregate data
            self.rag_system = None
        else:
            self.query_tools = LeadQueryTools()
            # Initialize RAG system (will gracefully handle missing API key)
            try:
                self.rag_system = LeadRAGSystem()
                self.rag_enabled = True
            except Exception as e:
                print(f"⚠️  RAG system not available: {str(e)}")
                self.rag_system = None
                self.rag_enabled = False
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create prompt
        self.prompt = self._create_prompt()
        
        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=False,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )
        
        mode_name = "Aggregate Analytics" if mode == "aggregate" else "Detailed Conversation Intelligence"
        print(f"✅ AI Agent initialized successfully ({mode_name} mode)")
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools from query functions"""
        
        if self.mode == "aggregate":
            # Aggregate mode tools
            tools = [
                Tool(
                    name="get_lead_by_id",
                    func=lambda lead_id: json.dumps(self.query_tools.get_lead_by_id(lead_id), indent=2),
                    description="""Get aggregate lead information by ID.
                    Input: lead_id (string)
                    Returns: Lead details including date, country, state, lost_reason, city."""
                ),
                
                Tool(
                    name="filter_leads",
                    func=lambda query: self._filter_leads_wrapper(query),
                    description="""Filter aggregate leads by various criteria.
                    Input: JSON string with filters like:
                    {"state": "lost", "source_country": "Japan", "city_name": "London", "lost_reason": "Parent lead already present"}
                    Available filters: state, source_country, city_name, lost_reason, repeat
                    Returns: List of matching leads."""
                ),
                
                Tool(
                    name="get_aggregations",
                    func=lambda _: json.dumps(self.query_tools.get_aggregations(), indent=2),
                    description="""Get comprehensive KPIs and statistics about all aggregate leads (1,525 leads).
                    Input: empty string or any text (ignored)
                    Returns: Total leads, status breakdown, conversion rate, lost reasons, country breakdown, 
                    city breakdown, repeat rate, monthly trends."""
                ),
                
                Tool(
                    name="get_leads_by_status",
                    func=lambda status: json.dumps(self.query_tools.get_leads_by_status(status), indent=2),
                    description="""Get all leads with a specific status.
                    Input: status (one of: 'won', 'lost')
                    Returns: List of leads with that status."""
                ),
                
                Tool(
                    name="get_top_lost_reasons",
                    func=lambda limit: json.dumps(self.query_tools.get_top_lost_reasons(int(str(limit)) if str(limit).isdigit() else 10), indent=2),
                    description="""Get top lost reasons across all leads.
                    Input: limit as string (e.g., "10"), optional, default 10
                    Returns: List of lost reasons ranked by frequency."""
                ),
                
                Tool(
                    name="get_country_statistics",
                    func=lambda _: json.dumps(self.query_tools.get_country_statistics(), indent=2),
                    description="""Get detailed statistics by source country.
                    Input: empty string or any text (ignored)
                    Returns: Country breakdown with total, won, lost, and conversion rates."""
                ),
                
                Tool(
                    name="search_leads_by_country",
                    func=lambda country: json.dumps(self.query_tools.search_leads_by_country(country), indent=2),
                    description="""Search leads by source country.
                    Input: country name (e.g., 'Japan', 'United Kingdom')
                    Returns: List of leads from that country."""
                )
            ]
        else:
            # Detailed mode tools
            tools = [
                Tool(
                    name="get_lead_by_id",
                    func=lambda lead_id: json.dumps(self.query_tools.get_lead_by_id(lead_id), indent=2),
                    description="""Get complete information about a specific lead by their ID.
                    Input: lead_id (string like '#10245302799')
                    Returns: Full lead details including status, requirements, budget, move-in date, etc."""
                ),
                
                Tool(
                    name="filter_leads",
                    func=lambda query: self._filter_leads_wrapper(query),
                    description="""Filter leads by various criteria.
                    Input: JSON string with filters like:
                    {"status": "Won", "budget_max": 400, "move_in_month": "2026-01", "location": "London", 
                     "lease_duration_min": 40, "lease_duration_max": 60}
                    Available filters: status, nationality, location, university, budget_max, budget_min, 
                    move_in_month, room_type, lease_duration_min, lease_duration_max
                    Returns: List of matching leads with their details."""
                ),
                
                Tool(
                    name="get_aggregations",
                    func=lambda _: json.dumps(self.query_tools.get_aggregations(), indent=2),
                    description="""Get comprehensive KPIs and statistics about all leads.
                    Input: empty string or any text (ignored)
                    Returns: Total leads, status breakdown, won/lost counts, location distribution,
                    university breakdown, average budgets, room type preferences, move-in month trends,
                    lease duration statistics (average, min, max)."""
                ),
                
                Tool(
                    name="get_leads_by_status",
                    func=lambda status: json.dumps(self.query_tools.get_leads_by_status(status), indent=2),
                    description="""Get all leads with a specific status.
                    Input: status (one of: 'Won', 'Lost', 'Oppurtunity', 'Contacted', 'Disputed')
                    Returns: List of leads with that status."""
                ),
                
                Tool(
                    name="search_leads_by_name",
                    func=lambda name: json.dumps(self.query_tools.search_leads_by_name(name), indent=2),
                    description="""Search for leads by name (partial match supported).
                    Input: name or partial name
                    Returns: Matching leads with their basic info."""
                ),
                
                Tool(
                    name="get_lead_tasks",
                    func=lambda lead_id: json.dumps(self.query_tools.get_lead_tasks(lead_id), indent=2),
                    description="""Get all tasks and actionables for a specific lead.
                    Input: lead_id (string like '#10245302799')
                    Returns: List of tasks with status, due dates, and descriptions."""
                ),
                
                Tool(
                    name="get_conversation_summary",
                    func=lambda lead_id: json.dumps(self.query_tools.get_conversation_summary(lead_id), indent=2),
                    description="""Get detailed conversation summary and insights for a specific lead.
                    Input: lead_id (string like '#10245302799')
                    Returns: Comprehensive conversation summary with student behavior, key points, timeline."""
                ),
                
                Tool(
                    name="get_lead_properties",
                    func=lambda lead_id: json.dumps(self.query_tools.get_lead_properties(lead_id), indent=2),
                    description="""Get properties and rooms that a specific lead is considering.
                    Input: lead_id (string like '#10245302799')
                    Returns: Property names and room types the lead is interested in."""
                ),
                
                Tool(
                    name="get_popular_properties",
                    func=lambda x="": json.dumps(self.query_tools.get_popular_properties(), indent=2),
                    description="""Get list of most popular properties across all leads.
                    Input: any text (optional, ignored)
                    Returns: Properties ranked by number of leads considering them."""
                ),
                
                Tool(
                    name="get_lead_amenities",
                    func=lambda lead_id: json.dumps(self.query_tools.get_lead_amenities(lead_id), indent=2),
                    description="""Get amenities requested by a specific lead.
                    Input: lead_id (string like '#10245302799')
                    Returns: List of amenities the lead wants."""
                ),
                
                Tool(
                    name="get_popular_amenities",
                    func=lambda x="": json.dumps(self.query_tools.get_popular_amenities(), indent=2),
                    description="""Get most requested amenities across all leads.
                    Input: any text (optional, ignored)
                    Returns: Amenities ranked by how many leads requested them."""
                )
            ]
            
            # Add RAG tools if available (only for detailed mode)
            if self.rag_enabled:
                tools.extend([
                    Tool(
                        name="semantic_search",
                        func=lambda query: self._semantic_search_wrapper(query),
                        description="""Perform semantic search across all lead conversations, summaries, and objections.
                        Use this to find leads discussing specific topics, concerns, or patterns.
                        Input: natural language query about what you're looking for
                        Returns: Most relevant conversation excerpts with lead context."""
                    ),
                    
                    Tool(
                        name="search_objections",
                        func=lambda query: self._search_objections_wrapper(query),
                        description="""Search specifically for objections and concerns raised by leads.
                        Input: query about objection type (e.g., 'budget concerns', 'pricing issues')
                        Returns: Relevant objections and concerns from leads."""
                    )
                ])
        
        return tools
    
    def _filter_leads_wrapper(self, query_str: str) -> str:
        """Wrapper for filter_leads to handle JSON input"""
        try:
            # Handle various input formats
            if not isinstance(query_str, str):
                query_str = str(query_str)
            
            # Try JSON parsing first
            filters = json.loads(query_str)
            results = self.query_tools.filter_leads(**filters)
            return json.dumps(results, indent=2)
            
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # Try to parse as simple key=value format
            # e.g., "status=Won,budget_max=400"
            filters = {}
            
            # Handle if it's just a simple value
            if '=' not in str(query_str) and ',' not in str(query_str):
                # Likely a single value, return error
                return json.dumps({
                    "error": f"Invalid filter format. Expected JSON or key=value pairs. Got: {query_str}"
                })
            
            for part in str(query_str).split(','):
                if '=' in part:
                    key, value = part.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Try to convert to appropriate type
                    try:
                        # Try int first, then float
                        if '.' not in value:
                            value = int(value)
                        else:
                            value = float(value)
                    except:
                        pass
                    filters[key] = value
            
            if not filters:
                return json.dumps({
                    "error": "No valid filters found",
                    "input_received": str(query_str)
                })
            
            results = self.query_tools.filter_leads(**filters)
            return json.dumps(results, indent=2)
    
    def _semantic_search_wrapper(self, query: str) -> str:
        """Wrapper for semantic search"""
        if not self.rag_enabled:
            return json.dumps({"error": "RAG system not available"})
        
        results = self.rag_system.semantic_search(query, n_results=5)
        
        # Format results for LLM
        formatted = []
        for r in results:
            formatted.append({
                "lead_id": r['metadata'].get('lead_id'),
                "lead_name": r['metadata'].get('lead_name'),
                "status": r['metadata'].get('status'),
                "type": r['metadata'].get('chunk_type'),
                "content_preview": r['content'][:500],
                "relevance_score": round(1 - r['distance'], 3) if r['distance'] else None
            })
        
        return json.dumps(formatted, indent=2)
    
    def _search_objections_wrapper(self, query: str) -> str:
        """Wrapper for objections search"""
        if not self.rag_enabled:
            return json.dumps({"error": "RAG system not available"})
        
        results = self.rag_system.search_objections(query, n_results=5)
        
        # Format results
        formatted = []
        for r in results:
            formatted.append({
                "lead_id": r['metadata'].get('lead_id'),
                "lead_name": r['metadata'].get('lead_name'),
                "status": r['metadata'].get('status'),
                "objection_content": r['content'][:400]
            })
        
        return json.dumps(formatted, indent=2)
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt"""
        
        if self.mode == "aggregate":
            system_message = """You are an intelligent AI assistant for UCL (University College London) Lead Intelligence - AGGREGATE ANALYTICS MODE.
You help university admins analyze large-scale lead data (1,525 leads) with volume analytics, lost reasons, country trends, and conversion insights.

## Your Capabilities (Aggregate Mode):
1. **Volume Analytics**: Analyze 1,525 leads with country, city, and geographic trends
2. **Lost Reason Analysis**: Identify top lost reasons and patterns
3. **Conversion Insights**: Calculate conversion rates, repeat lead analysis
4. **Country/Geography Trends**: Breakdown by source countries, cities, regions
5. **Time-Series Analysis**: Monthly trends, date-based patterns
6. **Status Filtering**: Filter by won, lost, repeat status

## Available Data:
- 1,525 aggregate leads
- Lost reasons (explicit field)
- Source countries and cities
- Lead dates and monthly trends
- Repeat lead tracking
- Status breakdown (won/lost)

## What You DON'T Have in Aggregate Mode:
- Individual conversation details
- Budget information
- Property preferences
- Amenity requests
- Detailed requirements
- Communication timeline
"""
        else:
            system_message = """You are an intelligent AI assistant for UCL (University College London) Lead Intelligence - DETAILED CONVERSATION MODE.
You help university admins understand their student leads, analyze trends, and extract insights from conversations.

## Your Capabilities (Detailed Mode):
1. **Structured Queries**: Filter leads by status, budget, location, move-in dates, university, etc.
2. **KPI & Analytics**: Provide statistics, trends, breakdowns by various dimensions
3. **Lead Details**: Get comprehensive information about specific leads
4. **Conversation Intelligence**: Search and analyze lead conversations, objections, and concerns (when RAG is enabled)

## CRITICAL Guidelines:
- **Be HONEST about data availability**: If data doesn't exist, say "I don't have this information" - NEVER make up or guess data
- **NO HALLUCINATION**: Only provide information that exists in the tools' responses
- **Be Precise**: Always cite sources (lead IDs, names) and provide evidence
- **Be Analytical**: When asked about trends, compare numbers and explain patterns
- **Be Helpful**: Translate data into actionable insights
- **Show Confidence**: Clearly distinguish between data you have vs. data you don't have
- **Format Well**: Use bullet points, numbers, and clear structure

## When Data is NOT Available:
❌ DON'T SAY: "The data shows..." (if it doesn't)
❌ DON'T GUESS: Don't infer data that isn't in tool responses
✅ DO SAY: "I don't have information about [X] in the current data"
✅ DO SAY: "This data is not available in the system"
✅ DO SAY: "I can see [what you DO have] but not [what you don't]"

## Examples of Good Responses:
- "Based on the data, there are 5 Won leads. Here are the details: [list with names and key info]"
- "Laia's budget is £395 (GBP), moving in January 2026 to London for UCL"
- "I don't have specific property names in the current data, but I can see location is London" ← HONEST

## Examples of BAD Responses (NEVER DO THIS):
- "The property is likely XYZ..." ← NO GUESSING
- "Based on similar leads, it might be..." ← NO INFERENCE WITHOUT DATA
- Making up details not in tool responses ← NEVER

## When Analyzing:
- Always get the full context using available tools
- For "why" questions, look at both structured data AND conversation summaries
- Provide specific numbers, not vague statements
- Cite which leads you're referring to
- If you don't have certain data, explicitly say so

Now, answer the user's question using the available tools. Be honest if data is not available."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    def query(self, question: str, chat_history: Optional[List] = None) -> Dict[str, Any]:
        """Query the agent"""
        try:
            result = self.agent_executor.invoke({
                "input": question,
                "chat_history": chat_history or []
            })
            
            return {
                "answer": result['output'],
                "intermediate_steps": result.get('intermediate_steps', []),
                "success": True
            }
        
        except Exception as e:
            return {
                "answer": f"I encountered an error: {str(e)}",
                "error": str(e),
                "success": False
            }
    
    def format_response_with_sources(self, result: Dict) -> str:
        """Format response with source citations"""
        answer = result['answer']
        
        # Add sources section if intermediate steps exist
        if result.get('intermediate_steps'):
            answer += "\n\n---\n**Sources Used:**\n"
            for i, (action, observation) in enumerate(result['intermediate_steps'], 1):
                tool_name = action.tool
                answer += f"{i}. Used `{tool_name}` tool\n"
        
        return answer


if __name__ == "__main__":
    # Test the agent
    print("="*60)
    print("🤖 INITIALIZING AI AGENT")
    print("="*60)
    
    agent = LeadIntelligenceAgent()
    
    print("\n" + "="*60)
    print("🧪 TESTING QUERIES")
    print("="*60)
    
    # Test queries
    test_queries = [
        "How many total leads do we have?",
        "Show me leads moving in January 2026 with budget less than 400 pounds",
        "What is Laia's accommodation requirement?",
        "List all Won leads"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Q: {query}")
        print("-" * 60)
        
        result = agent.query(query)
        print(f"💡 A: {result['answer']}\n")
    
    print("="*60)
    print("✅ AI Agent Ready")
    print("="*60)

