"""
Influencer Brand Deal Negotiator Agent
A conversational AI agent that negotiates with influencers for brand deals
using LangChain React Agents and Gemini, with Supabase integration.
"""

import os
import json
import logging
import re
import uuid
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BrandDetails:
    """Brand details for the negotiation"""
    name: str
    budget: float
    budget_currency: str
    goals: List[str]
    target_platforms: List[str]
    content_requirements: Dict[str, int]
    campaign_duration_days: int
    target_audience: str
    brand_guidelines: str
    brand_location: str

@dataclass
class InfluencerProfile:
    """Influencer profile for the negotiation"""
    name: str
    followers: int
    engagement_rate: float
    location: str
    platforms: List[str]
    niches: List[str]
    previous_brand_collaborations: int

@dataclass
class NegotiationState:
    """Current state of the negotiation"""
    session_id: str
    brand_details: BrandDetails
    influencer_profile: InfluencerProfile
    current_offer: float
    max_budget: float
    deliverables_agreed: Dict[str, Any]
    messages: List[Dict[str, str]]
    status: str
    created_at: datetime

class RealTimeMarketResearchTool:
    """Tool for real-time influencer marketing rate research using Serper API"""
    
    def __init__(self):
        self.name = "realtime_market_research"
        self.description = "Research current influencer marketing rates in real-time using web search. Input should be a JSON string with influencer details and platform information."
        self.serper_api_key = os.getenv("SERPER_API_KEY")
    
    def run(self, query: str) -> str:
        """Research real-time market rates"""
        try:
            data = json.loads(query)
            influencer_data = data.get("influencer", {})
            deliverables = data.get("deliverables", {})
            
            followers = influencer_data.get("followers", 0)
            location = influencer_data.get("location", "india")
            platforms = influencer_data.get("platforms", ["instagram"])
            niches = influencer_data.get("niches", ["general"])
            engagement_rate = influencer_data.get("engagement_rate", 3.0)
            
            # Research current market rates
            market_data = self._search_market_rates(followers, location, platforms, niches)
            
            # Calculate estimated rate based on research
            estimated_rate = self._calculate_rate_from_research(
                market_data, followers, engagement_rate, deliverables
            )
            
            return f"""Real-time market research results:
            
📊 Market Analysis for {followers:,} followers in {location}:
{market_data}

💰 Estimated Rate: ₹{estimated_rate:,.0f}
📈 Engagement Factor: {engagement_rate}% ({"Above average" if engagement_rate > 3.5 else "Average" if engagement_rate > 2.5 else "Below average"})
🎯 Platforms: {', '.join(platforms)}
🏷️ Niches: {', '.join(niches)}

💡 Recommendation: Consider rates between ₹{estimated_rate * 0.8:,.0f} - ₹{estimated_rate * 1.2:,.0f} based on current market conditions."""
            
        except Exception as e:
            logger.error(f"Error in real-time market research: {e}")
            return f"Error researching market rates: {e}. Using industry averages as fallback."
    
    def _search_market_rates(self, followers: int, location: str, platforms: List[str], niches: List[str]) -> str:
        """Search for current market rates using Serper API"""
        if not self.serper_api_key:
            return self._get_fallback_market_data(followers, location, platforms)
        
        try:
            # Construct search query for current rates
            followers_range = self._get_follower_range(followers)
            platform_str = " ".join(platforms)
            niche_str = " ".join(niches)
            
            search_query = f"influencer marketing rates {location} {platform_str} {followers_range} followers {niche_str} 2024 2025 cost per post pricing"
            
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': search_query,
                'gl': 'in' if location.lower() == 'india' else 'us',
                'hl': 'en',
                'num': 5
            }
            
            response = requests.post(
                'https://google.serper.dev/search',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                return self._extract_rate_insights(results, followers)
            else:
                logger.warning(f"Serper API error: {response.status_code}")
                return self._get_fallback_market_data(followers, location, platforms)
                
        except Exception as e:
            logger.error(f"Error calling Serper API: {e}")
            return self._get_fallback_market_data(followers, location, platforms)
    
    def _get_follower_range(self, followers: int) -> str:
        """Get follower range category"""
        if followers < 10000:
            return "micro"
        elif followers < 100000:
            return "mid-tier"
        elif followers < 1000000:
            return "macro"
        else:
            return "mega"
    
    def _extract_rate_insights(self, search_results: dict, followers: int) -> str:
        """Extract rate insights from search results"""
        insights = []
        
        # Extract information from organic results
        organic_results = search_results.get('organic', [])
        
        rate_mentions = []
        for result in organic_results[:3]:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Look for rate mentions in title and snippet
            rate_patterns = [
                r'₹\s*([0-9,]+)',
                r'\$\s*([0-9,]+)',
                r'([0-9,]+)\s*(?:rupees|inr|rs)',
                r'([0-9]+)k?\s*(?:per post|per content)'
            ]
            
            for pattern in rate_patterns:
                matches = re.findall(pattern, f"{title} {snippet}", re.IGNORECASE)
                for match in matches:
                    try:
                        amount = float(match.replace(',', '').replace('k', '000'))
                        if 1000 <= amount <= 500000:  # Reasonable range
                            rate_mentions.append(amount)
                    except:
                        continue
        
        if rate_mentions:
            avg_rate = sum(rate_mentions) / len(rate_mentions)
            min_rate = min(rate_mentions)
            max_rate = max(rate_mentions)
            insights.append(f"• Market rates found: ₹{min_rate:,.0f} - ₹{max_rate:,.0f} (avg: ₹{avg_rate:,.0f})")
        
        # Add follower category insights
        follower_category = self._get_follower_range(followers)
        category_insights = {
            "micro": "Micro-influencers typically charge ₹2,000-15,000 per post",
            "mid-tier": "Mid-tier influencers typically charge ₹10,000-50,000 per post", 
            "macro": "Macro influencers typically charge ₹30,000-150,000 per post",
            "mega": "Mega influencers typically charge ₹100,000+ per post"
        }
        
        insights.append(f"• {category_insights.get(follower_category, 'Standard rates apply')}")
        
        # Add trending insights from search results
        if organic_results:
            insights.append(f"• Current market research shows active pricing discussions")
            insights.append(f"• {len(organic_results)} relevant sources found for rate benchmarking")
        
        return "\n".join(insights) if insights else "Limited market data available"
    
    def _get_fallback_market_data(self, followers: int, location: str, platforms: List[str]) -> str:
        """Fallback market data when API is unavailable"""
        follower_category = self._get_follower_range(followers)
        
        # Conservative industry averages for India (2024-2025)
        fallback_rates = {
            "micro": {"min": 3000, "max": 12000},
            "mid-tier": {"min": 12000, "max": 45000},
            "macro": {"min": 35000, "max": 120000},
            "mega": {"min": 80000, "max": 300000}
        }
        
        rate_range = fallback_rates.get(follower_category, {"min": 5000, "max": 25000})
        
        return f"""• Industry averages ({follower_category}): ₹{rate_range['min']:,} - ₹{rate_range['max']:,} per post
• Platform: {', '.join(platforms)} in {location}
• Note: Using industry benchmarks (API unavailable)"""
    
    def _calculate_rate_from_research(self, market_data: str, followers: int, engagement_rate: float, deliverables: dict) -> float:
        """Calculate estimated rate based on research data"""
        # Extract rate mentions from market data
        rate_pattern = r'₹([0-9,]+)'
        rates = []
        
        for match in re.finditer(rate_pattern, market_data):
            try:
                rate = float(match.group(1).replace(',', ''))
                rates.append(rate)
            except:
                continue
        
        if rates:
            base_rate = sum(rates) / len(rates)
        else:
            # Fallback calculation based on followers
            follower_category = self._get_follower_range(followers)
            base_rates = {
                "micro": 7500,
                "mid-tier": 28500,
                "macro": 77500,
                "mega": 190000
            }
            base_rate = base_rates.get(follower_category, 15000)
        
        # Adjust for engagement rate
        engagement_multiplier = max(0.7, min(1.5, engagement_rate / 3.5))
        
        # Adjust for deliverables
        total_deliverables = sum(deliverables.values()) if deliverables else 1
        
        # Stories and reels typically cost less per unit than posts
        deliverable_multiplier = 1.0
        if deliverables:
            posts = deliverables.get('posts', 0)
            stories = deliverables.get('stories', 0)
            reels = deliverables.get('reels', 0)
            
            # Weighted pricing: Posts = 1.0, Reels = 1.2, Stories = 0.4
            weighted_deliverables = (posts * 1.0) + (reels * 1.2) + (stories * 0.4)
            deliverable_multiplier = weighted_deliverables
        
        estimated_rate = base_rate * engagement_multiplier * deliverable_multiplier
        
        return max(2000, estimated_rate)  # Minimum rate floor

class SupabaseManager:
    """Manage Supabase operations for negotiation data"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not found. Running without database.")
            self.client = None
        else:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def save_negotiation_state(self, state: NegotiationState) -> bool:
        """Save negotiation state to Supabase using upsert (insert or update)"""
        if not self.client:
            logger.info("No Supabase client, skipping database save")
            return False
            
        try:
            data = {
                "session_id": state.session_id,
                "brand_details": asdict(state.brand_details),
                "influencer_profile": asdict(state.influencer_profile),
                "current_offer": state.current_offer,
                "max_budget": state.max_budget,
                "deliverables_agreed": state.deliverables_agreed,
                "messages": state.messages,
                "status": state.status,
                "created_at": state.created_at.isoformat()
            }
            
            # Use upsert to insert or update based on session_id
            result = self.client.table("negotiations").upsert(
                data, 
                on_conflict="session_id"
            ).execute()
            logger.info(f"Saved negotiation state for session {state.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to Supabase: {e}")
            return False
    
    def get_negotiation_state(self, session_id: str) -> Optional[Dict]:
        """Retrieve negotiation state from Supabase"""
        if not self.client:
            return None
            
        try:
            result = self.client.table("negotiations").select("*").eq("session_id", session_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error retrieving from Supabase: {e}")
            return None
    
    def save_contract(self, session_id: str, contract_data: Dict[str, Any], pdf_file_path: str = None) -> bool:
        """Save contract data to Supabase contracts table"""
        if not self.client:
            logger.info("No Supabase client, skipping contract save")
            return False
            
        try:
            # Generate unique contract number
            contract_number = f"CNT-{datetime.now().strftime('%Y%m%d')}-{session_id[:8].upper()}"
            
            # Get file size if PDF path provided
            pdf_file_size = None
            if pdf_file_path and os.path.exists(pdf_file_path):
                pdf_file_size = os.path.getsize(pdf_file_path)
            
            # Prepare contract data
            data = {
                "session_id": session_id,
                "contract_number": contract_number,
                "brand_name": contract_data.get("brand_name"),
                "influencer_name": contract_data.get("influencer_name"),
                "agreed_amount": float(contract_data.get("agreed_amount", 0)),
                "agreed_deliverables": contract_data.get("agreed_deliverables", {}),
                "campaign_duration_days": int(contract_data.get("campaign_duration_days", 0)),
                "platforms": contract_data.get("platforms", []),
                "contract_terms": contract_data.get("contract_terms", ""),
                "pdf_file_path": pdf_file_path,
                "pdf_file_size": pdf_file_size,
                "pdf_storage_bucket": "contracts",
                "contract_status": "generated",
                "start_date": contract_data.get("start_date"),
                "end_date": contract_data.get("end_date"),
                "metadata": contract_data.get("metadata", {})
            }
            
            # Insert contract data
            result = self.client.table("contracts").insert(data).execute()
            logger.info(f"Saved contract for session {session_id} with contract number {contract_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving contract to Supabase: {e}")
            return False
    
    def get_contract_by_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve contract data by session ID"""
        if not self.client:
            return None
            
        try:
            result = self.client.table("contracts").select("*").eq("session_id", session_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error retrieving contract from Supabase: {e}")
            return None
    
    def update_contract_status(self, session_id: str, status: str) -> bool:
        """Update contract status"""
        if not self.client:
            return False
            
        try:
            result = self.client.table("contracts").update(
                {"contract_status": status}
            ).eq("session_id", session_id).execute()
            logger.info(f"Updated contract status to {status} for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating contract status: {e}")
            return False
    
    def upload_contract_pdf(self, file_path: str, session_id: str) -> Optional[str]:
        """Upload contract PDF to Supabase storage"""
        if not self.client:
            logger.info("No Supabase client, skipping PDF upload")
            return None
            
        try:
            # Generate file name
            file_name = f"contract_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Read the PDF file
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            # Upload to Supabase storage
            result = self.client.storage.from_("contracts").upload(
                path=file_name,
                file=file_data,
                file_options={"content-type": "application/pdf"}
            )
            
            if result:
                # Get public URL
                public_url = self.client.storage.from_("contracts").get_public_url(file_name)
                logger.info(f"Uploaded PDF for session {session_id} to {public_url}")
                return public_url
            else:
                logger.error(f"Failed to upload PDF for session {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading PDF to Supabase storage: {e}")
            return None

class MarketResearchTool:
    """Tool for researching market rates using real-time data"""
    
    def __init__(self):
        self.name = "market_research"
        self.description = "Research current market rates for influencer collaborations. Input should be a JSON string containing influencer data and deliverables."
        self.realtime_tool = RealTimeMarketResearchTool()
    
    def run(self, query: str) -> str:
        """Run market research using real-time data"""
        return self.realtime_tool.run(query)

class BudgetAnalysisTool:
    """Tool for analyzing budget constraints"""
    
    def __init__(self):
        self.name = "budget_analysis"
        self.description = "Analyze budget constraints and calculate negotiation limits. Input should be a JSON string with budget and market_rate."
    
    def run(self, query: str) -> str:
        """Analyze budget vs market rate"""
        try:
            data = json.loads(query)
            budget_amount = float(data.get("budget", 0))
            market_amount = float(data.get("market_rate", 0))
            
            max_offer = budget_amount * 1.15  # 15% buffer
            
            if budget_amount < market_amount:
                return f"Budget (₹{budget_amount:,.0f}) is below market rate (₹{market_amount:,.0f}). Max offer: ₹{max_offer:,.0f}"
            else:
                return f"Budget (₹{budget_amount:,.0f}) is above market rate (₹{market_amount:,.0f}). Negotiation advantage."
        except Exception as e:
            return f"Error in budget analysis: {e}"

class NegotiationAgent:
    """Main negotiation agent class"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        
        # Tools for direct use
        self.market_research_tool = MarketResearchTool()
        self.budget_analysis_tool = BudgetAnalysisTool()
        
        # Initialize other components
        self.supabase_manager = SupabaseManager()
        self.current_state: Optional[NegotiationState] = None
    
    def start_negotiation(self, brand_details: Dict, influencer_profile: Dict) -> str:
        """Start a new negotiation session"""        
        session_id = str(uuid.uuid4())
        brand = BrandDetails(**brand_details)
        influencer = InfluencerProfile(**influencer_profile)
        
        # Research market rate using real-time data
        market_research_tool = RealTimeMarketResearchTool()
        research_query = json.dumps({
            "influencer": {
                "followers": influencer.followers,
                "engagement_rate": influencer.engagement_rate,
                "location": influencer.location,
                "platforms": influencer.platforms,
                "niches": influencer.niches
            },
            "deliverables": brand.content_requirements
        })
        
        market_research_result = market_research_tool.run(research_query)
        
        # Extract estimated rate from research (fallback to conservative estimate)
        rate_pattern = r'Estimated Rate: ₹([0-9,]+)'
        market_rate_match = re.search(rate_pattern, market_research_result)
        market_rate = float(market_rate_match.group(1).replace(',', '')) if market_rate_match else 25000
        
        logger.info(f"Market research completed. Estimated rate: ₹{market_rate:,.0f}")
        
        # Initialize negotiation state
        self.current_state = NegotiationState(
            session_id=session_id,
            brand_details=brand,
            influencer_profile=influencer,
            current_offer=0.0,
            max_budget=brand.budget * 1.15,  # 15% buffer
            deliverables_agreed={},
            messages=[],
            status="active",
            created_at=datetime.now()
        )
        
        # Create negotiation prompt
        system_prompt = self._create_negotiation_prompt(brand, influencer, market_rate)
        
        # Start conversation
        opening_message = f"""
        Hello {influencer.name}! I hope you're doing well. 
        
        I'm reaching out on behalf of {brand.name}, and we're really impressed with your content and engagement in the {', '.join(influencer.niches)} space. 
        
        We have an exciting {brand.campaign_duration_days}-day campaign opportunity that aligns perfectly with your audience and content style. The campaign focuses on {', '.join(brand.goals)} and we believe your authentic voice would be perfect for this collaboration.
        
        We're looking for content across {', '.join(brand.target_platforms)} - specifically {self._format_deliverables(brand.content_requirements)}. 
        
        What are your thoughts on this collaboration? I'd love to hear your initial feedback and discuss how we can make this work for both of us.
        """
        
        self.current_state.messages.append({
            "speaker": "agent",
            "message": opening_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save to database
        self.supabase_manager.save_negotiation_state(self.current_state)
        
        return opening_message.strip()
    
    def respond_to_influencer(self, influencer_message: str) -> str:
        """Generate response to influencer's message"""
        if not self.current_state:
            return "Please start a negotiation session first."
        
        # Check if negotiation has already ended
        if self._should_stop_negotiation():
            return f"This negotiation session has already {self.current_state.status}. Thank you for your time!"
        
        # Add influencer message to state
        self.current_state.messages.append({
            "speaker": "influencer",
            "message": influencer_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Extract any budget mentioned by influencer
        influencer_offer = self._extract_budget_from_message(influencer_message)
        if influencer_offer:
            logger.info(f"Influencer mentioned ₹{influencer_offer:,.0f}")
        
        # Detect early agreement/rejection status before generating response
        preliminary_status = self._detect_agreement_status("", influencer_message)
        
        # Handle immediate rejection
        if preliminary_status == 'failed':
            self.current_state.status = 'failed'
            response = self._generate_closing_response('rejection')
        
        # Handle immediate acceptance 
        elif preliminary_status == 'completed':
            self.current_state.status = 'completed'
            
            # Calculate the total agreed amount from conversation
            total_agreed = self._calculate_total_agreed_amount()
            if total_agreed > 0:
                self.current_state.current_offer = total_agreed
            elif influencer_offer:
                self.current_state.current_offer = influencer_offer
            
            # Extract agreed deliverables from recent conversation
            agreed_deliverables = self._extract_agreed_deliverables()
            if agreed_deliverables:
                self.current_state.deliverables_agreed = agreed_deliverables
                logger.info(f"Agreed deliverables: {agreed_deliverables}")
            
            response = self._generate_closing_response('acceptance')
        
        # Continue negotiation
        else:
            # Create context for the agent
            context = self._create_response_context(influencer_message)
            
            # Generate response using direct LLM call
            try:
                response = self.llm.invoke(context).content
                    
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                response = "I apologize for the technical difficulty. Let me address your message directly based on our conversation context."
                # Fall back to simpler prompt
                try:
                    fallback_prompt = f"""
                    You are a brand deal negotiator. Respond conversationally to this influencer message:
                    "{influencer_message}"
                    
                    Context: Negotiating for {self.current_state.brand_details.name} with budget limit of ₹{self.current_state.max_budget:,.0f}.
                    Current negotiating position: ₹{self.current_state.current_offer:,.0f}
                    
                    Keep it brief, professional, and within budget constraints.
                    """
                    response = self.llm.invoke(fallback_prompt).content
                except Exception as e2:
                    logger.error(f"Fallback LLM also failed: {e2}")
                    response = self._generate_fallback_response(influencer_message)
            
            # Update current offer based on what the agent proposed
            agent_offer = self._extract_budget_from_message(response)
            if agent_offer and agent_offer <= self.current_state.max_budget:
                self.current_state.current_offer = agent_offer
                logger.info(f"Agent offered ₹{agent_offer:,.0f}")
            elif influencer_offer and influencer_offer <= self.current_state.max_budget:
                # If influencer made a reasonable offer, track it as current position
                self.current_state.current_offer = influencer_offer
                logger.info(f"Tracking influencer offer: ₹{influencer_offer:,.0f}")
            
            # Detect final agreement status after response
            final_status = self._detect_agreement_status(response, influencer_message)
            if final_status != 'active':
                self.current_state.status = final_status
                
                # Add a closing message if agreement reached
                if final_status == 'completed':
                    response += f"\n\n🎉 Excellent! I believe we have a deal at ₹{self.current_state.current_offer:,.0f}. Let me get our contracts team involved to finalize everything!"
                elif final_status == 'failed':
                    response += f"\n\nI understand this opportunity isn't the right fit. Thank you for your time and consideration."
        
        # Add agent response to state
        self.current_state.messages.append({
            "speaker": "agent",
            "message": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Log final status if negotiation ended
        if self.current_state.status in ['completed', 'failed']:
            logger.info(f"Negotiation {self.current_state.status}! Final offer: ₹{self.current_state.current_offer:,.0f}")
        
        # Save updated state
        self.supabase_manager.save_negotiation_state(self.current_state)
        
        return response
    
    def _create_negotiation_prompt(self, brand: BrandDetails, influencer: InfluencerProfile, market_rate: float) -> str:
        """Create the system prompt for negotiation"""
        return f"""
        You are an expert brand deal negotiator representing {brand.name}. Your goal is to secure a collaboration with {influencer.name} within budget constraints.

        CRITICAL RULES:
        1. NEVER reveal the exact budget (₹{brand.budget:,.0f}) to the influencer
        2. Maximum you can offer is ₹{brand.budget * 1.15:,.0f} (15% buffer)
        3. Market rate for this influencer is approximately ₹{market_rate:,.0f}
        4. Prioritize staying within budget over market rates
        5. Be conversational, friendly, and professional
        6. Focus on value proposition, not just price

        BRAND DETAILS:
        - Company: {brand.name}
        - Campaign Duration: {brand.campaign_duration_days} days
        - Goals: {', '.join(brand.goals)}
        - Platforms: {', '.join(brand.target_platforms)}
        - Required Content: {brand.content_requirements}
        - Target Audience: {brand.target_audience}
        - Brand Guidelines: {brand.brand_guidelines}

        INFLUENCER PROFILE:
        - Name: {influencer.name}
        - Followers: {influencer.followers:,}
        - Engagement Rate: {influencer.engagement_rate}%
        - Location: {influencer.location}
        - Niches: {', '.join(influencer.niches)}
        - Experience: {influencer.previous_brand_collaborations} previous collaborations

        NEGOTIATION STRATEGY:
        1. Start by emphasizing brand alignment and mutual value
        2. When discussing rates, focus on the complete package value
        3. If asked for budget, deflect by asking for their rates first
        4. Negotiate deliverables if needed to fit budget
        5. Highlight long-term partnership potential
        6. Use data about their engagement and audience fit

        Be human-like, dynamic, and adapt your responses based on what the influencer says. Show genuine interest in their work and find creative ways to make the deal work within budget.
        """
    
    def _create_response_context(self, influencer_message: str) -> str:
        """Create context for agent response"""
        recent_messages = self.current_state.messages[-8:]  # Last 8 messages for better context
        conversation_history = "\n".join([
            f"{msg['speaker'].title()}: {msg['message'][:200]}{'...' if len(msg['message']) > 200 else ''}" 
            for msg in recent_messages
        ])
        
        # Extract any mentioned budget from influencer's message
        mentioned_budget = self._extract_budget_from_message(influencer_message)
        budget_analysis = ""
        budget_warning = ""
        
        if mentioned_budget:
            if mentioned_budget > self.current_state.max_budget:
                excess = mentioned_budget - self.current_state.max_budget
                budget_analysis = f"💡 INFLUENCER COUNTER-OFFER: ₹{mentioned_budget:,.0f} - exceeds our limit by ₹{excess:,.0f}. MUST negotiate down or adjust deliverables."
                budget_warning = "⚠️ CRITICAL: Their offer exceeds maximum budget!"
            elif mentioned_budget <= self.current_state.brand_details.budget:
                budget_analysis = f"💚 INFLUENCER OFFER: ₹{mentioned_budget:,.0f} - within allocated budget! This is acceptable - show enthusiasm."
            else:
                budget_analysis = f"💛 INFLUENCER OFFER: ₹{mentioned_budget:,.0f} - within max limit but uses buffer budget."
        
        # Current negotiation status
        if self.current_state.current_offer > 0:
            if self.current_state.current_offer > self.current_state.max_budget:
                budget_warning = "⚠️ CRITICAL: Current negotiating position exceeds maximum budget!"
            elif self.current_state.current_offer > self.current_state.brand_details.budget:
                remaining = self.current_state.max_budget - self.current_state.current_offer
                budget_warning = f"⚠️ WARNING: Using buffer budget. Only ₹{remaining:,.0f} remaining."
        
        # Get current deliverables from conversation (what's been discussed/agreed)
        current_deliverables = self._extract_agreed_deliverables()
        if not current_deliverables:
            # Fall back to original brand requirements if no deliverables mentioned yet
            current_deliverables = self.current_state.brand_details.content_requirements
        
        # Check if influencer mentioned different deliverables in their latest message
        influencer_mentioned_deliverables = self._extract_deliverables_from_message(influencer_message)
        deliverables_context = ""
        
        if influencer_mentioned_deliverables:
            # Compare with current/original deliverables
            changes_made = False
            for content_type, count in influencer_mentioned_deliverables.items():
                original_count = current_deliverables.get(content_type, 0)
                if count != original_count:
                    changes_made = True
                    break
            
            if changes_made:
                deliverables_context = f"""
        
        🔄 DELIVERABLES UPDATE: Influencer proposed different deliverables:
        - Their proposal: {self._format_deliverables(influencer_mentioned_deliverables)}
        - Previous terms: {self._format_deliverables(current_deliverables)}
        
        IMPORTANT: Update your understanding and respond to THEIR proposed deliverables, not the original ones!
        """
                # Update current deliverables to what influencer mentioned
                current_deliverables = influencer_mentioned_deliverables
        
        return f"""
        RESPOND AS A PROFESSIONAL BRAND NEGOTIATOR. Be conversational, strategic, and specific.
        
        CURRENT NEGOTIATION STATUS:
        Brand: {self.current_state.brand_details.name}
        Campaign: {self.current_state.brand_details.campaign_duration_days} days on {', '.join(self.current_state.brand_details.target_platforms)}
        Current Deliverables in Discussion: {self._format_deliverables(current_deliverables)}{deliverables_context}
        
        BUDGET CONSTRAINTS (CONFIDENTIAL - NEVER REVEAL):
        - Allocated Budget: ₹{self.current_state.brand_details.budget:,.0f} 
        - Maximum Limit: ₹{self.current_state.max_budget:,.0f} (includes 15% buffer)
        - Current Negotiating Position: ₹{self.current_state.current_offer:,.0f}
        
        {budget_warning}
        {budget_analysis}
        
        RECENT CONVERSATION:
        {conversation_history}
        
        INFLUENCER'S LATEST MESSAGE: "{influencer_message}"
        
        NEGOTIATION INSTRUCTIONS:
        1. Address their message directly and personally
        2. Stay within budget constraints (absolute max: ₹{self.current_state.max_budget:,.0f})
        3. NEVER reveal actual budget numbers or limits
        4. If they quoted a price above your limit: suggest reducing deliverables or alternative solutions
        5. If they quoted an acceptable price: show enthusiasm and move toward finalizing
        6. If they're being vague: ask for specific rates and deliverables
        7. Focus on mutual value, partnership benefits, and long-term relationship
        8. Be warm, professional, and solution-oriented
        9. Keep response concise and actionable (2-3 paragraphs max)
        10. Make specific counter-proposals when needed
        11. If deliverables seem too high for budget: Research current market rates using tools
        12. Use market research to justify counter-offers and negotiate deliverable adjustments
        
        STRATEGIC MARKET RESEARCH USAGE:
        - Market research is conducted automatically at negotiation start
        - Use market data to justify offers and negotiate deliverable adjustments
        - Present market data professionally to support your position
        - Focus on value proposition and deliverable optimization within budget
        
        Generate a strategic response that moves this negotiation toward a successful conclusion within budget.
        """
    
    def _format_deliverables(self, content_requirements: Dict[str, int]) -> str:
        """Format deliverables for display"""
        deliverables = []
        for content_type, count in content_requirements.items():
            deliverables.append(f"{count} {content_type}")
        return ", ".join(deliverables)
    
    def get_negotiation_summary(self) -> Dict[str, Any]:
        """Get current negotiation summary"""
        if not self.current_state:
            return {}
        
        budget_utilization = 0
        if self.current_state.current_offer > 0:
            budget_utilization = (self.current_state.current_offer / self.current_state.brand_details.budget) * 100
        
        return {
            "session_id": self.current_state.session_id,
            "brand": self.current_state.brand_details.name,
            "influencer": self.current_state.influencer_profile.name,
            "status": self.current_state.status,
            "current_offer": self.current_state.current_offer,
            "max_budget": self.current_state.max_budget,
            "allocated_budget": self.current_state.brand_details.budget,
            "budget_utilization": f"{budget_utilization:.1f}%",
            "within_budget": self.current_state.current_offer <= self.current_state.max_budget,
            "message_count": len(self.current_state.messages),
            "created_at": self.current_state.created_at.isoformat()
        }
    
    def is_within_budget(self, amount: float) -> bool:
        """Check if an amount is within the negotiable budget (15% buffer)"""
        return amount <= self.current_state.max_budget if self.current_state else False
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get detailed budget status information"""
        if not self.current_state:
            return {}
        
        return {
            "allocated_budget": self.current_state.brand_details.budget,
            "max_negotiable": self.current_state.max_budget,
            "current_offer": self.current_state.current_offer,
            "remaining_buffer": self.current_state.max_budget - self.current_state.current_offer,
            "buffer_percentage": 15.0,
            "budget_utilization_percentage": (self.current_state.current_offer / self.current_state.brand_details.budget) * 100 if self.current_state.current_offer > 0 else 0
        }
    
    def _extract_budget_from_message(self, message: str) -> Optional[float]:
        """Extract budget/price mentions from a message"""        
        # Patterns to match Indian currency formats
        patterns = [
            r'₹\s*([0-9,]+)',  # ₹50,000 or ₹ 50,000
            r'([0-9,]+)\s*(?:rupees?|inr|rs\.?)',  # 50,000 rupees/INR/Rs
            r'(?:budget|offer|price|rate|cost|fee|charge)\s*(?:is|of|:)?\s*₹?\s*([0-9,]+)',
            r'([0-9,]+)\s*(?:thousand|k|lakh|lac)',  # 50k, 5 lakh
        ]
        
        message_lower = message.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean and convert the number
                    clean_number = match.replace(',', '').strip()
                    
                    # Handle thousand/lakh multipliers
                    if 'thousand' in message_lower or 'k' in message_lower:
                        if len(clean_number) <= 3:  # Like "50k"
                            return float(clean_number) * 1000
                    elif 'lakh' in message_lower or 'lac' in message_lower:
                        return float(clean_number) * 100000
                    
                    amount = float(clean_number)
                    # Only consider reasonable amounts (1K to 10M INR)
                    if 1000 <= amount <= 10000000:
                        return amount
                        
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _detect_agreement_status(self, agent_message: str, influencer_message: str) -> str:
        """Detect if negotiation has reached an agreement"""
        
        # Check recent messages for agreement patterns
        recent_agent = agent_message.lower()
        recent_influencer = influencer_message.lower()
        
        # Use AI to detect agreement intent with better contract language recognition
        agreement_context = f"""
        Influencer's response: "{influencer_message}"
        
        MARK AS AGREE if the influencer wants to finalize the deal or create a contract with phrases like:
        - "I agree to the deal" / "I accept your offer"
        - "Let's close this" / "Deal, let's do it"
        - "Perfect, I'm ready to sign"
        - "Let's create contract" / "Let's make a contract"
        - "Yes, let's proceed" / "Let's finalize this"
        - "Sounds good, let's move forward"
        - "Agreed" / "Deal" / "Done"
        
        MARK AS REJECT if they CLEARLY want to END negotiations completely:
        - "I have to pass on this opportunity"
        - "This won't work for me, thanks anyway"
        - "I'm not interested in this collaboration"
        - "I can't do this deal"
        
        MARK AS CONTINUE for ongoing negotiation (discussing terms, prices, deliverables, concerns, questions).
        
        Answer with just: AGREE, REJECT, or CONTINUE
        """
        
        try:
            intent_result = self.llm.invoke(agreement_context).content.strip().upper()
            if intent_result == 'AGREE':
                logger.info(f"AI detected agreement intent in: '{influencer_message}'")
                return 'completed'
            elif intent_result == 'REJECT':
                logger.info(f"AI detected rejection intent in: '{influencer_message}'")
                return 'failed'
        except Exception as e:
            logger.error(f"Error in AI agreement detection: {e}")
            # Fall back to basic sentiment analysis with contract keywords
            clear_agreement = [
                'i agree to', 'i accept', 'let\'s close', 'deal!', 'let\'s finalize', 
                'i\'m ready to sign', 'let\'s create contract', 'let\'s make a contract',
                'ya let\'s create', 'create contract', 'make contract', 'finalize this'
            ]
            clear_rejection = ['i have to pass', 'not interested', 'can\'t do this', 'won\'t work for me', 'i decline']
            
            if any(phrase in recent_influencer for phrase in clear_agreement):
                logger.info(f"Fallback detection: Agreement detected in '{influencer_message}'")
                return 'completed'
            elif any(phrase in recent_influencer for phrase in clear_rejection):
                return 'failed'
        
        # Check for price + positive sentiment combination
        influencer_budget = self._extract_budget_from_message(recent_influencer)
        if influencer_budget and influencer_budget <= self.current_state.max_budget:
            # If they mention a reasonable price, look for any positive sentiment
            positive_words = ['deal', 'accept', 'agreed', 'perfect', 'good', 'works', 'fine']
            if any(word in recent_influencer for word in positive_words):
                logger.info(f"Detected price + positive sentiment: ₹{influencer_budget:,.0f}")
                return 'completed'
        
        # Only detect VERY clear rejection statements - avoid false positives
        clear_rejection_phrases = [
            'i have to pass on', 'not interested in this', 'can\'t do this deal', 
            'this won\'t work for me', 'i\'m going to decline', 'not feasible for me'
        ]
        if any(phrase in recent_influencer for phrase in clear_rejection_phrases):
            logger.info(f"Detected clear rejection in: '{recent_influencer}'")
            return 'failed'
        
        # Check for mutual budget understanding
        agent_budget = self._extract_budget_from_message(recent_agent)
        if influencer_budget and agent_budget and abs(influencer_budget - agent_budget) < 5000:
            # If budgets are close and there's any confirmation language
            confirmation_words = ['deal', 'agreed', 'perfect', 'confirmed', 'good']
            if any(word in recent_influencer for word in confirmation_words):
                logger.info(f"Detected mutual budget understanding: ₹{influencer_budget:,.0f} ≈ ₹{agent_budget:,.0f}")
                return 'completed'
        
        # Check for inflexible counter-offers that exceed our budget significantly
        if influencer_budget and influencer_budget > self.current_state.max_budget:
            excess_percentage = (influencer_budget - self.current_state.max_budget) / self.current_state.max_budget
            if excess_percentage > 0.4:  # 40% more than our max budget
                # Check if they seem inflexible
                inflexible_words = ['minimum', 'non-negotiable', 'final offer', 'won\'t go lower', 'lowest i can do', 'that\'s my rate']
                if any(word in recent_influencer for word in inflexible_words):
                    logger.info(f"Detected inflexible counter-offer: ₹{influencer_budget:,.0f} (40%+ over budget)")
                    return 'failed'
        
        # Default to active negotiation - be more conservative about ending
        return 'active'
    
    def _extract_deliverables_from_message(self, message: str) -> Dict[str, int]:
        """Extract deliverables mentioned in a message"""
        deliverables = {}
        message_lower = message.lower()
        
        # Look for specific deliverable patterns
        patterns = {
            'posts': r'(\d+)\s*(?:instagram\s+)?posts?',
            'stories': r'(\d+)\s*(?:instagram\s+)?stor(?:y|ies)',
            'reels': r'(\d+)\s*(?:instagram\s+)?reels?',
            'videos': r'(\d+)\s*videos?',
            'linkedin_posts': r'(\d+)\s*linkedin\s*posts?'
        }
        
        for deliverable_type, pattern in patterns.items():
            matches = re.findall(pattern, message_lower)
            if matches:
                try:
                    # Take the last mentioned number for each type
                    deliverables[deliverable_type] = int(matches[-1])
                except (ValueError, IndexError):
                    continue
        
        return deliverables
    
    def _extract_agreed_deliverables(self) -> Dict[str, int]:
        """Extract agreed deliverables from recent conversation history"""
        if not self.current_state or len(self.current_state.messages) < 2:
            return {}
        
        # Look at last 8 messages for deliverable mentions (more comprehensive)
        recent_messages = self.current_state.messages[-8:]
        all_deliverables = {}
        
        # First, get deliverables from agent's most recent offer
        for message in reversed(recent_messages):  # Start from most recent
            if message.get('speaker') == 'agent':
                content = message.get('message', '')
                deliverables = self._extract_deliverables_from_message(content)
                if deliverables:
                    all_deliverables.update(deliverables)
                    logger.info(f"Found deliverables in agent message: {deliverables}")
                    break  # Use the most recent agent offer
        
        # Then, check influencer messages for any modifications or confirmations
        for message in recent_messages:
            if message.get('speaker') == 'influencer':
                content = message.get('message', '')
                deliverables = self._extract_deliverables_from_message(content)
                if deliverables:
                    # Influencer deliverables override agent deliverables for same type
                    all_deliverables.update(deliverables)
                    logger.info(f"Found deliverables in influencer message: {deliverables}")
        
        # If we still don't have deliverables, fall back to original brand requirements
        if not all_deliverables:
            all_deliverables = self.current_state.brand_details.content_requirements.copy()
            logger.info(f"Using original brand requirements: {all_deliverables}")
        
        return all_deliverables
    
    def _update_current_offer(self, message: str):
        """Update the current offer based on the agent's message"""
        if not self.current_state:
            return
            
        # Extract any budget mention from agent's message
        offer = self._extract_budget_from_message(message)
        if offer and offer <= self.current_state.max_budget:
            self.current_state.current_offer = offer
            logger.info(f"Updated current offer to ₹{offer:,.0f}")
    
    def _should_stop_negotiation(self) -> bool:
        """Check if negotiation should stop"""
        if not self.current_state or len(self.current_state.messages) < 4:
            return False
            
        return self.current_state.status in ['completed', 'failed']
    
    def _generate_closing_response(self, closure_type: str) -> str:
        """Generate appropriate closing response based on negotiation outcome"""
        brand_name = self.current_state.brand_details.name
        influencer_name = self.current_state.influencer_profile.name
        
        if closure_type == 'acceptance':
            # Use agreed deliverables if available, otherwise fall back to original requirements
            deliverables_to_show = (self.current_state.deliverables_agreed 
                                  if self.current_state.deliverables_agreed 
                                  else self.current_state.brand_details.content_requirements)
            
            # Generate and save contract with PDF to Supabase
            contract_saved = self._save_contract_to_database()
            contract_status = "✅ Contract generated and saved successfully!" if contract_saved else "⚠️ Contract generated (database save pending)"
            
            return f"""
            Fantastic! I'm thrilled that we've reached an agreement, {influencer_name}! 
            
            🎉 **DEAL CONFIRMED**
            To summarize our finalized partnership:
            • Campaign Budget: ₹{self.current_state.current_offer:,.0f}
            • Duration: {self.current_state.brand_details.campaign_duration_days} days
            • Deliverables: {self._format_deliverables(deliverables_to_show)}
            • Platforms: {', '.join(self.current_state.brand_details.target_platforms)}
            
            📄 **CONTRACT GENERATED**
            I've generated a formal contract for this partnership. Here's a preview:
            
            {self._generate_contract()}
            
            {contract_status}
            
            Our contracts team will reach out within 24 hours to finalize the paperwork and arrange payment terms. Thank you for this wonderful partnership with {brand_name}!
            
            Looking forward to seeing the amazing content you'll create! 🎉
            
            Thank you for this wonderful partnership with {brand_name}! Looking forward to seeing the amazing content you'll create! 🎉
            """.strip()
            
        elif closure_type == 'rejection':
            return f"""
            Thank you for your honest feedback, {influencer_name}. While we're disappointed that we couldn't align on the terms for this particular campaign, I completely understand your position.
            
            We truly appreciate the time you've taken to discuss this opportunity with {brand_name}. Your professionalism throughout this conversation has been excellent.
            
            Please keep us in mind for future campaigns - we'd love to explore collaboration opportunities that might be a better fit down the line.
            
            Wishing you all the best with your content and partnerships! 🙏
            """.strip()
        
        return "Thank you for your time in this negotiation."
    
    def _generate_fallback_response(self, influencer_message: str) -> str:
        """Generate a simple fallback response when AI fails"""
        return f"""
        Thank you for your message. I want to make sure I address your points properly. 
        
        Based on our conversation, we're working on finding the right collaboration terms for {self.current_state.brand_details.name}'s campaign. 
        
        Could you help me understand your main priorities for this partnership? This will help me provide you with the most relevant response.
        """
    
    def _generate_contract(self) -> str:
        """Generate a minimalist contract for the agreed deal"""
        if not self.current_state:
            return "Contract generation error: No active negotiation state"
        
        brand = self.current_state.brand_details
        influencer = self.current_state.influencer_profile
        
        # Use agreed deliverables if available, otherwise fall back to original requirements
        deliverables = (self.current_state.deliverables_agreed 
                       if self.current_state.deliverables_agreed 
                       else self.current_state.brand_details.content_requirements)
        
        # Calculate start and end dates
        start_date = datetime.now() + timedelta(days=7)  # Campaign starts in 7 days
        end_date = start_date + timedelta(days=brand.campaign_duration_days)
        
        contract_text = f"""
INFLUENCER COLLABORATION AGREEMENT

Contract Date: {datetime.now().strftime('%B %d, %Y')}
Contract Number: CNT-{datetime.now().strftime('%Y%m%d')}-{self.current_state.session_id[:8].upper()}

PARTIES:
Brand: {brand.name}
Location: {brand.brand_location}

Influencer: {influencer.name}
Location: {influencer.location}
Followers: {influencer.followers:,}

CAMPAIGN DETAILS:
Campaign Duration: {brand.campaign_duration_days} days
Start Date: {start_date.strftime('%B %d, %Y')}
End Date: {end_date.strftime('%B %d, %Y')}

Platforms: {', '.join(brand.target_platforms)}
Campaign Goals: {', '.join(brand.goals)}

AGREED DELIVERABLES:
{self._format_deliverables_for_contract(deliverables)}

COMPENSATION:
Total Amount: ₹{self.current_state.current_offer:,.2f}
Currency: {brand.budget_currency}
Payment Terms: 50% advance, 50% upon completion

CONTENT GUIDELINES:
- Target Audience: {brand.target_audience}
- Brand Guidelines: {brand.brand_guidelines}
- Content must align with brand values and messaging
- All content subject to brand approval before posting

TERMS & CONDITIONS:
1. Content Creation: Influencer will create and deliver agreed content within specified timeline
2. Usage Rights: Brand receives perpetual license for promotional use of created content
3. Exclusivity: No competing brand partnerships during campaign period
4. Performance: Influencer commits to maintaining standard engagement levels
5. Compliance: All content must comply with platform guidelines and disclosure requirements

This agreement represents the complete understanding between parties.

Brand Representative: _________________    Date: ____________

Influencer: _________________    Date: ____________
"""
        
        return contract_text.strip()
    
    def _format_deliverables_for_contract(self, deliverables: Dict[str, int]) -> str:
        """Format deliverables for contract display"""
        formatted = []
        for content_type, count in deliverables.items():
            formatted.append(f"- {count} {content_type.replace('_', ' ').title()}")
        return "\n".join(formatted)
    
    def _generate_contract_pdf(self, contract_text: str) -> str:
        """Generate a PDF contract and save it locally"""
        if not self.current_state:
            raise ValueError("No active negotiation state")
        
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_short = self.current_state.session_id[:8]
        filename = f"contract_{session_short}_{timestamp}.pdf"
        filepath = os.path.join("contracts", filename)
        
        # Create contracts directory if it doesn't exist
        os.makedirs("contracts", exist_ok=True)
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=letter, topMargin=0.5*inch)
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=20,
                alignment=1,  # Center alignment
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                spaceBefore=15,
                spaceAfter=10,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=8,
                fontName='Helvetica'
            )
            
            # Build document content
            content = []
            
            # Title
            content.append(Paragraph("INFLUENCER COLLABORATION AGREEMENT", title_style))
            content.append(Spacer(1, 0.3*inch))
            
            # Parse and format contract text
            sections = contract_text.split('\n\n')
            
            for section in sections:
                if not section.strip():
                    continue
                    
                lines = section.strip().split('\n')
                section_title = lines[0]
                
                # Format section title
                if section_title.isupper() and len(section_title) > 3:
                    content.append(Paragraph(section_title, heading_style))
                    
                    # Add section content
                    for line in lines[1:]:
                        if line.strip():
                            content.append(Paragraph(line.strip(), normal_style))
                else:
                    # Regular content
                    for line in lines:
                        if line.strip():
                            content.append(Paragraph(line.strip(), normal_style))
                
                content.append(Spacer(1, 0.1*inch))
            
            # Add signature section with more space
            content.append(Spacer(1, 0.5*inch))
            
            # Create signature table
            signature_data = [
                ['Brand Representative: ____________________', 'Date: ________________'],
                ['', ''],
                ['Influencer: ____________________', 'Date: ________________']
            ]
            
            signature_table = Table(signature_data, colWidths=[3*inch, 2*inch])
            signature_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            content.append(signature_table)
            
            # Build PDF
            doc.build(content)
            
            logger.info(f"Contract PDF generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
    
    def _save_contract_to_database(self) -> bool:
        """Save contract data and PDF to Supabase"""
        if not self.current_state:
            return False
        
        try:
            # Generate contract text and PDF
            contract_text = self._generate_contract()
            pdf_path = self._generate_contract_pdf(contract_text)
            
            # Upload PDF to Supabase storage
            pdf_url = self.supabase_manager.upload_contract_pdf(pdf_path, self.current_state.session_id)
            
            # Use agreed deliverables if available
            deliverables = (self.current_state.deliverables_agreed 
                           if self.current_state.deliverables_agreed 
                           else self.current_state.brand_details.content_requirements)
            
            # Calculate dates
            start_date = datetime.now() + timedelta(days=7)
            end_date = start_date + timedelta(days=self.current_state.brand_details.campaign_duration_days)
            
            # Prepare contract data
            contract_data = {
                "brand_name": self.current_state.brand_details.name,
                "influencer_name": self.current_state.influencer_profile.name,
                "agreed_amount": self.current_state.current_offer,
                "agreed_deliverables": deliverables,
                "campaign_duration_days": self.current_state.brand_details.campaign_duration_days,
                "platforms": self.current_state.brand_details.target_platforms,
                "contract_terms": contract_text,
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "metadata": {
                    "negotiation_date": self.current_state.created_at.isoformat(),
                    "session_id": self.current_state.session_id,
                    "pdf_url": pdf_url,
                    "brand_budget_utilization": (self.current_state.current_offer / self.current_state.brand_details.budget) * 100
                }
            }
            
            # Save contract to database
            success = self.supabase_manager.save_contract(
                self.current_state.session_id, 
                contract_data, 
                pdf_path
            )
            
            if success:
                logger.info(f"Contract saved successfully for session {self.current_state.session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving contract: {e}")
            return False
    
    def _calculate_total_agreed_amount(self) -> float:
        """Calculate total agreed amount from recent conversation"""
        if not self.current_state:
            return 0.0
        
        # Look for agent's final offer in recent messages
        recent_messages = self.current_state.messages[-6:]  # Last 6 messages
        
        # Pattern to match total amounts mentioned by agent
        total_patterns = [
            r'total\s+(?:of\s+|to\s+)?₹\s*([0-9,]+)',
            r'bringing\s+the\s+total\s+to\s+₹\s*([0-9,]+)',
            r'campaign\s+budget:\s*₹\s*([0-9,]+)',
            r'₹\s*([0-9,]+)\s+for\s+the\s+(?:fashionforward\s+)?campaign',
            r'total\s+campaign\s+(?:cost|budget):\s*₹\s*([0-9,]+)'
        ]
        
        for message in reversed(recent_messages):  # Start from most recent
            if message.get('speaker') == 'agent':
                content = message.get('message', '').lower()
                
                for pattern in total_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        try:
                            amount = float(matches[-1].replace(',', ''))
                            if 10000 <= amount <= 200000:  # Reasonable range
                                logger.info(f"Found total agreed amount: ₹{amount:,.0f}")
                                return amount
                        except (ValueError, TypeError):
                            continue
        
        # Fallback: calculate from individual components if mentioned
        # Look for breakdown like "₹20,000 for posts/stories + ₹30,000 for reels"
        breakdown_pattern = r'₹\s*([0-9,]+)\s*(?:for|posts|stories|reels)'
        all_amounts = []
        
        for message in reversed(recent_messages):
            if message.get('speaker') == 'agent':
                content = message.get('message', '').lower()
                amounts = re.findall(breakdown_pattern, content, re.IGNORECASE)
                for amount_str in amounts:
                    try:
                        amount = float(amount_str.replace(',', ''))
                        if 5000 <= amount <= 50000:  # Reasonable component range
                            all_amounts.append(amount)
                    except (ValueError, TypeError):
                        continue
        
        if all_amounts:
            total = sum(all_amounts)
            logger.info(f"Calculated total from components {all_amounts}: ₹{total:,.0f}")
            return total
        
        # Last fallback: use current_offer if it seems reasonable
        if self.current_state.current_offer >= 10000:
            return self.current_state.current_offer
        
        return 0.0

def main():
    """Main function to demonstrate the negotiator agent"""
    print("🤝 Influencer Brand Deal Negotiator Agent")
    print("=" * 50)
    
    # Example brand and influencer data
    brand_data = {
        "name": "FashionForward",
        "budget": 50000,
        "budget_currency": "INR",
        "goals": ["brand awareness", "product promotion"],
        "target_platforms": ["instagram", "youtube"],
        "content_requirements": {
            "posts": 3,
            "stories": 5,
            "reels": 2
        },
        "campaign_duration_days": 30,
        "target_audience": "Young adults interested in fashion",
        "brand_guidelines": "Focus on sustainability and style",
        "brand_location": "india"
    }
    
    influencer_data = {
        "name": "StyleInfluencer",
        "followers": 150000,
        "engagement_rate": 4.5,
        "location": "india",
        "platforms": ["instagram", "youtube"],
        "niches": ["fashion", "lifestyle"],
        "previous_brand_collaborations": 25
    }
    
    # Initialize the agent
    agent = NegotiationAgent()
    
    # Start negotiation
    print("\n🚀 Starting negotiation...")
    opening_message = agent.start_negotiation(brand_data, influencer_data)
    print(f"\nAgent: {opening_message}")
    
    # Interactive conversation loop
    print("\n" + "=" * 50)
    print("💬 Interactive Negotiation (type 'quit' to exit)")
    print("💡 Try phrases like 'I accept', 'deal!', 'I have to pass', etc.")
    print("=" * 50)
    
    while True:
        try:
            # Check if negotiation has ended
            if agent.current_state and agent._should_stop_negotiation():
                summary = agent.get_negotiation_summary()
                print(f"\n🏁 Negotiation {summary['status'].upper()}!")
                print(f"Final details: ₹{summary['current_offer']:,.0f} ({summary['budget_utilization']} of budget)")
                break
            
            influencer_input = input(f"\n{influencer_data['name']}: ")
            
            if influencer_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Negotiation ended by user.")
                break
            
            if influencer_input.strip():
                response = agent.respond_to_influencer(influencer_input)
                print(f"\nAgent: {response}")
                
                # Show negotiation summary
                summary = agent.get_negotiation_summary()
                if summary:
                    status_emoji = "✅" if summary['status'] == 'completed' else "❌" if summary['status'] == 'failed' else "🔄"
                    print(f"\n📊 {status_emoji} Status: {summary['status']} | Messages: {summary['message_count']} | Budget used: {summary['budget_utilization']}")
                    
                    # Show if offer was updated
                    if summary['current_offer'] > 0:
                        print(f"💰 Current offer: ₹{summary['current_offer']:,.0f}")
                    
                    # If negotiation completed successfully, show contract information
                    if summary['status'] == 'completed':
                        print("\n🎉 Negotiation completed successfully!")
                        
                        # Check if contract was already saved during negotiation
                        contract = agent.supabase_manager.get_contract_by_session(agent.current_state.session_id)
                        if contract:
                            print(f"\n📄 Contract generated and saved!")
                            print(f"   Contract Number: {contract.get('contract_number', 'N/A')}")
                            print(f"   Amount: ₹{contract.get('agreed_amount', 0):,.2f}")
                            print(f"   Status: {contract.get('contract_status', 'Unknown')}")
                        
                        show_contract = input("\n📄 Would you like to view the full contract? (y/n): ").strip().lower()
                        if show_contract in ['y', 'yes']:
                            print("\n📄 Contract Details:")
                            print("=" * 80)
                            print(agent._generate_contract())
                            print("=" * 80)
        
        except KeyboardInterrupt:
            print("\n\n👋 Negotiation interrupted.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Main loop error: {e}")

if __name__ == "__main__":
    main()
