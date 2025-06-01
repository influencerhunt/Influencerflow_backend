from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
from datetime import datetime
import uuid

from app.agents.agent import NegotiationAgent
from app.services.supabase_manager import SupabaseManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/negotiation-agent", tags=["negotiation-agent"])

# Initialize services
negotiation_agent = NegotiationAgent()
supabase_manager = SupabaseManager()

# ==================== VALIDATION HELPERS ====================

# Platform and location constants
VALID_PLATFORMS = ["instagram", "youtube", "tiktok", "twitter", "linkedin", "facebook"]
VALID_LOCATIONS = ["US", "UK", "CANADA", "AUSTRALIA", "INDIA", "GERMANY", "FRANCE", "BRAZIL", "JAPAN", "OTHER"]

# Valid negotiation status values (must match database constraints and NegotiationStatus enum)
VALID_STATUSES = {
    "initiated": "initiated",
    "in_progress": "in_progress",
    "counter_offer": "counter_offer",
    "agreed": "agreed",
    "rejected": "rejected",
    "cancelled": "cancelled",
    "contract_generated": "contract_generated",
    "archived": "archived"
}

# Agent status to database status mapping
AGENT_STATUS_MAPPING = {
    "active": "in_progress",
    "completed": "agreed", 
    "failed": "rejected",  # Map failed to rejected (not cancelled)
    "cancelled": "cancelled",
    "initiated": "initiated"
}

def validate_user_id(user_id: Optional[str]) -> Optional[str]:
    """Validate user_id UUID format, return None if invalid"""
    if user_id is None:
        return None
    
    try:
        # Try to parse as UUID to validate format
        uuid.UUID(user_id)
        return user_id
    except ValueError:
        # If it's not a valid UUID, return None (will be handled as anonymous user)
        logger.warning(f"Invalid UUID format for user_id: {user_id}, treating as anonymous user")
        return None

def validate_negotiation_status(status: str) -> str:
    """Validate and normalize negotiation status"""
    if not status:
        return "in_progress"
    
    # Check if it's already a valid database status
    if status in VALID_STATUSES:
        return status
    
    # Check if it's an agent status that needs mapping
    if status in AGENT_STATUS_MAPPING:
        mapped_status = AGENT_STATUS_MAPPING[status]
        logger.info(f"Mapped agent status '{status}' to database status '{mapped_status}'")
        return mapped_status
    
    # Unknown status - log warning and default to safe value
    logger.warning(f"Unknown status '{status}', defaulting to 'in_progress'")
    return "in_progress"

def validate_brand_details(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate brand details dictionary"""
    required_fields = ["name", "budget", "goals", "target_platforms", "content_requirements", 
                      "campaign_duration_days", "target_audience"]
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Type validation
    if not isinstance(data["budget"], (int, float)) or data["budget"] <= 0:
        raise ValueError("Budget must be a positive number")
    
    if not isinstance(data["goals"], list) or not data["goals"]:
        raise ValueError("Goals must be a non-empty list")
    
    if not isinstance(data["target_platforms"], list) or not data["target_platforms"]:
        raise ValueError("Target platforms must be a non-empty list")
    
    # Validate platform values
    for platform in data["target_platforms"]:
        if platform.lower() not in VALID_PLATFORMS:
            raise ValueError(f"Invalid platform: {platform}. Valid platforms: {VALID_PLATFORMS}")
    
    if not isinstance(data["content_requirements"], dict):
        raise ValueError("Content requirements must be a dictionary")
    
    if not isinstance(data["campaign_duration_days"], int) or data["campaign_duration_days"] <= 0:
        raise ValueError("Campaign duration must be a positive integer")
    
    # Set defaults
    data.setdefault("budget_currency", "USD")
    data.setdefault("brand_guidelines", None)
    data.setdefault("brand_location", "US")
    
    return data

def validate_influencer_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate influencer profile dictionary"""
    required_fields = ["name", "followers", "engagement_rate", "location", "platforms", "niches"]
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Type validation
    if not isinstance(data["followers"], int) or data["followers"] <= 0:
        raise ValueError("Followers must be a positive integer")
    
    if not isinstance(data["engagement_rate"], (int, float)) or not (0 <= data["engagement_rate"] <= 1):
        raise ValueError("Engagement rate must be between 0 and 1")
    
    if not isinstance(data["platforms"], list) or not data["platforms"]:
        raise ValueError("Platforms must be a non-empty list")
    
    # Validate platform values
    for platform in data["platforms"]:
        if platform.lower() not in VALID_PLATFORMS:
            raise ValueError(f"Invalid platform: {platform}. Valid platforms: {VALID_PLATFORMS}")
    
    if not isinstance(data["niches"], list) or not data["niches"]:
        raise ValueError("Niches must be a non-empty list")
    
    # Validate location
    if data["location"].upper() not in VALID_LOCATIONS:
        raise ValueError(f"Invalid location: {data['location']}. Valid locations: {VALID_LOCATIONS}")
    
    # Set defaults
    data.setdefault("previous_brand_collaborations", 0)
    
    return data

def create_brand_details_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a brand details dictionary from validated data"""
    return {
        "name": data["name"],
        "budget": data["budget"],
        "budget_currency": data["budget_currency"],
        "goals": data["goals"],
        "target_platforms": [p.lower() for p in data["target_platforms"]],
        "content_requirements": data["content_requirements"],
        "campaign_duration_days": data["campaign_duration_days"],
        "target_audience": data["target_audience"],
        "brand_guidelines": data["brand_guidelines"],
        "brand_location": data["brand_location"]
    }

def create_influencer_profile_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create an influencer profile dictionary from validated data"""
    return {
        "name": data["name"],
        "followers": data["followers"],
        "engagement_rate": data["engagement_rate"],
        "location": data["location"].upper(),
        "platforms": [p.lower() for p in data["platforms"]],
        "niches": data["niches"],
        "previous_brand_collaborations": data["previous_brand_collaborations"]
    }

# ==================== CORE NEGOTIATION ENDPOINTS ====================

@router.post("/start")
# @log_to_supabase("start_negotiation", "start")
async def start_negotiation(request: Dict[str, Any]):
    """Start a new negotiation session with comprehensive logging"""
    try:
        # Validate request structure
        if "brand_details" not in request or "influencer_profile" not in request:
            raise ValueError("Missing brand_details or influencer_profile")
        
        # Validate individual components
        brand_data = validate_brand_details(request["brand_details"])
        influencer_data = validate_influencer_profile(request["influencer_profile"])
        user_id = validate_user_id(request.get("user_id"))
        
        # Convert to dictionaries for the agent
        brand_details_dict = create_brand_details_dict(brand_data)
        influencer_profile_dict = create_influencer_profile_dict(influencer_data)
        
        # Start negotiation with agent (pass as dictionaries)
        agent_response = negotiation_agent.start_negotiation(
            brand_details_dict, 
            influencer_profile_dict
        )
        
        # Get session ID from the agent's current state
        session_id = negotiation_agent.current_state.session_id if negotiation_agent.current_state else str(uuid.uuid4())
        
        # Create session in Supabase
        if session_id:
            await supabase_manager.create_negotiation_session_from_dicts(
                session_id=session_id,
                brand_details=brand_details_dict,
                influencer_profile=influencer_profile_dict,
                user_id=user_id
            )
            
            # Log conversation message
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
            "agent_response": agent_response,
            "market_analysis": "Real-time market research completed",
            "proposed_terms": "Initial offer presented",
            "metadata": {
                "brand_name": brand_details_dict["name"],
                "influencer_name": influencer_profile_dict["name"],
                "platforms": brand_details_dict["target_platforms"],
                "budget": brand_details_dict["budget"],
                "currency": brand_details_dict["budget_currency"]
            }
        }
        
    except ValueError as e:
        logger.error(f"Validation error in start negotiation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start negotiation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start negotiation: {str(e)}")

@router.post("/continue")
# @log_to_supabase("continue_conversation", "continue")
async def continue_conversation(request: Dict[str, Any]):
    """Continue an existing negotiation conversation"""
    try:
        # Validate required fields
        if "session_id" not in request or "user_input" not in request:
            raise ValueError("Missing session_id or user_input")
        
        session_id = request["session_id"]
        user_input = request["user_input"]
        user_id = validate_user_id(request.get("user_id"))
        
        if not session_id or not user_input:
            raise ValueError("session_id and user_input cannot be empty")
        
        # Log user message
        await supabase_manager.log_conversation_message(
            session_id=session_id,
            message_type="user",
            content=user_input,
            metadata={"operation": "continue_conversation"}
        )
        
        # Continue conversation with agent
        agent_response = negotiation_agent.respond_to_influencer(user_input)
        
        # Get negotiation status from agent state
        agent_status = negotiation_agent.current_state.status if negotiation_agent.current_state else "active"
        
        # Map agent status to database-compatible status
        negotiation_status = validate_negotiation_status(agent_status)
        negotiation_round = len(negotiation_agent.current_state.messages) // 2 if negotiation_agent.current_state else 1
        
        # Log agent response
        if agent_response:
            await supabase_manager.log_conversation_message(
                session_id=session_id,
                message_type="agent",
                content=agent_response,
                metadata={
                    "operation": "continue_conversation",
                    "negotiation_status": negotiation_status
                }
            )
        
        # Update session status if changed
        await supabase_manager.update_negotiation_session(
            session_id,
            {
                "status": negotiation_status,
                "negotiation_round": negotiation_round
            }
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "agent_response": agent_response,
            "negotiation_status": negotiation_status,
            "proposed_changes": "Check agent response for details",
            "counter_offer": "Check agent response for counter offers",
            "next_steps": "Continue negotiation or finalize agreement"
        }
        
    except ValueError as e:
        logger.error(f"Validation error in continue conversation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to continue conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to continue conversation: {str(e)}")

@router.get("/session/{session_id}/summary")
async def get_negotiation_summary(session_id: str):
    """Get comprehensive negotiation summary"""
    try:
        if not session_id:
            raise ValueError("session_id is required")
        
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

@router.put("/session/{session_id}/deliverables")
# @log_to_supabase("update_deliverables", "deliverable_update")
async def update_deliverables(session_id: str, request: Dict[str, Any]):
    """Update deliverables for a negotiation session"""
    try:
        if not session_id:
            raise ValueError("session_id is required")
        
        if "deliverables" not in request:
            raise ValueError("Missing deliverables in request")
        
        deliverables = request["deliverables"]
        if not isinstance(deliverables, list):
            raise ValueError("deliverables must be a list")
        
        # Save deliverables to Supabase
        success = await supabase_manager.save_deliverables(
            session_id=session_id,
            deliverables=deliverables
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save deliverables")
        
        return {
            "success": True,
            "session_id": session_id,
            "deliverables_count": len(deliverables),
            "message": "Deliverables updated successfully"
        }
        
    except ValueError as e:
        logger.error(f"Validation error in update deliverables: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update deliverables: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update deliverables: {str(e)}")

@router.get("/session/{session_id}/deliverables")
async def get_deliverables(session_id: str):
    """Get deliverables for a negotiation session"""
    try:
        if not session_id:
            raise ValueError("session_id is required")
        
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

@router.put("/session/{session_id}/budget")
# @log_to_supabase("update_budget", "budget_change")
async def update_budget(session_id: str, request: Dict[str, Any]):
    """Update budget for a negotiation session"""
    try:
        if not session_id:
            raise ValueError("session_id is required")
        
        # Validate required fields
        required_fields = ["new_budget", "change_reason"]
        for field in required_fields:
            if field not in request:
                raise ValueError(f"Missing required field: {field}")
        
        new_budget = request["new_budget"]
        currency = request.get("currency", "USD")
        change_reason = request["change_reason"]
        
        if not isinstance(new_budget, (int, float)) or new_budget <= 0:
            raise ValueError("new_budget must be a positive number")
        
        # Get current session to get old budget
        session = await supabase_manager.get_negotiation_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        old_budget = session.get("brand_details", {}).get("budget", 0)
        
        # Log budget change
        await supabase_manager.log_budget_change(
            session_id=session_id,
            old_budget=old_budget,
            new_budget=new_budget,
            currency=currency,
            change_reason=change_reason
        )
        
        # Update session with new budget
        updated_brand_details = session.get("brand_details", {})
        updated_brand_details["budget"] = new_budget
        updated_brand_details["budget_currency"] = currency
        
        await supabase_manager.update_negotiation_session(
            session_id,
            {"brand_details": updated_brand_details}
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "old_budget": old_budget,
            "new_budget": new_budget,
            "currency": currency,
            "change_amount": new_budget - old_budget,
            "change_reason": change_reason
        }
        
    except ValueError as e:
        logger.error(f"Validation error in update budget: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update budget: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update budget: {str(e)}")

# ==================== CONTRACT MANAGEMENT ====================

@router.post("/session/{session_id}/generate-contract")
# @log_to_supabase("generate_contract", "contract_generation")
async def generate_contract(session_id: str, request: Dict[str, Any]):
    """Generate contract for completed negotiation"""
    try:
        if not session_id:
            raise ValueError("session_id is required")
        
        # Validate required fields
        required_fields = ["brand_contact_email", "brand_contact_name", "influencer_contact"]
        for field in required_fields:
            if field not in request:
                raise ValueError(f"Missing required field: {field}")
        
        brand_contact_email = request["brand_contact_email"]
        brand_contact_name = request["brand_contact_name"] 
        influencer_contact = request["influencer_contact"]
        
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
            brand_contact_email=brand_contact_email,
            brand_contact_name=brand_contact_name,
            influencer_contact=influencer_contact
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
        
    except ValueError as e:
        logger.error(f"Validation error in generate contract: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate contract: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate contract: {str(e)}")

@router.get("/session/{session_id}/contract")
async def get_contract(session_id: str):
    """Get contract information for a session"""
    try:
        if not session_id:
            raise ValueError("session_id is required")
        
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

@router.get("/analytics/session/{session_id}")
async def get_session_analytics(session_id: str):
    """Get detailed analytics for a specific session"""
    try:
        if not session_id:
            raise ValueError("session_id is required")
        
        analytics = await supabase_manager.get_session_analytics(session_id)
        
        return {
            "session_analytics": analytics,
            "period": "session_lifetime"
        }
        
    except Exception as e:
        logger.error(f"Failed to get session analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/analytics/global")
async def get_global_analytics():
    """Get global analytics across all sessions"""
    try:
        analytics = await supabase_manager.get_global_analytics()
        
        return {
            "global_analytics": analytics,
            "period": "all_time"
        }
        
    except Exception as e:
        logger.error(f"Failed to get global analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/analytics/dashboard")
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

@router.get("/sessions")
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
            formatted_sessions.append({
                "session_id": session.get("session_id"),
                "status": session.get("status", "unknown"),
                "created_at": session.get("created_at", ""),
                "brand_name": session.get("brand_details", {}).get("name", "Unknown"),
                "influencer_name": session.get("influencer_profile", {}).get("name", "Unknown"),
                "current_round": session.get("negotiation_round", 1),
                "is_active": session.get("is_active", True)
            })
        
        return {
            "success": True,
            "sessions": formatted_sessions,
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

@router.delete("/session/{session_id}")
# @log_to_supabase("delete_session", "delete")
async def delete_session(session_id: str):
    """Delete a negotiation session and all related data"""
    try:
        if not session_id:
            raise ValueError("session_id is required")
        
        success = await supabase_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete session")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session deleted successfully"
        }
        
    except ValueError as e:
        logger.error(f"Validation error in delete session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@router.put("/session/{session_id}/archive")
# @log_to_supabase("archive_session", "archive")
async def archive_session(session_id: str):
    """Archive a negotiation session"""
    try:
        if not session_id:
            raise ValueError("session_id is required")
        
        success = await supabase_manager.archive_session(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to archive session")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session archived successfully"
        }
        
    except ValueError as e:
        logger.error(f"Validation error in archive session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to archive session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to archive session: {str(e)}")

# ==================== UTILITY ENDPOINTS ====================

@router.get("/platforms")
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

@router.get("/locations")
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

@router.get("/health")
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
