import requests
import json
import random
from typing import List, Dict, Any
from decouple import config
from bs4 import BeautifulSoup
import re
import asyncio
import aiohttp
from urllib.parse import urljoin
from app.models.influencer import Influencer, SearchFilters, InfluencerSource, PlatformType

class ExternalInfluencerScraper:
    def __init__(self):
        self.serper_api_key = config("SERPER_API_KEY", default="")
        self.serper_url = "https://google.serper.dev/search"
        
        # Headers to avoid being blocked
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    async def search_external_influencers(self, filters: SearchFilters, query: str, limit: int = 100) -> List[Influencer]:
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
        """Build focused search query for external APIs to find actual influencer profiles"""
        if platform.lower() == "instagram":
            query_parts = ["site:instagram.com"]
            
            # Exclude non-profile pages
            query_parts.append("-inurl:p/ -inurl:tv/ -inurl:reel/ -inurl:stories/")
            
            # Add niche-specific search if specified
            if filters.niche:
                # Use the exact niche term for more precise results
                query_parts.append(f'"{filters.niche}" influencer')
            else:
                query_parts.append("influencer")
            
            # Add location if specified
            if filters.location:
                query_parts.append(f'"{filters.location}"')
            
            # Add follower count indicators for better targeting
            if filters.followers_max and filters.followers_max <= 50000:
                query_parts.append("micro")
            elif filters.followers_min and filters.followers_min >= 1000000:
                query_parts.append("celebrity OR verified")
            
            # Add profile indicators to ensure we get actual profiles
            query_parts.append("followers")
            
        elif platform.lower() == "youtube":
            query_parts = ["site:youtube.com"]
            query_parts.append("inurl:channel OR inurl:c OR inurl:@")
            query_parts.append("-inurl:watch -inurl:playlist -inurl:shorts")
            
            # Add niche-specific search if specified
            if filters.niche:
                query_parts.append(f'"{filters.niche}" channel')
            else:
                query_parts.append("channel")
            
            # Add location if specified
            if filters.location:
                query_parts.append(f'"{filters.location}"')
            
            # Add subscriber indicators for better targeting
            if filters.followers_max and filters.followers_max <= 100000:
                query_parts.append("subscribers")
            elif filters.followers_min and filters.followers_min >= 1000000:
                query_parts.append("million subscribers")
            else:
                query_parts.append("subscribers")
            
        elif platform.lower() == "tiktok":
            query_parts = ["site:tiktok.com"]
            query_parts.append("inurl:@")
            query_parts.append("-inurl:video -inurl:discover -inurl:tag")
            
            # Add niche-specific search if specified
            if filters.niche:
                query_parts.append(f'"{filters.niche}" creator')
            else:
                query_parts.append("creator")
            
            # Add location if specified
            if filters.location:
                query_parts.append(f'"{filters.location}"')
            
            # Add follower indicators
            query_parts.append("followers")
        
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
            
            # Apply follower constraints from filters
            if filters.followers_min and followers < filters.followers_min:
                return None
            if filters.followers_max and followers > filters.followers_max:
                return None
            
            # Only include if it looks like an actual influencer (has reasonable follower count)
            if followers < 1000:
                return None
            
            # Estimate price based on followers (rough calculation)
            estimated_price = self._estimate_price(followers, PlatformType.INSTAGRAM)
            
            # Apply price constraints from filters
            if filters.price_min and estimated_price < filters.price_min:
                return None
            if filters.price_max and estimated_price > filters.price_max:
                return None
            
            # Estimate engagement rate based on follower count and platform
            engagement_rate = self._estimate_engagement_rate(followers, PlatformType.INSTAGRAM)
            
            # Extract bio from search snippet with improved cleaning
            bio = self._extract_bio_from_snippet(snippet, title, PlatformType.INSTAGRAM)
            
            return Influencer(
                name=title.split(' - ')[0] if ' - ' in title else username,
                username=username,
                platform=PlatformType.INSTAGRAM,
                followers=followers,
                source=InfluencerSource.EXTERNAL,
                id=None,
                engagement_rate=engagement_rate,
                price_per_post=estimated_price,
                location=filters.location or "Unknown",
                niche=filters.niche or "General",
                bio=bio[:200] if bio else None,
                profile_link=link,
                avatar_url=None,
                verified=self._is_likely_verified(title, snippet),
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
            
            # Apply follower constraints from filters
            if filters.followers_min and followers < filters.followers_min:
                return None
            if filters.followers_max and followers > filters.followers_max:
                return None
            
            # Only include channels with reasonable subscriber count
            if followers < 1000:
                return None
            
            # Estimate price based on subscribers
            estimated_price = self._estimate_price(followers, PlatformType.YOUTUBE)
            
            # Apply price constraints from filters
            if filters.price_min and estimated_price < filters.price_min:
                return None
            if filters.price_max and estimated_price > filters.price_max:
                return None
            
            # Estimate engagement rate based on subscriber count and platform
            engagement_rate = self._estimate_engagement_rate(followers, PlatformType.YOUTUBE)
            
            # Fetch actual bio from profile page
            # Extract bio from search snippet with improved cleaning
            bio = self._extract_bio_from_snippet(snippet, title, PlatformType.YOUTUBE)
            
            return Influencer(
                name=channel_name,
                username=username or channel_name,
                platform=PlatformType.YOUTUBE,
                followers=followers,
                source=InfluencerSource.EXTERNAL,
                id=None,
                engagement_rate=engagement_rate,
                price_per_post=estimated_price,
                location=filters.location or "Unknown",
                niche=filters.niche or "General",
                bio=bio[:200] if bio else None,
                profile_link=link,
                avatar_url=None,
                verified=self._is_likely_verified(title, snippet),
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
            
            # Apply follower constraints from filters
            if filters.followers_min and followers < filters.followers_min:
                return None
            if filters.followers_max and followers > filters.followers_max:
                return None
            
            # Only include if it looks like an actual influencer (has reasonable follower count)
            if followers < 1000:
                return None
            
            # Estimate price based on followers
            estimated_price = self._estimate_price(followers, PlatformType.TIKTOK)
            
            # Apply price constraints from filters
            if filters.price_min and estimated_price < filters.price_min:
                return None
            if filters.price_max and estimated_price > filters.price_max:
                return None
            
            # Estimate engagement rate based on follower count and platform
            engagement_rate = self._estimate_engagement_rate(followers, PlatformType.TIKTOK)
            
            # Fetch actual bio from profile page
            # Extract bio from search snippet with improved cleaning
            bio = self._extract_bio_from_snippet(snippet, title, PlatformType.TIKTOK)
            
            return Influencer(
                name=title.split(' - ')[0] if ' - ' in title else username,
                username=username,
                platform=PlatformType.TIKTOK,
                followers=followers,
                source=InfluencerSource.EXTERNAL,
                id=None,
                engagement_rate=engagement_rate,
                price_per_post=estimated_price,
                location=filters.location or "Unknown",
                niche=filters.niche or "General",
                bio=bio[:200] if bio else None,
                profile_link=link,
                avatar_url=None,
                verified=self._is_likely_verified(title, snippet),
                created_at=None,
                updated_at=None
            )
            
        except Exception as e:
            print(f"Error parsing TikTok result: {e}")
            return None
    
    async def _fetch_actual_bio(self, profile_url: str, platform: PlatformType) -> str:
        """Fetch the actual bio from the platform profile page"""
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(profile_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_bio_from_html(html, platform)
                    else:
                        return None
        except Exception as e:
            print(f"Error fetching bio from {profile_url}: {e}")
            return None

    def _extract_bio_from_html(self, html: str, platform: PlatformType) -> str:
        """Extract bio/description from platform HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            if platform == PlatformType.INSTAGRAM:
                # Instagram bio selectors
                bio_selectors = [
                    'meta[property="og:description"]',
                    'meta[name="description"]',
                    '[data-testid="user-description"]',
                    '.user__info__desc',
                    '.-vDIg span'
                ]
                
                for selector in bio_selectors:
                    bio_element = soup.select_one(selector)
                    if bio_element:
                        bio_text = bio_element.get('content') or bio_element.get_text(strip=True)
                        if bio_text and len(bio_text) > 10:
                            # Clean up Instagram bio text
                            bio_text = bio_text.replace('Followers, ', '').replace(' Following, ', '')
                            bio_text = re.sub(r'\d+\s*Posts?', '', bio_text)
                            bio_text = re.sub(r'\d+\s*Followers?', '', bio_text)
                            bio_text = re.sub(r'\d+\s*Following', '', bio_text)
                            return bio_text.strip()[:200]
                            
            elif platform == PlatformType.YOUTUBE:
                # YouTube channel description selectors
                bio_selectors = [
                    'meta[name="description"]',
                    'meta[property="og:description"]',
                    '#channel-description',
                    '.about-description',
                    'yt-formatted-string[slot="content"]'
                ]
                
                for selector in bio_selectors:
                    bio_element = soup.select_one(selector)
                    if bio_element:
                        bio_text = bio_element.get('content') or bio_element.get_text(strip=True)
                        if bio_text and len(bio_text) > 10:
                            # Clean up YouTube description
                            bio_text = re.sub(r'Subscribe for more.*', '', bio_text, flags=re.IGNORECASE)
                            bio_text = re.sub(r'\d+\s*subscribers?', '', bio_text, flags=re.IGNORECASE)
                            return bio_text.strip()[:200]
                            
            elif platform == PlatformType.TIKTOK:
                # TikTok bio selectors
                bio_selectors = [
                    'meta[name="description"]',
                    'meta[property="og:description"]',
                    '[data-e2e="user-bio"]',
                    '.user-bio',
                    'h2[data-e2e="user-subtitle"]'
                ]
                
                for selector in bio_selectors:
                    bio_element = soup.select_one(selector)
                    if bio_element:
                        bio_text = bio_element.get('content') or bio_element.get_text(strip=True)
                        if bio_text and len(bio_text) > 10:
                            # Clean up TikTok bio text
                            bio_text = re.sub(r'\d+\s*Followers?', '', bio_text, flags=re.IGNORECASE)
                            bio_text = re.sub(r'\d+\s*Following', '', bio_text, flags=re.IGNORECASE)
                            bio_text = re.sub(r'\d+\s*Likes?', '', bio_text, flags=re.IGNORECASE)
                            return bio_text.strip()[:200]
            
            return None
            
        except Exception as e:
            print(f"Error extracting bio from HTML: {e}")
            return None
    
    def _extract_bio_from_snippet(self, snippet: str, title: str, platform: PlatformType) -> str:
        """Extract and clean bio information from search snippet"""
        try:
            # Start with just the snippet - title often contains redundant platform info
            text = snippet
            
            # Remove common search result noise patterns
            noise_patterns = [
                r'\d+\.?\d*[KMB]?\s*Followers?(?:\s*[,·•]\s*\d+\.?\d*[KMB]?\s*Following)?(?:\s*[,·•]\s*\d+\.?\d*[KMB]?\s*Posts?)?',
                r'\d+\.?\d*[KMB]?\s*Following(?:\s*[,·•]\s*\d+\.?\d*[KMB]?\s*Posts?)?',
                r'\d+\.?\d*[KMB]?\s*Posts?(?:\s*[,·•])?',
                r'\d+\.?\d*[KMB]?\s*Likes?(?:\s*[,·•])?',
                r'\d+\.?\d*[KMB]?\s*Videos?(?:\s*[,·•])?',
                r'\d+\.?\d*[KMB]?\s*subscribers?(?:\s*[,·•])?',
                r'See photos and videos from\s*[^.]*',
                r'Follow to see their photos and videos',
                r'Latest posts from\s*[^.]*',
                r'@\w+\s*on\s*(Instagram|TikTok|YouTube)',
                r'@\w+\s*•\s*(Instagram|TikTok|YouTube)',
                r'(@\w+)',  # Remove @username mentions
                r'instagram\.com/\w+',
                r'tiktok\.com/@\w+',
                r'youtube\.com/[\w/]+',
                r'Verified account',
                r'•\s*(Instagram|TikTok|YouTube)(?:\s*$)?',
                r'―\s*(Instagram|TikTok|YouTube)(?:\s*$)?',
                r'Subscribe for more.*',
                r'Business inquiries:.*',
                r'Contact:.*',
                r'Email:.*',
                r'^\s*[-•·,\s]+',  # Remove leading punctuation and whitespace
                r'[-•·,\s]+$'     # Remove trailing punctuation and whitespace
            ]
            
            cleaned_text = text
            for pattern in noise_patterns:
                cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
            
            # Clean up extra whitespace and repeated punctuation
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            cleaned_text = re.sub(r'[,;]\s*[,;]+', ', ', cleaned_text)
            cleaned_text = re.sub(r'\.+', '.', cleaned_text)
            cleaned_text = cleaned_text.strip()
            
            # Split into sentences and filter for meaningful content
            sentences = [s.strip() for s in re.split(r'[.!?]+', cleaned_text) if s.strip()]
            meaningful_sentences = []
            
            for sentence in sentences:
                # Skip very short sentences
                if len(sentence) < 15:
                    continue
                    
                # Skip sentences with too many numbers (likely stats)
                digit_ratio = len(re.findall(r'\d', sentence)) / len(sentence) if sentence else 0
                if digit_ratio > 0.3:
                    continue
                    
                # Skip sentences that are mostly symbols or single characters
                if len([c for c in sentence if c.isalpha()]) < len(sentence) * 0.5:
                    continue
                    
                # Skip sentences that look like navigation or UI elements
                ui_indicators = ['click', 'tap', 'swipe', 'scroll', 'view more', 'see all']
                if any(indicator in sentence.lower() for indicator in ui_indicators):
                    continue
                    
                meaningful_sentences.append(sentence)
            
            # Reconstruct bio from meaningful sentences
            if meaningful_sentences:
                bio = '. '.join(meaningful_sentences[:2])  # Take first 2 meaningful sentences
                
                # Ensure proper sentence ending
                if bio and not bio.endswith(('.', '!', '?')):
                    bio += '.'
                    
                # Trim to reasonable length
                if len(bio) > 200:
                    bio = bio[:197] + "..."
                    
                return bio if len(bio) > 10 else None
            
            # Fallback: if we have some cleaned text but no good sentences
            if len(cleaned_text) > 15:
                fallback = cleaned_text[:200] if len(cleaned_text) > 200 else cleaned_text
                if not fallback.endswith(('.', '!', '?')):
                    fallback += '.'
                return fallback
                
            return None
            
        except Exception as e:
            print(f"Error extracting bio from snippet: {e}")
            return None

    def _estimate_engagement_rate(self, followers: int, platform: PlatformType) -> float:
        """Estimate engagement rate based on follower count and platform"""
        # Engagement rates generally decrease as follower count increases
        
        base_rates = {
            PlatformType.INSTAGRAM: {
                'micro': (0.03, 0.08),      # 3-8% for micro influencers
                'mid': (0.02, 0.05),        # 2-5% for mid-tier
                'macro': (0.01, 0.03),      # 1-3% for macro
                'mega': (0.005, 0.02)       # 0.5-2% for mega
            },
            PlatformType.YOUTUBE: {
                'micro': (0.02, 0.06),      # 2-6% for micro
                'mid': (0.015, 0.04),       # 1.5-4% for mid-tier
                'macro': (0.01, 0.025),     # 1-2.5% for macro
                'mega': (0.005, 0.015)      # 0.5-1.5% for mega
            },
            PlatformType.TIKTOK: {
                'micro': (0.05, 0.12),      # 5-12% for micro
                'mid': (0.03, 0.08),        # 3-8% for mid-tier
                'macro': (0.02, 0.05),      # 2-5% for macro
                'mega': (0.01, 0.03)        # 1-3% for mega
            }
        }
        
        # Determine tier based on follower count
        if followers < 100000:
            tier = 'micro'
        elif followers < 500000:
            tier = 'mid'
        elif followers < 1000000:
            tier = 'macro'
        else:
            tier = 'mega'
        
        # Get rate range for platform and tier
        rate_range = base_rates.get(platform, base_rates[PlatformType.INSTAGRAM])[tier]
        
        # Return random rate within range
        return round(random.uniform(rate_range[0], rate_range[1]), 3)

    def _is_likely_verified(self, title: str, snippet: str) -> bool:
        """Determine if influencer is likely verified based on content indicators"""
        content = f"{title} {snippet}".lower()
        
        verified_indicators = [
            'verified', 'official', 'celebrity', 'famous', 'star',
            'actor', 'actress', 'singer', 'musician', 'athlete',
            'brand', 'company', 'founder', 'ceo'
        ]
        
        return any(indicator in content for indicator in verified_indicators)
    
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
        """Extract follower count from text with improved patterns and smart estimation"""
        # Look for explicit follower/subscriber counts
        patterns = [
            r'(\d+\.?\d*)\s*[Mm](?:illion)?\s*(?:followers?|subs?|subscribers?)',
            r'(\d+\.?\d*)\s*[Kk](?:thousand)?\s*(?:followers?|subs?|subscribers?)',
            r'(\d+,?\d*)\s*(?:followers?|subs?|subscribers?)',
            r'(\d+\.?\d*)[Mm]\s*(?:follow|fans?)',
            r'(\d+\.?\d*)[Kk]\s*(?:follow|fans?)',
            # Look for any large numbers that might indicate followers
            r'(\d+\.?\d*)[Mm]',
            r'(\d+\.?\d*)[Kk]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num_str = match.group(1).replace(',', '')
                num = float(num_str)
                if 'M' in match.group(0) or 'm' in match.group(0):
                    return int(num * 1000000)
                elif 'K' in match.group(0) or 'k' in match.group(0):
                    return int(num * 1000)
                else:
                    return int(num)
        
        # Smart estimation based on content indicators
        return self._estimate_follower_count_from_content(text)
    
    def _extract_subscriber_count(self, text: str) -> int:
        """Extract subscriber count from text (YouTube specific)"""
        patterns = [
            r'(\d+\.?\d*)\s*[Mm](?:illion)?\s*(?:subscribers?|subs?)',
            r'(\d+\.?\d*)\s*[Kk](?:thousand)?\s*(?:subscribers?|subs?)',
            r'(\d+,?\d*)\s*(?:subscribers?|subs?)',
            r'(\d+\.?\d*)[Mm]\s*(?:subs?|views?)',
            r'(\d+\.?\d*)[Kk]\s*(?:subs?|views?)',
            # Look for any large numbers that might indicate subscribers
            r'(\d+\.?\d*)[Mm]',
            r'(\d+\.?\d*)[Kk]'
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
        
        return self._estimate_follower_count_from_content(text)
    
    def _estimate_follower_count_from_content(self, content: str) -> int:
        """Estimate follower count based on content indicators"""
        content_lower = content.lower()
        
        # Look for celebrity/mega influencer indicators
        celebrity_indicators = [
            'celebrity', 'famous', 'star', 'actor', 'actress', 'singer', 'musician',
            'athlete', 'model', 'tv', 'movie', 'film', 'grammy', 'oscar', 'emmy'
        ]
        
        # Look for verified/professional indicators
        professional_indicators = [
            'verified', 'official', 'founder', 'ceo', 'brand', 'company',
            'entrepreneur', 'business', 'coach', 'trainer', 'expert'
        ]
        
        # Look for micro influencer indicators
        micro_indicators = [
            'micro', 'small', 'local', 'community', 'lifestyle blogger',
            'content creator', 'up and coming', 'emerging'
        ]
        
        # Check for app/product mentions (usually indicates larger following)
        app_indicators = [
            'app', 'download', 'free trial', 'challenge', 'program',
            'course', 'membership', 'subscription'
        ]
        
        # Count indicators
        celebrity_count = sum(1 for indicator in celebrity_indicators if indicator in content_lower)
        professional_count = sum(1 for indicator in professional_indicators if indicator in content_lower)
        micro_count = sum(1 for indicator in micro_indicators if indicator in content_lower)
        app_count = sum(1 for indicator in app_indicators if indicator in content_lower)
        
        # Estimate based on indicators
        if celebrity_count >= 2:
            return random.randint(1000000, 10000000)  # 1M - 10M
        elif app_count >= 2 or professional_count >= 2:
            return random.randint(500000, 2000000)   # 500K - 2M
        elif professional_count >= 1 or app_count >= 1:
            return random.randint(100000, 500000)    # 100K - 500K
        elif micro_count >= 1:
            return random.randint(10000, 100000)     # 10K - 100K
        else:
            return random.randint(25000, 150000)     # 25K - 150K (general influencer)

    def _estimate_engagement_rate(self, followers: int, platform: PlatformType) -> float:
        """Estimate engagement rate based on follower count and platform"""
        # Engagement rates generally decrease as follower count increases
        
        base_rates = {
            PlatformType.INSTAGRAM: {
                'micro': (0.03, 0.08),      # 3-8% for micro influencers
                'mid': (0.02, 0.05),        # 2-5% for mid-tier
                'macro': (0.01, 0.03),      # 1-3% for macro
                'mega': (0.005, 0.02)       # 0.5-2% for mega
            },
            PlatformType.YOUTUBE: {
                'micro': (0.02, 0.06),      # 2-6% for micro
                'mid': (0.015, 0.04),       # 1.5-4% for mid-tier
                'macro': (0.01, 0.025),     # 1-2.5% for macro
                'mega': (0.005, 0.015)      # 0.5-1.5% for mega
            },
            PlatformType.TIKTOK: {
                'micro': (0.05, 0.12),      # 5-12% for micro (TikTok has higher engagement)
                'mid': (0.03, 0.08),        # 3-8% for mid-tier
                'macro': (0.02, 0.05),      # 2-5% for macro
                'mega': (0.01, 0.03)        # 1-3% for mega
            }
        }
        
        # Determine tier based on follower count
        if followers < 100000:
            tier = 'micro'
        elif followers < 500000:
            tier = 'mid'
        elif followers < 1000000:
            tier = 'macro'
        else:
            tier = 'mega'
        
        # Get rate range for platform and tier
        platform_rates = base_rates.get(platform, base_rates[PlatformType.INSTAGRAM])
        min_rate, max_rate = platform_rates.get(tier, (0.01, 0.03))
        
        # Generate random engagement rate within the range
        engagement_rate = random.uniform(min_rate, max_rate)
        return round(engagement_rate, 3)

    def _is_likely_verified(self, title: str, snippet: str) -> bool:
        """Determine if an influencer is likely verified based on content indicators"""
        content = f"{title} {snippet}".lower()
        
        verification_indicators = [
            'verified', 'official', 'celebrity', 'famous', 'star',
            'founder', 'ceo', 'brand', 'company', 'million', 'grammy',
            'oscar', 'emmy', 'athlete', 'actor', 'actress', 'singer',
            'musician', 'model', 'tv show', 'movie'
        ]
        
        # Count verification indicators
        indicator_count = sum(1 for indicator in verification_indicators if indicator in content)
        
        # Higher chance of verification with more indicators
        if indicator_count >= 3:
            return random.choice([True, True, True, False])  # 75% chance
        elif indicator_count >= 2:
            return random.choice([True, True, False, False])  # 50% chance
        elif indicator_count >= 1:
            return random.choice([True, False, False, False])  # 25% chance
        else:
            return False

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
