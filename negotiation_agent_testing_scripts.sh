#!/bin/bash

# ==================================================================================
# COMPREHENSIVE NEGOTIATION AGENT API TESTING SCRIPTS
# ==================================================================================
# 
# This script provides complete curl commands for testing all negotiation agent endpoints
# with full Supabase logging functionality.
#
# Prerequisites:
# 1. Server running on http://localhost:8000
# 2. Supabase database tables created (run create_negotiation_agent_tables.sql)
# 3. Environment variables configured
#
# Usage:
# 1. Start server: python -m uvicorn main:app --reload --port 8000
# 2. Run individual commands or use this script
# 3. Check Supabase dashboard for logged data
#
# ==================================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Server configuration
BASE_URL="http://localhost:8000"
API_PREFIX="/api/v1/negotiation-agent"

echo -e "${CYAN}🚀 InfluencerFlow Negotiation Agent API Test Suite${NC}"
echo -e "${CYAN}=====================================================${NC}"
echo ""
echo -e "${YELLOW}📋 Server: $BASE_URL$API_PREFIX${NC}"
echo -e "${YELLOW}📅 Date: $(date)${NC}"
echo ""

# Test server health first
echo -e "${BLUE}🏥 TESTING SERVER HEALTH${NC}"
echo "curl -X GET \"$BASE_URL$API_PREFIX/health\""
echo ""

# ==================== CORE NEGOTIATION ENDPOINTS ====================

echo -e "${GREEN}==================== CORE NEGOTIATION ENDPOINTS ====================${NC}"
echo ""

echo -e "${PURPLE}1️⃣ START NEW NEGOTIATION${NC}"
cat << 'EOF'
curl -X POST "http://localhost:8000/api/v1/negotiation-agent/start" \
-H "Content-Type: application/json" \
-d '{
  "brand_details": {
    "name": "EcoTech Solutions",
    "budget": 8000.0,
    "budget_currency": "USD",
    "goals": ["brand awareness", "product launch", "engagement boost"],
    "target_platforms": ["instagram", "youtube"],
    "content_requirements": {
      "instagram_post": 4,
      "instagram_reel": 3,
      "youtube_shorts": 2
    },
    "campaign_duration_days": 45,
    "target_audience": "Tech-savvy millennials interested in sustainability",
    "brand_guidelines": "Authentic, educational content focusing on environmental impact",
    "brand_location": "US"
  },
  "influencer_profile": {
    "name": "Alex Green",
    "followers": 75000,
    "engagement_rate": 0.065,
    "location": "US",
    "platforms": ["instagram", "youtube"],
    "niches": ["sustainability", "technology", "lifestyle"],
    "previous_brand_collaborations": 12
  },
  "user_id": "test-user-123"
}'
EOF
echo ""
echo ""

echo -e "${PURPLE}2️⃣ CONTINUE CONVERSATION${NC}"
echo "# Replace SESSION_ID with actual session ID from start response"
cat << 'EOF'
curl -X POST "http://localhost:8000/api/v1/negotiation-agent/continue" \
-H "Content-Type: application/json" \
-d '{
  "session_id": "SESSION_ID",
  "user_input": "The pricing looks great! I love the breakdown you provided. Can we discuss the timeline and when we could start this campaign?",
  "user_id": "test-user-123"
}'
EOF
echo ""
echo ""

echo -e "${PURPLE}3️⃣ GET NEGOTIATION SUMMARY${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/session/SESSION_ID/summary" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

# ==================== DELIVERABLES MANAGEMENT ====================

echo -e "${GREEN}==================== DELIVERABLES MANAGEMENT ====================${NC}"
echo ""

echo -e "${PURPLE}4️⃣ UPDATE DELIVERABLES${NC}"
cat << 'EOF'
curl -X PUT "http://localhost:8000/api/v1/negotiation-agent/session/SESSION_ID/deliverables" \
-H "Content-Type: application/json" \
-d '{
  "session_id": "SESSION_ID",
  "deliverables": [
    {
      "platform": "instagram",
      "content_type": "post",
      "quantity": 4,
      "description": "High-quality posts showcasing eco-friendly tech products",
      "specifications": {
        "format": "photo+caption",
        "hashtags_required": true,
        "brand_mention": true,
        "posting_schedule": "weekly"
      },
      "rate_per_deliverable": 200,
      "total_rate": 800
    },
    {
      "platform": "instagram",
      "content_type": "reel",
      "quantity": 3,
      "description": "Engaging reels demonstrating product features",
      "specifications": {
        "duration": "30-60 seconds",
        "music": "brand-approved",
        "call_to_action": true
      },
      "rate_per_deliverable": 350,
      "total_rate": 1050
    },
    {
      "platform": "youtube",
      "content_type": "shorts",
      "quantity": 2,
      "description": "YouTube Shorts highlighting sustainability benefits",
      "specifications": {
        "duration": "under 60 seconds",
        "vertical_format": true,
        "hook_within_3_seconds": true
      },
      "rate_per_deliverable": 400,
      "total_rate": 800
    }
  ]
}'
EOF
echo ""
echo ""

echo -e "${PURPLE}5️⃣ GET DELIVERABLES${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/session/SESSION_ID/deliverables" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

# ==================== BUDGET MANAGEMENT ====================

echo -e "${GREEN}==================== BUDGET MANAGEMENT ====================${NC}"
echo ""

echo -e "${PURPLE}6️⃣ UPDATE BUDGET${NC}"
cat << 'EOF'
curl -X PUT "http://localhost:8000/api/v1/negotiation-agent/session/SESSION_ID/budget" \
-H "Content-Type: application/json" \
-d '{
  "session_id": "SESSION_ID",
  "new_budget": 9500.0,
  "currency": "USD",
  "change_reason": "Increased budget due to excellent proposal and potential for high ROI"
}'
EOF
echo ""
echo ""

# ==================== CONTRACT MANAGEMENT ====================

echo -e "${GREEN}==================== CONTRACT MANAGEMENT ====================${NC}"
echo ""

echo -e "${PURPLE}7️⃣ GENERATE CONTRACT${NC}"
cat << 'EOF'
curl -X POST "http://localhost:8000/api/v1/negotiation-agent/session/SESSION_ID/generate-contract" \
-H "Content-Type: application/json" \
-d '{
  "session_id": "SESSION_ID",
  "brand_contact_email": "legal@ecotechsolutions.com",
  "brand_contact_name": "Sarah Johnson - Legal Team",
  "influencer_contact": "+1-555-0123"
}'
EOF
echo ""
echo ""

echo -e "${PURPLE}8️⃣ GET CONTRACT INFO${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/session/SESSION_ID/contract" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

# ==================== ANALYTICS & REPORTING ====================

echo -e "${GREEN}==================== ANALYTICS & REPORTING ====================${NC}"
echo ""

echo -e "${PURPLE}9️⃣ GET SESSION ANALYTICS${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/analytics/session/SESSION_ID" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

echo -e "${PURPLE}🔟 GET GLOBAL ANALYTICS${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/analytics/global" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

echo -e "${PURPLE}1️⃣1️⃣ GET ANALYTICS DASHBOARD${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/analytics/dashboard" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

# ==================== SESSION MANAGEMENT ====================

echo -e "${GREEN}==================== SESSION MANAGEMENT ====================${NC}"
echo ""

echo -e "${PURPLE}1️⃣2️⃣ LIST ALL SESSIONS${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/sessions?active_only=true&limit=20&offset=0" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

echo -e "${PURPLE}1️⃣3️⃣ ARCHIVE SESSION${NC}"
cat << 'EOF'
curl -X PUT "http://localhost:8000/api/v1/negotiation-agent/session/SESSION_ID/archive" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

echo -e "${PURPLE}1️⃣4️⃣ DELETE SESSION${NC}"
echo "⚠️  WARNING: This permanently deletes the session and all related data!"
cat << 'EOF'
curl -X DELETE "http://localhost:8000/api/v1/negotiation-agent/session/SESSION_ID" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

# ==================== UTILITY ENDPOINTS ====================

echo -e "${GREEN}==================== UTILITY ENDPOINTS ====================${NC}"
echo ""

echo -e "${PURPLE}1️⃣5️⃣ GET PLATFORM DETAILS${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/platforms" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

echo -e "${PURPLE}1️⃣6️⃣ GET SUPPORTED LOCATIONS${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/locations" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

echo -e "${PURPLE}1️⃣7️⃣ HEALTH CHECK${NC}"
cat << 'EOF'
curl -X GET "http://localhost:8000/api/v1/negotiation-agent/health" \
-H "Content-Type: application/json"
EOF
echo ""
echo ""

# ==================== ADVANCED TESTING SCENARIOS ====================

echo -e "${GREEN}==================== ADVANCED TESTING SCENARIOS ====================${NC}"
echo ""

echo -e "${YELLOW}🧪 SCENARIO 1: COMPLETE NEGOTIATION FLOW${NC}"
echo "Run these commands in sequence:"
echo ""
echo "1. Start negotiation (copy session_id from response)"
echo "2. Continue conversation 2-3 times with different inputs"
echo "3. Update deliverables"
echo "4. Update budget"
echo "5. Generate contract"
echo "6. Get session analytics"
echo "7. Archive session"
echo ""

echo -e "${YELLOW}🧪 SCENARIO 2: BUDGET CONSTRAINT TESTING${NC}"
cat << 'EOF'
# Test with very low budget
curl -X POST "http://localhost:8000/api/v1/negotiation-agent/start" \
-H "Content-Type: application/json" \
-d '{
  "brand_details": {
    "name": "StartupCorp",
    "budget": 500.0,
    "budget_currency": "USD",
    "goals": ["brand awareness"],
    "target_platforms": ["instagram"],
    "content_requirements": {"instagram_post": 2},
    "campaign_duration_days": 30,
    "target_audience": "Young professionals",
    "brand_location": "US"
  },
  "influencer_profile": {
    "name": "Micro Influencer",
    "followers": 10000,
    "engagement_rate": 0.08,
    "location": "US",
    "platforms": ["instagram"],
    "niches": ["lifestyle"],
    "previous_brand_collaborations": 3
  }
}'
EOF
echo ""
echo ""

echo -e "${YELLOW}🧪 SCENARIO 3: INTERNATIONAL NEGOTIATION${NC}"
cat << 'EOF'
# Test with different location and currency
curl -X POST "http://localhost:8000/api/v1/negotiation-agent/start" \
-H "Content-Type: application/json" \
-d '{
  "brand_details": {
    "name": "Global Fashion Brand",
    "budget": 2500.0,
    "budget_currency": "EUR",
    "goals": ["brand awareness", "engagement"],
    "target_platforms": ["instagram", "tiktok"],
    "content_requirements": {
      "instagram_post": 3,
      "tiktok_video": 2
    },
    "campaign_duration_days": 30,
    "target_audience": "Fashion-forward millennials",
    "brand_location": "GERMANY"
  },
  "influencer_profile": {
    "name": "European Fashion Influencer",
    "followers": 50000,
    "engagement_rate": 0.055,
    "location": "GERMANY",
    "platforms": ["instagram", "tiktok"],
    "niches": ["fashion", "lifestyle"],
    "previous_brand_collaborations": 8
  }
}'
EOF
echo ""
echo ""

# ==================== POSTMAN COLLECTION ====================

echo -e "${GREEN}==================== POSTMAN COLLECTION ====================${NC}"
echo ""
echo -e "${CYAN}📦 For easier testing, import the Postman collection:${NC}"
echo ""
echo "1. Open Postman"
echo "2. Click Import"
echo "3. Copy and paste this URL or import the generated JSON file:"
echo "   File: negotiation_agent_postman_collection.json"
echo ""
echo -e "${CYAN}🌐 OR use the interactive API docs:${NC}"
echo "   http://localhost:8000/docs"
echo ""

# ==================== SUPABASE VERIFICATION ====================

echo -e "${GREEN}==================== SUPABASE VERIFICATION ====================${NC}"
echo ""
echo -e "${CYAN}📊 After running tests, verify data in Supabase:${NC}"
echo ""
echo "1. Check negotiation_sessions table for session data"
echo "2. Check negotiation_operations table for logged operations"
echo "3. Check conversation_messages table for chat history"
echo "4. Check contracts table for generated contracts"
echo "5. Use the analytics views:"
echo "   - SELECT * FROM session_analytics;"
echo "   - SELECT * FROM operation_analytics;"
echo ""

# ==================== TROUBLESHOOTING ====================

echo -e "${GREEN}==================== TROUBLESHOOTING ====================${NC}"
echo ""
echo -e "${RED}❌ Common Issues:${NC}"
echo ""
echo "1. 404 Not Found:"
echo "   - Check if server is running on correct port"
echo "   - Verify router is included in main.py"
echo ""
echo "2. 500 Internal Server Error:"
echo "   - Check server logs for detailed error"
echo "   - Verify Supabase connection"
echo "   - Check database tables exist"
echo ""
echo "3. Import Errors:"
echo "   - Check all dependencies are installed"
echo "   - Verify agent.py file has required methods"
echo ""
echo "4. Supabase Errors:"
echo "   - Verify environment variables"
echo "   - Check database schema"
echo "   - Test Supabase connection separately"
echo ""

# ==================== COMPLETION ====================

echo -e "${CYAN}=====================================================${NC}"
echo -e "${GREEN}✅ Negotiation Agent API Test Suite Ready!${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Start your server: python -m uvicorn main:app --reload --port 8000"
echo "2. Run the health check first"
echo "3. Start with the basic negotiation flow"
echo "4. Check Supabase for logged data"
echo "5. Use analytics endpoints to monitor usage"
echo ""
echo -e "${CYAN}🎉 Happy Testing!${NC}"
echo ""
