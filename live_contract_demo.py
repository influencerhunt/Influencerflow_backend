#!/usr/bin/env python3
"""
Real-time Contract Generation Demo
Shows how contracts are automatically generated from negotiations
"""

from app.services.conversation_handler import ConversationHandler
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, 
    ContentType, LocationType
)

def demonstrate_real_time_contract_generation():
    print("🚀 REAL-TIME CONTRACT GENERATION FROM NEGOTIATION")
    print("=" * 60)
    
    # Initialize handler
    handler = ConversationHandler()
    
    # Create realistic brand and influencer
    brand = BrandDetails(
        name="TechFlow Innovations",
        brand_location=LocationType.US,
        budget=3000.0,
        goals=["brand_awareness", "product_launch"],
        target_platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE],
        content_requirements={
            PlatformType.INSTAGRAM: [ContentType.INSTAGRAM_POST, ContentType.INSTAGRAM_REEL],
            PlatformType.YOUTUBE: [ContentType.YOUTUBE_LONG_FORM]
        },
        campaign_duration_days=30
    )
    
    influencer = InfluencerProfile(
        name="Sarah TechReview",
        location=LocationType.US,
        followers=95000,
        engagement_rate=0.045,
        platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE]
    )
    
    print("📝 STEP 1: Creating Negotiation Session...")
    session_id = handler.create_session(brand, influencer)
    print(f"✅ Session Created: {session_id}")
    print()
    
    print("📝 STEP 2: Brand Makes Initial Proposal...")
    proposal = handler.generate_proposal(session_id)
    print("✅ Brand's Proposal:")
    print("-" * 40)
    # Show first part of proposal
    lines = proposal.split('\n')
    for line in lines[:15]:  # Show first 15 lines
        print(line)
    print("... (proposal continues)")
    print()
    
    print("📝 STEP 3: Influencer Accepts → TRIGGERS CONTRACT GENERATION!")
    print("Influencer Response: 'This looks perfect! I accept the offer.'")
    print()
    
    # This is where the magic happens - contract auto-generation
    print("🔄 Processing acceptance... GENERATING CONTRACT...")
    acceptance_response = handler.handle_user_input(session_id, "This looks perfect! I accept the offer.")
    
    print("🎉 LIVE CONTRACT GENERATION RESULT:")
    print("=" * 60)
    print(acceptance_response)
    print()
    
    # Extract contract ID if generated
    if "Contract ID:" in acceptance_response:
        lines = acceptance_response.split('\n')
        for line in lines:
            if "Contract ID:" in line:
                contract_id = line.split('`')[1] if '`' in line else "ID_NOT_FOUND"
                print(f"📄 CONTRACT SUCCESSFULLY GENERATED!")
                print(f"   Contract ID: {contract_id}")
                print(f"   Status: Ready for signatures")
                print(f"   Available via API: /contracts/{contract_id}")
                break
    
    print("\n✅ REAL-TIME FLOW COMPLETE!")
    print("The contract was automatically generated the moment the influencer accepted!")

if __name__ == "__main__":
    demonstrate_real_time_contract_generation()
