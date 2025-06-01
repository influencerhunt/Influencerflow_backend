#!/bin/bash

# Quick test for brand_id and inf_id functionality
# Run this after starting your server

echo "Testing brand_id and inf_id storage..."

# Start a negotiation with specific IDs
curl -X POST "http://localhost:8000/negotiation-agent/start" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_details": {
      "name": "Test Brand",
      "budget": 5000,
      "budget_currency": "USD",
      "goals": ["brand awareness"],
      "target_platforms": ["instagram"],
      "content_requirements": {"instagram_post": 3},
      "campaign_duration_days": 30,
      "target_audience": "Tech enthusiasts",
      "brand_id": "test_brand_001"
    },
    "influencer_profile": {
      "name": "Test Influencer", 
      "followers": 50000,
      "engagement_rate": 0.05,
      "location": "US",
      "platforms": ["instagram"],
      "niches": ["technology"],
      "inf_id": "test_inf_001"
    }
  }'

echo -e "\n\n"
echo "Check your database to verify brand_id and inf_id are saved!"
echo "Or test the new endpoints:"
echo "- GET /negotiation-agent/sessions/brand/test_brand_001"
echo "- GET /negotiation-agent/sessions/influencer/test_inf_001"
