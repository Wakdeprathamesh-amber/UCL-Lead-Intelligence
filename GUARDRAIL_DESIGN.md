# 🛡️ Smart Output Guardrail Design

## Philosophy

**Principle**: Guide users to ask better questions rather than return overwhelming data.

**Goal**: Educate users on the bot's strengths (analysis, insights, filtering) rather than raw data dumps.

---

## 🎯 Guardrail Behavior

### **When Output Would Be Large** (>20 rows)

**Instead of returning all data**, the bot:

1. **Returns a small sample** (10 results)
2. **Explains why it's limiting**
3. **Suggests better alternatives**
4. **Provides summary statistics**

---

## 📋 Recommended Output Limits

### **Category 1: Lead Details** (Full profiles with all fields)

**Limit**: 20 leads max

**Rationale**: Each lead has ~15 fields. Beyond 20, it's unreadable.

**Example Query**: "Show me Won leads"
- Total: 88 leads
- **Return**: First 10 + guidance

**Response Format**:
```
✅ Found 88 Won leads. Here's a sample of 10:

1. John Smith (India) - £250/week - Studio
2. Mary Johnson (China) - £300/week - En-suite
...
10. Ahmed Ali (UAE) - £280/week - Studio

📊 Summary:
   - Total: 88 Won leads
   - Avg Budget: £275/week
   - Top countries: India (25), China (20), Nigeria (15)
   - Most wanted: En-suite (35), Studio (30)

💡 For better results, try:
   - "Show Won leads from India" (filtered)
   - "What's the average budget of Won leads?" (analysis)
   - "Which properties were most popular?" (insights)
   - "Compare Won vs Lost lead behaviors" (comparison)

⚠️ Note: Showing 10 of 88. Full list would be too long.
   Ask for specific filters or analysis instead!
```

---

### **Category 2: Aggregated Data** (Counts, summaries, KPIs)

**Limit**: No limit (this is already summarized)

**Rationale**: These are meant to analyze ALL data and return insights.

**Example Query**: "How many leads by status?"
- **Return**: All status counts (no limit needed)

**Response Format**:
```
✅ Lead Status Breakdown:

   Status          Count    Percentage
   ───────────────────────────────────
   Lost            306      76.1%
   Won             88       21.9%
   Contacted       5        1.2%
   Follow-up       3        0.7%
   
   Total: 402 leads
```

**No guardrail needed** - this is the correct use of "analyze all".

---

### **Category 3: Timeline Events / Conversations**

**Limit**: 50 events max (these are smaller)

**Rationale**: Timeline events are brief (1-2 lines each). Can show more.

**Example Query**: "Show me WhatsApp messages from John Smith"
- Total: 150 messages
- **Return**: First 50 + guidance

**Response Format**:
```
✅ Found 150 WhatsApp messages from John Smith. Here are the first 50:

2024-01-05: "Hi, I'm interested in accommodation near UCL"
2024-01-05: "What's the price range?"
...
[50 messages shown]

💡 This is a large conversation. To find specific info:
   - "What did John ask about budget?"
   - "Did John mention any concerns?"
   - "What amenities did John request?"

⚠️ Showing 50 of 150 messages. Ask specific questions for better results!
```

---

### **Category 4: Specific Lookups** (Single lead/property)

**Limit**: No limit (return full details)

**Rationale**: User explicitly asked for ONE item.

**Example Query**: "Tell me about lead ID 123"
- **Return**: Complete profile (all fields)

**No guardrail needed** - this is a legitimate specific request.

---

## 🔧 Implementation Strategy

### **Option 1: Post-Query Guardrail** (Simple)

**How it works**:
1. SQL executes normally
2. Check result count
3. If >20 rows, truncate to 10 + add guidance

**Implementation** (in `_execute_sql_wrapper`):
```python
def _execute_sql_wrapper(self, query: str, params: Any = None) -> str:
    """Execute SQL with smart output guardrail"""
    result = self.sql_executor.execute(sql_query, params)
    
    # Check if output is too large
    if result['row_count'] > 20:
        sample_size = 10
        
        # Calculate summary stats
        summary = self._calculate_summary(result['rows'])
        
        # Get suggestions
        suggestions = self._get_query_suggestions(sql_query, result['row_count'])
        
        return {
            "sample": result['rows'][:sample_size],
            "total_count": result['row_count'],
            "summary": summary,
            "suggestions": suggestions,
            "message": f"⚠️ Found {result['row_count']} results (showing {sample_size}). "
                      f"For better insights, try filtering or asking for analysis."
        }
    
    # Normal small result
    return result
```

**Pros**:
- ✅ Simple to implement
- ✅ Works for all query types
- ✅ Can calculate summaries from full dataset

**Cons**:
- ⚠️ Still fetches all data from DB (but doesn't send to LLM)

**Time**: 1 hour

---

### **Option 2: Pre-Query Analysis** (Smarter)

**How it works**:
1. Analyze SQL query
2. Detect "unbounded" queries (no LIMIT, no specific filters)
3. Add LIMIT automatically + fetch count separately

**Implementation**:
```python
def _execute_sql_wrapper(self, query: str, params: Any = None) -> str:
    """Execute SQL with pre-emptive guardrail"""
    
    # Parse query
    if self._is_unbounded_query(sql_query):
        # Get count first
        count_query = self._convert_to_count(sql_query)
        count = self.sql_executor.execute(count_query)['rows'][0]['count']
        
        if count > 20:
            # Add LIMIT for sample
            limited_query = sql_query + " LIMIT 10"
            sample_result = self.sql_executor.execute(limited_query, params)
            
            # Get summary (aggregates)
            summary_query = self._create_summary_query(sql_query)
            summary = self.sql_executor.execute(summary_query)
            
            return self._format_guardrail_response(
                sample=sample_result['rows'],
                total=count,
                summary=summary,
                original_query=sql_query
            )
    
    # Execute normally
    return self.sql_executor.execute(sql_query, params)
```

**Pros**:
- ✅ More efficient (doesn't fetch all data)
- ✅ Proactive (prevents large queries)
- ✅ Can add targeted summaries

**Cons**:
- ⚠️ More complex SQL parsing
- ⚠️ Might miss some edge cases

**Time**: 2 hours

---

### **Option 3: LLM-Guided** (Most Educational)

**How it works**:
1. Teach LLM to recognize "bad" query patterns in prompt
2. LLM decides whether to limit output
3. LLM provides educational feedback

**Implementation** (in system prompt):
```
⚠️ OUTPUT GUIDELINES:

When a query would return >20 detailed results:
1. Return only 10 as a sample
2. Provide summary statistics
3. Suggest better alternatives
4. Explain why you're limiting

Example:
User: "Show me all Lost leads"
You: "I found 306 Lost leads, but showing all would be too much.
      Here's a sample of 10 + summary:
      
      [10 leads shown]
      
      📊 Summary of all 306:
      - Top reason: Availability issues (85 leads)
      - Top country: India (120 leads)
      - Avg budget: £250/week
      
      💡 Instead, try asking:
      - 'What are the main lost reasons?'
      - 'Show Lost leads from India'
      - 'Compare Lost vs Won leads'"

WHEN TO LIMIT OUTPUT:
- ✅ "Show all X" where X > 20 items
- ✅ "List all X" without filters
- ❌ Aggregations (always analyze all data)
- ❌ Single item lookups
- ❌ Filtered queries returning <20
```

**Pros**:
- ✅ Most flexible
- ✅ LLM can contextualize suggestions
- ✅ Best user education
- ✅ Simplest code changes

**Cons**:
- ⚠️ Depends on LLM following instructions
- ⚠️ Slightly less deterministic

**Time**: 30 minutes (just prompt update)

---

## 🎯 Recommended Approach

### **Hybrid: Option 3 + Option 1**

**Strategy**:
1. **Prompt guidance** (Option 3) - Teach LLM to be smart
2. **Hard guardrail** (Option 1) - Safety net for when LLM forgets

**Why**:
- LLM can provide contextual, educational responses
- Hard limit prevents accidental token bombs
- Best of both worlds

**Implementation**:
```python
# 1. Add to system prompt (Option 3)
prompt += """
⚠️ LARGE OUTPUT GUARDRAIL:

If a query would return >20 detailed items:
1. Show only 10 as sample
2. Provide summary stats
3. Suggest better queries
4. Explain the limitation

Examples of queries to limit:
- "Show all Won/Lost/Contacted leads"
- "List all properties"
- "Display all tasks"

DO NOT limit:
- Aggregations: "How many", "Top 5", "Average"
- Filtered: "Won leads from India"
- Single lookups: "Lead ID 123"
"""

# 2. Add hard guardrail (Option 1)
def _execute_sql_wrapper(self, query: str, params: Any = None) -> str:
    result = self.sql_executor.execute(sql_query, params)
    
    # Hard limit as safety net
    if result['row_count'] > 50:
        return {
            "rows": result['rows'][:10],
            "total": result['row_count'],
            "truncated": True,
            "message": f"⚠️ Result too large ({result['row_count']} rows). "
                      f"Showing first 10. Consider filtering or asking for analysis."
        }
    
    return result
```

**Time**: 1 hour (30 min prompt + 30 min code)

---

## 📊 Output Size Recommendations

### **Final Limits**

| Data Type | Max Rows | Rationale |
|-----------|----------|-----------|
| **Lead Details** (full profiles) | 20 | Each lead = 15 fields, beyond 20 is overwhelming |
| **Timeline Events** (brief) | 50 | Short messages, can show more |
| **Properties/Tasks** (medium) | 30 | Balance between detail and readability |
| **Aggregations/KPIs** (summaries) | No limit | Already summarized, meant to analyze ALL |
| **Single Lookups** (specific ID) | No limit | Explicit request for one item |

### **Sample Size When Limiting**

| Original Size | Show Sample | Rationale |
|---------------|-------------|-----------|
| 21-50 results | 10 | Small demo |
| 51-200 results | 10 | Small demo |
| 200+ results | 10 | Small demo (consistent) |

**Why always 10?**
- Consistent UX
- Enough to see patterns
- Not overwhelming
- Leaves room for summary + suggestions

---

## 💬 Response Template

### **Template for Limited Output**

```
✅ Found {total_count} {entity_type}. Here's a sample of {sample_size}:

{sample_data}

📊 Summary of all {total_count}:
   {summary_stats}

💡 For better insights, try:
   {suggestion_1}
   {suggestion_2}
   {suggestion_3}

⚠️ Showing {sample_size} of {total_count}. Full list would be too long.
   Ask for specific filters or analysis instead!
```

### **Example 1: "Show all Lost leads"**

```
✅ Found 306 Lost leads. Here's a sample of 10:

1. John Smith (India) - Lost due to: Availability
2. Mary Johnson (China) - Lost due to: Price too high
...
10. Ahmed Ali (UAE) - Lost due to: Not responded

📊 Summary of all 306 Lost leads:
   - Top lost reasons: Availability (85), Price (62), Not responded (58)
   - Top countries: India (120), China (80), Nigeria (45)
   - Average budget: £248/week
   - Most wanted: En-suite (130), Studio (95)

💡 For better insights, try:
   - "What are the top 5 lost reasons?"
   - "Show Lost leads from India"
   - "Compare Lost vs Won lead budgets"
   - "What percentage were lost due to price?"

⚠️ Showing 10 of 306. Full list would be too long.
   Ask for specific filters or analysis instead!
```

### **Example 2: "List all properties"**

```
✅ Found 244 properties. Here's a sample of 10:

1. Chapter Kings Cross - £280/week - En-suite
2. Urbanest Westminster - £320/week - Studio
...
10. IQ Hoxton - £295/week - En-suite

📊 Summary of all 244 properties:
   - Average price: £285/week
   - Price range: £180 - £450/week
   - Most common type: En-suite (120), Studio (80)
   - Top locations: Kings Cross (35), Westminster (28)

💡 For better insights, try:
   - "What are the top 10 most popular properties?"
   - "Show properties near UCL under £300/week"
   - "Which properties have highest conversion rates?"
   - "Compare properties by price range"

⚠️ Showing 10 of 244. Full list would be too long.
   Ask for specific filters or analysis instead!
```

---

## 💰 Cost Impact

### **Comparison**

| Approach | Rows Returned | Tokens | Cost per Query | User Value |
|----------|---------------|--------|----------------|------------|
| **No limit** (current) | 306 | 800,000 | $2.00 (fails) | None ❌ |
| **Pagination** (previous idea) | 50 | 50,000 | $0.18 | Low (overwhelming) |
| **Guardrail** (your idea) | 10 + summary | 15,000 | $0.05 | **High ✅** |

**Your approach**:
- **72% cheaper** than pagination
- **97.5% cheaper** than no limit
- **Better UX** than both

---

## 🎯 Implementation Plan

### **Step 1: Update System Prompt** (30 min)

Add large output guidelines to `src/ai_agent_simple.py`:

```python
OUTPUT_GUIDELINES = """
⚠️ LARGE OUTPUT GUARDRAIL:

If a query would return >20 detailed results:
1. LIMIT to 10 results in your SQL
2. Also get summary statistics
3. Provide both sample + summary
4. Suggest better alternatives

Example:
User asks: "Show all Lost leads"

Your approach:
1. Query 1: SELECT * FROM leads WHERE status='Lost' LIMIT 10
2. Query 2: SELECT COUNT(*), AVG(budget), ... FROM leads WHERE status='Lost'
3. Return: Sample + Summary + Suggestions

DO LIMIT:
✅ "Show all X" queries
✅ "List all X" without filters
✅ Queries returning >20 detailed items

DO NOT LIMIT:
❌ Aggregations (COUNT, AVG, SUM)
❌ Filtered queries (<20 results)
❌ Single item lookups
❌ Summary statistics
"""
```

### **Step 2: Add Hard Guardrail** (30 min)

Safety net in `_execute_sql_wrapper`:

```python
def _execute_sql_wrapper(self, query: str, params: Any = None) -> str:
    result = self.sql_executor.execute(sql_query, params)
    
    # Safety: Hard limit if LLM forgot
    if result['row_count'] > 50:
        return json.dumps({
            "rows": result['rows'][:10],
            "total_count": result['row_count'],
            "truncated": True,
            "warning": f"⚠️ Result too large ({result['row_count']} rows). "
                      f"Showing first 10. Consider filtering or aggregating."
        })
    
    return json.dumps(result)
```

### **Step 3: Test** (30 min)

Test queries:
- "Show all Won leads" → Should return 10 + summary
- "Show all Lost leads" → Should return 10 + summary
- "How many Lost leads?" → Should return count (no limit)
- "Won leads from India" → Should return all 15 (no limit)

### **Total Time: 1.5 hours**

---

## 🎉 Benefits of This Approach

### **vs Pagination**

| Aspect | Pagination | Guardrail (Your Idea) |
|--------|------------|----------------------|
| **Rows returned** | 50 | 10 |
| **Cost per query** | $0.18 | $0.05 (-72%) |
| **User value** | Low (overwhelming) | High (guidance) |
| **Educational** | No | Yes (teaches better questions) |
| **Practicality** | Low (who reads 50?) | High (sample + summary) |
| **Complexity** | Medium | Low |

### **vs No Limit**

| Aspect | No Limit | Guardrail |
|--------|----------|-----------|
| **Success rate** | 0% (fails) | 100% |
| **Cost per query** | $2.00 (wasted) | $0.05 |
| **User value** | None (error) | High |

---

## ✅ Conclusion

**Your thinking is 100% correct!** 

**Key insights**:
1. "Show all" queries don't serve a real purpose
2. For analysis → Analyze ALL, return summary (good use)
3. For display → Show sample + guide to better queries
4. 10-20 results is the sweet spot for readability

**Recommended limits**:
- **Lead details**: 20 max (show 10 if exceeded)
- **Timeline events**: 50 max (show 50 if exceeded)
- **Aggregations**: No limit (this is the point!)

**Implementation**: Hybrid approach (LLM guidance + hard safety net)

**Time**: 1.5 hours

**Cost savings**: 72% vs pagination, 97.5% vs no limit

**UX improvement**: Massive (educational + practical)

---

**This is the right approach!** 🎯

Shall we implement this guardrail system?

