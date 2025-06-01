from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
from datetime import datetime

from app.agents.agent import NegotiationAgent
from app.services.supabase_manager import SupabaseManager, log_to_supabase
from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, PlatformType, LocationType, 
    NegotiationStatus, ContentType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/negotiation-agent", tags=["negotiation-agent"])

# Initialize services
negotiation_agent = NegotiationAgent()
supabase_manager = SupabaseManager()

# ==================== REQUEST/RESPONSE MODELS ====================

class BrandDetailsRequest(BaseModel):
    name: str = Field(..., description="Brand name")
    budget: float = Field(..., description="Budget amount in base currency")
    budget_currency: str = Field(default="USD", description="Budget currency code")
    goals: List[str] = Field(..., description="Campaign goals")
    target_platforms: List[str] = Field(..., description="Target social media platforms")
    content_requirements: Dict[str, int] = Field(..., description="Content requirements breakdown")
    campaign_duration_days: int = Field(..., description="Campaign duration in days")
    target_audience: str = Field(..., description="Target audience description")
    brand_guidelines: Optional[str] = Field(default=None, description="Brand guidelines")
    brand_location: str = Field(default="US", description="Brand location")

class InfluencerProfileRequest(BaseModel):
    name: str = Field(..., description="Influencer name")
    followers: int = Field(..., description="Number of followers")
    engagement_rate: float = Field(..., description="Engagement rate (0.0 to 1.0)")
    location: str = Field(..., description="Influencer location")
    platforms: List[str] = Field(..., description="Active platforms")
    niches: List[str] = Field(..., description="Content niches")
    previous_brand_collaborations: int = Field(default=0, description="Number of previous collaborations")

class StartNegotiationRequest(BaseModel):
    brand_details: BrandDetailsRequest
    influencer_profile: InfluencerProfileRequest
    user_id: Optional[str] = Field(default=None, description="User ID for tracking")

class ContinueConversationRequest(BaseModel):
    session_id: str = Field(..., description="Negotiation session ID")
    user_input: str = Field(..., description="User's input/message")
    user_id: Optional[str] = Field(default=None, description="User ID for tracking")

class UpdateDeliverablesRequest(BaseModel):
    session_id: str = Field(..., description="Negotiation session ID")
    deliverables: List[Dict[str, Any]] = Field(..., description="Updated deliverables list")

class UpdateBudgetRequest(BaseModel):
    session_id: str = Field(..., description="Negotiation session ID")
    new_budget: float = Field(..., description="New budget amount")
    currency: str = Field(default="USD", description="Budget currency")
    change_reason: str = Field(..., description="Reason for budget change")

class GenerateContractRequest(BaseModel):
    session_id: str = Field(..., description="Negotiation session ID")
    brand_contact_email: str = Field(..., description="Brand contact email")
    brand_contact_name: str = Field(..., description="Brand contact name")
    influencer_contact: str = Field(..., description="Influencer contact information")

class SessionResponse(BaseModel):
    session_id: str
    status: str
    created_at: str
    brand_name: str
    influencer_name: str
    current_round: int
    is_active: bool

class AnalyticsResponse(BaseModel):
    session_analytics: Optional[Dict[str, Any]] = None
    global_analytics: Optional[Dict[str, Any]] = None
    period: str = "all_time"

# ==================== CORE NEGOTIATION ENDPOINTS ====================

@router.post("/start", response_model=Dict[str, Any])
@log_to_supabase("start_negotiation", "start")
async def start_negotiation(request: StartNegotiationRequest):
    """Start a new negotiation session with comprehensive logging"""
    try:
        # Convert request models to domain models
        brand_details = BrandDetails(
            name=request.brand_details.name,
            budget=request.brand_details.budget,
            budget_currency=request.brand_details.budget_currency,
            goals=request.brand_details.goals,
            target_platforms=[PlatformType(p.lower()) for p in request.brand_details.target_platforms],
            content_requirements=request.brand_details.content_requirements,
            campaign_duration_days=request.brand_details.campaign_duration_days,
            target_audience=request.brand_details.target_audience,
            brand_guidelines=request.brand_details.brand_guidelines,
            brand_location=request.brand_details.brand_location,
            original_budget_amount=request.brand_details.budget
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
        
        # Start negotiation with agent
        result = await negotiation_agent.start_negotiation_conversation(brand_details, influencer_profile)
        
        # Create session in Supabase
        session_id = result.get("session_id")
        if session_id:
            await supabase_manager.create_negotiation_session(
                session_id=session_id,
                brand_details=brand_details,
                influencer_profile=influencer_profile,
                user_id=request.user_id
            )
            
            # Log conversation message
            agent_response = result.get("agent_response", "")
            if agent_response:
                await supabase_manager.log_conversation_message(
                    session_id=session_id,
                    message_type="agent",
                    content=agent_response,
                    metadata={"operation": "start_negotiation"}
                )
        
        return {
            "success": True,
            "session_id": session_id,
            "agent_response": result.get("agent_response"),
            "market_analysis": result.get("market_analysis"),
            "proposed_terms": result.get("proposed_terms"),
            "metadata": {
                "brand_name": brand_details.name,
                "influencer_name": influencer_profile.name,
                "platforms": [p.value for p in brand_details.target_platforms],
                "budget": brand_details.budget,
                "currency": brand_details.budget_currency
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start negotiation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start negotiation: {str(e)}")

@router.post("/continue", response_model=Dict[str, Any])
@log_to_supabase("continue_conversation", "continue")
async def continue_conversation(request: ContinueConversationRequest):
    """Continue an existing negotiation conversation"""
    try:
        # Log user message
        await supabase_manager.log_conversation_message(
            session_id=request.session_id,
            message_type="user",
            content=request.user_input,
            metadata={"operation": "continue_conversation"}
        )
        
        # Continue conversation with agent
        result = await negotiation_agent.continue_conversation(
            session_id=request.session_id,
            user_input=request.user_input
        )
        
        # Log agent response
        agent_response = result.get("agent_response", "")
        if agent_response:
            await supabase_manager.log_conversation_message(
                session_id=request.session_id,
                message_type="agent",
                content=agent_response,
                metadata={
                    "operation": "continue_conversation",
                    "negotiation_status": result.get("negotiation_status")
                }
            )
        
        # Update session status if changed
        if "negotiation_status" in result:
            await supabase_manager.update_negotiation_session(
                request.session_id,
                {
                    "status": result["negotiation_status"],
                    "negotiation_round": result.get("negotiation_round", 1)
                }
            )
        
        return {
            "success": True,
            "session_id": request.session_id,
            "agent_response": agent_response,
            "negotiation_status": result.get("negotiation_status"),
            "proposed_changes": result.get("proposed_changes"),
            "counter_offer": result.get("counter_offer"),
            "next_steps": result.get("next_steps")
        }
        
    except Exception as e:
        logger.error(f"Failed to continue conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to continue conversation: {str(e)}")

@router.get("/session/{session_id}/summary", response_model=Dict[str, Any])
async def get_negotiation_summary(session_id: str):
    """Get comprehensive negotiation summary"""
    try:
        # Get summary from agent
        agent_summary = await negotiation_agent.get_negotiation_summary(session_id)
        
        # Get analytics from Supabase
        analytics = await supabase_manager.get_session_analytics(session_id)
        
        # Get session data
        session_data = await supabase_manager.get_negotiation_session(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "agent_summary": agent_summary,
            "analytics": analytics,
            "session_data": session_data,
            "deliverables": await supabase_manager.get_deliverables(session_id)
        }
        
    except Exception as e:
        logger.error(f"Failed to get negotiation summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

# ==================== DELIVERABLES MANAGEMENT ====================

@router.put("/session/{session_id}/deliverables", response_model=Dict[str, Any])
@log_to_supabase("update_deliverables", "deliverable_update")
async def update_deliverables(session_id: str, request: UpdateDeliverablesRequest):
    """Update deliverables for a negotiation session"""
    try:
        # Save deliverables to Supabase
        success = await supabase_manager.save_deliverables(
            session_id=session_id,
            deliverables=request.deliverables
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save deliverables")
        
        return {
            "success": True,
            "session_id": session_id,
            "deliverables_count": len(request.deliverables),
            "message": "Deliverables updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to update deliverables: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update deliverables: {str(e)}")

@router.get("/session/{session_id}/deliverables", response_model=Dict[str, Any])
async def get_deliverables(session_id: str):
    """Get deliverables for a negotiation session"""
    try:
        deliverables = await supabase_manager.get_deliverables(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "deliverables": deliverables,
            "total_count": len(deliverables)
        }
        
    except Exception as e:
        logger.error(f"Failed to get deliverables: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get deliverables: {str(e)}")

# ==================== BUDGET MANAGEMENT ====================

@router.put("/session/{session_id}/budget", response_model=Dict[str, Any])
@log_to_supabase("update_budget", "budget_change")
async def update_budget(session_id: str, request: UpdateBudgetRequest):
    """Update budget for a negotiation session"""
    try:
        # Get current session to get old budget
        session = await supabase_manager.get_negotiation_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        old_budget = session.get("brand_details", {}).get("budget", 0)
        
        # Log budget change
        await supabase_manager.log_budget_change(
            session_id=session_id,
            old_budget=old_budget,
            new_budget=request.new_budget,
            currency=request.currency,
            change_reason=request.change_reason
        )
        
        # Update session with new budget
        updated_brand_details = session.get("brand_details", {})
        updated_brand_details["budget"] = request.new_budget
        updated_brand_details["budget_currency"] = request.currency
        
        await supabase_manager.update_negotiation_session(
            session_id,
            {"brand_details": updated_brand_details}
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "old_budget": old_budget,
            "new_budget": request.new_budget,
            "currency": request.currency,
            "change_amount": request.new_budget - old_budget,
            "change_reason": request.change_reason
        }
        
    except Exception as e:
        logger.error(f"Failed to update budget: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update budget: {str(e)}")

# ==================== CONTRACT MANAGEMENT ====================

@router.post("/session/{session_id}/generate-contract", response_model=Dict[str, Any])
@log_to_supabase("generate_contract", "contract_generation")
async def generate_contract(session_id: str, request: GenerateContractRequest):
    """Generate contract for completed negotiation"""
    try:
        # Get session data
        session = await supabase_manager.get_negotiation_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if negotiation is completed
        if session.get("status") != "agreed":
            raise HTTPException(status_code=400, detail="Negotiation must be completed before generating contract")
        
        # Generate contract with agent
        contract_result = await negotiation_agent.generate_contract(
            session_id=session_id,
            brand_contact_email=request.brand_contact_email,
            brand_contact_name=request.brand_contact_name,
            influencer_contact=request.influencer_contact
        )
        
        contract_id = contract_result.get("contract_id")
        if contract_id:
            # Save contract to Supabase
            await supabase_manager.save_contract(
                session_id=session_id,
                contract_id=contract_id,
                contract_data=contract_result.get("contract_data", {})
            )
        
        return {
            "success": True,
            "session_id": session_id,
            "contract_id": contract_id,
            "contract_url": contract_result.get("contract_url"),
            "pdf_url": contract_result.get("pdf_url"),
            "message": "Contract generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate contract: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate contract: {str(e)}")

@router.get("/session/{session_id}/contract", response_model=Dict[str, Any])
async def get_contract(session_id: str):
    """Get contract information for a session"""
    try:
        session = await supabase_manager.get_negotiation_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        contract_id = session.get("contract_id")
        if not contract_id:
            raise HTTPException(status_code=404, detail="No contract found for this session")
        
        # Get contract from agent
        contract_info = await negotiation_agent.get_contract_info(contract_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "contract_id": contract_id,
            "contract_info": contract_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get contract: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get contract: {str(e)}")

# ==================== ANALYTICS & REPORTING ====================

@router.get("/analytics/session/{session_id}", response_model=AnalyticsResponse)
async def get_session_analytics(session_id: str):
    """Get detailed analytics for a specific session"""
    try:
        analytics = await supabase_manager.get_session_analytics(session_id)
        
        return AnalyticsResponse(
            session_analytics=analytics,
            period="session_lifetime"
        )
        
    except Exception as e:
        logger.error(f"Failed to get session analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/analytics/global", response_model=AnalyticsResponse)
async def get_global_analytics():
    """Get global analytics across all sessions"""
    try:
        analytics = await supabase_manager.get_global_analytics()
        
        return AnalyticsResponse(
            global_analytics=analytics,
            period="all_time"
        )
        
    except Exception as e:
        logger.error(f"Failed to get global analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/analytics/dashboard", response_model=Dict[str, Any])
async def get_analytics_dashboard():
    """Get comprehensive analytics dashboard data"""
    try:
        # Get global analytics
        global_analytics = await supabase_manager.get_global_analytics()
        
        # Get recent sessions
        recent_sessions = await supabase_manager.list_active_sessions()
        recent_sessions = recent_sessions[:10]  # Last 10 sessions
        
        return {
            "success": True,
            "global_analytics": global_analytics,
            "recent_sessions": recent_sessions,
            "total_active_sessions": len(await supabase_manager.list_active_sessions()),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")

# ==================== SESSION MANAGEMENT ====================

@router.get("/sessions", response_model=Dict[str, Any])
async def list_sessions(
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0
):
    """List negotiation sessions with filtering"""
    try:
        if active_only:
            sessions = await supabase_manager.list_active_sessions()
        else:
            # Get all sessions (would need additional method in SupabaseManager)
            sessions = await supabase_manager.list_active_sessions()
        
        # Apply pagination
        total_count = len(sessions)
        paginated_sessions = sessions[offset:offset + limit]
        
        # Format sessions for response
        formatted_sessions = []
        for session in paginated_sessions:
            formatted_sessions.append(SessionResponse(
                session_id=session.get("session_id"),
                status=session.get("status", "unknown"),
                created_at=session.get("created_at", ""),
                brand_name=session.get("brand_details", {}).get("name", "Unknown"),
                influencer_name=session.get("influencer_profile", {}).get("name", "Unknown"),
                current_round=session.get("negotiation_round", 1),
                is_active=session.get("is_active", True)
            ))
        
        return {
            "success": True,
            "sessions": [session.dict() for session in formatted_sessions],
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@router.delete("/session/{session_id}", response_model=Dict[str, Any])
@log_to_supabase("delete_session", "delete")
async def delete_session(session_id: str):
    """Delete a negotiation session and all related data"""
    try:
        success = await supabase_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete session")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@router.put("/session/{session_id}/archive", response_model=Dict[str, Any])
@log_to_supabase("archive_session", "archive")
async def archive_session(session_id: str):
    """Archive a negotiation session"""
    try:
        success = await supabase_manager.archive_session(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to archive session")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session archived successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to archive session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to archive session: {str(e)}")

# ==================== UTILITY ENDPOINTS ====================

@router.get("/platforms", response_model=Dict[str, Any])
async def get_platform_details():
    """Get available platforms and their content types"""
    try:
        platforms = {
            "instagram": {
                "name": "Instagram",
                "content_types": ["post", "reel", "story"],
                "base_rates": {"post": 100, "reel": 150, "story": 50}
            },
            "youtube": {
                "name": "YouTube",
                "content_types": ["long_form", "shorts"],
                "base_rates": {"long_form": 500, "shorts": 200}
            },
            "tiktok": {
                "name": "TikTok",
                "content_types": ["video"],
                "base_rates": {"video": 200}
            },
            "linkedin": {
                "name": "LinkedIn",
                "content_types": ["post", "video"],
                "base_rates": {"post": 150, "video": 300}
            },
            "twitter": {
                "name": "Twitter",
                "content_types": ["post", "video"],
                "base_rates": {"post": 75, "video": 150}
            }
        }
        
        return {
            "success": True,
            "platforms": platforms,
            "total_platforms": len(platforms)
        }
        
    except Exception as e:
        logger.error(f"Failed to get platform details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get platforms: {str(e)}")

@router.get("/locations", response_model=Dict[str, Any])
async def get_supported_locations():
    """Get supported influencer locations and their multipliers"""
    try:
        locations = {
            "US": {"name": "United States", "multiplier": 1.0, "currency": "USD"},
            "UK": {"name": "United Kingdom", "multiplier": 0.9, "currency": "GBP"},
            "CANADA": {"name": "Canada", "multiplier": 0.8, "currency": "CAD"},
            "AUSTRALIA": {"name": "Australia", "multiplier": 0.85, "currency": "AUD"},
            "INDIA": {"name": "India", "multiplier": 0.3, "currency": "INR"},
            "GERMANY": {"name": "Germany", "multiplier": 0.95, "currency": "EUR"},
            "FRANCE": {"name": "France", "multiplier": 0.9, "currency": "EUR"},
            "BRAZIL": {"name": "Brazil", "multiplier": 0.4, "currency": "BRL"},
            "JAPAN": {"name": "Japan", "multiplier": 1.1, "currency": "JPY"},
            "OTHER": {"name": "Other", "multiplier": 0.7, "currency": "USD"}
        }
        
        return {
            "success": True,
            "locations": locations,
            "total_locations": len(locations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get locations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get locations: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for the negotiation agent router"""
    try:
        # Test Supabase connection
        test_analytics = await supabase_manager.get_global_analytics()
        supabase_healthy = True
    except:
        supabase_healthy = False
    
    return {
        "success": True,
        "service": "negotiation_agent_router",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "negotiation_agent": True,
            "supabase_manager": supabase_healthy,
            "router": True
        }
    }
    campaign_duration_days: int = Field(..., description="Campaign duration in days")
    target_audience: str = Field(..., description="Target audience description")
    brand_guidelines: str = Field(..., description="Brand guidelines and requirements")
    brand_location: Optional[str] = Field(None, description="Brand location/country")

class InfluencerProfileRequest(BaseModel):
    name: str = Field(..., description="Influencer name")
    followers: int = Field(..., description="Follower count")
    engagement_rate: float = Field(..., description="Engagement rate as decimal (e.g., 0.05 for 5%)")
    location: str = Field(..., description="Influencer location/country")
    platforms: List[str] = Field(..., description="Active social media platforms")
    niches: List[str] = Field(..., description="Content niches/categories")
    previous_brand_collaborations: int = Field(default=0, description="Number of previous brand collaborations")

class StartNegotiationRequest(BaseModel):
    brand_details: BrandDetailsRequest
    influencer_profile: InfluencerProfileRequest
    user_id: Optional[str] = Field(None, description="User ID for session tracking")

class ContinueConversationRequest(BaseModel):
    session_id: str = Field(..., description="Negotiation session ID")
    user_input: str = Field(..., description="User's message/response")
    user_id: Optional[str] = Field(None, description="User ID for session tracking")

class UpdateDeliverableRequest(BaseModel):
    session_id: str = Field(..., description="Negotiation session ID")
    content_type: str = Field(..., description="Content type (e.g., 'instagram_post')")
    count: int = Field(..., description="Number of deliverables")
    user_id: Optional[str] = Field(None, description="User ID for session tracking")

class UpdateBudgetRequest(BaseModel):
    session_id: str = Field(..., description="Negotiation session ID")
    new_budget: float = Field(..., description="New budget amount")
    currency: str = Field(default="USD", description="Currency code")
    user_id: Optional[str] = Field(None, description="User ID for session tracking")

class ContractGenerationRequest(BaseModel):
    session_id: str = Field(..., description="Negotiation session ID")
    user_id: Optional[str] = Field(None, description="User ID for session tracking")
    influencer_email: Optional[str] = Field(None, description="Influencer email for contract")
    brand_contact_email: Optional[str] = Field(None, description="Brand contact email")

# ==================== CORE NEGOTIATION ENDPOINTS ====================

@router.post("/start")
@log_to_supabase("start_negotiation", "start")
async def start_negotiation(request: StartNegotiationRequest):
    """Start a new negotiation session with full Supabase logging"""
    try:
        # Helper function to map location strings to LocationType
        def map_location(location_str: str) -> LocationType:
            location_mapping = {
                "india": LocationType.INDIA,
                "us": LocationType.US, "usa": LocationType.US, "united states": LocationType.US,
                "uk": LocationType.UK, "united kingdom": LocationType.UK,
                "canada": LocationType.CANADA,
                "australia": LocationType.AUSTRALIA,
                "germany": LocationType.GERMANY,
                "france": LocationType.FRANCE,
                "brazil": LocationType.BRAZIL,
                "japan": LocationType.JAPAN,
            }
            return location_mapping.get(location_str.lower().strip(), LocationType.OTHER)

        # Convert pydantic models to domain dataclasses
        brand_details = BrandDetails(
            name=request.brand_details.name,
            budget=request.brand_details.budget,
            goals=request.brand_details.goals,
            target_platforms=[PlatformType(p.lower()) for p in request.brand_details.target_platforms],
            content_requirements=request.brand_details.content_requirements,
            campaign_duration_days=request.brand_details.campaign_duration_days,
            target_audience=request.brand_details.target_audience,
            brand_guidelines=request.brand_details.brand_guidelines,
            brand_location=map_location(request.brand_details.brand_location or ""),
            budget_currency=request.brand_details.budget_currency,
            original_budget_amount=request.brand_details.budget
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
        result = await negotiation_agent.start_negotiation(brand_details, influencer_profile)
        
        # Log detailed session start to Supabase
        session_data = {
            "session_id": result["session_id"],
            "user_id": request.user_id,
            "brand_name": brand_details.name,
            "influencer_name": influencer_profile.name,
            "initial_budget": brand_details.budget,
            "budget_currency": brand_details.budget_currency,
            "content_requirements": brand_details.content_requirements,
            "platforms": [p.value for p in brand_details.target_platforms],
            "campaign_duration": brand_details.campaign_duration_days,
            "status": "initiated",
            "created_at": datetime.now().isoformat()
        }
        
        await supabase_manager.log_negotiation_session(session_data)
        
        return result
        
    except ValueError as e:
        logger.error(f"Invalid input for negotiation start: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Error starting negotiation: {e}")
        raise HTTPException(status_code=500, detail=f"Negotiation failed: {str(e)}")

@router.post("/continue")
@log_to_supabase("continue_conversation", "continue")
async def continue_conversation(request: ContinueConversationRequest):
    """Continue an existing negotiation conversation"""
    try:
        result = await negotiation_agent.continue_conversation(
            request.session_id, request.user_input
        )
        
        # Log conversation message to Supabase
        message_data = {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "speaker": "influencer",
            "message": request.user_input,
            "timestamp": datetime.now().isoformat(),
            "message_type": "user_response"
        }
        
        await supabase_manager.log_conversation_message(message_data)
        
        # Log agent response
        agent_message_data = {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "speaker": "agent",
            "message": result.get("message", ""),
            "timestamp": datetime.now().isoformat(),
            "message_type": "agent_response",
            "negotiation_status": result.get("status", "active")
        }
        
        await supabase_manager.log_conversation_message(agent_message_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")

@router.get("/session/{session_id}/summary")
@log_to_supabase("get_session_summary", "query")
async def get_negotiation_summary(session_id: str, user_id: Optional[str] = None):
    """Get comprehensive summary of negotiation session"""
    try:
        summary = negotiation_agent.get_negotiation_summary()
        
        # Enhance summary with additional data from Supabase
        enhanced_summary = await supabase_manager.get_enhanced_session_summary(session_id, user_id)
        
        # Merge the summaries
        if enhanced_summary:
            summary.update(enhanced_summary)
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting summary for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.get("/session/{session_id}/conversation")
@log_to_supabase("get_conversation_history", "query")
async def get_conversation_history(session_id: str, user_id: Optional[str] = None):
    """Get full conversation history for a session"""
    try:
        history = await supabase_manager.get_conversation_history(session_id, user_id)
        return {
            "session_id": session_id,
            "conversation_history": history,
            "message_count": len(history),
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

# ==================== DELIVERABLES MANAGEMENT ====================

@router.post("/session/{session_id}/deliverables/update")
@log_to_supabase("update_deliverables", "deliverable_update")
async def update_deliverables(session_id: str, request: UpdateDeliverableRequest):
    """Update deliverables for an active session"""
    try:
        # Update deliverables through the agent
        result = await negotiation_agent.update_deliverables(
            session_id, request.content_type, request.count
        )
        
        # Log deliverable change
        deliverable_data = {
            "session_id": session_id,
            "user_id": request.user_id,
            "content_type": request.content_type,
            "new_count": request.count,
            "timestamp": datetime.now().isoformat(),
            "change_type": "deliverable_update"
        }
        
        await supabase_manager.log_deliverable_change(deliverable_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating deliverables: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update deliverables: {str(e)}")

@router.get("/session/{session_id}/deliverables")
@log_to_supabase("get_deliverables", "query")
async def get_current_deliverables(session_id: str, user_id: Optional[str] = None):
    """Get current agreed deliverables for a session"""
    try:
        deliverables = await supabase_manager.get_session_deliverables(session_id, user_id)
        return {
            "session_id": session_id,
            "current_deliverables": deliverables,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting deliverables: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get deliverables: {str(e)}")

# ==================== BUDGET MANAGEMENT ====================

@router.post("/session/{session_id}/budget/update")
@log_to_supabase("update_budget", "budget_change")
async def update_session_budget(session_id: str, request: UpdateBudgetRequest):
    """Update budget for an active session"""
    try:
        result = await negotiation_agent.update_budget(
            session_id, request.new_budget, request.currency
        )
        
        # Log budget change
        budget_data = {
            "session_id": session_id,
            "user_id": request.user_id,
            "new_budget": request.new_budget,
            "currency": request.currency,
            "timestamp": datetime.now().isoformat(),
            "change_type": "budget_update"
        }
        
        await supabase_manager.log_budget_change(budget_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating budget: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update budget: {str(e)}")

@router.get("/session/{session_id}/budget/status")
@log_to_supabase("get_budget_status", "query")
async def get_budget_status(session_id: str, user_id: Optional[str] = None):
    """Get current budget status and utilization"""
    try:
        budget_status = negotiation_agent.get_budget_status()
        
        # Enhanced budget status from Supabase
        enhanced_status = await supabase_manager.get_budget_analytics(session_id, user_id)
        
        if enhanced_status:
            budget_status.update(enhanced_status)
        
        return budget_status
        
    except Exception as e:
        logger.error(f"Error getting budget status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get budget status: {str(e)}")

# ==================== CONTRACT MANAGEMENT ====================

@router.post("/session/{session_id}/contract/generate")
@log_to_supabase("generate_contract", "contract_generation")
async def generate_contract(session_id: str, request: ContractGenerationRequest):
    """Generate contract for agreed negotiation"""
    try:
        # Generate contract through the agent
        contract_result = await negotiation_agent.generate_contract(
            session_id, 
            request.influencer_email,
            request.brand_contact_email
        )
        
        # Log contract generation
        contract_data = {
            "session_id": session_id,
            "user_id": request.user_id,
            "contract_id": contract_result.get("contract_id"),
            "generated_at": datetime.now().isoformat(),
            "status": "generated",
            "contract_type": "influencer_collaboration"
        }
        
        await supabase_manager.log_contract_generation(contract_data)
        
        return contract_result
        
    except Exception as e:
        logger.error(f"Error generating contract: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate contract: {str(e)}")

@router.get("/session/{session_id}/contract")
@log_to_supabase("get_contract", "query")
async def get_session_contract(session_id: str, user_id: Optional[str] = None):
    """Get contract details for a session"""
    try:
        contract = await supabase_manager.get_session_contract(session_id, user_id)
        return contract
        
    except Exception as e:
        logger.error(f"Error getting contract: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get contract: {str(e)}")

# ==================== ANALYTICS & REPORTING ====================

@router.get("/analytics/sessions")
@log_to_supabase("get_session_analytics", "analytics")
async def get_session_analytics(
    user_id: Optional[str] = None,
    days: int = 30,
    status: Optional[str] = None
):
    """Get analytics for negotiation sessions"""
    try:
        analytics = await supabase_manager.get_session_analytics(user_id, days, status)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/analytics/performance")
@log_to_supabase("get_performance_analytics", "analytics")
async def get_performance_analytics(user_id: Optional[str] = None, days: int = 30):
    """Get performance analytics for negotiations"""
    try:
        performance = await supabase_manager.get_performance_analytics(user_id, days)
        return performance
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance analytics: {str(e)}")

# ==================== SESSION MANAGEMENT ====================

@router.delete("/session/{session_id}")
@log_to_supabase("delete_session", "delete")
async def clear_session(session_id: str, user_id: Optional[str] = None):
    """Clear/delete a specific negotiation session"""
    try:
        # Clear session from agent
        result = await negotiation_agent.clear_session(session_id)
        
        # Archive session in Supabase (don't delete, just mark as archived)
        await supabase_manager.archive_session(session_id, user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")

@router.get("/sessions")
@log_to_supabase("list_sessions", "query")
async def list_active_sessions(user_id: Optional[str] = None, status: Optional[str] = None):
    """List all active negotiation sessions"""
    try:
        # Get sessions from both agent and Supabase
        agent_sessions = await negotiation_agent.list_active_sessions()
        supabase_sessions = await supabase_manager.list_user_sessions(user_id, status)
        
        return {
            "agent_sessions": agent_sessions,
            "database_sessions": supabase_sessions,
            "total_active": len(supabase_sessions),
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

# ==================== UTILITY ENDPOINTS ====================

@router.get("/platforms")
async def get_platform_details():
    """Get available platforms and their content types"""
    return {
        "platforms": [
            {
                "name": "instagram", 
                "display_name": "Instagram",
                "content_types": ["post", "story", "reel", "igtv"]
            },
            {
                "name": "youtube", 
                "display_name": "YouTube",
                "content_types": ["video", "shorts", "live"]
            },
            {
                "name": "tiktok", 
                "display_name": "TikTok",
                "content_types": ["video", "live"]
            },
            {
                "name": "twitter", 
                "display_name": "Twitter/X",
                "content_types": ["tweet", "thread", "space"]
            },
            {
                "name": "linkedin", 
                "display_name": "LinkedIn",
                "content_types": ["post", "article", "story"]
            },
            {
                "name": "facebook", 
                "display_name": "Facebook",
                "content_types": ["post", "story", "reel", "live"]
            }
        ]
    }

@router.get("/locations")
async def get_supported_locations():
    """Get supported influencer locations"""
    return {
        "locations": [
            {"code": "india", "name": "India", "currency": "INR"},
            {"code": "us", "name": "United States", "currency": "USD"},
            {"code": "uk", "name": "United Kingdom", "currency": "GBP"},
            {"code": "canada", "name": "Canada", "currency": "CAD"},
            {"code": "australia", "name": "Australia", "currency": "AUD"},
            {"code": "germany", "name": "Germany", "currency": "EUR"},
            {"code": "france", "name": "France", "currency": "EUR"},
            {"code": "brazil", "name": "Brazil", "currency": "BRL"},
            {"code": "japan", "name": "Japan", "currency": "JPY"},
            {"code": "other", "name": "Other", "currency": "USD"}
        ]
    }

# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check():
    """Health check for the negotiation agent service"""
    try:
        # Check agent status
        agent_status = "healthy" if negotiation_agent else "unhealthy"
        
        # Check Supabase connection
        supabase_status = await supabase_manager.health_check()
        
        return {
            "status": "healthy" if agent_status == "healthy" and supabase_status else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "negotiation_agent": agent_status,
                "supabase_manager": "healthy" if supabase_status else "unhealthy"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
