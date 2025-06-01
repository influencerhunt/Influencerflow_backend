from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime
from dataclasses import asdict, fields
from app.services.supabase import SupabaseService
from app.models.negotiation_models import (
    NegotiationState, BrandDetails, InfluencerProfile, 
    NegotiationOffer, NegotiationStatus, PlatformType, LocationType
)

logger = logging.getLogger(__name__)

class NegotiationSessionService:
    """Service for managing negotiation sessions in Supabase database"""
    
    @classmethod
    def _serialize_dataclass(cls, obj: Any) -> Any:
        """Serialize dataclass objects to JSON-serializable format"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field in fields(obj):
                value = getattr(obj, field.name)
                if hasattr(value, '__dataclass_fields__'):
                    result[field.name] = cls._serialize_dataclass(value)
                elif isinstance(value, list):
                    result[field.name] = [cls._serialize_dataclass(item) if hasattr(item, '__dataclass_fields__') else 
                                        item.value if hasattr(item, 'value') else item for item in value]
                elif hasattr(value, 'value'):  # Enum
                    result[field.name] = value.value
                else:
                    result[field.name] = value
            return result
        elif hasattr(obj, 'value'):  # Enum
            return obj.value
        else:
            return obj
    
    @classmethod
    def _deserialize_brand_details(cls, data: Dict[str, Any]) -> BrandDetails:
        """Deserialize brand details from database"""
        # Convert platform strings back to enums
        target_platforms = []
        if 'target_platforms' in data and data['target_platforms']:
            target_platforms = [PlatformType(platform) for platform in data['target_platforms']]
        
        brand_location = None
        if 'brand_location' in data and data['brand_location']:
            brand_location = LocationType(data['brand_location'])
        
        return BrandDetails(
            name=data.get('name', ''),
            budget=float(data.get('budget', 0)),
            goals=data.get('goals', []),
            target_platforms=target_platforms,
            content_requirements=data.get('content_requirements', {}),
            campaign_duration_days=data.get('campaign_duration_days', 30),
            target_audience=data.get('target_audience'),
            brand_guidelines=data.get('brand_guidelines'),
            brand_location=brand_location,
            budget_currency=data.get('budget_currency'),
            original_budget_amount=data.get('original_budget_amount')
        )
    
    @classmethod
    def _deserialize_influencer_profile(cls, data: Dict[str, Any]) -> InfluencerProfile:
        """Deserialize influencer profile from database"""
        # Convert platform strings back to enums
        platforms = []
        if 'platforms' in data and data['platforms']:
            platforms = [PlatformType(platform) for platform in data['platforms']]
        
        location = LocationType.OTHER
        if 'location' in data and data['location']:
            location = LocationType(data['location'])
        
        return InfluencerProfile(
            name=data.get('name', ''),
            followers=int(data.get('followers', 0)),
            engagement_rate=float(data.get('engagement_rate', 0)),
            location=location,
            platforms=platforms,
            niches=data.get('niches', []),
            previous_brand_collaborations=data.get('previous_brand_collaborations', 0)
        )
    
    @classmethod
    def _deserialize_negotiation_offer(cls, data: Optional[Dict[str, Any]]) -> Optional[NegotiationOffer]:
        """Deserialize negotiation offer from database"""
        if not data:
            return None
        
        return NegotiationOffer(
            total_price=float(data.get('total_price', 0)),
            payment_terms=data.get('payment_terms', '50% upfront, 50% on completion'),
            revisions_included=data.get('revisions_included', 2),
            timeline_days=data.get('timeline_days', 30),
            usage_rights=data.get('usage_rights', '6 months social media usage'),
            currency=data.get('currency', 'USD'),
            content_breakdown=data.get('content_breakdown'),
            deliverables=data.get('deliverables'),
            campaign_duration_days=data.get('campaign_duration_days'),
            exclusivity_period_days=data.get('exclusivity_period_days')
        )
    
    @classmethod
    async def create_session(
        cls, 
        session_id: str,
        brand_details: BrandDetails, 
        influencer_profile: InfluencerProfile,
        user_id: Optional[str] = None
    ) -> str:
        """Create a new negotiation session in the database"""
        try:
            client = SupabaseService.get_client()
            
            # Serialize the dataclass objects
            brand_data = cls._serialize_dataclass(brand_details)
            influencer_data = cls._serialize_dataclass(influencer_profile)
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'brand_details': brand_data,
                'influencer_profile': influencer_data,
                'status': NegotiationStatus.INITIATED.value,
                'negotiation_round': 1,
                'conversation_history': []
            }
            
            result = client.table('negotiation_sessions').insert(session_data).execute()
            
            if result.data:
                logger.info(f"Created negotiation session {session_id} in database")
                return session_id
            else:
                raise Exception("Failed to create session in database")
                
        except Exception as e:
            logger.error(f"Error creating session in database: {e}")
            raise e
    
    @classmethod
    async def get_session(cls, session_id: str, user_id: Optional[str] = None) -> Optional[NegotiationState]:
        """Retrieve a negotiation session from the database"""
        try:
            client = SupabaseService.get_client()
            
            query = client.table('negotiation_sessions').select("*").eq('session_id', session_id)
            
            # If user_id is provided, add it to the query for security
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            if not result.data:
                return None
            
            session_data = result.data[0]
            
            # Deserialize the data back to dataclass objects
            brand_details = cls._deserialize_brand_details(session_data['brand_details'])
            influencer_profile = cls._deserialize_influencer_profile(session_data['influencer_profile'])
            
            current_offer = cls._deserialize_negotiation_offer(session_data.get('current_offer'))
            agreed_terms = cls._deserialize_negotiation_offer(session_data.get('agreed_terms'))
            
            # Deserialize counter offers
            counter_offers = []
            if session_data.get('counter_offers'):
                for offer_data in session_data['counter_offers']:
                    offer = cls._deserialize_negotiation_offer(offer_data)
                    if offer:
                        counter_offers.append(offer)
            
            return NegotiationState(
                session_id=session_data['session_id'],
                brand_details=brand_details,
                influencer_profile=influencer_profile,
                status=NegotiationStatus(session_data['status']),
                conversation_history=session_data.get('conversation_history', []),
                current_offer=current_offer,
                counter_offers=counter_offers,
                agreed_terms=agreed_terms,
                negotiation_round=session_data.get('negotiation_round', 1)
            )
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    @classmethod
    async def update_session(cls, session: NegotiationState, user_id: Optional[str] = None) -> bool:
        """Update a negotiation session in the database"""
        try:
            client = SupabaseService.get_client()
            
            # Serialize the data
            current_offer_data = None
            if session.current_offer:
                current_offer_data = cls._serialize_dataclass(session.current_offer)
            
            agreed_terms_data = None
            if session.agreed_terms:
                agreed_terms_data = cls._serialize_dataclass(session.agreed_terms)
            
            counter_offers_data = []
            for offer in session.counter_offers:
                counter_offers_data.append(cls._serialize_dataclass(offer))
            
            update_data = {
                'status': session.status.value,
                'negotiation_round': session.negotiation_round,
                'conversation_history': session.conversation_history,
                'current_offer': current_offer_data,
                'counter_offers': counter_offers_data,
                'agreed_terms': agreed_terms_data,
                'last_activity_at': datetime.now().isoformat()
            }
            
            query = client.table('negotiation_sessions').update(update_data).eq('session_id', session.session_id)
            
            # If user_id is provided, add it to the query for security
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            if result.data:
                logger.info(f"Updated negotiation session {session.session_id}")
                return True
            else:
                logger.warning(f"No session updated for {session.session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating session {session.session_id}: {e}")
            return False
    
    @classmethod
    async def delete_session(cls, session_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a negotiation session from the database"""
        try:
            client = SupabaseService.get_client()
            
            query = client.table('negotiation_sessions').delete().eq('session_id', session_id)
            
            # If user_id is provided, add it to the query for security
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            if result.data:
                logger.info(f"Deleted negotiation session {session_id}")
                return True
            else:
                logger.warning(f"No session deleted for {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    @classmethod
    async def list_user_sessions(
        cls, 
        user_id: str, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List negotiation sessions for a user"""
        try:
            client = SupabaseService.get_client()
            
            query = client.table('negotiation_session_summaries').select("*").eq('user_id', user_id)
            
            if status:
                query = query.eq('status', status)
            
            query = query.order('last_activity_at', desc=True).range(offset, offset + limit - 1)
            
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error listing sessions for user {user_id}: {e}")
            return []
    
    @classmethod
    async def add_message_to_conversation(
        cls, 
        session_id: str, 
        role: str, 
        message: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Add a message to the conversation history"""
        try:
            # First, get the current session
            session = await cls.get_session(session_id, user_id)
            if not session:
                return False
            
            # Add the new message
            new_message = {
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            session.conversation_history.append(new_message)
            
            # Update the session
            return await cls.update_session(session, user_id)
            
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False
    
    @classmethod
    async def get_conversation_history(
        cls, 
        session_id: str, 
        user_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        try:
            session = await cls.get_session(session_id, user_id)
            return session.conversation_history if session else []
            
        except Exception as e:
            logger.error(f"Error getting conversation history for {session_id}: {e}")
            return []
    
    @classmethod
    async def cleanup_old_sessions(cls, days: int = 30) -> int:
        """Clean up old inactive sessions"""
        try:
            client = SupabaseService.get_admin_client()
            
            # Call the cleanup function
            result = client.rpc('cleanup_old_negotiation_sessions').execute()
            
            logger.info("Cleaned up old negotiation sessions")
            return 0  # Supabase RPC doesn't return count easily
            
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")
            return 0

# Create a global instance
negotiation_session_service = NegotiationSessionService()
