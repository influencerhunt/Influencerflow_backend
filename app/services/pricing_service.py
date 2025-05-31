from typing import Dict, List
from app.models.negotiation_models import (
    InfluencerProfile, PlatformType, ContentType, LocationType, 
    MarketRateData, PlatformConfig
)
import json
import logging

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        self.platform_configs = {
            PlatformType.INSTAGRAM: PlatformConfig(
                name="Instagram",
                content_types=[ContentType.INSTAGRAM_POST, ContentType.INSTAGRAM_REEL, ContentType.INSTAGRAM_STORY],
                base_rates={
                    ContentType.INSTAGRAM_POST: 1.0,
                    ContentType.INSTAGRAM_REEL: 1.5,
                    ContentType.INSTAGRAM_STORY: 0.3
                },
                engagement_weight=1.2,
                follower_weight=1.0
            ),
            PlatformType.YOUTUBE: PlatformConfig(
                name="YouTube",
                content_types=[ContentType.YOUTUBE_LONG_FORM, ContentType.YOUTUBE_SHORTS],
                base_rates={
                    ContentType.YOUTUBE_LONG_FORM: 2.0,
                    ContentType.YOUTUBE_SHORTS: 1.0
                },
                engagement_weight=1.5,
                follower_weight=1.2
            ),
            PlatformType.LINKEDIN: PlatformConfig(
                name="LinkedIn",
                content_types=[ContentType.LINKEDIN_POST, ContentType.LINKEDIN_VIDEO],
                base_rates={
                    ContentType.LINKEDIN_POST: 0.8,
                    ContentType.LINKEDIN_VIDEO: 1.3
                },
                engagement_weight=1.8,
                follower_weight=0.8
            ),
            PlatformType.TIKTOK: PlatformConfig(
                name="TikTok",
                content_types=[ContentType.TIKTOK_VIDEO],
                base_rates={
                    ContentType.TIKTOK_VIDEO: 1.2
                },
                engagement_weight=1.3,
                follower_weight=1.1
            ),
            PlatformType.TWITTER: PlatformConfig(
                name="Twitter",
                content_types=[ContentType.TWITTER_POST, ContentType.TWITTER_VIDEO],
                base_rates={
                    ContentType.TWITTER_POST: 0.5,
                    ContentType.TWITTER_VIDEO: 0.8
                },
                engagement_weight=1.0,
                follower_weight=0.7
            )
        }
        
        self.location_multipliers = {
            LocationType.US: 1.8,
            LocationType.UK: 1.6,
            LocationType.CANADA: 1.5,
            LocationType.AUSTRALIA: 1.4,
            LocationType.GERMANY: 1.3,
            LocationType.FRANCE: 1.2,
            LocationType.JAPAN: 1.1,
            LocationType.BRAZIL: 0.8,
            LocationType.INDIA: 0.6,
            LocationType.OTHER: 1.0
        }

    def calculate_market_rate(
        self, 
        influencer_profile: InfluencerProfile, 
        platform: PlatformType, 
        content_type: ContentType
    ) -> MarketRateData:
        """Calculate market rate for specific content type on platform."""
        try:
            # Get platform configuration
            platform_config = self.platform_configs.get(platform)
            if not platform_config:
                raise ValueError(f"Unsupported platform: {platform}")
            
            # Check if content type is valid for platform
            if content_type not in platform_config.base_rates:
                raise ValueError(f"Content type {content_type} not supported on {platform}")
            
            # Base rate per 1k followers
            base_rate = platform_config.base_rates[content_type]
            
            # Calculate engagement multiplier (convert rate to percentage and apply weight)
            engagement_multiplier = (
                (influencer_profile.engagement_rate * 100) * 
                platform_config.engagement_weight
            )
            
            # Follower multiplier (per 1k followers with platform weight)
            follower_multiplier = (
                (influencer_profile.followers / 1000) * 
                platform_config.follower_weight
            )
            
            # Location multiplier
            location_multiplier = self.location_multipliers.get(
                influencer_profile.location, 
                self.location_multipliers[LocationType.OTHER]
            )
            
            # Calculate final rate
            final_rate = (
                base_rate * 
                max(engagement_multiplier, 0.1) *  # Minimum 0.1 to avoid zero rates
                max(follower_multiplier, 1.0) *    # Minimum 1.0 for small accounts
                location_multiplier
            )
            
            return MarketRateData(
                platform=platform,
                content_type=content_type,
                base_rate_per_1k_followers=base_rate,
                engagement_multiplier=engagement_multiplier,
                location_multiplier=location_multiplier,
                final_rate=round(final_rate, 2)
            )
            
        except Exception as e:
            logger.error(f"Error calculating market rate: {e}")
            # Return a default minimal rate in case of error
            return MarketRateData(
                platform=platform,
                content_type=content_type,
                base_rate_per_1k_followers=0.5,
                engagement_multiplier=1.0,
                location_multiplier=1.0,
                final_rate=50.0  # Minimum default rate
            )

    def get_rate_breakdown(
        self, 
        influencer_profile: InfluencerProfile, 
        content_requirements: Dict[str, int]
    ) -> Dict[str, MarketRateData]:
        """Get rate breakdown for all requested content."""
        rate_breakdown = {}
        
        for content_key, quantity in content_requirements.items():
            try:
                # Parse content key (e.g., "instagram_post", "youtube_shorts")
                parts = content_key.split('_', 1)
                if len(parts) != 2:
                    continue
                    
                platform_str, content_str = parts
                
                # Map to enums
                platform = PlatformType(platform_str.lower())
                content_type = ContentType(content_str.lower())
                
                # Calculate rate
                rate_data = self.calculate_market_rate(
                    influencer_profile, platform, content_type
                )
                
                rate_breakdown[content_key] = rate_data
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Could not calculate rate for {content_key}: {e}")
                continue
        
        return rate_breakdown

    def calculate_total_campaign_cost(
        self, 
        influencer_profile: InfluencerProfile, 
        content_requirements: Dict[str, int],
        campaign_multiplier: float = 1.0
    ) -> Dict[str, float]:
        """Calculate total campaign cost with breakdown."""
        rate_breakdown = self.get_rate_breakdown(influencer_profile, content_requirements)
        
        total_cost = 0.0
        item_costs = {}
        
        for content_key, quantity in content_requirements.items():
            if content_key in rate_breakdown:
                rate_data = rate_breakdown[content_key]
                item_cost = rate_data.final_rate * quantity * campaign_multiplier
                item_costs[content_key] = {
                    "unit_rate": rate_data.final_rate,
                    "quantity": quantity,
                    "total": item_cost
                }
                total_cost += item_cost
        
        return {
            "total_cost": round(total_cost, 2),
            "item_breakdown": item_costs,
            "campaign_multiplier": campaign_multiplier
        }

    def suggest_alternative_pricing(
        self, 
        influencer_profile: InfluencerProfile,
        content_requirements: Dict[str, int],
        target_budget: float
    ) -> Dict[str, any]:
        """Suggest alternative pricing to fit budget."""
        current_cost = self.calculate_total_campaign_cost(
            influencer_profile, content_requirements
        )
        
        if current_cost["total_cost"] <= target_budget:
            return {
                "fits_budget": True,
                "current_cost": current_cost,
                "suggestions": []
            }
        
        suggestions = []
        
        # Suggestion 1: Reduce quantity proportionally
        reduction_factor = target_budget / current_cost["total_cost"]
        reduced_requirements = {}
        for content_key, quantity in content_requirements.items():
            reduced_quantity = max(1, int(quantity * reduction_factor))
            reduced_requirements[content_key] = reduced_quantity
        
        reduced_cost = self.calculate_total_campaign_cost(
            influencer_profile, reduced_requirements
        )
        
        suggestions.append({
            "type": "reduce_quantity",
            "description": "Reduce content quantity proportionally",
            "new_requirements": reduced_requirements,
            "estimated_cost": reduced_cost["total_cost"]
        })
        
        # Suggestion 2: Focus on lower-cost content types
        rate_breakdown = self.get_rate_breakdown(influencer_profile, content_requirements)
        sorted_rates = sorted(
            rate_breakdown.items(), 
            key=lambda x: x[1].final_rate
        )
        
        budget_focused_requirements = {}
        remaining_budget = target_budget
        
        for content_key, rate_data in sorted_rates:
            max_quantity = int(remaining_budget / rate_data.final_rate)
            if max_quantity > 0:
                budget_focused_requirements[content_key] = min(
                    max_quantity, 
                    content_requirements[content_key]
                )
                remaining_budget -= budget_focused_requirements[content_key] * rate_data.final_rate
        
        budget_focused_cost = self.calculate_total_campaign_cost(
            influencer_profile, budget_focused_requirements
        )
        
        suggestions.append({
            "type": "optimize_content_mix",
            "description": "Focus on cost-effective content types",
            "new_requirements": budget_focused_requirements,
            "estimated_cost": budget_focused_cost["total_cost"]
        })
        
        return {
            "fits_budget": False,
            "current_cost": current_cost,
            "target_budget": target_budget,
            "suggestions": suggestions
        }
