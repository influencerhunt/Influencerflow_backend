import json
import google.generativeai as genai
from typing import Dict, Any, Optional
from decouple import config
from app.models.influencer import SearchFilters, PlatformType

class AIQueryParser:
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=config("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
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
You are an expert AI assistant that extracts search parameters from natural language queries for influencer search. You must handle complex comparison operators and nuanced language.

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

CRITICAL PARSING RULES:

1. **Follower Count Conversions:**
   - "10k", "10K" → 10000
   - "1m", "1M", "1 million" → 1000000
   - "500k followers" → 500000

2. **Comparison Operators - Pay Close Attention:**
   - "over X", "above X", "more than X", "greater than X", ">X" → followers_min: X
   - "under X", "below X", "less than X", "fewer than X", "<X", "X or less", "X or fewer" → followers_max: X
   - "at least X", "minimum X", "X+" → followers_min: X
   - "at most X", "maximum X", "up to X", "X or less", "X or fewer" → followers_max: X
   - "between X and Y", "X-Y", "X to Y" → followers_min: X, followers_max: Y
   - "around X", "approximately X", "about X" → followers_min: X*0.8, followers_max: X*1.2

3. **Price Parsing:**
   - "$500", "500 dollars", "500 USD" → 500
   - "under $1000", "below $1k" → price_max: 1000
   - "over $500", "above $500" → price_min: 500
   - "between $200-$800" → price_min: 200, price_max: 800

4. **Engagement Rate Parsing:**
   - "high engagement" → engagement_min: 4.0
   - "low engagement" → engagement_max: 2.0
   - "good engagement" → engagement_min: 3.0
   - "excellent engagement" → engagement_min: 5.0
   - "over 5% engagement" → engagement_min: 5.0
   - "less than 3% engagement" → engagement_max: 3.0

5. **Platform Recognition:**
   - "YouTubers", "YouTube creators", "on YouTube" → "youtube"
   - "Instagram influencers", "on Instagram", "IG" → "instagram"
   - "TikTokers", "TikTok creators", "on TikTok" → "tiktok"
   - "Twitter users", "on Twitter" → "twitter"

6. **Location Standardization:**
   - "NYC", "New York City" → "New York"
   - "LA", "Los Angeles" → "Los Angeles"
   - "SF", "San Francisco" → "San Francisco"

COMPLEX EXAMPLES:
- "Fashion influencers with more than 100k followers but less than 500k" → {{"niche": "fashion", "followers_min": 100000, "followers_max": 500000}}
- "YouTubers over 1M subscribers under $2000 per video" → {{"platform": "youtube", "followers_min": 1000000, "price_max": 2000}}
- "Tech creators with at least 50k followers and high engagement" → {{"niche": "tech", "followers_min": 50000, "engagement_min": 4.0}}
- "Beauty influencers under 200k followers with excellent engagement rates" → {{"niche": "beauty", "followers_max": 200000, "engagement_min": 5.0}}
- "Instagram users in NYC with 10k+ followers below $300" → {{"platform": "instagram", "location": "New York", "followers_min": 10000, "price_max": 300}}
- "Fitness creators with fewer than 100k but more than 25k followers" → {{"niche": "fitness", "followers_min": 25000, "followers_max": 100000}}
- "Dance influencers from Hyderabad with 50k followers or less" → {{"niche": "dance", "location": "Hyderabad", "followers_max": 50000}}
- "Travel bloggers with 20k or fewer followers" → {{"niche": "travel", "followers_max": 20000}}
- "Micro influencers with 10k followers or less" → {{"followers_max": 10000}}
- "Small creators under 5k followers" → {{"followers_max": 5000}}
- "Budget influencers for $100 or less per post" → {{"price_max": 100}}

IMPORTANT:
- Return ONLY valid JSON, no explanations or extra text
- Handle all comparison operators correctly
- Understand context and implied meanings
- Be precise with min/max assignments based on comparison words

JSON:
"""
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from AI response text with enhanced parsing"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            
            # Try to find JSON block markers first
            json_markers = ['```json', '```', 'JSON:', 'json:']
            for marker in json_markers:
                if marker in response_text:
                    # Extract content after the marker
                    start_idx = response_text.find(marker) + len(marker)
                    response_text = response_text[start_idx:].strip()
                    # Remove closing markers
                    if response_text.endswith('```'):
                        response_text = response_text[:-3].strip()
                    break
            
            # Find the JSON object boundaries
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                
                # Clean up common JSON formatting issues
                json_str = json_str.replace('\n', ' ').replace('\t', ' ')
                # Fix common AI response issues
                json_str = json_str.replace('{{', '{').replace('}}', '}')
                
                parsed_json = json.loads(json_str)
                
                # Validate that it's a proper dictionary
                if isinstance(parsed_json, dict):
                    return parsed_json
            
            # Fallback: try to parse the entire response as JSON
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response text: {response_text}")
            return {}
        except Exception as e:
            print(f"Unexpected error in JSON extraction: {e}")
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
        else:
            filters["followers_min"] = 1000
        
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
