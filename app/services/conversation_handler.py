from typing import Dict, List, Optional, Any
import json
import uuid
from datetime import datetime
from app.models.negotiation_models import (
    NegotiationState, BrandDetails, InfluencerProfile, 
    NegotiationOffer, ContentDeliverable, NegotiationStatus,
    PlatformType, ContentType
)
from app.services.pricing_service import PricingService
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
💰 **Our Budget**: ${budget:,.2f}
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

**Our Total Offer**: ${total_value:,.2f}

This offer reflects our research into fair market pricing while aligning with our campaign budget. We believe this compensation recognizes your value while allowing us to achieve our marketing objectives.

What are your thoughts on this proposal?""",

            "proposal": """Here's our formal collaboration proposal:

📋 **Deliverables & Compensation**:
{deliverables_breakdown}

💰 **Total Compensation**: ${total_price:,.2f}
💳 **Payment Terms**: {payment_terms}
🔄 **Revisions**: {revisions} included per deliverable
📅 **Timeline**: {duration} days
🔒 **Usage Rights**: {usage_rights}

This proposal has been carefully crafted to offer competitive compensation while fitting within {brand_name}'s campaign budget. We're committed to a successful partnership and believe this structure sets us both up for success.

Would you like to move forward with these terms, or are there specific aspects you'd like to discuss?""",

            "counter_offer_response": """Thank you for your counter-proposal. Let me review this with our team's perspective:

**Your Request**: ${counter_price:,.2f}
**Our Budget**: ${our_price:,.2f}
**Gap**: ${difference:,.2f}

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
        
        # Create content summary
        content_summary = []
        for content_type, quantity in brand.content_requirements.items():
            content_summary.append(f"{quantity}x {content_type.replace('_', ' ').title()}")
        
        message = self.conversation_templates["greeting"].format(
            brand_name=brand.name,
            goals=", ".join(brand.goals),
            budget=brand.budget,
            platforms=", ".join([p.value.title() for p in brand.target_platforms]),
            content_summary=", ".join(content_summary),
            duration=brand.campaign_duration_days
        )
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def generate_market_analysis(self, session_id: str) -> str:
        """Generate market analysis message."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # Calculate market rates
        cost_breakdown = self.pricing_service.calculate_total_campaign_cost(
            influencer, brand.content_requirements
        )
        
        # Format rate breakdown
        rate_breakdown_lines = []
        for content_type, details in cost_breakdown["item_breakdown"].items():
            content_display = content_type.replace('_', ' ').title()
            rate_breakdown_lines.append(
                f"• {content_display}: ${details['unit_rate']:.2f} × {details['quantity']} = ${details['total']:.2f}"
            )
        
        message = self.conversation_templates["market_analysis"].format(
            followers=influencer.followers,
            engagement_rate=influencer.engagement_rate,
            location=influencer.location.value,
            platforms=", ".join([p.value.title() for p in influencer.platforms]),
            rate_breakdown="\n".join(rate_breakdown_lines),
            total_value=cost_breakdown["total_cost"]
        )
        
        self._add_to_conversation(session_id, "assistant", message)
        return message

    def generate_proposal(self, session_id: str) -> str:
        """Generate formal proposal message."""
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found."
        
        influencer = session.influencer_profile
        brand = session.brand_details
        
        # Calculate pricing
        cost_breakdown = self.pricing_service.calculate_total_campaign_cost(
            influencer, brand.content_requirements
        )
        
        # Create deliverables
        deliverables = []
        for content_type, details in cost_breakdown["item_breakdown"].items():
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
        
        # Create offer
        offer = NegotiationOffer(
            total_price=cost_breakdown["total_cost"],
            deliverables=deliverables,
            campaign_duration_days=brand.campaign_duration_days,
            payment_terms="50% upfront, 50% on completion",
            revisions_included=2,
            usage_rights="6 months social media usage"
        )
        
        session.current_offer = offer
        session.status = NegotiationStatus.IN_PROGRESS
        
        # Format deliverables breakdown
        deliverables_lines = []
        for deliverable in deliverables:
            platform_name = deliverable.platform.value.title()
            content_name = deliverable.content_type.value.replace('_', ' ').title()
            deliverables_lines.append(
                f"• {platform_name} {content_name} × {deliverable.quantity}: ${deliverable.proposed_price:.2f}"
            )
        
        message = self.conversation_templates["proposal"].format(
            deliverables_breakdown="\n".join(deliverables_lines),
            total_price=offer.total_price,
            payment_terms=offer.payment_terms,
            revisions=offer.revisions_included,
            duration=offer.campaign_duration_days,
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
        
        # Format final terms
        final_terms_lines = []
        if session.current_offer:
            for deliverable in session.current_offer.deliverables:
                platform_name = deliverable.platform.value.title()
                content_name = deliverable.content_type.value.replace('_', ' ').title()
                final_terms_lines.append(
                    f"• {platform_name} {content_name} × {deliverable.quantity}: ${deliverable.proposed_price:.2f}"
                )
            
            final_terms_lines.extend([
                f"• Total Investment: ${session.current_offer.total_price:.2f}",
                f"• Payment Terms: {session.current_offer.payment_terms}",
                f"• Campaign Duration: {session.current_offer.campaign_duration_days} days",
                f"• Usage Rights: {session.current_offer.usage_rights}"
            ])
        
        message = self.conversation_templates["agreement"].format(
            final_terms="\n".join(final_terms_lines),
            brand_name=session.brand_details.name
        )
        
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
        """Handle counter offer from user."""
        session = self.active_sessions[session_id]
        session.status = NegotiationStatus.COUNTER_OFFER
        session.negotiation_round += 1
        
        # Try to extract price from user input
        import re
        price_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', user_input.replace(',', ''))
        counter_price = float(price_match.group(1)) if price_match else None
        
        our_price = session.current_offer.total_price if session.current_offer else 0
        
        if counter_price:
            difference = abs(counter_price - our_price)
            
            if counter_price < our_price * 0.7:  # More than 30% below our offer
                analysis_response = "I understand you're looking for a more budget-friendly option. However, this price point is significantly below market rates for your audience quality and the deliverables requested."
                compromise_suggestion = f"Would you be open to a middle ground around ${(our_price + counter_price) / 2:.2f}? We could also adjust the deliverables to better fit your preferred budget."
            
            elif counter_price > our_price * 1.3:  # More than 30% above our offer
                analysis_response = "I appreciate you valuing your content highly! However, this pricing exceeds the brand's allocated budget for this campaign."
                compromise_suggestion = f"Could we explore a structure around ${min(counter_price, our_price * 1.15):.2f} with some additional value-adds like extended usage rights or bonus content?"
            
            else:  # Within reasonable range
                analysis_response = "That's definitely within a reasonable negotiation range. I can see how we might work with this."
                compromise_suggestion = f"How about we meet at ${(our_price + counter_price) / 2:.2f}? This feels like a fair middle ground that respects both your expertise and the brand's budget."
        
        else:
            analysis_response = "I'd love to work with your pricing preferences."
            compromise_suggestion = "Could you share your preferred rate structure? I'm confident we can find a solution that works for everyone."
            counter_price = our_price
            difference = 0
        
        message = self.conversation_templates["counter_offer_response"].format(
            counter_price=counter_price,
            our_price=our_price,
            difference=difference,
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
