from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.agents import AdvancedNegotiationAgent
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, LocationType
)
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()
negotiation_agent = AdvancedNegotiationAgent()

# Voice call session mapping: call_sid -> negotiation_session_id
voice_call_sessions: Dict[str, str] = {}

# Active voice calls tracking
active_voice_calls: Dict[str, Dict] = {}

# Simple pydantic models for FastAPI request validation
class BrandDetailsRequest(BaseModel):
    name: str
    budget: float
    goals: List[str]
    target_platforms: List[str]
    content_requirements: Dict[str, int]
    campaign_duration_days: int = 30
    target_audience: Optional[str] = None
    brand_guidelines: Optional[str] = None

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

class VoiceCallRequest(BaseModel):
    to_number: str
    brand_details: BrandDetailsRequest
    influencer_profile: InfluencerProfileRequest
    webhook_base_url: str

def _create_gather_twiml(action_endpoint: str):
    """Create a standardized Gather TwiML element"""
    try:
        from twilio.twiml.voice_response import Gather
        return Gather(
            input="speech",
            action=action_endpoint,
            method="POST",
            timeout=30,
            speechTimeout=5,
            partialResultCallback="/api/v1/negotiation-fixed/voice/partial",
            partialResultCallbackMethod="POST",
            enhanced=True,
            language="en-IN",
            speechModel="phone_call",
            profanityFilter=False,
            hints="rupees, lakhs, crores, price, rate, amount, cost, budget, negotiation, deal, partnership, instagram, posts, endorsement, influencer, marketing, brand, collaboration, sponsored, content, social media, followers, engagement, reach"
        )
    except ImportError:
        return None

# Regular negotiation endpoints (existing)
@router.post("/start")
async def start_negotiation(request: StartNegotiationRequest):
    """Start a new negotiation session."""
    try:
        # Convert pydantic models to domain dataclasses
        brand_details = BrandDetails(
            name=request.brand_details.name,
            budget=request.brand_details.budget,
            goals=request.brand_details.goals,
            target_platforms=[PlatformType(p.lower()) for p in request.brand_details.target_platforms],
            content_requirements=request.brand_details.content_requirements,
            campaign_duration_days=request.brand_details.campaign_duration_days,
            target_audience=request.brand_details.target_audience,
            brand_guidelines=request.brand_details.brand_guidelines
        )
        influencer_profile = InfluencerProfile(
            name=request.influencer_profile.name,
            followers=request.influencer_profile.followers,
            engagement_rate=request.influencer_profile.engagement_rate,
            location=LocationType(request.influencer_profile.location.upper()),
            platforms=[PlatformType(p.lower()) for p in request.influencer_profile.platforms],
            niches=request.influencer_profile.niches,
            previous_brand_collaborations=request.influencer_profile.previous_brand_collaborations
        )
        # Start negotiation
        print(f"Brand details: {brand_details}")
        print(f"Influencer profile: {influencer_profile}")
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

# Voice call endpoints (new)
@router.post("/voice/start-call")
async def start_voice_call(request: VoiceCallRequest):
    """Start a voice call with negotiation capabilities."""
    try:
        # Import here to avoid dependency issues
        try:
            from twilio.rest import Client
            import os
            
            # Initialize Twilio client (using environment variables)
            twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "dummy_sid")
            twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "dummy_token") 
            twilio_number = os.getenv("TWILIO_NUMBER", "+1234567890")
            
            if all([twilio_account_sid != "dummy_sid", twilio_auth_token != "dummy_token"]):
                twilio_client = Client(twilio_account_sid, twilio_auth_token)
            else:
                twilio_client = None
                logger.warning("Using mock mode for voice call - no real Twilio credentials")
        except ImportError:
            twilio_client = None
            logger.warning("Twilio library not installed - using mock mode")
        
        # Convert pydantic models to domain dataclasses  
        brand_details = BrandDetails(
            name=request.brand_details.name,
            budget=request.brand_details.budget,
            goals=request.brand_details.goals,
            target_platforms=[PlatformType(p.lower()) for p in request.brand_details.target_platforms],
            content_requirements=request.brand_details.content_requirements,
            campaign_duration_days=request.brand_details.campaign_duration_days,
            target_audience=request.brand_details.target_audience,
            brand_guidelines=request.brand_details.brand_guidelines
        )
        
        influencer_profile = InfluencerProfile(
            name=request.influencer_profile.name,
            followers=request.influencer_profile.followers,
            engagement_rate=request.influencer_profile.engagement_rate,
            location=LocationType(request.influencer_profile.location.upper()),
            platforms=[PlatformType(p.lower()) for p in request.influencer_profile.platforms],
            niches=request.influencer_profile.niches,
            previous_brand_collaborations=request.influencer_profile.previous_brand_collaborations
        )
        
        # Start negotiation session
        negotiation_result = await negotiation_agent.start_negotiation_conversation(
            brand_details, influencer_profile
        )
        
        if "error" in negotiation_result:
            raise HTTPException(status_code=500, detail=f"Failed to start negotiation: {negotiation_result['error']}")
        
        negotiation_session_id = negotiation_result["session_id"]
        
        # Make the voice call
        if twilio_client:
            try:
                call = twilio_client.calls.create(
                    to=request.to_number,
                    from_=twilio_number,
                    url=f"{request.webhook_base_url.rstrip('/')}/api/v1/negotiation-fixed/voice/inbound"
                )
                call_sid = call.sid
                logger.info(f"Real call initiated with SID: {call_sid}")
            except Exception as e:
                logger.error(f"Error making real call: {e}")
                call_sid = f"MOCK_CALL_{uuid.uuid4().hex[:8]}"
        else:
            # Mock call
            call_sid = f"MOCK_CALL_{uuid.uuid4().hex[:8]}"
            logger.info(f"Mock call initiated with SID: {call_sid}")
        
        # Link call to negotiation session
        voice_call_sessions[call_sid] = negotiation_session_id
        active_voice_calls[call_sid] = {
            "negotiation_session_id": negotiation_session_id,
            "to_number": request.to_number,
            "status": "initiated",
            "brand_name": brand_details.name,
            "influencer_name": influencer_profile.name
        }
        
        return {
            "success": True,
            "call_sid": call_sid,
            "negotiation_session_id": negotiation_session_id,
            "message": f"Voice call initiated to {request.to_number}",
            "initial_negotiation_message": negotiation_result["message"]
        }
        
    except Exception as e:
        logger.error(f"Error starting voice call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/inbound")
async def voice_inbound_webhook(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(default=""),
    To: str = Form(default="")
):
    """Twilio webhook for incoming voice calls."""
    try:
        logger.info(f"Voice webhook called for CallSid: {CallSid}")
        
        # Import here to avoid dependency issues
        try:
            from twilio.twiml.voice_response import VoiceResponse
        except ImportError:
            logger.error("Twilio library not installed")
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service temporarily unavailable</Say></Response>',
                media_type="application/xml"
            )
        
        # Check if we have a linked negotiation session
        negotiation_session_id = voice_call_sessions.get(CallSid)
        
        if not negotiation_session_id:
            # If no existing session, this might be a direct inbound call
            # Create a default negotiation session
            default_brand = BrandDetails(
                name="Your Company",
                budget=5000.0,
                goals=["brand awareness", "engagement"],
                target_platforms=[PlatformType.INSTAGRAM],
                content_requirements={"instagram_post": 3},
                campaign_duration_days=30,
                target_audience="General audience",
                brand_guidelines="Professional content"
            )
            
            default_influencer = InfluencerProfile(
                name="Influencer",
                followers=50000,
                engagement_rate=0.05,
                location=LocationType.OTHER,
                platforms=[PlatformType.INSTAGRAM],
                niches=["general"]
            )
            
            negotiation_result = await negotiation_agent.start_negotiation_conversation(
                default_brand, default_influencer
            )
            
            negotiation_session_id = negotiation_result["session_id"]
            voice_call_sessions[CallSid] = negotiation_session_id
            active_voice_calls[CallSid] = {
                "negotiation_session_id": negotiation_session_id,
                "status": "active",
                "from_number": From
            }
        
        # Get the negotiation session summary to provide context
        summary = await negotiation_agent.get_conversation_summary(negotiation_session_id)
        
        # Create TwiML response
        twiml = VoiceResponse()
        gather = _create_gather_twiml("/api/v1/negotiation-fixed/voice/gather")
        
        if gather:
            # Get initial greeting from the negotiation agent
            if summary and not summary.get("error"):
                greeting_message = f"Hello! I'm calling from {summary.get('brand', 'our company')} to discuss a potential collaboration opportunity. I'm excited to talk with you about an influencer partnership. How are you doing today?"
            else:
                greeting_message = "Hello! I'm calling to discuss a potential influencer collaboration opportunity. How are you doing today?"
            
            gather.say(greeting_message, voice="alice", language="en-IN")
            twiml.append(gather)
        else:
            twiml.say("Service temporarily unavailable", voice="alice", language="en-IN")
        
        return Response(content=str(twiml), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in voice webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/voice/gather")
async def voice_gather_webhook(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(default="")
):
    """Twilio webhook for gathering speech input."""
    try:
        logger.info(f"Gather webhook called for CallSid: {CallSid}, Speech: {SpeechResult}")
        
        # Import here to avoid dependency issues
        try:
            from twilio.twiml.voice_response import VoiceResponse
        except ImportError:
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service temporarily unavailable</Say></Response>',
                media_type="application/xml"
            )
        
        twiml = VoiceResponse()
        
        # Get the linked negotiation session
        negotiation_session_id = voice_call_sessions.get(CallSid)
        
        if not negotiation_session_id:
            logger.error(f"No negotiation session found for CallSid: {CallSid}")
            twiml.say(
                "Sorry, our session got disconnected. Please call back to continue our discussion.",
                voice="alice", language="en-IN"
            )
            return Response(content=str(twiml), media_type="application/xml")
        
        # If no speech detected, continue listening
        if not SpeechResult:
            logger.debug(f"No speech detected for CallSid: {CallSid}")
            gather_continue = _create_gather_twiml("/api/v1/negotiation-fixed/voice/gather")
            
            if gather_continue:
                gather_continue.say(
                    "I'm still here and listening. Please share your thoughts about this collaboration opportunity.",
                    voice="alice", language="en-IN"
                )
                twiml.append(gather_continue)
            else:
                twiml.say("Please try again", voice="alice", language="en-IN")
            return Response(content=str(twiml), media_type="application/xml")
        
        try:
            # Send user input to negotiation agent
            negotiation_response = await negotiation_agent.continue_conversation(
                negotiation_session_id, SpeechResult
            )
            
            if "error" in negotiation_response:
                response_text = "I encountered a brief issue. Could you please repeat what you said about the collaboration?"
            else:
                response_text = negotiation_response["message"]
                
                # Update call status if negotiation is complete
                if negotiation_response.get("status") in ["agreed", "rejected"]:
                    if CallSid in active_voice_calls:
                        active_voice_calls[CallSid]["status"] = negotiation_response["status"]
            
            # Create next gather for continued conversation
            gather_next = _create_gather_twiml("/api/v1/negotiation-fixed/voice/gather")
            
            if gather_next:
                gather_next.say(response_text, voice="alice", language="en-IN")
                twiml.append(gather_next)
            else:
                twiml.say(response_text, voice="alice", language="en-IN")
            
        except Exception as e:
            logger.exception("Error getting response from negotiation agent")
            gather_error = _create_gather_twiml("/api/v1/negotiation-fixed/voice/gather")
            
            error_message = "I had a brief technical issue. Could you please repeat what you were saying?"
            
            if gather_error:
                gather_error.say(error_message, voice="alice", language="en-IN")
                twiml.append(gather_error)
            else:
                twiml.say(error_message, voice="alice", language="en-IN")
        
        return Response(content=str(twiml), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in gather webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/voice/partial")
async def voice_partial_webhook(
    request: Request,
    CallSid: str = Form(...),
    UnstableSpeechResult: str = Form(default="")
):
    """Twilio webhook for partial speech results."""
    try:
        logger.debug(f"Partial webhook called for CallSid: {CallSid}, Partial: {UnstableSpeechResult}")
        
        # Just return empty response for partial results
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"Error in partial webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/voice/status/{call_sid}")
async def get_voice_call_status(call_sid: str):
    """Get the status of a voice call and its negotiation."""
    try:
        call_info = active_voice_calls.get(call_sid)
        
        if not call_info:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Get negotiation summary
        negotiation_summary = None
        if call_info.get("negotiation_session_id"):
            summary = await negotiation_agent.get_conversation_summary(
                call_info["negotiation_session_id"]
            )
            if not summary.get("error"):
                negotiation_summary = summary
        
        return {
            "call_sid": call_sid,
            "call_status": call_info.get("status", "unknown"),
            "to_number": call_info.get("to_number"),
            "from_number": call_info.get("from_number"),
            "brand_name": call_info.get("brand_name"),
            "influencer_name": call_info.get("influencer_name"),
            "negotiation_session_id": call_info.get("negotiation_session_id"),
            "negotiation_summary": negotiation_summary
        }
        
    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice/sessions")
async def get_voice_sessions():
    """Get all active voice call sessions."""
    try:
        return {
            "active_voice_calls": len(active_voice_calls),
            "calls": [
                {
                    "call_sid": call_sid,
                    "status": info.get("status", "unknown"),
                    "brand_name": info.get("brand_name"),
                    "influencer_name": info.get("influencer_name"),
                    "negotiation_session_id": info.get("negotiation_session_id")
                }
                for call_sid, info in active_voice_calls.items()
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting voice sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/voice/end-session/{call_sid}")
async def end_voice_session(call_sid: str):
    """End a voice call session."""
    try:
        if call_sid in active_voice_calls:
            negotiation_session_id = active_voice_calls[call_sid].get("negotiation_session_id")
            
            # Clean up voice call tracking
            del active_voice_calls[call_sid]
            
            # Clean up session mapping
            if call_sid in voice_call_sessions:
                del voice_call_sessions[call_sid]
            
            # Optionally clean up negotiation session
            if negotiation_session_id:
                negotiation_agent.clear_session(negotiation_session_id)
            
            return {"message": f"Voice session {call_sid} ended successfully"}
        else:
            raise HTTPException(status_code=404, detail="Voice session not found")
        
    except Exception as e:
        logger.error(f"Error ending voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Original endpoints continue below...
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

@router.post("/test/mock-voice-call")
async def create_mock_voice_call():
    """Create a mock voice call for testing purposes."""
    try:
        # Mock voice call request
        mock_request = VoiceCallRequest(
            to_number="+1234567890",
            webhook_base_url="https://your-app.ngrok.io",
            brand_details=BrandDetailsRequest(
                name="TechBrand Inc",
                budget=5000.0,
                goals=["brand awareness", "product launch"],
                target_platforms=["instagram", "youtube"],
                content_requirements={"instagram_post": 3, "youtube_shorts": 2},
                campaign_duration_days=30,
                target_audience="Tech enthusiasts",
                brand_guidelines="Professional and innovative"
            ),
            influencer_profile=InfluencerProfileRequest(
                name="TechInfluencer",
                followers=50000,
                engagement_rate=0.06,
                location="US",
                platforms=["instagram", "youtube"],
                niches=["technology", "gadgets"],
                previous_brand_collaborations=8
            )
        )
        
        result = await start_voice_call(mock_request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mock voice call failed: {str(e)}")
