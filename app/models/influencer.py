from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

class PlatformType(str, Enum):
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"

class InfluencerSource(str, Enum):
    ON_PLATFORM = "on_platform"
    EXTERNAL = "external"

@dataclass
class Influencer:
    name: str
    username: str
    platform: PlatformType
    followers: int
    source: InfluencerSource
    id: Optional[str] = None
    engagement_rate: Optional[float] = None
    price_per_post: Optional[int] = None
    location: Optional[str] = None
    niche: Optional[str] = None
    bio: Optional[str] = None
    profile_link: Optional[str] = None
    avatar_url: Optional[str] = None
    verified: Optional[bool] = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self):
        """Convert dataclass to dictionary for JSON serialization"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result

@dataclass
class SearchFilters:
    location: Optional[str] = None
    niche: Optional[str] = None
    platform: Optional[PlatformType] = None
    followers_min: Optional[int] = None
    followers_max: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    engagement_min: Optional[float] = None
    engagement_max: Optional[float] = None
    verified_only: Optional[bool] = False
    
    def to_dict(self):
        """Convert dataclass to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result

@dataclass
class SearchRequest:
    query: str
    filters: Optional[SearchFilters] = None
    limit: Optional[int] = 20
    include_external: Optional[bool] = True
    
    def __post_init__(self):
        # Validate limit
        if self.limit and self.limit > 100:
            self.limit = 100
        elif self.limit and self.limit < 1:
            self.limit = 1

@dataclass
class SearchResponse:
    query: str
    total_results: int
    on_platform_count: int
    external_count: int
    on_platform_influencers: List[Influencer]
    external_influencers: List[Influencer]
    parsed_filters: Optional[SearchFilters] = None
    
    def to_dict(self):
        """Convert search response to dictionary for JSON serialization"""
        response_dict = {
            "query": self.query,
            "total_results": self.total_results,
            "on_platform_count": self.on_platform_count,
            "external_count": self.external_count,
            "on_platform_influencers": [influencer.to_dict() for influencer in self.on_platform_influencers],
            "external_influencers": [influencer.to_dict() for influencer in self.external_influencers],
            # Legacy field for backward compatibility
            "influencers": [influencer.to_dict() for influencer in (self.on_platform_influencers + self.external_influencers)]
        }
        
        # Add parsed filters if available
        if self.parsed_filters:
            response_dict["parsed_filters"] = self.parsed_filters.to_dict()
        
        return response_dict
