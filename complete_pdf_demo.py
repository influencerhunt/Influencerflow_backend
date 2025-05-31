#!/usr/bin/env python3
"""
Complete PDF Demo - Generate contract, start server, and test PDF endpoints
"""

import sys
import os
import subprocess
import time
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_handler import ConversationHandler
from app.services.contract_service import contract_service
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, 
    ContentType, LocationType, NegotiationStatus
)

def generate_test_contract():
    """Generate a test contract and return contract ID"""
    
    print("🎯 Generating test contract...")
    
    # Create test data
    brand = BrandDetails(
        name="PDF Demo Corp",
        brand_location=LocationType.US,
        budget=1500.0,
        goals=["brand_awareness"],
        target_platforms=[PlatformType.INSTAGRAM],
        content_requirements={
            PlatformType.INSTAGRAM: [ContentType.INSTAGRAM_POST, ContentType.INSTAGRAM_REEL]
        },
        campaign_duration_days=30
    )
    
    influencer = InfluencerProfile(
        name="Demo Influencer",
        location=LocationType.US,
        followers=80000,
        engagement_rate=0.04,
        platforms=[PlatformType.INSTAGRAM]
    )
    
    # Generate contract
    handler = ConversationHandler()
    session_id = handler.create_session(brand, influencer)
    proposal = handler.generate_proposal(session_id)
    acceptance_response = handler._handle_acceptance(session_id)
    
    # Extract contract ID
    contract_id = None
    if "Contract ID" in acceptance_response:
        lines = acceptance_response.split('\n')
        for line in lines:
            if "Contract ID:" in line:
                contract_id = line.split('`')[1]
                break
    
    if contract_id:
        print(f"✅ Contract generated: {contract_id}")
        return contract_id
    else:
        print("❌ Failed to generate contract")
        return None

def test_pdf_in_memory():
    """Test PDF generation in memory before starting server"""
    
    contract_id = generate_test_contract()
    if not contract_id:
        return False
    
    try:
        print("\n📄 Testing in-memory PDF generation...")
        
        # Test PDF generation
        pdf_bytes = contract_service.generate_contract_pdf(contract_id)
        print(f"✅ PDF generated: {len(pdf_bytes)} bytes")
        
        # Save PDF to file
        pdf_filename = f"demo_contract_{contract_id}.pdf"
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_bytes)
        print(f"✅ PDF saved as: {pdf_filename}")
        
        # Test contract signing and PDF update
        print("\n✍️ Testing contract signing...")
        
        # Brand signs
        contract_service.sign_contract(
            contract_id=contract_id,
            signer_type="brand",
            signer_name="PDF Demo Corp Legal",
            signer_email="legal@pdfdemo.com",
            ip_address="192.168.1.100",
            user_agent="PDF Demo Test Script"
        )
        print("✅ Brand signed")
        
        # Generate PDF after brand signature
        pdf_bytes_signed = contract_service.generate_contract_pdf(contract_id)
        pdf_filename_signed = f"demo_contract_{contract_id}_brand_signed.pdf"
        with open(pdf_filename_signed, 'wb') as f:
            f.write(pdf_bytes_signed)
        print(f"✅ Brand-signed PDF saved as: {pdf_filename_signed}")
        
        # Influencer signs
        contract_service.sign_contract(
            contract_id=contract_id,
            signer_type="influencer",
            signer_name="Demo Influencer",
            signer_email="demo@influencer.com",
            ip_address="192.168.1.101",
            user_agent="PDF Demo Test Script"
        )
        print("✅ Influencer signed")
        
        # Generate final PDF
        pdf_bytes_final = contract_service.generate_contract_pdf(contract_id)
        pdf_filename_final = f"demo_contract_{contract_id}_fully_signed.pdf"
        with open(pdf_filename_final, 'wb') as f:
            f.write(pdf_bytes_final)
        print(f"✅ Fully-signed PDF saved as: {pdf_filename_final}")
        
        print(f"\n🎉 PDF Demo Complete!")
        print(f"   Contract ID: {contract_id}")
        print(f"   Generated files:")
        print(f"   - {pdf_filename}")
        print(f"   - {pdf_filename_signed}")
        print(f"   - {pdf_filename_final}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Complete PDF Demo...")
    success = test_pdf_in_memory()
    
    if success:
        print("\n✅ PDF Demo completed successfully!")
        print("\n📋 To test HTTP endpoints:")
        print("1. Start server: python -m uvicorn main:app --reload --port 8000")
        print("2. Use the curl commands in contract_testing_commands.sh")
        print("3. Check the PDF download endpoint with the contract ID above")
    else:
        print("\n❌ PDF Demo failed!")
        sys.exit(1)
