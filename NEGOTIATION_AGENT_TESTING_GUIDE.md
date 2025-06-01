# 🤝 NEGOTIATION AGENT API - QUICK TESTING GUIDE

## 📋 Overview
Complete API testing suite for the Influencer Negotiation Agent with Supabase logging.

**Server URL:** `http://localhost:8000`
**API Base Path:** `/negotiation-agent`

## 🚀 Quick Start

### 1. Import Postman Collection
1. Open Postman
2. Click "Import" → "Upload Files"
3. Select `negotiation_agent_postman_collection.json`
4. The collection will include all endpoints with sample data

### 2. Set Environment Variables
In Postman, create these environment variables:
- `base_url`: `http://localhost:8000`
- `session_id`: (will be auto-set from responses)

### 3. Run Test Workflow

#### Complete Negotiation Flow:
1. **Start Negotiation** → Save `session_id`
2. **Continue Negotiation** (multiple rounds)
3. **Update Deliverables/Budget** (if needed)
4. **Generate Contract** (when agreed)
5. **Get Analytics** and **Export Data**

## 📊 Key Endpoints

### Core Negotiation
- `POST /start` - Start new negotiation session
- `POST /continue` - Send influencer messages
- `GET /session/{id}/summary` - Get session overview

### Session Management
- `GET /sessions` - List all sessions
- `GET /session/{id}/conversation` - Get full chat history
- `GET /session/{id}/export` - Export session data

### Deliverables & Budget
- `PUT /session/{id}/deliverables` - Update content requirements
- `PUT /session/{id}/budget` - Modify budget allocation

### Contract Generation
- `POST /session/{id}/generate-contract` - Create contract
- `GET /session/{id}/contract` - Retrieve contract details

### Analytics
- `GET /analytics/session/{id}` - Individual session metrics
- `GET /analytics/global` - Overall system analytics

## 🧪 Sample Test Scenarios

### 1. Standard Negotiation
```json
Brand: TechFlow Solutions (₹75,000 budget)
Influencer: TechGuru_Priya (185K followers, 4.8% engagement)
Expected: Successful negotiation around ₹78,000
```

### 2. High-Budget Campaign
```json
Brand: Premium Luxury Brand (₹250,000 budget)
Influencer: LuxuryLifestyle_Maya (500K followers, 6.2% engagement)
Expected: Premium pricing with extensive deliverables
```

### 3. Micro-Influencer Deal
```json
Brand: Local Food Startup (₹15,000 budget)
Influencer: MumbaiFoodie_Raj (25K followers, 7.8% engagement)
Expected: Cost-effective local campaign
```

## 💡 Testing Tips

### Conversation Testing
Test these influencer responses:
- **Interested**: "I'm interested! My rates are ₹X for this scope."
- **Counter Offer**: "Could we meet at ₹Y instead?"
- **Agreement**: "Perfect! Let's create the contract."
- **Rejection**: "This won't work for me, thanks anyway."

### Budget Constraints
- Test offers within budget (should accept)
- Test offers above max budget (should negotiate down)
- Test budget updates (should recalculate limits)

### Error Scenarios
- Invalid session IDs
- Missing required fields
- Negative budget values
- Empty message content

## 📈 Expected Response Formats

### Start Negotiation Response
```json
{
  "session_id": "uuid-string",
  "message": "Agent's opening message",
  "status": "active",
  "market_research": "Real-time market analysis"
}
```

### Continue Negotiation Response
```json
{
  "response": "Agent's response to influencer",
  "session_status": "active|completed|failed",
  "current_offer": 75000,
  "negotiation_round": 2
}
```

### Session Analytics Response
```json
{
  "session_id": "uuid-string",
  "brand": "Brand Name",
  "influencer": "Influencer Name",
  "status": "active",
  "current_offer": 75000,
  "budget_utilization": "85.0%",
  "message_count": 6,
  "created_at": "2025-06-01T10:00:00Z"
}
```

## 🔍 Monitoring & Debugging

### Check Logs
- Server logs show negotiation progress
- Supabase logs track all database operations
- Response times and error rates

### Validate Data
- Check `negotiation_sessions` table in Supabase
- Verify `conversation_messages` are being logged
- Confirm `contracts` are generated properly

### Performance Metrics
- Response times should be < 5 seconds
- Market research calls should complete < 10 seconds
- Database operations should be < 1 second

## 🚨 Common Issues

### Import Errors
- Ensure all dependencies are installed
- Check environment variables (Google API, Supabase)
- Verify database schema is created

### API Errors
- 404: Endpoint not found (check URL path)
- 422: Validation error (check request body)
- 500: Server error (check logs)

### Database Issues
- Connection errors: Check Supabase credentials
- Permission errors: Verify RLS policies
- Schema errors: Run `create_negotiation_agent_tables.sql`

## 📞 Support
- Check server logs for detailed error messages
- Verify Supabase connection and tables
- Test individual endpoints before workflows
- Use Postman's built-in tests for validation

---

**Ready to test! 🎉**
Start with the "Health Check" endpoint, then proceed with the complete negotiation workflow.
