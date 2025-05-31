#!/usr/bin/env python3
"""
Start server and test PDF endpoint
"""

import subprocess
import time
import requests
import sys
import os

# Contract ID from our successful test
CONTRACT_ID = "16dbf6a4-6cd0-41af-a2fc-8caeb40e6201"

def test_pdf_endpoint():
    """Test PDF endpoint with curl equivalent"""
    
    base_url = "http://localhost:8000"
    
    try:
        # Test PDF download endpoint
        print(f"🔍 Testing PDF download for contract: {CONTRACT_ID}")
        
        response = requests.get(f"{base_url}/api/v1/contracts/{CONTRACT_ID}/pdf")
        
        if response.status_code == 200:
            print(f"✅ PDF endpoint working!")
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content-Length: {len(response.content)} bytes")
            
            # Save the downloaded PDF
            with open(f"downloaded_{CONTRACT_ID}.pdf", 'wb') as f:
                f.write(response.content)
            print(f"✅ Downloaded PDF saved as: downloaded_{CONTRACT_ID}.pdf")
            
        else:
            print(f"❌ PDF endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error testing PDF endpoint: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🌐 Testing PDF Download Endpoint...")
    print("   Make sure server is running: python -m uvicorn main:app --reload --port 8000")
    print("")
    
    # Wait a moment for user to start server
    input("Press Enter when server is ready...")
    
    success = test_pdf_endpoint()
    
    if success:
        print("\n✅ PDF endpoint test passed!")
    else:
        print("\n❌ PDF endpoint test failed!")
