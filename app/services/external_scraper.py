import requests
import json
from typing import List, Dict, Any
from decouple import config
from bs4 import BeautifulSoup
import re
from app.models.influencer import Influencer, SearchFilters, InfluencerSource, PlatformType

class ExternalInfluencerScraper:
    def __init__(self):
        self.serper_api_key = config("SERPER_API_KEY", default="")
        self.serper_url = "https://google.serper.dev/search"
    
    async def search_external_influencers(self, filters: SearchFilters, query: str, limit: int = 10) -> List[Influencer]:
        """
        Search for influencers from external sources using web scraping and APIs
        """
        influencers = []
        
        try:
            # Search Instagram influencers
            if not filters.platform or filters.platform == PlatformType.INSTAGRAM:
                instagram_results = await self._search_instagram_influencers(filters, query, limit // 2)
                influencers.extend(instagram_results)
            
            # Search YouTube influencers
            if not filters.platform or filters.platform == PlatformType.YOUTUBE:
                youtube_results = await self._search_youtube_influencers(filters, query, limit // 2)
                influencers.extend(youtube_results)
            
            # Search TikTok influencers
            if not filters.platform or filters.platform == PlatformType.TIKTOK:
                tiktok_results = await self._search_tiktok_influencers(filters, query, limit // 3)
                influencers.extend(tiktok_results)
            
            return influencers[:limit]
            
        except Exception as e:
            print(f"External search error: {e}")
            return []
    
    async def _search_instagram_influencers(self, filters: SearchFilters, query: str, limit: int) -> List[Influencer]:
        """Search Instagram influencers using Serper API"""
        search_query = self._build_search_query("Instagram", filters, query)
        
        try:
            results = await self._serper_search(search_query)
            influencers = []
            
            for result in results.get('organic', [])[:limit]:
                influencer = await self._parse_instagram_result(result, filters)
                if influencer:
                    influencers.append(influencer)
            
            return influencers
            
        except Exception as e:
            print(f"Instagram search error: {e}")
            return []
    
    async def _search_youtube_influencers(self, filters: SearchFilters, query: str, limit: int) -> List[Influencer]:
        """Search YouTube influencers using Serper API"""
        search_query = self._build_search_query("YouTube", filters, query)
        
        try:
            results = await self._serper_search(search_query)
            influencers = []
            
            for result in results.get('organic', [])[:limit]:
                influencer = await self._parse_youtube_result(result, filters)
                if influencer:
                    influencers.append(influencer)
            
            return influencers
            
        except Exception as e:
            print(f"YouTube search error: {e}")
            return []
    
    async def _search_tiktok_influencers(self, filters: SearchFilters, query: str, limit: int) -> List[Influencer]:
        """Search TikTok influencers using Serper API"""
        search_query = self._build_search_query("TikTok", filters, query)
        
        try:
            results = await self._serper_search(search_query)
            influencers = []
            
            for result in results.get('organic', [])[:limit]:
                influencer = await self._parse_tiktok_result(result, filters)
                if influencer:
                    influencers.append(influencer)
            
            return influencers
            
        except Exception as e:
            print(f"TikTok search error: {e}")
            return []
    
    def _build_search_query(self, platform: str, filters: SearchFilters, original_query: str) -> str:
        """Build search query for external APIs to find actual influencer profiles"""
        if platform.lower() == "instagram":
            query_parts = ["site:instagram.com"]
            if filters.niche:
                query_parts.append(f"{filters.niche} influencer")
            else:
                query_parts.append("influencer")
            
            if filters.location:
                query_parts.append(filters.location)
            
            # Add follower count hints
            if filters.followers_min:
                if filters.followers_min >= 1000000:
                    query_parts.append(f"{filters.followers_min // 1000000}M followers")
                elif filters.followers_min >= 1000:
                    query_parts.append(f"{filters.followers_min // 1000}K followers")
            
            # Add bio keywords to find actual profiles
            query_parts.extend(["bio", "profile", "creator"])
            
        elif platform.lower() == "youtube":
            query_parts = ["site:youtube.com/channel OR site:youtube.com/c OR site:youtube.com/@"]
            if filters.niche:
                query_parts.append(f"{filters.niche} creator")
            else:
                query_parts.append("creator")
            
            if filters.location:
                query_parts.append(filters.location)
            
            # Add subscriber count hints
            if filters.followers_min:
                if filters.followers_min >= 1000000:
                    query_parts.append(f"{filters.followers_min // 1000000}M subscribers")
                elif filters.followers_min >= 1000:
                    query_parts.append(f"{filters.followers_min // 1000}K subscribers")
            
            query_parts.extend(["channel", "videos"])
            
        elif platform.lower() == "tiktok":
            query_parts = ["site:tiktok.com/@"]
            if filters.niche:
                query_parts.append(f"{filters.niche} creator")
            else:
                query_parts.append("creator")
            
            if filters.location:
                query_parts.append(filters.location)
            
            if filters.followers_min:
                if filters.followers_min >= 1000000:
                    query_parts.append(f"{filters.followers_min // 1000000}M followers")
                elif filters.followers_min >= 1000:
                    query_parts.append(f"{filters.followers_min // 1000}K followers")
            
            query_parts.extend(["profile", "videos"])
        
        return " ".join(query_parts)
    
    async def _serper_search(self, query: str) -> Dict[str, Any]:
        """Perform search using Serper API"""
        if not self.serper_api_key:
            return {}
        
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': query,
            'num': 10
        }
        
        try:
            response = requests.post(self.serper_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Serper API error: {e}")
            return {}
    
    async def _parse_instagram_result(self, result: Dict[str, Any], filters: SearchFilters) -> Influencer | None:
        """Parse Instagram search result into Influencer model"""
        try:
            title = result.get('title', '')
            link = result.get('link', '')
            snippet = result.get('snippet', '')
            
            # Validate it's actually an Instagram profile URL
            if not ('instagram.com/' in link and not any(x in link for x in ['/p/', '/tv/', '/reel/', '/stories/'])):
                return None
            
            # Extract username from Instagram URL
            username = self._extract_instagram_username(link)
            if not username or len(username) < 3:
                return None
            
            # Skip non-profile pages
            if username in ['explore', 'accounts', 'directory', 'help', 'about', 'press', 'jobs', 'privacy', 'terms']:
                return None
            
            # Extract follower count from snippet
            followers = self._extract_follower_count(snippet)
            
            # Only include if it looks like an actual influencer (has reasonable follower count)
            if followers < 1000:
                return None
            
            # Estimate price based on followers (rough calculation)
            price = self._estimate_price(followers, PlatformType.INSTAGRAM)
            
            return Influencer(
                name=title.split(' - ')[0] if ' - ' in title else username,
                username=username,
                platform=PlatformType.INSTAGRAM,
                followers=followers,
                source=InfluencerSource.EXTERNAL,
                id=None,
                engagement_rate=None,
                price_per_post=price,
                location=filters.location or "Unknown",
                niche=filters.niche or "General",
                bio=snippet[:200] if snippet else None,
                profile_link=link,
                avatar_url=None,
                verified=False,
                created_at=None,
                updated_at=None
            )
            
        except Exception as e:
            print(f"Error parsing Instagram result: {e}")
            return None
    
    async def _parse_youtube_result(self, result: Dict[str, Any], filters: SearchFilters) -> Influencer | None:
        """Parse YouTube search result into Influencer model"""
        try:
            title = result.get('title', '')
            link = result.get('link', '')
            snippet = result.get('snippet', '')
            
            # Validate it's actually a YouTube channel URL
            if not any(x in link for x in ['/channel/', '/c/', '/user/', '/@']):
                return None
                
            # Skip non-creator pages
            if any(x in link.lower() for x in ['/watch', '/playlist', '/shorts', '/results']):
                return None
            
            # Extract channel name
            channel_name = title.replace(' - YouTube', '').strip()
            username = self._extract_youtube_username(link)
            
            # Skip if it doesn't look like a real channel
            if not channel_name or len(channel_name) < 2:
                return None
            
            # Extract subscriber count from snippet
            followers = self._extract_subscriber_count(snippet)
            
            # Only include channels with reasonable subscriber count
            if followers < 1000:
                return None
            
            # Estimate price based on subscribers
            price = self._estimate_price(followers, PlatformType.YOUTUBE)
            
            return Influencer(
                name=channel_name,
                username=username or channel_name,
                platform=PlatformType.YOUTUBE,
                followers=followers,
                source=InfluencerSource.EXTERNAL,
                id=None,
                engagement_rate=None,
                price_per_post=price,
                location=filters.location or "Unknown",
                niche=filters.niche or "General",
                bio=snippet[:200] if snippet else None,
                profile_link=link,
                avatar_url=None,
                verified=False,
                created_at=None,
                updated_at=None
            )
            
        except Exception as e:
            print(f"Error parsing YouTube result: {e}")
            return None
    
    async def _parse_tiktok_result(self, result: Dict[str, Any], filters: SearchFilters) -> Influencer | None:
        """Parse TikTok search result into Influencer model"""
        try:
            title = result.get('title', '')
            link = result.get('link', '')
            snippet = result.get('snippet', '')
            
            # Extract username from TikTok URL
            username = self._extract_tiktok_username(link)
            if not username:
                return None
            
            # Extract follower count from snippet
            followers = self._extract_follower_count(snippet)
            
            # Estimate price based on followers
            price = self._estimate_price(followers, PlatformType.TIKTOK)
            
            return Influencer(
                name=title.split(' - ')[0] if ' - ' in title else username,
                username=username,
                platform=PlatformType.TIKTOK,
                followers=followers,
                source=InfluencerSource.EXTERNAL,
                id=None,
                engagement_rate=None,
                price_per_post=price,
                location=filters.location or "Unknown",
                niche=filters.niche or "General",
                bio=snippet[:200] if snippet else None,
                profile_link=link,
                avatar_url=None,
                verified=False,
                created_at=None,
                updated_at=None
            )
            
        except Exception as e:
            print(f"Error parsing TikTok result: {e}")
            return None
    
    def _extract_instagram_username(self, url: str) -> str | None:
        """Extract username from Instagram URL"""
        if 'instagram.com' in url:
            pattern = r'instagram\.com/([^/\?]+)'
            match = re.search(pattern, url)
            return match.group(1) if match else None
        return None
    
    def _extract_youtube_username(self, url: str) -> str | None:
        """Extract username from YouTube URL"""
        if 'youtube.com' in url:
            if '/channel/' in url:
                pattern = r'youtube\.com/channel/([^/\?]+)'
            elif '/c/' in url:
                pattern = r'youtube\.com/c/([^/\?]+)'
            elif '/user/' in url:
                pattern = r'youtube\.com/user/([^/\?]+)'
            else:
                pattern = r'youtube\.com/@([^/\?]+)'
            
            match = re.search(pattern, url)
            return match.group(1) if match else None
        return None
    
    def _extract_tiktok_username(self, url: str) -> str | None:
        """Extract username from TikTok URL"""
        if 'tiktok.com' in url:
            pattern = r'tiktok\.com/@([^/\?]+)'
            match = re.search(pattern, url)
            return match.group(1) if match else None
        return None
    
    def _extract_follower_count(self, text: str) -> int:
        """Extract follower count from text"""
        # Look for patterns like "1.2M followers", "500K followers", "10000 followers"
        patterns = [
            r'(\d+\.?\d*)[Mm]\s*(?:followers?|subs?)',
            r'(\d+\.?\d*)[Kk]\s*(?:followers?|subs?)',
            r'(\d+)\s*(?:followers?|subs?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num = float(match.group(1))
                if 'M' in match.group(0) or 'm' in match.group(0):
                    return int(num * 1000000)
                elif 'K' in match.group(0) or 'k' in match.group(0):
                    return int(num * 1000)
                else:
                    return int(num)
        
        # Default fallback
        return 10000
    
    def _extract_subscriber_count(self, text: str) -> int:
        """Extract subscriber count from text (YouTube specific)"""
        patterns = [
            r'(\d+\.?\d*)[Mm]\s*(?:subscribers?|subs?)',
            r'(\d+\.?\d*)[Kk]\s*(?:subscribers?|subs?)',
            r'(\d+)\s*(?:subscribers?|subs?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num = float(match.group(1))
                if 'M' in match.group(0) or 'm' in match.group(0):
                    return int(num * 1000000)
                elif 'K' in match.group(0) or 'k' in match.group(0):
                    return int(num * 1000)
                else:
                    return int(num)
        
        return 10000
    
    def _estimate_price(self, followers: int, platform: PlatformType) -> int:
        """Estimate price per post based on followers and platform"""
        base_rates = {
            PlatformType.INSTAGRAM: 0.01,  # $10 per 1K followers
            PlatformType.YOUTUBE: 0.02,    # $20 per 1K subscribers
            PlatformType.TIKTOK: 0.008,    # $8 per 1K followers
            PlatformType.TWITTER: 0.005,   # $5 per 1K followers
            PlatformType.LINKEDIN: 0.015,  # $15 per 1K connections
            PlatformType.FACEBOOK: 0.005   # $5 per 1K followers
        }
        
        rate = base_rates.get(platform, 0.01)
        estimated_price = int(followers * rate)
        
        # Add some bounds
        return max(50, min(estimated_price, 50000))

# Create singleton instance
external_scraper = ExternalInfluencerScraper()
