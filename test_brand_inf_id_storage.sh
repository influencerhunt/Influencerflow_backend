#!/bin/bash

# Test script to verify brand_id and inf_id are being saved correctly
# Make sure your server is running before executing this script

BASE_URL="http://localhost:8000"
API_URL="$BASE_URL/negotiation-agent"

echo "============================================="
echo "Testing Brand ID and Influencer ID Storage"
echo "============================================="

# Test 1: Start a negotiation with specific brand_id and inf_id
echo "Test 1: Starting negotiation with custom brand_id and inf_id..."

RESPONSE=$(curl -s -X POST "$API_URL/start" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_details": {
      "name": "Test Brand",
      "budget": 5000,
      "budget_currency": "USD", 
      "goals": ["brand awareness", "engagement"],
      "target_platforms": ["instagram", "youtube"],
      "content_requirements": {
        "instagram_post": 3,
        "youtube_shorts": 2
      },
      "campaign_duration_days": 30,
      "target_audience": "Tech enthusiasts aged 18-35",
      "brand_guidelines": "Authentic, professional content",
      "brand_location": "US",
      "brand_id": "brand_123_test"
    },
    "influencer_profile": {
      "name": "Test Influencer",
      "followers": 100000,
      "engagement_rate": 0.045,
      "location": "US",
      "platforms": ["instagram", "youtube"],
      "niches": ["technology", "lifestyle"],
      "previous_brand_collaborations": 5,
      "inf_id": "inf_456_test"
    },
    "user_id": "user_789_test"
  }')

# Extract session_id from response
SESSION_ID=$(echo $RESPONSE | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$SESSION_ID" ]; then
    echo "✅ Negotiation started successfully!"
    echo "📍 Session ID: $SESSION_ID"
    
    # Test 2: Get session summary to verify brand_id and inf_id are saved
    echo -e "\nTest 2: Getting session summary to verify IDs..."
    
    SUMMARY_RESPONSE=$(curl -s -X GET "$API_URL/session/$SESSION_ID/summary")
    
    # Check if brand_id and inf_id are in the response
    if echo "$SUMMARY_RESPONSE" | grep -q "brand_123_test" && echo "$SUMMARY_RESPONSE" | grep -q "inf_456_test"; then
        echo "✅ Brand ID and Influencer ID found in session summary!"
        echo "🔍 Summary response (partial):"
        echo "$SUMMARY_RESPONSE" | jq -r '.brand_id, .inf_id' 2>/dev/null || echo "Brand ID and Inf ID present in response"
    else
        echo "❌ Brand ID or Influencer ID not found in session summary"
        echo "📋 Full response: $SUMMARY_RESPONSE"
    fi
    
    # Test 3: Query sessions by brand_id
    echo -e "\nTest 3: Querying sessions by brand_id..."
    
    BRAND_SESSIONS=$(curl -s -X GET "$API_URL/sessions/brand/brand_123_test")
    
    if echo "$BRAND_SESSIONS" | grep -q "$SESSION_ID"; then
        echo "✅ Session found when querying by brand_id!"
        echo "📊 Brand sessions count: $(echo "$BRAND_SESSIONS" | jq -r '.total_count' 2>/dev/null || echo "1")"
    else
        echo "❌ Session not found when querying by brand_id"
        echo "📋 Brand sessions response: $BRAND_SESSIONS"
    fi
    
    # Test 4: Query sessions by inf_id
    echo -e "\nTest 4: Querying sessions by inf_id..."
    
    INF_SESSIONS=$(curl -s -X GET "$API_URL/sessions/influencer/inf_456_test")
    
    if echo "$INF_SESSIONS" | grep -q "$SESSION_ID"; then
        echo "✅ Session found when querying by inf_id!"
        echo "📊 Influencer sessions count: $(echo "$INF_SESSIONS" | jq -r '.total_count' 2>/dev/null || echo "1")"
    else
        echo "❌ Session not found when querying by inf_id"
        echo "📋 Influencer sessions response: $INF_SESSIONS"
    fi
    
    # Test 5: Query sessions by both brand_id and inf_id
    echo -e "\nTest 5: Querying sessions by both brand_id and inf_id..."
    
    COLLABORATION_SESSIONS=$(curl -s -X GET "$API_URL/sessions/collaboration/brand_123_test/inf_456_test")
    
    if echo "$COLLABORATION_SESSIONS" | grep -q "$SESSION_ID"; then
        echo "✅ Session found when querying by collaboration!"
        echo "📊 Collaboration sessions count: $(echo "$COLLABORATION_SESSIONS" | jq -r '.total_count' 2>/dev/null || echo "1")"
    else
        echo "❌ Session not found when querying by collaboration"
        echo "📋 Collaboration sessions response: $COLLABORATION_SESSIONS"
    fi
    
    # Test 6: Get brand analytics
    echo -e "\nTest 6: Getting brand analytics..."
    
    BRAND_ANALYTICS=$(curl -s -X GET "$API_URL/analytics/brand/brand_123_test")
    
    if echo "$BRAND_ANALYTICS" | grep -q "brand_analytics"; then
        echo "✅ Brand analytics retrieved successfully!"
        echo "📈 Total sessions for brand: $(echo "$BRAND_ANALYTICS" | jq -r '.brand_analytics.total_sessions' 2>/dev/null || echo "N/A")"
    else
        echo "❌ Failed to get brand analytics"
        echo "📋 Brand analytics response: $BRAND_ANALYTICS"
    fi
    
    # Test 7: Get influencer analytics  
    echo -e "\nTest 7: Getting influencer analytics..."
    
    INF_ANALYTICS=$(curl -s -X GET "$API_URL/analytics/influencer/inf_456_test")
    
    if echo "$INF_ANALYTICS" | grep -q "influencer_analytics"; then
        echo "✅ Influencer analytics retrieved successfully!"
        echo "📈 Total sessions for influencer: $(echo "$INF_ANALYTICS" | jq -r '.influencer_analytics.total_sessions' 2>/dev/null || echo "N/A")"
    else
        echo "❌ Failed to get influencer analytics"
        echo "📋 Influencer analytics response: $INF_ANALYTICS"
    fi
    
    echo -e "\n============================================="
    echo "Testing Complete!"
    echo "============================================="
    echo "📝 Session ID for manual verification: $SESSION_ID"
    echo "🔗 Brand ID: brand_123_test"
    echo "🔗 Influencer ID: inf_456_test"
    
else
    echo "❌ Failed to start negotiation"
    echo "📋 Response: $RESPONSE"
fi
