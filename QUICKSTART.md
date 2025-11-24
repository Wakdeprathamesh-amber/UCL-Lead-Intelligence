# 🚀 Quick Start

## Setup (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Add OpenAI API Key

Create `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run App

```bash
streamlit run app.py
```

App opens at `http://localhost:8501`

## Try These Queries

**Basic:**
- "How many leads do we have?"
- "Give me leads by source country"
- "Show me Won leads"

**Analytics:**
- "What are the top queries from students?"
- "What top amenities are leads asking for?"
- "What's the average budget?"

**Advanced:**
- "Leads moving in January 2026 with budget < £400"
- "What are the most common concerns?"

## Dashboard

Sidebar shows live KPIs:
- Total leads: 402
- Status breakdown
- Average budget: £376/week
- Top source countries

## Troubleshooting

**"Agent initialization failed"**
- Check `.env` file exists with valid API key

**"No module named X"**
- Run: `pip install -r requirements.txt`

**Port 8501 in use**
- Run: `streamlit run app.py --server.port 8502`

## Next Steps

- See `DEMO.md` for demo script
- See `DEPLOYMENT_GUIDE.md` for cloud deployment
- See `ARCHITECTURE.md` for system details
