from typing import Dict, List, Optional, Any
import json
import uuid
from datetime import datetime
from app.models.negotiation_models import (
    NegotiationState, BrandDetails, InfluencerProfile, 
    NegotiationOffer, ContentDeliverable, NegotiationStatus,
    PlatformType, ContentType, LocationType
)
from app.services.pricing_service import PricingService
from app.services.contract_service import contract_service
import logging

logger = logging.getLogger(__name__)

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
        
        # Get brand's location context for currency formatting
        # If brand location is not provided, use USD as default
        brand_location = brand.brand_location if brand.brand_location else LocationType.OTHER
        brand_location_context = self.pricing_service.get_location_context(brand_location)
        brand_currency = brand_location_context["currency"]
        
        # Convert budget to brand's local currency for display
        budget_local = self.pricing_service.convert_from_usd(brand.budget, brand_currency)
        budget_formatted = self.pricing_service.format_currency(budget_local, brand_currency)
        
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
        """Generate market analysis message with budget-constrained pricing."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # Generate budget-constrained proposal using enhanced pricing service
        location_proposal = self.pricing_service.generate_budget_constrained_proposal(
            influencer, brand.content_requirements, brand.budget, negotiation_flexibility_percent=15.0
        )
        
        # Get location context for cultural intelligence
        location_context = self.pricing_service.get_location_context(influencer.location)
        local_currency = location_context["currency"]
        
        # Format rate breakdown with local currency
        rate_breakdown_lines = []
        for content_type, details in location_proposal["item_breakdown"].items():
            content_display = content_type.replace('_', ' ').title()
            
            # Use final rates from budget-constrained proposal
            unit_rate_local = self.pricing_service.convert_from_usd(details['final_unit_rate'], local_currency)
            total_local = self.pricing_service.convert_from_usd(details['final_total'], local_currency)
            
            rate_breakdown_lines.append(
                f"• {content_display}: {self.pricing_service.format_currency(unit_rate_local, local_currency)} × {details['quantity']} = {self.pricing_service.format_currency(total_local, local_currency)}"
            )
        
        # Add cultural context information and budget strategy
        cultural_note = ""
        budget_analysis = location_proposal.get("budget_analysis", {})
        budget_strategy = budget_analysis.get("strategy", "within_budget")
        
        if budget_strategy == "within_budget":
            cultural_note += "\n\n💰 **Budget Analysis**: Excellent news! Market rates align perfectly with your budget allocation."
        elif budget_strategy == "negotiable_above_budget":
            overage_percent = (budget_analysis.get("budget_ratio", 1.0) - 1) * 100
            cultural_note += f"\n\n💰 **Budget Analysis**: Market rates are {overage_percent:.1f}% above budget, which is within our negotiation flexibility. We're confident we can find a mutually beneficial agreement."
        elif budget_strategy == "scale_to_max_budget":
            cultural_note += f"\n\n💰 **Budget Analysis**: We've adjusted our proposal to respect your budget constraints while maintaining fair compensation. Our rates reflect a balanced approach between market value and budget considerations."
        
        if influencer.location.value.lower() == "india":
            cultural_note += f"\n\n🌍 **Market Context**: We understand the Indian creator market and have tailored our rates accordingly. Our pricing reflects the volume-oriented approach and relationship-building focus that works well in this market."
        elif location_context["market_maturity"] == "emerging":
            cultural_note += f"\n\n🌍 **Market Context**: We've adjusted our proposal to reflect the local market dynamics in {influencer.location.value}."
        
        # Convert total to local currency for display
        total_value_local = self.pricing_service.convert_from_usd(location_proposal["total_cost"], local_currency)
        total_value_formatted = self.pricing_service.format_currency(total_value_local, local_currency)
        
        message = self.conversation_templates["market_analysis"].format(
            followers=influencer.followers,
            engagement_rate=influencer.engagement_rate,
            location=influencer.location.value,
            platforms=", ".join([p.value.title() for p in influencer.platforms]),
            rate_breakdown="\n".join(rate_breakdown_lines),
            total_value=total_value_formatted
        ) + cultural_note
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def generate_proposal(self, session_id: str) -> str:
        """Generate formal proposal message with location-aware pricing."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # Generate budget-constrained proposal using enhanced pricing service
        location_proposal = self.pricing_service.generate_budget_constrained_proposal(
            influencer, brand.content_requirements, brand.budget, negotiation_flexibility_percent=15.0
        )
        
        # Get location context for currency formatting
        location_context = self.pricing_service.get_location_context(influencer.location)
        local_currency = location_context["currency"]
        
        # Create deliverables using location-aware pricing
        deliverables = []
        for content_type, details in location_proposal["item_breakdown"].items():
            # Parse platform and content type
            parts = content_type.split('_', 1)
            if len(parts) == 2:
                platform_str, content_str = parts
                try:
                    platform = PlatformType(platform_str.lower())
                    content_enum = ContentType(content_str.lower())
                    
                    deliverable = ContentDeliverable(
                        platform=platform,
                        content_type=content_enum,
                        quantity=details["quantity"],
                        proposed_price=details["total"],
                        market_rate=details["unit_rate"]
                    )
                    deliverables.append(deliverable)
                except ValueError:
                    continue
        
        # Get location-specific payment terms
        payment_terms = location_proposal["payment_recommendations"][0] if location_proposal["payment_recommendations"] else "50% upfront, 50% on completion"
        
        # Create offer with location intelligence
        offer = NegotiationOffer(
            total_price=location_proposal["total_cost"],
            deliverables=deliverables,
            campaign_duration_days=brand.campaign_duration_days,
            payment_terms=payment_terms,
            revisions_included=2,
            usage_rights="6 months social media usage"
        )
        
        session.current_offer = offer
        session.status = NegotiationStatus.IN_PROGRESS
        
        # Format deliverables breakdown with local currency
        deliverables_lines = []
        for deliverable in deliverables:
            platform_name = deliverable.platform.value.title()
            content_name = deliverable.content_type.value.replace('_', ' ').title()
            
            # Convert price to local currency for display
            price_local = self.pricing_service.convert_from_usd(deliverable.proposed_price, local_currency)
            price_formatted = self.pricing_service.format_currency(price_local, local_currency)
            
            deliverables_lines.append(
                f"• {platform_name} {content_name} × {deliverable.quantity}: {price_formatted}"
            )
        
        # Add location-specific considerations
        location_note = ""
        if "india_specific" in location_proposal:
            india_info = location_proposal["india_specific"]
            if india_info["volume_discount_available"]:
                location_note += "\n\n💡 **Volume Bonus**: Since this is a substantial campaign, we're including our volume partnership rate."
            if india_info["portfolio_value_emphasis"]:
                location_note += "\n🎯 **Portfolio Value**: This collaboration will be a valuable addition to your brand partnership portfolio."
        
        # Add timeline considerations
        if location_proposal["timeline_considerations"]:
            timeline_note = f"\n⏰ **Timeline Note**: {location_proposal['timeline_considerations'][0]}"
            location_note += timeline_note
        
        # Convert total price to local currency for display
        total_price_local = self.pricing_service.convert_from_usd(offer.total_price, local_currency)
        total_price_formatted = self.pricing_service.format_currency(total_price_local, local_currency)
        
        message = self.conversation_templates["proposal"].format(
            deliverables_breakdown="\n".join(deliverables_lines),
            total_price=total_price_formatted,
            payment_terms=offer.payment_terms,
            revisions=offer.revisions_included,
            duration=offer.campaign_duration_days,
            usage_rights=offer.usage_rights,
            brand_name=brand.name
        ) + location_note
        
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
            for deliverable in session.current_offer.deliverables:
                platform_name = deliverable.platform.value.title()
                content_name = deliverable.content_type.value.replace('_', ' ').title()
                
                # Convert price to local currency for display
                price_local = self.pricing_service.convert_from_usd(deliverable.proposed_price, local_currency)
                price_formatted = self.pricing_service.format_currency(price_local, local_currency)
                
                final_terms_lines.append(
                    f"• {platform_name} {content_name} × {deliverable.quantity}: {price_formatted}"
                )
            
            # Convert total to local currency
            total_local = self.pricing_service.convert_from_usd(session.current_offer.total_price, local_currency)
            total_formatted = self.pricing_service.format_currency(total_local, local_currency)
            
            final_terms_lines.extend([
                f"• Total Investment: {total_formatted}",
                f"• Payment Terms: {session.current_offer.payment_terms}",
                f"• Campaign Duration: {session.current_offer.campaign_duration_days} days",
                f"• Usage Rights: {session.current_offer.usage_rights}"
            ])
        
        # 🆕 GENERATE DIGITAL CONTRACT AUTOMATICALLY
        try:
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
        """Handle counter offer from user with location-aware strategy."""
        session = self.active_sessions[session_id]
        session.status = NegotiationStatus.COUNTER_OFFER
        session.negotiation_round += 1
        
        # Get location context for currency formatting
        location_context = self.pricing_service.get_location_context(session.influencer_profile.location)
        local_currency = location_context["currency"]
        
        # Get location-specific negotiation strategy
        negotiation_strategy = self.pricing_service.get_negotiation_strategy(session.influencer_profile)
        
        # Try to extract price from user input (handles multiple currency symbols)
        import re
        price_match = re.search(r'[₹$€£¥]?(\d+(?:,\d{3})*(?:\.\d{2})?)', user_input.replace(',', ''))
        counter_price_input = float(price_match.group(1)) if price_match else None
        
        # Convert counter price to USD for comparison (assume it's in local currency)
        counter_price_usd = self.pricing_service.convert_to_usd(counter_price_input, local_currency) if counter_price_input else None
        
        our_price_usd = session.current_offer.total_price if session.current_offer else 0
        
        # CRITICAL: Get the brand's budget constraints with 15% negotiation flexibility
        brand_budget_usd = session.brand_details.budget  # This is already in USD
        max_negotiation_flexibility = 0.15  # 15% maximum flexibility
        max_allowable_usd = brand_budget_usd * (1 + max_negotiation_flexibility)  # 15% above budget max
        
        if counter_price_usd:
            difference_usd = abs(counter_price_usd - our_price_usd)
            
            # Convert values to local currency for display
            counter_price_local = self.pricing_service.convert_from_usd(counter_price_usd, local_currency)
            our_price_local = self.pricing_service.convert_from_usd(our_price_usd, local_currency)
            difference_local = self.pricing_service.convert_from_usd(difference_usd, local_currency)
            
            # Convert max allowable budget to local currency for display
            max_allowable_local = self.pricing_service.convert_from_usd(max_allowable_usd, local_currency)
            
            # Apply location-specific negotiation approach WITH strict budget constraints (15% max)
            if session.influencer_profile.location.value.lower() == "india":
                # Indian market approach - more collaborative and relationship-focused
                if counter_price_usd > max_allowable_usd:
                    analysis_response = f"I really appreciate your expertise and value! However, our campaign budget allows for a maximum of {self.pricing_service.format_currency(max_allowable_local, local_currency)} (including our 15% negotiation flexibility). We'd love to find a creative way to work within this constraint."
                    compromise_suggestion = f"Could we structure this at {self.pricing_service.format_currency(max_allowable_local, local_currency)} with added benefits like portfolio showcase opportunities, long-term partnership rates, or performance bonuses that don't impact the base budget?"
                elif counter_price_usd <= brand_budget_usd:
                    analysis_response = "That's within our base budget! We appreciate your understanding of our budget parameters."
                    compromise_suggestion = f"We can definitely work with {self.pricing_service.format_currency(counter_price_local, local_currency)}. This demonstrates our mutual commitment to a successful partnership."
                else:
                    # Between budget and max allowable
                    analysis_response = "That's a very reasonable request within our negotiation range! We appreciate your professional approach to this discussion."
                    compromise_suggestion = f"I think we can make {self.pricing_service.format_currency(counter_price_local, local_currency)} work. This demonstrates our commitment to building a long-term partnership with you."
            
            elif negotiation_strategy["cultural_context"] == "direct":
                # US/Western direct approach
                if counter_price_usd > max_allowable_usd:
                    analysis_response = f"Your rate exceeds our maximum budget flexibility of {self.pricing_service.format_currency(max_allowable_local, local_currency)} (15% above our allocated budget). We need to stay within these constraints."
                    compromise_suggestion = f"Our maximum flexibility is {self.pricing_service.format_currency(max_allowable_local, local_currency)}. Can we add value through extended usage rights or performance incentives instead?"
                elif counter_price_usd <= brand_budget_usd:
                    analysis_response = "This is within our base budget allocation. We can work with this rate."
                    compromise_suggestion = f"Let's move forward with {self.pricing_service.format_currency(counter_price_local, local_currency)}. This represents good value for both parties."
                else:
                    # Between budget and max allowable
                    analysis_response = "That's within our negotiation range. We can work with this."
                    compromise_suggestion = f"Let's settle on {self.pricing_service.format_currency(counter_price_local, local_currency)}. This feels fair for both parties."
            
            elif negotiation_strategy["cultural_context"] in ["warm_relationship", "relationship_respect"]:
                # Relationship-focused markets (Brazil, etc.)
                if counter_price_usd > max_allowable_usd:
                    analysis_response = f"We appreciate you valuing the partnership highly! Our budget allows up to {self.pricing_service.format_currency(max_allowable_local, local_currency)} (15% above our base budget). Let's find a creative solution within this range."
                    compromise_suggestion = f"How about {self.pricing_service.format_currency(max_allowable_local, local_currency)} with relationship-building elements like co-marketing opportunities or exclusive partnership status?"
                elif counter_price_usd <= brand_budget_usd:
                    analysis_response = "This fits perfectly within our budget! We love working with creators who understand budget considerations."
                    compromise_suggestion = f"What if we start with {self.pricing_service.format_currency(counter_price_local, local_currency)} for this campaign and explore even better rates for future collaborations as our partnership grows?"
                else:
                    # Between budget and max allowable
                    analysis_response = "Perfect! We love working with creators who value mutual success."
                    compromise_suggestion = f"{self.pricing_service.format_currency(counter_price_local, local_currency)} sounds like a great foundation for our partnership."
            
            else:
                # Default approach with strict budget constraints
                if counter_price_usd > max_allowable_usd:
                    analysis_response = f"This exceeds our maximum budget flexibility of {self.pricing_service.format_currency(max_allowable_local, local_currency)} (15% above our allocated budget)."
                    compromise_suggestion = f"Our flexibility extends to {self.pricing_service.format_currency(max_allowable_local, local_currency)}. Can we find additional value to justify this investment?"
                elif counter_price_usd <= brand_budget_usd:
                    analysis_response = "This fits within our base budget allocation."
                    compromise_suggestion = f"We can work with {self.pricing_service.format_currency(counter_price_local, local_currency)}. This represents good value for the collaboration."
                else:
                    # Between budget and max allowable
                    analysis_response = "That's a reasonable request within our negotiation range."
                    compromise_suggestion = f"How about we meet at {self.pricing_service.format_currency(counter_price_local, local_currency)}?"
        
        else:
            analysis_response = "I'd love to work with your pricing preferences."
            compromise_suggestion = "Could you share your preferred rate structure? I'm confident we can find a solution that works for everyone within our budget constraints."
            counter_price_local = our_price_local
            difference_local = 0
        
        # Format currency values for display
        counter_price_formatted = self.pricing_service.format_currency(counter_price_local, local_currency)
        our_price_formatted = self.pricing_service.format_currency(our_price_local, local_currency)
        difference_formatted = self.pricing_service.format_currency(difference_local, local_currency)
        
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
