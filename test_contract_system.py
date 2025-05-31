#!/usr/bin/env python3
"""
Test Contract Generation and Digital Signing
Tests the complete flow from negotiation agreement to contract signing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, NegotiationOffer, ContentDeliverable,
    LocationType, PlatformType, ContentType, NegotiationStatus, ContractStatus
)
from app.services.conversation_handler import ConversationHandler
from app.services.contract_service import contract_service

def test_contract_generation():
    """Test contract generation when negotiation reaches AGREED status"""
    print("🔬 Testing Contract Generation System")
    print("=" * 60)
    
    # Create test data
    brand = BrandDetails(
        name="Mama Earth",
        budget=500.0,  # $500 USD
        goals=["brand awareness", "engagement"],
        target_platforms=[PlatformType.INSTAGRAM],
        content_requirements={
            "instagram_post": 3,
            "instagram_story": 2
        },
        campaign_duration_days=30,
        brand_location=LocationType.US
    )
    
    influencer = InfluencerProfile(
        name="Priya Sharma",
        followers=50000,
        engagement_rate=0.045,
        location=LocationType.INDIA,
        platforms=[PlatformType.INSTAGRAM],
        niches=["lifestyle", "wellness"]
    )
    
    # Initialize conversation handler
    handler = ConversationHandler()
    
    # Create session
    session_id = handler.create_session(brand, influencer)
    print(f"✅ Created negotiation session: {session_id}")
    
    # Generate proposal to create an offer
    proposal_msg = handler.generate_proposal(session_id)
    print(f"✅ Generated proposal")
    
    # Simulate user acceptance to trigger contract generation
    print("\n📝 Simulating user acceptance...")
    acceptance_msg = handler._handle_acceptance(session_id)
    print(f"✅ Acceptance handled")
    
    # Check if contract was generated
    session = handler.get_session_state(session_id)
    assert session.status == NegotiationStatus.AGREED, f"Expected AGREED status, got {session.status}"
    
    # Find the generated contract
    contract = contract_service.get_contract_by_session(session_id)
    assert contract is not None, "Contract should have been generated"
    
    print(f"\n🎉 Contract Generated Successfully!")
    print(f"Contract ID: {contract.contract_id}")
    print(f"Status: {contract.status.value}")
    print(f"Brand: {contract.brand_name}")
    print(f"Influencer: {contract.influencer_name}")
    print(f"Total Amount: ${contract.total_amount:.2f}")
    print(f"Campaign: {contract.campaign_start_date.strftime('%Y-%m-%d')} to {contract.campaign_end_date.strftime('%Y-%m-%d')}")
    
    return contract

def test_contract_signing(contract):
    """Test digital signing process"""
    print("\n🖊️  Testing Digital Signing Process")
    print("=" * 60)
    
    contract_id = contract.contract_id
    
    # Test brand signature
    print("1. Brand signing contract...")
    signed_contract = contract_service.sign_contract(
        contract_id=contract_id,
        signer_type="brand",
        signer_name="John Marketing Manager",
        signer_email="john@mamaearth.com",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser"
    )
    
    print(f"✅ Brand signed! Status: {signed_contract.status.value}")
    assert signed_contract.brand_signature is not None
    assert signed_contract.status == ContractStatus.BRAND_SIGNED
    
    # Test influencer signature
    print("2. Influencer signing contract...")
    signed_contract = contract_service.sign_contract(
        contract_id=contract_id,
        signer_type="influencer",
        signer_name="Priya Sharma",
        signer_email="priya.sharma@email.com",
        ip_address="192.168.1.101",
        user_agent="Mozilla/5.0 Mobile Browser"
    )
    
    print(f"✅ Influencer signed! Status: {signed_contract.status.value}")
    assert signed_contract.influencer_signature is not None
    assert signed_contract.status == ContractStatus.FULLY_EXECUTED
    
    print(f"\n🎉 Contract Fully Executed!")
    print(f"Brand Signer: {signed_contract.brand_signature.signer_name}")
    print(f"Brand Signed At: {signed_contract.brand_signature.signature_timestamp}")
    print(f"Influencer Signer: {signed_contract.influencer_signature.signer_name}")
    print(f"Influencer Signed At: {signed_contract.influencer_signature.signature_timestamp}")
    
    return signed_contract

def test_contract_html_generation(contract):
    """Test HTML contract generation for viewing/printing"""
    print("\n📄 Testing Contract HTML Generation")
    print("=" * 60)
    
    try:
        html_content = contract_service.generate_contract_pdf_content(contract.contract_id)
        
        # Basic validation of HTML content
        assert "<html>" in html_content
        assert contract.brand_name in html_content
        assert contract.influencer_name in html_content
        assert contract.contract_id in html_content
        assert "INFLUENCER MARKETING AGREEMENT" in html_content
        
        print(f"✅ HTML contract generated successfully")
        print(f"Content length: {len(html_content)} characters")
        print(f"Contains brand name: {'✅' if contract.brand_name in html_content else '❌'}")
        print(f"Contains influencer name: {'✅' if contract.influencer_name in html_content else '❌'}")
        print(f"Contains deliverables table: {'✅' if 'deliverables-table' in html_content else '❌'}")
        print(f"Contains signatures: {'✅' if 'Signed digitally by' in html_content else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        return False

def test_contract_api_compatibility():
    """Test contract service compatibility with API responses"""
    print("\n🔌 Testing API Compatibility")
    print("=" * 60)
    
    # List all contracts
    contracts_list = contract_service.list_contracts()
    print(f"✅ Listed {len(contracts_list)} contracts")
    
    if contracts_list:
        # Test contract summary
        contract_id = contracts_list[0]["contract_id"]
        summary = contract_service.get_contract_summary(contract_id)
        
        required_fields = [
            "contract_id", "status", "brand_name", "influencer_name",
            "campaign_title", "total_amount", "signatures", "created_date"
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing required field: {field}"
        
        print(f"✅ Contract summary contains all required fields")
        print(f"✅ Signature status: Brand={summary['signatures']['brand_signed']}, Influencer={summary['signatures']['influencer_signed']}")
        
        return True
    
    return False

def main():
    """Run all contract tests"""
    print("🚀 Contract Generation & Signing Test Suite")
    print("=" * 80)
    
    try:
        # Test 1: Contract Generation
        contract = test_contract_generation()
        
        # Test 2: Digital Signing
        signed_contract = test_contract_signing(contract)
        
        # Test 3: HTML Generation
        html_success = test_contract_html_generation(signed_contract)
        
        # Test 4: API Compatibility
        api_success = test_contract_api_compatibility()
        
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"✅ Contract Generation: PASSED")
        print(f"✅ Digital Signing: PASSED")
        print(f"{'✅' if html_success else '❌'} HTML Generation: {'PASSED' if html_success else 'FAILED'}")
        print(f"{'✅' if api_success else '❌'} API Compatibility: {'PASSED' if api_success else 'FAILED'}")
        
        if html_success and api_success:
            print(f"\n🎉 ALL TESTS PASSED! Contract system is fully functional.")
            print(f"📄 Digital contracts are automatically generated when negotiations reach AGREED status")
            print(f"🖊️  Both parties can digitally sign contracts")
            print(f"📋 HTML contracts can be generated for viewing/printing")
            print(f"🔌 API endpoints are ready for frontend integration")
        else:
            print(f"\n⚠️  Some tests failed. Please check the errors above.")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
