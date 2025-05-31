from typing import List
import asyncio
from app.models.influencer import Influencer, SearchFilters, SearchRequest, SearchResponse, InfluencerSource
from app.services.ai_parser import ai_parser
from app.services.database import database_service
from app.services.external_scraper import external_scraper

class InfluencerSearchService:
    """
    Main service that orchestrates AI query parsing, database search, and external scraping
    """
    
    async def search_influencers(self, search_request: SearchRequest) -> SearchResponse:
        """
        Perform comprehensive influencer search combining AI parsing, database search, and external scraping
        """
        # Parse the natural language query using Gemini AI
        if search_request.filters:
            # Use provided filters
            filters = search_request.filters
        else:
            # Parse query with AI
            filters = await ai_parser.parse_query(search_request.query)
        
        # Search on-platform influencers from database
        on_platform_task = database_service.search_influencers(
            filters, 
            limit=search_request.limit // 2 if search_request.include_external else search_request.limit
        )
        
        # Search external influencers if requested
        external_task = None
        if search_request.include_external:
            external_task = external_scraper.search_external_influencers(
                filters, 
                search_request.query, 
                limit=search_request.limit // 2
            )
        
        # Execute searches concurrently
        if external_task:
            on_platform_results, external_results = await asyncio.gather(
                on_platform_task,
                external_task,
                return_exceptions=True
            )
        else:
            on_platform_results = await on_platform_task
            external_results = []
        
        # Handle exceptions
        if isinstance(on_platform_results, Exception):
            print(f"Database search error: {on_platform_results}")
            on_platform_results = []
        
        if isinstance(external_results, Exception):
            print(f"External search error: {external_results}")
            external_results = []
        
        # Remove duplicates separately for each category
        on_platform_unique = self._deduplicate_influencers(on_platform_results)
        external_unique = self._deduplicate_influencers(external_results)
        
        # Remove cross-category duplicates (prioritize on-platform)
        external_deduplicated = self._remove_cross_duplicates(on_platform_unique, external_unique)
        
        # Apply separate ranking for each category
        on_platform_ranked = self._rank_influencers(on_platform_unique, filters)
        external_ranked = self._rank_influencers(external_deduplicated, filters)
        
        # Limit results for each category
        on_platform_limit = search_request.limit // 2 if search_request.include_external else search_request.limit
        external_limit = search_request.limit // 2 if search_request.include_external else 0
        
        on_platform_final = on_platform_ranked[:on_platform_limit]
        external_final = external_ranked[:external_limit] if search_request.include_external else []
        
        total_results = len(on_platform_final) + len(external_final)
        
        return SearchResponse(
            query=search_request.query,
            total_results=total_results,
            on_platform_count=len(on_platform_final),
            external_count=len(external_final),
            on_platform_influencers=on_platform_final,
            external_influencers=external_final
        )
    
    def _deduplicate_influencers(self, influencers: List[Influencer]) -> List[Influencer]:
        """
        Remove duplicates within a single category
        """
        seen = set()
        unique_influencers = []
        
        for influencer in influencers:
            key = f"{influencer.username.lower()}_{influencer.platform.value}"
            if key not in seen:
                seen.add(key)
                unique_influencers.append(influencer)
        
        return unique_influencers
    
    def _remove_cross_duplicates(self, on_platform: List[Influencer], external: List[Influencer]) -> List[Influencer]:
        """
        Remove external influencers that already exist in on-platform results
        On-platform results have priority
        """
        on_platform_keys = {f"{inf.username.lower()}_{inf.platform.value}" for inf in on_platform}
        
        unique_external = []
        for influencer in external:
            key = f"{influencer.username.lower()}_{influencer.platform.value}"
            if key not in on_platform_keys:
                unique_external.append(influencer)
        
        return unique_external
    
    def _rank_influencers(self, influencers: List[Influencer], filters: SearchFilters) -> List[Influencer]:
        """
        Rank influencers based on multiple parameters with weighted scoring
        """
        def calculate_relevance_score(influencer: Influencer) -> float:
            score = 0.0
            
            # Follower count score (normalized to 0-100 scale)
            # Using log scale to prevent extremely large accounts from dominating
            if influencer.followers > 0:
                import math
                follower_score = min(100, math.log10(influencer.followers) * 10)
                score += follower_score * 0.3  # 30% weight
            
            # Engagement rate score (0-100 scale, 5% engagement = 100 points)
            if influencer.engagement_rate is not None:
                engagement_score = min(100, influencer.engagement_rate * 20)  # 5% = 100 points
                score += engagement_score * 0.4  # 40% weight (most important)
            else:
                # Default moderate score if engagement rate is unknown
                score += 50 * 0.4
            
            # Price efficiency score (lower price = higher score for same quality)
            if influencer.price_per_post is not None and influencer.price_per_post > 0:
                # Calculate followers per dollar (efficiency metric)
                efficiency = influencer.followers / influencer.price_per_post
                # Normalize efficiency score (logarithmic scale)
                import math
                efficiency_score = min(100, math.log10(efficiency + 1) * 25)
                score += efficiency_score * 0.2  # 20% weight
            else:
                # Default score if price is unknown
                score += 50 * 0.2
            
            # Verification bonus
            if influencer.verified:
                score += 10  # 10% bonus for verified accounts
            
            # Filter matching bonuses
            if filters:
                # Location match bonus
                if (filters.location and influencer.location and 
                    filters.location.lower() in influencer.location.lower()):
                    score += 15
                
                # Niche match bonus
                if (filters.niche and influencer.niche and 
                    filters.niche.lower() in influencer.niche.lower()):
                    score += 15
                
                # Platform match bonus
                if filters.platform and influencer.platform == filters.platform:
                    score += 10
            
            return score
        
        # Calculate scores and sort
        scored_influencers = [(inf, calculate_relevance_score(inf)) for inf in influencers]
        scored_influencers.sort(key=lambda x: x[1], reverse=True)
        
        return [inf for inf, score in scored_influencers]
    
    async def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions based on partial query
        """
        # This could be enhanced with ML/AI for better suggestions
        base_suggestions = [
            "fashion influencers in New York",
            "tech YouTubers with 100k+ subscribers",
            "fitness influencers under $500",
            "beauty TikTokers in Los Angeles",
            "travel bloggers with high engagement",
            "food influencers in Chicago",
            "lifestyle Instagram creators",
            "gaming streamers on Twitch"
        ]
        
        # Filter suggestions based on query
        if query:
            filtered = [s for s in base_suggestions if query.lower() in s.lower()]
            return filtered[:5]
        
        return base_suggestions[:5]

# Create singleton instance
search_service = InfluencerSearchService()
