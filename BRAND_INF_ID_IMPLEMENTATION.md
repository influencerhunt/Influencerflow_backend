# Brand ID and Influencer ID Storage Implementation

## Overview
This implementation adds support for storing and querying brand_id and inf_id in the negotiation system database, enabling better tracking and analytics for brands and influencers.

## Changes Made

### 1. Database Schema Updates
- **File**: `add_brand_inf_id_columns.sql`
- Added `brand_id` and `inf_id` columns to the `negotiation_sessions` table
- Created indexes for better query performance
- Added composite index for brand_id + inf_id queries

### 2. Backend Code Updates

#### Supabase Manager (`app/services/supabase_manager.py`)
- Modified `create_negotiation_session_from_dicts()` to extract and save brand_id and inf_id as separate columns
- Added new query methods:
  - `get_sessions_by_brand_id(brand_id, limit)`
  - `get_sessions_by_inf_id(inf_id, limit)`
  - `get_sessions_by_brand_and_inf_id(brand_id, inf_id, limit)`
  - `get_brand_analytics(brand_id)`
  - `get_influencer_analytics(inf_id)`

#### API Endpoints (`app/routers/negotiation_agent.py`)
- Added new endpoints for querying sessions by IDs:
  - `GET /sessions/brand/{brand_id}` - Get all sessions for a brand
  - `GET /sessions/influencer/{inf_id}` - Get all sessions for an influencer
  - `GET /sessions/collaboration/{brand_id}/{inf_id}` - Get sessions between specific brand and influencer
- Added analytics endpoints:
  - `GET /analytics/brand/{brand_id}` - Get analytics for a specific brand
  - `GET /analytics/influencer/{inf_id}` - Get analytics for a specific influencer
- Updated existing endpoints to include brand_id and inf_id in responses:
  - `/sessions` endpoint now includes brand_id and inf_id
  - `/session/{session_id}/summary` endpoint includes brand_id and inf_id

### 3. Data Flow

#### When Creating a Session:
1. Brand details and influencer profile are validated
2. If brand_id or inf_id are not provided, UUIDs are generated automatically
3. Both IDs are stored in the JSON objects AND as separate columns
4. Session is created in database with all information

#### When Querying Sessions:
1. Sessions can be queried by session_id (existing functionality)
2. Sessions can now be queried by brand_id, inf_id, or both
3. Analytics can be generated for specific brands or influencers

## API Usage Examples

### Start Negotiation with Custom IDs
```bash
curl -X POST "http://localhost:8000/negotiation-agent/start" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_details": {
      "name": "Tech Corp",
      "budget": 5000,
      "brand_id": "brand_123",
      ...
    },
    "influencer_profile": {
      "name": "Tech Reviewer",
      "followers": 100000,
      "inf_id": "inf_456",
      ...
    }
  }'
```

### Query Sessions by Brand
```bash
curl "http://localhost:8000/negotiation-agent/sessions/brand/brand_123"
```

### Query Sessions by Influencer
```bash
curl "http://localhost:8000/negotiation-agent/sessions/influencer/inf_456"
```

### Query Collaboration History
```bash
curl "http://localhost:8000/negotiation-agent/sessions/collaboration/brand_123/inf_456"
```

### Get Brand Analytics
```bash
curl "http://localhost:8000/negotiation-agent/analytics/brand/brand_123"
```

### Get Influencer Analytics
```bash
curl "http://localhost:8000/negotiation-agent/analytics/influencer/inf_456"
```

## Database Setup

Run the following SQL to add the new columns:

```sql
-- Add brand_id and inf_id columns
ALTER TABLE negotiation_sessions 
ADD COLUMN IF NOT EXISTS brand_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS inf_id VARCHAR(255);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_brand_id ON negotiation_sessions(brand_id);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_inf_id ON negotiation_sessions(inf_id);
CREATE INDEX IF NOT EXISTS idx_negotiation_sessions_brand_inf ON negotiation_sessions(brand_id, inf_id);
```

## Testing

Use the provided test script to verify functionality:

```bash
./test_brand_inf_id_storage.sh
```

This script will:
1. Create a negotiation with custom brand_id and inf_id
2. Verify the IDs are saved correctly
3. Test all new query endpoints
4. Test analytics endpoints

## Benefits

1. **Better Organization**: Sessions can be grouped by brand or influencer
2. **Enhanced Analytics**: Generate specific metrics for brands and influencers
3. **Relationship Tracking**: Track collaboration history between brands and influencers
4. **Performance**: Indexed columns enable fast queries
5. **Backwards Compatibility**: Existing functionality remains unchanged

## Error Handling

- If brand_id or inf_id are not provided, UUIDs are automatically generated
- All existing sessions continue to work normally
- New columns are nullable to support existing data
- Validation ensures proper data types and formats

## Future Enhancements

1. Add more sophisticated analytics (conversion rates, ROI, etc.)
2. Implement brand/influencer relationship scoring
3. Add notification systems for brands/influencers
4. Create dashboard views for brand/influencer management
