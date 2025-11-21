# 🏗️ Complete Architecture Rebuild Plan

## 🎯 End Goal

**A simple, maintainable, flexible chatbot that:**
- Handles any query without needing new tools
- Uses LLM reasoning for SQL generation
- Uses RAG for semantic/conversation queries
- Maintains accuracy and performance
- Easy to maintain and extend

---

## 📋 Phase 1: Research & Planning (Current)

### ✅ Completed:
- Industry research on text-to-SQL architectures
- Analysis of current complexity (25+ tools, 2,400+ lines)
- Identification of tool proliferation problem
- Research on latest best practices

### 🔍 Latest Research Findings:

1. **LangChain SQL Agent Pattern** (2024)
   - Uses `create_sql_agent` with schema
   - Handles complex multi-step queries
   - Self-correcting SQL generation
   - Best practice: Provide schema + few examples

2. **RAG + SQL Hybrid** (2024)
   - SQL for structured data
   - RAG for unstructured/semantic data
   - LLM decides which to use
   - Pattern: Minimal tools, maximum reasoning

3. **Schema Injection Best Practices** (2024)
   - Include table names, columns, types
   - Include relationships (FKs)
   - Include sample data (1-2 rows per table)
   - Include common query patterns as examples

4. **Tool Reduction Strategy** (2024)
   - 1-3 tools maximum
   - LLM writes SQL for structured queries
   - RAG handles semantic queries
   - No pre-computed aggregations needed

---

## 📋 Phase 2: Architecture Design

### **New Simplified Architecture**

```
┌─────────────────────────────────────────┐
│         User Query (Natural Language)   │
└──────────────────┬──────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      Simplified AI Agent (GPT-4o)       │
│                                          │
│  Context Provided:                      │
│  - Complete database schema             │
│  - Sample data examples                 │
│  - Query pattern examples               │
│  - RAG system access                    │
│                                          │
│  Tools Available (3 only):              │
│  1. execute_sql_query                   │
│  2. semantic_search                     │
│  3. get_lead_by_id (convenience)        │
│                                          │
│  LLM Decision:                          │
│  - Structured query? → Write SQL         │
│  - Semantic query? → Use RAG            │
│  - Combined? → Use both                 │
└──────┬──────────────────────┬───────────┘
       │                      │
       │ SQL                  │ RAG
       │                      │
       ▼                      ▼
┌──────────────┐      ┌──────────────┐
│ SQLite DB    │      │ ChromaDB     │
│ (Structured) │      │ (Vectors)    │
└──────────────┘      └──────────────┘
```

### **Core Principles:**

1. **Trust LLM Reasoning**: LLM can write SQL, don't pre-compute
2. **Minimal Tools**: 3 tools maximum
3. **Schema-Driven**: Provide complete schema, let LLM reason
4. **RAG for Semantics**: Use RAG for conversations/themes
5. **Self-Correcting**: LLM can fix SQL errors

---

## 📋 Phase 3: Implementation Plan

### **Step 1: Create New Simplified Agent**
- File: `src/ai_agent_simple.py`
- 3 tools only
- Enhanced prompt with schema
- Clean, maintainable code

### **Step 2: Schema Documentation**
- File: `src/database_schema.py`
- Complete schema with relationships
- Sample data examples
- Query pattern examples

### **Step 3: Enhanced Prompt Template**
- Schema injection
- Query strategy guide
- Examples of good queries
- Error handling instructions

### **Step 4: Testing Framework**
- Test all existing queries
- Verify accuracy
- Measure performance
- Compare with old system

### **Step 5: Migration**
- Replace old agent
- Update app.py
- Remove unused tools
- Clean up code

---

## 📋 Phase 4: File Structure

### **New Structure:**
```
src/
├── ai_agent_simple.py      # New simplified agent (3 tools)
├── database_schema.py       # Schema documentation
├── sql_executor.py          # SQL execution with safety
├── rag_system.py            # Keep existing (works well)
├── init_databases.py        # Keep (needed for setup)
└── utils/
    ├── error_handling.py    # Keep (useful)
    └── connection_pool.py   # Keep (performance)

# Files to Archive/Remove:
├── query_tools.py           # Remove (replaced by SQL)
├── ai_agent.py              # Remove (replaced by simple)
├── property_analytics.py    # Remove (LLM can write SQL)
└── [other tool files]       # Remove
```

---

## 📋 Phase 5: Implementation Details

### **Tool 1: execute_sql_query**

**Purpose**: All structured queries

**Implementation**:
```python
def execute_sql_query(query: str, params: Optional[tuple] = None) -> Dict:
    """
    Execute SQL SELECT query safely.
    - Only SELECT allowed
    - Parameterized queries supported
    - Returns structured results
    """
    # Safety checks
    # Execute query
    # Return results
```

**LLM Usage**:
- LLM writes SQL based on schema
- LLM can fix errors if query fails
- LLM combines multiple queries if needed

### **Tool 2: semantic_search**

**Purpose**: All conversation/semantic queries

**Implementation**:
```python
def semantic_search(query: str, n_results: int = 5) -> List[Dict]:
    """
    Search conversations semantically.
    - Uses existing RAG system
    - Returns relevant context
    """
    # Use existing rag_system
```

**LLM Usage**:
- LLM uses for themes, concerns, patterns
- LLM can combine with SQL results
- LLM synthesizes final answer

### **Tool 3: get_lead_by_id** (Optional Convenience)

**Purpose**: Quick lookup

**Implementation**:
```python
def get_lead_by_id(lead_id: str) -> Dict:
    """
    Quick lookup for specific lead.
    Convenience tool, not essential.
    """
```

---

## 📋 Phase 6: Prompt Engineering

### **Schema Injection Format:**

```python
schema_prompt = """
## Database Schema:

### Table: leads
- lead_id (TEXT, PK): Unique lead identifier
- name (TEXT): Lead's full name
- status (TEXT): 'Won', 'Lost', 'Opportunity', 'Contacted', 'Disputed'
- mobile_number (TEXT): Phone number
- structured_data (TEXT): JSON with conversation summary
- communication_timeline (TEXT): JSON with timeline events

### Table: lead_requirements
- lead_id (TEXT, FK → leads.lead_id): Links to leads
- nationality (TEXT): Source country (where lead is from)
- location (TEXT): Destination (where moving to)
- budget_max (REAL): Maximum budget
- budget_currency (TEXT): 'GBP', 'USD', etc.
- room_type (TEXT): 'ensuite', 'studio', etc.
- move_in_date (TEXT): Move-in date
- university (TEXT): University name

### Table: crm_data
- lead_id (TEXT, FK → leads.lead_id): Links to leads
- phone_country (TEXT): SOURCE country (where from) - Use this for "by source country"
- location_country (TEXT): DESTINATION country (where moving to) - NOT for source queries
- lost_reason (TEXT): Reason if status = 'Lost'
- property_name (TEXT): Property name

### Table: timeline_events
- lead_id (TEXT, FK → leads.lead_id): Links to leads
- event_type (TEXT): 'whatsapp', 'call', 'email'
- content (TEXT): Event content
- timestamp (TEXT): Event time

### Relationships:
- leads.lead_id → lead_requirements.lead_id (1:1)
- leads.lead_id → crm_data.lead_id (1:many, typically 1:1)
- leads.lead_id → timeline_events.lead_id (1:many)

### Sample Data:
leads: {lead_id: "123", name: "John Doe", status: "Won"}
lead_requirements: {lead_id: "123", budget_max: 400, room_type: "ensuite"}
crm_data: {lead_id: "123", phone_country: "GB", location_country: "United Kingdom"}

### Common Query Patterns:
- "Room types by source country": 
  SELECT COALESCE(c.phone_country, lr.nationality) as source_country, lr.room_type, COUNT(*) 
  FROM leads l JOIN lead_requirements lr ON l.lead_id = lr.lead_id 
  LEFT JOIN crm_data c ON l.lead_id = c.lead_id 
  GROUP BY source_country, lr.room_type

- "Min/Max budget":
  SELECT MIN(budget_max) as min_budget, MAX(budget_max) as max_budget 
  FROM lead_requirements WHERE budget_max IS NOT NULL
"""
```

### **Query Strategy Guide:**

```python
strategy_prompt = """
## Query Strategy:

### Use execute_sql_query for:
- Counts, aggregations, statistics
- Filtering, grouping, sorting
- Min/max/average calculations
- Joins across tables
- Any structured data query

### Use semantic_search for:
- Themes, concerns, patterns
- Conversation analysis
- Behavioral insights
- "What do leads say about X?"
- Any semantic/meaning-based query

### Combine both for:
- "Behavioral differences Won vs Lost" → SQL for status + RAG for conversations
- "High-budget lead concerns" → SQL for filtering + RAG for concerns
- Complex analytical queries

## Important Notes:
- phone_country = SOURCE country (where from)
- location_country = DESTINATION country (where moving to)
- When user asks "by source country", use phone_country/nationality
- You can write SQL for any structured query
- Trust your reasoning - you can handle any query
"""
```

---

## 📋 Phase 7: Testing Strategy

### **Test Queries:**

1. **Simple Structured:**
   - "How many total leads?"
   - "What's the average budget?"
   - "Show me all Won leads"

2. **Complex Structured:**
   - "Room types by source country"
   - "Min and max prices"
   - "Budget by source country"

3. **Semantic:**
   - "What concerns do leads have?"
   - "Behavioral differences Won vs Lost"
   - "Communication preferences"

4. **Combined:**
   - "High-budget lead concerns"
   - "Lost reasons by country"
   - "Property preferences by source country"

### **Success Criteria:**
- ✅ All queries work without new tools
- ✅ SQL is generated correctly
- ✅ Results are accurate
- ✅ Response time < 5 seconds
- ✅ No tool proliferation

---

## 📋 Phase 8: Migration Steps

1. **Create new files** (don't delete old yet)
2. **Test new system** alongside old
3. **Compare results** for accuracy
4. **Update app.py** to use new agent
5. **Archive old files** (keep for reference)
6. **Update documentation**
7. **Deploy and monitor**

---

## 🎯 Success Metrics

- **Code Reduction**: 2,400 lines → ~500 lines
- **Tool Reduction**: 25+ tools → 3 tools
- **Query Coverage**: 100% (any query works)
- **Maintenance**: Low (simple codebase)
- **Performance**: Same or better
- **Accuracy**: Same or better

---

## 📅 Timeline Estimate

- **Phase 1**: Research (✅ Done)
- **Phase 2**: Design (✅ Done)
- **Phase 3**: Implementation (2-3 hours)
- **Phase 4**: Testing (1 hour)
- **Phase 5**: Migration (30 min)
- **Total**: ~4 hours

---

## 🚀 Ready to Build!

Let's start building the simplified architecture now.

