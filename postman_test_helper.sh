#!/bin/bash
# Quick Contract API Test Script for Postman
# Run this to get current contract IDs and test the API

echo "🚀 InfluencerFlow Contract API Quick Test"
echo "========================================"

BASE_URL="http://localhost:8000"

echo ""
echo "📋 1. Listing all contracts..."
curl -s -X GET "$BASE_URL/api/v1/contracts/" | python3 -m json.tool

echo ""
echo "📄 2. Getting first contract details..."
# Get the first contract ID
CONTRACT_ID=$(curl -s -X GET "$BASE_URL/api/v1/contracts/" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['contracts']:
    print(data['contracts'][0]['contract_id'])
else:
    print('No contracts found')
")

if [ "$CONTRACT_ID" != "No contracts found" ]; then
    echo "Contract ID: $CONTRACT_ID"
    
    echo ""
    echo "🔍 3. Contract details:"
    curl -s -X GET "$BASE_URL/api/v1/contracts/$CONTRACT_ID" | python3 -m json.tool
    
    echo ""
    echo "✍️  4. Contract signature status:"
    curl -s -X GET "$BASE_URL/api/v1/contracts/$CONTRACT_ID/status" | python3 -m json.tool
    
    echo ""
    echo "📱 POSTMAN READY URLs:"
    echo "GET  $BASE_URL/api/v1/contracts/"
    echo "GET  $BASE_URL/api/v1/contracts/$CONTRACT_ID"
    echo "GET  $BASE_URL/api/v1/contracts/$CONTRACT_ID/view"
    echo "GET  $BASE_URL/api/v1/contracts/$CONTRACT_ID/status"
    echo "POST $BASE_URL/api/v1/contracts/$CONTRACT_ID/sign"
    
else
    echo "No contracts available. Start a negotiation first!"
fi
