# Database Schema Reference

## Complete Database Schema for SQLite (data/leads.db)

### Table: `leads`
Main lead information table.

| Column | Type | Description |
|--------|------|-------------|
| `lead_id` | TEXT | Primary key, unique lead identifier |
| `name` | TEXT | Lead's full name |
| `mobile_number` | TEXT | Lead's mobile phone number |
| `status` | TEXT | Lead status: 'Won', 'Lost', 'Opportunity', 'Contacted', 'Disputed' |
| `structured_data` | TEXT | JSON string with structured lead data |
| `communication_timeline` | TEXT | JSON string with communication timeline |
| `crm_conversation_details` | TEXT | JSON string with CRM conversation details |
| `created_at` | TIMESTAMP | Record creation timestamp |

### Table: `lead_requirements`
Extracted requirements and preferences for each lead.

| Column | Type | Description |
|--------|------|-------------|
| `lead_id` | TEXT | Foreign key to leads.lead_id |
| `nationality` | TEXT | Lead's nationality (source country) |
| `location` | TEXT | Preferred location (destination) |
| `university` | TEXT | University name |
| `move_in_date` | TEXT | Move-in date (format: YYYY-MM-DD) |
| `budget_max` | REAL | Maximum budget (numeric) |
| `budget_currency` | TEXT | Currency code (e.g., 'GBP', 'USD') |
| `room_type` | TEXT | Preferred room type (e.g., 'ensuite', 'studio') |
| `lease_duration_weeks` | INTEGER | Lease duration in weeks |
| `visa_status` | TEXT | Visa status |
| `university_acceptance` | TEXT | University acceptance status |

### Table: `crm_data`
CRM export data with additional lead information.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `crm_id` | TEXT | CRM system ID |
| `lead_id` | TEXT | Foreign key to leads.lead_id |
| `budget_full` | REAL | Full budget amount |
| `budget_currency` | TEXT | Currency code |
| `lost_reason` | TEXT | Reason for loss (if status = 'Lost') |
| `move_in_date` | TEXT | Move-in date |
| `lease_duration` | TEXT | Lease duration text |
| `lease_duration_days` | INTEGER | Lease duration in days |
| `state` | TEXT | State/province |
| `created_at` | TEXT | Creation date from CRM |
| `location_name` | TEXT | Location name |
| `location_state` | TEXT | Location state |
| `location_country` | TEXT | **Destination country** (where they're moving to) |
| `location_locality` | TEXT | Location locality |
| `street_number` | TEXT | Street number |
| `lead_name` | TEXT | Lead name |
| `lead_email` | TEXT | Lead email |
| `lead_phone` | TEXT | Lead phone number |
| `phone_country` | TEXT | **Source country** (where lead is from, based on phone) |
| `inventory_id` | TEXT | Inventory ID |
| `property_name` | TEXT | Property name |
| `source_details` | TEXT | Source details |
| `tags` | TEXT | Tags |
| `display_name` | TEXT | Display name |
| `partner_id` | TEXT | Partner ID |
| `created_at_db` | TIMESTAMP | Database creation timestamp |

**IMPORTANT**: 
- `location_country` = Destination country (where they're moving to)
- `phone_country` = Source country (where lead is from)

### Table: `lead_properties`
Properties and room types leads are considering.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `lead_id` | TEXT | Foreign key to leads.lead_id |
| `property_name` | TEXT | Property name |
| `room_type` | TEXT | Room type at this property |

### Table: `lead_amenities`
Amenities requested by leads.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `lead_id` | TEXT | Foreign key to leads.lead_id |
| `amenity` | TEXT | Amenity name (e.g., 'WiFi', 'Gym', 'Parking') |

### Table: `lead_tasks`
Tasks and action items for leads.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `lead_id` | TEXT | Foreign key to leads.lead_id |
| `task_type` | TEXT | Type of task |
| `description` | TEXT | Task description |
| `status` | TEXT | Task status: 'pending', 'in_progress', 'completed' |
| `due_date` | TEXT | Due date |
| `task_for` | TEXT | Task assigned to |

### Table: `lead_objections`
Objections and concerns raised by leads.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `lead_id` | TEXT | Foreign key to leads.lead_id |
| `objection_type` | TEXT | Type of objection |
| `objection_text` | TEXT | Objection text |
| `resolved` | BOOLEAN | Whether objection is resolved |
| `source` | TEXT | Source of objection |

### Table: `timeline_events`
Individual communication events (WhatsApp, calls, emails).

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `lead_id` | TEXT | Foreign key to leads.lead_id |
| `event_id` | INTEGER | Event ID from source system |
| `event_type` | TEXT | Type: 'whatsapp', 'call', 'email', etc. |
| `timestamp` | TEXT | Event timestamp |
| `content` | TEXT | Event content/message |
| `source` | TEXT | Source system |
| `direction` | TEXT | 'inbound' or 'outbound' |
| `agent_id` | INTEGER | Agent ID |
| `raw_data` | TEXT | Raw event data (JSON) |
| `created_at` | TIMESTAMP | Database creation timestamp |

### Table: `call_transcripts`
Call transcripts.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `lead_id` | TEXT | Foreign key to leads.lead_id |
| `call_id` | TEXT | Call ID |
| `transcript_text` | TEXT | Full transcript text |
| `record_url` | TEXT | Recording URL |
| `transcription_status` | TEXT | Transcription status |
| `created_at` | TIMESTAMP | Database creation timestamp |

## Common Query Patterns

### Get min/max budget:
```sql
SELECT MIN(budget_max) as min_budget, MAX(budget_max) as max_budget, AVG(budget_max) as avg_budget
FROM lead_requirements
WHERE budget_max IS NOT NULL AND budget_currency = 'GBP'
```

### Get room preferences (all countries):
```sql
SELECT room_type, COUNT(*) as count
FROM lead_requirements
WHERE room_type IS NOT NULL AND room_type != ''
GROUP BY room_type
ORDER BY count DESC
```

### Get Won leads with specific room type (all countries):
```sql
SELECT COUNT(*) as total_count
FROM leads l
JOIN lead_requirements lr ON l.lead_id = lr.lead_id
WHERE l.status = 'Won'
  AND lr.room_type LIKE '%ensuite%'
```

### Get room types by source country:
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

## Relationships

- `leads.lead_id` → `lead_requirements.lead_id` (1:1)
- `leads.lead_id` → `crm_data.lead_id` (1:many, but typically 1:1)
- `leads.lead_id` → `lead_properties.lead_id` (1:many)
- `leads.lead_id` → `lead_amenities.lead_id` (1:many)
- `leads.lead_id` → `lead_tasks.lead_id` (1:many)
- `leads.lead_id` → `lead_objections.lead_id` (1:many)
- `leads.lead_id` → `timeline_events.lead_id` (1:many)
- `leads.lead_id` → `call_transcripts.lead_id` (1:many)

