#!/usr/bin/env python3
"""
Direct PDF Generation Test - Generate contract and PDF in one run
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
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_generation():
    """Test complete contract generation and PDF creation flow"""
    
    # Create test data (using same pattern as working test)
    brand = BrandDetails(
        name="TechCorp PDF Test",
        brand_location=LocationType.US,
        budget=2000.0,
        goals=["brand_awareness", "lead_generation"],
        target_platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE],
        content_requirements={
            PlatformType.INSTAGRAM: [ContentType.INSTAGRAM_POST, ContentType.INSTAGRAM_REEL],
            PlatformType.YOUTUBE: [ContentType.YOUTUBE_LONG_FORM]
        },
        campaign_duration_days=30
    )
    
    influencer = InfluencerProfile(
        name="PDF TestInfluencer",
        location=LocationType.US,
        followers=75000,
        engagement_rate=0.045,
        platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE]
    )
    
    # Create conversation handler
    handler = ConversationHandler()
        influencer_profile=influencer,
        negotiation_rounds=5,
        agreed_terms=agreed_terms,
        negotiation_status="AGREED"
    )
    
    return negotiation_state

def test_pdf_generation_direct():
    """Test complete PDF generation flow"""
    print("🎯 Starting Direct PDF Generation Test...")
    print("=" * 50)
    
    try:
        # 1. Setup negotiation state
        print("1️⃣ Setting up negotiation state...")
        negotiation_state = setup_negotiation_state()
        print("✅ Negotiation state created")
        
        # 2. Generate contract
        print("\n2️⃣ Generating contract...")
        contract = contract_service.generate_contract(
            session_id=negotiation_state.session_id,
            negotiation_state=negotiation_state,
            brand_contact_email="john@techcorp.com",
            brand_contact_name="John Doe",
            influencer_email="tech@influencer.com",
            influencer_contact="@techinfluencer"
        )
        print(f"✅ Contract generated: {contract.contract_id}")
        
        # 3. Test HTML generation
        print("\n3️⃣ Testing HTML generation...")
        html_content = contract_service.generate_contract_pdf_content(contract.contract_id)
        print(f"✅ HTML generated successfully ({len(html_content)} characters)")
        
        # 4. Test PDF generation
        print("\n4️⃣ Testing PDF generation...")
        pdf_bytes = contract_service.generate_contract_pdf(contract.contract_id)
        print(f"✅ PDF generated successfully ({len(pdf_bytes)} bytes)")
        
        # 5. Save PDF to file
        pdf_filename = f"contract_{contract.contract_id[:8]}.pdf"
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_bytes)
        print(f"💾 PDF saved as: {pdf_filename}")
        
        # 6. Test signatures and regenerate PDF
        print("\n5️⃣ Testing signatures and PDF regeneration...")
        
        # Sign by brand
        contract_service.sign_contract(
            contract_id=contract.contract_id,
            signer_type="brand",
            signer_name="John Doe",
            signer_email="john@techcorp.com",
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )
        print("✅ Brand signature added")
        
        # Sign by influencer
        contract_service.sign_contract(
            contract_id=contract.contract_id,
            signer_type="influencer", 
            signer_name="TechInfluencer",
            signer_email="tech@influencer.com",
            ip_address="192.168.1.101",
            user_agent="TestAgent/1.0"
        )
        print("✅ Influencer signature added")
        
        # Generate final signed PDF
        signed_pdf_bytes = contract_service.generate_contract_pdf(contract.contract_id)
        signed_pdf_filename = f"contract_{contract.contract_id[:8]}_signed.pdf"
        with open(signed_pdf_filename, 'wb') as f:
            f.write(signed_pdf_bytes)
        print(f"💾 Signed PDF saved as: {signed_pdf_filename}")
        
        # 7. Summary
        final_contract = contract_service.get_contract(contract.contract_id)
        print(f"\n📊 Final Contract Summary:")
        print(f"   - Contract ID: {contract.contract_id}")
        print(f"   - Brand: {final_contract.brand_name}")
        print(f"   - Influencer: {final_contract.influencer_name}")
        print(f"   - Status: {final_contract.status.value}")
        print(f"   - Total: ${final_contract.total_amount}")
        print(f"   - Deliverables: {len(final_contract.deliverables)}")
        print(f"   - Brand Signed: {'✅' if final_contract.brand_signature else '❌'}")
        print(f"   - Influencer Signed: {'✅' if final_contract.influencer_signature else '❌'}")
        
        print(f"\n🎉 PDF generation test completed successfully!")
        print(f"📂 Generated files:")
        print(f"   - Unsigned: {pdf_filename}")
        print(f"   - Signed: {signed_pdf_filename}")
        
        print(f"\n🌐 API Testing Commands:")
        print(f"curl -X GET \"http://localhost:8000/api/v1/contracts/{contract.contract_id}/pdf\" -o \"downloaded_contract.pdf\"")
        
    except Exception as e:
        print(f"❌ Error during PDF generation test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation_direct()
