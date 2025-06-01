from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import logging
import re
import uuid
from app.models.negotiation_models import (
    NegotiationState, BrandDetails, InfluencerProfile, 
    NegotiationOffer, ContentDeliverable, NegotiationStatus,
    PlatformType, ContentType, LocationType
)
from app.services.negotiation_session_service import negotiation_session_service
from enum import Enum

logger = logging.getLogger(__name__)

# Import contract service lazily to avoid circular imports
def get_contract_service():
    try:
        from app.services.contract_service import contract_service
        return contract_service
    except ImportError:
        logger.warning("Contract service not available")
        return None

class ConversationHandlerDB:
    """Database-backed conversation handler for brand-side negotiations."""
    
    def __init__(self):
        """Initialize the conversation handler with database support."""
        # Remove in-memory storage, everything goes to database
        
        # Conversation templates for different stages - Agent represents the Brand
        self.conversation_templates = {
            "greeting": """Hello! I'm representing {brand_name} and I'm excited to discuss a potential collaboration opportunity with you.

We've reviewed your profile and believe you'd be a great fit for our upcoming campaign. Here's what we're looking for:

🎯 **Campaign Goals**: {goals}
💰 **Our Budget**: {budget}
📱 **Target Platforms**: {platforms}
📋 **Content Requirements**: {content_summary}
⏰ **Campaign Duration**: {duration} days

Based on our market research and your profile, we'd like to propose a collaboration that's mutually beneficial. We believe in fair compensation while staying within our allocated budget.

Are you interested in learning more about this opportunity?""",

            "market_analysis": """We've conducted a thorough analysis of current market rates for creators with your profile:

📊 **Your Profile Highlights**:
• Followers: {followers:,}
• Engagement Rate: {engagement_rate:.1%}
• Location: {location}
• Active Platforms: {platforms}

💹 **Our Proposed Rates** (based on market research):
{rate_breakdown}

**Our Total Offer**: {total_value}

This offer reflects our research into fair market pricing while aligning with our campaign budget. We believe this compensation recognizes your value while allowing us to achieve our marketing objectives.

What are your thoughts on this proposal?""",

            "proposal": """Here's our formal collaboration proposal:

📋 **Deliverables & Compensation**:
{deliverables_breakdown}

💰 **Total Compensation**: {total_price}
💳 **Payment Terms**: {payment_terms}
🔄 **Revisions**: {revisions} included per deliverable
📅 **Timeline**: {duration} days
🔒 **Usage Rights**: {usage_rights}

This proposal has been carefully crafted to offer competitive compensation while fitting within {brand_name}'s campaign budget. We're committed to a successful partnership and believe this structure sets us both up for success.

Would you like to move forward with these terms, or are there specific aspects you'd like to discuss?""",

            "counter_offer_response": """Thank you for your counter-proposal. Let me review this with our team's perspective:

**Your Request**: {counter_price}
**Our Budget**: {our_price}
**Gap**: {difference}

{analysis_response}

{compromise_suggestion}

We value working with talented creators like yourself and want to find a solution that works for both parties. Can we explore some options to bridge this gap?""",

            "agreement": """🎉 Excellent! We're thrilled to move forward with this partnership!

**Final Agreement Summary**:
{final_terms}

On behalf of {brand_name}, I'm excited about the content you'll create for our campaign. We believe this collaboration will deliver great results for both of us.

**Next Steps from Our Side**:
1. Our legal team will prepare the contract within 2 business days
2. First payment (50%) will be processed upon contract signing
3. Our marketing team will share the creative brief and brand guidelines
4. We'll establish a streamlined content review process

Welcome to the {brand_name} family! Is there anything else you need from us to get started?""",

            "rejection_response": """I understand and respect your decision. While we're disappointed this particular opportunity isn't the right fit, we appreciate you taking the time to consider our proposal.

{brand_name} values building long-term relationships with quality creators. If your circumstances change or if you'd be interested in exploring different campaign formats in the future, we'd love to reconnect.

Thank you for your professionalism throughout this process. We wish you all the best with your upcoming projects!

Feel free to reach out if you'd like to discuss future collaboration opportunities."""
        }

    async def create_session(
        self, 
        brand_details: BrandDetails, 
        influencer_profile: InfluencerProfile,
        user_id: Optional[str] = None
    ) -> str:
        """Create a new negotiation session in the database."""
        try:
            # Note: NegotiationState doesn't have created_at/updated_at fields
            # These are handled by the database layer
            session = NegotiationState(
                session_id="",  # Will be generated below
                brand_details=brand_details,
                influencer_profile=influencer_profile,
                status=NegotiationStatus.INITIATED,
                negotiation_round=1,  # Start from round 1
                conversation_history=[],
                current_offer=None,
                counter_offers=[],
                agreed_terms=None
            )
            
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Create session in database using the service
            await negotiation_session_service.create_session(
                session_id=session_id,
                brand_details=brand_details,
                influencer_profile=influencer_profile,
                user_id=user_id
            )
            
            logger.info(f"Created new session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    async def generate_greeting_message(self, session_id: str, user_id: Optional[str] = None) -> str:
        """Generate the initial greeting message."""
        session = await negotiation_session_service.get_session(session_id, user_id)
        if not session:
            return "Session not found."
        
        brand = session.brand_details
        influencer = session.influencer_profile
        
        # Format campaign goals
        goals_str = ", ".join(brand.goals) if brand.goals else "Brand awareness and engagement"
        
        # Format budget
        budget_str = f"${brand.budget:,.2f}"
        if hasattr(brand, 'budget_currency') and brand.budget_currency and brand.budget_currency != "USD":
            if hasattr(brand, 'original_budget_amount') and brand.original_budget_amount:
                budget_str = f"{brand.original_budget_amount:,.2f} {brand.budget_currency}"
        
        # Format platforms
        platforms_str = ", ".join([p.value.title() for p in brand.target_platforms])
        
        # Format content requirements
        content_summary = []
        for content_type, quantity in brand.content_requirements.items():
            content_display = content_type.replace('_', ' ').title()
            content_summary.append(f"{quantity} {content_display}{'s' if quantity > 1 else ''}")
        content_str = ", ".join(content_summary)
        
        message = self.conversation_templates["greeting"].format(
            brand_name=brand.name,
            goals=goals_str,
            budget=budget_str,
            platforms=platforms_str,
            content_summary=content_str,
            duration=brand.campaign_duration_days
        )
        
        await self._add_to_conversation(session_id, "assistant", message, user_id)
        return message

    async def generate_market_analysis(self, session_id: str, user_id: Optional[str] = None) -> str:
        """Generate market analysis message using BUDGET-BASED approach."""
        session = await negotiation_session_service.get_session(session_id, user_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # Determine display currency
        display_currency = "USD"
        if hasattr(brand, 'budget_currency') and brand.budget_currency:
            display_currency = brand.budget_currency
        else:
            location_context = self._get_location_context(influencer.location)
            display_currency = location_context["currency"]
        
        # Generate budget-based proposal using brand's exact budget
        budget_usd = brand.budget
        if hasattr(brand, 'budget_currency') and brand.budget_currency and brand.budget_currency != "USD":
            budget_usd = self._convert_to_usd(brand.budget, brand.budget_currency)
        
        budget_proposal = self._generate_budget_constrained_proposal_fixed(
            budget_usd, brand.content_requirements, display_currency
        )
        
        # Create rate breakdown for display
        rate_breakdown_lines = []
        for content_type, details in budget_proposal["breakdown"].items():
            content_display = content_type.replace('_', ' ').title()
            rate_breakdown_lines.append(
                f"• {content_display}: {details['rate_per_piece']} × {details['count']} = {details['total']}"
            )
        
        # Add cultural context based on location
        cultural_note = ""
        if influencer.location == LocationType.INDIA:
            cultural_note = "\n\nWe understand the Indian market dynamics and have structured this offer to be competitive within the local creator economy."
        elif influencer.location == LocationType.US:
            cultural_note = "\n\nThis proposal aligns with current US market standards for creators in your category."
        elif influencer.location == LocationType.BRAZIL:
            cultural_note = "\n\nWe've considered the Brazilian market context in structuring this collaboration opportunity."
        
        # Store the proposal in session for later reference
        session.current_offer = NegotiationOffer(
            total_price=budget_usd,
            currency=display_currency,
            content_breakdown=budget_proposal["breakdown"],
            payment_terms="50% advance, 50% on completion",
            timeline_days=brand.campaign_duration_days,
            usage_rights="6 months social media usage",
            revisions_included=2
        )
        
        # Format total offer in display currency
        total_offer_display = budget_proposal["total_budget"]
        if display_currency != "USD":
            total_offer_local = self._convert_from_usd(budget_usd, display_currency)
            total_offer_display = self._format_currency(total_offer_local, display_currency)
        else:
            total_offer_display = self._format_currency(budget_proposal["total_budget"], "USD")
        
        message = self.conversation_templates["market_analysis"].format(
            followers=influencer.followers,
            engagement_rate=influencer.engagement_rate,
            location=influencer.location.value,
            platforms=", ".join([p.value.title() for p in influencer.platforms]),
            rate_breakdown="\n".join(rate_breakdown_lines),
            total_value=total_offer_display
        ) + cultural_note + f"\n\n{budget_proposal['remaining_budget']} remaining budget"
        
        # Update session in database
        await negotiation_session_service.update_session(session, user_id)
        await self._add_to_conversation(session_id, "assistant", message, user_id)
        return message

    async def generate_proposal(self, session_id: str, user_id: Optional[str] = None) -> str:
        """Generate formal proposal message using budget-based approach with currency support."""
        session = await negotiation_session_service.get_session(session_id, user_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # Use the offer already created in market analysis, or create new one
        if not session.current_offer:
            # Determine display currency
            display_currency = "USD"
            if hasattr(brand, 'budget_currency') and brand.budget_currency:
                display_currency = brand.budget_currency
            else:
                location_context = self._get_location_context(influencer.location)
                display_currency = location_context["currency"]
            
            budget_usd = brand.budget
            if hasattr(brand, 'budget_currency') and brand.budget_currency and brand.budget_currency != "USD":
                budget_usd = self._convert_to_usd(brand.budget, brand.budget_currency)
            
            budget_proposal = self._generate_budget_constrained_proposal_fixed(
                budget_usd, brand.content_requirements, display_currency
            )
            
            session.current_offer = NegotiationOffer(
                total_price=budget_usd,
                currency=display_currency,
                content_breakdown=budget_proposal["breakdown"],
                payment_terms="50% advance, 50% on completion",
                timeline_days=brand.campaign_duration_days,
                usage_rights="6 months social media usage",
                revisions_included=2
            )
        
        offer = session.current_offer
        
        # Format deliverables breakdown
        deliverables_lines = []
        for content_type, details in offer.content_breakdown.items():
            content_display = content_type.replace('_', ' ').title()
            deliverables_lines.append(
                f"• {content_display}: {details['rate_per_piece']} × {details['count']} = {details['total']}"
            )
        
        # Get location-specific payment recommendations
        location_context = self._get_location_context(influencer.location)
        
        # Use location-appropriate payment terms
        if influencer.location == LocationType.INDIA:
            payment_terms = "50% advance, 50% on completion (milestone-based as preferred in Indian market)"
        elif influencer.location == LocationType.US:
            payment_terms = "50% upfront, 50% within NET-30 terms"
        else:
            payment_terms = "50% advance, 50% on completion"
        
        # Convert total to display currency
        display_currency = offer.currency if hasattr(offer, 'currency') else location_context["currency"]
        total_local = self._convert_from_usd(offer.total_price, display_currency)
        total_formatted = self._format_currency(total_local, display_currency)
        
        session.status = NegotiationStatus.IN_PROGRESS
        
        message = self.conversation_templates["proposal"].format(
            deliverables_breakdown="\n".join(deliverables_lines),
            total_price=total_formatted,
            payment_terms=payment_terms,
            revisions=offer.revisions_included,
            duration=offer.timeline_days,
            usage_rights=offer.usage_rights,
            brand_name=brand.name
        )
        
        # Update session in database
        await negotiation_session_service.update_session(session, user_id)
        await self._add_to_conversation(session_id, "assistant", message, user_id)
        return message

    async def handle_user_response(self, session_id: str, user_input: str, user_id: Optional[str] = None) -> str:
        """Handle user response and generate appropriate reply."""
        session = await negotiation_session_service.get_session(session_id, user_id)
        if not session:
            return "Session not found."
        
        await self._add_to_conversation(session_id, "user", user_input, user_id)
        
        # Analyze user intent
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ['accept', 'agree', 'deal', 'yes', 'perfect', 'sounds good']):
            return await self._handle_acceptance(session_id, user_id)
        
        elif any(word in user_input_lower for word in ['reject', 'decline', 'no', 'not interested', 'pass']):
            return await self._handle_rejection(session_id, user_id)
        
        elif any(word in user_input_lower for word in ['counter', 'offer', 'suggest', '$', 'price', 'rate']):
            return await self._handle_counter_offer(session_id, user_input, user_id)
        
        elif any(word in user_input_lower for word in ['question', 'clarify', 'explain', 'details', 'more info']):
            return await self._handle_clarification(session_id, user_input, user_id)
        
        else:
            return await self._handle_general_response(session_id, user_input, user_id)

    async def _handle_acceptance(self, session_id: str, user_id: Optional[str] = None) -> str:
        """Handle user acceptance of offer."""
        session = await negotiation_session_service.get_session(session_id, user_id)
        if not session:
            return "Session not found."
        
        session.status = NegotiationStatus.AGREED
        session.agreed_terms = session.current_offer
        
        # Get location context for currency formatting
        location_context = self._get_location_context(session.influencer_profile.location)
        local_currency = location_context["currency"]
        
        # Format final terms with local currency
        final_terms_lines = []
        if session.current_offer:
            if session.current_offer.content_breakdown:
                for content_type, details in session.current_offer.content_breakdown.items():
                    content_display = content_type.replace('_', ' ').title()
                    final_terms_lines.append(
                        f"• {content_display}: {details['rate_per_piece']} × {details['count']} = {details['total']}"
                    )
            
            # Convert total to local currency
            total_local = self._convert_from_usd(session.current_offer.total_price, local_currency)
            total_formatted = self._format_currency(total_local, local_currency)
            
            final_terms_lines.extend([
                f"• Total Investment: {total_formatted}",
                f"• Payment Terms: {session.current_offer.payment_terms}",
                f"• Campaign Duration: {session.current_offer.timeline_days} days",
                f"• Usage Rights: {session.current_offer.usage_rights}"
            ])
        
        # Generate digital contract
        contract_service = get_contract_service()
        try:
            if contract_service:
                contract = contract_service.generate_contract(
                    session_id=session_id,
                    negotiation_state=session,
                    brand_contact_email=f"legal@{session.brand_details.name.lower().replace(' ', '')}.com",
                    brand_contact_name=f"{session.brand_details.name} Legal Team",
                    influencer_email=f"{session.influencer_profile.name.lower().replace(' ', '.')}@email.com",
                    influencer_contact="+1-XXX-XXX-XXXX"
                )
                
                contract_info = f"\n\n📄 **Digital Contract Generated!**\n"
                contract_info += f"Contract ID: `{contract.contract_id}`\n"
                contract_info += f"Status: {contract.status.value.replace('_', ' ').title()}\n"
                contract_info += f"Ready for signatures from both parties.\n"
                contract_info += f"\n🔗 You can view and sign the contract using the contract ID above."
                
                logger.info(f"Contract {contract.contract_id} generated for session {session_id}")
            else:
                contract_info = f"\n\n📄 **Contract Generation**: Our legal team will prepare the digital contract within 2 business days."
            
        except Exception as e:
            logger.error(f"Failed to generate contract for session {session_id}: {e}")
            contract_info = f"\n\n📄 **Contract Generation**: Our legal team will prepare the digital contract within 2 business days."
        
        message = self.conversation_templates["agreement"].format(
            final_terms="\n".join(final_terms_lines),
            brand_name=session.brand_details.name
        ) + contract_info
        
        # Update session in database
        await negotiation_session_service.update_session(session, user_id)
        await self._add_to_conversation(session_id, "assistant", message, user_id)
        return message

    async def _handle_rejection(self, session_id: str, user_id: Optional[str] = None) -> str:
        """Handle user rejection of offer."""
        session = await negotiation_session_service.get_session(session_id, user_id)
        if not session:
            return "Session not found."
        
        session.status = NegotiationStatus.REJECTED
        
        message = self.conversation_templates["rejection_response"].format(
            brand_name=session.brand_details.name
        )
        
        # Update session in database
        await negotiation_session_service.update_session(session, user_id)
        await self._add_to_conversation(session_id, "assistant", message, user_id)
        return message

    async def _handle_counter_offer(self, session_id: str, user_input: str, user_id: Optional[str] = None) -> str:
        """Handle counter offer from user with STRICT budget respect."""
        session = await negotiation_session_service.get_session(session_id, user_id)
        if not session:
            return "Session not found."
        
        session.status = NegotiationStatus.COUNTER_OFFER
        session.negotiation_round += 1
        
        # Get location context for currency formatting
        location_context = self._get_location_context(session.influencer_profile.location)
        local_currency = location_context["currency"]
        
        # Try to extract price from user input
        price_match = re.search(r'[₹$€£¥]?(\d+(?:,\d{3})*(?:\.\d{2})?)', user_input.replace(',', ''))
        counter_price_input = float(price_match.group(1)) if price_match else None
        
        # Convert counter price to USD for comparison
        counter_price_usd = self._convert_to_usd(counter_price_input, local_currency) if counter_price_input else None
        
        # Handle brand's budget calculations
        brand = session.brand_details
        brand_budget_usd = brand.budget
        
        if hasattr(brand, 'budget_currency') and brand.budget_currency and brand.budget_currency != "USD":
            brand_budget_usd = self._convert_to_usd(brand.budget, brand.budget_currency)
        
        our_price_usd = brand_budget_usd
        max_allowable_usd = brand_budget_usd * 1.10  # 10% flexibility
        
        # Generate response based on counter offer
        if counter_price_usd:
            # Determine display currency
            display_currency = local_currency
            if hasattr(brand, 'budget_currency') and brand.budget_currency:
                display_currency = brand.budget_currency
            
            our_price_display = self._convert_from_usd(our_price_usd, display_currency)
            counter_price_display = self._convert_from_usd(counter_price_usd, local_currency)
            
            our_price_formatted = self._format_currency(our_price_display, display_currency)
            counter_price_formatted = self._format_currency(counter_price_display, local_currency)
            
            difference_display = abs(counter_price_usd - our_price_usd)
            difference_formatted = self._format_currency(difference_display, 'USD')
            
            if counter_price_usd <= brand_budget_usd:
                analysis_response = f"✅ **Perfect!** Your request of {counter_price_formatted} is within our allocated budget."
                compromise_suggestion = f"We'll proceed with {counter_price_formatted} as agreed."
                session.current_offer.total_price = counter_price_usd
                session.status = NegotiationStatus.AGREED
                
            elif counter_price_usd <= max_allowable_usd:
                overage_percent = ((counter_price_usd / brand_budget_usd) - 1) * 100
                analysis_response = f"Your request of {counter_price_formatted} is {overage_percent:.1f}% above our allocated budget."
                
                if session.influencer_profile.location == LocationType.INDIA:
                    middle_price_usd = (our_price_usd + counter_price_usd) / 2
                    middle_price_local = self._convert_from_usd(middle_price_usd, local_currency)
                    compromise_suggestion = f"Let's meet in the middle at {self._format_currency(middle_price_local, local_currency)}?"
                else:
                    stretch_price_usd = min(counter_price_usd, max_allowable_usd)
                    stretch_price_local = self._convert_from_usd(stretch_price_usd, local_currency)
                    compromise_suggestion = f"We can stretch to {self._format_currency(stretch_price_local, local_currency)}."
                    
            else:
                overage_amount = counter_price_usd - max_allowable_usd
                overage_formatted = self._format_currency(self._convert_from_usd(overage_amount, local_currency), local_currency)
                analysis_response = f"Your request exceeds our budget by {overage_formatted}."
                
                max_offer_local = self._convert_from_usd(max_allowable_usd, local_currency)
                max_offer_formatted = self._format_currency(max_offer_local, local_currency)
                compromise_suggestion = f"Our absolute maximum is {max_offer_formatted}."
        else:
            our_price_formatted = "Current offer"
            counter_price_formatted = "Not specified"
            difference_formatted = "N/A"
            analysis_response = "I'd love to discuss your thoughts on the proposal."
            compromise_suggestion = "Could you share your budget expectations?"
        
        message = self.conversation_templates["counter_offer_response"].format(
            counter_price=counter_price_formatted,
            our_price=our_price_formatted,
            difference=difference_formatted,
            analysis_response=analysis_response,
            compromise_suggestion=compromise_suggestion
        )
        
        # Update session in database
        await negotiation_session_service.update_session(session, user_id)
        await self._add_to_conversation(session_id, "assistant", message, user_id)
        return message

    async def _handle_clarification(self, session_id: str, user_input: str, user_id: Optional[str] = None) -> str:
        """Handle clarification questions."""
        clarification_response = """I'm happy to clarify any details! Here are some key points:

📋 **Content Deliverables**: Each piece includes concept development, creation, editing, and posting
🔄 **Revision Process**: 2 rounds of revisions included to ensure content meets brand guidelines
📅 **Timeline**: Flexible scheduling with milestone-based delivery
💳 **Payment**: Secure payment processing with clear terms
🎯 **Brand Guidelines**: Detailed brief provided to ensure authentic content creation
📊 **Performance**: Optional performance reporting available

What specific aspect would you like me to explain further?"""
        
        await self._add_to_conversation(session_id, "assistant", clarification_response, user_id)
        return clarification_response

    async def _handle_general_response(self, session_id: str, user_input: str, user_id: Optional[str] = None) -> str:
        """Handle general conversational responses."""
        responses = [
            "That's a great point! What aspects are most important to you in this partnership?",
            "I appreciate your perspective! What would make this opportunity more appealing?",
            "Building the right partnership is crucial. What elements would you like to discuss?",
            "I'm here to make this smooth for you. What questions do you have?"
        ]
        
        # Simple sentiment-based response selection
        if any(word in user_input.lower() for word in ['excited', 'interested', 'love', 'great']):
            response = responses[0]
        elif any(word in user_input.lower() for word in ['concerned', 'worried', 'unsure']):
            response = responses[1]
        else:
            response = responses[2]
        
        await self._add_to_conversation(session_id, "assistant", response, user_id)
        return response

    async def _add_to_conversation(self, session_id: str, role: str, message: str, user_id: Optional[str] = None):
        """Add message to conversation history in database."""
        try:
            await negotiation_session_service.add_message_to_conversation(
                session_id, role, message, user_id
            )
        except Exception as e:
            logger.error(f"Error adding message to conversation {session_id}: {e}")

    async def get_session_state(self, session_id: str, user_id: Optional[str] = None) -> Optional[NegotiationState]:
        """Get current session state from database."""
        try:
            return await negotiation_session_service.get_session(session_id, user_id)
        except Exception as e:
            logger.error(f"Error getting session state {session_id}: {e}")
            return None

    async def get_conversation_history(self, session_id: str, user_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Get conversation history for session from database."""
        try:
            return await negotiation_session_service.get_conversation_history(session_id, user_id)
        except Exception as e:
            logger.error(f"Error getting conversation history {session_id}: {e}")
            return []

    async def delete_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a negotiation session from database."""
        try:
            return await negotiation_session_service.delete_session(session_id, user_id)
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    async def list_user_sessions(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active sessions for a user from database."""
        try:
            return await negotiation_session_service.list_user_sessions(user_id, status)
        except Exception as e:
            logger.error(f"Error listing sessions for user {user_id}: {e}")
            return []

    # Currency conversion and formatting methods
    def _format_currency(self, amount: float, currency: str) -> str:
        """Simple currency formatting."""
        currency_symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'CAD': 'C$', 'AUD': 'A$', 'CHF': 'CHF ', 'CNY': '¥',
            'INR': '₹', 'BRL': 'R$', 'MXN': 'MX$', 'KRW': '₩'
        }
        
        symbol = currency_symbols.get(currency, f'{currency} ')
        
        if currency in ['JPY', 'KRW']:
            return f"{symbol}{amount:,.0f}"
        else:
            return f"{symbol}{amount:,.2f}"

    def _convert_from_usd(self, amount: float, to_currency: str) -> float:
        """Simple fallback currency conversion from USD."""
        if to_currency == 'USD':
            return amount
        
        rates_from_usd = {
            'EUR': 0.85, 'GBP': 0.79, 'CAD': 1.35, 'AUD': 1.52,
            'JPY': 150.0, 'INR': 83.0, 'BRL': 5.0, 'MXN': 18.0,
            'CHF': 0.91, 'CNY': 7.2, 'KRW': 1320.0
        }
        
        rate = rates_from_usd.get(to_currency, 1.0)
        return amount * rate

    def _convert_to_usd(self, amount: float, from_currency: str) -> float:
        """Simple fallback currency conversion to USD."""
        if from_currency == 'USD':
            return amount
        
        rates_to_usd = {
            'EUR': 1.18, 'GBP': 1.27, 'CAD': 0.74, 'AUD': 0.66,
            'JPY': 0.0067, 'INR': 0.012, 'BRL': 0.20, 'MXN': 0.055,
            'CHF': 1.10, 'CNY': 0.14, 'KRW': 0.00076
        }
        
        rate = rates_to_usd.get(from_currency, 1.0)
        return amount * rate
        
    def _generate_budget_constrained_proposal_fixed(
        self, 
        brand_budget: float,
        content_requirements: Dict[str, int],
        brand_currency: str = "USD"
    ) -> Dict[str, Any]:
        """Generate a budget-constrained proposal with basic rates."""
        
        base_rates = {
            "instagram_post": 50,
            "instagram_reel": 75,
            "instagram_story": 25,
            "youtube_long_form": 200,
            "youtube_shorts": 100,
            "linkedin_post": 40,
            "linkedin_video": 80,
            "tiktok_video": 60
        }
        
        total_content_pieces = sum(content_requirements.values())
        budget_per_piece = brand_budget / total_content_pieces if total_content_pieces > 0 else 0
        
        breakdown = {}
        total_allocated = 0
        
        for content_type, count in content_requirements.items():
            base_rate = base_rates.get(content_type, 50)
            adjusted_rate = min(base_rate, budget_per_piece)
            
            breakdown[content_type] = {
                "count": count,
                "rate_per_piece": self._format_currency(adjusted_rate, brand_currency),
                "total": self._format_currency(adjusted_rate * count, brand_currency)
            }
            total_allocated += adjusted_rate * count
        
        return {
            "total_budget": brand_budget,
            "total_allocated": total_allocated,
            "remaining_budget": self._format_currency(brand_budget - total_allocated, brand_currency),
            "breakdown": breakdown,
            "currency": brand_currency
        }

    def _get_location_context(self, location: LocationType) -> Dict[str, str]:
        """Get basic location context."""
        location_contexts = {
            LocationType.INDIA: {
                "greeting": "Namaste",
                "currency": "INR",
                "note": "Looking forward to working with you!"
            },
            LocationType.US: {
                "greeting": "Hello",
                "currency": "USD", 
                "note": "Excited about this collaboration opportunity!"
            },
            LocationType.UK: {
                "greeting": "Hello",
                "currency": "GBP",
                "note": "Brilliant! Looking forward to working together!"
            }
        }
        
        return location_contexts.get(location, {
            "greeting": "Hello",
            "currency": "USD",
            "note": "Looking forward to our collaboration!"
        })

# Create a global instance
conversation_handler_db = ConversationHandlerDB()
