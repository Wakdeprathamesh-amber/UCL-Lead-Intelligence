# 🚀 Quick Start Guide

## Get Up and Running in 5 Minutes

### Step 1: Add Your OpenAI API Key

Create a file named `.env` in the project root and add:

```
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

**Don't have an OpenAI key?** Get one at https://platform.openai.com/api-keys

---

### Step 2: Install Dependencies

```bash
# Using the setup script (recommended)
./setup.sh

# OR manually
source venv/bin/activate
pip install -r requirements.txt
```

---

### Step 3: Launch the App

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501` 🎉

---

### Step 4: Try These Questions

**Factual Queries:**
- "How many total leads do we have?"
- "Show me all Won leads"
- "What is Laia's budget and move-in date?"
- "Leads moving in January 2026 with budget less than 400 pounds"

**Analytical Queries:**
- "What's the average budget across all leads?"
- "Show me the status breakdown"
- "Which cities have the most leads?"
- "What room types are most popular?"

**Lead-Specific:**
- "Get details about lead #10245302799"
- "What tasks are pending for Laia?"
- "Search for leads named Wang"

---

### Step 5 (Optional): Enable RAG for Semantic Search

For advanced conversation search, create embeddings:

```bash
python src/rag_system.py
```

This takes ~30 seconds and enables queries like:
- "What are students concerned about the most?"
- "Show me conversations mentioning budget issues"
- "What objections do leads have?"

---

## 🎯 What You'll See

### Dashboard (Left Sidebar)
- Live KPI metrics
- Status breakdown
- Location distribution
- Budget averages
- Move-in month trends

### Chat Interface (Main Area)
- Natural language queries
- AI-powered responses
- Source citations
- Tool usage transparency

---

## 🧪 Test Without UI

Want to test the agent directly?

```bash
python src/ai_agent.py
```

This runs 4 sample queries and shows responses.

---

## 📊 View Your Data

All data is stored in SQLite:

```bash
sqlite3 data/leads.db

# Example queries:
SELECT name, status, budget_max FROM leads l 
JOIN lead_requirements lr ON l.lead_id = lr.lead_id;
```

---

## 🆘 Troubleshooting

**"Agent initialization failed"**
- Make sure `.env` file exists with valid OpenAI API key

**"No module named X"**
- Run: `pip install -r requirements.txt`

**"No such table: leads"**
- Run: `python src/data_ingestion.py`

**Port 8501 already in use**
- Run: `streamlit run app.py --server.port 8502`

---

## 🎓 Demo Script

Perfect for showing to stakeholders:

1. **Show Dashboard** - "Here are our key metrics at a glance"
2. **Ask Factual Query** - "Show me all Won leads"
3. **Filter Query** - "Leads moving in Jan 2026 with budget < £400"
4. **Lead Detail** - "What is Laia looking for?"
5. **Analytical** - "What's our average budget?"
6. **Semantic** (if RAG enabled) - "What concerns do students have?"

---

## 📝 Next Steps

- Add more lead data for richer insights
- Enable RAG for conversation intelligence
- Deploy to cloud (Render, Railway, Streamlit Cloud)
- Add authentication for production use
- Integrate with live CRM systems

---

**Questions?** Check `README.md` for full documentation!

Happy querying! 🚀

