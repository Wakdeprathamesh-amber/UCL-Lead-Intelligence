# 🏗️ Architecture Overview

> **System architecture and design**

## High-Level Architecture

```
User Query → GPT-4o Agent → [SQL Executor | RAG System | Conversation Aggregator] → Response
                                    ↓              ↓                    ↓
                               SQLite DB      ChromaDB          Timeline Events
```

## Core Components

1. **Streamlit App** (`app.py`) - Web interface
2. **AI Agent** (`src/ai_agent_simple.py`) - Query orchestration with GPT-4o
3. **SQL Executor** (`src/sql_executor.py`) - Structured database queries
4. **RAG System** (`src/rag_system.py`) - Semantic search on conversations
5. **Conversation Aggregator** (`src/conversation_aggregator.py`) - Text-based aggregation

## Data Storage

- **SQLite** (`data/leads.db`) - Structured lead data (402 leads)
- **ChromaDB** (`data/chroma_db/`) - Vector embeddings for semantic search (23,746 documents)

## Query Routing

- **SQL Queries** → Use `execute_sql_query` for structured data (counts, filters, aggregations)
- **Semantic Search** → Use `semantic_search` for themes, concerns, patterns
- **Conversation Analysis** → Use `aggregate_conversations` for "top/most" queries on conversations

## Tools Available

1. `execute_sql_query` - SQL SELECT queries
2. `semantic_search` - RAG-based semantic search
3. `aggregate_conversations` - Text aggregation (queries, concerns, amenities)
4. `get_lead_by_id` - Quick lead lookup

## Database Schema

See `DATABASE_SCHEMA.md` for complete schema details.
