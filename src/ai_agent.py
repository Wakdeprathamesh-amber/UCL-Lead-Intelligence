"""
AI Agent Module
LangChain agent that orchestrates MCP tools and RAG for intelligent query handling
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool, StructuredTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from query_tools import LeadQueryTools
from aggregate_query_tools import AggregateQueryTools
from rag_system import LeadRAGSystem
from property_analytics import PropertyAnalytics
from rate_limiter import get_rate_limiter
from audit_logger import get_audit_logger
from reasoning_validator import ReasoningValidator

load_dotenv()


class LeadIntelligenceAgent:
    """AI Agent for UCL Lead Intelligence"""
    
    def __init__(self, mode: str = "detailed"):
        """
        Initialize agent with specified mode
        
        Args:
            mode: "detailed" for 402-lead conversation data or "aggregate" for 1,525-lead analytics
        """
        self.mode = mode
        
        if mode == "aggregate":
            self.query_tools = AggregateQueryTools()
            self.rag_enabled = False  # No RAG for aggregate data
            self.rag_system = None
        else:
            self.query_tools = LeadQueryTools()
            # Initialize property analytics
            self.property_analytics = PropertyAnalytics()
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
            handle_parsing_errors=True,
            max_iterations=15,  # Prevent infinite loops
            max_execution_time=60  # 60 second timeout
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
                
                StructuredTool.from_function(
                    func=self._get_aggregations_wrapper,
                    name="get_aggregations",
                    description="""Get comprehensive KPIs and statistics about all aggregate leads (1,525 leads).
                    This tool takes no arguments.
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
                
                StructuredTool.from_function(
                    func=self._get_country_statistics_wrapper,
                    name="get_country_statistics",
                    description="""Get detailed statistics by source country.
                    This tool takes no arguments.
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
                
                StructuredTool.from_function(
                    func=self._get_aggregations_wrapper,
                    name="get_aggregations",
                    description="""Get comprehensive KPIs and statistics about all leads.
                    This tool takes no arguments.
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
                
                StructuredTool.from_function(
                    func=self._get_popular_properties_wrapper,
                    name="get_popular_properties",
                    description="""Get list of most popular properties across all leads.
                    This tool takes no arguments.
                    Returns: Properties ranked by number of leads considering them."""
                ),
                
                Tool(
                    name="get_lead_amenities",
                    func=lambda lead_id: json.dumps(self.query_tools.get_lead_amenities(lead_id), indent=2),
                    description="""Get amenities requested by a specific lead.
                    Input: lead_id (string like '#10245302799')
                    Returns: List of amenities the lead wants."""
                ),
                
                StructuredTool.from_function(
                    func=self._get_popular_amenities_wrapper,
                    name="get_popular_amenities",
                    description="""Get most requested amenities across all leads.
                    This tool takes no arguments.
                    Returns: Amenities ranked by how many leads requested them."""
                ),
                
                Tool(
                    name="get_lead_timeline",
                    func=lambda args: self._get_lead_timeline_wrapper(args),
                    description="""Get timeline of all events (WhatsApp messages, calls, etc.) for a specific lead.
                    Input: lead_id (string), optionally event_type ('whatsapp', 'call', 'email', 'lead_info')
                    Returns: Chronological list of all events with timestamps, content, and direction."""
                ),
                
                Tool(
                    name="get_call_transcripts",
                    func=lambda args: self._get_call_transcripts_wrapper(args),
                    description="""Get call transcripts for leads.
                    Input: lead_id (optional string) - if provided, returns transcripts for that lead only
                    Returns: List of call transcripts with transcript text, call IDs, and record URLs."""
                ),
                
                Tool(
                    name="search_timeline_events",
                    func=lambda args: self._search_timeline_events_wrapper(args),
                    description="""Search timeline events (WhatsApp messages, calls) by content.
                    Input: query_text (string to search for), optionally event_type ('whatsapp', 'call', etc.)
                    Returns: Matching timeline events with lead context, timestamps, and content."""
                ),
                
                Tool(
                    name="get_crm_data",
                    func=lambda args="": self._get_crm_data_wrapper(args),
                    description="""Get CRM data for leads including lost reasons, country, property info.
                    Input: JSON string with optional filters like {"lead_id": "123"} or {"lost_reason": "Not responded", "location_country": "United Kingdom"}, or empty string for all CRM data.
                    Returns: List of CRM records with all available fields including lost_reason, location_country, phone_country, property_name, etc."""
                ),
                
                StructuredTool.from_function(
                    func=self._get_lost_reasons_analysis_wrapper,
                    name="get_lost_reasons_analysis",
                    description="""Get comprehensive lost reasons analysis grouped by country.
                    This tool takes no arguments.
                    Returns: Dict with top_reasons, by_location_country, by_phone_country breakdowns."""
                ),
                
                StructuredTool.from_function(
                    func=self._get_room_types_by_country_wrapper,
                    name="get_room_types_by_country",
                    description="""Get room type preferences grouped by SOURCE country (where leads are from, not destination).
                    This tool takes no arguments.
                    Returns: Dict with room types by source country showing preferences per country.
                    Note: Uses phone_country (source) not location_country (destination)."""
                ),
                
                StructuredTool.from_function(
                    func=self._get_booked_room_types_by_country_wrapper,
                    name="get_booked_room_types_by_country",
                    description="""Get booked (Won) room types grouped by SOURCE country (where leads are from, not destination).
                    Use this for queries about 'most booked room types by source country' or 'booked room types categorized by source country'.
                    This tool takes no arguments.
                    Returns: Dict with booked room types by source country, showing only Won leads.
                    Note: Uses phone_country (source) not location_country (destination)."""
                ),
                
                StructuredTool.from_function(
                    func=self._get_all_pending_tasks_wrapper,
                    name="get_all_pending_tasks",
                    description="""Get summary of all pending and in-progress tasks across all leads.
                    Returns aggregated statistics (total count, by status, by urgency, by task type) 
                    plus sample urgent tasks (10 most urgent).
                    For specific tasks, use filter_leads + get_lead_tasks.
                    This tool takes no arguments.
                    Returns: Dict with task statistics and sample urgent tasks."""
                ),
                
                StructuredTool.from_function(
                    func=self._get_all_objections_wrapper,
                    name="get_all_objections",
                    description="""Get all objections from the database.
                    This tool takes no arguments.
                    Returns: List of all objections with lead information and objection types."""
                ),
                
                Tool(
                    name="get_won_leads_by_room_type",
                    func=lambda room_type: self._get_won_leads_by_room_type_wrapper(room_type),
                    description="""Get count of Won leads with a specific room type (all countries combined).
                    Input: room_type (string) - e.g., 'ensuite', 'studio', 'private room'
                    Returns: Dict with total count and breakdown by source country for Won leads with that room type."""
                ),
                
                Tool(
                    name="execute_sql_query",
                    func=lambda query, params=None: self._execute_sql_query_wrapper(query, params),
                    description="""Execute a direct SQL SELECT query against the database.
                    Use this when no existing tool fits your need, or when you can write a more efficient query.
                    You know the database schema - use your reasoning to write the best query.
                    
                    Input: 
                    - query (string): SQL SELECT query
                    - params (optional tuple): Parameters for parameterized queries
                    
                    Returns: Dict with 'columns', 'rows' (list of dicts), 'row_count', and 'error' (if any)
                    
                    IMPORTANT: 
                    - Only SELECT queries are allowed (safety)
                    - Use parameterized queries when possible: execute_sql_query("SELECT * FROM leads WHERE status = ?", ("Won",))
                    - Think about the schema and write efficient queries
                    - This is a powerful tool - use your reasoning to determine when it's better than combining multiple tools"""
                ),
                
                StructuredTool.from_function(
                    func=self._get_communication_mode_analysis_wrapper,
                    name="get_communication_mode_analysis",
                    description="""Analyze communication mode preferences (WhatsApp vs Calls) and conversion rates.
                    This tool takes no arguments.
                    Returns: Dict with communication mode statistics, event counts, and conversion rates by mode.
                    Use this for queries about 'communication preferences', 'WhatsApp vs calls', 'conversion by communication mode'."""
                ),
                
                Tool(
                    name="get_property_analytics",
                    func=lambda query="": self._property_analytics_wrapper(query),
                    description="""Get comprehensive property analytics including popularity, conversion rates, and performance metrics.
                    Input: Optional property name (string) to filter by specific property, or empty string for all properties.
                    Returns: Property analytics including popular properties, conversion rates, performance metrics, room type distribution, and status distribution."""
                ),
                
                Tool(
                    name="get_property_details",
                    func=lambda property_name: json.dumps(self.property_analytics.get_property_details(property_name), indent=2),
                    description="""Get detailed information about a specific property.
                    Input: property_name (string) - the name of the property
                    Returns: Detailed property information including total leads, won/lost counts, conversion rate, room types, average budget, and list of leads."""
                ),
                
                Tool(
                    name="compare_properties",
                    func=lambda property_names: self._compare_properties_wrapper(property_names),
                    description="""Compare multiple properties side by side.
                    Input: JSON string with array of property names, e.g., '["Property A", "Property B"]' or comma-separated string
                    Returns: Comparison of properties with metrics like conversion rates, lead counts, and average budgets."""
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
    
    def _get_lead_timeline_wrapper(self, args: str) -> str:
        """Wrapper for get_lead_timeline"""
        try:
            # Try to parse as JSON first
            if isinstance(args, str) and args.strip().startswith('{'):
                params = json.loads(args)
                lead_id = params.get('lead_id', '')
                event_type = params.get('event_type')
            else:
                # Simple string format: "lead_id" or "lead_id,event_type"
                parts = str(args).split(',')
                lead_id = parts[0].strip()
                event_type = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
            
            if not lead_id:
                return json.dumps({"error": "lead_id is required"})
            
            results = self.query_tools.get_lead_timeline(lead_id, event_type)
            return json.dumps(results, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error getting timeline: {str(e)}"})
    
    def _get_call_transcripts_wrapper(self, args: str) -> str:
        """Wrapper for get_call_transcripts"""
        try:
            lead_id = str(args).strip() if args else None
            if not lead_id or lead_id == "":
                lead_id = None
            
            results = self.query_tools.get_call_transcripts(lead_id)
            return json.dumps(results, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error getting transcripts: {str(e)}"})
    
    def _search_timeline_events_wrapper(self, args: str) -> str:
        """Wrapper for search_timeline_events"""
        try:
            # Try to parse as JSON first
            if isinstance(args, str) and args.strip().startswith('{'):
                params = json.loads(args)
                query_text = params.get('query_text', '')
                event_type = params.get('event_type')
            else:
                # Simple string format: "query_text" or "query_text,event_type"
                parts = str(args).split(',')
                query_text = parts[0].strip()
                event_type = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
            
            if not query_text:
                return json.dumps({"error": "query_text is required"})
            
            results = self.query_tools.search_timeline_events(query_text, event_type, limit=20)
            return json.dumps(results, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error searching timeline: {str(e)}"})
    
    def _get_crm_data_wrapper(self, args: str = "") -> str:
        """Wrapper for get_crm_data"""
        try:
            # Handle empty or None input
            if not args or args == "":
                result = self.query_tools.get_crm_data()
                return json.dumps(result, indent=2, default=str)
            
            # Try to parse as JSON first
            if isinstance(args, str) and args.strip().startswith('{'):
                filters = json.loads(args)
            elif args:
                # Try to parse as JSON string
                try:
                    filters = json.loads(str(args))
                except:
                    # If not JSON, treat as lead_id
                    filters = {"lead_id": str(args).strip()}
            else:
                filters = {}
            
            result = self.query_tools.get_crm_data(**filters)
            return json.dumps(result, indent=2, default=str)
        except json.JSONDecodeError:
            # If JSON parsing fails, treat entire string as lead_id
            result = self.query_tools.get_crm_data(lead_id=str(args).strip() if args else None)
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting CRM data: {str(e)}"})
    
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
    
    def _get_all_pending_tasks_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_all_pending_tasks that handles any input type and returns smart aggregation"""
        try:
            # Ignore all inputs, return smart aggregation (summary format)
            result = self.query_tools.get_all_pending_tasks(format="summary")
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting pending tasks: {str(e)}"})
    
    def _get_all_objections_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_all_objections that handles any input type"""
        try:
            # Ignore all inputs, just call the tool
            result = self.query_tools.get_all_objections()
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting objections: {str(e)}"})
    
    def _get_aggregations_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_aggregations that handles any input type"""
        try:
            result = self.query_tools.get_aggregations()
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting aggregations: {str(e)}"})
    
    def _get_country_statistics_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_country_statistics that handles any input type"""
        try:
            result = self.query_tools.get_country_statistics()
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting country statistics: {str(e)}"})
    
    def _get_popular_properties_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_popular_properties that handles any input type"""
        try:
            result = self.query_tools.get_popular_properties()
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting popular properties: {str(e)}"})
    
    def _get_popular_amenities_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_popular_amenities that handles any input type"""
        try:
            result = self.query_tools.get_popular_amenities()
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting popular amenities: {str(e)}"})
    
    def _get_lost_reasons_analysis_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_lost_reasons_analysis that handles any input type"""
        try:
            result = self.query_tools.get_lost_reasons_analysis()
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting lost reasons analysis: {str(e)}"})
    
    def _get_room_types_by_country_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_room_types_by_country that handles any input type"""
        try:
            result = self.query_tools.get_room_types_by_country()
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting room types by country: {str(e)}"})
    
    def _get_booked_room_types_by_country_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_booked_room_types_by_country that handles any input type"""
        try:
            result = self.query_tools.get_booked_room_types_by_country()
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting booked room types by country: {str(e)}"})
    
    def _get_won_leads_by_room_type_wrapper(self, room_type: str) -> str:
        """Wrapper for get_won_leads_by_room_type"""
        try:
            if not room_type or not isinstance(room_type, str):
                return json.dumps({"error": "room_type parameter is required"})
            result = self.query_tools.get_won_leads_by_room_type(room_type.strip())
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting Won leads by room type: {str(e)}"})
    
    def _execute_sql_query_wrapper(self, query: str, params: Any = None) -> str:
        """Wrapper for execute_sql_query"""
        try:
            # Handle params - could be tuple, list, or None
            if params:
                if isinstance(params, str):
                    # Try to parse as JSON if string
                    try:
                        params = json.loads(params)
                        if isinstance(params, list):
                            params = tuple(params)
                    except:
                        params = (params,)
                elif isinstance(params, list):
                    params = tuple(params)
            
            result = self.query_tools.execute_sql_query(query, params)
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error executing SQL query: {str(e)}"})
    
    def _get_communication_mode_analysis_wrapper(self, *args, **kwargs) -> str:
        """Wrapper for get_communication_mode_analysis"""
        try:
            result = self.query_tools.get_communication_mode_analysis()
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error getting communication mode analysis: {str(e)}"})
    
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

## YOUR ROLE:
You are a specialized AI assistant that provides data-driven insights about student leads for university accommodation services. You have access to comprehensive lead data, conversations, CRM records, and analytics tools.

## DATA AVAILABLE:
- **402 leads** with full conversation data
- **2,271 pending/in-progress tasks** across all leads
- **406 CRM records** with lost reasons, country data, property info
- **10,000+ conversation documents** (embedded in RAG system)
- **Lead statuses**: Won, Lost, Opportunity, Contacted, Disputed
- **Full conversation timelines**: WhatsApp messages, calls, emails
- **Property preferences**: Room types, amenities, locations
- **Budget and requirements**: Move-in dates, lease durations, university info

## YOUR TOOLS (24 total, organized by category):

### 📊 **Analytics & Aggregations** (Use for statistics and trends):
1. `get_aggregations` - Comprehensive KPIs (total leads, status breakdown, averages, trends)
2. `get_lost_reasons_analysis` - Pre-computed lost reasons by country (FASTEST for this query)
3. `get_room_types_by_country` - Pre-computed room preferences by country (FASTEST for this query)
4. `get_all_pending_tasks` - Task summary with statistics (total, by status, by urgency, by type)
5. `get_all_objections` - All objections from database
6. `get_property_analytics` - Property popularity, conversion rates, performance metrics
7. `get_popular_properties` - Most popular properties ranked
8. `get_popular_amenities` - Most requested amenities ranked

### 🔍 **Lead Lookup & Filtering** (Use for finding specific leads):
9. `get_lead_by_id` - Get complete info for a specific lead by ID
10. `filter_leads` - Filter by status, budget, location, university, move-in date, etc.
11. `get_leads_by_status` - Get all leads with specific status (Won, Lost, etc.)
12. `search_leads_by_name` - Search leads by name (partial match)

### 📋 **Lead Details** (Use for comprehensive lead information):
13. `get_lead_tasks` - All tasks for a specific lead
14. `get_conversation_summary` - Detailed conversation summary and insights
15. `get_lead_properties` - Properties and room types a lead is considering
16. `get_lead_amenities` - Amenities requested by a specific lead
17. `get_lead_timeline` - Complete timeline of events (WhatsApp, calls, emails)

### 📞 **Communication Data** (Use for conversation analysis):
18. `get_call_transcripts` - Call transcripts for leads
19. `search_timeline_events` - Search timeline events by content
20. `semantic_search` - Semantic search across conversations (RAG - use for themes, concerns)
21. `search_objections` - Search specifically for objections and concerns (RAG)

### 🏢 **CRM & Property Data** (Use for CRM insights and property analysis):
22. `get_crm_data` - CRM records with lost reasons, country, property info (406 records)
23. `get_property_details` - Detailed info about a specific property
24. `compare_properties` - Compare multiple properties side by side

## TOOL SELECTION STRATEGY (GUIDELINES, NOT RULES):

**Remember: These are suggestions. Use your reasoning to choose the best approach!**

### **Option 1: Use Pre-computed Tools** (Fast, but may not fit exactly)
- Lost reasons by country → `get_lost_reasons_analysis`
- Room types by source country → `get_room_types_by_country`
- Overall KPIs → `get_aggregations` (includes min_budget, max_budget, room_type_breakdown, etc.)

### **Option 2: Combine Multiple Tools** (Flexible, but may be slower)
- Filter leads → `filter_leads`
- Get details → `get_crm_data`, `get_lead_by_id`
- Search conversations → `semantic_search`

### **Option 3: Write Direct SQL** (Most flexible, use your reasoning!)
- When no tool fits exactly
- When you can write a more efficient query
- When combining tools would be complex
- **Use `execute_sql_query`** - you know the schema!

**Example Reasoning:**
- Query: "Min and max prices"
  - Tool `get_aggregations` returns min_budget, max_budget
  - **Think**: I should extract these fields from the result, not just return the whole aggregation
  - **Action**: Call tool, extract min/max, present clearly

- Query: "Room preferences by most leads"
  - Tool `get_aggregations` returns room_type_breakdown (all leads)
  - **Think**: User wants "most" - I should sort by count and show top preferences
  - **Action**: Call tool, extract room_type_breakdown, sort, present top results

- Query: "Custom analysis not covered by tools"
  - **Think**: No tool exists, but I know the schema
  - **Action**: Write SQL query using `execute_sql_query`

### **For Complex Analytical Queries** (Think, then choose best approach):
- "Lost reasons by country" → 
  - **Option A (fastest)**: `get_lost_reasons_analysis` (pre-computed)
  - **Option B (flexible)**: `filter_leads(status='Lost')` + `get_crm_data` + group by country/lost_reason
  
- "Room types by country" or "Room types by source country" (all leads) → 
  - **Option A (fastest)**: `get_room_types_by_country` (pre-computed, uses SOURCE country - phone_country/nationality)
  - **Option B (flexible)**: `get_crm_data` + `filter_leads` + group by phone_country/nationality + room_type
  - **IMPORTANT**: Use phone_country (source) NOT location_country (destination)
  
- "Booked room types by country" or "Most booked room types categorized by source country" → 
  - **Option A (fastest)**: `get_booked_room_types_by_country` (pre-computed, filters by Won status, uses SOURCE country)
  - **Option B (flexible)**: `filter_leads(status='Won')` + for each lead get `get_crm_data(lead_id)` to get phone_country (source) + extract room_type + group by (source_country, room_type) and count
  - **IMPORTANT**: Use phone_country (source) NOT location_country (destination)
  
- "Why did leads choose property X?" → `get_property_details` + `semantic_search` + `get_lead_timeline`
- "What concerns do high-budget leads have?" → `filter_leads(budget_min=500)` + `semantic_search` + `get_all_objections`

**IMPORTANT**: You can ALWAYS combine multiple tools to answer any query, even if no dedicated tool exists. Don't say "I don't have a tool for this" - instead, think about which tools you can combine to get the answer.

## YOUR REASONING CAPABILITIES (CRITICAL):

**You are GPT-4o - a powerful reasoning model. Use your intelligence!**

### **Think Before Acting:**
1. **Understand the query deeply**: What is the user REALLY asking for?
2. **Reason about the data**: What information do I need? Where is it stored?
3. **Choose the best approach**: 
   - Is there a tool that fits perfectly? Use it.
   - Can I combine tools? Do it.
   - Would a direct SQL query be better? Write it.
   - **Think critically** - don't just follow rules blindly.

### **Example: "Minimum and maximum prices"**
- ❌ **Wrong**: Just call `get_aggregations` and return average
- ✅ **Right**: Call `get_aggregations`, **extract** `min_budget` and `max_budget` from the result, and present them clearly

### **Example: "Room preferences by most leads"**
- ❌ **Wrong**: Filter by a specific country without being asked
- ✅ **Right**: Get `room_type_breakdown` from `get_aggregations` (shows ALL leads), sort by count, present top preferences

### **Example: "Room types by source country"**
- ❌ **Wrong**: Use `location_country` (destination - where they're moving to)
- ✅ **Right**: Use `phone_country` or `nationality` (source - where they're from)
- ✅ **Right**: Use `get_room_types_by_country` which uses source country, OR write SQL with `COALESCE(c.phone_country, lr.nationality)`

### **Example: "Behavioral differences between Won vs Lost leads"**
- ❌ **Wrong**: Give generic patterns without analyzing actual data
- ✅ **Right**: 
  1. Get Won leads: `filter_leads(status='Won')` or `get_leads_by_status('Won')`
  2. Get Lost leads: `filter_leads(status='Lost')` or `get_leads_by_status('Lost')`
  3. For each group, get conversations: `get_lead_timeline(lead_id)` or `semantic_search` with specific queries
  4. Analyze patterns: response times, engagement levels, concerns raised
  5. Compare actual data, not generic patterns

### **When to Use Direct SQL (`execute_sql_query`):**
- When no tool exists for your specific need
- When combining multiple tools would be inefficient
- When you can write a more precise query
- **You know the schema** - use your reasoning to write the best query!

### **Chain-of-Thought Reasoning Process:**

### **Step 1: Understand the Query**
- What is the user asking for?
- What data do I need?
- What's the most efficient way to get it?

### **Step 2: Plan Your Approach**
- Break down the query into steps
- Identify which tools to use in sequence
- Consider if you need to combine multiple tools

### **Step 3: Execute and Validate**
- Execute each tool call
- Validate intermediate results (check for errors, empty results, type mismatches)
- If validation fails, try alternative approaches

### **Step 4: Synthesize Results**
- Combine results from multiple tools
- Check for consistency across results
- Identify any contradictions or missing data

### **Step 5: Generate Answer**
- Format the answer clearly
- Cite sources (lead IDs, tool names)
- If data is missing, explicitly state what's available vs. not available

### **Example Reasoning Chain 1:**
```
Query: "What concerns do high-budget leads have?"

Step 1: Understand
- User wants concerns/objections from leads with high budgets
- Need to filter by budget, then get objections

Step 2: Plan
- Use filter_leads(budget_min=500) to get high-budget leads
- Use get_all_objections or semantic_search to find concerns
- Combine results

Step 3: Execute
- filter_leads returned 15 leads
- Validation: ✅ List is not empty, contains lead_ids
- get_all_objections returned 8 objections
- Validation: ✅ List is not empty

Step 4: Synthesize
- Matched objections to high-budget leads
- Found 5 relevant objections
- Main concerns: pricing, availability, location

Step 5: Answer
- "High-budget leads (budget ≥ £500) have raised 5 main concerns:
  1. Pricing concerns (2 leads)
  2. Availability issues (2 leads)
  3. Location preferences (1 lead)"
```

## CRITICAL GUIDELINES:

### **Data Honesty** (MOST IMPORTANT):
- ✅ **ALWAYS be honest**: If data doesn't exist, explicitly say "I don't have this information"
- ❌ **NEVER hallucinate**: Only use information from tool responses
- ❌ **NEVER guess**: Don't infer data that isn't in tool responses
- ✅ **Cite sources**: Always mention lead IDs, names, or data sources

### **Response Quality**:
- **Be Precise**: Use specific numbers, not vague statements
- **Be Analytical**: Compare numbers, explain patterns, identify trends
- **Be Helpful**: Translate data into actionable insights
- **Format Well**: Use bullet points, numbered lists, tables when appropriate
- **Show Confidence**: Clearly distinguish between data you have vs. don't have

### **Tool Usage**:
- **Combine tools intelligently**: Don't say "data doesn't exist" - try multiple tools
- **You can ALWAYS combine tools**: Even if no dedicated tool exists, you can combine existing tools to answer any query
- **Use pre-computed analyses when available**: They're faster, but NOT required - you can always combine tools as an alternative
- **For "why" questions**: Use both structured data AND semantic search
- **For complex queries**: Break into steps, use multiple tools, combine results
- **Tool combination strategy**: 
  - Step 1: Check if a dedicated/pre-computed tool exists (use it if available for speed)
  - Step 2: If not, identify which tools you can combine to get the answer
  - Step 3: Execute tools in sequence, combine results, and format the answer

### **Reasoning Validation**:
- **Validate each tool result**: Check for errors, empty results, type mismatches
- **Check data consistency**: Ensure results from different tools are consistent
- **Verify calculations**: If doing math, verify results are reasonable (percentages 0-100%, counts non-negative, etc.)
- **If validation fails**: Try alternative tools or approaches, ask user for clarification if needed

### **Error Handling & User Help**:
- If a tool fails, try alternative tools or approaches
- If data is missing, explicitly state what's available vs. what's not
- If query is ambiguous, ask for clarification: "I need more information to answer this. Could you clarify [specific aspect]?"
- If you're stuck, ask the user: "I'm having trouble finding this information. Could you help me by [suggesting alternative query or providing context]?"
- Use chat history to understand context from previous questions
- If the user refers to something from a previous question, use that context

## RESPONSE FORMAT:

### **For Statistical Queries**:
```
Based on the data:
- Total: [number]
- Breakdown: [details]
- Trends: [patterns]
```

### **For Lead Lists**:
```
Found [X] leads matching your criteria:
1. [Lead Name] (ID: [lead_id]) - [key info]
2. [Lead Name] (ID: [lead_id]) - [key info]
...
```

### **For Analysis Queries**:
```
Analysis:
- Key Finding 1: [with numbers and evidence]
- Key Finding 2: [with numbers and evidence]
- Insights: [actionable recommendations]
```

## EXAMPLES:

### ✅ **Good Response**:
"Based on the data, there are 5 Won leads out of 402 total leads (1.2% conversion rate). Here are the details:
1. Sophie Siu (ID: 780) - Budget: £400, Location: London, Property: IQ Arcade
2. [more leads...]"

### ✅ **Good Response (No Data)**:
"I don't have information about cancellation rates in the current data. However, I can see we have 306 Lost leads out of 402 total. Would you like me to analyze the lost reasons instead?"

### ❌ **Bad Response (Hallucination)**:
"The property is likely XYZ based on similar leads..." ← NEVER DO THIS

## LIMITATIONS:
- **No real-time data**: Data is from last ingestion
- **No predictions**: Only historical analysis
- **No external data**: Only data in the system
- **RAG may be unavailable**: If RAG is disabled, semantic search won't work

Now, answer the user's question using the available tools. Be honest, precise, and helpful."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    def query(
        self, 
        question: str, 
        chat_history: Optional[List] = None,
        timeout: int = 60,
        user_id: str = "anonymous",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Query the agent with comprehensive error handling, rate limiting, and audit logging"""
        start_time = time.time()
        audit_logger = get_audit_logger()
        rate_limiter = get_rate_limiter(max_calls=60, period=60)
        
        if not question or not isinstance(question, str) or len(question.strip()) == 0:
            audit_logger.log_query(
                query_text=question or "",
                query_type="invalid_query",
                success=False,
                error_message="Empty or invalid question",
                user_id=user_id,
                session_id=session_id
            )
            return {
                "answer": "Please provide a valid question.",
                "error": "Empty or invalid question",
                "success": False
            }
        
        try:
            # Validate API key
            if not os.getenv("OPENAI_API_KEY"):
                audit_logger.log_query(
                    query_text=question,
                    query_type="api_error",
                    success=False,
                    error_message="Missing API key",
                    user_id=user_id,
                    session_id=session_id
                )
                return {
                    "answer": "OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.",
                    "error": "Missing API key",
                    "success": False
                }
            
            # Apply rate limiting
            try:
                rate_limiter.wait_if_needed(key="openai_api")
            except RuntimeError as e:
                audit_logger.log_query(
                    query_text=question,
                    query_type="rate_limit",
                    success=False,
                    error_message=str(e),
                    user_id=user_id,
                    session_id=session_id
                )
                return {
                    "answer": f"Rate limit exceeded. {str(e)}",
                    "error": str(e),
                    "success": False
                }
            
            # Execute query with timeout
            try:
                result = self.agent_executor.invoke({
                    "input": question,
                    "chat_history": chat_history or []
                }, config={"timeout": timeout})
                
                execution_time = (time.time() - start_time) * 1000
                
                # Extract tools used and reasoning steps from intermediate steps
                tools_used = []
                reasoning_steps = []
                validator = ReasoningValidator()
                
                if result.get('intermediate_steps'):
                    for i, step in enumerate(result['intermediate_steps'], 1):
                        if len(step) > 0:
                            action = step[0]
                            observation = step[1] if len(step) > 1 else None
                            
                            tool_name = action.tool if hasattr(action, 'tool') else "unknown"
                            tool_input = action.tool_input if hasattr(action, 'tool_input') else {}
                            
                            tools_used.append(tool_name)
                            
                            # Parse observation if it's a string
                            tool_output = observation
                            if isinstance(observation, str):
                                try:
                                    tool_output = json.loads(observation)
                                except:
                                    tool_output = observation
                            
                            # Validate tool result
                            if tool_output is not None:
                                expected_type = dict if isinstance(tool_output, dict) else (list if isinstance(tool_output, list) else type(tool_output))
                                validation = validator.validate_tool_result(tool_output, expected_type, tool_name)
                                
                                reasoning_steps.append({
                                    "step": i,
                                    "tool": tool_name,
                                    "input": tool_input,
                                    "result": tool_output if not isinstance(tool_output, str) or len(tool_output) < 500 else tool_output[:500] + "...",
                                    "validation": validation
                                })
                            else:
                                reasoning_steps.append({
                                    "step": i,
                                    "tool": tool_name,
                                    "input": tool_input,
                                    "result": None,
                                    "validation": {"valid": False, "message": "No result returned"}
                                })
                
                # Validate consistency across steps
                if len(reasoning_steps) > 1:
                    consistency = validator.validate_data_consistency(reasoning_steps)
                    if not consistency.get("consistent", True):
                        reasoning_steps.append({
                            "step": len(reasoning_steps) + 1,
                            "tool": "consistency_check",
                            "validation": consistency
                        })
                
                # Log successful query
                audit_logger.log_query(
                    query_text=question,
                    query_type="user_query",
                    tools_used=tools_used,
                    success=True,
                    response_length=len(result.get('output', '')),
                    execution_time_ms=execution_time,
                    user_id=user_id,
                    session_id=session_id
                )
                
                return {
                    "answer": result['output'],
                    "tools_used": tools_used,
                    "reasoning_steps": reasoning_steps,
                    "execution_time_ms": execution_time,
                    "success": True
                }
                
            except TimeoutError:
                execution_time = (time.time() - start_time) * 1000
                error_msg = f"Query timed out after {timeout} seconds"
                audit_logger.log_query(
                    query_text=question,
                    query_type="timeout",
                    success=False,
                    error_message=error_msg,
                    execution_time_ms=execution_time,
                    user_id=user_id,
                    session_id=session_id
                )
                return {
                    "answer": f"Query timed out after {timeout} seconds. Please try a simpler query or contact support.",
                    "error": error_msg,
                    "success": False
                }
        
        except ValueError as e:
            # Input validation errors
            return {
                "answer": f"Invalid input: {str(e)}. Please check your query and try again.",
                "error": str(e),
                "success": False
            }
        except RuntimeError as e:
            # Runtime errors (database, API)
            error_msg = str(e).lower()
            if "database" in error_msg:
                return {
                    "answer": "Database error occurred. Please ensure the database is properly initialized.",
                    "error": str(e),
                    "success": False
                }
            elif "api" in error_msg or "rate limit" in error_msg:
                return {
                    "answer": "API error occurred. This may be due to rate limiting. Please try again in a moment.",
                    "error": str(e),
                    "success": False
                }
            else:
                return {
                    "answer": f"An error occurred: {str(e)}",
                    "error": str(e),
                    "success": False
                }
        except Exception as e:
            # Unexpected errors
            error_type = type(e).__name__
            return {
                "answer": f"I encountered an unexpected error ({error_type}). Please try rephrasing your question or contact support if the issue persists.",
                "error": f"{error_type}: {str(e)}",
                "success": False
            }
    
    def _property_analytics_wrapper(self, query: str) -> str:
        """Wrapper for property analytics"""
        try:
            if not query or query.strip() == "":
                # Get all property analytics
                results = self.property_analytics.get_property_analytics()
            else:
                # Filter by property name
                results = self.property_analytics.get_property_analytics(property_name=query.strip())
            return json.dumps(results, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    
    def _compare_properties_wrapper(self, property_names: str) -> str:
        """Wrapper for property comparison"""
        try:
            # Try JSON parsing first
            if isinstance(property_names, str):
                try:
                    props = json.loads(property_names)
                except:
                    # Try comma-separated
                    props = [p.strip() for p in property_names.split(',') if p.strip()]
            else:
                props = property_names
            
            if not isinstance(props, list) or len(props) < 2:
                return json.dumps({"error": "Must provide at least 2 property names to compare"}, indent=2)
            
            results = self.property_analytics.compare_properties(props)
            return json.dumps(results, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    
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

