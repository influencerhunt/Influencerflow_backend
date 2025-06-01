"""
Pydantic models for negotiation agent functionality
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

# ==================== ENUMS ====================

class PlatformType(str, Enum):
    """Social media platform types"""
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    SNAPCHAT = "snapchat"
    PINTEREST = "pinterest"

class LocationType(str, Enum):
    """Location types for targeting"""
    INDIA = "india"
    USA = "usa"
    UK = "uk"
    CANADA = "canada"
    AUSTRALIA = "australia"
    GERMANY = "germany"
    FRANCE = "france"
    BRAZIL = "brazil"
    JAPAN = "japan"
    GLOBAL = "global"

class NegotiationStatus(str, Enum):
    """Negotiation session status"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COUNTER_OFFER = "counter_offer"
    AGREED = "agreed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    CONTRACT_GENERATED = "contract_generated"
    ARCHIVED = "archived"

class ContentType(str, Enum):
    """Content types for deliverables"""
    POSTS = "posts"
    STORIES = "stories"
    REELS = "reels"
    VIDEOS = "videos"
    LINKEDIN_POSTS = "linkedin_posts"
    TIKTOK_VIDEOS = "tiktok_videos"
    BLOG_POSTS = "blog_posts"

# ==================== CORE MODELS ====================

class BrandDetails(BaseModel):
    """Brand details for negotiation"""
    name: str = Field(..., description="Brand name")
    budget: float = Field(..., description="Budget amount in base currency", gt=0)
    budget_currency: str = Field(default="USD", description="Budget currency code")
    goals: List[str] = Field(..., description="Campaign goals")
    target_platforms: List[PlatformType] = Field(..., description="Target social media platforms")
    content_requirements: Dict[str, int] = Field(..., description="Content requirements breakdown")
    campaign_duration_days: int = Field(..., description="Campaign duration in days", gt=0)
    target_audience: str = Field(..., description="Target audience description")
    brand_guidelines: str = Field(..., description="Brand guidelines and requirements")
    brand_location: LocationType = Field(default=LocationType.GLOBAL, description="Brand location")

    class Config:
        use_enum_values = True

class InfluencerProfile(BaseModel):
    """Influencer profile for negotiation"""
    name: str = Field(..., description="Influencer name")
    followers: int = Field(..., description="Number of followers", ge=0)
    engagement_rate: float = Field(..., description="Engagement rate percentage", ge=0, le=100)
    location: LocationType = Field(..., description="Influencer location")
    platforms: List[PlatformType] = Field(..., description="Platforms the influencer is active on")
    niches: List[str] = Field(..., description="Content niches/categories")
    previous_brand_collaborations: int = Field(default=0, description="Number of previous brand collaborations", ge=0)

    class Config:
        use_enum_values = True

class DeliverableUpdate(BaseModel):
    """Update to deliverables during negotiation"""
    content_type: ContentType = Field(..., description="Type of content")
    quantity: int = Field(..., description="Number of deliverables", gt=0)
    platform: PlatformType = Field(..., description="Platform for the content")
    additional_requirements: Optional[str] = Field(None, description="Additional requirements")

    class Config:
        use_enum_values = True

class BudgetChange(BaseModel):
    """Budget change during negotiation"""
    new_amount: float = Field(..., description="New budget amount", gt=0)
    reason: str = Field(..., description="Reason for budget change")
    currency: str = Field(default="USD", description="Currency code")

class ContractTerms(BaseModel):
    """Contract terms for the deal"""
    total_amount: float = Field(..., description="Total contract amount", gt=0)
    currency: str = Field(default="USD", description="Currency code")
    deliverables: List[DeliverableUpdate] = Field(..., description="Agreed deliverables")
    campaign_duration: int = Field(..., description="Campaign duration in days", gt=0)
    start_date: Optional[datetime] = Field(None, description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")
    payment_terms: str = Field(..., description="Payment terms and conditions")
    additional_terms: Optional[str] = Field(None, description="Additional contract terms")

# ==================== SESSION MODELS ====================

class NegotiationSession(BaseModel):
    """Complete negotiation session data"""
    session_id: str = Field(..., description="Unique session identifier")
    brand_details: BrandDetails = Field(..., description="Brand information")
    influencer_profile: InfluencerProfile = Field(..., description="Influencer information")
    status: NegotiationStatus = Field(default=NegotiationStatus.INITIATED, description="Current session status")
    current_offer: Optional[float] = Field(None, description="Current offer amount")
    max_budget: Optional[float] = Field(None, description="Maximum negotiable budget")
    deliverables_agreed: Dict[str, Any] = Field(default_factory=dict, description="Agreed deliverables")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")

    class Config:
        use_enum_values = True

class NegotiationMessage(BaseModel):
    """Individual message in negotiation"""
    session_id: str = Field(..., description="Session identifier")
    speaker: str = Field(..., description="Message speaker (agent/influencer)")
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message metadata")

# ==================== ANALYTICS MODELS ====================

class SessionAnalytics(BaseModel):
    """Analytics data for a negotiation session"""
    session_id: str = Field(..., description="Session identifier")
    status: NegotiationStatus = Field(..., description="Session status")
    duration_minutes: Optional[float] = Field(None, description="Session duration in minutes")
    message_count: int = Field(default=0, description="Total messages exchanged")
    offer_count: int = Field(default=0, description="Number of offers made")
    final_amount: Optional[float] = Field(None, description="Final agreed amount")
    budget_utilization: Optional[float] = Field(None, description="Budget utilization percentage")
    success_rate: Optional[float] = Field(None, description="Success probability")

    class Config:
        use_enum_values = True

class GlobalAnalytics(BaseModel):
    """Global analytics across all sessions"""
    total_sessions: int = Field(default=0, description="Total number of sessions")
    successful_sessions: int = Field(default=0, description="Number of successful sessions")
    failed_sessions: int = Field(default=0, description="Number of failed sessions")
    average_duration_minutes: Optional[float] = Field(None, description="Average session duration")
    average_budget_utilization: Optional[float] = Field(None, description="Average budget utilization")
    success_rate: Optional[float] = Field(None, description="Overall success rate")
    popular_platforms: List[str] = Field(default_factory=list, description="Most popular platforms")
    popular_locations: List[str] = Field(default_factory=list, description="Most popular locations")

# ==================== CONTRACT MODELS ====================

class ContractData(BaseModel):
    """Contract data for PDF generation"""
    brand_name: str = Field(..., description="Brand name")
    influencer_name: str = Field(..., description="Influencer name")
    agreed_amount: float = Field(..., description="Agreed amount", gt=0)
    agreed_deliverables: Dict[str, Any] = Field(..., description="Agreed deliverables")
    campaign_duration_days: int = Field(..., description="Campaign duration", gt=0)
    platforms: List[str] = Field(..., description="Platforms involved")
    contract_terms: str = Field(..., description="Contract terms text")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ContractResponse(BaseModel):
    """Response model for contract operations"""
    contract_id: str = Field(..., description="Unique contract identifier")
    session_id: str = Field(..., description="Associated session ID")
    status: str = Field(..., description="Contract status")
    pdf_url: Optional[str] = Field(None, description="PDF download URL")
    created_at: datetime = Field(..., description="Contract creation time")
    contract_data: ContractData = Field(..., description="Contract details")

# ==================== UTILITY MODELS ====================

class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")

class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    success: bool = Field(..., description="Operation success status")
    data: List[Dict[str, Any]] = Field(..., description="Response data")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    version: str = Field(default="1.0.0", description="API version")
    services: Dict[str, str] = Field(default_factory=dict, description="Service statuses")

# ==================== VALIDATION HELPERS ====================

def validate_budget_range(budget: float, currency: str = "USD") -> bool:
    """Validate budget is within reasonable range"""
    min_budgets = {"USD": 100, "EUR": 90, "GBP": 80, "INR": 8000, "CAD": 130}
    max_budgets = {"USD": 1000000, "EUR": 900000, "GBP": 800000, "INR": 80000000, "CAD": 1300000}
    
    min_budget = min_budgets.get(currency, 100)
    max_budget = max_budgets.get(currency, 1000000)
    
    return min_budget <= budget <= max_budget

def validate_engagement_rate(rate: float) -> bool:
    """Validate engagement rate is realistic"""
    return 0.1 <= rate <= 20.0  # 0.1% to 20% is realistic range

def validate_follower_count(followers: int, platform: str) -> bool:
    """Validate follower count is realistic for platform"""
    min_followers = {"instagram": 100, "youtube": 50, "tiktok": 100, "twitter": 50}
    max_followers = 500000000  # 500M max for any platform
    
    min_count = min_followers.get(platform.lower(), 50)
    return min_count <= followers <= max_followers
