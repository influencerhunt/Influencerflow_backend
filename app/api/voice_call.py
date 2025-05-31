from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import Response
from typing import Optional, Dict, Any
import logging

from app.services.voice_call_service import voice_call_service

router = APIRouter()
logger = logging.getLogger(__name__)


def validate_twilio_signature(request: Request):
    """Dependency to validate Twilio webhook signatures"""
    # Get the signature and URL
    signature = request.headers.get("X-Twilio-Signature", "")
    
    # Construct the full URL
    proto = request.headers.get("X-Forwarded-Proto", "https")
    host = request.headers.get("Host", "")
    url = f"{proto}://{host}{request.url.path}"
    
    # This will be populated by the form data
    return {"url": url, "signature": signature}


@router.post("/outbound-call")
async def initiate_outbound_call(request: Request):
    """
    Initiate an outbound voice call
    """
    try:
        data = await request.json()
        to_number = data.get("to_number")
        webhook_base_url = data.get("webhook_base_url")
        
        if not to_number or not webhook_base_url:
            raise HTTPException(status_code=400, detail="to_number and webhook_base_url are required")
        
        call_sid = voice_call_service.make_outbound_call(
            to_number=to_number,
            webhook_base_url=webhook_base_url
        )
        
        return {
            "success": True,
            "call_sid": call_sid,
            "message": f"Call initiated successfully to {to_number}"
        }
        
    except Exception as e:
        logger.error(f"Error initiating outbound call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/call-status/{call_sid}")
async def get_call_status(call_sid: str):
    """
    Get the status of a specific call
    """
    try:
        call_info = voice_call_service.get_call_status(call_sid)
        
        return {
            "sid": call_info["sid"],
            "status": call_info["status"],
            "duration": call_info["duration"],
            "direction": call_info["direction"],
            "from_number": call_info["from_number"],
            "to_number": call_info["to_number"]
        }
        
    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end-session")
async def end_voice_call_session(request: Request):
    """
    End a voice call session and clean up resources
    """
    try:
        data = await request.json()
        call_sid = data.get("call_sid")
        
        if not call_sid:
            raise HTTPException(status_code=400, detail="call_sid is required")
        
        voice_call_service.end_session(call_sid)
        
        return {
            "success": True,
            "message": f"Session ended successfully for call {call_sid}"
        }
        
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Twilio Webhook Endpoints
@router.post("/voice")
async def voice_webhook(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(default=""),
    To: str = Form(default="")
):
    """
    Twilio webhook for incoming voice calls
    """
    try:
        # Simple validation - skip signature validation for MVP
        logger.info(f"Voice webhook called for CallSid: {CallSid}")
        
        # Handle the inbound call
        twiml_response = voice_call_service.handle_inbound_call(CallSid)
        
        return Response(content=twiml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in voice webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/gather")
async def gather_webhook(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(default="")
):
    """
    Twilio webhook for gathering speech input
    """
    try:
        # Simple validation - skip signature validation for MVP
        logger.info(f"Gather webhook called for CallSid: {CallSid}, Speech: {SpeechResult}")
        
        # Handle the speech input
        twiml_response = voice_call_service.handle_gather(CallSid, SpeechResult)
        
        return Response(content=twiml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in gather webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/partial")
async def partial_webhook(
    request: Request,
    CallSid: str = Form(...),
    UnstableSpeechResult: str = Form(default="")
):
    """
    Twilio webhook for partial speech results
    """
    try:
        # Simple validation - skip signature validation for MVP
        logger.debug(f"Partial webhook called for CallSid: {CallSid}, Partial: {UnstableSpeechResult}")
        
        # Handle partial results
        twiml_response = voice_call_service.handle_partial_results(CallSid, UnstableSpeechResult)
        
        return Response(content=twiml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in partial webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions")
async def get_active_sessions():
    """
    Get information about active voice call sessions
    """
    try:
        sessions_data = voice_call_service.get_active_sessions()
        
        return {
            "success": True,
            "message": f"Found {sessions_data['total_sessions']} active voice sessions",
            "data": sessions_data
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def voice_call_health_check():
    """
    Health check endpoint for the voice call service
    """
    try:
        # Get comprehensive service status
        service_status = voice_call_service.get_service_status()
        
        return {
            "success": True,
            "message": "Voice call service is healthy",
            "data": service_status
        }
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy") 