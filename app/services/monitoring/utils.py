import re
from typing import List
from datetime import datetime, timedelta
import dateutil.relativedelta as rd

def extract_hashtags(text: str) -> List[str]:
    """Extract all hashtags from a given string."""
    return re.findall(r"#\w+", text)

def match_hashtags(description: str, campaign_tags: List[str]) -> List[str]:
    """Returns matching hashtags found in description."""
    description_tags = extract_hashtags(description.lower())
    return [tag for tag in campaign_tags if tag.lower() in description_tags]

def get_start_date(duration: str) -> str:
    now = datetime.utcnow()
    if duration.endswith("d"):
        delta = timedelta(days=int(duration[:-1]))
    elif duration.endswith("m"):
        delta = rd.relativedelta(months=int(duration[:-1]))
    elif duration.endswith("y"):
        delta = rd.relativedelta(years=int(duration[:-1]))
    else:
        raise ValueError("Invalid duration format. Use '7d', '2m', or '1y'.")
    return (now - delta).isoformat("T") + "Z"
