from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class PlatformType(str, Enum):
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    TWITTER = "twitter"

class ContentType(str, Enum):
    # Instagram
    INSTAGRAM_POST = "post"
    INSTAGRAM_REEL = "reel"
    INSTAGRAM_STORY = "story"
    
    # YouTube
    YOUTUBE_LONG_FORM = "long_form"
    YOUTUBE_SHORTS = "shorts"
    
    # LinkedIn
    LINKEDIN_POST = "post"
    LINKEDIN_VIDEO = "video"
    
    # TikTok
    TIKTOK_VIDEO = "video"
    
    # Twitter
    TWITTER_POST = "post"
    TWITTER_VIDEO = "video"

class LocationType(str, Enum):
    US = "US"
    UK = "UK"
    CANADA = "Canada"
    AUSTRALIA = "Australia"
    INDIA = "India"
    GERMANY = "Germany"
    FRANCE = "France"
    BRAZIL = "Brazil"
    JAPAN = "Japan"
    OTHER = "Other"

class NegotiationStatus(str, Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COUNTER_OFFER = "counter_offer"
    AGREED = "agreed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

@dataclass
class InfluencerProfile:
    """Influencer's profile information"""
    name: str
    followers: int  # Number of followers (must be > 0)
    engagement_rate: float  # Engagement rate (0-1)
    location: LocationType
    platforms: List[PlatformType]  # Platforms the influencer is active on
    niches: List[str] = field(default_factory=list)  # Influencer's content niches
    previous_brand_collaborations: int = 0  # Number of previous brand collaborations
    
@dataclass
class BrandDetails:
    """Brand campaign details"""
    name: str
    budget: float  # Total budget for the campaign in USD (must be > 0)
    goals: List[str]  # Campaign goals
    target_platforms: List[PlatformType]  # Target platforms for the campaign
    content_requirements: Dict[str, int]  # Required content with quantities
    campaign_duration_days: int = 30  # Campaign duration in days
    target_audience: Optional[str] = None  # Target audience description
    brand_guidelines: Optional[str] = None  # Brand guidelines or requirements
    brand_location: Optional[LocationType] = None  # Brand's location for currency handling
    budget_currency: Optional[str] = None  # Currency for the budget (e.g., "USD", "INR", "EUR")
    original_budget_amount: Optional[float] = None  # Original budget amount in original currency
    
@dataclass
class ContentDeliverable:
    """Individual content deliverable details"""
    platform: PlatformType
    content_type: ContentType
    quantity: int  # Must be > 0
    proposed_price: float
    market_rate: float
    description: Optional[str] = None
    milestones: Optional[List[str]] = None

@dataclass
class NegotiationOffer:
    """Complete negotiation offer"""
    total_price: float
    payment_terms: str = "50% upfront, 50% on completion"
    revisions_included: int = 2
    timeline_days: int = 30
    usage_rights: str = "6 months social media usage"
    currency: Optional[str] = "USD"
    content_breakdown: Optional[Dict[str, any]] = None
    deliverables: Optional[List[ContentDeliverable]] = None
    campaign_duration_days: Optional[int] = None
    exclusivity_period_days: Optional[int] = None
    
@dataclass
class NegotiationState:
    """Current state of negotiation session"""
    session_id: str
    brand_details: BrandDetails
    influencer_profile: InfluencerProfile
    status: NegotiationStatus = NegotiationStatus.INITIATED
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    current_offer: Optional[NegotiationOffer] = None
    counter_offers: List[NegotiationOffer] = field(default_factory=list)
    agreed_terms: Optional[NegotiationOffer] = None
    negotiation_round: int = 1
    
@dataclass
class MarketRateData:
    """Market rate calculation data with location intelligence"""
    base_rate: float = 0.0
    engagement_bonus: float = 0.0
    follower_bonus: float = 0.0
    location_multiplier: float = 1.0
    final_rate: float = 0.0
    currency: str = "USD"
    market_insights: Optional[Dict[str, str]] = field(default_factory=dict)
    
    # Legacy fields for backward compatibility
    platform: Optional[PlatformType] = None
    content_type: Optional[ContentType] = None
    base_rate_per_1k_followers: float = 0.0
    engagement_multiplier: float = 1.0
    
@dataclass
class PlatformConfig:
    """Platform configuration details"""
    name: str
    content_types: List[ContentType]
    base_rates: Dict[ContentType, float]
    engagement_weight: float = 1.0
    follower_weight: float = 1.0

# Contract-related models for contract generation system

class ContractStatus(str, Enum):
    """Contract status enumeration"""
    PENDING_SIGNATURES = "pending_signatures"
    BRAND_SIGNED = "brand_signed"
    INFLUENCER_SIGNED = "influencer_signed"
    FULLY_EXECUTED = "fully_executed"
    CANCELLED = "cancelled"

@dataclass
class DigitalSignature:
    """Digital signature information"""
    signer_name: str
    signer_email: str
    signature_timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class ContractTerms:
    """Contract terms and legal information"""
    contract_id: str
    session_id: str
    brand_name: str
    influencer_name: str
    campaign_title: str
    deliverables: List[ContentDeliverable]
    total_amount: float
    currency: str = "USD"
    campaign_start_date: datetime = field(default_factory=datetime.now)
    campaign_end_date: datetime = field(default_factory=datetime.now)
    contract_date: datetime = field(default_factory=datetime.now)
    payment_terms: str = "50% upfront, 50% on completion"
    usage_rights: str = "6 months social media usage"
    exclusivity_period_days: Optional[int] = None
    revisions_included: int = 2
    status: ContractStatus = ContractStatus.PENDING_SIGNATURES
    brand_signature: Optional[DigitalSignature] = None
    influencer_signature: Optional[DigitalSignature] = None
    brand_contact_email: Optional[str] = None
    brand_contact_name: Optional[str] = None
    influencer_email: Optional[str] = None
    influencer_contact: Optional[str] = None
    campaign_description: Optional[str] = None
    cancellation_policy: Optional[str] = None
    dispute_resolution: Optional[str] = None
    governing_law: Optional[str] = None
    legal_terms: Optional[str] = None
