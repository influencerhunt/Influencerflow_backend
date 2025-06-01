#!/bin/bash

# ====================================================================
# NEGOTIATION AGENT API - COMPREHENSIVE CURL TESTING SCRIPTS
# ====================================================================
# Server URL: http://localhost:8000
# Date: June 1, 2025
# 
# Use these curl commands in Postman or terminal to test all endpoints
# ====================================================================

BASE_URL="http://localhost:8000/api/v1"

echo "🤝 NEGOTIATION AGENT API TESTING SCRIPTS"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# ====================================================================
# 1. HEALTH CHECK
# ====================================================================
echo "1️⃣ HEALTH CHECK"
echo "curl -X GET '$BASE_URL/negotiation-agent/health'"
echo ""

# ====================================================================
# 2. GET SUPPORTED PLATFORMS
# ====================================================================
echo "2️⃣ GET SUPPORTED PLATFORMS"
echo "curl -X GET '$BASE_URL/negotiation-agent/platforms'"
echo ""

# ====================================================================
# 3. GET SUPPORTED LOCATIONS
# ====================================================================
echo "3️⃣ GET SUPPORTED LOCATIONS"
echo "curl -X GET '$BASE_URL/negotiation-agent/locations'"
echo ""

# ====================================================================
# 4. START NEGOTIATION SESSION
# ====================================================================
echo "4️⃣ START NEGOTIATION SESSION"
echo "curl -X POST '$BASE_URL/negotiation-agent/start' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"brand_details\": {"
echo "      \"name\": \"TechFlow Solutions\","
echo "      \"budget\": 75000,"
echo "      \"budget_currency\": \"INR\","
echo "      \"goals\": [\"brand awareness\", \"product launch\", \"engagement boost\"],"
echo "      \"target_platforms\": [\"instagram\", \"youtube\"],"
echo "      \"content_requirements\": {"
echo "        \"posts\": 4,"
echo "        \"stories\": 8,"
echo "        \"reels\": 3"
echo "      },"
echo "      \"campaign_duration_days\": 30,"
echo "      \"target_audience\": \"Tech-savvy millennials and Gen Z\","
echo "      \"brand_guidelines\": \"Modern, professional, tech-focused content with authentic storytelling\","
echo "      \"brand_location\": \"india\""
echo "    },"
echo "    \"influencer_profile\": {"
echo "      \"name\": \"TechGuru_Priya\","
echo "      \"followers\": 185000,"
echo "      \"engagement_rate\": 4.8,"
echo "      \"location\": \"india\","
echo "      \"platforms\": [\"instagram\", \"youtube\", \"linkedin\"],"
echo "      \"niches\": [\"technology\", \"gadgets\", \"lifestyle\"],"
echo "      \"previous_brand_collaborations\": 32"
echo "    }"
echo "  }'"
echo ""

# ====================================================================
# 5. CONTINUE NEGOTIATION
# ====================================================================
echo "5️⃣ CONTINUE NEGOTIATION"
echo "curl -X POST '$BASE_URL/negotiation-agent/continue' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"session_id\": \"YOUR_SESSION_ID_HERE\","
echo "    \"message\": \"Hi! Thanks for reaching out. I'm interested in this collaboration. For this scope of work, my rates are typically ₹85,000 for the complete package. What do you think?\""
echo "  }'"
echo ""

# ====================================================================
# 6. GET SESSION SUMMARY
# ====================================================================
echo "6️⃣ GET SESSION SUMMARY"
echo "curl -X GET '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE/summary'"
echo ""

# ====================================================================
# 7. UPDATE DELIVERABLES
# ====================================================================
echo "7️⃣ UPDATE DELIVERABLES"
echo "curl -X PUT '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE/deliverables' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"deliverables\": {"
echo "      \"posts\": 5,"
echo "      \"stories\": 10,"
echo "      \"reels\": 4,"
echo "      \"youtube_videos\": 1"
echo "    },"
echo "    \"notes\": \"Updated deliverables based on influencer feedback\""
echo "  }'"
echo ""

# ====================================================================
# 8. UPDATE BUDGET
# ====================================================================
echo "8️⃣ UPDATE BUDGET"
echo "curl -X PUT '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE/budget' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"new_budget\": 90000,"
echo "    \"reason\": \"Increased budget due to additional deliverables and high engagement rates\","
echo "    \"approved_by\": \"Brand Manager\""
echo "  }'"
echo ""

# ====================================================================
# 9. GENERATE CONTRACT
# ====================================================================
echo "9️⃣ GENERATE CONTRACT"
echo "curl -X POST '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE/generate-contract' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"final_amount\": 85000,"
echo "    \"payment_terms\": \"50% advance, 50% upon completion\","
echo "    \"additional_terms\": \"Content approval required before posting, usage rights for 1 year\""
echo "  }'"
echo ""

# ====================================================================
# 10. GET CONTRACT
# ====================================================================
echo "🔟 GET CONTRACT"
echo "curl -X GET '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE/contract'"
echo ""

# ====================================================================
# 11. SESSION ANALYTICS
# ====================================================================
echo "1️⃣1️⃣ SESSION ANALYTICS"
echo "curl -X GET '$BASE_URL/negotiation-agent/analytics/session/YOUR_SESSION_ID_HERE'"
echo ""

# ====================================================================
# 12. GLOBAL ANALYTICS
# ====================================================================
echo "1️⃣2️⃣ GLOBAL ANALYTICS"
echo "curl -X GET '$BASE_URL/negotiation-agent/analytics/global'"
echo ""

# ====================================================================
# 13. LIST ALL SESSIONS
# ====================================================================
echo "1️⃣3️⃣ LIST ALL SESSIONS"
echo "curl -X GET '$BASE_URL/negotiation-agent/sessions?limit=10&offset=0&status=active'"
echo ""

# ====================================================================
# 14. DELETE SESSION
# ====================================================================
echo "1️⃣4️⃣ DELETE SESSION"
echo "curl -X DELETE '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE'"
echo ""

# ====================================================================
# 15. ARCHIVE SESSION
# ====================================================================
echo "1️⃣5️⃣ ARCHIVE SESSION"
echo "curl -X POST '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE/archive' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"reason\": \"Campaign completed successfully\""
echo "  }'"
echo ""

# ====================================================================
# 16. EXPORT SESSION DATA
# ====================================================================
echo "1️⃣6️⃣ EXPORT SESSION DATA"
echo "curl -X GET '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE/export'"
echo ""

# ====================================================================
# 17. CONVERSATION HISTORY
# ====================================================================
echo "1️⃣7️⃣ GET CONVERSATION HISTORY"
echo "curl -X GET '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE/conversation'"
echo ""

# ====================================================================
# SAMPLE WORKFLOW COMMANDS
# ====================================================================
echo ""
echo "📋 SAMPLE WORKFLOW:"
echo "==================="
echo ""
echo "Step 1: Start a negotiation session (save the session_id from response)"
echo "Step 2: Continue negotiation with influencer messages"
echo "Step 3: Update deliverables or budget if needed"
echo "Step 4: Generate contract when agreement is reached"
echo "Step 5: Get session analytics and export data"
echo ""

# ====================================================================
# POSTMAN COLLECTION VARIABLES
# ====================================================================
echo ""
echo "📬 POSTMAN COLLECTION VARIABLES:"
echo "================================="
echo "Set these variables in your Postman environment:"
echo ""
echo "- base_url: http://localhost:8000"
echo "- session_id: {{session_id}} (use from start negotiation response)"
echo ""

# ====================================================================
# SAMPLE RESPONSES
# ====================================================================
echo ""
echo "📄 EXPECTED RESPONSE FORMATS:"
echo "=============================="
echo ""
echo "Start Negotiation Response:"
echo "{"
echo "  \"session_id\": \"uuid-here\","
echo "  \"message\": \"Agent's opening message\","
echo "  \"status\": \"active\","
echo "  \"market_research\": \"Research data\""
echo "}"
echo ""
echo "Continue Negotiation Response:"
echo "{"
echo "  \"response\": \"Agent's response\","
echo "  \"session_status\": \"active\","
echo "  \"current_offer\": 75000,"
echo "  \"negotiation_round\": 2"
echo "}"
echo ""
echo "Session Summary Response:"
echo "{"
echo "  \"session_id\": \"uuid-here\","
echo "  \"brand\": \"TechFlow Solutions\","
echo "  \"influencer\": \"TechGuru_Priya\","
echo "  \"status\": \"active\","
echo "  \"current_offer\": 75000,"
echo "  \"budget_utilization\": \"85.0%\","
echo "  \"message_count\": 6"
echo "}"
echo ""

# ====================================================================
# ERROR TESTING COMMANDS
# ====================================================================
echo ""
echo "🚨 ERROR TESTING COMMANDS:"
echo "=========================="
echo ""
echo "Test invalid session ID:"
echo "curl -X GET '$BASE_URL/negotiation-agent/session/invalid-id/summary'"
echo ""
echo "Test missing required fields:"
echo "curl -X POST '$BASE_URL/negotiation-agent/start' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"brand_details\": {\"name\": \"Test\"}}'"
echo ""
echo "Test invalid budget update:"
echo "curl -X PUT '$BASE_URL/negotiation-agent/session/YOUR_SESSION_ID_HERE/budget' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"new_budget\": -1000}'"
echo ""

echo ""
echo "✅ CURL SCRIPTS READY!"
echo "Copy and paste these commands into Postman or run them in terminal"
echo "Replace 'YOUR_SESSION_ID_HERE' with actual session IDs from responses"
echo ""
