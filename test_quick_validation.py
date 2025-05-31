#!/usr/bin/env python3
"""
Quick validation test for budget constraints and currency accuracy fixes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pricing_service import PricingService
from app.services.conversation_handler import ConversationHandler
from app.models.negotiation_models import (
    InfluencerProfile, BrandDetails, LocationType, PlatformType, ContentType
)

def test_budget_constraint_enforcement():
    """Test that budget constraints are strictly enforced."""
    print("🔒 Testing Budget Constraint Enforcement...")
    
    # Create services
    pricing_service = PricingService()
    
    # Create Indian influencer
    influencer = InfluencerProfile(
        name="Test Creator",
        followers=50000,
        engagement_rate=0.052,  # 5.2% as decimal
        location=LocationType.INDIA,
        platforms=[PlatformType.INSTAGRAM]
    )
    
    # Create brand with small budget (₹7,500 = ~$90.36 USD)
    brand_budget_inr = 7500
    brand_budget_usd = pricing_service.convert_to_usd(brand_budget_inr, "INR")
    
    content_requirements = {
        "instagram_reel": 1,
        "instagram_post": 2
    }
    
    print(f"   Brand Budget: ₹{brand_budget_inr:,} = ${brand_budget_usd:.2f} USD")
    
    # Generate proposal with budget constraint
    proposal = pricing_service.generate_location_specific_proposal(
        influencer, content_requirements, brand_budget_usd
    )
    
    final_cost = proposal["total_cost"]
    print(f"   Proposed Cost: ${final_cost:.2f} USD")
    print(f"   Budget Respected: {'✅' if final_cost <= brand_budget_usd else '❌'}")
    
    if final_cost > brand_budget_usd:
        print(f"   ERROR: Cost ${final_cost:.2f} exceeds budget ${brand_budget_usd:.2f}")
        return False
    else:
        print(f"   SUCCESS: Cost is within budget limit")
        return True

def test_currency_accuracy():
    """Test currency formatting accuracy."""
    print("\n💱 Testing Currency Accuracy...")
    
    pricing_service = PricingService()
    
    # Test USD to INR conversion
    usd_amount = 100.0
    inr_amount = pricing_service.convert_from_usd(usd_amount, "INR")
    formatted_inr = pricing_service.format_currency(inr_amount, "INR")
    
    print(f"   ${usd_amount} USD = {formatted_inr}")
    
    # Test INR to USD conversion
    inr_test = 7500
    usd_converted = pricing_service.convert_to_usd(inr_test, "INR")
    formatted_usd = pricing_service.format_currency(usd_converted, "USD")
    
    print(f"   ₹{inr_test:,} = {formatted_usd}")
    
    # Verify round-trip accuracy
    back_to_inr = pricing_service.convert_from_usd(usd_converted, "INR")
    accuracy_check = abs(back_to_inr - inr_test) < 1.0  # Allow 1 rupee difference for rounding
    
    print(f"   Round-trip Accuracy: {'✅' if accuracy_check else '❌'}")
    return accuracy_check

def test_counter_offer_budget_respect():
    """Test that counter-offer handling respects budget limits."""
    print("\n🤝 Testing Counter-Offer Budget Respect...")
    
    conversation_handler = ConversationHandler()
    
    # Create test session
    influencer = InfluencerProfile(
        name="Test Creator 2",
        followers=75000,
        engagement_rate=0.061,  # 6.1% as decimal
        location=LocationType.INDIA,
        platforms=[PlatformType.INSTAGRAM]
    )
    
    brand = BrandDetails(
        name="Test Brand",
        budget=90.36,  # $90.36 USD (equivalent to ₹7,500)
        goals=["engagement", "awareness"],
        target_platforms=[PlatformType.INSTAGRAM],
        content_requirements={"instagram_reel": 1, "instagram_post": 1},
        campaign_duration_days=30
    )
    
    session_id = conversation_handler.create_session(brand, influencer)
    
    # Generate initial proposal
    proposal_msg = conversation_handler.generate_proposal(session_id)
    print(f"   Initial proposal generated: {'✅' if proposal_msg else '❌'}")
    
    # Test counter offer above budget
    session = conversation_handler.active_sessions[session_id]
    if session and session.current_offer:
        original_price = session.current_offer.total_price
        print(f"   Original offer: ${original_price:.2f} USD")
        
        # Test with counter-offer way above budget (₹15,000 = ~$180 USD)
        high_counter_msg = conversation_handler._handle_counter_offer(
            session_id, "I was thinking more like ₹15,000 for this campaign"
        )
        
        # Check if response mentions budget constraint
        budget_respected = "budget" in high_counter_msg.lower() or "constraint" in high_counter_msg.lower()
        print(f"   Budget constraint mentioned in response: {'✅' if budget_respected else '❌'}")
        
        return budget_respected
    
    return False

def main():
    """Run all validation tests."""
    print("🎯 Quick Validation of Currency & Budget Fixes")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(test_budget_constraint_enforcement())
    results.append(test_currency_accuracy())
    results.append(test_counter_offer_budget_respect())
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Currency accuracy and budget constraints are working correctly.")
    else:
        print("⚠️  Some tests failed. Review the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
