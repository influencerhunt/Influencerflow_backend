"""
User models for the InfluencerFlow application.
"""

from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    BRAND = "brand"
    INFLUENCER = "influencer"
    USER = "user"


@dataclass
class User:
    """User model with authentication and profile information."""
    username: str
    email: str  # Using str instead of EmailStr
    id: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Profile information
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    # Social media handles
    instagram_handle: Optional[str] = None
    youtube_handle: Optional[str] = None
    linkedin_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    twitter_handle: Optional[str] = None
    
    # Influencer-specific fields
    follower_count: Optional[int] = None
    engagement_rate: Optional[float] = None
    niches: Optional[List[str]] = None
    
    # Brand-specific fields
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    
    def __post_init__(self):
        """Validate fields after initialization."""
        if self.engagement_rate is not None and (self.engagement_rate < 0 or self.engagement_rate > 100):
            raise ValueError('Engagement rate must be between 0 and 100')
        if self.follower_count is not None and self.follower_count < 0:
            raise ValueError('Follower count must be non-negative')
        if self.niches is None:
            self.niches = []


@dataclass
class UserCreate:
    """Model for creating a new user."""
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER


@dataclass
class UserUpdate:
    """Model for updating user information."""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Social media handles
    instagram_handle: Optional[str] = None
    youtube_handle: Optional[str] = None
    linkedin_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    twitter_handle: Optional[str] = None
    
    # Influencer-specific fields
    follower_count: Optional[int] = None
    engagement_rate: Optional[float] = None
    niches: Optional[List[str]] = None
    
    # Brand-specific fields
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None


@dataclass
class UserResponse:
    """Model for user response (excludes sensitive information)."""
    id: str
    email: str
    username: str
    role: UserRole
    is_active: bool
    is_verified: bool
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Profile information
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    # Social media handles
    instagram_handle: Optional[str] = None
    youtube_handle: Optional[str] = None
    linkedin_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    twitter_handle: Optional[str] = None
    
    # Influencer-specific fields
    follower_count: Optional[int] = None
    engagement_rate: Optional[float] = None
    niches: Optional[List[str]] = None
    
    # Brand-specific fields
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
