from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from app.models.influencer import SearchRequest, SearchResponse, SearchFilters, PlatformType
from app.services.search_service import search_service

router = APIRouter()

@router.post("/search")
async def search_influencers(request_data: Dict[str, Any] = Body(...)):
    """
    Search for influencers using AI-powered natural language query parsing
    
    Request body should contain:
    - **query**: Natural language search query (e.g., "fashion influencers in NYC with 50k followers")
    - **filters**: Optional structured filters to override AI parsing
    - **limit**: Maximum number of results to return (default: 20, max: 100)
    - **include_external**: Whether to include external influencers (default: True)
    """
    try:
        # Parse request data
        query = request_data.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Parse filters if provided
        filters = None
        if "filters" in request_data and request_data["filters"]:
            filter_data = request_data["filters"]
            # Convert platform string to enum if present
            if "platform" in filter_data and filter_data["platform"]:
                filter_data["platform"] = PlatformType(filter_data["platform"])
            filters = SearchFilters(**filter_data)
        
        # Create search request
        search_request = SearchRequest(
            query=query,
            filters=filters,
            limit=request_data.get("limit", 20),
            include_external=request_data.get("include_external", True)
        )
        
        # Perform search
        response = await search_service.search_influencers(search_request)
        
        # Return as dictionary
        return response.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search")
async def search_influencers_get(
    query: str = Query(..., description="Natural language search query"),
    location: Optional[str] = Query(None, description="Location filter"),
    niche: Optional[str] = Query(None, description="Niche filter"),
    platform: Optional[str] = Query(None, description="Platform filter"),
    followers_min: Optional[int] = Query(None, description="Minimum followers"),
    followers_max: Optional[int] = Query(None, description="Maximum followers"),
    price_min: Optional[int] = Query(None, description="Minimum price per post"),
    price_max: Optional[int] = Query(None, description="Maximum price per post"),
    engagement_min: Optional[float] = Query(None, description="Minimum engagement rate"),
    engagement_max: Optional[float] = Query(None, description="Maximum engagement rate"),
    verified_only: Optional[bool] = Query(False, description="Only verified accounts"),
    limit: Optional[int] = Query(20, le=100, description="Maximum results"),
    include_external: Optional[bool] = Query(True, description="Include external results")
):
    """
    Search for influencers using GET method with query parameters
    """
    try:
        # Build filters from query parameters
        platform_enum = None
        if platform:
            try:
                platform_enum = PlatformType(platform.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
        
        filters = SearchFilters(
            location=location,
            niche=niche,
            platform=platform_enum,
            followers_min=followers_min,
            followers_max=followers_max,
            price_min=price_min,
            price_max=price_max,
            engagement_min=engagement_min,
            engagement_max=engagement_max,
            verified_only=verified_only
        )
        
        # Create search request
        search_request = SearchRequest(
            query=query,
            filters=filters,
            limit=limit,
            include_external=include_external
        )
        
        # Perform search
        response = await search_service.search_influencers(search_request)
        
        # Return as dictionary
        return response.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/suggestions")
async def get_search_suggestions(
    query: Optional[str] = Query(None, description="Partial query for suggestions")
) -> List[str]:
    """
    Get search suggestions based on partial query
    """
    try:
        return await search_service.get_search_suggestions(query or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@router.get("/filters/options")
async def get_filter_options():
    """
    Get available filter options for the frontend
    """
    return {
        "platforms": [platform.value for platform in PlatformType],
        "popular_niches": [
            "fashion",
            "beauty",
            "fitness",
            "food",
            "travel",
            "tech",
            "gaming",
            "lifestyle",
            "business",
            "education",
            "art",
            "music",
            "comedy",
            "sports",
            "health"
        ],
        "follower_ranges": [
            {"label": "Nano (1K-10K)", "min": 1000, "max": 10000},
            {"label": "Micro (10K-100K)", "min": 10000, "max": 100000},
            {"label": "Mid-tier (100K-1M)", "min": 100000, "max": 1000000},
            {"label": "Macro (1M-10M)", "min": 1000000, "max": 10000000},
            {"label": "Mega (10M+)", "min": 10000000, "max": None}
        ],
        "price_ranges": [
            {"label": "Budget (<$100)", "min": 0, "max": 100},
            {"label": "Standard ($100-$500)", "min": 100, "max": 500},
            {"label": "Premium ($500-$2000)", "min": 500, "max": 2000},
            {"label": "Luxury ($2000-$10000)", "min": 2000, "max": 10000},
            {"label": "Celebrity ($10000+)", "min": 10000, "max": None}
        ]
    }
