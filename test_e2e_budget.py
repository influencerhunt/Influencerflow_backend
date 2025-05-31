#!/usr/bin/env python3
"""
End-to-end test to validate the complete system with budget constraints.
"""

import requests
import json
import time

def test_e2e_budget_constraint():
    """Test the complete flow with budget constraints"""
    base_url = "http://localhost:8000"
    
    print("🌐 Testing End-to-End Budget Constraint Flow")
    print("=" * 60)
    
    # Test data - ₹7,500 budget case
    test_data = {
        "brand_details": {
            "name": "TestBrand",
            "budget": "₹7,500",  # Small budget to test constraint
            "goals": ["Brand Awareness", "Engagement"],
            "target_platforms": ["instagram"],
            "content_requirements": {
                "instagram_reel": 1,
                "instagram_post": 2
            },
            "campaign_duration_days": 30,
            "target_audience": "Young adults interested in lifestyle",
            "brand_guidelines": "Maintain authentic, casual tone",
            "brand_location": "India"
        },
        "influencer_profile": {
            "name": "Test Creator",
            "followers": 50000,
            "engagement_rate": 5.2,
            "location": "India",
            "platforms": ["instagram"],
            "niches": ["lifestyle", "fashion"],
            "previous_brand_collaborations": 15
        }
    }
    
    try:
        # Step 1: Start negotiation
        print("1️⃣ Starting negotiation...")
        start_response = requests.post(
            f"{base_url}/api/negotiation/start",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if start_response.status_code != 200:
            print(f"❌ Failed to start negotiation: {start_response.status_code}")
            print(f"Response: {start_response.text}")
            return False
            
        start_result = start_response.json()
        session_id = start_result["session_id"]
        print(f"✅ Negotiation started with session: {session_id[:8]}...")
        
        # Step 2: Get initial message
        print("\n2️⃣ Getting initial message...")
        initial_response = requests.post(
            f"{base_url}/api/negotiation/message",
            json={
                "session_id": session_id,
                "message": "Hi! I'm interested in this collaboration opportunity."
            }
        )
        
        if initial_response.status_code != 200:
            print(f"❌ Failed to get initial message: {initial_response.status_code}")
            return False
            
        initial_result = initial_response.json()
        print(f"✅ Initial response received")
        
        # Check if budget is properly mentioned
        initial_msg = initial_result["response"]
        budget_mentioned = "₹7,500" in initial_msg or "7500" in initial_msg or "90" in initial_msg
        print(f"   Budget properly displayed: {'✅' if budget_mentioned else '❌'}")
        
        # Step 3: Request proposal  
        print("\n3️⃣ Requesting proposal...")
        proposal_response = requests.post(
            f"{base_url}/api/negotiation/message",
            json={
                "session_id": session_id,
                "message": "Can you send me your detailed proposal?"
            }
        )
        
        if proposal_response.status_code != 200:
            print(f"❌ Failed to get proposal: {proposal_response.status_code}")
            return False
            
        proposal_result = proposal_response.json()
        proposal_msg = proposal_result["response"]
        print(f"✅ Proposal received")
        
        # Check if proposal respects budget
        proposal_within_budget = "₹7,500" in proposal_msg or "90" in proposal_msg
        print(f"   Proposal within budget: {'✅' if proposal_within_budget else '❌'}")
        
        # Step 4: Test counter-offer above budget
        print("\n4️⃣ Testing counter-offer above budget...")
        counter_response = requests.post(
            f"{base_url}/api/negotiation/message",
            json={
                "session_id": session_id,
                "message": "I was thinking more like ₹15,000 for this campaign."
            }
        )
        
        if counter_response.status_code != 200:
            print(f"❌ Failed to send counter-offer: {counter_response.status_code}")
            return False
            
        counter_result = counter_response.json()
        counter_msg = counter_result["response"]
        print(f"✅ Counter-offer response received")
        
        # Check if budget constraint is mentioned
        budget_constraint_mentioned = any(word in counter_msg.lower() for word in ["budget", "constraint", "limit", "₹7,500", "90"])
        print(f"   Budget constraint enforced: {'✅' if budget_constraint_mentioned else '❌'}")
        
        # Step 5: Get session status
        print("\n5️⃣ Checking session status...")
        status_response = requests.get(f"{base_url}/api/negotiation/status/{session_id}")
        
        if status_response.status_code != 200:
            print(f"❌ Failed to get status: {status_response.status_code}")
            return False
            
        status_result = status_response.json()
        print(f"✅ Session status: {status_result.get('status', 'unknown')}")
        
        # Summary
        print("\n📊 E2E Test Results:")
        print(f"   Negotiation Started: ✅")
        print(f"   Budget Display: {'✅' if budget_mentioned else '❌'}")
        print(f"   Proposal Generation: ✅")
        print(f"   Budget Respect: {'✅' if proposal_within_budget else '❌'}")
        print(f"   Counter-offer Handling: ✅")
        print(f"   Budget Constraint Enforcement: {'✅' if budget_constraint_mentioned else '❌'}")
        
        all_passed = all([
            budget_mentioned,
            proposal_within_budget,
            budget_constraint_mentioned
        ])
        
        return all_passed
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on port 8000.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Run the end-to-end test"""
    print("🎯 End-to-End Budget Constraint Test")
    print("=" * 60)
    
    success = test_e2e_budget_constraint()
    
    if success:
        print("\n🎉 END-TO-END TEST PASSED!")
        print("✅ Currency accuracy and budget constraints are working correctly in the live system.")
    else:
        print("\n⚠️  END-TO-END TEST FAILED!")
        print("❌ Some issues detected in the live system.")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
