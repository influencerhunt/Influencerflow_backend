#!/usr/bin/env python3
"""
Direct Contract API Test
Tests contract endpoints without going through negotiation
"""

import requests
import json
from datetime import datetime
import uuid

def test_contract_endpoints():
    """Test contract endpoints directly"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Contract Endpoints Directly")
    print("=" * 60)
    
    try:
        # Test 1: List existing contracts
        print("\n1️⃣ Listing existing contracts...")
        response = requests.get(f"{base_url}/api/v1/contracts/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_count']} contracts")
            print(f"   Status breakdown: {data['status_breakdown']}")
            
            # If there are contracts, test one of them
            if data['total_count'] > 0 and data.get('contracts'):
                first_contract = data['contracts'][0]
                contract_id = first_contract['contract_id']
                print(f"   📄 First contract ID: {contract_id}")
                
                # Test 2: Get contract details
                print(f"\n2️⃣ Getting contract details for {contract_id}...")
                response = requests.get(f"{base_url}/api/v1/contracts/{contract_id}", timeout=10)
                if response.status_code == 200:
                    contract_details = response.json()
                    print(f"✅ Contract Details:")
                    print(f"   Brand: {contract_details.get('brand_name', 'N/A')}")
                    print(f"   Influencer: {contract_details.get('influencer_name', 'N/A')}")
                    print(f"   Total: {contract_details.get('total_amount', 'N/A')}")
                    print(f"   Status: {contract_details.get('status', 'N/A')}")
                else:
                    print(f"❌ Failed to get contract details: {response.status_code}")
                
                # Test 3: Get contract HTML view
                print(f"\n3️⃣ Getting contract HTML view...")
                response = requests.get(f"{base_url}/api/v1/contracts/{contract_id}/view", timeout=10)
                if response.status_code == 200:
                    html_data = response.json()
                    print(f"✅ HTML contract generated ({len(html_data.get('html_content', ''))} characters)")
                else:
                    print(f"❌ Failed to get HTML contract: {response.status_code}")
                
                # Test 4: Get contract status
                print(f"\n4️⃣ Getting contract status...")
                response = requests.get(f"{base_url}/api/v1/contracts/{contract_id}/status", timeout=10)
                if response.status_code == 200:
                    status_data = response.json()
                    print(f"✅ Contract Status:")
                    print(f"   Status: {status_data.get('status', 'N/A')}")
                    print(f"   Brand Signed: {status_data.get('signatures', {}).get('brand', {}).get('signed', False)}")
                    print(f"   Influencer Signed: {status_data.get('signatures', {}).get('influencer', {}).get('signed', False)}")
                    print(f"   Next Action: {status_data.get('next_action', 'N/A')}")
                else:
                    print(f"❌ Failed to get contract status: {response.status_code}")
                
                # Test 5: Try signing (if not already fully signed)
                if contract_details.get('status') != 'FULLY_EXECUTED':
                    signatures = status_data.get('signatures', {})
                    
                    if not signatures.get('brand', {}).get('signed', False):
                        print(f"\n5️⃣ Testing brand signature...")
                        brand_signature = {
                            "signer_type": "brand",
                            "signer_name": "Test Brand Representative",
                            "signer_email": "brand@test.com"
                        }
                        response = requests.post(f"{base_url}/api/v1/contracts/{contract_id}/sign", 
                                               json=brand_signature, timeout=10)
                        if response.status_code == 200:
                            result = response.json()
                            print(f"✅ Brand signature added: {result.get('status', 'Unknown')}")
                        else:
                            print(f"⚠️  Brand signature failed: {response.status_code} - {response.text}")
                    
                    if not signatures.get('influencer', {}).get('signed', False):
                        print(f"\n6️⃣ Testing influencer signature...")
                        influencer_signature = {
                            "signer_type": "influencer",
                            "signer_name": "Test Influencer",
                            "signer_email": "influencer@test.com"
                        }
                        response = requests.post(f"{base_url}/api/v1/contracts/{contract_id}/sign", 
                                               json=influencer_signature, timeout=10)
                        if response.status_code == 200:
                            result = response.json()
                            print(f"✅ Influencer signature added: {result.get('status', 'Unknown')}")
                            print(f"🎉 Contract fully executed: {result.get('fully_executed', False)}")
                        else:
                            print(f"⚠️  Influencer signature failed: {response.status_code} - {response.text}")
            
        else:
            print(f"❌ Failed to list contracts: {response.status_code}")
            return False
        
        print("\n" + "=" * 60)
        print("✅ Contract API endpoints test completed!")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_contract_endpoints()
    exit(0 if success else 1)
