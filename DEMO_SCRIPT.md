# 🎬 Demo Script for Stakeholders

## 5-Minute Demo Flow

---

## Introduction (30 seconds)

> "This is the UCL Lead Intelligence AI - an intelligent assistant that helps university admins understand their student leads, analyze trends, and extract insights instantly. Instead of waiting for manual reports or digging through spreadsheets, you can just ask questions in natural language."

---

## Part 1: Dashboard Overview (1 minute)

**[Point to sidebar]**

> "First, let's look at the live dashboard. We can see at a glance:"
> - "We have **14 leads** total in this demo"
> - "**5 are Won** bookings - our successful conversions"
> - "**3 Lost**, 2 Opportunities still in play"
> - "Most leads are for **London** accommodation"
> - "Average budget is **£376** per week"
> - "Peak move-in months are **January and September 2026**"

---

## Part 2: Factual Queries (1.5 minutes)

### Query 1: Simple Lookup
**Type:** `"How many total leads do we have?"`

**Expected:** "We have 14 total leads with the following breakdown..."

> "See how it gives us exact numbers with context."

---

### Query 2: Filtered Search
**Type:** `"Show me leads moving in January 2026 with budget less than 400 pounds"`

**Expected:** Returns Laia with her details

> "Here's where it gets powerful - we can filter by multiple criteria at once. Budget, move-in dates, location, status - anything."

---

### Query 3: Lead Details
**Type:** `"What is Laia's accommodation requirement?"`

**Expected:** Full details about room type, budget, preferences

> "We get comprehensive information instantly - no need to dig through multiple screens or CSV files."

---

## Part 3: Analytical Insights (1.5 minutes)

### Query 4: Status Analysis
**Type:** `"List all Won leads with their universities"`

**Expected:** 5 won leads with details

> "Now let's analyze our successful conversions. We can see which universities, what their budgets were, when they're moving in."

---

### Query 5: Trends
**Type:** `"What are the most popular room types?"`

**Expected:** Breakdown of room type preferences

> "This helps us understand student preferences. We can see studios and ensuites are most popular."

---

### Query 6: Budget Analysis
**Type:** `"What's the average budget for UCL students?"`

**Expected:** £376.80 GBP

> "Financial insights help us understand market positioning and pricing strategies."

---

## Part 4: Advanced (Optional - if RAG is enabled) (1 minute)

### Query 7: Semantic Search
**Type:** `"What concerns do students have about accommodation?"`

**Expected:** Insights from conversations

> "With RAG enabled, we can search conversations semantically - understanding context and meaning, not just keywords."

---

### Query 8: Objections Analysis
**Type:** `"Show me common objections faced by leads"`

**Expected:** Categorized objections

> "This is gold for ops teams - understanding why deals don't close, what concerns are most common."

---

## Closing (30 seconds)

### Key Value Propositions

✅ **Instant Insights** - No waiting for reports or analyst queries  
✅ **Natural Language** - No need to learn complex filters or query languages  
✅ **Evidence-Based** - Every answer shows sources and tools used  
✅ **Scalable** - Works with 14 leads or 14,000 leads  
✅ **Multi-dimensional** - Status, budget, location, time, conversations - all queryable  

---

## Follow-up Questions to Handle

### "How does it handle larger datasets?"
> "This is built on scalable tech - SQLite + vector databases. In production, we'd use PostgreSQL and can handle millions of leads with sub-second response times."

### "What about data security?"
> "For production, we'd implement role-based access control, data encryption, audit logs, and comply with GDPR/data protection requirements."

### "Can it integrate with our CRM?"
> "Absolutely. The architecture is designed to sync with live CRM systems, Salesforce, HubSpot, or custom systems via APIs. This demo uses CSV for simplicity."

### "What about multiple universities?"
> "The full product would be multi-tenant - each university has isolated data, custom branding, and their own dashboard. This POC shows one tenant (UCL)."

### "How accurate is it?"
> "For structured queries (filters, counts, lookups) - 100% accurate, it queries directly from your data. For analytical insights, it uses GPT-4 which is highly reliable and always shows its reasoning."

---

## Alternative Demo Flow (Technical Audience)

For technical stakeholders, emphasize:

1. **Architecture** - Show the hybrid MCP + RAG approach
2. **Tools** - Demonstrate the function-calling and tool usage
3. **Extensibility** - Show how easy it is to add new query types
4. **Performance** - Mention sub-second response times
5. **Code Quality** - Clean, modular, production-ready structure

---

## Preparation Checklist

Before demo:

- [ ] `.env` file with valid OpenAI API key
- [ ] Run `streamlit run app.py` and verify it loads
- [ ] Test 2-3 queries to ensure responses are good
- [ ] (Optional) Run `python src/rag_system.py` to enable RAG
- [ ] Clear any previous chat history
- [ ] Have backup browser tab ready in case of issues
- [ ] Prepare answers to common follow-up questions

---

## Post-Demo Actions

After successful demo:

1. **Share access** - Provide demo link or credentials
2. **Gather feedback** - What features are most valuable?
3. **Discuss timeline** - When could they go live?
4. **Next steps** - Pilot program, pricing, integration requirements
5. **Follow-up** - Schedule technical deep-dive with their team

---

## Sample Questions to Seed Interest

During demo, you can ask audience:

- "What questions do YOU currently struggle to answer about your leads?"
- "How long does it take to generate a monthly lead report today?"
- "What would you ask this system if you could ask anything?"
- "What insights would help your admissions team close more leads?"

This gets them thinking about their own use cases and imagining the value.

---

**Good luck with your demo! 🚀**

