# 📋 Demo Questions Reference Guide

> **Quick reference for all 12 demo questions and their expected outcomes**

---

## 🔍 Category 1: Lead Lookup & Filtering

### 1. **📊 All Won Leads**
**Query**: "Show me all Won leads with their details"

**Expected Response**:
- List of 5 Won leads
- Names, budgets, locations
- Move-in dates
- Universities

**Use Case**: Quick view of successful conversions

**Response Time**: ~2 seconds

---

### 2. **💰 Budget < £400**
**Query**: "Show me leads with budget less than 400 pounds"

**Expected Response**:
- Laia Vilatersana Alsina (£395)
- Full lead details
- Room type, location, status

**Use Case**: Filter leads by budget criteria

**Response Time**: ~2 seconds

---

### 3. **📅 January 2026 Move-ins**
**Query**: "Show me leads moving in January 2026"

**Expected Response**:
- 2 leads with Jan 2026 move-in dates
- Laia Vilatersana Alsina
- Details of accommodation requirements

**Use Case**: Planning for specific move-in periods

**Response Time**: ~2 seconds

---

## 📈 Category 2: Analytics & Insights

### 4. **📊 Lead Statistics**
**Query**: "What are our total lead statistics and breakdown by status?"

**Expected Response**:
- Total: 14 leads
- Won: 5 (36%)
- Lost: 3 (21%)
- Opportunity: 2 (14%)
- Contacted: 2 (14%)
- Disputed: 2 (14%)

**Use Case**: Quick performance overview

**Response Time**: ~2 seconds

---

### 5. **💷 Average Budget**
**Query**: "What's the average budget across all leads?"

**Expected Response**:
- Average: £376.80 GBP per week
- Breakdown if multiple currencies
- Context about lead count

**Use Case**: Understanding budget ranges

**Response Time**: ~2 seconds

---

### 6. **🏆 Top Trends**
**Query**: "What are the top trends and patterns in our lead data?"

**Expected Response**:
- London as primary location (12 leads)
- January/September peak move-in months
- Average budget £376.80
- Room type preferences (studios, ensuites)
- 36% conversion rate (Won)

**Use Case**: Strategic insights for planning

**Response Time**: ~3 seconds (uses aggregations)

---

## 👤 Category 3: Specific Lead Information

### 7. **👩 Laia's Details**
**Query**: "What are Laia's accommodation requirements and current status?"

**Expected Response**:
- Name: Laia Vilatersana Alsina
- Status: Won
- Budget: £395 GBP
- Move-in: January 3, 2026
- Room: Bronze Studio Premium
- Location: Sterling Court, London
- Requirements: Private bathroom, kitchen, quiet study areas

**Use Case**: Deep dive into specific lead

**Response Time**: ~2 seconds

---

### 8. **🔎 Search by Name**
**Query**: "Show me all information about Haoran Wang"

**Expected Response**:
- Lead ID: #09223660506
- Status: Won
- Location: London
- Budget: £279 GBP
- Lease: 42 weeks
- All available details

**Use Case**: Quick lead lookup by name

**Response Time**: ~2 seconds

---

### 9. **📋 Lead Tasks**
**Query**: "What tasks are associated with Won leads?"

**Expected Response**:
- Total tasks for Won leads
- Task types (booking, payment, follow-up, etc.)
- Status of tasks (completed, pending, in_progress)
- Examples from specific leads

**Use Case**: Understanding action items

**Response Time**: ~2-3 seconds

---

## ⚖️ Category 4: Comparative Analysis

### 10. **✅ Won vs ❌ Lost**
**Query**: "Compare Won leads versus Lost leads - what are the key differences?"

**Expected Response**:
- Won leads: 5 total, avg budget £368
- Lost leads: 3 total, avg budget £415
- Key differences:
  - Budget alignment
  - Response time
  - Requirement matching
- Insights on conversion factors

**Use Case**: Understanding what drives conversions

**Response Time**: ~3-4 seconds (hybrid query)

---

### 11. **🎯 Conversion Insights**
**Query**: "What factors contribute to successful lead conversion?"

**Expected Response**:
- Budget fit (within range)
- Quick response times
- Clear requirements met
- Location availability
- Room type alignment
- Good communication

**Use Case**: Improving conversion strategy

**Response Time**: ~3 seconds

---

### 12. **📊 Monthly Comparison**
**Query**: "Compare leads by move-in month - which months are most popular?"

**Expected Response**:
- January 2026: 2 leads
- September 2025: 2 leads
- December 2025: 1 lead
- Analysis of seasonal trends
- Insights for capacity planning

**Use Case**: Capacity and resource planning

**Response Time**: ~2 seconds

---

## 🎯 Query Type Breakdown

### Factual Queries (MCP) - 6 questions
Uses SQLite for exact data:
1. All Won Leads
2. Budget < £400
3. January 2026 Move-ins
4. Lead Statistics
5. Average Budget
6. Search by Name

**Characteristics**:
- ✅ 100% accurate
- ⚡ Fast (~50-100ms DB query)
- 📊 Structured results

---

### Analytical Queries (MCP Aggregation) - 4 questions
Uses SQL GROUP BY and calculations:
6. Top Trends
9. Lead Tasks
12. Monthly Comparison
(partial): Won vs Lost statistics

**Characteristics**:
- ✅ Exact numbers
- 📈 Trend analysis
- 🔢 Aggregated data

---

### Hybrid Queries (MCP + RAG) - 2 questions
Uses both databases:
7. Laia's Details (facts + context)
10. Won vs Lost (stats + insights)
11. Conversion Insights (data + patterns)

**Characteristics**:
- 🎯 Comprehensive
- 💡 Contextual insights
- 🔄 Multi-source data

---

## 💡 Pro Tips for Demo

### Start Simple → Complex
1. **Begin**: "All Won Leads" (simple lookup)
2. **Middle**: "Top Trends" (analytics)
3. **End**: "Won vs Lost" (comparative analysis)

### Show Different Capabilities
- **Filtering**: Budget, date, status queries
- **Analytics**: Statistics, averages, trends
- **Lookup**: Specific lead by name
- **Insights**: Conversion factors, comparisons

### Highlight Features
- ⚡ Speed of responses
- 🎯 Accuracy of data
- 📊 Multiple data sources
- 💬 Natural language understanding
- 📋 Copy-to-clipboard functionality
- 🔍 Source transparency (tools used)

---

## 🎬 Suggested Demo Flow (5 minutes)

### Act 1: Simple Queries (1 min)
```
"All Won Leads" → Show 5 successful conversions
"Budget < £400" → Demonstrate filtering
```

### Act 2: Analytics (2 min)
```
"Lead Statistics" → Show KPIs
"Top Trends" → Demonstrate insights
"Monthly Comparison" → Show planning value
```

### Act 3: Deep Dive (2 min)
```
"Laia's Details" → Show individual lead depth
"Won vs Lost" → Demonstrate comparative analysis
Copy response → Show copy feature
```

---

## 📊 Expected Response Formats

### List Format
```
Here are all Won leads:

1. **Laia Vilatersana Alsina**
   - Budget: £395
   - Location: London
   - Move-in: Jan 3, 2026
   
2. **Haoran Wang**
   ...
```

### Statistical Format
```
Lead Statistics:

Total Leads: 14

Status Breakdown:
• Won: 5 (36%)
• Lost: 3 (21%)
...
```

### Comparative Format
```
Comparison of Won vs Lost:

WON (5 leads):
• Average budget: £368
• Common factors: Budget fit, quick response

LOST (3 leads):
• Average budget: £415
• Common reasons: Budget too high, availability
```

---

## 🔧 Troubleshooting

### If Response is Wrong:
- Check if API key is valid
- Verify database has data (14 leads)
- Rephrase question more clearly

### If Response is Slow (>5s):
- Normal for first query (cold start)
- Subsequent queries should be faster
- Complex queries (hybrid) take 3-4s

### If No Results:
- Check filter criteria
- Verify data exists for query
- Try broader search terms

---

## 📚 Related Documentation

- **QUICKSTART.md** - Setup guide
- **DEMO_SCRIPT.md** - Full presentation flow
- **UI_ENHANCEMENTS.md** - UI features explained
- **ARCHITECTURE.md** - How queries work

---

## 🎓 Custom Questions

Beyond the 12 demo questions, users can ask:

### More Filtering
- "Leads in London with private bathrooms"
- "Students moving in before December"
- "Leads with budget between £300-400"

### More Analytics
- "What's the most common room type?"
- "How many leads per university?"
- "Average lease duration"

### More Comparisons
- "Compare studio vs ensuite preferences"
- "London vs other cities"
- "Short-term vs long-term leases"

### Lead-Specific
- "Show me [any lead name]'s details"
- "What properties is [lead name] considering?"
- "What are [lead name]'s concerns?"

---

**Total Demo Questions: 12**  
**Categories: 4**  
**Coverage: Complete feature set** ✅

*Ready for professional demo presentation!* 🚀

