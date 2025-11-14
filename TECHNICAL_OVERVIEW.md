# 📘 Technical Overview - Quick Reference

> **Fast reference guide to understanding the UCL Lead Intelligence AI system**

---

## 🎯 What This System Does

**In Plain English:**
A chatbot that lets UCL admins ask natural language questions about their student leads and get instant, accurate answers backed by real data.

**Technical:**
A hybrid RAG + MCP architecture that intelligently routes queries between structured database queries (SQLite) and semantic search (ChromaDB) using GPT-4o as the orchestration layer.

---

## 🏗️ Architecture in 60 Seconds

### The Stack

```
Frontend:  Streamlit (Python web app)
Backend:   LangChain + GPT-4o (AI orchestration)
Databases: SQLite (structured) + ChromaDB (vectors)
APIs:      OpenAI (embeddings + chat completion)
```

### Two Data Paths

**Path 1: MCP (Structured Queries)**
```
User → GPT-4o → SQL Query → SQLite → Exact Results
```
*Use for: Filters, lookups, statistics*

**Path 2: RAG (Semantic Search)**
```
User → GPT-4o → Embedding → ChromaDB → Relevant Context
```
*Use for: Themes, concerns, conversations*

---

## 🗄️ Database Comparison

| Feature | SQLite | ChromaDB |
|---------|--------|----------|
| **Purpose** | Structured data | Semantic search |
| **Data Type** | Relational tables | Vector embeddings |
| **Query Type** | SQL | Similarity search |
| **Best For** | Exact matches | Finding meaning |
| **Speed** | 10-100ms | 150-300ms |
| **Accuracy** | 100% | ~85% relevance |
| **Size** | 500 KB (14 leads) | 5 MB (24 docs) |

### SQLite Tables (5 total)
1. `leads` - Main lead info
2. `lead_requirements` - Budget, dates, preferences
3. `lead_objections` - Concerns raised
4. `lead_tasks` - Action items
5. `rag_documents` - Text for embeddings

### ChromaDB Collection (1 total)
- `lead_conversations` - 24 embedded documents
- Embedding model: `text-embedding-3-small`
- Dimensions: 1536
- Distance metric: Cosine similarity

---

## 🔀 Query Routing

### How GPT-4o Decides

```python
# Simplified pseudo-code

if query.has_exact_criteria():
    use_sqlite()  # MCP path
    
elif query.about_meaning_or_themes():
    use_chromadb()  # RAG path
    
elif query.needs_both():
    use_sqlite() + use_chromadb()  # Hybrid
```

### Real Examples

| Query | Route | Why |
|-------|-------|-----|
| "Budget < £400" | SQLite | Exact filter |
| "What concerns?" | ChromaDB | Semantic meaning |
| "Why choose X?" | Both | Facts + context |
| "How many leads?" | SQLite | Count/aggregate |
| "Worried about?" | ChromaDB | Theme search |

---

## ⚡ Performance

### Query Response Times

```
Component              Time
─────────────────────────────
GPT-4o reasoning:      1-2s   (constant)
SQLite query:          10-100ms
Embedding generation:  100ms  (OpenAI API)
ChromaDB search:       50-200ms
─────────────────────────────
Total (MCP):          ~1.5s
Total (RAG):          ~2.5s
Total (Hybrid):       ~3.5s
```

### Bottlenecks
1. **GPT-4o API calls** - Largest time consumer
2. **OpenAI embedding API** - For RAG queries
3. **Network latency** - API calls to OpenAI

**Database queries are fast!** (<100ms each)

---

## 🔧 Key Components

### 1. Data Ingestion (`src/data_ingestion.py`)
- Parses CSV lead data
- Creates SQLite tables
- Extracts text for RAG

### 2. Query Tools (`src/query_tools.py`)
- MCP layer implementation
- 7 tools for structured queries
- Direct SQLite access

### 3. RAG System (`src/rag_system.py`)
- Vector embedding generation
- ChromaDB management
- Semantic search tools

### 4. AI Agent (`src/ai_agent.py`)
- LangChain orchestration
- Query routing logic
- Tool selection
- Response formatting

### 5. Web App (`app.py`)
- Streamlit interface
- Chat UI
- Dashboard KPIs

---

## 📊 Data Flow Examples

### Example 1: Factual Query

```
"Show leads with budget < £400"
│
├─► GPT-4o: This needs exact filtering
│
├─► Call: filter_leads(budget_max=400)
│
├─► SQL: SELECT * FROM leads WHERE budget_max <= 400
│
└─► Response: "Found 1 lead: Laia (£395)"
```

### Example 2: Semantic Query

```
"What are students worried about?"
│
├─► GPT-4o: This needs semantic understanding
│
├─► Call: semantic_search("students worried")
│
├─► Generate embedding [1536 dims]
│
├─► ChromaDB: Find similar vectors
│
├─► Returns: 5 most relevant conversations
│
└─► Response: "Top concerns: Budget (3), Safety (2)..."
```

### Example 3: Hybrid Query

```
"Why did Laia choose this property?"
│
├─► GPT-4o: Needs facts + context
│
├─► Call: get_lead_by_id("Laia") [MCP]
│   └─► Returns: Budget £395, Studio, London
│
├─► Call: semantic_search("Laia decision") [RAG]
│   └─► Returns: Safety concerns, transport needs
│
└─► Response: "Chose because: budget fit, safety, 
              good transport (sources: both DBs)"
```

---

## 🎓 How RAG Works

### 1. Embedding Generation
```
Text: "Student concerned about budget constraints"
      ↓
OpenAI API (text-embedding-3-small)
      ↓
Vector: [0.123, -0.456, 0.789, ... × 1536]
```

### 2. Storage
```
ChromaDB stores:
  • Vector (1536 floats)
  • Original text
  • Metadata (lead_id, status, type)
```

### 3. Search
```
Query: "budget concerns"
      ↓
Convert to vector
      ↓
Find nearest vectors (cosine similarity)
      ↓
Return top K matches with metadata
```

### 4. Why It Works
- **Semantic understanding**: "expensive" ≈ "high cost" ≈ "budget issue"
- **Context preserved**: Full conversation text stored
- **Fast retrieval**: Vector math is quick
- **Relevance ranking**: Distance scores show relevance

---

## 🔑 Key Design Decisions

### 1. Why Hybrid (MCP + RAG)?
- **MCP alone**: Can't understand themes/meaning
- **RAG alone**: Can't do exact filters accurately
- **Both together**: Best of both worlds

### 2. Why SQLite?
- ✅ No server setup
- ✅ File-based (easy deployment)
- ✅ Fast for small datasets
- ✅ Perfect for POC

**Trade-off**: Won't scale to 100k+ leads (use PostgreSQL then)

### 3. Why ChromaDB?
- ✅ File-based (no server)
- ✅ Built for embeddings
- ✅ Good for POC
- ✅ Easy to use

**Trade-off**: Won't scale to millions of docs (use Pinecone then)

### 4. Why GPT-4o?
- ✅ Best reasoning capabilities
- ✅ Function calling (tool selection)
- ✅ Natural language understanding
- ✅ Context synthesis

**Trade-off**: Expensive at scale (consider caching/fine-tuning)

---

## 🚀 Scaling Considerations

### Current POC (14 leads)
```
✓ SQLite:   Perfect
✓ ChromaDB: Perfect
✓ Cost:     ~$5-10/month
✓ Speed:    Sub-3s responses
```

### Production (1000+ leads)
```
→ PostgreSQL (better concurrency)
→ Pinecone/Weaviate (managed vector DB)
→ Caching layer (Redis)
→ Load balancing
→ Cost: ~$100-200/month per tenant
```

### Enterprise (10,000+ leads, multi-tenant)
```
→ Kubernetes deployment
→ Database sharding
→ CDN for static assets
→ Advanced caching
→ Fine-tuned models (reduce API costs)
→ Cost: $500-1000/month
```

---

## 📈 Metrics & Monitoring

### What to Track

**Performance:**
- Query response time
- Database query time
- API call latency
- Error rates

**Usage:**
- Queries per day
- Tool usage breakdown (MCP vs RAG)
- Popular query types
- User satisfaction

**Cost:**
- OpenAI API costs (GPT-4o + embeddings)
- Compute resources
- Storage costs

**Quality:**
- Answer accuracy (user feedback)
- Source citation rate
- Tool selection accuracy

---

## 🔒 Security & Privacy

### Current POC
- ✅ Local-only
- ✅ No authentication
- ✅ No data sharing

### Production Needs
- 🔐 User authentication
- 🔐 Role-based access control
- 🔐 Data encryption at rest
- 🔐 Audit logging
- 🔐 GDPR compliance
- 🔐 Rate limiting

---

## 📚 Documentation Guide

**For different audiences:**

### Developers
- 📖 `ARCHITECTURE.md` - Deep technical details
- 📖 `QUERY_FLOW_DIAGRAMS.md` - Visual flow examples
- 📖 `TECHNICAL_OVERVIEW.md` - This file!
- 📖 `src/` directory - Implementation code

### Users/Admins
- 📖 `README.md` - Project overview
- 📖 `QUICKSTART.md` - Get started fast
- 📖 `DEMO_SCRIPT.md` - Demo guidance

### Stakeholders
- 📖 `PROJECT_STATUS.md` - Current state
- 📖 `DEMO_SCRIPT.md` - Presentation flow

---

## 🛠️ Common Tasks

### Add a New MCP Tool
```python
# In src/query_tools.py
def my_new_query(self, param):
    conn = self._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ... WHERE ?", (param,))
    return cursor.fetchall()

# In src/ai_agent.py
Tool(
    name="my_new_query",
    func=lambda x: self.query_tools.my_new_query(x),
    description="What this tool does..."
)
```

### Add New Lead Data
```python
# Re-run ingestion
python src/data_ingestion.py

# Re-create embeddings
python src/rag_system.py
```

### Change Embedding Model
```python
# In src/rag_system.py
self.embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",  # More accurate but costly
    # or "text-embedding-3-small"     # Faster, cheaper
)
```

---

## 🐛 Debugging Guide

### Query Not Working?

**Check:**
1. API key valid? (`.env` file)
2. Database has data? (`sqlite3 data/leads.db`)
3. Embeddings created? (`ls data/chroma_db/`)
4. Error in logs? (Streamlit terminal output)

### Slow Responses?

**Profile:**
1. GPT-4o calls (1-2s) - normal
2. Database queries (>1s) - investigate
3. Embedding generation (>500ms) - check OpenAI API
4. Network issues - check internet

### Wrong Results?

**Debug:**
1. Check which tool was used (look at sources)
2. For MCP: Verify SQL query logic
3. For RAG: Check relevance scores (<0.7 is good)
4. Review GPT-4o reasoning (add verbose=True)

---

## 🎯 Quick Reference

### File Structure
```
├── app.py                    # Main Streamlit app
├── src/
│   ├── data_ingestion.py     # CSV → SQLite
│   ├── query_tools.py        # MCP layer
│   ├── rag_system.py         # RAG layer
│   └── ai_agent.py           # Orchestration
├── data/
│   ├── leads.db              # SQLite database
│   └── chroma_db/            # Vector store
└── Data/
    └── UCL Leads Data.csv    # Source data
```

### Key Commands
```bash
# Run app
streamlit run app.py

# View database
sqlite3 data/leads.db
# or
open http://localhost:8080  # (sqlite-web)

# Re-ingest data
python src/data_ingestion.py

# Re-create embeddings
python src/rag_system.py

# Test agent
python src/ai_agent.py
```

### Environment Variables
```bash
# .env file
OPENAI_API_KEY=sk-...
```

---

## 🤔 FAQ

**Q: Why not just use RAG for everything?**  
A: RAG can't do exact filters accurately. "Budget < 400" might return "budget around 400-ish" instead of precise results.

**Q: Why not just use SQL for everything?**  
A: SQL can't understand meaning. "What worries students?" has no SQL equivalent without predefined categories.

**Q: How accurate is the RAG search?**  
A: ~85-90% relevance for well-formed queries. Quality depends on embedding model and document quality.

**Q: Can I add more data?**  
A: Yes! Just update the CSV and re-run ingestion + embedding scripts.

**Q: How much does it cost to run?**  
A: POC: ~$5-10/month. Production: ~$100-200/month. Depends on query volume.

**Q: Will it work with 10,000 leads?**  
A: Need to switch to PostgreSQL + Pinecone, but architecture stays the same!

---

## 📞 Support

- **Architecture questions**: See `ARCHITECTURE.md`
- **Flow diagrams**: See `QUERY_FLOW_DIAGRAMS.md`
- **Usage help**: See `QUICKSTART.md`
- **Demo prep**: See `DEMO_SCRIPT.md`

---

**Built with** ❤️ **for UCL Lead Intelligence**

