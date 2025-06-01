from typing import List, Dict, Any
from app.services.supabase import supabase_service
from app.models.influencer import Influencer, SearchFilters, InfluencerSource, PlatformType

class DatabaseSearchService:
    def __init__(self):
        self.supabase = supabase_service.get_client()
    
    async def search_influencers(self, filters: SearchFilters, limit: int = 20) -> List[Influencer]:
        """
        Search for influencers in the database based on filters
        """
        try:
            # Build Supabase query
            query = self.supabase.table('influencers').select('*')
            
            # Apply filters
            if filters.location:
                query = query.ilike('location', f'%{filters.location}%')
            
            if filters.niche:
                query = query.ilike('niche', f'%{filters.niche}%')
            
            if filters.platform:
                query = query.eq('platform', filters.platform.value)
            
            if filters.followers_min:
                query = query.gte('followers', filters.followers_min)
            
            if filters.followers_max:
                query = query.lte('followers', filters.followers_max)
            
            if filters.price_min:
                query = query.gte('price_per_post', filters.price_min)
            
            if filters.price_max:
                query = query.lte('price_per_post', filters.price_max)
            
            if filters.engagement_min:
                query = query.gte('engagement_rate', filters.engagement_min)
            
            if filters.engagement_max:
                query = query.lte('engagement_rate', filters.engagement_max)
            
            if filters.verified_only:
                query = query.eq('verified', True)
            
            # Execute query with limit
            result = query.limit(limit).execute()
            
            # Convert to Influencer dataclasses
            influencers = []
            for row in result.data:
                # Convert platform string to enum
                platform = PlatformType(row['platform']) if row.get('platform') else PlatformType.INSTAGRAM
                
                influencer = Influencer(
                    id=row.get('id'),
                    name=row.get('name', ''),
                    username=row.get('username', ''),
                    platform=platform,
                    followers=row.get('followers', 0),
                    engagement_rate=row.get('engagement_rate'),
                    price_per_post=row.get('price_per_post'),
                    location=row.get('location'),
                    niche=row.get('niche'),
                    bio=row.get('bio'),
                    profile_link=row.get('profile_link'),
                    avatar_url=row.get('avatar_url'),
                    verified=row.get('verified', False),
                    source=InfluencerSource.ON_PLATFORM,
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                )
                influencers.append(influencer)
            
            return influencers
            
        except Exception as e:
            print(f"Database search error: {e}")
            return []
    
    async def get_influencer_by_id(self, influencer_id: str) -> Influencer | None:
        """Get a specific influencer by ID"""
        try:
            result = self.supabase.table('influencers').select('*').eq('id', influencer_id).execute()
            
            if result.data:
                row = result.data[0]
                # Convert platform string to enum
                platform = PlatformType(row['platform']) if row.get('platform') else PlatformType.INSTAGRAM
                
                return Influencer(
                    id=row.get('id'),
                    name=row.get('name', ''),
                    username=row.get('username', ''),
                    platform=platform,
                    followers=row.get('followers', 0),
                    engagement_rate=row.get('engagement_rate'),
                    price_per_post=row.get('price_per_post'),
                    location=row.get('location'),
                    niche=row.get('niche'),
                    bio=row.get('bio'),
                    profile_link=row.get('profile_link'),
                    avatar_url=row.get('avatar_url'),
                    verified=row.get('verified', False),
                    source=InfluencerSource.ON_PLATFORM,
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                )
            
            return None
            
        except Exception as e:
            print(f"Error fetching influencer: {e}")
            return None

# Create singleton instance
database_service = DatabaseSearchService()
