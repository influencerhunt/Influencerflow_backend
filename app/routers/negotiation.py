from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Union
from app.agents.negotiation_agent import AdvancedNegotiationAgent
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, LocationType
)
from app.services.pricing_service import PricingService

router = APIRouter()
negotiation_agent = AdvancedNegotiationAgent()
pricing_service = PricingService()

# Simple pydantic models for FastAPI request validation
class BrandDetailsRequest(BaseModel):
    name: str
    budget: Union[str, float]  # Accept both string (₹7,500) and float (7500)
    goals: List[str]
    target_platforms: List[str]
    content_requirements: Dict[str, int]
    campaign_duration_days: int = 30
    target_audience: Optional[str] = None
    brand_guidelines: Optional[str] = None
    brand_location: Optional[str] = None  # Brand's country for currency handling

class InfluencerProfileRequest(BaseModel):
    name: str
    followers: int
    engagement_rate: float
    location: str
    platforms: List[str]
    niches: List[str] = []
    previous_brand_collaborations: int = 0

class StartNegotiationRequest(BaseModel):
    brand_details: BrandDetailsRequest
    influencer_profile: InfluencerProfileRequest

class ContinueConversationRequest(BaseModel):
    session_id: str
    user_input: str

@router.post("/start")
async def start_negotiation(request: StartNegotiationRequest):
    """Start a new negotiation session."""
    try:
        # Helper function to map location strings to LocationType
        def map_location(location_str: str) -> LocationType:
            location_mapping = {
                "india": LocationType.INDIA,
                "us": LocationType.US,
                "usa": LocationType.US,
                "united states": LocationType.US,
                "uk": LocationType.UK,
                "united kingdom": LocationType.UK,
                "canada": LocationType.CANADA,
                "australia": LocationType.AUSTRALIA,
                "germany": LocationType.GERMANY,
                "france": LocationType.FRANCE,
                "brazil": LocationType.BRAZIL,
                "japan": LocationType.JAPAN,
            }
            
            normalized = location_str.lower().strip()
            return location_mapping.get(normalized, LocationType.OTHER)
        
        # Convert pydantic models to domain dataclasses
        # Parse budget with currency conversion
        budget_usd, original_currency = pricing_service.parse_budget_amount(request.brand_details.budget)
        
        # Determine brand location from input or budget currency
        brand_location = LocationType.OTHER  # Default
        if request.brand_details.brand_location:
            brand_location = map_location(request.brand_details.brand_location)
        elif original_currency != "USD":
            # Infer brand location from currency if not provided
            currency_to_location = {
                "INR": LocationType.INDIA,
                "EUR": LocationType.GERMANY,  # Default to Germany for EUR
                "GBP": LocationType.UK,
                "CAD": LocationType.CANADA,
                "AUD": LocationType.AUSTRALIA,
                "BRL": LocationType.BRAZIL,
                "JPY": LocationType.JAPAN
            }
            brand_location = currency_to_location.get(original_currency, LocationType.OTHER)
        
        brand_details = BrandDetails(
            name=request.brand_details.name,
            budget=budget_usd,  # Now in USD
            goals=request.brand_details.goals,
            target_platforms=[PlatformType(p.lower()) for p in request.brand_details.target_platforms],
            content_requirements=request.brand_details.content_requirements,
            campaign_duration_days=request.brand_details.campaign_duration_days,
            target_audience=request.brand_details.target_audience,
            brand_guidelines=request.brand_details.brand_guidelines,
            brand_location=brand_location
        )
        
        influencer_profile = InfluencerProfile(
            name=request.influencer_profile.name,
            followers=request.influencer_profile.followers,
            engagement_rate=request.influencer_profile.engagement_rate,
            location=map_location(request.influencer_profile.location),
            platforms=[PlatformType(p.lower()) for p in request.influencer_profile.platforms],
            niches=request.influencer_profile.niches,
            previous_brand_collaborations=request.influencer_profile.previous_brand_collaborations
        )
        
        # Start negotiation
        result = await negotiation_agent.start_negotiation_conversation(
            brand_details, influencer_profile
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Negotiation failed: {str(e)}")

@router.post("/continue")
async def continue_conversation(request: ContinueConversationRequest):
    """Continue an existing negotiation conversation."""
    try:
        result = await negotiation_agent.continue_conversation(
            request.session_id, request.user_input
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")

@router.get("/session/{session_id}/summary")
async def get_negotiation_summary(session_id: str):
    """Get summary of negotiation session."""
    try:
        summary = await negotiation_agent.get_conversation_summary(session_id)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific negotiation session."""
    try:
        result = negotiation_agent.clear_session(session_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")

@router.get("/sessions")
async def list_active_sessions():
    """List all active negotiation sessions."""
    try:
        result = negotiation_agent.list_active_sessions()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@router.get("/platforms")
async def get_platform_details():
    """Get available platforms and their content types."""
    return {
        "platforms": {
            "instagram": {
                "name": "Instagram",
                "content_types": ["post", "reel", "story"],
                "description": "Visual social media platform"
            },
            "youtube": {
                "name": "YouTube",
                "content_types": ["long_form", "shorts"],
                "description": "Video sharing platform"
            },
            "linkedin": {
                "name": "LinkedIn",
                "content_types": ["post", "video"],
                "description": "Professional networking platform"
            },
            "tiktok": {
                "name": "TikTok",
                "content_types": ["video"],
                "description": "Short-form video platform"
            },
            "twitter": {
                "name": "Twitter",
                "content_types": ["post", "video"],
                "description": "Microblogging platform"
            }
        }
    }

@router.get("/locations")
async def get_supported_locations():
    """Get supported influencer locations."""
    return {
        "locations": [
            {"code": "US", "name": "United States", "multiplier": 1.8},
            {"code": "UK", "name": "United Kingdom", "multiplier": 1.6},
            {"code": "CANADA", "name": "Canada", "multiplier": 1.5},
            {"code": "AUSTRALIA", "name": "Australia", "multiplier": 1.4},
            {"code": "GERMANY", "name": "Germany", "multiplier": 1.3},
            {"code": "FRANCE", "name": "France", "multiplier": 1.2},
            {"code": "JAPAN", "name": "Japan", "multiplier": 1.1},
            {"code": "BRAZIL", "name": "Brazil", "multiplier": 0.8},
            {"code": "INDIA", "name": "India", "multiplier": 0.6},
            {"code": "OTHER", "name": "Other", "multiplier": 1.0}
        ]
    }

# Mock data endpoint for testing
@router.post("/test/mock-negotiation")
async def create_mock_negotiation():
    """Create a mock negotiation for testing purposes."""
    try:
        # Mock brand details
        brand = BrandDetails(
            name="EcoTech Solutions",
            budget=8000.0,
            goals=["brand awareness", "product launch", "engagement boost"],
            target_platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE],
            content_requirements={
                "instagram_post": 4,
                "instagram_reel": 3,
                "youtube_shorts": 2
            },
            campaign_duration_days=45,
            target_audience="Tech-savvy millennials interested in sustainability",
            brand_guidelines="Authentic, educational content focusing on environmental impact"
        )
        
        # Mock influencer profile
        influencer = InfluencerProfile(
            name="Alex Green",
            followers=75000,
            engagement_rate=0.065,
            location=LocationType.US,
            platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE],
            niches=["sustainability", "technology", "lifestyle"],
            previous_brand_collaborations=12
        )
        
        # Start negotiation
        result = await negotiation_agent.start_negotiation_conversation(brand, influencer)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mock negotiation failed: {str(e)}")
