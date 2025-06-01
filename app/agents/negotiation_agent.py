from typing import Dict, List, Optional, Any
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
import os
import json
from dotenv import load_dotenv
import logging
from dataclasses import asdict

from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, NegotiationState, 
    NegotiationStatus, PlatformType, ContentType
)
from app.services.pricing_service import PricingService
from app.services.conversation_handler import ConversationHandler

logger = logging.getLogger(__name__)
load_dotenv()

class AdvancedNegotiationAgent:
    def __init__(self):
        """Initialize the brand-side negotiation agent with enhanced capabilities."""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        
        self.pricing_service = PricingService()
        self.conversation_handler = ConversationHandler()
        self.memory = ConversationBufferMemory(return_messages=True)
        
        self._create_agent_tools()
        self._create_agent()

    def _create_agent_tools(self):
        """Create enhanced tools for the negotiation agent."""
        
        def calculate_market_rate_tool(input_str: str) -> str:
            """Calculate market rate for specific influencer and content type."""
            try:
                data = json.loads(input_str)
                
                # Create InfluencerProfile
                profile_data = data.get('influencer_profile', {})
                influencer = InfluencerProfile(
                    name=profile_data.get('name', 'Influencer'),
                    followers=profile_data.get('followers', 0),
                    engagement_rate=profile_data.get('engagement_rate', 0.0),
                    location=profile_data.get('location', 'OTHER'),
                    platforms=[PlatformType(p) for p in profile_data.get('platforms', [])],
                    niches=profile_data.get('niches', [])
                )
                
                platform = PlatformType(data.get('platform'))
                content_type = ContentType(data.get('content_type'))
                
                rate_data = self.pricing_service.calculate_market_rate(
                    influencer, platform, content_type
                )
                
                return json.dumps({
                    "platform": platform.value,
                    "content_type": content_type.value,
                    "market_rate": rate_data.final_rate,
                    "base_rate": rate_data.base_rate_per_1k_followers,
                    "engagement_multiplier": rate_data.engagement_multiplier,
                    "location_multiplier": rate_data.location_multiplier
                })
                
            except Exception as e:
                logger.error(f"Error in market rate calculation: {e}")
                return json.dumps({"error": str(e)})

        def calculate_campaign_cost_tool(input_str: str) -> str:
            """Calculate total campaign cost with breakdown."""
            try:
                data = json.loads(input_str)
                
                profile_data = data.get('influencer_profile', {})
                influencer = InfluencerProfile(
                    name=profile_data.get('name', 'Influencer'),
                    followers=profile_data.get('followers', 0),
                    engagement_rate=profile_data.get('engagement_rate', 0.0),
                    location=profile_data.get('location', 'OTHER'),
                    platforms=[PlatformType(p) for p in profile_data.get('platforms', [])],
                    niches=profile_data.get('niches', [])
                )
                
                content_requirements = data.get('content_requirements', {})
                
                cost_breakdown = self.pricing_service.calculate_total_campaign_cost(
                    influencer, content_requirements
                )
                
                return json.dumps(cost_breakdown)
                
            except Exception as e:
                logger.error(f"Error in campaign cost calculation: {e}")
                return json.dumps({"error": str(e)})

        def suggest_budget_alternatives_tool(input_str: str) -> str:
            """Suggest alternatives when budget doesn't align."""
            try:
                data = json.loads(input_str)
                
                profile_data = data.get('influencer_profile', {})
                influencer = InfluencerProfile(
                    name=profile_data.get('name', 'Influencer'),
                    followers=profile_data.get('followers', 0),
                    engagement_rate=profile_data.get('engagement_rate', 0.0),
                    location=profile_data.get('location', 'OTHER'),
                    platforms=[PlatformType(p) for p in profile_data.get('platforms', [])],
                    niches=profile_data.get('niches', [])
                )
                
                content_requirements = data.get('content_requirements', {})
                target_budget = data.get('target_budget', 0)
                
                suggestions = self.pricing_service.suggest_alternative_pricing(
                    influencer, content_requirements, target_budget
                )
                
                return json.dumps(suggestions)
                
            except Exception as e:
                logger.error(f"Error in budget alternatives: {e}")
                return json.dumps({"error": str(e)})

        def analyze_negotiation_context_tool(input_str: str) -> str:
            """Analyze negotiation context and provide strategic insights."""
            try:
                data = json.loads(input_str)
                
                brand_budget = data.get('brand_budget', 0)
                market_rate = data.get('market_rate', 0)
                influencer_ask = data.get('influencer_ask', 0)
                
                analysis = {
                    "budget_gap": abs(brand_budget - market_rate),
                    "influencer_gap": abs(influencer_ask - market_rate),
                    "negotiation_room": min(brand_budget * 1.1, market_rate * 1.2),
                    "recommendation": "proceed" if abs(brand_budget - market_rate) < market_rate * 0.3 else "negotiate"
                }
                
                if influencer_ask > 0:
                    if influencer_ask <= market_rate * 1.1:
                        analysis["influencer_position"] = "reasonable"
                    elif influencer_ask <= market_rate * 1.3:
                        analysis["influencer_position"] = "high_but_negotiable"
                    else:
                        analysis["influencer_position"] = "significantly_above_market"
                
                return json.dumps(analysis)
                
            except Exception as e:
                logger.error(f"Error in negotiation analysis: {e}")
                return json.dumps({"error": str(e)})

        self.tools = [
            Tool(
                name="calculate_market_rate",
                func=calculate_market_rate_tool,
                description="Calculate market rate for specific content type. Input: JSON with influencer_profile, platform, content_type"
            ),
            Tool(
                name="calculate_campaign_cost",
                func=calculate_campaign_cost_tool,
                description="Calculate total campaign cost breakdown. Input: JSON with influencer_profile, content_requirements"
            ),
            Tool(
                name="suggest_budget_alternatives",
                func=suggest_budget_alternatives_tool,
                description="Suggest alternatives when budget doesn't align. Input: JSON with influencer_profile, content_requirements, target_budget"
            ),
            Tool(
                name="analyze_negotiation_context",
                func=analyze_negotiation_context_tool,
                description="Analyze negotiation context for strategic insights. Input: JSON with brand_budget, market_rate, influencer_ask"
            )
        ]

    def _create_agent(self):
        """Create the LangChain React agent with enhanced conversational abilities."""
        
        prompt = PromptTemplate.from_template("""
You are Alex, a professional brand partnerships manager representing the company side of influencer collaborations. You're friendly, knowledgeable, and focused on building successful partnerships while staying within budget constraints.

PERSONALITY TRAITS:
- Professional yet approachable, representing your company with confidence
- Data-driven and transparent about budget limitations
- Solution-oriented, looking for creative ways to make partnerships work
- Respectful of influencers while advocating for your brand's interests
- Experienced in market rates and industry best practices

NEGOTIATION APPROACH AS BRAND REPRESENTATIVE:
1. Lead with your company's campaign goals and budget parameters
2. Present fair market-rate offers based on thorough research
3. Be transparent about budget constraints while remaining flexible
4. Focus on mutual value creation within your company's financial limits
5. Maintain professionalism even when negotiations don't reach agreement

Your primary goal is to secure quality influencer partnerships that deliver ROI for your company while offering fair compensation to creators.
4. Address concerns directly and honestly
5. Celebrate agreements and maintain relationships even when deals don't work out

AVAILABLE TOOLS: {tools}
TOOL NAMES: {tool_names}

CONVERSATION CONTEXT:
{chat_history}

CURRENT SITUATION:
{input}

Think step by step about how to respond. Use tools when you need data analysis or calculations. Always be conversational and human-like in your responses.

Thought: What information do I need to provide the best response?
Action: [tool name if needed, or skip to Final Answer]
Action Input: [tool input if using a tool]
Observation: [tool result if using a tool]
Thought: Now I can provide a complete response
Final Answer: [Your conversational response]

Begin!

Thought: {agent_scratchpad}
""")

        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=True
        )

    async def start_negotiation_conversation(
        self, 
        brand_details: BrandDetails, 
        influencer_profile: InfluencerProfile
    ) -> Dict[str, Any]:
        """Start a new negotiation conversation."""
        try:
            # Create session in conversation handler
            session_id = self.conversation_handler.create_session(
                brand_details, influencer_profile
            )
            
            # Generate greeting message
            greeting = self.conversation_handler.generate_greeting_message(session_id)
            
            # Generate market analysis
            market_analysis = self.conversation_handler.generate_market_analysis(session_id)
            
            # Generate initial proposal
            proposal = self.conversation_handler.generate_proposal(session_id)
            
            # Combine initial messages
            initial_message = f"{greeting}\n\n---\n\n{market_analysis}\n\n---\n\n{proposal}"
            
            return {
                "session_id": session_id,
                "message": initial_message,
                "status": "initiated",
                "conversation_stage": "proposal_presented"
            }
            
        except Exception as e:
            logger.error(f"Error starting negotiation: {e}")
            return {
                "error": str(e),
                "message": "I apologize, but I encountered an error starting our conversation. Let me try again."
            }

    async def continue_conversation(
        self, 
        session_id: str, 
        user_input: str
    ) -> Dict[str, Any]:
        """Continue the negotiation conversation."""
        try:
            # Get session state
            session = self.conversation_handler.get_session_state(session_id)
            if not session:
                return {
                    "error": "Session not found",
                    "message": "I'm sorry, I couldn't find our conversation. Let's start a new negotiation."
                }
            
            # Format conversation history for the agent
            chat_history = ""
            for msg in session.conversation_history[-6:]:  # Last 6 messages for context
                role = "Human" if msg["role"] == "user" else "Assistant"
                chat_history += f"{role}: {msg['message']}\n\n"
            
            # Prepare context for the agent
            context = f"""
            BRAND: {session.brand_details.name}
            BUDGET: ${session.brand_details.budget:,.2f}
            INFLUENCER: {session.influencer_profile.name}
            FOLLOWERS: {session.influencer_profile.followers:,}
            ENGAGEMENT: {session.influencer_profile.engagement_rate:.1%}
            CURRENT STATUS: {session.status.value}
            ROUND: {session.negotiation_round}
            
            USER JUST SAID: "{user_input}"
            
            Please respond conversationally as Alex, considering the context and using tools if you need to calculate rates or analyze the situation.
            """
            
            # Execute the agent
            response = await self.agent_executor.ainvoke({
                "input": context,
                "chat_history": chat_history
            })
            
            agent_response = response.get("output", "I'm processing your message...")
            
            # Also use conversation handler for structured responses when appropriate
            handler_response = self.conversation_handler.handle_user_response(
                session_id, user_input
            )
            
            # Combine intelligent agent response with structured handler when needed
            if session.status in [NegotiationStatus.AGREED, NegotiationStatus.REJECTED]:
                final_response = handler_response
            else:
                # Use agent response but update session state through handler
                final_response = agent_response
            
            # Get updated session state
            updated_session = self.conversation_handler.get_session_state(session_id)
            
            return {
                "session_id": session_id,
                "message": final_response,
                "status": updated_session.status.value if updated_session else "unknown",
                "negotiation_round": updated_session.negotiation_round if updated_session else 1,
                "conversation_stage": self._determine_conversation_stage(updated_session)
            }
            
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            return {
                "error": str(e),
                "message": "I encountered an issue processing your response. Could you please try rephrasing that?"
            }

    def _determine_conversation_stage(self, session: Optional[NegotiationState]) -> str:
        """Determine current conversation stage."""
        if not session:
            return "unknown"
        
        if session.status == NegotiationStatus.INITIATED:
            return "initial_proposal"
        elif session.status == NegotiationStatus.IN_PROGRESS:
            return "active_negotiation"
        elif session.status == NegotiationStatus.COUNTER_OFFER:
            return "counter_negotiation"
        elif session.status == NegotiationStatus.AGREED:
            return "agreement_reached"
        elif session.status == NegotiationStatus.REJECTED:
            return "negotiation_ended"
        else:
            return "unknown"

    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the current negotiation state."""
        session = self.conversation_handler.get_session_state(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "status": session.status.value,
            "brand": session.brand_details.name,
            "influencer": session.influencer_profile.name,
            "negotiation_round": session.negotiation_round,
            "current_offer": asdict(session.current_offer) if session.current_offer else None,
            "agreed_terms": asdict(session.agreed_terms) if session.agreed_terms else None,
            "conversation_length": len(session.conversation_history)
        }

    def clear_session(self, session_id: str) -> Dict[str, str]:
        """Clear a specific negotiation session."""
        if session_id in self.conversation_handler.active_sessions:
            del self.conversation_handler.active_sessions[session_id]
            return {"status": "Session cleared"}
        return {"status": "Session not found"}

    def list_active_sessions(self) -> Dict[str, List[str]]:
        """List all active negotiation sessions."""
        return {
            "active_sessions": list(self.conversation_handler.active_sessions.keys())
        }


# Example usage and testing
async def test_negotiation_agent():
    """Test the negotiation agent with sample data."""
    agent = AdvancedNegotiationAgent()
    
    # Sample brand details
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
    
    # Sample influencer profile  
    influencer = InfluencerProfile(
        name="Alex Green",
        followers=75000,
        engagement_rate=0.065,
        location="US",
        platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE],
        niches=["sustainability", "technology", "lifestyle"],
        previous_brand_collaborations=12
    )
    
    # Start negotiation
    result = await agent.start_negotiation_conversation(brand, influencer)
    print("🤖 Agent Response:", result["message"])
    
    # Simulate user responses
    test_responses = [
        "This looks interesting! The pricing seems a bit high though. Could we discuss the rates?",
        "I usually charge $300 per Instagram post. Would that work?",
        "That sounds fair. I'm interested in moving forward!"
    ]
    
    session_id = result["session_id"]
    
    for user_response in test_responses:
        print(f"\n👤 User: {user_response}")
        
        response = await agent.continue_conversation(session_id, user_response)
        print(f"\n🤖 Agent: {response['message']}")
        print(f"Status: {response['status']}")
        
        if response["status"] in ["agreed", "rejected"]:
            break

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_negotiation_agent())