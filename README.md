# 🎓 UCL Lead Intelligence AI

> Intelligent conversational AI assistant for university lead management

## 🎯 What This Does

Query lead data conversationally, get instant KPIs, understand student concerns, and analyze patterns from thousands of conversations.

**Key Features:**
- ✅ Natural language queries - "Show me leads moving in Jan 2026 with budget < £400"
- ✅ Instant KPIs - Total leads, won/lost breakdown, trends
- ✅ Conversation analysis - Semantic search across conversations
- ✅ Pattern analysis - Top queries, concerns, amenities
- ✅ Evidence-backed insights - Every answer includes source citations

## 🏗️ Architecture

**Hybrid System: SQL + RAG + Aggregation**

```
User Query → GPT-4o Agent → [SQL | RAG | Aggregation] → Response
                              ↓      ↓         ↓
                          SQLite  ChromaDB  Timeline
```

**Components:**
- **SQL Executor** - Structured database queries
- **RAG System** - Semantic search on conversations
- **Conversation Aggregator** - Text-based aggregation
- **Streamlit UI** - Chat interface with live dashboard

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Add OpenAI API key to .env
echo "OPENAI_API_KEY=your_key_here" > .env
```

### 2. Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

## 📊 Data

- **402 leads** with full conversation data
- **23,746 conversation events** in timeline
- **Status breakdown**: Won (88), Lost (306), Contacted (5), etc.

## 🎮 Example Queries

**Structured Queries:**
- "How many leads do we have?"
- "Give me leads by source country"
- "Show me Won leads"

**Conversation Analysis:**
- "What are the top queries from students?"
- "What top amenities are leads asking for?"
- "What are the most common concerns?"

**Advanced:**
- "Leads moving in January 2026 with budget < £400"
- "Why did leads choose specific properties?"

## 📁 Project Structure

```
├── app.py                    # Streamlit frontend
├── src/
│   ├── ai_agent_simple.py   # AI agent with 4 tools
│   ├── sql_executor.py      # SQL query execution
│   ├── rag_system.py        # Semantic search
│   ├── conversation_aggregator.py  # Text aggregation
│   └── init_databases.py    # Database initialization
├── Data/                     # Source data files
└── data/                     # Generated databases
```

## 🔧 Tech Stack

- **Frontend**: Streamlit
- **Backend**: LangChain + GPT-4o
- **Databases**: SQLite (structured) + ChromaDB (vectors)
- **APIs**: OpenAI (embeddings + chat)

## 📚 Documentation

- `QUICKSTART.md` - Getting started guide
- `ARCHITECTURE.md` - System architecture
- `TECHNICAL_OVERVIEW.md` - Technical reference
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
- `DATABASE_SCHEMA.md` - Database structure
- `DEMO.md` - Demo script and questions

## 🆘 Troubleshooting

**"Agent initialization failed"**
- Check `.env` file has valid `OPENAI_API_KEY`

**"Database table not found"**
- Databases are auto-created on first run
- Check Streamlit Cloud logs if deployed

**"No module named X"**
- Run: `pip install -r requirements.txt`

## 📝 License

Proprietary - Amber Intelligence POC
