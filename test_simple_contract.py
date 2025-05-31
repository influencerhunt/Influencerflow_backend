#!/usr/bin/env python3
"""
Simple Contract API Test
"""

import requests
import json

def test_simple_contract_api():
    """Test basic contract API endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Contract API Endpoints")
    print("=" * 50)
    
    try:
        # Test 1: Health check
        print("\n1️⃣ Testing server health...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is responsive")
        else:
            print(f"❌ Server returned {response.status_code}")
            return False
        
        # Test 2: List contracts endpoint
        print("\n2️⃣ Testing contracts list endpoint...")
        response = requests.get(f"{base_url}/api/v1/contracts/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Contracts endpoint working: {data['total_count']} contracts")
        else:
            print(f"❌ Contracts endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Test 3: Try to get a non-existent contract
        print("\n3️⃣ Testing contract details endpoint...")
        fake_contract_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{base_url}/api/v1/contracts/{fake_contract_id}", timeout=10)
        if response.status_code == 404:
            print("✅ Contract not found (expected)")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
        
        print("\n" + "=" * 50)
        print("✅ Basic API tests completed successfully!")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server may be slow or unresponsive")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_contract_api()
    exit(0 if success else 1)
