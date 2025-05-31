#!/usr/bin/env python3
"""
Complete Integration Test for Contract System
Tests the full workflow from negotiation to fully executed contract
"""

import uuid
import requests
import json
import time
from datetime import datetime

def test_complete_contract_workflow():
    """Test the complete contract workflow via API"""
    
    print("🚀 Contract System Integration Test")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Step 1: Start a negotiation
    print("\n1️⃣ Starting negotiation...")
    negotiation_data = {
        "brand_details": {
            "name": "TechFlow Industries",
            "budget": 1200.0,
            "goals": ["brand awareness", "product launch"],
            "target_platforms": ["instagram"],
            "content_requirements": {
                "instagram_post": 2,
                "instagram_story": 3
            },
            "campaign_duration_days": 30,
            "brand_location": "US"
        },
        "influencer_profile": {
            "name": "Sarah Johnson",
            "followers": 75000,
            "engagement_rate": 0.055,
            "location": "US",
            "platforms": ["instagram"],
            "niches": ["technology", "lifestyle"]
        }
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/negotiation/start", json=negotiation_data)
        if response.status_code != 200:
            print(f"❌ Failed to start negotiation: {response.status_code}")
            print(response.text)
            return False
        
        negotiation_result = response.json()
        session_id = negotiation_result["session_id"]
        print(f"✅ Negotiation started: {session_id}")
        
        # Step 2: Simulate acceptance to trigger contract generation
        print("\n2️⃣ Accepting the proposal...")
        accept_data = {
            "session_id": session_id,
            "user_input": "This looks perfect! I accept this proposal and would like to move forward."
        }
        
        response = requests.post(f"{base_url}/api/v1/negotiation/continue", json=accept_data)
        if response.status_code != 200:
            print(f"❌ Failed to accept proposal: {response.status_code}")
            print(response.text)
            return False
        
        acceptance_result = response.json()
        print(f"✅ Proposal accepted")
        
        # Extract contract ID from the response message
        if "contract_id" in acceptance_result.get("message", ""):
            import re
            contract_match = re.search(r'Contract ID: ([a-f0-9-]+)', acceptance_result["message"])
            if contract_match:
                contract_id = contract_match.group(1)
                print(f"📄 Contract ID extracted: {contract_id}")
            else:
                print("⚠️  Contract ID not found in response, will check by session")
                contract_id = None
        else:
            contract_id = None
        
        # Step 3: Get contract by session if needed
        if not contract_id:
            print("\n3️⃣ Getting contract by session...")
            response = requests.get(f"{base_url}/api/v1/contracts/session/{session_id}")
            if response.status_code != 200:
                print(f"❌ Failed to get contract: {response.status_code}")
                print(response.text)
                return False
            
            contract_data = response.json()
            contract_id = contract_data["contract_id"]
            print(f"✅ Contract found: {contract_id}")
        
        # Step 4: View contract details
        print("\n4️⃣ Viewing contract details...")
        response = requests.get(f"{base_url}/api/v1/contracts/{contract_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get contract details: {response.status_code}")
            return False
        
        contract_details = response.json()
        print(f"✅ Contract Details:")
        print(f"   Brand: {contract_details['brand_name']}")
        print(f"   Influencer: {contract_details['influencer_name']}")
        print(f"   Total: ${contract_details['total_amount']:.2f}")
        print(f"   Status: {contract_details['status']}")
        
        # Step 5: Get contract HTML view
        print("\n5️⃣ Generating contract HTML...")
        response = requests.get(f"{base_url}/api/v1/contracts/{contract_id}/view")
        if response.status_code != 200:
            print(f"❌ Failed to get contract HTML: {response.status_code}")
            return False
        
        html_data = response.json()
        print(f"✅ Contract HTML generated ({len(html_data['html_content'])} characters)")
        
        # Step 6: Brand signs contract
        print("\n6️⃣ Brand signing contract...")
        brand_signature = {
            "signer_type": "brand",
            "signer_name": "John Marketing Director",
            "signer_email": "john@techflow.com"
        }
        
        response = requests.post(f"{base_url}/api/v1/contracts/{contract_id}/sign", json=brand_signature)
        if response.status_code != 200:
            print(f"❌ Failed to sign contract (brand): {response.status_code}")
            print(response.text)
            return False
        
        brand_sign_result = response.json()
        print(f"✅ Brand signed: {brand_sign_result['status']}")
        
        # Step 7: Influencer signs contract
        print("\n7️⃣ Influencer signing contract...")
        influencer_signature = {
            "signer_type": "influencer",
            "signer_name": "Sarah Johnson",
            "signer_email": "sarah@influencer.com"
        }
        
        response = requests.post(f"{base_url}/api/v1/contracts/{contract_id}/sign", json=influencer_signature)
        if response.status_code != 200:
            print(f"❌ Failed to sign contract (influencer): {response.status_code}")
            print(response.text)
            return False
        
        influencer_sign_result = response.json()
        print(f"✅ Influencer signed: {influencer_sign_result['status']}")
        print(f"🎉 Contract fully executed: {influencer_sign_result['fully_executed']}")
        
        # Step 8: Get final contract status
        print("\n8️⃣ Final contract status...")
        response = requests.get(f"{base_url}/api/v1/contracts/{contract_id}/status")
        if response.status_code != 200:
            print(f"❌ Failed to get contract status: {response.status_code}")
            return False
        
        status_data = response.json()
        print(f"✅ Final Status: {status_data['status']}")
        print(f"   Brand Signed: {status_data['signatures']['brand']['signed']}")
        print(f"   Influencer Signed: {status_data['signatures']['influencer']['signed']}")
        print(f"   Next Action: {status_data['next_action']}")
        
        # Step 9: List all contracts
        print("\n9️⃣ Listing all contracts...")
        response = requests.get(f"{base_url}/api/v1/contracts/")
        if response.status_code != 200:
            print(f"❌ Failed to list contracts: {response.status_code}")
            return False
        
        contracts_list = response.json()
        print(f"✅ Total Contracts: {contracts_list['total_count']}")
        print(f"   Status Breakdown: {contracts_list['status_breakdown']}")
        
        print("\n" + "=" * 60)
        print("🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("📋 Summary:")
        print(f"   ✅ Negotiation started and accepted")
        print(f"   ✅ Contract automatically generated")
        print(f"   ✅ HTML contract view created")
        print(f"   ✅ Both parties digitally signed")
        print(f"   ✅ Contract fully executed")
        print(f"   ✅ All API endpoints working")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Please ensure the server is running:")
        print("   uvicorn app.main:app --port 8000")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_contract_workflow()
    exit(0 if success else 1)
