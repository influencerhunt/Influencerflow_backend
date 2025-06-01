from pydantic import BaseModel
from typing import List, Optional, Dict

class MetricsRequest(BaseModel):
    platform: str  
    influencer_id: str  
    campaign_name: Optional[str] = None
    hashtags: Optional[List[str]] = []

class PostMetrics(BaseModel):
    platform: str
    post_id: str
    url: str
    hashtags_found: List[str]
    metrics: Dict[str, float]

class MetricsResponse(BaseModel):
    campaign: Optional[str]
    verified_posts: List[PostMetrics]
