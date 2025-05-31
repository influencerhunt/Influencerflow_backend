import os
import logging
from typing import Dict, Optional, Any
from app.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

class AgentService:
    """Service for handling AI agent conversations using Google Gemini"""
    
    def __init__(self):
        # Configuration from settings - with fallback for MVP
        self.google_api_key = settings.google_api_key or "dummy_key"
        
        # Initialize Gemini client only if we have real credentials
        self.gemini_client = None
        
        if settings.google_api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.google_api_key)
                logger.info("Agent service initialized with real Gemini credentials")
            except ImportError as e:
                logger.warning(f"Missing dependencies for agent service: {e}")
            except Exception as e:
                logger.warning(f"Failed to initialize agent service: {e}")
        else:
            logger.warning("Agent service running in mock mode - missing Google API key")
        
        # Model configuration
        self.model_name = "gemini-2.0-flash"
        
        # In-memory store of session_id → Gemini chat session
        self.chat_sessions: Dict[str, Any] = {}
        
        # System prompt for negotiations
        self.system_prompt = """You are a professional negotiation agent for influencer marketing deals. 
Your role is to negotiate on behalf of an influencer for Instagram post endorsements for Mama Earth products.

Key details:
- Product: Mama Earth (eco-friendly personal care products)
- Service: Instagram post endorsements  
- Your target: Negotiate for 5 Instagram posts
- Maximum budget: $500 per post (total $2500 for 5 posts)
- You should start negotiations and try to get the best deal possible within this budget

Be professional, persuasive, and highlight the value of Instagram endorsements. 
Discuss reach, engagement rates, content quality, and brand alignment.
Keep responses concise for phone conversations (under 100 words per response).
Stay focused on the negotiation and don't get sidetracked.

IMPORTANT: You may be speaking with people who use Indian English. Be patient and understanding if:
- They use terms like "rupees, lakhs, crores" for money
- They say "good name" instead of "what's your name"
- They use British spellings (colour, realise, etc.)
- They have different pronunciation patterns
- They use phrases like "do one thing", "out of station", "prepone"
- Don't immediately say "yes" or "no" to their questions try negotiating for the best deal and not reveal our budget early on unless the quoted amount is within our budget.

Always be respectful and adapt to their communication style while staying focused on the Instagram deal negotiation."""

        # Greeting message for starting conversations
        self.greeting_message = "Hello! I'm your negotiation agent for Instagram marketing deals. I'm here to discuss a potential partnership with Mama Earth for Instagram post endorsements. I'm listening - please tell me your thoughts on this opportunity."

    def create_chat_session(self, session_id: str) -> Any:
        """Create a new Gemini chat session"""
        if not self.gemini_client:
            logger.warning(f"Creating mock chat session for {session_id} - no Gemini client available")
            mock_chat = type('MockChat', (), {
                'send_message': lambda msg: type('MockResponse', (), {
                    'text': f'This is a mock AI response to: "{msg}". In a real scenario, I would negotiate the Instagram deal professionally.'
                })()
            })()
            self.chat_sessions[session_id] = mock_chat
            return mock_chat
            
        try:
            chat = self.gemini_client.chats.create(model=self.model_name)
            # Initialize the chat with the system prompt
            chat.send_message(self.system_prompt)
            self.chat_sessions[session_id] = chat
            logger.info(f"Created new chat session for session_id: {session_id}")
            return chat
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise

    def get_chat_session(self, session_id: str) -> Optional[Any]:
        """Get existing chat session"""
        return self.chat_sessions.get(session_id)

    def send_message(self, session_id: str, message: str) -> str:
        """Send a message to the AI agent and get response"""
        logger.info(f"Processing message for session {session_id}: {message}")
        
        # Get or create chat session
        chat = self.get_chat_session(session_id)
        if chat is None:
            chat = self.create_chat_session(session_id)
        
        try:
            # Send message to Gemini and get response
            response = chat.send_message(message)
            reply_text = response.text
            logger.info(f"Agent reply for session {session_id}: {reply_text}")
            return reply_text
            
        except Exception as e:
            logger.error(f"Error sending message to agent: {e}")
            # Return a fallback response
            return "I had a brief technical issue. Could you please repeat what you were saying about the Instagram deal?"

    def get_greeting_message(self) -> str:
        """Get the initial greeting message for new conversations"""
        return self.greeting_message

    def end_session(self, session_id: str):
        """Clean up chat session"""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            logger.info(f"Cleaned up chat session for session_id: {session_id}")

    def get_active_sessions(self) -> Dict:
        """Get list of active chat sessions"""
        return {
            "active_sessions": list(self.chat_sessions.keys()),
            "count": len(self.chat_sessions)
        }

    def update_system_prompt(self, new_prompt: str):
        """Update the system prompt (useful for different conversation types)"""
        self.system_prompt = new_prompt
        logger.info("System prompt updated")

    def get_service_status(self) -> Dict:
        """Get agent service status"""
        return {
            "service": "agent",
            "status": "healthy",
            "gemini_client": "real" if self.gemini_client else "mock",
            "active_sessions": len(self.chat_sessions),
            "model": self.model_name
        }

# Create a global instance
agent_service = AgentService() 