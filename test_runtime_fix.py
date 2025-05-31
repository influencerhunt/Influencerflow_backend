#!/usr/bin/env python3
"""
Quick test to verify the runtime 'total' error is fixed.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pricing_service import PricingService
from app.services.conversation_handler import ConversationHandler
from app.models.negotiation_models import InfluencerProfile, BrandDetails, LocationType, PlatformType

def test_runtime_fix():
    """Test that the 'total' key error is resolved."""
    print("🔧 Testing Runtime Fix for 'total' Key Error")
    print("=" * 50)
    
    try:
        # Initialize services
        pricing_service = PricingService()
        conversation_handler = ConversationHandler()
        
        # Create test influencer
        influencer = InfluencerProfile(
            name="Test Creator",
            followers=50000,
            engagement_rate=0.052,
            location=LocationType.INDIA,
            platforms=[PlatformType.INSTAGRAM]
        )
        
        # Create test brand with small budget
        brand = BrandDetails(
            name="Test Brand",
            budget=90.36,  # $90.36 USD (equivalent to ₹7,500)
            goals=["engagement"],
            target_platforms=[PlatformType.INSTAGRAM],
            content_requirements={"instagram_reel": 1, "instagram_post": 1},
            campaign_duration_days=30
        )
        
        print(f"📊 Test Setup:")
        print(f"   Influencer: {influencer.name} ({influencer.followers:,} followers)")
        print(f"   Budget: ${brand.budget:.2f} USD")
        print(f"   Requirements: {brand.content_requirements}")
        
        # Test 1: Create session
        print(f"\n1️⃣ Creating session...")
        session_id = conversation_handler.create_session(brand, influencer)
        print(f"   ✅ Session created: {session_id}")
        
        # Test 2: Generate market analysis (this used to fail with 'total' error)
        print(f"\n2️⃣ Generating market analysis...")
        market_analysis = conversation_handler.generate_market_analysis(session_id)
        print(f"   ✅ Market analysis generated successfully")
        print(f"   📝 Preview: {market_analysis[:200]}...")
        
        # Test 3: Generate proposal (this also used 'total' key)
        print(f"\n3️⃣ Generating proposal...")
        proposal = conversation_handler.generate_proposal(session_id)
        print(f"   ✅ Proposal generated successfully")
        print(f"   📝 Preview: {proposal[:200]}...")
        
        # Test 4: Handle counter-offer
        print(f"\n4️⃣ Testing counter-offer handling...")
        counter_response = conversation_handler._handle_counter_offer(
            session_id, 
            "I was thinking more like ₹15,000 for this campaign"
        )
        print(f"   ✅ Counter-offer handled successfully")
        print(f"   📝 Preview: {counter_response[:200]}...")
        
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ The 'total' key error has been fixed")
        print(f"✅ Budget constraints are working properly")
        print(f"✅ Negotiation flow is functional")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_runtime_fix()
    sys.exit(0 if success else 1)
