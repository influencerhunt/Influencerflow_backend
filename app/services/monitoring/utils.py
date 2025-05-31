import re
from typing import List

def extract_hashtags(text: str) -> List[str]:
    """Extract all hashtags from a given string."""
    return re.findall(r"#\w+", text)

def match_hashtags(description: str, campaign_tags: List[str]) -> List[str]:
    """Returns matching hashtags found in description."""
    description_tags = extract_hashtags(description.lower())
    return [tag for tag in campaign_tags if tag.lower() in description_tags]

def get_token_for_influencer(influencer_id: str, platform: str) -> str:
    """
    Placeholder: Replace this with DB lookup or token store logic.
    Currently fetching from env for simplicity.
    """
    import os
    if platform == "youtube":
        return os.getenv("YOUTUBE_ACCESS_TOKEN")
    elif platform == "instagram":
        return os.getenv("INSTAGRAM_ACCESS_TOKEN")
    else:
        raise ValueError("Unsupported platform")
