# 📊 Database Schema

## Main Tables

### `leads` - Main lead information
- `lead_id` (TEXT, PK) - Unique identifier
- `name`, `mobile_number`, `status`
- `structured_data` (JSON) - Structured lead data
- `communication_timeline` (JSON) - Communication history
- `crm_conversation_details` (JSON) - CRM details
- `created_at` (TIMESTAMP)

### `lead_requirements` - Lead preferences
- `lead_id` (TEXT, FK) - Links to leads
- `nationality` - Source country
- `location` - Destination location
- `move_in_date`, `budget_max`, `budget_currency`
- `room_type`, `lease_duration_weeks`
- `visa_status`, `university_acceptance`

### `crm_data` - CRM export data
- `lead_id` (TEXT, FK) - Links to leads
- `phone_country` - **Source country** (where from)
- `location_country` - **Destination country** (where moving to)
- `budget_full`, `lost_reason`, `move_in_date`
- `property_name`, `inventory_id`

### `timeline_events` - Individual messages/calls
- `lead_id` (TEXT, FK)
- `event_type` - 'whatsapp', 'call', 'email'
- `content` - Message content
- `timestamp`, `source`, `direction`

### `lead_properties` - Properties under consideration
- `lead_id` (TEXT, FK)
- `property_name`, `room_type`

### `lead_amenities` - Requested amenities
- `lead_id` (TEXT, FK)
- `amenity` - e.g., 'WiFi', 'Gym', 'Parking'

### `lead_tasks` - Action items
- `lead_id` (TEXT, FK)
- `task_type`, `description`, `status`, `due_date`

### `lead_objections` - Concerns raised
- `lead_id` (TEXT, FK)
- `objection_type`, `description`

## Key Relationships

```
leads (1) ──→ (many) lead_requirements
leads (1) ──→ (many) timeline_events
leads (1) ──→ (many) lead_properties
leads (1) ──→ (many) lead_amenities
leads (1) ──→ (many) lead_tasks
leads (1) ──→ (1) crm_data
```

## Important Notes

- **Source Country**: Use `crm_data.phone_country` or `lead_requirements.nationality`
- **Destination Country**: Use `crm_data.location_country` or `lead_requirements.location`
- **Date Fields**: `created_at` (TIMESTAMP), `move_in_date` (TEXT, YYYY-MM-DD)
- **Status Values**: 'Won', 'Lost', 'Opportunity', 'Contacted', 'Disputed'

## Common Queries

```sql
-- Leads by source country
SELECT COALESCE(c.phone_country, lr.nationality) as source_country, COUNT(*)
FROM leads l
LEFT JOIN lead_requirements lr ON l.lead_id = lr.lead_id
LEFT JOIN crm_data c ON l.lead_id = c.lead_id
GROUP BY source_country;

-- Won leads with details
SELECT l.*, lr.*, c.phone_country
FROM leads l
JOIN lead_requirements lr ON l.lead_id = lr.lead_id
LEFT JOIN crm_data c ON l.lead_id = c.lead_id
WHERE l.status = 'Won';
```
