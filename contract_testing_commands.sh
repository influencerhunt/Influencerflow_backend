#!/bin/bash
# Contract System Testing Commands for Pecho "7️⃣ SIGN CONTRACT (Influencer):"
echo "curl -X POST \"http://localhost:8000/api/v1/contracts/$CONTRACT_ID/sign\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"signer_type\": \"influencer\", \"signer_name\": \"Influencer Name\", \"signer_email\": \"influencer@example.com\", \"ip_address\": \"192.168.1.101\", \"user_agent\": \"Mozilla/5.0\"}'"
echo ""

echo "8️⃣ GET CONTRACT STATUS:"# Make sure the FastAPI server is running: uvicorn main:app --reload

echo "🚀 InfluencerFlow Contract System - API Testing Commands"
echo "========================================================"
echo ""
echo "💡 Prerequisites:"
echo "   1. Start the server: uvicorn main:app --reload"
echo "   2. Server should be running on http://localhost:8000"
echo "   3. Copy and paste these commands into Postman or terminal"
echo ""

# Note: Replace CONTRACT_ID with actual contract ID from your test
CONTRACT_ID="16dbf6a4-6cd0-41af-a2fc-8caeb40e6201"

echo "📋 Test Contract ID: $CONTRACT_ID"
echo "(Replace with your actual contract ID from the system)"
echo ""

echo "1️⃣ GET CONTRACT DETAILS:"
echo "curl -X GET \"http://localhost:8000/api/v1/contracts/$CONTRACT_ID\" \\"
echo "  -H \"Content-Type: application/json\""
echo ""

echo "2️⃣ GET CONTRACT SUMMARY:"
echo "curl -X GET \"http://localhost:8000/api/v1/contracts/$CONTRACT_ID/summary\" \\"
echo "  -H \"Content-Type: application/json\""
echo ""

echo "3️⃣ LIST ALL CONTRACTS:"
echo "curl -X GET \"http://localhost:8000/api/v1/contracts\" \\"
echo "  -H \"Content-Type: application/json\""
echo ""

echo "4️⃣ GET CONTRACT HTML VIEW:"
echo "curl -X GET \"http://localhost:8000/api/v1/contracts/$CONTRACT_ID/view\" \\"
echo "  -H \"Content-Type: application/json\""
echo ""

echo "5️⃣ DOWNLOAD CONTRACT PDF:"
echo "curl -X GET \"http://localhost:8000/api/v1/contracts/$CONTRACT_ID/pdf\" \\"
echo "  -H \"Accept: application/pdf\" \\"
echo "  -o \"contract_$CONTRACT_ID.pdf\""
echo ""

echo "6️⃣ SIGN CONTRACT (Brand):"
echo "curl -X POST \"http://localhost:8000/api/v1/contracts/$CONTRACT_ID/sign\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"signer_type\": \"brand\", \"signer_name\": \"Brand Legal Team\", \"signer_email\": \"legal@brand.com\", \"ip_address\": \"192.168.1.100\", \"user_agent\": \"Mozilla/5.0\"}'"
echo ""

echo "7️⃣ SIGN CONTRACT (Influencer):"
echo "curl -X POST \"http://localhost:8000/api/v1/contracts/$CONTRACT_ID/sign\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"signer_type\": \"influencer\", \"signer_name\": \"Influencer Name\", \"signer_email\": \"influencer@email.com\", \"ip_address\": \"192.168.1.101\", \"user_agent\": \"Mozilla/5.0\"}'"
echo ""

echo "6️⃣ GET CONTRACT PDF/HTML:"
echo "curl -X GET \"http://localhost:8000/api/v1/contracts/$CONTRACT_ID/pdf\" \\"
echo "  -H \"Content-Type: application/json\""
echo ""

echo "========================================================"
echo "🎯 POSTMAN COLLECTION IMPORT:"
echo ""
echo "For easier testing, you can also visit:"
echo "http://localhost:8000/docs"
echo ""
echo "This will open the FastAPI Swagger documentation where you can"
echo "test all endpoints interactively!"
echo ""

echo "🔄 TESTING WORKFLOW:"
echo "1. First run the contract generation test to get a contract ID"
echo "2. Replace CONTRACT_ID in the commands above"
echo "3. Test each endpoint in sequence"
echo "4. Check contract status changes after signing"
echo ""

echo "💾 EXPECTED RESPONSES:"
echo "- Contract details: Full contract JSON object"
echo "- Summary: Simplified contract overview"
echo "- List: Array of all contracts"
echo "- Sign: Updated contract with signature"
echo "- PDF: HTML content for contract display"
