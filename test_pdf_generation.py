#!/usr/bin/env python3
"""
Test PDF Generation for Contract System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.contract_service import contract_service

def test_pdf_generation():
    """Test PDF generation for existing contracts"""
    print("🔍 Testing PDF Generation...")
    print("=" * 50)
    
    # List existing contracts
    contracts = contract_service.list_contracts()
    print(f"📋 Found {len(contracts)} contracts in the system")
    
    if not contracts:
        print("❌ No contracts found. Run test_contract_complete.py first to generate a contract.")
        return
    
    # Test PDF generation for the first contract
    contract_id = contracts[0]["contract_id"]
    print(f"🧪 Testing PDF generation for contract: {contract_id}")
    
    try:
        # Test HTML generation first
        print("\n1️⃣ Testing HTML generation...")
        html_content = contract_service.generate_contract_pdf_content(contract_id)
        print(f"✅ HTML generated successfully ({len(html_content)} characters)")
        
        # Test PDF generation
        print("\n2️⃣ Testing PDF generation...")
        pdf_bytes = contract_service.generate_contract_pdf(contract_id)
        print(f"✅ PDF generated successfully ({len(pdf_bytes)} bytes)")
        
        # Save PDF to file for verification
        pdf_filename = f"test_contract_{contract_id[:8]}.pdf"
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_bytes)
        print(f"💾 PDF saved as: {pdf_filename}")
        
        # Get contract details for summary
        contract = contract_service.get_contract(contract_id)
        print(f"\n📊 Contract Summary:")
        print(f"   - Brand: {contract.brand_name}")
        print(f"   - Influencer: {contract.influencer_name}")
        print(f"   - Status: {contract.status.value}")
        print(f"   - Total: {contract.total_amount} USD")
        print(f"   - Deliverables: {len(contract.deliverables)}")
        
        print(f"\n🎉 PDF generation test completed successfully!")
        print(f"📂 Check the generated file: {pdf_filename}")
        
    except Exception as e:
        print(f"❌ Error during PDF generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()
