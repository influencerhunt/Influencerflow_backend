"""
Example usage of the Advanced Negotiation Agent for Influencer Marketing

This script demonstrates how to use the negotiation agent to facilitate
conversations between brands and influencers for collaboration deals.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.agents.negotiation_agent import AdvancedNegotiationAgent
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, LocationType
)

async def demo_negotiation():
    """Demonstrate a complete negotiation flow."""
    
    print("🎯 Starting Influencer Marketing Negotiation Demo\n")
    
    # Initialize the agent
    agent = AdvancedNegotiationAgent()
    
    # Create sample brand details
    brand = BrandDetails(
        name="GreenTech Innovations",
        budget=12000.0,
        goals=["brand awareness", "product launch", "sustainability messaging"],
        target_platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE, PlatformType.LINKEDIN],
        content_requirements={
            "instagram_post": 5,
            "instagram_reel": 4,
            "instagram_story": 8,
            "youtube_shorts": 3,
            "linkedin_post": 2
        },
        campaign_duration_days=60,
        target_audience="Environmentally conscious millennials and Gen Z",
        brand_guidelines="Authentic content showcasing sustainability, innovation, and positive environmental impact"
    )
    
    # Create sample influencer profile
    influencer = InfluencerProfile(
        name="Sarah EcoLiving",
        followers=125000,
        engagement_rate=0.078,  # 7.8% engagement rate
        location=LocationType.US,
        platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE, PlatformType.LINKEDIN],
        niches=["sustainability", "zero waste", "green technology", "environmental advocacy"],
        previous_brand_collaborations=25
    )
    
    print(f"Brand: {brand.name}")
    print(f"Budget: ${brand.budget:,.2f}")
    print(f"Goals: {', '.join(brand.goals)}")
    print(f"Target Platforms: {', '.join([p.value.title() for p in brand.target_platforms])}")
    print(f"Campaign Duration: {brand.campaign_duration_days} days\n")
    
    print(f"Influencer: {influencer.name}")
    print(f"Followers: {influencer.followers:,}")
    print(f"Engagement Rate: {influencer.engagement_rate:.1%}")
    print(f"Location: {influencer.location.value}")
    print(f"Niches: {', '.join(influencer.niches)}\n")
    
    print("=" * 60)
    print("🤖 MAYA (Negotiation Agent) STARTS CONVERSATION")
    print("=" * 60)
    
    # Start the negotiation
    try:
        result = await agent.start_negotiation_conversation(brand, influencer)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        session_id = result["session_id"]
        print(f"\n{result['message']}")
        
        # Simulate a conversation flow
        conversation_flow = [
            {
                "user": "Hi Maya! This looks like an exciting opportunity. I'm definitely interested in working with GreenTech Innovations. The pricing seems quite competitive. I do have a few questions though - could we discuss the timeline for the Instagram reels? I typically need about 3-4 days per reel to ensure high quality content.",
                "description": "💭 Influencer shows interest and asks about timeline"
            },
            {
                "user": "That timeline works perfectly for me! I'm also wondering about the usage rights. The 6 months social media usage sounds reasonable, but would the brand be interested in extending this for an additional fee? I find that brands often want to repurpose content for longer campaigns.",
                "description": "💭 Influencer negotiates usage rights"
            },
            {
                "user": "I really appreciate the thorough breakdown and the flexibility on usage rights! Everything looks great. I'd like to move forward with this collaboration. When can we get the contract and creative brief?",
                "description": "💭 Influencer accepts the proposal"
            }
        ]
        
        for i, interaction in enumerate(conversation_flow, 1):
            print(f"\n{'-' * 40}")
            print(f"ROUND {i}: {interaction['description']}")
            print(f"{'-' * 40}")
            print(f"\n👤 INFLUENCER: {interaction['user']}")
            
            # Get agent response
            response = await agent.continue_conversation(session_id, interaction['user'])
            
            if "error" in response:
                print(f"❌ Error: {response['error']}")
                break
            
            print(f"\n🤖 MAYA: {response['message']}")
            print(f"\n📊 Status: {response['status'].upper()}")
            print(f"🔄 Round: {response['negotiation_round']}")
            print(f"🎭 Stage: {response['conversation_stage']}")
            
            # If negotiation is complete, break
            if response["status"] in ["agreed", "rejected"]:
                break
        
        # Get final summary
        print(f"\n{'=' * 60}")
        print("📋 FINAL NEGOTIATION SUMMARY")
        print(f"{'=' * 60}")
        
        summary = await agent.get_conversation_summary(session_id)
        
        if "error" not in summary:
            print(f"Session ID: {summary['session_id']}")
            print(f"Final Status: {summary['status'].upper()}")
            print(f"Brand: {summary['brand']}")
            print(f"Influencer: {summary['influencer']}")
            print(f"Negotiation Rounds: {summary['negotiation_round']}")
            print(f"Conversation Length: {summary['conversation_length']} messages")
            
            if summary.get('agreed_terms'):
                terms = summary['agreed_terms']
                print(f"\n💰 Agreed Total: ${terms['total_price']:,.2f}")
                print(f"📅 Duration: {terms['campaign_duration_days']} days")
                print(f"💳 Payment Terms: {terms['payment_terms']}")
                print(f"🔄 Revisions: {terms['revisions_included']}")
                print(f"🔒 Usage Rights: {terms['usage_rights']}")
        
        print(f"\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

async def test_pricing_scenarios():
    """Test different pricing scenarios."""
    
    print("\n🧮 TESTING PRICING SCENARIOS\n")
    
    agent = AdvancedNegotiationAgent()
    
    # Test cases with different influencer profiles
    test_cases = [
        {
            "name": "Micro-Influencer (Tech)",
            "profile": InfluencerProfile(
                name="TechReviewer_Mike",
                followers=15000,
                engagement_rate=0.095,  # High engagement
                location=LocationType.US,
                platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE],
                niches=["technology", "gadgets"]
            ),
            "content": {"instagram_post": 2, "youtube_shorts": 1}
        },
        {
            "name": "Mid-Tier Influencer (Lifestyle)",
            "profile": InfluencerProfile(
                name="LifestyleLisa",
                followers=85000,
                engagement_rate=0.065,
                location=LocationType.UK,
                platforms=[PlatformType.INSTAGRAM, PlatformType.LINKEDIN],
                niches=["lifestyle", "wellness"]
            ),
            "content": {"instagram_reel": 3, "linkedin_post": 2}
        },
        {
            "name": "Macro-Influencer (Fashion)",
            "profile": InfluencerProfile(
                name="FashionForward_Anna",
                followers=250000,
                engagement_rate=0.045,
                location=LocationType.FRANCE,
                platforms=[PlatformType.INSTAGRAM],
                niches=["fashion", "beauty"]
            ),
            "content": {"instagram_post": 4, "instagram_reel": 2, "instagram_story": 6}
        }
    ]
    
    for test_case in test_cases:
        print(f"📊 {test_case['name']}")
        print(f"   Followers: {test_case['profile'].followers:,}")
        print(f"   Engagement: {test_case['profile'].engagement_rate:.1%}")
        print(f"   Location: {test_case['profile'].location.value}")
        
        # Calculate pricing using the pricing service
        cost_breakdown = agent.pricing_service.calculate_total_campaign_cost(
            test_case['profile'], 
            test_case['content']
        )
        
        print(f"   💰 Total Cost: ${cost_breakdown['total_cost']:,.2f}")
        
        for content_type, details in cost_breakdown['item_breakdown'].items():
            print(f"      • {content_type.replace('_', ' ').title()}: ${details['unit_rate']:.2f} × {details['quantity']} = ${details['total']:.2f}")
        
        print()

if __name__ == "__main__":
    print("🚀 Advanced Influencer Marketing Negotiation Agent Demo")
    print("=" * 60)
    
    # Check if required environment variables are set
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        print("Please set your Google Gemini API key in the .env file")
        exit(1)
    
    # Run the demos
    asyncio.run(demo_negotiation())
    asyncio.run(test_pricing_scenarios())
    
    print("\n🎉 All demos completed!")
    print("💡 Try running the FastAPI server with: uvicorn main:app --reload")
    print("📚 Check the API documentation at: http://localhost:8000/docs")
