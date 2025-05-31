#!/usr/bin/env python3
"""
Simple PDF Test - Just test PDF generation for existing contract
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.contract_service import contract_service

def test_existing_pdf():
    """Test PDF generation for the contract we just created"""
    
    contract_id = "86692296-5323-4600-92e5-e3f9161b91a7"
    print(f"🎯 Testing PDF generation for contract: {contract_id}")
    
    try:
        # Test HTML generation
        html_content = contract_service.generate_contract_pdf_content(contract_id)
        print(f"✅ HTML generated: {len(html_content)} characters")
        
        # Test PDF generation
        pdf_bytes = contract_service.generate_contract_pdf(contract_id)
        print(f"✅ PDF generated: {len(pdf_bytes)} bytes")
        
        # Save PDF
        pdf_filename = f"test_simple_{contract_id}.pdf"
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_bytes)
        print(f"✅ PDF saved as: {pdf_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_existing_pdf()
    if success:
        print("\n✅ Simple PDF test passed!")
    else:
        print("\n❌ Simple PDF test failed!")
