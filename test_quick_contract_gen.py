#!/usr/bin/env python3
"""
Quick Contract Generation Test
Tests the contract generation triggered by negotiation acceptance
"""

import requests
import json
import time

def test_quick_contract_generation():
    """Test contract generation from negotiation"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Quick Contract Generation Test")
    print("=" * 50)
    
    try:
        # Step 1: Start a quick negotiation
        print("\n1️⃣ Starting negotiation...")
        negotiation_data = {
            "brand_details": {
                "name": "QuickTest Corp",
                "budget": 800.0,
                "goals": ["brand awareness"],
                "target_platforms": ["instagram"],
                "content_requirements": {
                    "instagram_post": 1,
                    "instagram_story": 2
                },
                "campaign_duration_days": 14,
                "brand_location": "US"
            },
            "influencer_profile": {
                "name": "Alex Creator",
                "followers": 50000,
                "engagement_rate": 0.045,
                "location": "US",
                "platforms": ["instagram"],
                "niches": ["lifestyle"]
            }
        }
        
        response = requests.post(f"{base_url}/api/v1/negotiation/start", json=negotiation_data, timeout=15)
        if response.status_code != 200:
            print(f"❌ Failed to start negotiation: {response.status_code}")
            return False
            
        negotiation_result = response.json()
        session_id = negotiation_result["session_id"]
        print(f"✅ Negotiation started: {session_id}")
        
        # Step 2: Accept the proposal quickly
        print("\n2️⃣ Accepting proposal...")
        accept_data = {
            "session_id": session_id,
            "user_input": "Perfect! I accept this proposal."
        }
        
        # Set a longer timeout for the negotiation processing
        response = requests.post(f"{base_url}/api/v1/negotiation/continue", json=accept_data, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to accept proposal: {response.status_code}")
            print(response.text[:500])  # Show first 500 chars of error
            return False
        
        acceptance_result = response.json()
        print(f"✅ Proposal accepted")
        
        # Check if contract was mentioned in response
        message = acceptance_result.get("message", "")
        if "contract" in message.lower() or "Contract ID" in message:
            print("📄 Contract generation confirmed in response!")
            
            # Extract contract ID if present
            import re
            contract_match = re.search(r'Contract ID: ([a-f0-9-]+)', message)
            if contract_match:
                contract_id = contract_match.group(1)
                print(f"📋 Contract ID: {contract_id}")
                
                # Test the new contract
                print(f"\n3️⃣ Testing generated contract...")
                response = requests.get(f"{base_url}/api/v1/contracts/{contract_id}", timeout=10)
                if response.status_code == 200:
                    contract_details = response.json()
                    print(f"✅ Contract verified:")
                    print(f"   Brand: {contract_details.get('brand_name')}")
                    print(f"   Influencer: {contract_details.get('influencer_name')}")
                    print(f"   Total: {contract_details.get('total_amount')}")
                    print(f"   Status: {contract_details.get('status')}")
                    
                    return True
                else:
                    print(f"❌ Could not verify contract: {response.status_code}")
        else:
            print("⚠️  Contract generation not detected in response")
            print(f"Response: {message[:200]}...")
            
            # Try to find contract by session
            print(f"\n3️⃣ Checking for contract by session...")
            response = requests.get(f"{base_url}/api/v1/contracts/session/{session_id}", timeout=10)
            if response.status_code == 200:
                contract_data = response.json()
                print(f"✅ Contract found by session: {contract_data['contract_id']}")
                return True
            else:
                print(f"❌ No contract found for session: {response.status_code}")
        
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out - negotiation processing may be slow")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_quick_contract_generation()
    if success:
        print("\n🎉 CONTRACT GENERATION TEST PASSED!")
    else:
        print("\n❌ CONTRACT GENERATION TEST FAILED!")
    exit(0 if success else 1)
