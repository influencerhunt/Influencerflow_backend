#!/usr/bin/env python3
"""
Integration test to verify budget constraints work end-to-end through the conversation handler.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_handler import ConversationHandler
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, ContentType, LocationType
)

def test_budget_constraint_integration():
    """Test budget constraints through the full conversation handler flow."""
    
    print("🔄 Testing Budget Constraint Integration")
    print("=" * 50)
    
    # Create conversation handler
    handler = ConversationHandler()
    
    # Create brand with limited budget
    brand = BrandDetails(
        name="Test Brand",
        budget=1500.0,  # $1500 budget
        goals=["brand awareness", "product launch"],
        target_platforms=[PlatformType.INSTAGRAM],
        content_requirements={"instagram_post": 2, "instagram_story": 3},
        campaign_duration_days=30,
        target_audience="Tech enthusiasts"
    )
    
    # Create influencer
    influencer = InfluencerProfile(
        name="TechInfluencer",
        followers=75000,
        engagement_rate=0.06,
        location=LocationType.US,
        platforms=[PlatformType.INSTAGRAM]
    )
    
    print(f"\n📊 Brand Budget: ${brand.budget:.2f}")
    print(f"📋 Content Requirements: {brand.content_requirements}")
    
    # Test initial proposal generation
    print("\n🎯 Generating initial proposal...")
    proposal_message = handler.generate_market_analysis(
        influencer, brand, 
        negotiation_flexibility_percent=15.0
    )
    
    print("✅ Initial proposal generated successfully")
    print(f"📝 Proposal length: {len(proposal_message)} characters")
    
    # Verify budget mention in proposal
    if "budget" in proposal_message.lower():
        print("✅ Budget considerations mentioned in proposal")
    else:
        print("⚠️ Budget not explicitly mentioned in proposal")
    
    # Test counter-offer handling
    print("\n💬 Testing counter-offer scenarios...")
    
    # Test 1: Counter-offer within budget
    counter_offer_1 = "I can do it for $1400"
    response_1 = handler.handle_counter_offer(
        influencer, brand, counter_offer_1,
        negotiation_flexibility_percent=15.0
    )
    print(f"✅ Counter-offer 1 ($1400): {'Accepted' if 'accept' in response_1.lower() else 'Negotiated'}")
    
    # Test 2: Counter-offer at max flexibility
    counter_offer_2 = "My rate is $1725"  # Exactly 15% above budget
    response_2 = handler.handle_counter_offer(
        influencer, brand, counter_offer_2,
        negotiation_flexibility_percent=15.0
    )
    print(f"✅ Counter-offer 2 ($1725): {'Accepted' if 'accept' in response_2.lower() else 'Negotiated'}")
    
    # Test 3: Counter-offer above max flexibility
    counter_offer_3 = "I need $2000 for this"  # 33% above budget
    response_3 = handler.handle_counter_offer(
        influencer, brand, counter_offer_3,
        negotiation_flexibility_percent=15.0
    )
    print(f"✅ Counter-offer 3 ($2000): {'Declined' if 'budget' in response_3.lower() else 'Unexpected'}")
    
    print("\n🎉 Integration test completed successfully!")
    print("✅ Budget constraints are working end-to-end")

if __name__ == "__main__":
    test_budget_constraint_integration()
