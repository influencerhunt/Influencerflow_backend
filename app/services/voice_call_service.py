import os
import logging
from typing import Dict, Optional
from app.core.config import settings
from app.services.agent_service import agent_service

# Setup logging
logger = logging.getLogger(__name__)

class VoiceCallService:
    """Service for handling voice calls via Twilio and delegating AI conversations to AgentService"""
    
    def __init__(self):
        # Configuration from settings - with fallback for MVP
        self.twilio_account_sid = settings.twilio_account_sid or "dummy_sid"
        self.twilio_auth_token = settings.twilio_auth_token or "dummy_token"
        self.twilio_number = settings.twilio_number or "+1234567890"
        
        # Initialize Twilio clients only if we have real credentials
        self.twilio_client = None
        self.validator = None
        
        if all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_number]):
            try:
                from twilio.rest import Client
                from twilio.request_validator import RequestValidator
                
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
                self.validator = RequestValidator(self.twilio_auth_token)
                logger.info("Voice call service initialized with real Twilio credentials")
            except ImportError as e:
                logger.warning(f"Missing dependencies for voice call service: {e}")
            except Exception as e:
                logger.warning(f"Failed to initialize voice call service: {e}")
        else:
            logger.warning("Voice call service running in mock mode - missing Twilio credentials")
        
        # Track active call sessions
        self.active_calls: Dict[str, Dict] = {}

    def validate_twilio_request(self, url: str, params: Dict, signature: str) -> bool:
        """Validate Twilio request signature"""
        if not self.validator:
            return True  # Skip validation in MVP mode
        return self.validator.validate(url, params, signature)

    def _create_gather_twiml(self, action_endpoint: str) -> any:
        """Create a standardized Gather TwiML element"""
        try:
            from twilio.twiml.voice_response import Gather
        except ImportError:
            return None
            
        return Gather(
            input="speech",
            action=action_endpoint,
            method="POST",
            timeout=30,
            speechTimeout=5,
            partialResultCallback="/api/v1/voice-call/partial",
            partialResultCallbackMethod="POST",
            enhanced=True,
            language="en-IN",
            speechModel="phone_call",
            profanityFilter=False,
            hints="rupees, lakhs, crores, price, rate, amount, cost, budget, negotiation, deal, partnership, instagram, posts, endorsement, mama earth, influencer, marketing, brand, collaboration, sponsored, content, social media, followers, engagement, reach"
        )

    def handle_inbound_call(self, call_sid: str) -> str:
        """Handle inbound call and return TwiML response"""
        logger.info(f"Handling inbound call for CallSid: {call_sid}")
        
        # Track this call as active
        self.active_calls[call_sid] = {
            "status": "active",
            "start_time": "now"  # In real implementation, use datetime
        }
        
        # Create agent session for this call
        agent_service.create_chat_session(call_sid)
        
        # Import here to avoid issues if twilio is not installed
        try:
            from twilio.twiml.voice_response import VoiceResponse
        except ImportError:
            logger.error("Twilio library not installed")
            return '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service temporarily unavailable</Say></Response>'
        
        # Create TwiML response with agent's greeting
        twiml = VoiceResponse()
        gather = self._create_gather_twiml("/api/v1/voice-call/gather")
        
        if gather:
            gather.say(
                agent_service.get_greeting_message(), 
                voice="alice", 
                language="en-IN"
            )
            twiml.append(gather)
        else:
            twiml.say("Service temporarily unavailable", voice="alice", language="en-IN")
        
        return str(twiml)

    def handle_gather(self, call_sid: str, user_speech: str) -> str:
        """Handle speech input and return TwiML response"""
        logger.info(f"Handling gather for CallSid: {call_sid}, speech: {user_speech}")
        
        try:
            from twilio.twiml.voice_response import VoiceResponse
        except ImportError:
            return '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service temporarily unavailable</Say></Response>'
        
        twiml = VoiceResponse()
        
        # Check if we have an active session
        if call_sid not in self.active_calls:
            logger.error(f"No active call found for CallSid: {call_sid}")
            twiml.say(
                "Sorry, our session got disconnected. Please call back to continue discussing the Instagram partnership.",
                voice="alice", 
                language="en-IN"
            )
            return str(twiml)

        # If no speech detected, continue listening
        if not user_speech:
            logger.debug(f"No speech detected for CallSid: {call_sid}")
            gather_continue = self._create_gather_twiml("/api/v1/voice-call/gather")
            
            if gather_continue:
                gather_continue.say(
                    "I'm still here and listening. Please share your thoughts about the Instagram endorsement deal.",
                    voice="alice", 
                    language="en-IN"
                )
                twiml.append(gather_continue)
            else:
                twiml.say("Please try again", voice="alice", language="en-IN")
            return str(twiml)

        try:
            # Send user input to agent service and get response
            agent_reply = agent_service.send_message(call_sid, user_speech)
            
            # Create next gather for continued conversation
            gather_next = self._create_gather_twiml("/api/v1/voice-call/gather")
            
            if gather_next:
                gather_next.say(agent_reply, voice="alice", language="en-IN")
                twiml.append(gather_next)
            else:
                twiml.say(agent_reply, voice="alice", language="en-IN")
            
        except Exception as e:
            logger.exception("Error getting response from agent service")
            gather_error = self._create_gather_twiml("/api/v1/voice-call/gather")
            
            error_message = "I had a brief technical hiccup. Could you please repeat what you were saying about the Instagram deal?"
            
            if gather_error:
                gather_error.say(error_message, voice="alice", language="en-IN")
                twiml.append(gather_error)
            else:
                twiml.say(error_message, voice="alice", language="en-IN")
        
        return str(twiml)

    def handle_partial_results(self, call_sid: str, partial_result: str) -> str:
        """Handle partial speech results for interruption detection"""
        logger.debug(f"Partial result for {call_sid}: {partial_result}")
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'

    def make_outbound_call(self, to_number: str, webhook_base_url: str) -> str:
        """Initiate an outbound call"""
        if not self.twilio_client:
            logger.warning("Mock outbound call - no Twilio client available")
            mock_call_sid = f"MOCK_CALL_SID_{to_number}"
            # Track mock call
            self.active_calls[mock_call_sid] = {
                "status": "mock-active",
                "to_number": to_number,
                "start_time": "now"
            }
            return mock_call_sid
            
        try:
            logger.info(f"Placing outbound call to {to_number}")
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.twilio_number,
                url=f"{webhook_base_url.rstrip('/')}/api/v1/voice-call/voice"
            )
            
            # Track real call
            self.active_calls[call.sid] = {
                "status": "active",
                "to_number": to_number,
                "start_time": "now"
            }
            
            logger.info(f"Call initiated with SID: {call.sid}")
            return call.sid
        except Exception as e:
            logger.error(f"Error making outbound call: {e}")
            raise

    def get_call_status(self, call_sid: str) -> Dict:
        """Get the status of a call"""
        if not self.twilio_client:
            # Return mock data based on our tracking
            call_info = self.active_calls.get(call_sid, {})
            return {
                "sid": call_sid,
                "status": call_info.get("status", "mock-completed"),
                "duration": "120",
                "direction": "outbound-api",
                "from_number": self.twilio_number,
                "to_number": call_info.get("to_number", "+1234567890")
            }
            
        try:
            call = self.twilio_client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "direction": call.direction,
                "from_number": call.from_,
                "to_number": call.to
            }
        except Exception as e:
            logger.error(f"Error fetching call status: {e}")
            raise

    def get_active_sessions(self) -> Dict:
        """Get active voice call sessions"""
        # Combine our call tracking with agent session tracking
        voice_sessions = list(self.active_calls.keys())
        agent_sessions_data = agent_service.get_active_sessions()
        
        return {
            "voice_sessions": voice_sessions,
            "agent_sessions": agent_sessions_data["active_sessions"],
            "total_sessions": len(voice_sessions)
        }

    def end_session(self, call_sid: str):
        """Clean up session when call ends"""
        # Clean up voice call tracking
        if call_sid in self.active_calls:
            del self.active_calls[call_sid]
            logger.info(f"Cleaned up voice call session for CallSid: {call_sid}")
        
        # Clean up agent session
        agent_service.end_session(call_sid)

    def get_service_status(self) -> Dict:
        """Get voice call service status"""
        agent_status = agent_service.get_service_status()
        
        return {
            "service": "voice-call",
            "status": "healthy",
            "twilio_client": "real" if self.twilio_client else "mock",
            "active_calls": len(self.active_calls),
            "agent_service": agent_status,
            "mode": "mvp" if not self.twilio_client else "production"
        }

# Create a global instance
voice_call_service = VoiceCallService() 