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
    
    print("🎯 Starting PDF Generation Test...")
    
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
    
    try:
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
            return False
            
        print(f"📄 Contract ID: {contract_id}")
        
        # Step 5: Test HTML contract generation
        print("\n🌐 Testing HTML Contract Generation:")
        try:
            html_content = contract_service.generate_contract_pdf_content(contract_id)
            print(f"✅ HTML contract generated ({len(html_content)} characters)")
        except Exception as e:
            print(f"❌ HTML generation failed: {e}")
            return False
        
        # Step 6: Test PDF generation
        print("\n📄 Testing PDF Generation:")
        try:
            pdf_bytes = contract_service.generate_contract_pdf(contract_id)
            print(f"✅ PDF contract generated ({len(pdf_bytes)} bytes)")
            
            # Save PDF to file for verification
            pdf_filename = f"contract_{contract_id}.pdf"
            with open(pdf_filename, 'wb') as f:
                f.write(pdf_bytes)
            print(f"✅ PDF saved as: {pdf_filename}")
            
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return False
        
        # Step 7: Test contract signing and re-generating PDF
        print("\n✍️ Testing Contract Signing and PDF Update:")
        try:
            # Brand signs first
            signed_contract = contract_service.sign_contract(
                contract_id=contract_id,
                signer_type="brand",
                signer_name="TechCorp Legal Team",
                signer_email="legal@techcorp.com",
                ip_address="192.168.1.100"
            )
            print(f"✅ Brand signed contract")
            
            # Generate PDF after brand signature
            pdf_bytes_brand_signed = contract_service.generate_contract_pdf(contract_id)
            pdf_filename_brand_signed = f"contract_{contract_id}_brand_signed.pdf"
            with open(pdf_filename_brand_signed, 'wb') as f:
                f.write(pdf_bytes_brand_signed)
            print(f"✅ Brand-signed PDF saved as: {pdf_filename_brand_signed}")
            
            # Influencer signs
            signed_contract = contract_service.sign_contract(
                contract_id=contract_id,
                signer_type="influencer", 
                signer_name="PDF TestInfluencer",
                signer_email="test@influencer.com",
                ip_address="192.168.1.101"
            )
            print(f"✅ Influencer signed contract")
            
            # Generate final PDF with both signatures
            pdf_bytes_final = contract_service.generate_contract_pdf(contract_id)
            pdf_filename_final = f"contract_{contract_id}_fully_signed.pdf"
            with open(pdf_filename_final, 'wb') as f:
                f.write(pdf_bytes_final)
            print(f"✅ Fully-signed PDF saved as: {pdf_filename_final}")
            
        except Exception as e:
            print(f"❌ Contract signing or PDF update failed: {e}")
            return False
        
        print(f"\n🎉 PDF Generation Test Complete!")
        print(f"   Contract ID: {contract_id}")
        print(f"   Generated PDFs:")
        print(f"   - {pdf_filename} (initial)")
        print(f"   - {pdf_filename_brand_signed} (brand signed)")
        print(f"   - {pdf_filename_final} (fully signed)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    if success:
        print("\n✅ All PDF tests passed!")
    else:
        print("\n❌ PDF tests failed!")
        sys.exit(1)
