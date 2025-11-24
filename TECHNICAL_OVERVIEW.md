# 📘 Technical Overview

> **Quick technical reference**

## Stack

- **Frontend**: Streamlit (Python web app)
- **Backend**: LangChain + GPT-4o (AI orchestration)
- **Databases**: SQLite (structured) + ChromaDB (vectors)
- **APIs**: OpenAI (embeddings + chat completion)

## Query Paths

**Structured Queries (SQL)**
```
User → GPT-4o → SQL Query → SQLite → Results
```
*Use for: Filters, lookups, statistics*

**Semantic Search (RAG)**
```
User → GPT-4o → Embedding → ChromaDB → Relevant Context
```
*Use for: Themes, concerns, conversations*

## Database Comparison

| Feature | SQLite | ChromaDB |
|---------|--------|----------|
| Purpose | Structured data | Semantic search |
| Query Type | SQL | Similarity search |
| Speed | 10-100ms | 150-300ms |
| Data | 402 leads | 23,746 documents |

## Key Components

- `app.py` - Streamlit web interface
- `src/ai_agent_simple.py` - AI agent with 4 tools
- `src/sql_executor.py` - SQL query execution
- `src/rag_system.py` - Vector embeddings and semantic search
- `src/conversation_aggregator.py` - Text-based aggregation
- `src/init_databases.py` - Database initialization

## Performance

- SQL queries: 10-100ms
- RAG search: 150-300ms
- GPT-4o reasoning: 1-2s
- **Total response time**: ~1.5-3s

## Environment Variables

```bash
OPENAI_API_KEY=your_key_here
```

## Quick Commands

```bash
# Run app
streamlit run app.py

# View database
sqlite3 data/leads.db

# Initialize databases
python -c "from src.init_databases import ensure_databases_exist; ensure_databases_exist()"
```
