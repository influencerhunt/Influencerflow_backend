#!/usr/bin/env python3
"""
Debug script to test contract generation in conversation handler
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_handler import ConversationHandler
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, 
    ContentType, LocationType, NegotiationStatus
)
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_contract_generation():
    """Test contract generation in acceptance flow"""
    
    # Create test data
    brand = BrandDetails(
        name="TestBrand",
        brand_location=LocationType.US,
        budget=5000.0,
        goals=["brand_awareness", "engagement"],
        target_platforms=[PlatformType.INSTAGRAM],
        content_requirements={PlatformType.INSTAGRAM: [ContentType.INSTAGRAM_POST]},
        campaign_duration_days=30
    )
    
    influencer = InfluencerProfile(
        name="TestInfluencer",
        location=LocationType.US,
        followers=100000,
        engagement_rate=0.03,
        platforms=[PlatformType.INSTAGRAM]
    )
    
    # Create conversation handler
    handler = ConversationHandler()
    
    try:
        # Create session
        session_id = handler.create_session(brand, influencer)
        print(f"✅ Session created: {session_id}")
        
        # Generate greeting
        greeting = handler.generate_greeting_message(session_id)
        print(f"✅ Greeting generated")
        
        # Generate proposal
        proposal = handler.generate_proposal(session_id)
        print(f"✅ Proposal generated")
        
        # Test acceptance (this should trigger contract generation)
        print("\n🎯 Testing acceptance and contract generation...")
        acceptance_response = handler._handle_acceptance(session_id)
        print(f"✅ Acceptance handled")
        
        # Check if contract was mentioned in response
        if "Contract ID" in acceptance_response:
            print("✅ CONTRACT GENERATION SUCCESSFUL!")
            print(f"Response contains contract info: {acceptance_response[:200]}...")
        elif "2 business days" in acceptance_response:
            print("❌ CONTRACT GENERATION FAILED - Fallback message detected")
            print(f"Response: {acceptance_response[:200]}...")
        else:
            print("❓ UNCLEAR RESPONSE")
            print(f"Response: {acceptance_response[:200]}...")
            
        # Check session state
        session = handler.get_session_state(session_id)
        if session and session.status == NegotiationStatus.AGREED:
            print(f"✅ Session status correctly set to AGREED")
        else:
            print(f"❌ Session status issue: {session.status if session else 'No session'}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_contract_generation()
