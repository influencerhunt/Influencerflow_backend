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
import requests
from datetime import datetime

from app.models.negotiation_models import (
    BrandDetails, InfluencerProfile, NegotiationState, 
    NegotiationStatus, PlatformType, ContentType, LocationType
)
from app.services.conversation_handler_db import ConversationHandlerDB

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
        
        self.conversation_handler = ConversationHandlerDB()
        self.memory = ConversationBufferMemory(return_messages=True)
        
        self._create_agent_tools()
        self._create_agent()

    def _create_agent_tools(self):
        """Create enhanced tools for the negotiation agent."""
        
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

        def handle_currency_operations_tool(input_str: str) -> str:
            """Handle currency conversions, formatting, and exchange rate operations."""
            try:
                # Clean input string - remove backticks and extra whitespace
                cleaned_input = input_str.strip()
                if cleaned_input.startswith('`') and cleaned_input.endswith('`'):
                    cleaned_input = cleaned_input[1:-1].strip()
                
                # Handle cases where the input might be wrapped in additional quotes
                if cleaned_input.startswith('"') and cleaned_input.endswith('"'):
                    cleaned_input = cleaned_input[1:-1]
                
                data = json.loads(cleaned_input)
                operation = data.get('operation', 'convert')
                
                if operation == 'convert':
                    amount = data.get('amount', 0)
                    from_currency = data.get('from_currency', 'USD').upper()
                    to_currency = data.get('to_currency', 'USD').upper()
                    
                    if from_currency == to_currency:
                        return json.dumps({
                            "original_amount": amount,
                            "converted_amount": amount,
                            "from_currency": from_currency,
                            "to_currency": to_currency,
                            "exchange_rate": 1.0,
                            "formatted": self._format_currency(amount, to_currency)
                        })
                    
                    # Get exchange rate
                    exchange_rate = self._get_exchange_rate(from_currency, to_currency)
                    converted_amount = amount * exchange_rate
                    
                    return json.dumps({
                        "original_amount": amount,
                        "converted_amount": round(converted_amount, 2),
                        "from_currency": from_currency,
                        "to_currency": to_currency,
                        "exchange_rate": exchange_rate,
                        "formatted": self._format_currency(converted_amount, to_currency),
                        "conversion_note": f"{self._format_currency(amount, from_currency)} = {self._format_currency(converted_amount, to_currency)}"
                    })
                
                elif operation == 'format':
                    amount = data.get('amount', 0)
                    currency = data.get('currency', 'USD').upper()
                    
                    return json.dumps({
                        "amount": amount,
                        "currency": currency,
                        "formatted": self._format_currency(amount, currency)
                    })
                
                elif operation == 'compare_rates':
                    base_amount = data.get('amount', 0)
                    base_currency = data.get('currency', 'USD').upper()
                    target_currencies = data.get('target_currencies', ['EUR', 'GBP', 'CAD'])
                    
                    comparisons = {}
                    for target_currency in target_currencies:
                        if target_currency.upper() != base_currency:
                            rate = self._get_exchange_rate(base_currency, target_currency.upper())
                            converted = base_amount * rate
                            comparisons[target_currency] = {
                                "amount": round(converted, 2),
                                "exchange_rate": rate,
                                "formatted": self._format_currency(converted, target_currency.upper())
                            }
                    
                    return json.dumps({
                        "base_amount": base_amount,
                        "base_currency": base_currency,
                        "base_formatted": self._format_currency(base_amount, base_currency),
                        "conversions": comparisons
                    })
                
                elif operation == 'suggest_pricing':
                    amount_usd = data.get('amount_usd', 0)
                    influencer_country = data.get('influencer_country', 'US')
                    
                    # Map countries to currencies
                    country_currency_map = {
                        'US': 'USD', 'CA': 'CAD', 'GB': 'GBP', 'AU': 'AUD',
                        'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR',
                        'IN': 'INR', 'BR': 'BRL', 'MX': 'MXN', 'JP': 'JPY'
                    }
                    
                    local_currency = country_currency_map.get(influencer_country, 'USD')
                    
                    if local_currency != 'USD':
                        rate = self._get_exchange_rate('USD', local_currency)
                        local_amount = amount_usd * rate
                        
                        return json.dumps({
                            "usd_amount": amount_usd,
                            "local_currency": local_currency,
                            "local_amount": round(local_amount, 2),
                            "exchange_rate": rate,
                            "usd_formatted": self._format_currency(amount_usd, 'USD'),
                            "local_formatted": self._format_currency(local_amount, local_currency),
                            "suggestion": f"Consider offering {self._format_currency(local_amount, local_currency)} (approximately {self._format_currency(amount_usd, 'USD')})"
                        })
                    else:
                        return json.dumps({
                            "usd_amount": amount_usd,
                            "local_currency": 'USD',
                            "local_amount": amount_usd,
                            "formatted": self._format_currency(amount_usd, 'USD')
                        })
                
                else:
                    return json.dumps({"error": "Unknown operation. Supported: convert, format, compare_rates, suggest_pricing"})
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error in currency operations: {e}. Input was: {input_str}")
                return json.dumps({
                    "error": f"Invalid JSON format. Please provide valid JSON. Error: {str(e)}",
                    "received_input": input_str[:100]  # Show first 100 chars for debugging
                })
            except Exception as e:
                logger.error(f"Error in currency operations: {e}")
                return json.dumps({"error": str(e)})

        self.tools = [
            Tool(
                name="analyze_negotiation_context",
                func=analyze_negotiation_context_tool,
                description="Analyze negotiation context for strategic insights. Input: JSON with brand_budget, market_rate, influencer_ask"
            ),
            Tool(
                name="handle_currency_operations",
                func=handle_currency_operations_tool,
                description="Handle currency conversions and formatting. Operations: 'convert' (amount, from_currency, to_currency), 'format' (amount, currency), 'compare_rates' (amount, currency, target_currencies), 'suggest_pricing' (amount_usd, influencer_country)"
            )
        ]

    def _get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get current exchange rate between two currencies."""
        try:
            # Try to use a free exchange rate API (exchangerate-api.com)
            response = requests.get(
                f"https://api.exchangerate-api.com/v4/latest/{from_currency}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                rate = data.get('rates', {}).get(to_currency)
                if rate:
                    return float(rate)
            
            # Fallback to approximate rates if API fails
            logger.warning(f"API failed for {from_currency} to {to_currency}, using fallback rates")
            return self._get_fallback_exchange_rate(from_currency, to_currency)
            
        except Exception as e:
            logger.error(f"Error getting exchange rate: {e}")
            return self._get_fallback_exchange_rate(from_currency, to_currency)
    
    def _get_fallback_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Fallback exchange rates (approximate, for when API is unavailable)."""
        # These are approximate rates and should be updated periodically
        rates_to_usd = {
            'USD': 1.0, 'EUR': 1.08, 'GBP': 1.27, 'CAD': 0.74,
            'AUD': 0.66, 'JPY': 0.0067, 'INR': 0.012, 'BRL': 0.20,
            'MXN': 0.055, 'CHF': 1.10, 'CNY': 0.14, 'KRW': 0.00076
        }
        
        if from_currency == 'USD':
            return 1.0 / rates_to_usd.get(to_currency, 1.0)
        elif to_currency == 'USD':
            return rates_to_usd.get(from_currency, 1.0)
        else:
            # Convert through USD
            from_to_usd = rates_to_usd.get(from_currency, 1.0)
            usd_to_target = 1.0 / rates_to_usd.get(to_currency, 1.0)
            return from_to_usd * usd_to_target
    
    def _format_currency(self, amount: float, currency: str) -> str:
        """Format currency amount with proper symbol and formatting."""
        currency_symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'CAD': 'C$', 'AUD': 'A$', 'CHF': 'CHF ', 'CNY': '¥',
            'INR': '₹', 'BRL': 'R$', 'MXN': 'MX$', 'KRW': '₩'
        }
        
        symbol = currency_symbols.get(currency, f'{currency} ')
        
        # Format based on currency (some don't use decimals)
        if currency in ['JPY', 'KRW']:
            return f"{symbol}{amount:,.0f}"
        else:
            return f"{symbol}{amount:,.2f}"

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

TOOL USAGE INSTRUCTIONS:
- When using the handle_currency_operations tool, provide clean JSON without backticks or markdown formatting
- Example: {{"operation": "convert", "amount": 100, "from_currency": "USD", "to_currency": "EUR"}}
- Use currency tools when dealing with international influencers or when currency conversion is mentioned

CONVERSATION CONTEXT:
{chat_history}

CURRENT SITUATION:
{input}

Think step by step about how to respond. Use tools when you need data analysis or calculations. Always be conversational and human-like in your responses.

Thought: What information do I need to provide the best response?
Action: [tool name if needed, or skip to Final Answer]
Action Input: [Clean JSON format for tool input - NO backticks or markdown]
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
            session_id = await self.conversation_handler.create_session(
                brand_details, influencer_profile
            )
            print(f"Brand budget currency: {brand_details.budget_currency}")
            print(f"Brand budget: {brand_details.budget}")
            
            
            # Generate greeting message
            greeting = await self.conversation_handler.generate_greeting_message(session_id)
            
            # Generate market analysis
            market_analysis = await self.conversation_handler.generate_market_analysis(session_id)
            
            # Generate initial proposal
            proposal = await self.conversation_handler.generate_proposal(session_id)
            
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
            session = await self.conversation_handler.get_session_state(session_id)
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
            handler_response = await self.conversation_handler.handle_user_response(
                session_id, user_input
            )
            
            # Combine intelligent agent response with structured handler when needed
            if session.status in [NegotiationStatus.AGREED, NegotiationStatus.REJECTED]:
                final_response = handler_response
            else:
                # Use agent response but update session state through handler
                final_response = agent_response
            
            # Get updated session state
            updated_session = await self.conversation_handler.get_session_state(session_id)
            
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
        session = await self.conversation_handler.get_session_state(session_id)
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

    async def clear_session(self, session_id: str) -> Dict[str, str]:
        """Clear a specific negotiation session."""
        try:
            # For database-backed handler, we would need to implement a delete method
            # For now, return a message indicating the session would be cleared
            return {"status": "Session cleared from database"}
        except Exception as e:
            logger.error(f"Error clearing session {session_id}: {e}")
            return {"status": "Error clearing session"}

    async def list_active_sessions(self) -> Dict[str, Any]:
        """List all active negotiation sessions."""
        try:
            # For database-backed handler, we would need to implement a list method
            # For now, return a placeholder
            return {
                "active_sessions": [],
                "message": "Database-backed session listing not yet implemented"
            }
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return {"active_sessions": [], "error": str(e)}


# Example usage and testing
async def test_negotiation_agent():
    """Test the negotiation agent with sample data."""
    agent = AdvancedNegotiationAgent()
    
    # Test currency operations
    print("🔄 Testing Currency Operations:")
    
    # Test currency conversion
    print("\n💱 Currency Conversion Test:")
    conv_result = agent.tools[1].func(json.dumps({
        "operation": "convert",
        "amount": 1000,
        "from_currency": "USD",
        "to_currency": "EUR"
    }))
    print(f"USD to EUR conversion: {json.loads(conv_result)}")
    
    # Test currency formatting
    print("\n💰 Currency Formatting Test:")
    format_result = agent.tools[1].func(json.dumps({
        "operation": "format",
        "amount": 2500.50,
        "currency": "GBP"
    }))
    print(f"GBP formatting: {json.loads(format_result)}")
    
    # Test pricing suggestions for international influencers
    print("\n🌍 International Pricing Suggestion Test:")
    pricing_result = agent.tools[1].func(json.dumps({
        "operation": "suggest_pricing",
        "amount_usd": 500,
        "influencer_country": "DE"
    }))
    print(f"German influencer pricing: {json.loads(pricing_result)}")
    
    print("\n" + "="*50)
    print("🤝 Starting Negotiation Test:")
    
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
        location=LocationType.US,
        platforms=[PlatformType.INSTAGRAM, PlatformType.YOUTUBE],
        niches=["sustainability", "technology", "lifestyle"],
        previous_brand_collaborations=12
    )
    
    # Start negotiation
    result = await agent.start_negotiation_conversation(brand, influencer)
    print("🤖 Agent Response:", result["message"])
    
    # Simulate user responses including currency-related questions
    test_responses = [
        "This looks interesting! Could you also show me what this would be in Euros? I'm based in Germany.",
        "I usually charge €300 per Instagram post. Would that work for your budget?",
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