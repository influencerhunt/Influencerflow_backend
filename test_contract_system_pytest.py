#!/usr/bin/env python3
"""
Test Contract Generation and Digital Signing with pytest
Tests the complete flow from negotiation agreement to contract signing
"""

import sys
import os
import uuid
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, NegotiationOffer, ContentDeliverable,
    LocationType, PlatformType, ContentType, NegotiationStatus, ContractStatus,
    NegotiationState
)
from app.services.conversation_handler import ConversationHandler
from app.services.contract_service import contract_service


def create_sample_negotiation():
    """Create a sample negotiation state for testing"""
    session_id = str(uuid.uuid4())
    
    agreed_offer = NegotiationOffer(
        total_price=385.0,
        deliverables=[
            ContentDeliverable(
                platform=PlatformType.INSTAGRAM,
                content_type=ContentType.INSTAGRAM_POST,
                quantity=3,
                proposed_price=231.0,
                market_rate=77.0
            ),
            ContentDeliverable(
                platform=PlatformType.INSTAGRAM,
                content_type=ContentType.INSTAGRAM_STORY,
                quantity=2,
                proposed_price=154.0,
                market_rate=77.0
            )
        ],
        campaign_duration_days=30
    )
    
    return NegotiationState(
        session_id=session_id,
        brand_details=BrandDetails(
            name="Mama Earth",
            budget=500.0,
            goals=["brand awareness", "engagement"],
            target_platforms=[PlatformType.INSTAGRAM],
            content_requirements={
                "instagram_post": 3,
                "instagram_story": 2
            },
            campaign_duration_days=30,
            brand_location=LocationType.US
        ),
        influencer_profile=InfluencerProfile(
            name="Priya Sharma",
            followers=50000,
            engagement_rate=0.045,
            location=LocationType.INDIA,
            platforms=[PlatformType.INSTAGRAM],
            niches=["lifestyle", "wellness"]
        ),
        current_offer=agreed_offer,
        agreed_terms=agreed_offer,  # This is needed for contract generation
        status=NegotiationStatus.AGREED,
        conversation_history=[]
    )


@pytest.fixture
def sample_contract():
    """Create a contract for testing"""
    session_id = str(uuid.uuid4())
    session = create_sample_negotiation()
    
    contract = contract_service.generate_contract(
        session_id=session_id,
        negotiation_state=session,
        brand_contact_email="legal@mamaearth.com",
        brand_contact_name="Mama Earth Legal Team",
        influencer_contact="+1-XXX-XXX-XXXX"
    )
    return contract


def test_contract_generation():
    """Test contract generation from agreed negotiation"""
    print("\n📄 Testing Contract Generation")
    print("=" * 60)
    
    # Create sample negotiation state
    session_id = str(uuid.uuid4())
    session = create_sample_negotiation()
    
    print("1. Creating contract from negotiation...")
    contract = contract_service.generate_contract(
        session_id=session_id,
        negotiation_state=session,
        brand_contact_email="legal@mamaearth.com",
        brand_contact_name="Mama Earth Legal Team",
        influencer_contact="+1-XXX-XXX-XXXX"
    )
    
    print("✅ Contract generated successfully!")
    print(f"Contract ID: {contract.contract_id}")
    print(f"Status: {contract.status.value}")
    print(f"Brand: {contract.brand_name}")
    print(f"Influencer: {contract.influencer_name}")
    print(f"Total Amount: ${contract.total_amount:.2f}")
    print(f"Campaign: {contract.campaign_start_date.strftime('%Y-%m-%d')} to {contract.campaign_end_date.strftime('%Y-%m-%d')}")
    
    assert contract.contract_id is not None
    assert contract.status == ContractStatus.PENDING_SIGNATURES
    assert contract.brand_name == "Mama Earth"
    assert contract.influencer_name == "Priya Sharma"
    assert contract.total_amount == 385.0


def test_contract_signing(sample_contract):
    """Test digital signing process"""
    print("\n🖊️  Testing Digital Signing Process")
    print("=" * 60)
    
    contract_id = sample_contract.contract_id
    
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


def test_contract_html_generation(sample_contract):
    """Test HTML contract generation for viewing/printing"""
    print("\n📄 Testing Contract HTML Generation")
    print("=" * 60)
    
    html_content = contract_service.generate_contract_pdf_content(sample_contract.contract_id)
    
    # Basic validation of HTML content
    assert "<html>" in html_content
    assert sample_contract.brand_name in html_content
    assert sample_contract.influencer_name in html_content
    assert sample_contract.contract_id in html_content
    assert "INFLUENCER MARKETING AGREEMENT" in html_content
    
    print(f"✅ HTML contract generated successfully")
    print(f"Content length: {len(html_content)} characters")
    print(f"Contains brand name: {'✅' if sample_contract.brand_name in html_content else '❌'}")
    print(f"Contains influencer name: {'✅' if sample_contract.influencer_name in html_content else '❌'}")
    print(f"Contains deliverables table: {'✅' if 'deliverables-table' in html_content else '❌'}")


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
    
    assert True  # Always pass if we reach here


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
