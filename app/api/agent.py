from fastapi import APIRouter, Request, HTTPException
from typing import Optional, Dict, Any
import logging

from app.services.agent_service import agent_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def agent_health_check():
    """
    Health check endpoint for the agent service
    """
    try:
        service_status = agent_service.get_service_status()
        
        return {
            "success": True,
            "message": "Agent service is healthy",
            "data": service_status
        }
            
    except Exception as e:
        logger.error(f"Agent health check failed: {e}")
        raise HTTPException(status_code=503, detail="Agent service unhealthy")


@router.post("/create-session")
async def create_agent_session(request: Request):
    """
    Create a new agent conversation session
    """
    try:
        data = await request.json()
        session_id = data.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Create new chat session
        chat_session = agent_service.create_chat_session(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Agent session created successfully",
            "greeting": agent_service.get_greeting_message()
        }
        
    except Exception as e:
        logger.error(f"Error creating agent session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-message")
async def send_message_to_agent(request: Request):
    """
    Send a message to the agent and get a response
    """
    try:
        data = await request.json()
        session_id = data.get("session_id")
        message = data.get("message")
        
        if not session_id or not message:
            raise HTTPException(status_code=400, detail="session_id and message are required")
        
        # Send message to agent
        agent_response = agent_service.send_message(session_id, message)
        
        return {
            "success": True,
            "session_id": session_id,
            "user_message": message,
            "agent_response": agent_response
        }
        
    except Exception as e:
        logger.error(f"Error sending message to agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_agent_sessions():
    """
    Get information about active agent sessions
    """
    try:
        sessions_data = agent_service.get_active_sessions()
        
        return {
            "success": True,
            "message": f"Found {sessions_data['count']} active agent sessions",
            "data": sessions_data
        }
        
    except Exception as e:
        logger.error(f"Error getting agent sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end-session")
async def end_agent_session(request: Request):
    """
    End an agent session and clean up resources
    """
    try:
        data = await request.json()
        session_id = data.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        agent_service.end_session(session_id)
        
        return {
            "success": True,
            "message": f"Agent session ended successfully for {session_id}"
        }
        
    except Exception as e:
        logger.error(f"Error ending agent session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-prompt")
async def update_system_prompt(request: Request):
    """
    Update the system prompt for the agent (affects new sessions)
    """
    try:
        data = await request.json()
        new_prompt = data.get("prompt")
        
        if not new_prompt:
            raise HTTPException(status_code=400, detail="prompt is required")
        
        agent_service.update_system_prompt(new_prompt)
        
        return {
            "success": True,
            "message": "System prompt updated successfully",
            "note": "This will affect new chat sessions only"
        }
        
    except Exception as e:
        logger.error(f"Error updating system prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/greeting")
async def get_agent_greeting():
    """
    Get the current greeting message
    """
    try:
        greeting = agent_service.get_greeting_message()
        
        return {
            "success": True,
            "greeting": greeting
        }
        
    except Exception as e:
        logger.error(f"Error getting agent greeting: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 