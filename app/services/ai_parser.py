import json
import google.generativeai as genai
from typing import Dict, Any, Optional
from decouple import config
from app.models.influencer import SearchFilters, PlatformType

class AIQueryParser:
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=config("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def parse_query(self, query: str) -> SearchFilters:
        """
        Parse natural language query into structured search filters using Gemini AI
        """
        prompt = self._create_parsing_prompt(query)
        
        try:
            response = self.model.generate_content(prompt)
            parsed_data = self._extract_json_from_response(response.text)
            return self._create_search_filters(parsed_data)
        except Exception as e:
            print(f"Error parsing query with AI: {e}")
            return SearchFilters()
    
    def _create_parsing_prompt(self, query: str) -> str:
        return f"""
You are an AI assistant that extracts search parameters from natural language queries for influencer search.

Extract the following information from the user query and return ONLY a valid JSON object:

Query: "{query}"

Extract these parameters:
- location: string (city, country, region mentioned)
- niche: string (fashion, tech, fitness, beauty, food, travel, gaming, lifestyle, etc.)
- platform: string (instagram, youtube, tiktok, twitter, linkedin, facebook)
- followers_min: integer (minimum follower count)
- followers_max: integer (maximum follower count)
- price_min: integer (minimum price per post in USD)
- price_max: integer (maximum price per post in USD)
- engagement_min: float (minimum engagement rate as percentage)
- engagement_max: float (maximum engagement rate as percentage)
- verified_only: boolean (if they want only verified accounts)

Rules:
1. Convert follower mentions like "10k" to 10000, "1M" to 1000000
2. Convert price mentions like "$500" to 500
3. If a range is mentioned, extract both min and max
4. If only one value is mentioned, treat it as max
5. Only include fields that are explicitly mentioned or can be inferred
6. Return ONLY valid JSON, no other text

Example outputs:
- "Fashion influencers in NYC with 50k-100k followers under $1000" → {{"location": "New York", "niche": "fashion", "followers_min": 50000, "followers_max": 100000, "price_max": 1000}}
- "Tech YouTubers with high engagement" → {{"niche": "tech", "platform": "youtube", "engagement_min": 5.0}}

JSON:
"""
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from AI response text"""
        try:
            # Find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            
            return {}
        except json.JSONDecodeError:
            return {}
    
    def _create_search_filters(self, parsed_data: Dict[str, Any]) -> SearchFilters:
        """Convert parsed data to SearchFilters model"""
        filters = {}
        
        # Map parsed data to SearchFilters fields
        if "location" in parsed_data:
            filters["location"] = parsed_data["location"]
        
        if "niche" in parsed_data:
            filters["niche"] = parsed_data["niche"]
        
        if "platform" in parsed_data:
            platform_str = parsed_data["platform"].lower()
            try:
                filters["platform"] = PlatformType(platform_str)
            except ValueError:
                pass  # Skip invalid platform
        
        if "followers_min" in parsed_data:
            filters["followers_min"] = int(parsed_data["followers_min"])
        
        if "followers_max" in parsed_data:
            filters["followers_max"] = int(parsed_data["followers_max"])
        
        if "price_min" in parsed_data:
            filters["price_min"] = int(parsed_data["price_min"])
        
        if "price_max" in parsed_data:
            filters["price_max"] = int(parsed_data["price_max"])
        
        if "engagement_min" in parsed_data:
            filters["engagement_min"] = float(parsed_data["engagement_min"])
        
        if "engagement_max" in parsed_data:
            filters["engagement_max"] = float(parsed_data["engagement_max"])
        
        if "verified_only" in parsed_data:
            filters["verified_only"] = bool(parsed_data["verified_only"])
        
        return SearchFilters(**filters)

# Create singleton instance
ai_parser = AIQueryParser()
