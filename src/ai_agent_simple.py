"""
Simplified AI Agent Module
Minimal tool architecture: 4 tools (SQL, RAG, Aggregation, Quick Lookup)
Trusts LLM reasoning for query generation
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool, StructuredTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage

from src.sql_executor import SQLExecutor
from src.rag_system import LeadRAGSystem
from src.database_schema import get_schema_prompt, get_sample_queries
from src.conversation_aggregator import aggregate_conversations

load_dotenv()


class AggregationInput(BaseModel):
    """Input schema for conversation aggregation tool"""
    aggregation_type: str = Field(
        description="Type of aggregation: 'queries', 'concerns', 'mentions', 'amenities', 'by_status'"
    )
    query_type: str = Field(
        default="all",
        description="Type of messages to analyze: 'whatsapp', 'call', 'email', 'all'"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="List of keywords to search for (required for 'mentions' type)"
    )
    limit: int = Field(
        default=5000,
        description="Maximum number of messages to analyze"
    )


class SimpleLeadIntelligenceAgent:
    """Simplified AI Agent with minimal tools - trusts LLM reasoning"""
    
    def __init__(self, db_path: str = "data/leads.db"):
        """
        Initialize simplified agent
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        
        # Initialize SQL executor
        self.sql_executor = SQLExecutor(db_path=db_path)
        
        # Initialize RAG system
        try:
            self.rag_system = LeadRAGSystem(db_path=db_path)
            self.rag_enabled = True
        except Exception as e:
            print(f"⚠️  RAG system not available: {str(e)}")
            self.rag_system = None
            self.rag_enabled = False
        
        # Initialize LLM
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=api_key
        )
        
        # Create tools (only 3!)
        self.tools = self._create_tools()
        
        # Create prompt
        self.prompt = self._create_prompt()
        
        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=False,
            max_iterations=15,
            max_execution_time=60,
            handle_parsing_errors=True
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create minimal tool set (3 tools only)"""
        
        tools = []
        
        # Tool 1: SQL Executor (for all structured queries)
        tools.append(
            Tool(
                name="execute_sql_query",
                func=lambda query, params=None: self._execute_sql_wrapper(query, params),
                description="""Execute a SQL SELECT query against the database.
                
                Use this for ANY structured data query:
                - Counts, aggregations, statistics
                - Filtering, grouping, sorting
                - Min/max/average calculations
                - Joins across tables
                - Any query that needs structured data
                
                Input: 
                - query (string): SQL SELECT query
                - params (optional): Parameters for parameterized queries
                
                Returns: Dict with 'columns', 'rows' (list of dicts), 'row_count', and 'error' (if any)
                
                You know the database schema - write SQL directly based on the schema provided in your context.
                You can write any SQL query as long as it's a SELECT statement.
                """
            )
        )
        
        # Tool 2: Semantic Search (for all conversation/semantic queries)
        if self.rag_enabled:
            tools.append(
                Tool(
                    name="semantic_search",
                    func=self._semantic_search_wrapper,
                    description="""Search conversations and lead data semantically using RAG.
                    
                    Use this for:
                    - Themes, concerns, patterns
                    - Conversation analysis
                    - Behavioral insights
                    - "What do leads say about X?"
                    - "What concerns do leads have?"
                    - Any semantic/meaning-based query
                    
                    Input: query (string) - Natural language query to search for
                    Optional: n_results (int) - Number of results (default: 5)
                    
                    Returns: List of relevant conversation excerpts with context
                    """
                )
            )
        
        # Tool 3: Conversation Aggregator (for text-based aggregation) - Using StructuredTool
        tools.append(
            StructuredTool.from_function(
                func=self._aggregate_conversations_structured,
                name="aggregate_conversations",
                description="""Aggregate and analyze conversations for patterns, counts, and rankings.
                
                Use this for TEXT-BASED aggregation queries where you need ACTUAL COUNTS across ALL data:
                - "Top queries from students"
                - "Most common concerns"
                - "Most frequently mentioned amenities"
                - "What topics do students ask about most"
                
                Returns: JSON with categories, counts, percentages, and examples
                
                This tool:
                ✅ Analyzes ALL relevant messages (not just 5 samples)
                ✅ Returns ACTUAL counts and percentages
                ✅ Categorizes by patterns (budget, move-in, room type, etc.)
                ✅ Provides examples for each category
                
                When to use:
                - "top/most/count" queries on conversation content
                - Need accurate statistics across ALL conversations
                - Want categorized results with examples
                """,
                args_schema=AggregationInput
            )
        )
        
        # Tool 4: Quick Lookup (convenience, optional)
        tools.append(
            Tool(
                name="get_lead_by_id",
                func=self._get_lead_wrapper,
                description="""Quick lookup for a specific lead by ID.
                
                Use this for convenience when you need basic lead info quickly.
                For detailed queries, use execute_sql_query instead.
                
                Input: lead_id (string)
                Returns: Dict with lead information
                """
            )
        )
        
        return tools
    
    def _execute_sql_wrapper(self, query: str, params: Optional[Any] = None) -> str:
        """Wrapper for SQL execution with smart output guardrail"""
        try:
            # LangChain may pass query as string or dict
            if isinstance(query, dict):
                sql_query = query.get('query', '') or query.get('input', '')
                params = query.get('params', params)
            else:
                sql_query = str(query)
            
            # Handle params
            if params:
                if isinstance(params, str):
                    try:
                        params = json.loads(params)
                        if isinstance(params, list):
                            params = tuple(params)
                    except:
                        params = (params,)
                elif isinstance(params, list):
                    params = tuple(params)
            
            result = self.sql_executor.execute(sql_query, params)
            
            # 🛡️ HARD GUARDRAIL: Prevent large outputs (safety net if LLM forgets)
            if result.get('row_count', 0) > 50:
                # Truncate to 10 rows with warning
                truncated_result = {
                    "columns": result.get('columns', []),
                    "rows": result.get('rows', [])[:10],
                    "row_count": result.get('row_count', 0),
                    "truncated": True,
                    "original_count": result.get('row_count', 0),
                    "warning": f"⚠️ LARGE OUTPUT DETECTED: Query returned {result.get('row_count', 0)} rows. "
                              f"Automatically limited to first 10 for practical display. "
                              f"Consider: (1) Adding WHERE filters, (2) Using aggregations (COUNT, AVG), "
                              f"or (3) Asking for analysis instead of raw data."
                }
                return json.dumps(truncated_result, indent=2, default=str)
            
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": f"Error executing SQL: {str(e)}"})
    
    def _semantic_search_wrapper(self, query: str, n_results: int = 5) -> str:
        """Wrapper for semantic search"""
        if not self.rag_enabled:
            return json.dumps({
                "error": "RAG system not available",
                "suggestion": "Try using execute_sql_query to search conversation data directly from the database. For example: SELECT l.lead_id, l.name, l.communication_timeline, l.crm_conversation_details FROM leads l WHERE l.communication_timeline LIKE '%keyword%'"
            })
        
        try:
            # Handle different input formats
            if isinstance(query, dict):
                search_query = query.get('query', '') or query.get('input', '')
                n_results = query.get('n_results', n_results)
            else:
                search_query = str(query)
            
            results = self.rag_system.semantic_search(search_query, n_results=n_results)
            
            # If no results, provide helpful message
            if not results or len(results) == 0:
                return json.dumps({
                    "message": "No results found in semantic search. The ChromaDB collection may be empty or still initializing.",
                    "suggestion": "Try using execute_sql_query to search conversation data directly. For example: SELECT l.lead_id, l.name, SUBSTR(l.communication_timeline, 1, 500) as conversation_preview FROM leads l WHERE l.communication_timeline IS NOT NULL AND l.communication_timeline != '' LIMIT 10",
                    "results": []
                })
            
            return json.dumps(results, indent=2, default=str)
        except Exception as e:
            error_msg = str(e)
            # Provide helpful error message with SQL fallback suggestion
            return json.dumps({
                "error": f"Error in semantic search: {error_msg}",
                "suggestion": "The RAG system may not be fully initialized. You can query conversation data directly using execute_sql_query. Example: SELECT l.lead_id, l.name, l.status, SUBSTR(l.communication_timeline, 1, 1000) as conversation FROM leads l WHERE l.communication_timeline IS NOT NULL"
            })
    
    def _aggregate_conversations_structured(
        self,
        aggregation_type: str,
        query_type: str = "all",
        keywords: Optional[List[str]] = None,
        limit: int = 5000
    ) -> str:
        """Structured wrapper for conversation aggregation (used with StructuredTool)"""
        try:
            # Call the aggregation function directly with properly typed parameters
            result = aggregate_conversations(
                aggregation_type=aggregation_type,
                query_type=query_type,
                keywords=keywords,
                limit=limit
            )
            
            return result
        except Exception as e:
            return json.dumps({"error": f"Error in conversation aggregation: {str(e)}"})
    
    def _get_lead_wrapper(self, lead_id: str) -> str:
        """Wrapper for quick lead lookup"""
        try:
            result = self.sql_executor.execute(
                "SELECT l.*, lr.* FROM leads l LEFT JOIN lead_requirements lr ON l.lead_id = lr.lead_id WHERE l.lead_id = ?",
                (lead_id,)
            )
            if result['rows']:
                return json.dumps(result['rows'][0], indent=2, default=str)
            else:
                return json.dumps({"error": f"Lead {lead_id} not found"})
        except Exception as e:
            return json.dumps({"error": f"Error getting lead: {str(e)}"})
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create enhanced prompt with schema"""
        
        schema = get_schema_prompt()
        sample_queries = get_sample_queries()
        
        system_message = f"""You are an AI assistant for UCL Lead Intelligence. You help analyze student leads data.

## YOUR TOOLS (4 tools):
1. **execute_sql_query** - Write SQL for structured data queries (counts, filtering, joins, etc.)
2. **semantic_search** - Search conversations for examples, themes, patterns (returns 5-10 samples)
3. **aggregate_conversations** - Analyze ALL conversations for patterns, counts, rankings (for "top/most" queries)
4. **get_lead_by_id** - Quick lead lookup (convenience)

## QUERY STRATEGY:

### ⚠️ AGGREGATION vs EXAMPLES (Critical Distinction):

**AGGREGATION Queries** (need ALL data + COUNTING):
- Keywords: "top", "most", "count", "all", "how many", "percentage", "rank", "distribution", "frequently"
- Examples: 
  * "Top queries from students" → Use aggregate_conversations(aggregation_type='queries')
  * "Most common concerns" → Use aggregate_conversations(aggregation_type='concerns')
  * "Most frequently mentioned amenities" → Use aggregate_conversations(aggregation_type='amenities')
  * "How many leads asked about X" → Use aggregate_conversations(aggregation_type='mentions', keywords=['X'])
- **Method**: aggregate_conversations → Analyzes ALL messages → Returns categories with ACTUAL counts
- **✅ USE aggregate_conversations for these!** - It's designed for this exact purpose

**EXAMPLE Queries** (need samples, not counts):
- Keywords: "what do", "show me", "give examples", "what are some", "find"
- Examples:
  * "What concerns do students have?" → Use semantic_search
  * "Show me budget questions" → Use semantic_search
  * "Give examples of WiFi questions" → Use semantic_search
- **Method**: semantic_search → Returns top 5-10 examples

**STRUCTURED Queries** (need database fields):
- Keywords: "how many leads", "status breakdown", "by country", "budget range"
- Examples:
  * "How many leads by status?" → Use execute_sql_query
  * "Room types by source country?" → Use execute_sql_query
  * "Average budget?" → Use execute_sql_query
- **Method**: execute_sql_query → Write SQL → Get exact results

### 🎯 When to Use aggregate_conversations:

**PERFECT FOR**:
- "Top queries from students" → {{{{"aggregation_type": "queries"}}}}
- "Most common concerns" → {{{{"aggregation_type": "concerns"}}}}
- "Most mentioned amenities" → {{{{"aggregation_type": "amenities"}}}}
- "Top topics in WhatsApp" → {{{{"aggregation_type": "queries", "query_type": "whatsapp"}}}}
- "How many asked about [X]" → {{{{"aggregation_type": "mentions", "keywords": ["X"]}}}}
- "Concerns by lead status" → {{{{"aggregation_type": "by_status"}}}}

**Returns**:
- Categories with ACTUAL counts (e.g., "Budget: 245 messages, 6.4%")
- Ranked by frequency
- Top 3 examples per category
- Summary statistics

### Basic Strategy:
- **Text aggregation** (top/most/count on conversations) → Use **aggregate_conversations** 
- **Structured queries** (counts, stats, filters on DB fields) → Use **execute_sql_query**
- **Examples/samples** (themes, patterns, specific cases) → Use **semantic_search**
- **Combined queries** → Use multiple tools

## CRITICAL RULES:

### 1. Data Honesty (MOST IMPORTANT):
- ✅ ONLY use information from tool responses
- ✅ If data doesn't exist, explicitly say "I don't have this information" or "No data found"
- ❌ NEVER hallucinate or make up data
- ❌ NEVER give generic/standard responses without actual data
- ❌ NEVER say "typically" or "usually" - use ACTUAL data only
- ❌ NEVER refuse to execute a query - ALWAYS try to use tools (SQL, RAG, aggregation)
- ❌ NEVER say "I am unable to execute" - Instead, write SQL and execute it!

### 2. Use Actual Conversation Data:
- When asked about behaviors, concerns, patterns → ALWAYS use semantic_search first
- Read actual WhatsApp messages, call transcripts, emails
- Cite specific examples from conversations
- If no conversation data found, say so explicitly

### 3. Geographic Data:
- phone_country = SOURCE country (where from) - Use for "by source country"
- location_country = DESTINATION (where moving to) - NOT for source queries
- You know the schema - write SQL directly

### 3.5. Date-Based Queries:
- **"booking count in 2025"** = Count Won leads created in 2025
  - Use: `SELECT COUNT(*) FROM leads WHERE status='Won' AND created_at LIKE '2025%'`
- **"leads in 2025"** = Filter by created_at date
  - Use: `WHERE created_at LIKE '2025%'` or `WHERE strftime('%Y', created_at) = '2025'`
- **"move-in in 2025"** = Filter by move_in_date
  - Use: `JOIN lead_requirements ON leads.lead_id = lead_requirements.lead_id WHERE move_in_date LIKE '2025%'`
- **"room types by month"** = Group by month from created_at
  - Use: `SELECT strftime('%Y-%m', created_at) as month, room_type, COUNT(*) FROM leads l JOIN lead_requirements lr ON l.lead_id = lr.lead_id GROUP BY month, room_type`
- **"room types by month and source country"** = Multi-dimensional grouping
  - Use: `SELECT strftime('%Y-%m', l.created_at) as month, COALESCE(c.phone_country, lr.nationality) as source_country, lr.room_type, COUNT(*) FROM leads l JOIN lead_requirements lr ON l.lead_id = lr.lead_id LEFT JOIN crm_data c ON l.lead_id = c.lead_id GROUP BY month, source_country, room_type`
- **"booking"** = Won status (successful conversion)
- **Date fields available**:
  - `leads.created_at` - When lead record was created (TIMESTAMP, use strftime for grouping)
  - `lead_requirements.move_in_date` - When lead plans to move in (TEXT, format: YYYY-MM-DD)
  - `crm_data.created_at` - CRM creation date
- **Month extraction**: Use `strftime('%Y-%m', created_at)` to get 'YYYY-MM' format for grouping
- **Always write SQL directly** - Don't refuse queries, execute them! The SQL executor allows created_at column.

### 4. ⚠️ LARGE OUTPUT GUARDRAIL (Critical for UX):

**Problem**: "Show all X" queries with large datasets don't serve a useful purpose.
Nobody can read 300 lead profiles. They need insights, not raw dumps.

**Your Response When Output Would Be >20 Rows**:

**Step 1**: Recognize this is a "show all" query
- Keywords: "show all", "list all", "display all", "get all"
- Example: "Show all Lost leads" (306 results)

**Step 2**: Modify your SQL to limit to 10 samples + get summary stats
```sql
-- Get sample
SELECT * FROM leads WHERE status='Lost' LIMIT 10;

-- Get summary stats
SELECT 
    COUNT(*) as total,
    AVG(budget_max) as avg_budget,
    COUNT(DISTINCT phone_country) as num_countries
FROM leads WHERE status='Lost';

-- Get top categories
SELECT phone_country, COUNT(*) as count 
FROM leads WHERE status='Lost' 
GROUP BY phone_country 
ORDER BY count DESC LIMIT 5;
```

**Step 3**: Format response with:
✅ Sample (10 results)
📊 Summary stats (total, averages, distributions)
💡 Suggestions for better queries
⚠️ Explain why you limited output

**Response Template**:
```
✅ Found [total] [entity_type]. Here's a sample of 10:

1. [First result]
2. [Second result]
...
10. [Tenth result]

📊 Summary of all [total]:
   - [Key statistic 1]
   - [Key statistic 2]
   - [Key distribution]

💡 For better insights, try:
   - "[Suggestion 1]" (filtered view)
   - "[Suggestion 2]" (analysis)
   - "[Suggestion 3]" (comparison)

⚠️ Showing 10 of [total]. Full list would be too long for practical use.
   Ask for specific filters or analysis instead!
```

**DO LIMIT** (Apply guardrail):
✅ "Show all Won/Lost leads" (88/306 results)
✅ "List all properties" (244 results)
✅ "Display all tasks" (2,271 results)
✅ Any query returning >20 detailed rows

**DO NOT LIMIT** (Return all data):
❌ Aggregations: "How many leads by status?" → Return all status counts
❌ Filtered queries: "Won leads from India" → Return all 15 (small set)
❌ Single lookups: "Lead ID 123" → Return complete profile
❌ Summary statistics: Already summarized, not raw data

**Key Principle**: 
- For ANALYSIS → Analyze ALL data, return summary
- For DISPLAY → Show small sample + guide to better queries

## DATABASE SCHEMA:

{schema}

## EXAMPLES:

{sample_queries}

### ⚠️ CRITICAL EXAMPLE: Text-Based Aggregation

**Query**: "What are the top queries from students?"

**WRONG Approach** ❌:
```
Use semantic_search("student queries")
→ Returns 5 message samples
→ Answer: "I don't have data" or "Students typically ask about budget, move-in..."
→ Problem: Based on 5 samples, not ALL data, no actual counts
```

**CORRECT Approach (Phase 2)** ✅:
```
Use aggregate_conversations tool:
Input: {{{{"aggregation_type": "queries", "query_type": "all", "limit": 5000}}}}

Returns:
{{{{
  "total_analyzed": 5000,
  "categories": [
    {{{{
      "category": "Budget",
      "count": 245,
      "percentage": 4.9,
      "examples": ["What's the budget?", "How much is it?", "Is it expensive?"]
    }}}},
    {{{{
      "category": "Move In",
      "count": 189,
      "percentage": 3.8,
      "examples": ["When can I move in?", "What's the earliest date?"]
    }}}},
    ...
  ]
}}}}

Your Answer:
"Based on analysis of 5,000 student messages, here are the top queries:

1. **Budget/Pricing** - 245 messages (4.9%)
   Students frequently ask about pricing, budgets, and costs
   Examples: 'What's the budget?', 'How much is it?'

2. **Move-in Date** - 189 messages (3.8%)
   Questions about when they can move in or start their tenancy
   Examples: 'When can I move in?', 'What's the earliest date?'
..."
```

**Why This Works**:
- ✅ Analyzes ALL data (5000 messages, not just 5)
- ✅ Returns ACTUAL counts and percentages
- ✅ Categorizes automatically using patterns
- ✅ Provides examples for each category
- ✅ Simple, reliable, accurate

### Query Pattern Recognition:

**Use aggregate_conversations for**:
- "top queries from students" → {{{{"aggregation_type": "queries"}}}}
- "most common questions" → {{{{"aggregation_type": "queries"}}}}
- "what do students ask about most" → {{{{"aggregation_type": "queries"}}}}
- "most frequently mentioned amenities" → {{{{"aggregation_type": "amenities"}}}}
- "common concerns" → {{{{"aggregation_type": "concerns"}}}}
- "top topics in WhatsApp" → {{{{"aggregation_type": "queries", "query_type": "whatsapp"}}}}
- "how many students asked about [X]" → {{{{"aggregation_type": "mentions", "keywords": ["X"]}}}}

**Key Lesson**: For "top/most/count" queries on conversations → Use aggregate_conversations tool directly!

## Response Format:
- Base answers ONLY on tool output
- If tool returns no data → Say "No data found"
- If tool returns data → Use it, cite it, don't embellish
- For behavioral questions → Show actual conversation examples

Always answer the user's question directly. Use tools when needed. Be honest about data availability.
"""
        
        # Simplified prompt template
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
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a query using the simplified agent
        
        Args:
            question: User's question
            chat_history: Optional chat history (List of HumanMessage/AIMessage)
            user_id: Optional user ID for logging
            session_id: Optional session ID for logging
            
        Returns:
            Dict with 'answer', 'success', 'error' (if any)
        """
        try:
            # Validate input
            if not question or not isinstance(question, str):
                return {
                    "answer": "",
                    "success": False,
                    "error": "Invalid question: must be a non-empty string"
                }
            
            # Convert chat history to LangChain format
            langchain_history = []
            if chat_history:
                for msg in chat_history:
                    if isinstance(msg, (HumanMessage, AIMessage)):
                        langchain_history.append(msg)
                    elif isinstance(msg, dict):
                        if msg.get("role") == "user":
                            langchain_history.append(HumanMessage(content=msg.get("content", "")))
                        elif msg.get("role") == "assistant":
                            langchain_history.append(AIMessage(content=msg.get("content", "")))
            
            # Execute query
            result = self.agent_executor.invoke({
                "input": question,
                "chat_history": langchain_history
            })
            
            return {
                "answer": result.get('output', ''),
                "success": True,
                "error": None
            }
            
        except Exception as e:
            error_msg = str(e)
            return {
                "answer": f"I encountered an error: {error_msg}",
                "success": False,
                "error": error_msg
            }

