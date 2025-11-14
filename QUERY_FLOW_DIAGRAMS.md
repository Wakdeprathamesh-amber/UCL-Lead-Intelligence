# 🔄 Query Flow Diagrams - Visual End-to-End Examples

> **Visual representations of how different types of queries flow through the system**

---

## 📊 Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  "Show me leads moving in Jan 2026 with budget < £400"     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                │ Query String
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     GPT-4o AI AGENT                                  │
│                   (Query Understanding)                              │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  1. Parse query intent                                       │  │
│  │  2. Identify required data:                                  │  │
│  │     • move_in_date = "2026-01"                               │  │
│  │     • budget_max = 400                                       │  │
│  │  3. Determine query type: FACTUAL FILTER                     │  │
│  │  4. Select tool: filter_leads                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                ┌───────────────┴─────────────┐
                │                             │
                │ Tool: filter_leads          │
                │ Params: {                   │
                │   move_in_month: "2026-01"  │
                │   budget_max: 400           │
                │ }                           │
                │                             │
                ▼                             │
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP LAYER                                    │
│                    (Query Tools Module)                              │
│                                                                      │
│  def filter_leads(move_in_month, budget_max):                       │
│      query = """                                                     │
│          SELECT l.*, r.*                                             │
│          FROM leads l                                                │
│          JOIN lead_requirements r ON l.lead_id = r.lead_id          │
│          WHERE r.move_in_date LIKE ?                                 │
│            AND r.budget_max <= ?                                     │
│      """                                                             │
│      return execute_query(query, ['2026-01%', 400])                 │
│                                                                      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                │ SQL Query
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          SQLite DB                                   │
│                      (data/leads.db)                                 │
│                                                                      │
│  ┌────────────────┐          ┌─────────────────────┐               │
│  │  leads table   │◄────────►│ lead_requirements   │               │
│  │  14 rows       │   JOIN   │      table          │               │
│  └────────────────┘          └─────────────────────┘               │
│                                                                      │
│  Query executes in ~50ms                                             │
│  Returns 1 matching row: Laia Vilatersana Alsina                    │
│                                                                      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                │ Result Set
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     GPT-4o AI AGENT                                  │
│                   (Response Formatting)                              │
│                                                                      │
│  Takes structured result and formats natural language response:     │
│                                                                      │
│  "There is one lead moving in January 2026 with budget less        │
│   than £400. Here are the details:                                 │
│                                                                      │
│   • Name: Laia Vilatersana Alsina                                   │
│   • Lead ID: #10245302799                                           │
│   • Budget: £395 (GBP)                                              │
│   • Move-in Date: January 3, 2026                                   │
│   • Location: London                                                │
│   • University: University College London                           │
│   • Status: Won                                                     │
│                                                                      │
│   Sources Used: filter_leads tool"                                  │
│                                                                      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                │ Formatted Response
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                      (Display Response)                              │
│                                                                      │
│  Shows response with:                                                │
│  • Natural language answer                                           │
│  • Structured data                                                   │
│  • Source citations                                                  │
│  • Tools used indicator                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

Total Time: ~2 seconds (1.5s GPT-4o, 0.5s query execution)
```

---

## 🔍 Semantic Query Flow (RAG)

```
USER: "What are students concerned about the most?"
│
├─► Step 1: Query enters AI Agent
│   └─► GPT-4o analyzes: "This needs semantic understanding"
│
├─► Step 2: Agent calls RAG tool
│   │
│   └─► semantic_search("students concerned worried")
│       │
│       ├─► Step 2a: Generate Query Embedding
│       │   │
│       │   │   OpenAI API Call
│       │   │   ┌──────────────────────────────────┐
│       │   └──►│ text-embedding-3-small           │
│       │       │ Input: "students concerned..."   │
│       │       │ Output: [0.123, -0.456, ... ]    │
│       │       │         (1536 dimensions)         │
│       │       └──────────────────────────────────┘
│       │               │
│       │               │ Vector: [float × 1536]
│       │               ▼
│       │
│       ├─► Step 2b: Vector Search in ChromaDB
│       │   │
│       │   │   ChromaDB Collection: "lead_conversations"
│       │   │   ┌────────────────────────────────────────┐
│       │   └──►│  Document 1: [0.145, -0.432, ...]     │
│       │       │  Document 2: [0.098, -0.521, ...]     │
│       │       │  Document 3: [-0.032, 0.412, ...]     │
│       │       │  ...                                   │
│       │       │  Document 24: [0.234, -0.123, ...]    │
│       │       └────────────────────────────────────────┘
│       │               │
│       │               │ Cosine Similarity Calculation
│       │               │
│       │       ┌───────▼────────────────────────────────┐
│       │       │  Rank by similarity:                   │
│       │       │  1. Doc #12 (distance: 0.574) ✓       │
│       │       │  2. Doc #8  (distance: 0.579) ✓       │
│       │       │  3. Doc #6  (distance: 0.593) ✓       │
│       │       │  4. Doc #3  (distance: 0.610) ✓       │
│       │       │  5. Doc #14 (distance: 0.625) ✓       │
│       │       └────────────────────────────────────────┘
│       │               │
│       │               │ Top 5 Results
│       │               ▼
│       │
│       └─► Step 2c: Return Retrieved Documents
│           │
│           └─► [
│                 {
│                   "lead_id": "#09066409352",
│                   "lead_name": "Mauricette Isasi",
│                   "content": "Student worried about budget...",
│                   "relevance": 0.426
│                 },
│                 ...
│               ]
│
├─► Step 3: Agent Analyzes Retrieved Documents
│   │
│   └─► GPT-4o reads 5 documents and identifies patterns:
│       │
│       ├─► Theme 1: Budget concerns (3 mentions)
│       ├─► Theme 2: Safety worries (2 mentions)
│       ├─► Theme 3: Availability issues (2 mentions)
│       └─► Theme 4: Location concerns (1 mention)
│
├─► Step 4: Agent Synthesizes Response
│   │
│   └─► Generates natural language answer with:
│       • Identified themes ranked by frequency
│       • Specific examples from conversations
│       • Lead names as evidence
│       • Source citations
│
└─► Step 5: Display to User
    │
    └─► "Based on conversations across multiple leads, students
         are most concerned about:
         
         1. Budget & Pricing (3 leads)
            • Affordability of accommodation
            • Payment plan flexibility
            Examples: Mauricette, Miles, Shawn
         
         2. Safety & Security (2 leads)
            • Neighborhood safety
            • Building security features
            Examples: Laia, Rianne
         
         Sources: Semantic search across 24 conversation documents"

Total Time: ~3 seconds (1s embedding, 0.2s search, 1.8s GPT-4o)
```

---

## 🔀 Decision Tree: Query Routing

```
                      USER QUERY
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │   GPT-4o Query Analysis             │
        │   "What is this query asking for?"  │
        └─────────────┬───────────────────────┘
                      │
         ─────────────┼─────────────
        │             │             │
        ▼             ▼             ▼
    
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   FACTUAL    │  │  SEMANTIC    │  │ AGGREGATION  │
│   CRITERIA   │  │   MEANING    │  │  STATISTICS  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       │                 │                  │
       ▼                 ▼                  ▼

 Has specific        Contains words      Asks for
 filters?            like "concerns",    counts, totals,
 (budget, date,      "worried",          averages,
  status, etc.)      "themes"            trends?
       │                 │                  │
       │ YES             │ YES              │ YES
       ▼                 ▼                  ▼

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   MCP TOOL   │  │   RAG TOOL   │  │   MCP TOOL   │
│ filter_leads │  │   semantic   │  │     get      │
│ get_lead_by  │  │    _search   │  │ aggregations │
│      _id     │  │              │  │              │
│ search_by    │  │   search     │  │              │
│    _name     │  │  _objections │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       ▼                 ▼                  ▼

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   SQLite     │  │  ChromaDB    │  │   SQLite     │
│   Direct     │  │   Vector     │  │     GROUP    │
│   Query      │  │   Search     │  │      BY      │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └─────────────────┴──────────────────┘
                         │
                         ▼
              ┌────────────────────┐
              │  Combine Results   │
              │  Format Response   │
              │  Add Citations     │
              └────────┬───────────┘
                       │
                       ▼
                   USER GETS
                   RESPONSE


EXAMPLES BY PATH:

MCP Path:
• "Show leads with budget < 400"
• "Get lead #10245302799"
• "Leads moving in Jan 2026"
• "List all Won leads"

RAG Path:
• "What concerns do students have?"
• "Find conversations about pricing"
• "What themes appear in Won leads?"
• "Show objections about safety"

Aggregation Path:
• "How many leads total?"
• "What's the average budget?"
• "Status breakdown?"
• "Count leads by university"

Hybrid Path (Uses Both):
• "Why did Laia choose this property?"
• "Compare Won vs Lost leads concerns"
• "What budget do worried students have?"
```

---

## 🎭 Parallel Tool Execution (Hybrid Queries)

```
USER: "Why did Laia choose this property and what were her concerns?"
│
└─► GPT-4o recognizes need for BOTH factual data + conversation context
    │
    ├─────────────────────────┬─────────────────────────┐
    │                         │                         │
    │ PARALLEL EXECUTION      │                         │
    │                         │                         │
    ▼                         ▼                         ▼
    
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Tool 1:        │    │  Tool 2:        │    │  Tool 3:        │
│  search_leads   │    │  get_lead_by_id │    │  semantic       │
│  _by_name       │    │                 │    │  _search        │
│  ("Laia")       │    │  (from Tool 1)  │    │  ("Laia         │
│                 │    │                 │    │   concerns")    │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         │ ~50ms                │ ~50ms                │ ~300ms
         │                      │                      │
         ▼                      ▼                      ▼
    
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Result:         │    │ Result:         │    │ Result:         │
│ Lead ID:        │    │ • Budget: £395  │    │ • Safety        │
│ #10245302799    │    │ • Room: Studio  │    │ • Transport     │
│ Status: Won     │    │ • Location: LDN │    │ • Study areas   │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │  AI Agent Combines   │
                    │  All Results         │
                    └──────────┬───────────┘
                               │
                               ▼
                        
    "Laia chose the Bronze Studio Premium because:
    
    FACTUAL MATCH (from MCP):
    • £395 budget fit exactly
    • Studio with private facilities
    • 12-week lease for Jan-Mar period
    
    DECISION FACTORS (from RAG):
    • Primary concern: Safety in neighborhood
    • Needed: Good transport to UCL
    • Wanted: Quiet study areas
    • Required: Nearby supermarkets
    
    The property addressed all her requirements and concerns.
    
    Sources: search_leads_by_name, get_lead_by_id, semantic_search"

Total Time: ~3.5 seconds (parallel execution saves time!)
```

---

## 📊 Database Selection Logic

```
                    QUERY ARRIVES
                         │
                         ▼
              ┌──────────────────────┐
              │  What data is needed?│
              └──────────┬───────────┘
                         │
        ─────────────────┼─────────────────
       │                 │                 │
       ▼                 ▼                 ▼

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  STRUCTURED  │  │   SEMANTIC   │  │     BOTH     │
│    DATA      │  │   MEANING    │  │   NEEDED     │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       │                 │                  │
       ▼                 ▼                  ▼

┌──────────────────────────────────────────────────┐
│         Use SQLite when:                         │
│  ✓ Exact values needed                           │
│  ✓ Filtering by fields                           │
│  ✓ Counting/aggregating                          │
│  ✓ Specific ID lookup                            │
│  ✓ 100% accuracy required                        │
│                                                  │
│  Examples:                                       │
│  • "Leads with budget < 400"                     │
│  • "Get lead #123"                               │
│  • "How many Won leads?"                         │
│  • "Average budget?"                             │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│         Use ChromaDB when:                       │
│  ✓ Understanding themes                          │
│  ✓ Finding similar content                       │
│  ✓ Searching conversations                       │
│  ✓ Exploring concerns                            │
│  ✓ Context matters                               │
│                                                  │
│  Examples:                                       │
│  • "What are students worried about?"            │
│  • "Find conversations about pricing"            │
│  • "Similar concerns to Laia's"                  │
│  • "Themes in Won leads"                         │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│         Use BOTH when:                           │
│  ✓ Complex questions                             │
│  ✓ Need facts + context                          │
│  ✓ "Why" questions                               │
│  ✓ Comparative analysis                          │
│  ✓ Deep insights needed                          │
│                                                  │
│  Examples:                                       │
│  • "Why did Laia choose this?"                   │
│  • "Compare Won vs Lost concerns"                │
│  • "Which high-budget leads worried about X?"    │
└──────────────────────────────────────────────────┘
```

---

## ⚡ Performance Comparison

```
QUERY: "Show me leads with budget < £400"
│
├─► MCP Route (SQLite)
│   │
│   ├─► Parse query → 0ms (GPT-4o)
│   ├─► Execute SQL → 50ms
│   ├─► Format result → 0ms (GPT-4o)
│   │
│   └─► Total: ~1.5 seconds (mostly GPT-4o overhead)
│       ✓ 100% accurate
│       ✓ Deterministic
│       ✓ Fast


QUERY: "What are students concerned about?"
│
├─► RAG Route (ChromaDB)
│   │
│   ├─► Parse query → 0ms (GPT-4o)
│   ├─► Generate embedding → 100ms (OpenAI API)
│   ├─► Vector search → 200ms (ChromaDB)
│   ├─► Analyze & synthesize → 0ms (GPT-4o)
│   │
│   └─► Total: ~2.5 seconds
│       ✓ Contextual understanding
│       ✓ Finds patterns
│       ✓ Semantic relevance


QUERY: "Why did Laia choose this property?"
│
├─► Hybrid Route (Both DBs)
│   │
│   ├─► Parse query → 0ms (GPT-4o)
│   ├─► MCP query → 50ms (SQLite)
│   ├─► RAG query → 300ms (Embedding + ChromaDB)
│   ├─► Combine & format → 0ms (GPT-4o)
│   │
│   └─► Total: ~3 seconds
│       ✓ Complete picture
│       ✓ Facts + context
│       ✓ Rich insights


NOTE: GPT-4o reasoning time (~1-2s) is constant across all queries
```

---

## 🔄 Real Query Examples with Actual Flow

### Example 1: "What is Laia's budget?"

```
User Input → "What is Laia's budget?"
     │
     ▼
GPT-4o Analysis:
  • Type: Factual lookup
  • Entity: Laia (person name)
  • Attribute: budget
  • Route: MCP
     │
     ▼
Tool Selection: search_leads_by_name + get_lead_by_id
     │
     ▼
SQLite Query 1:
  SELECT lead_id, name FROM leads WHERE name LIKE '%Laia%'
  → Returns: #10245302799
     │
     ▼
SQLite Query 2:
  SELECT budget_max, budget_currency 
  FROM lead_requirements 
  WHERE lead_id = '#10245302799'
  → Returns: 395, 'GBP'
     │
     ▼
GPT-4o Response:
  "Laia's budget is £395 (GBP) per week."

Time: ~1.5s | Accuracy: 100% | Source: SQLite
```

### Example 2: "Find conversations about safety"

```
User Input → "Find conversations about safety"
     │
     ▼
GPT-4o Analysis:
  • Type: Semantic search
  • Concept: "safety"
  • Route: RAG
     │
     ▼
Tool Selection: semantic_search
     │
     ▼
OpenAI Embedding:
  Input: "conversations about safety"
  → Vector: [0.234, -0.123, 0.456, ... × 1536]
     │
     ▼
ChromaDB Search:
  Query vector against 24 documents
  Cosine similarity ranking
  → Top 3 results:
     1. Laia's safety concerns (distance: 0.523)
     2. Mauricette's area questions (distance: 0.587)
     3. Rianne's neighborhood query (distance: 0.612)
     │
     ▼
GPT-4o Synthesis:
  "Found 3 conversations mentioning safety:
  
  1. Laia asked about neighborhood safety and 
     building security features
  2. Mauricette inquired about area safety at night
  3. Rianne questioned safety of surrounding area
  
  All three expressed concern about security measures."

Time: ~2.5s | Relevance: High | Source: ChromaDB
```

### Example 3: "Compare Won vs Lost leads"

```
User Input → "Compare Won vs Lost leads"
     │
     ▼
GPT-4o Analysis:
  • Type: Analytical comparison
  • Needs: Statistics + themes
  • Route: MCP + RAG (hybrid)
     │
     ▼
Parallel Execution:
     │
     ├─► MCP: get_leads_by_status("Won")
     │   └─► Returns: 5 leads with details
     │
     ├─► MCP: get_leads_by_status("Lost")
     │   └─► Returns: 3 leads with details
     │
     ├─► RAG: semantic_search("Won leads characteristics")
     │   └─► Returns: patterns in Won conversations
     │
     └─► RAG: semantic_search("Lost leads reasons")
         └─► Returns: themes in Lost conversations
     │
     ▼
Combine Results:
     │
     ├─► Factual (MCP):
     │   • Won: 5 leads, Avg budget: £368
     │   • Lost: 3 leads, Avg budget: £415
     │
     └─► Contextual (RAG):
         • Won: Matched requirements, budget fit
         • Lost: Budget too high, availability issues
     │
     ▼
GPT-4o Response:
  "Comparison of Won vs Lost leads:
  
  WON (5 leads):
  • Average budget: £368
  • Common factors: Budget alignment, quick response,
    clear requirements met
  
  LOST (3 leads):
  • Average budget: £415 (higher)
  • Common reasons: Budget exceeded, availability
    conflicts, slow decision-making
  
  Key insight: Won leads had better budget-to-
  requirement alignment."

Time: ~4s | Depth: Comprehensive | Source: Both DBs
```

---

## 📝 Summary: Query Routing Rules

```
┌────────────────────────────────────────────────────────────┐
│              QUERY ROUTING DECISION TABLE                   │
├────────────────────┬─────────────────┬─────────────────────┤
│  If Query Has...   │  Use...         │  Because...         │
├────────────────────┼─────────────────┼─────────────────────┤
│ Specific values    │ MCP → SQLite    │ Exact match needed  │
│ Filter criteria    │ MCP → SQLite    │ Fast & precise      │
│ Counts/aggregates  │ MCP → SQLite    │ GROUP BY queries    │
│ Lead ID/name       │ MCP → SQLite    │ Direct lookup       │
├────────────────────┼─────────────────┼─────────────────────┤
│ "Worried", "concern"│ RAG → ChromaDB  │ Semantic meaning    │
│ "Themes", "patterns"│ RAG → ChromaDB  │ Find similarities   │
│ "Conversations"    │ RAG → ChromaDB  │ Search text         │
│ "Similar to..."    │ RAG → ChromaDB  │ Vector similarity   │
├────────────────────┼─────────────────┼─────────────────────┤
│ "Why did..."       │ Both (Hybrid)   │ Facts + context     │
│ "Compare..."       │ Both (Hybrid)   │ Stats + insights    │
│ Complex analysis   │ Both (Hybrid)   │ Complete picture    │
└────────────────────┴─────────────────┴─────────────────────┘
```

---

**End of Query Flow Diagrams** ✓

For architecture details, see `ARCHITECTURE.md`
For usage examples, see `QUICKSTART.md`

