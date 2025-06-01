from typing import Dict, List, Optional, Any
import json
import uuid
import re
from datetime import datetime
from app.models.negotiation_models import (
    NegotiationState, BrandDetails, InfluencerProfile, 
    NegotiationOffer, ContentDeliverable, NegotiationStatus,
    PlatformType, ContentType, LocationType
)
from app.services.pricing_service import PricingService
import logging

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
        self.pricing_service = PricingService()
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
        
        # Determine the currency to use for budget display
        # Priority: brand_currency > brand_location currency > USD default
        # 1) Choose which currency to show (brand.budget_currency → brand_location → USD default)
        if hasattr(brand, 'budget_currency') and brand.budget_currency:
            display_currency = brand.budget_currency
        else:
            display_currency = "USD"

# 2) Figure out raw “budget_display” WITHOUT re‐interpreting it as USD if it's already INR
        if display_currency == "USD":
    # We assume brand.budget is already USD
            budget_display = brand.budget
        else:
    # If the brand actually provided an INR budget_currency,
    # treat brand.budget as INR directly—no USD conversion step.
            if hasattr(brand, 'budget_currency') and brand.budget_currency == display_currency:
                budget_display = brand.budget
            else:
        # Fallback: convert from USD to display_currency only if brand.budget was truly
        # a USD number (brand.budget_currency != display_currency)
             budget_display = self.pricing_service.convert_from_usd(brand.budget, display_currency)

        budget_formatted = self.pricing_service.format_currency(budget_display, display_currency)

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
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def generate_market_analysis(self, session_id: str) -> str:
        """Generate market analysis message using BUDGET-BASED approach instead of market rates."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # Determine budget currency for internal calculations
        # If brand specifies currency, convert budget to USD for internal use
        budget_usd = brand.budget
        if hasattr(brand, 'budget_currency') and brand.budget_currency and brand.budget_currency != "USD":
            budget_usd = self.pricing_service.convert_to_usd(brand.budget, brand.budget_currency)
        
        # CRITICAL FIX: Use budget-based breakdown instead of market rates
        # Ensure brand_location is not None
        brand_location = getattr(brand, 'brand_location', None) or LocationType.US
        
        budget_proposal = self.pricing_service.generate_budget_constrained_proposal_fixed(
            influencer, 
            brand.content_requirements, 
            budget_usd,  # Use USD for internal calculations
            brand_location
        )
        
        if "error" in budget_proposal:
            return f"I apologize, but I encountered an issue generating the proposal: {budget_proposal['error']}"
        
        # Get location context for cultural intelligence and currency
        location_context = self.pricing_service.get_location_context(influencer.location)
        
        # Determine display currency (preferring brand's specified currency)
        if hasattr(brand, 'budget_currency') and brand.budget_currency:
            display_currency = brand.budget_currency
        else:
            display_currency = budget_proposal["currencies"]["influencer"]
        
        # Format rate breakdown using budget allocation (NOT market rates)
        rate_breakdown_lines = []
        for content_type, details in budget_proposal["content_breakdown"].items():
            content_display = content_type.replace('_', ' ').title()
            
            # Convert to display currency if needed
            if display_currency != budget_proposal["currencies"]["influencer"]:
                unit_rate_usd = self.pricing_service.convert_to_usd(
                    float(details['unit_rate'].replace('₹', '').replace('$', '').replace(',', '')), 
                    budget_proposal["currencies"]["influencer"]
                )
                unit_rate_display = self.pricing_service.convert_from_usd(unit_rate_usd, display_currency)
                unit_rate_formatted = self.pricing_service.format_currency(unit_rate_display, display_currency)
                
                total_usd = self.pricing_service.convert_to_usd(
                    float(details['total'].replace('₹', '').replace('$', '').replace(',', '')),
                    budget_proposal["currencies"]["influencer"]
                )
                total_display = self.pricing_service.convert_from_usd(total_usd, display_currency)
                total_formatted = self.pricing_service.format_currency(total_display, display_currency)
            else:
                unit_rate_formatted = details['unit_rate']
                total_formatted = details['total']
            
            rate_breakdown_lines.append(
                f"• {content_display}: {unit_rate_formatted} × {details['quantity']} = {total_formatted}"
            )
        
        # Add cultural context based on location
        cultural_note = ""
        if influencer.location == LocationType.INDIA:
            cultural_note = "\n\n🤝 **Partnership Approach**: We believe in building long-term relationships with talented creators like yourself. This budget allocation reflects our commitment to fair compensation while ensuring campaign success."
        elif influencer.location == LocationType.US:
            cultural_note = "\n\n📊 **Market Alignment**: Our budget allocation is competitive with current market standards and designed for optimal ROI."
        elif influencer.location == LocationType.BRAZIL:
            cultural_note = "\n\n🌟 **Collaboration Focus**: We're excited about the creative potential of this partnership and have allocated our budget to support your artistic vision."
        
        # Store the proposal in session for later reference
        session.current_offer = NegotiationOffer(
            total_price=budget_usd,  # Store in USD internally
            currency=display_currency,  # Remember the display currency
            content_breakdown=budget_proposal["content_breakdown"],
            payment_terms="50% advance, 50% on completion",
            timeline_days=brand.campaign_duration_days,
            usage_rights="6 months social media usage",
            revisions_included=2
        )
        
        # Format total offer in display currency
        total_offer_display = budget_proposal["total_offer"]
        if display_currency != budget_proposal["currencies"]["influencer"]:
            total_usd = self.pricing_service.convert_to_usd(
                float(budget_proposal["total_offer"].replace('₹', '').replace('$', '').replace(',', '')),
                budget_proposal["currencies"]["influencer"]
            )
            total_display_amount = self.pricing_service.convert_from_usd(total_usd, display_currency)
            total_offer_display = self.pricing_service.format_currency(total_display_amount, display_currency)
        
        message = self.conversation_templates["market_analysis"].format(
            followers=influencer.followers,
            engagement_rate=influencer.engagement_rate,
            location=influencer.location.value,
            platforms=", ".join([p.value.title() for p in influencer.platforms]),
            rate_breakdown="\n".join(rate_breakdown_lines),
            total_value=total_offer_display
        ) + cultural_note + f"\n\n{budget_proposal['budget_note']}"
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def generate_proposal(self, session_id: str) -> str:
        """Generate formal proposal message using budget-based approach with currency support."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # Determine budget currency for internal calculations
        # If brand specifies currency, convert budget to USD for internal use
        budget_usd = brand.budget
        if hasattr(brand, 'budget_currency') and brand.budget_currency and brand.budget_currency != "USD":
            budget_usd = self.pricing_service.convert_to_usd(brand.budget, brand.budget_currency)
        
        # Use budget-constrained proposal (already created in market analysis)
        if not hasattr(session, 'current_offer') or session.current_offer is None:
            # Create budget-based proposal if not exists
            # Ensure brand_location is not None
            brand_location = getattr(brand, 'brand_location', None) or LocationType.US
            
            budget_proposal = self.pricing_service.generate_budget_constrained_proposal_fixed(
                influencer, 
                brand.content_requirements, 
                budget_usd,  # Use USD for internal calculations
                brand_location
            )
            
            # Get location context
            location_context = self.pricing_service.get_location_context(influencer.location)
            
            # Determine display currency (preferring brand's specified currency)
            if hasattr(brand, 'budget_currency') and brand.budget_currency:
                display_currency = brand.budget_currency
            else:
                display_currency = budget_proposal["currencies"]["influencer"]
            
            # Store the proposal in session
            session.current_offer = NegotiationOffer(
                total_price=budget_usd,  # Store in USD internally
                currency=display_currency,  # Remember the display currency
                content_breakdown=budget_proposal["content_breakdown"],
                payment_terms="50% advance, 50% on completion",
                timeline_days=brand.campaign_duration_days,
                usage_rights="6 months social media usage",
                revisions_included=2
            )
        
        offer = session.current_offer
        
        # Format deliverables breakdown with appropriate currency
        deliverables_lines = []
        for content_type, details in offer.content_breakdown.items():
            content_display = content_type.replace('_', ' ').title()
            # Use the already formatted values from the budget proposal
            deliverables_lines.append(
                f"• {content_display}: {details['unit_rate']} × {details['quantity']} = {details['total']}"
            )
        
        # Get location-specific payment recommendations
        location_context = self.pricing_service.get_location_context(influencer.location)
        negotiation_strategy = self.pricing_service.get_negotiation_strategy(influencer)
        
        # Use location-appropriate payment terms
        if influencer.location == LocationType.INDIA:
            payment_terms = "50% advance, 50% on completion (milestone-based as preferred in Indian market)"
        elif influencer.location == LocationType.US:
            payment_terms = "50% upfront, 50% within NET-30 terms"
        else:
            payment_terms = "50% advance, 50% on completion"
        
        # Convert total to display currency
        display_currency = offer.currency if hasattr(offer, 'currency') else location_context["currency"]
        total_local = self.pricing_service.convert_from_usd(offer.total_price, display_currency)
        total_formatted = self.pricing_service.format_currency(total_local, display_currency)
        
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
        
        # Get location context for currency formatting
        location_context = self.pricing_service.get_location_context(session.influencer_profile.location)
        local_currency = location_context["currency"]
        
        # Format final terms with local currency
        final_terms_lines = []
        if session.current_offer:
            # Use content_breakdown instead of deliverables for budget-based approach
            if session.current_offer.content_breakdown:
                for content_type, details in session.current_offer.content_breakdown.items():
                    content_display = content_type.replace('_', ' ').title()
                    final_terms_lines.append(
                        f"• {content_display}: {details['unit_rate']} × {details['quantity']} = {details['total']}"
                    )
            
            # Convert total to local currency
            total_local = self.pricing_service.convert_from_usd(session.current_offer.total_price, local_currency)
            total_formatted = self.pricing_service.format_currency(total_local, local_currency)
            
            final_terms_lines.extend([
                f"• Total Investment: {total_formatted}",
                f"• Payment Terms: {session.current_offer.payment_terms}",
                f"• Campaign Duration: {session.current_offer.timeline_days} days",
                f"• Usage Rights: {session.current_offer.usage_rights}"
            ])
        
        # 🆕 GENERATE DIGITAL CONTRACT AUTOMATICALLY
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
        """Handle counter offer from user with STRICT budget respect."""
        session = self.active_sessions[session_id]
        session.status = NegotiationStatus.COUNTER_OFFER
        session.negotiation_round += 1
        
        # Get location context for currency formatting
        location_context = self.pricing_service.get_location_context(session.influencer_profile.location)
        local_currency = location_context["currency"]
        
        # Get location-specific negotiation strategy
        negotiation_strategy = self.pricing_service.get_negotiation_strategy(session.influencer_profile)
        
        # Try to extract price from user input (handles multiple currency symbols)
        price_match = re.search(r'[₹$€£¥]?(\d+(?:,\d{3})*(?:\.\d{2})?)', user_input.replace(',', ''))
        counter_price_input = float(price_match.group(1)) if price_match else None
        
        # Convert counter price to USD for comparison (assume it's in local currency)
        counter_price_usd = self.pricing_service.convert_to_usd(counter_price_input, local_currency) if counter_price_input else None
        
        # CRITICAL: Handle brand's specified currency for budget calculations
        brand = session.brand_details
        brand_budget_usd = brand.budget
        
        # If brand specified a currency, convert budget to USD for internal calculations
        if hasattr(brand, 'budget_currency') and brand.budget_currency and brand.budget_currency != "USD":
            brand_budget_usd = self.pricing_service.convert_to_usd(brand.budget, brand.budget_currency)
        
        # Our offer is EXACTLY the client's budget - never deviate
        our_price_usd = brand_budget_usd  # Client's exact budget in USD
        
        # STRICT POLICY: Maximum 10% flexibility above client's budget (reduced from 15%)
        max_negotiation_flexibility = 0.10  # 10% maximum flexibility
        max_allowable_usd = brand_budget_usd * (1 + max_negotiation_flexibility)
        
        if counter_price_usd:
            difference_usd = abs(counter_price_usd - our_price_usd)
            
            # Determine display currency for our price (preferring brand's specified currency)
            display_currency = local_currency  # Default to influencer's local currency
            if hasattr(brand, 'budget_currency') and brand.budget_currency:
                display_currency = brand.budget_currency
            
            # Convert values to display currency
            our_price_display = self.pricing_service.convert_from_usd(our_price_usd, display_currency)
            counter_price_display = self.pricing_service.convert_from_usd(counter_price_usd, local_currency)
            difference_display = abs(counter_price_display - our_price_display) if display_currency == local_currency else abs(counter_price_usd - our_price_usd)
            
            our_price_formatted = self.pricing_service.format_currency(our_price_display, display_currency)
            counter_price_formatted = self.pricing_service.format_currency(counter_price_display, local_currency)
            
            # Format difference in appropriate currency
            if display_currency == local_currency:
                difference_formatted = self.pricing_service.format_currency(difference_display, local_currency)
            else:
                difference_formatted = f"{self.pricing_service.format_currency(difference_display, 'USD')} USD"
            
            # FIXED: Respect client's budget constraints strictly
            if counter_price_usd <= brand_budget_usd:
                # Counter-offer is within or below client's budget - ACCEPT
                analysis_response = f"✅ **Perfect!** Your request of {counter_price_formatted} is within our allocated budget. We can definitely make this work!"
                compromise_suggestion = f"We'll proceed with {counter_price_formatted} as agreed. This demonstrates our commitment to building a strong partnership with you."
                
                # Update offer to the accepted amount
                session.current_offer.total_price = counter_price_usd
                session.status = NegotiationStatus.AGREED
                
            elif counter_price_usd <= max_allowable_usd:
                # Counter-offer is slightly above budget but within negotiation range
                overage_percent = ((counter_price_usd / brand_budget_usd) - 1) * 100
                analysis_response = f"Your request of {counter_price_formatted} is {overage_percent:.1f}% above our allocated budget of {our_price_formatted}."
                
                # Cultural response based on location
                if session.influencer_profile.location == LocationType.INDIA:
                    middle_price_usd = (our_price_usd + counter_price_usd) / 2
                    middle_price_local = self.pricing_service.convert_from_usd(middle_price_usd, local_currency)
                    compromise_suggestion = f"We appreciate your professional approach! Let's meet in the middle. How about {self.pricing_service.format_currency(middle_price_local, local_currency)}? This shows our commitment to building a long-term partnership."
                elif session.influencer_profile.location == LocationType.US:
                    stretch_price_usd = min(counter_price_usd, max_allowable_usd)
                    stretch_price_local = self.pricing_service.convert_from_usd(stretch_price_usd, local_currency)
                    compromise_suggestion = f"Given your quality portfolio, we can stretch our budget slightly. Would {self.pricing_service.format_currency(stretch_price_local, local_currency)} work for you?"
                else:
                    solution_price_usd = (our_price_usd + min(counter_price_usd, max_allowable_usd)) / 2
                    solution_price_local = self.pricing_service.convert_from_usd(solution_price_usd, local_currency)
                    compromise_suggestion = f"We value this collaboration. Let's find a solution at {self.pricing_service.format_currency(solution_price_local, local_currency)}?"
                
            else:
                # Counter-offer exceeds maximum allowable budget - FIRM BOUNDARY
                overage_amount = counter_price_usd - max_allowable_usd
                overage_formatted = self.pricing_service.format_currency(self.pricing_service.convert_from_usd(overage_amount, local_currency), local_currency)
                
                analysis_response = f"Your request of {counter_price_formatted} exceeds our campaign budget by {overage_formatted}."
                
                # Firm but respectful decline
                max_offer_local = self.pricing_service.convert_from_usd(max_allowable_usd, local_currency)
                max_offer_formatted = self.pricing_service.format_currency(max_offer_local, local_currency)
                
                compromise_suggestion = f"Our absolute maximum for this campaign is {max_offer_formatted}. Beyond this, we'd need to reduce content scope or explore a different campaign structure. Would the maximum budget work, or should we consider alternative approaches?"
                
        else:
            # No price detected in counter-offer
            analysis_response = "I'd love to discuss your thoughts on the proposal."
            compromise_suggestion = "Could you share your budget expectations so we can find the best path forward?"
            
            # Determine display currency for our price (preferring brand's specified currency)
            display_currency = local_currency  # Default to influencer's local currency
            if hasattr(brand, 'budget_currency') and brand.budget_currency:
                display_currency = brand.budget_currency
            
            our_price_display = self.pricing_service.convert_from_usd(our_price_usd, display_currency)
            our_price_formatted = self.pricing_service.format_currency(our_price_display, display_currency)
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
        # This would implement intelligent Q&A based on user questions
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
