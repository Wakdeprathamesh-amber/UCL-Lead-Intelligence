"""
Database Schema Documentation
Complete schema with relationships, sample data, and query patterns
"""

SCHEMA_DOCUMENTATION = """
## DATABASE SCHEMA (SQLite - data/leads.db)

### Table: leads
**Primary Key**: lead_id (TEXT)
**Purpose**: Main lead information table

| Column | Type | Description |
|--------|------|-------------|
| lead_id | TEXT | Unique lead identifier (PK) |
| name | TEXT | Lead's full name |
| mobile_number | TEXT | Lead's mobile phone number |
| status | TEXT | Lead status: 'Won', 'Lost', 'Opportunity', 'Contacted', 'Disputed' |
| structured_data | TEXT | JSON string with structured lead data (conversation summary) |
| communication_timeline | TEXT | JSON string with communication timeline (WhatsApp, calls, emails) |
| crm_conversation_details | TEXT | JSON string with CRM conversation details |
| created_at | TIMESTAMP | Record creation timestamp |

**Sample Data**:
- lead_id: "123456"
- name: "John Doe"
- status: "Won"
- mobile_number: "+44 1234567890"

---

### Table: lead_requirements
**Primary Key**: lead_id (TEXT, FK → leads.lead_id)
**Purpose**: Extracted requirements and preferences for each lead
**Relationship**: 1:1 with leads (one lead has one requirements record)

| Column | Type | Description |
|--------|------|-------------|
| lead_id | TEXT | Foreign key to leads.lead_id |
| nationality | TEXT | Lead's nationality (SOURCE country - where they're from) |
| location | TEXT | Preferred location (DESTINATION - where they're moving to) |
| university | TEXT | University name |
| move_in_date | TEXT | Move-in date (format: YYYY-MM-DD) |
| budget_max | REAL | Maximum budget (numeric value) |
| budget_currency | TEXT | Currency code (e.g., 'GBP', 'USD') |
| room_type | TEXT | Preferred room type (e.g., 'ensuite', 'studio', 'private room') |
| lease_duration_weeks | INTEGER | Lease duration in weeks |
| visa_status | TEXT | Visa status |
| university_acceptance | TEXT | University acceptance status |

**Sample Data**:
- lead_id: "123456"
- nationality: "British" (SOURCE country)
- location: "London" (DESTINATION)
- budget_max: 400.0
- budget_currency: "GBP"
- room_type: "ensuite"

**IMPORTANT**: 
- nationality = SOURCE country (where lead is from)
- location = DESTINATION (where they're moving to)

---

### Table: crm_data
**Primary Key**: id (INTEGER AUTOINCREMENT)
**Purpose**: CRM export data with additional lead information
**Relationship**: Many:1 with leads (one lead can have multiple CRM records, typically 1:1)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| crm_id | TEXT | CRM system ID |
| lead_id | TEXT | Foreign key to leads.lead_id |
| budget_full | REAL | Full budget amount |
| budget_currency | TEXT | Currency code |
| lost_reason | TEXT | Reason for loss (if status = 'Lost') |
| move_in_date | TEXT | Move-in date |
| lease_duration | TEXT | Lease duration text |
| lease_duration_days | INTEGER | Lease duration in days |
| state | TEXT | State/province |
| created_at | TEXT | Creation date from CRM |
| location_name | TEXT | Location name |
| location_state | TEXT | Location state |
| **location_country** | TEXT | **DESTINATION country** (where they're moving to) - DO NOT use for "source country" queries |
| location_locality | TEXT | Location locality |
| street_number | TEXT | Street number |
| lead_name | TEXT | Lead name |
| lead_email | TEXT | Lead email |
| lead_phone | TEXT | Lead phone number |
| **phone_country** | TEXT | **SOURCE country** (where lead is from, based on phone) - USE THIS for "source country" queries |
| inventory_id | TEXT | Inventory ID |
| property_name | TEXT | Property name |
| source_details | TEXT | Source details |
| tags | TEXT | Tags |
| display_name | TEXT | Display name |
| partner_id | TEXT | Partner ID |
| created_at_db | TIMESTAMP | Database creation timestamp |

**Sample Data**:
- lead_id: "123456"
- phone_country: "GB" (SOURCE - where from)
- location_country: "United Kingdom" (DESTINATION - where moving to)
- lost_reason: "Not responded"
- property_name: "Sterling Court"

**CRITICAL DISTINCTION**:
- **phone_country** = SOURCE country (where lead is FROM) - Use for "by source country" queries
- **location_country** = DESTINATION country (where they're MOVING TO) - Do NOT use for source queries

---

### Table: lead_properties
**Primary Key**: id (INTEGER AUTOINCREMENT)
**Purpose**: Properties and room types leads are considering
**Relationship**: Many:1 with leads (one lead can consider multiple properties)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| lead_id | TEXT | Foreign key to leads.lead_id |
| property_name | TEXT | Property name |
| room_type | TEXT | Room type at this property |

**Sample Data**:
- lead_id: "123456"
- property_name: "Sterling Court"
- room_type: "Bronze Studio Premium"

---

### Table: lead_amenities
**Primary Key**: id (INTEGER AUTOINCREMENT)
**Purpose**: Amenities requested by leads
**Relationship**: Many:1 with leads (one lead can request multiple amenities)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| lead_id | TEXT | Foreign key to leads.lead_id |
| amenity | TEXT | Amenity name (e.g., 'WiFi', 'Gym', 'Parking') |

**Sample Data**:
- lead_id: "123456"
- amenity: "WiFi"

---

### Table: lead_tasks
**Primary Key**: id (INTEGER AUTOINCREMENT)
**Purpose**: Tasks and action items for leads
**Relationship**: Many:1 with leads (one lead can have multiple tasks)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| lead_id | TEXT | Foreign key to leads.lead_id |
| task_type | TEXT | Type of task |
| description | TEXT | Task description |
| status | TEXT | Task status: 'pending', 'in_progress', 'completed' |
| due_date | TEXT | Due date |
| task_for | TEXT | Task assigned to |

**Sample Data**:
- lead_id: "123456"
- task_type: "Follow-up"
- description: "Send property details"
- status: "pending"

---

### Table: lead_objections
**Primary Key**: id (INTEGER AUTOINCREMENT)
**Purpose**: Objections and concerns raised by leads
**Relationship**: Many:1 with leads (one lead can have multiple objections)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| lead_id | TEXT | Foreign key to leads.lead_id |
| objection_type | TEXT | Type of objection |
| objection_text | TEXT | Objection text |
| resolved | BOOLEAN | Whether objection is resolved |
| source | TEXT | Source of objection |

**Sample Data**:
- lead_id: "123456"
- objection_type: "Budget"
- objection_text: "Price is too high"
- resolved: False

---

### Table: timeline_events
**Primary Key**: id (INTEGER AUTOINCREMENT)
**Purpose**: Individual communication events (WhatsApp, calls, emails)
**Relationship**: Many:1 with leads (one lead can have many events)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| lead_id | TEXT | Foreign key to leads.lead_id |
| event_id | INTEGER | Event ID from source system |
| event_type | TEXT | Type: 'whatsapp', 'call', 'email', 'lead_info' |
| timestamp | TEXT | Event timestamp |
| content | TEXT | Event content/message |
| source | TEXT | Source system |
| direction | TEXT | 'inbound' or 'outbound' (⚠️ often NULL) |
| agent_id | INTEGER | Agent ID |
| raw_data | TEXT | Raw event data (JSON) |
| created_at | TIMESTAMP | Database creation timestamp |

**Sample Data**:
- lead_id: "123456"
- event_type: "whatsapp"
- content: "Hi, I'm interested in your properties"
- direction: NULL (often empty)
- timestamp: "2025-01-15 10:30:00"

**IMPORTANT NOTE**:
- The `direction` field is often NULL in timeline_events
- When getting ALL messages for analysis, do NOT filter by direction
- Filter by event_type and content IS NOT NULL instead

---

### Table: call_transcripts
**Primary Key**: id (INTEGER AUTOINCREMENT)
**Purpose**: Call transcripts
**Relationship**: Many:1 with leads (one lead can have multiple calls)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| lead_id | TEXT | Foreign key to leads.lead_id |
| call_id | TEXT | Call ID |
| transcript_text | TEXT | Full transcript text |
| record_url | TEXT | Recording URL |
| transcription_status | TEXT | Transcription status |
| created_at | TIMESTAMP | Database creation timestamp |

**Sample Data**:
- lead_id: "123456"
- call_id: "call_123"
- transcript_text: "Agent: Hello, how can I help? Lead: I'm looking for accommodation..."

---

## RELATIONSHIPS SUMMARY

```
leads (1) ──→ (1) lead_requirements
leads (1) ──→ (many) crm_data (typically 1:1)
leads (1) ──→ (many) lead_properties
leads (1) ──→ (many) lead_amenities
leads (1) ──→ (many) lead_tasks
leads (1) ──→ (many) lead_objections
leads (1) ──→ (many) timeline_events
leads (1) ──→ (many) call_transcripts
```

---

## COMMON QUERY PATTERNS

### Pattern 1: Room Types by Source Country
```sql
SELECT 
    COALESCE(c.phone_country, lr.nationality, 'Unknown') as source_country,
    lr.room_type,
    COUNT(*) as count
FROM leads l
JOIN lead_requirements lr ON l.lead_id = lr.lead_id
LEFT JOIN crm_data c ON l.lead_id = c.lead_id
WHERE lr.room_type IS NOT NULL 
  AND lr.room_type != ''
  AND (c.phone_country IS NOT NULL OR lr.nationality IS NOT NULL)
GROUP BY source_country, lr.room_type
ORDER BY source_country, count DESC
```

### Pattern 2: Min/Max Budget
```sql
SELECT 
    MIN(budget_max) as min_budget,
    MAX(budget_max) as max_budget,
    AVG(budget_max) as avg_budget,
    budget_currency
FROM lead_requirements
WHERE budget_max IS NOT NULL
GROUP BY budget_currency
```

### Pattern 3: Won Leads by Room Type
```sql
SELECT 
    lr.room_type,
    COUNT(*) as total_count
FROM leads l
JOIN lead_requirements lr ON l.lead_id = lr.lead_id
WHERE l.status = 'Won'
  AND lr.room_type IS NOT NULL
GROUP BY lr.room_type
ORDER BY total_count DESC
```

### Pattern 4: Status Breakdown
```sql
SELECT 
    status,
    COUNT(*) as count
FROM leads
GROUP BY status
ORDER BY count DESC
```

### Pattern 5: Communication Mode Analysis
```sql
SELECT 
    te.event_type,
    l.status,
    COUNT(*) as event_count,
    COUNT(DISTINCT te.lead_id) as lead_count
FROM timeline_events te
JOIN leads l ON te.lead_id = l.lead_id
WHERE te.event_type IN ('whatsapp', 'call', 'email')
GROUP BY te.event_type, l.status
```

---

## IMPORTANT NOTES FOR LLM

1. **Source vs Destination Country**:
   - When user asks "by source country" → Use `phone_country` or `nationality`
   - When user asks "by destination country" → Use `location_country`
   - Default to SOURCE country unless specified

2. **Room Type Queries**:
   - Use `lead_requirements.room_type` for preferences
   - Use `lead_properties.room_type` for specific properties considered

3. **Budget Queries**:
   - Use `lead_requirements.budget_max` for budget
   - Use `crm_data.budget_full` as alternative
   - Always check `budget_currency` for currency

4. **Status Values**:
   - Valid statuses: 'Won', 'Lost', 'Opportunity', 'Contacted', 'Disputed'
   - Use exact case when filtering

5. **Joins**:
   - Always join through `leads.lead_id`
   - Use LEFT JOIN when data might be missing
   - Use COALESCE for fallback values (e.g., phone_country/nationality)

6. **Performance**:
   - Use indexes: lead_id columns are indexed
   - Filter early in WHERE clause
   - Use LIMIT for large result sets

---

## DATA STATISTICS

- **Total Leads**: ~402 leads
- **Total Tasks**: ~2,271 tasks
- **Total CRM Records**: ~406 records
- **Total Timeline Events**: 10,000+ events
- **Total RAG Documents**: 10,000+ documents

---

## QUERY STRATEGY GUIDE

### Use SQL (execute_sql_query) for:
- Counts, aggregations, statistics
- Filtering, grouping, sorting
- Min/max/average calculations
- Joins across tables
- Any structured data query
- "How many", "What is the average", "Show me all", "Group by"

### Use RAG (semantic_search) for:
- Themes, concerns, patterns
- Conversation analysis
- Behavioral insights
- "What do leads say about X?"
- "What concerns do leads have?"
- Any semantic/meaning-based query

### Combine both for:
- "Behavioral differences Won vs Lost" → SQL for status + RAG for conversations
- "High-budget lead concerns" → SQL for filtering + RAG for concerns
- Complex analytical queries requiring both structured and semantic data

"""


def get_schema_prompt() -> str:
    """Get formatted schema for LLM prompt"""
    return SCHEMA_DOCUMENTATION


def get_sample_queries() -> str:
    """Get sample SQL queries as examples"""
    return """
## SAMPLE SQL QUERIES (Examples for LLM)

### Example 1: Room Types by Source Country
```sql
SELECT 
    COALESCE(c.phone_country, lr.nationality, 'Unknown') as source_country,
    lr.room_type,
    COUNT(*) as count
FROM leads l
JOIN lead_requirements lr ON l.lead_id = lr.lead_id
LEFT JOIN crm_data c ON l.lead_id = c.lead_id
WHERE lr.room_type IS NOT NULL 
  AND (c.phone_country IS NOT NULL OR lr.nationality IS NOT NULL)
GROUP BY source_country, lr.room_type
ORDER BY source_country, count DESC
```

### Example 2: Budget Statistics
```sql
SELECT 
    MIN(budget_max) as min_budget,
    MAX(budget_max) as max_budget,
    AVG(budget_max) as avg_budget,
    budget_currency
FROM lead_requirements
WHERE budget_max IS NOT NULL
GROUP BY budget_currency
```

### Example 3: Won Leads Count
```sql
SELECT COUNT(*) as won_count
FROM leads
WHERE status = 'Won'
```

### Example 4: Communication Mode Analysis
```sql
SELECT 
    te.event_type,
    l.status,
    COUNT(DISTINCT te.lead_id) as lead_count
FROM timeline_events te
JOIN leads l ON te.lead_id = l.lead_id
WHERE te.event_type IN ('whatsapp', 'call', 'email')
GROUP BY te.event_type, l.status
```

### Example 5: Lost Reasons
```sql
SELECT 
    lost_reason,
    COUNT(*) as count
FROM crm_data
WHERE lost_reason IS NOT NULL
GROUP BY lost_reason
ORDER BY count DESC
```

### Example 6: Get ALL Conversation Messages (for text analysis)
```sql
-- For "top queries" or "most common questions" - get ALL messages first
-- Note: direction field may be NULL in many records, so don't filter by it
SELECT 
    content,
    lead_id,
    event_type,
    timestamp
FROM timeline_events
WHERE event_type IN ('whatsapp', 'call', 'email')
  AND content IS NOT NULL
  AND content != ''
ORDER BY timestamp DESC
LIMIT 5000  -- Get first 5000 for analysis
-- Returns ALL messages (18,000+ total)
-- Then analyze the text to categorize and count
```

### Example 7: Get ALL WhatsApp Messages (for conversation analysis)
```sql
-- For analyzing student questions/queries/concerns
-- Important: direction field is often NULL, so don't filter by it
SELECT 
    content,
    lead_id,
    timestamp
FROM timeline_events
WHERE event_type = 'whatsapp'
  AND content IS NOT NULL
  AND content != ''
ORDER BY timestamp DESC
LIMIT 5000  -- Get first 5000 for analysis
-- Returns ALL WhatsApp messages (18,000+ total)
-- LLM analyzes text to extract question categories
```
"""

