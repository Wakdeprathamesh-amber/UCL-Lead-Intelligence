# 🎓 UCL Lead Intelligence AI - POC

> Whitelabel AI Intelligence Layer for University Lead Management

An intelligent conversational AI assistant that helps university admins (like UCL) understand their student leads, analyze trends, and extract insights from thousands of conversations.

## 🎯 What This Does

This POC demonstrates a **Whitelabel AI Insight Layer** that allows university partners to:

- ✅ **Query lead data conversationally** - "Show me leads moving in Jan 2026 with budget < £400"
- ✅ **Get instant KPIs** - Total leads, won/lost breakdown, trends by month
- ✅ **Understand student concerns** - Semantic search across conversations and objections
- ✅ **Analyze patterns** - Why bookings dropped, what objections are common, etc.
- ✅ **Access structured data** - Filter by status, budget, location, move-in dates
- ✅ **Evidence-backed insights** - Every answer includes source citations

## 🏗️ Architecture

**Hybrid System: MCP + RAG + Aggregation Engine**

```
┌─────────────────────────────────────────────────┐
│          Streamlit Chat Interface                │
│         (User Query Input + Dashboard)           │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│         LangChain AI Agent (GPT-4)              │
│     (Query Router + Tool Orchestration)          │
└──────────┬───────────────────┬──────────────────┘
           │                   │
      ┌────▼────┐         ┌────▼─────┐
      │   MCP   │         │   RAG    │
      │  Tools  │         │ System   │
      └────┬────┘         └────┬─────┘
           │                   │
      ┌────▼────────┐    ┌────▼─────────┐
      │   SQLite    │    │   ChromaDB   │
      │ (Structured)│    │  (Vectors)   │
      └─────────────┘    └──────────────┘
```

### Components:

1. **MCP Layer** - Structured queries (filters, aggregations, lead lookups)
2. **RAG Layer** - Semantic search on conversations, summaries, objections
3. **Aggregation Engine** - Pre-computed KPIs and trend analysis
4. **LangChain Agent** - Intelligent orchestration and reasoning
5. **Streamlit UI** - Beautiful chat interface with live dashboard

## 📦 What's Included

```
WhiteLabel Lead Intelligence/
├── Data/
│   └── exported_dataset/                  # 402 leads with full conversation data
├── data/                                   # Generated at runtime
│   ├── leads.db                           # SQLite database
│   └── chroma_db/                         # Vector embeddings
├── src/
│   ├── data_ingestion.py                  # CSV → SQLite parser
│   ├── query_tools.py                     # MCP-style query tools
│   ├── rag_system.py                      # RAG + embeddings
│   └── ai_agent.py                        # LangChain agent
├── app.py                                  # Streamlit frontend
├── requirements.txt                        # Python dependencies
└── README.md                              # This file
```

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup OpenAI API Key

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Ingest Data (Already Done!)

The data has been ingested into SQLite. If you need to re-run:

```bash
python src/data_ingestion.py
```

### 5. Create Vector Embeddings (Optional but Recommended)

```bash
python src/rag_system.py
```

This creates semantic embeddings for RAG-powered conversation search.

### 6. Launch the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 🎮 Usage Examples

### Factual Queries (MCP Layer)

```
👤 "Show me all Won leads"
🤖 Returns: List of 5 won leads with details

👤 "Leads moving in January 2026 with budget under £400"
🤖 Returns: Laia Vilatersana Alsina (£395, Jan 3, 2026)

👤 "What is Laia's accommodation requirement?"
🤖 Returns: Studio, private kitchen/bathroom, £395 max budget, etc.
```

### Analytical Queries (Aggregation Engine)

```
👤 "How many total leads do we have?"
🤖 Returns: 14 total leads with status breakdown

👤 "What's the average budget for UCL students?"
🤖 Returns: £376.80 GBP average

👤 "Show me move-in month trends"
🤖 Returns: Jan 2026 (2 leads), Sep 2025 (2 leads), Dec 2025 (1 lead)
```

### Semantic Queries (RAG Layer - requires embeddings)

```
👤 "What are students concerned about the most?"
🤖 Searches conversations and returns top concerns with citations

👤 "Show me conversations mentioning budget or pricing"
🤖 Returns: Relevant conversation excerpts with lead context

👤 "What objections do Indian students face?"
🤖 Searches objections by nationality and provides insights
```

## 📊 Dashboard Features

The sidebar shows live KPIs:

- **Total Leads**: 14
- **Status Breakdown**: Won (5), Lost (3), Opportunity (2), etc.
- **Location Distribution**: London (12 leads)
- **Average Budget**: £376.80 GBP
- **Move-in Trends**: By month
- **Room Type Preferences**: Studio, ensuite, etc.

## 🧪 Testing the Agent

Test the AI agent directly:

```bash
python src/ai_agent.py
```

This runs 4 sample queries and shows the responses.

## 🔧 Technical Details

### Data Model

Each lead contains:
- **User Persona**: Name, nationality, contact info, student status
- **Accommodation Requirements**: Budget, location, room type, move-in date, amenities
- **Student Journey**: Visa status, university acceptance, flight booking
- **Properties Considered**: Properties and rooms under consideration
- **Tasks & Actionables**: Pending tasks, follow-ups, due dates
- **Conversation Summary**: Timeline, key insights, student behavior
- **Objections & Concerns**: Budget issues, availability, service quality

### Tools Available to Agent

1. `get_lead_by_id` - Get full lead details
2. `filter_leads` - Filter by status, budget, location, etc.
3. `get_aggregations` - Get all KPIs and statistics
4. `get_leads_by_status` - Get leads with specific status
5. `search_leads_by_name` - Search by name
6. `get_lead_tasks` - Get tasks for a lead
7. `get_conversation_summary` - Get conversation insights
8. `semantic_search` (RAG) - Semantic search across conversations
9. `search_objections` (RAG) - Search objections and concerns

### LLM Configuration

- **Model**: GPT-4o (OpenAI)
- **Temperature**: 0.3 (more factual, less creative)
- **Embedding Model**: text-embedding-3-small

## 📈 POC Statistics

**Current Data**:
- 402 leads loaded with full conversation data
- 5 Won, 3 Lost, 2 Opportunity, 2 Contacted, 2 Disputed
- 60 tasks extracted
- 24 RAG documents created
- 12 leads for London
- Average budget: £376.80 GBP

## 🎯 Success Criteria

✅ Partner admin can ask 10-15 realistic questions  
✅ Get correct, traceable, insightful responses  
✅ Validate answers using source citations  
✅ Feel confident that deeper insights are accessible instantly  
✅ Recognize value for full development  

## 🚧 Known Limitations (POC)

1. **Dataset**: 402 leads with full conversation data (scalable to thousands)
2. **No Real-time Updates**: Data is static from CSV
3. **No Multi-tenant**: Single university (UCL) in this POC
4. **No Authentication**: No login/user management
5. **Local Only**: Not deployed to cloud (yet)

## 🔮 Next Steps for Full Product

1. **Scale Data**: Support thousands of leads per partner
2. **Real-time Sync**: Connect to live CRM/conversation systems
3. **Multi-tenant**: Support multiple universities with data isolation
4. **Advanced Analytics**: Predictive models, conversion forecasting
5. **Export Features**: PDF reports, Excel exports
6. **API Access**: RESTful API for programmatic access
7. **Webhooks**: Real-time notifications for key events
8. **Role-based Access**: Different views for admins, agents, managers

## 📞 Support

For questions or issues, contact the development team.

## 📄 License

Proprietary - Amber Intelligence POC

---

**Built with**: Python, LangChain, OpenAI, Streamlit, ChromaDB, SQLite  
**Demo Ready**: Yes ✅  
**Production Ready**: POC Stage 🚧

