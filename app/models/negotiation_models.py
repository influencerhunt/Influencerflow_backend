from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

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
    budget: float  # Total budget for the campaign (must be > 0)
    goals: List[str]  # Campaign goals
    target_platforms: List[PlatformType]  # Target platforms for the campaign
    content_requirements: Dict[str, int]  # Required content with quantities
    campaign_duration_days: int = 30  # Campaign duration in days
    target_audience: Optional[str] = None  # Target audience description
    brand_guidelines: Optional[str] = None  # Brand guidelines or requirements
    
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
    deliverables: List[ContentDeliverable]
    campaign_duration_days: int
    payment_terms: str = "50% upfront, 50% on completion"
    revisions_included: int = 2
    exclusivity_period_days: Optional[int] = None
    usage_rights: str = "6 months social media usage"
    
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
    """Market rate calculation data"""
    platform: PlatformType
    content_type: ContentType
    base_rate_per_1k_followers: float
    engagement_multiplier: float
    location_multiplier: float
    final_rate: float
    
@dataclass
class PlatformConfig:
    """Platform configuration details"""
    name: str
    content_types: List[ContentType]
    base_rates: Dict[ContentType, float]
    engagement_weight: float = 1.0
    follower_weight: float = 1.0
