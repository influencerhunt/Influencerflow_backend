#!/usr/bin/env python3
"""
Test complete contract flow and generate curl commands
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_handler import ConversationHandler
from app.services.contract_service import contract_service
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, 
    ContentType, LocationType, NegotiationStatus
)
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_contract_flow():
    """Test complete contract generation and management flow"""
    
    # Create test data
    brand = BrandDetails(
        name="TechCorp",
        brand_location=LocationType.US,
        budget=5000.0,
        goals=["brand_awareness", "engagement"],
        target_platforms=[PlatformType.INSTAGRAM],
        content_requirements={PlatformType.INSTAGRAM: [ContentType.INSTAGRAM_POST, ContentType.INSTAGRAM_REEL]},
        campaign_duration_days=30
    )
    
    influencer = InfluencerProfile(
        name="TechInfluencer",
        location=LocationType.US,
        followers=150000,
        engagement_rate=0.035,
        platforms=[PlatformType.INSTAGRAM]
    )
    
    # Create conversation handler
    handler = ConversationHandler()
    
    try:
        print("🎯 Starting Complete Contract Flow Test...")
        
        # Step 1: Create session and negotiate
        session_id = handler.create_session(brand, influencer)
        print(f"✅ Session created: {session_id}")
        
        # Step 2: Generate proposal
        proposal = handler.generate_proposal(session_id)
        print(f"✅ Proposal generated")
        
        # Step 3: Accept offer (triggers contract generation)
        acceptance_response = handler._handle_acceptance(session_id)
        print(f"✅ Acceptance handled - Contract generated!")
        
        # Step 4: Extract contract ID from response
        contract_id = None
        if "Contract ID" in acceptance_response:
            lines = acceptance_response.split('\n')
            for line in lines:
                if "Contract ID:" in line:
                    contract_id = line.split('`')[1]
                    break
        
        if not contract_id:
            print("❌ Could not extract contract ID from response")
            return
            
        print(f"📄 Contract ID: {contract_id}")
        
        # Step 5: Test contract service methods
        print("\n🔍 Testing Contract Service Methods:")
        
        # Get contract details
        contract = contract_service.get_contract(contract_id)
        if contract:
            print(f"✅ Contract retrieved: {contract.brand_name} x {contract.influencer_name}")
            print(f"   Status: {contract.status.value}")
            print(f"   Total: ${contract.total_amount}")
        
        # Get contract summary
        summary = contract_service.get_contract_summary(contract_id)
        print(f"✅ Contract summary: {summary['contract_id']}")
        
        # Test signing
        print("\n✍️ Testing Digital Signatures:")
        
        # Brand signs first
        signed_contract = contract_service.sign_contract(
            contract_id=contract_id,
            signer_type="brand",
            signer_name="TechCorp Legal Team",
            signer_email="legal@techcorp.com",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser"
        )
        print(f"✅ Brand signed - Status: {signed_contract.status.value}")
        
        # Influencer signs
        signed_contract = contract_service.sign_contract(
            contract_id=contract_id,
            signer_type="influencer", 
            signer_name="TechInfluencer",
            signer_email="tech.influencer@email.com",
            ip_address="192.168.1.101",
            user_agent="Mozilla/5.0 Test Browser"
        )
        print(f"✅ Influencer signed - Status: {signed_contract.status.value}")
        
        # Generate HTML content
        html_content = contract_service.generate_contract_pdf_content(contract_id)
        print(f"✅ Contract HTML generated ({len(html_content)} characters)")
        
        print("\n🎯 CONTRACT FLOW TEST COMPLETED SUCCESSFULLY!")
        
        # Generate curl commands for testing
        generate_curl_commands(contract_id)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def generate_curl_commands(contract_id):
    """Generate curl commands for testing contract API endpoints"""
    
    print(f"\n📝 CURL COMMANDS FOR POSTMAN TESTING:")
    print("=" * 60)
    
    # 1. Get contract details
    print("1️⃣ GET CONTRACT DETAILS:")
    print(f'curl -X GET "http://localhost:8000/api/v1/contracts/{contract_id}" \\')
    print('  -H "Content-Type: application/json"')
    
    print("\n2️⃣ GET CONTRACT SUMMARY:")
    print(f'curl -X GET "http://localhost:8000/api/v1/contracts/{contract_id}/summary" \\')
    print('  -H "Content-Type: application/json"')
    
    print("\n3️⃣ LIST ALL CONTRACTS:")
    print('curl -X GET "http://localhost:8000/api/v1/contracts" \\')
    print('  -H "Content-Type: application/json"')
    
    print("\n4️⃣ SIGN CONTRACT (Brand):")
    print(f'curl -X POST "http://localhost:8000/api/v1/contracts/{contract_id}/sign" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"signer_type": "brand", "signer_name": "Brand Legal Team", "signer_email": "legal@brand.com", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0"}\'')
    
    print("\n5️⃣ SIGN CONTRACT (Influencer):")
    print(f'curl -X POST "http://localhost:8000/api/v1/contracts/{contract_id}/sign" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"signer_type": "influencer", "signer_name": "Influencer Name", "signer_email": "influencer@email.com", "ip_address": "192.168.1.101", "user_agent": "Mozilla/5.0"}\'')
    
    print("\n6️⃣ GET CONTRACT PDF/HTML:")
    print(f'curl -X GET "http://localhost:8000/api/v1/contracts/{contract_id}/pdf" \\')
    print('  -H "Content-Type: application/json"')
    
    print("\n=" * 60)
    print("🚀 Copy these commands to Postman for testing!")
    print("💡 Make sure the server is running on http://localhost:8000")

if __name__ == "__main__":
    test_complete_contract_flow()
