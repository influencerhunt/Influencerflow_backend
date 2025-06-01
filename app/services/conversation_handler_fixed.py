from typing import Dict, List, Optional, Any, Tuple
import json
import uuid
import re
from datetime import datetime
from dataclasses import dataclass
from app.models.negotiation_models import (
    NegotiationState, BrandDetails, InfluencerProfile, 
    NegotiationOffer, ContentDeliverable, NegotiationStatus,
    PlatformType, ContentType, LocationType
)
import logging
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

class ConversationHandler:
    def __init__(self):
        """Handle conversation flow for brand-side negotiations."""
        self.active_sessions: Dict[str, NegotiationState] = {}
        
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
        
        # Approximate exchange rates
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
        
        # Approximate exchange rates
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
        
        # Basic content rates (USD)
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
                "rate_per_piece": adjusted_rate,
                "total": adjusted_rate * count
            }
            total_allocated += adjusted_rate * count
        
        return {
            "total_budget": brand_budget,
            "total_allocated": total_allocated,
            "remaining_budget": brand_budget - total_allocated,
            "breakdown": breakdown,
            "currency": brand_currency
        }

    def create_session(
        self, 
        brand_details: BrandDetails, 
        influencer_profile: InfluencerProfile
    ) -> str:
        """Create a new negotiation session."""
        session_id = str(uuid.uuid4())
        
        negotiation_state = NegotiationState(
            session_id=session_id,
            brand_details=brand_details,
            influencer_profile=influencer_profile,
            status=NegotiationStatus.INITIATED
        )
        
        self.active_sessions[session_id] = negotiation_state
        return session_id

    def generate_greeting_message(self, session_id: str) -> str:
        """Generate the initial greeting message."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        brand = session.brand_details
        influencer = session.influencer_profile
        
        # SIMPLIFIED CURRENCY LOGIC: Use brand's specified currency throughout
        # The brand's budget and currency are used as-is, no conversions
        if hasattr(brand, 'budget_currency') and brand.budget_currency:
            display_currency = brand.budget_currency
            print(f"Brand budget currency: {display_currency}")
            budget_display = brand.budget  # Use budget as-is in the specified currency
            print(f"Brand budget: {budget_display}")
        else:
            # Fallback to USD if no currency specified
            display_currency = "USD"
            budget_display = brand.budget

        budget_formatted = self._format_currency(budget_display, display_currency)

        # Create content summary
        content_summary = []
        for content_type, quantity in brand.content_requirements.items():
            content_summary.append(f"{quantity}x {content_type.replace('_', ' ').title()}")
        
        message = self.conversation_templates["greeting"].format(
            brand_name=brand.name,
            goals=", ".join(brand.goals),
            budget=budget_formatted,
            platforms=", ".join([p.value.title() for p in brand.target_platforms]),
            content_summary=", ".join(content_summary),
            duration=brand.campaign_duration_days
        )
        print(f"Message: {message}")
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def generate_market_analysis(self, session_id: str) -> str:
        """Generate market analysis message using brand's specified currency throughout."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # SIMPLIFIED: Use brand's currency for all calculations and display
        if hasattr(brand, 'budget_currency') and brand.budget_currency:
            brand_currency = brand.budget_currency
            brand_budget = brand.budget  # Use as-is in brand currency
        else:
            brand_currency = "USD"
            brand_budget = brand.budget

        # For pricing service compatibility, we may need to pass USD values
        # Convert to USD only if needed for internal calculations
        # if brand_currency == "USD":
        #     budget_usd = brand_budget
        # else:
        #     budget_usd = self.pricing_service.convert_to_usd(brand_budget, brand_currency)
        budget_usd = int(brand_budget)

        print(f"Budget USD: {budget_usd}")
        print(f"Brand currency: {brand_currency}")
        # Generate budget proposal in USD for internal calculations
        brand_location = getattr(brand, 'brand_location', None) or LocationType.US
        budget_proposal = self._generate_budget_constrained_proposal_fixed(
            brand_budget,
            brand.content_requirements,
            brand_currency
        )
        
        if "error" in budget_proposal:
            return f"I apologize, but I encountered an issue generating the proposal: {budget_proposal['error']}"
        
        # Convert all values to brand's specified currency for display
        rate_breakdown_lines = []
        total_brand_currency = 0
        
        for content_type, details in budget_proposal["breakdown"].items():
            content_display = content_type.replace('_', ' ').title()
            
            # Extract numeric values from the pricing service output
            unit_rate_usd = float(details['rate_per_piece'])
            total_usd = float(details['total'])
            quantity = details['count']
            
            # Convert to brand currency
            if brand_currency == "USD":
                unit_rate_display = unit_rate_usd
                total_display = total_usd
            else:
                unit_rate_display = self._convert_from_usd(unit_rate_usd, brand_currency)
                total_display = self._convert_from_usd(total_usd, brand_currency)
            
            # Format in brand currency
            unit_rate_formatted = self._format_currency(unit_rate_display, brand_currency)
            total_formatted = self._format_currency(total_display, brand_currency)
            
            rate_breakdown_lines.append(
                f"• {content_display}: {unit_rate_formatted} × {quantity} = {total_formatted}"
            )
            
            total_brand_currency += total_display
        
        # Format total in brand currency
        total_formatted = self._format_currency(total_brand_currency, brand_currency)
        
        # Add cultural context based on location
        cultural_note = ""
        if influencer.location == LocationType.INDIA:
            cultural_note = "\n\n🤝 **Partnership Approach**: We believe in building long-term relationships with talented creators like yourself. This budget allocation reflects our commitment to fair compensation while ensuring campaign success."
        elif influencer.location == LocationType.US:
            cultural_note = "\n\n📊 **Market Alignment**: Our budget allocation is competitive with current market standards and designed for optimal ROI."
        elif influencer.location == LocationType.BRAZIL:
            cultural_note = "\n\n🌟 **Collaboration Focus**: We're excited about the creative potential of this partnership and have allocated our budget to support your artistic vision."
        
        # Store the proposal in session (convert back to USD for internal storage)
        session.current_offer = NegotiationOffer(
            total_price=budget_usd if brand_currency != "USD" else total_brand_currency,
            currency=brand_currency,
            content_breakdown=budget_proposal["breakdown"],
            payment_terms="50% advance, 50% on completion",
            timeline_days=brand.campaign_duration_days,
            usage_rights="6 months social media usage",
            revisions_included=2
        )
        
        message = self.conversation_templates["market_analysis"].format(
            followers=influencer.followers,
            engagement_rate=influencer.engagement_rate,
            location=influencer.location.value,
            platforms=", ".join([p.value.title() for p in influencer.platforms]),
            rate_breakdown="\n".join(rate_breakdown_lines),
            total_value=total_formatted
        ) + cultural_note + f"\n\n💰 **Budget Allocation**: This proposal utilizes our full allocated budget of {self._format_currency(brand_budget, brand_currency)} to provide you with competitive compensation."
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def generate_proposal(self, session_id: str) -> str:
        """Generate formal proposal message using brand's specified currency."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # Use brand's specified currency
        if hasattr(brand, 'budget_currency') and brand.budget_currency:
            brand_currency = brand.budget_currency
        else:
            brand_currency = "USD"
        
        # Use existing offer or create new one
        if not hasattr(session, 'current_offer') or session.current_offer is None:
            # Fallback: generate new proposal if needed
            return self.generate_market_analysis(session_id)
        
        offer = session.current_offer
        print(f"Offer: {offer}")
        # Format deliverables breakdown in brand currency
        deliverables_lines = []
        total_brand_currency = 0
        
        for content_type, details in offer.content_breakdown.items():
            content_display = content_type.replace('_', ' ').title()
            
            # Extract values and convert to brand currency
            print(f"Details: {details}")
            unit_rate_usd = float(details['rate_per_piece'])
            total_usd = float(details['total'])
            quantity = details['count']
            
            if brand_currency == "USD":
                unit_rate_display = unit_rate_usd
                total_display = total_usd
            else:
                unit_rate_display = self._convert_from_usd(unit_rate_usd, brand_currency)
                total_display = self._convert_from_usd(total_usd, brand_currency)
            
            unit_rate_formatted = self._format_currency(unit_rate_display, brand_currency)
            total_formatted = self._format_currency(total_display, brand_currency)
            
            deliverables_lines.append(
                f"• {content_display}: {unit_rate_formatted} × {quantity} = {total_formatted}"
            )
            
            total_brand_currency += total_display
        
        # Location-appropriate payment terms
        if influencer.location == LocationType.INDIA:
            payment_terms = "50% advance, 50% on completion (milestone-based as preferred in Indian market)"
        elif influencer.location == LocationType.US:
            payment_terms = "50% upfront, 50% within NET-30 terms"
        else:
            payment_terms = "50% advance, 50% on completion"
        
        total_formatted = self._format_currency(total_brand_currency, brand_currency)
        
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
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def handle_user_response(self, session_id: str, user_input: str) -> str:
        """Handle user response and generate appropriate reply."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        self._add_to_conversation(session_id, "user", user_input)
        
        # Analyze user intent
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ['accept', 'agree', 'deal', 'yes', 'perfect', 'sounds good']):
            return self._handle_acceptance(session_id)
        
        elif any(word in user_input_lower for word in ['reject', 'decline', 'no', 'not interested', 'pass']):
            return self._handle_rejection(session_id)
        
        elif any(word in user_input_lower for word in ['counter', 'offer', 'suggest', '$', 'price', 'rate']):
            return self._handle_counter_offer(session_id, user_input)
        
        elif any(word in user_input_lower for word in ['question', 'clarify', 'explain', 'details', 'more info']):
            return self._handle_clarification(session_id, user_input)
        
        else:
            return self._handle_general_response(session_id, user_input)

    def _handle_acceptance(self, session_id: str) -> str:
        """Handle user acceptance of offer."""
        session = self.active_sessions[session_id]
        session.status = NegotiationStatus.AGREED
        session.agreed_terms = session.current_offer
        
        # Use brand's specified currency for final terms
        brand = session.brand_details
        if hasattr(brand, 'budget_currency') and brand.budget_currency:
            brand_currency = brand.budget_currency
        else:
            brand_currency = "USD"
        
        # Format final terms in brand currency
        final_terms_lines = []
        if session.current_offer:
            if session.current_offer.content_breakdown:
                total_brand_currency = 0
                
                for content_type, details in session.current_offer.content_breakdown.items():
                    content_display = content_type.replace('_', ' ').title()
                    
                    # Convert to brand currency
                    unit_rate_usd = float(details['rate_per_piece'])
                    total_usd = float(details['total'])
                    quantity = details['count']
                    
                    if brand_currency == "USD":
                        unit_rate_display = unit_rate_usd
                        total_display = total_usd
                    else:
                        unit_rate_display = self._convert_from_usd(unit_rate_usd, brand_currency)
                        total_display = self._convert_from_usd(total_usd, brand_currency)
                    
                    unit_rate_formatted = self._format_currency(unit_rate_display, brand_currency)
                    total_formatted = self._format_currency(total_display, brand_currency)
                    
                    final_terms_lines.append(
                        f"• {content_display}: {unit_rate_formatted} × {quantity} = {total_formatted}"
                    )
                    
                    total_brand_currency += total_display
                
                total_formatted = self._format_currency(total_brand_currency, brand_currency)
                
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
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def _handle_rejection(self, session_id: str) -> str:
        """Handle user rejection of offer."""
        session = self.active_sessions[session_id]
        session.status = NegotiationStatus.REJECTED
        
        message = self.conversation_templates["rejection_response"].format(
            brand_name=session.brand_details.name
        )
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def _handle_counter_offer(self, session_id: str, user_input: str) -> str:
        """Handle counter offer using brand's specified currency for all negotiations."""
        session = self.active_sessions[session_id]
        session.status = NegotiationStatus.COUNTER_OFFER
        session.negotiation_round += 1
        
        brand = session.brand_details
        
        # Use brand's specified currency for all negotiations
        if hasattr(brand, 'budget_currency') and brand.budget_currency:
            brand_currency = brand.budget_currency
            brand_budget = brand.budget  # Use as-is in brand currency
        else:
            brand_currency = "USD"
            brand_budget = brand.budget
        
        # Extract price from user input (assume it's in the same currency context)
        price_match = re.search(r'[₹$€£¥]?(\d+(?:,\d{3})*(?:\.\d{2})?)', user_input.replace(',', ''))
        counter_price_input = float(price_match.group(1)) if price_match else None
        
        if counter_price_input:
            # Compare directly in brand currency - no conversions needed
            our_price = brand_budget
            counter_price = counter_price_input
            difference = abs(counter_price - our_price)
            
            # Format values in brand currency
            our_price_formatted = self._format_currency(our_price, brand_currency)
            counter_price_formatted = self._format_currency(counter_price, brand_currency)
            difference_formatted = self._format_currency(difference, brand_currency)
            
            # Maximum 10% flexibility above budget
            max_allowable = brand_budget * 1.10
            
            if counter_price <= brand_budget:
                # Counter-offer is within budget - ACCEPT
                analysis_response = f"✅ **Perfect!** Your request of {counter_price_formatted} is within our allocated budget. We can definitely make this work!"
                compromise_suggestion = f"We'll proceed with {counter_price_formatted} as agreed. This demonstrates our commitment to building a strong partnership with you."
                
                # Update offer to the accepted amount
                if hasattr(session, 'current_offer') and session.current_offer:
                    # Convert back to USD for internal storage if needed
                    if brand_currency == "USD":
                        session.current_offer.total_price = counter_price
                    else:
                        session.current_offer.total_price = self._convert_to_usd(counter_price, brand_currency)
                
                session.status = NegotiationStatus.AGREED
                
            elif counter_price <= max_allowable:
                # Counter-offer is slightly above budget but within negotiation range
                overage_percent = ((counter_price / brand_budget) - 1) * 100
                analysis_response = f"Your request of {counter_price_formatted} is {overage_percent:.1f}% above our allocated budget of {our_price_formatted}."
                
                # Cultural response based on location
                if session.influencer_profile.location == LocationType.INDIA:
                    middle_price = (our_price + counter_price) / 2
                    compromise_suggestion = f"We appreciate your professional approach! Let's meet in the middle. How about {self._format_currency(middle_price, brand_currency)}? This shows our commitment to building a long-term partnership."
                elif session.influencer_profile.location == LocationType.US:
                    stretch_price = min(counter_price, max_allowable)
                    compromise_suggestion = f"Given your quality portfolio, we can stretch our budget slightly. Would {self._format_currency(stretch_price, brand_currency)} work for you?"
                else:
                    solution_price = (our_price + min(counter_price, max_allowable)) / 2
                    compromise_suggestion = f"We value this collaboration. Let's find a solution at {self._format_currency(solution_price, brand_currency)}?"
                
            else:
                # Counter-offer exceeds maximum allowable budget
                overage_amount = counter_price - max_allowable
                overage_formatted = self._format_currency(overage_amount, brand_currency)
                
                analysis_response = f"Your request of {counter_price_formatted} exceeds our campaign budget by {overage_formatted}."
                
                max_offer_formatted = self._format_currency(max_allowable, brand_currency)
                compromise_suggestion = f"Our absolute maximum for this campaign is {max_offer_formatted}. Beyond this, we'd need to reduce content scope or explore a different campaign structure. Would the maximum budget work, or should we consider alternative approaches?"
                
        else:
            # No price detected in counter-offer
            analysis_response = "I'd love to discuss your thoughts on the proposal."
            compromise_suggestion = "Could you share your budget expectations so we can find the best path forward?"
            
            our_price_formatted = self._format_currency(brand_budget, brand_currency)
            counter_price_formatted = "Not specified"
            difference_formatted = "N/A"
        
        # Generate response using template
        message = self.conversation_templates["counter_offer_response"].format(
            counter_price=counter_price_formatted,
            our_price=our_price_formatted,
            difference=difference_formatted,
            analysis_response=analysis_response,
            compromise_suggestion=compromise_suggestion
        )
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def _handle_clarification(self, session_id: str, user_input: str) -> str:
        """Handle clarification questions."""
        clarification_response = """I'm happy to clarify any details! Here are some key points that might help:

📋 **Content Deliverables**: Each piece includes concept development, creation, editing, and posting
🔄 **Revision Process**: 2 rounds of revisions included to ensure content meets brand guidelines
📅 **Timeline**: Flexible scheduling with milestone-based delivery
💳 **Payment**: Secure payment processing with clear terms
🎯 **Brand Guidelines**: Detailed brief provided to ensure authentic content creation
📊 **Performance**: Optional performance reporting available

What specific aspect would you like me to explain further?"""
        
        self._add_to_conversation(session_id, "assistant", clarification_response)
        return clarification_response

    def _handle_general_response(self, session_id: str, user_input: str) -> str:
        """Handle general conversational responses."""
        responses = [
            "That's a great point! I want to make sure we create a collaboration that truly works for you. What aspects are most important to you in this partnership?",
            "I appreciate your perspective! Let's make sure we address all your concerns. What would make this opportunity more appealing for you?",
            "Absolutely! Building the right partnership is crucial. What elements would you like to discuss or adjust in our proposal?",
            "I'm here to make this as smooth as possible for you. What questions or suggestions do you have about the collaboration structure?"
        ]
        
        # Simple sentiment-based response selection
        if any(word in user_input.lower() for word in ['excited', 'interested', 'love', 'great']):
            response = responses[0]
        elif any(word in user_input.lower() for word in ['concerned', 'worried', 'unsure']):
            response = responses[1]
        else:
            response = responses[2]
        
        self._add_to_conversation(session_id, "assistant", response)
        return response

    def _add_to_conversation(self, session_id: str, role: str, message: str):
        """Add message to conversation history."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].conversation_history.append({
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })

    def get_session_state(self, session_id: str) -> Optional[NegotiationState]:
        """Get current session state."""
        return self.active_sessions.get(session_id)

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for session."""
        session = self.active_sessions.get(session_id)
        return session.conversation_history if session else []
