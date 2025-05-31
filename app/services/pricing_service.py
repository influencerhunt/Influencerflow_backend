from typing import Dict, List, Tuple
from app.models.negotiation_models import (
    InfluencerProfile, PlatformType, ContentType, LocationType, 
    MarketRateData, PlatformConfig
)
import json
import logging
import re

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        # Currency exchange rates (approximate, should be fetched from API in production)
        self.exchange_rates = {
            "USD": 1.0,        # Base currency
            "INR": 83.0,       # 1 USD = 83 INR (approximate)
            "EUR": 0.85,       # 1 USD = 0.85 EUR
            "GBP": 0.75,       # 1 USD = 0.75 GBP
            "CAD": 1.35,       # 1 USD = 1.35 CAD
            "AUD": 1.45,       # 1 USD = 1.45 AUD
            "BRL": 5.2         # 1 USD = 5.2 BRL
        }
        
        # Currency symbol mapping
        self.currency_symbols = {
            "$": "USD",
            "₹": "INR",
            "€": "EUR", 
            "£": "GBP",
            "C$": "CAD",
            "A$": "AUD",
            "R$": "BRL",
            "¥": "JPY"
        }
        
        # Enhanced location-based multipliers with currency support
        self.location_configs = {
            LocationType.US: {
                "multiplier": 1.8,
                "currency": "USD",
                "cultural_context": "direct",
                "negotiation_style": "professional_direct",
                "base_rate_per_1k": 15.0,
                "market_maturity": "high"
            },
            LocationType.UK: {
                "multiplier": 1.6,
                "currency": "GBP",
                "cultural_context": "polite_direct",
                "negotiation_style": "professional_courteous", 
                "base_rate_per_1k": 12.0,
                "market_maturity": "high"
            },
            LocationType.CANADA: {
                "multiplier": 1.5,
                "currency": "CAD",
                "cultural_context": "friendly_professional",
                "negotiation_style": "collaborative",
                "base_rate_per_1k": 11.0,
                "market_maturity": "high"
            },
            LocationType.AUSTRALIA: {
                "multiplier": 1.4,
                "currency": "AUD", 
                "cultural_context": "casual_professional",
                "negotiation_style": "straightforward",
                "base_rate_per_1k": 10.0,
                "market_maturity": "medium_high"
            },
            LocationType.GERMANY: {
                "multiplier": 1.3,
                "currency": "EUR",
                "cultural_context": "structured_professional",
                "negotiation_style": "detail_oriented",
                "base_rate_per_1k": 9.0,
                "market_maturity": "medium_high"
            },
            LocationType.FRANCE: {
                "multiplier": 1.2,
                "currency": "EUR",
                "cultural_context": "formal_elegant",
                "negotiation_style": "relationship_focused",
                "base_rate_per_1k": 8.0,
                "market_maturity": "medium"
            },
            LocationType.JAPAN: {
                "multiplier": 1.1,
                "currency": "USD",
                "cultural_context": "respectful_formal",
                "negotiation_style": "consensus_building",
                "base_rate_per_1k": 7.5,
                "market_maturity": "medium"
            },
            LocationType.BRAZIL: {
                "multiplier": 0.8,
                "currency": "BRL",
                "cultural_context": "warm_relationship",
                "negotiation_style": "personal_connection",
                "base_rate_per_1k": 4.5,
                "market_maturity": "emerging"
            },
            LocationType.INDIA: {
                "multiplier": 0.6,
                "currency": "INR", 
                "cultural_context": "relationship_respect",
                "negotiation_style": "value_conscious_respectful",
                "base_rate_per_1k": 200.0,  # Base rate in INR
                "market_maturity": "emerging_high_volume",
                "local_insights": {
                    "preferred_payment": "milestone_based",
                    "typical_negotiation": "expect_counter_offers",
                    "content_volume": "higher_quantity_expected",
                    "relationship_importance": "very_high",
                    "price_sensitivity": "high"
                }
            },
            LocationType.OTHER: {
                "multiplier": 1.0,
                "currency": "USD",
                "cultural_context": "adaptable",
                "negotiation_style": "flexible",
                "base_rate_per_1k": 6.0,
                "market_maturity": "medium"
            }
        }
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

    def parse_budget_amount(self, budget_input) -> Tuple[float, str]:
        """
        Parse budget input to extract amount and currency.
        
        Args:
            budget_input: Can be a string like "₹7,500", "$5000", or a float like 7500
            
        Returns:
            Tuple of (amount_in_usd, original_currency)
        """
        if isinstance(budget_input, (int, float)):
            # If it's just a number, assume USD
            return float(budget_input), "USD"
        
        if isinstance(budget_input, str):
            # Clean the string
            budget_str = budget_input.strip()
            
            # Extract currency symbol and amount using multiple patterns
            # Pattern 1: Symbol prefix (₹7,500, $100, €85)
            # Pattern 2: Currency code suffix (7500 INR, 100 USD)  
            # Pattern 3: Currency code prefix (INR 7500, USD 100)
            
            # More robust patterns that handle numbers with or without commas
            patterns = [
                r'([₹$€£¥])\s*([\d,]+(?:\.\d{2})?)',                 # ₹7,500 or ₹10000 - handles both
                r'([\d,]+(?:\.\d{2})?)\s+([A-Z]{3})',                # 7,500 INR or 7500 INR - handles both  
                r'([A-Z]{3})\s+([\d,]+(?:\.\d{2})?)'                 # INR 7,500 or INR 7500 - handles both
            ]
            
            symbol = None
            amount = 0
            currency_code = None
            
            for pattern in patterns:
                match = re.search(pattern, budget_str)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        # Determine which group is amount vs currency
                        if groups[0].isdigit() or ',' in groups[0] or '.' in groups[0]:
                            # First group is amount
                            amount = float(groups[0].replace(',', ''))
                            if groups[1] in self.exchange_rates:
                                currency_code = groups[1]
                        elif groups[1].isdigit() or ',' in groups[1] or '.' in groups[1]:
                            # Second group is amount
                            amount = float(groups[1].replace(',', ''))
                            if groups[0] in self.currency_symbols:
                                symbol = groups[0]
                                currency_code = self.currency_symbols[symbol]
                            elif groups[0] in self.exchange_rates:
                                currency_code = groups[0]
                    break
            
            if amount > 0:
                # Convert to USD
                if currency_code:
                    amount_usd = self.convert_to_usd(amount, currency_code)
                    return amount_usd, currency_code
                else:
                    return amount, "USD"  # Default to USD if no currency detected
            
        # Fallback - treat as USD
        try:
            amount = float(str(budget_input).replace(',', '').replace('$', '').replace('₹', ''))
            return amount, "USD"
        except:
            return 1000.0, "USD"  # Default fallback
    
    def convert_to_usd(self, amount: float, from_currency: str) -> float:
        """Convert amount from any currency to USD."""
        if from_currency == "USD":
            return amount
        
        exchange_rate = self.exchange_rates.get(from_currency, 1.0)
        # For most currencies, we divide by exchange rate to get USD
        # Example: ₹8300 / 83 = $100 USD
        return amount / exchange_rate
    
    def convert_from_usd(self, usd_amount: float, to_currency: str) -> float:
        """Convert USD amount to any currency."""
        if to_currency == "USD":
            return usd_amount
        
        exchange_rate = self.exchange_rates.get(to_currency, 1.0)
        return usd_amount * exchange_rate
    
    def format_currency(self, amount: float, currency: str) -> str:
        """Format amount with appropriate currency symbol."""
        symbol_map = {v: k for k, v in self.currency_symbols.items()}
        symbol = symbol_map.get(currency, "$")
        
        if currency == "INR":
            # Indian formatting with lakhs/crores
            if amount >= 10000000:  # 1 crore
                return f"₹{amount/10000000:.1f}Cr"
            elif amount >= 100000:  # 1 lakh
                return f"₹{amount/100000:.1f}L"
            else:
                return f"₹{amount:,.0f}"
        else:
            return f"{symbol}{amount:,.2f}"

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
                final_rate=round(final_rate, 2),
                base_rate=base_rate,
                engagement_bonus=engagement_multiplier,
                follower_bonus=follower_multiplier
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
                final_rate=50.0,  # Minimum default rate
                base_rate=0.5,
                engagement_bonus=1.0,
                follower_bonus=1.0
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
    
    def get_location_context(self, location: LocationType) -> Dict[str, any]:
        """Get detailed location context for pricing and negotiation strategy."""
        return self.location_configs.get(location, self.location_configs[LocationType.OTHER])
    
    def calculate_location_aware_rate(
        self, 
        influencer_profile: InfluencerProfile, 
        platform: PlatformType, 
        content_type: ContentType
    ) -> MarketRateData:
        """Enhanced market rate calculation with location intelligence."""
        # Get base market rate
        base_rate_data = self.calculate_market_rate(influencer_profile, platform, content_type)
        
        # Get location context
        location_context = self.get_location_context(influencer_profile.location)
        
        # Apply location-specific adjustments
        location_multiplier = location_context["multiplier"]
        base_rate_per_1k = location_context["base_rate_per_1k"]
        
        # For India and other emerging markets, use volume-based pricing
        if influencer_profile.location == LocationType.INDIA:
            # Indian market specific calculation
            adjusted_rate = self._calculate_indian_market_rate(
                influencer_profile, platform, content_type, base_rate_data
            )
        else:
            # Standard location multiplier application
            adjusted_rate = base_rate_data.final_rate * location_multiplier
        
        # Create enhanced rate data with location context
        return MarketRateData(
            platform=platform,
            content_type=content_type,
            base_rate=base_rate_data.final_rate / location_multiplier,  # Original base rate
            engagement_bonus=base_rate_data.final_rate * 0.1,  # Engagement component
            follower_bonus=base_rate_data.final_rate * 0.1,   # Follower component
            location_multiplier=location_multiplier,
            final_rate=adjusted_rate,
            currency=location_context["currency"],
            market_insights={
                "location": influencer_profile.location.value,
                "market_maturity": location_context["market_maturity"],
                "cultural_context": location_context["cultural_context"],
                "negotiation_style": location_context["negotiation_style"]
            }
        )
    
    def _calculate_indian_market_rate(
        self,
        influencer_profile: InfluencerProfile,
        platform: PlatformType,
        content_type: ContentType,
        base_rate_data: MarketRateData
    ) -> float:
        """Specialized pricing calculation for Indian market."""
        # Indian market characteristics
        followers = influencer_profile.followers
        engagement_rate = influencer_profile.engagement_rate
        
        # Tier-based pricing for Indian market
        if followers < 10000:  # Micro influencers
            base_per_1k = 1.5
            engagement_multiplier = 0.8
        elif followers < 50000:  # Small influencers  
            base_per_1k = 2.0
            engagement_multiplier = 1.0
        elif followers < 100000:  # Medium influencers
            base_per_1k = 2.5
            engagement_multiplier = 1.2
        elif followers < 500000:  # Large influencers
            base_per_1k = 3.0
            engagement_multiplier = 1.4
        else:  # Mega influencers
            base_per_1k = 4.0
            engagement_multiplier = 1.6
        
        # Platform adjustments for Indian market
        platform_multipliers = {
            PlatformType.INSTAGRAM: 1.0,
            PlatformType.YOUTUBE: 1.8,  # YouTube is very popular in India
            PlatformType.LINKEDIN: 0.7,
            PlatformType.TIKTOK: 0.6,   # Banned but similar platforms
            PlatformType.TWITTER: 0.5
        }
        
        # Content type adjustments
        content_multipliers = {
            ContentType.INSTAGRAM_REEL: 1.5,  # Reels are very popular in India
            ContentType.INSTAGRAM_POST: 1.0,
            ContentType.INSTAGRAM_STORY: 0.4,
            ContentType.YOUTUBE_LONG_FORM: 2.0,
            ContentType.YOUTUBE_SHORTS: 1.2,
            ContentType.LINKEDIN_POST: 0.8,
            ContentType.LINKEDIN_VIDEO: 1.0,
            ContentType.TWITTER_POST: 0.4,
            ContentType.TWITTER_VIDEO: 0.6
        }
        
        # Calculate rate
        follower_component = (followers / 1000) * base_per_1k
        engagement_component = follower_component * (engagement_rate * 100) * engagement_multiplier * 0.1
        platform_adjustment = platform_multipliers.get(platform, 1.0)
        content_adjustment = content_multipliers.get(content_type, 1.0)
        
        final_rate = (follower_component + engagement_component) * platform_adjustment * content_adjustment
        
        # Ensure minimum viable rate
        min_rate = 15.0 if followers > 1000 else 8.0
        
        return max(final_rate, min_rate)
    
    def get_negotiation_strategy(self, influencer_profile: InfluencerProfile) -> Dict[str, any]:
        """Get location-specific negotiation strategy and cultural insights."""
        location_context = self.get_location_context(influencer_profile.location)
        
        strategy = {
            "primary_approach": location_context["negotiation_style"],
            "cultural_context": location_context["cultural_context"],
            "market_maturity": location_context["market_maturity"],
            "currency": location_context["currency"]
        }
        
        # Add location-specific strategies
        if influencer_profile.location == LocationType.INDIA:
            strategy.update({
                "key_tactics": [
                    "Emphasize long-term partnership potential",
                    "Highlight brand prestige and portfolio value", 
                    "Be open to volume-based negotiations",
                    "Consider milestone-based payments",
                    "Show respect for creator's content quality"
                ],
                "cultural_notes": [
                    "Relationship building is crucial",
                    "Price negotiations are expected and welcomed",
                    "Family/team involvement in decisions is common",
                    "Timeline flexibility often requested",
                    "Portfolio enhancement value is important"
                ],
                "pricing_insights": [
                    "Volume discounts are common",
                    "Bundle deals preferred",
                    "Performance bonuses well received",
                    "Early payment discounts effective",
                    "Referral incentives valued"
                ]
            })
        elif influencer_profile.location == LocationType.US:
            strategy.update({
                "key_tactics": [
                    "Be direct and professional",
                    "Focus on ROI and performance metrics",
                    "Emphasize brand alignment and values",
                    "Offer clear terms and quick decisions"
                ],
                "cultural_notes": [
                    "Time is valued highly",
                    "Professional boundaries respected", 
                    "Contract details important",
                    "Performance measurement expected"
                ]
            })
        elif influencer_profile.location == LocationType.BRAZIL:
            strategy.update({
                "key_tactics": [
                    "Build personal connection first",
                    "Show enthusiasm for collaboration",
                    "Be flexible on creative control",
                    "Emphasize brand story and values"
                ],
                "cultural_notes": [
                    "Relationships come before business",
                    "Warm, personal communication preferred",
                    "Creative freedom highly valued",
                    "Social impact considerations important"
                ]
            })
        
        return strategy
    
    def generate_location_specific_proposal(
        self,
        influencer_profile: InfluencerProfile,
        content_requirements: Dict[str, int],
        brand_budget: float  # This is already in USD from parse_budget_amount
    ) -> Dict[str, any]:
        """Generate a culturally appropriate proposal based on location that respects the brand budget."""
        location_context = self.get_location_context(influencer_profile.location)
        negotiation_strategy = self.get_negotiation_strategy(influencer_profile)
        
        # CRITICAL: brand_budget is already in USD, so we use it directly
        # Calculate market rates first
        total_market_cost = 0.0
        item_breakdown = {}
        
        for content_key, quantity in content_requirements.items():
            try:
                parts = content_key.split('_', 1)
                if len(parts) == 2:
                    platform_str, content_str = parts
                    platform = PlatformType(platform_str.lower())
                    content_type = ContentType(content_str.lower())
                    
                    rate_data = self.calculate_location_aware_rate(
                        influencer_profile, platform, content_type
                    )
                    
                    item_total = rate_data.final_rate * quantity
                    total_market_cost += item_total
                    
                    item_breakdown[content_key] = {
                        "unit_rate": rate_data.final_rate,
                        "quantity": quantity,
                        "total": item_total,
                        "market_insights": rate_data.market_insights
                    }
            except (ValueError, KeyError):
                continue
        
        # FIXED: Respect budget constraints strictly - never exceed brand_budget
        if total_market_cost > brand_budget:
            # Scale down the rates proportionally to fit budget
            budget_ratio = brand_budget / total_market_cost
            adjusted_total_cost = 0.0
            
            # Apply budget scaling to each item
            for content_key in item_breakdown:
                original_unit_rate = item_breakdown[content_key]["unit_rate"]
                adjusted_unit_rate = original_unit_rate * budget_ratio
                quantity = item_breakdown[content_key]["quantity"]
                adjusted_total = adjusted_unit_rate * quantity
                
                item_breakdown[content_key]["unit_rate"] = adjusted_unit_rate
                item_breakdown[content_key]["total"] = adjusted_total
                adjusted_total_cost += adjusted_total
            
            final_cost = adjusted_total_cost  # This will be <= brand_budget
            budget_note = f"Adjusted rates to fit within budget constraint"
        else:
            # Even if market cost is lower, stay within budget
            final_cost = min(total_market_cost, brand_budget)
            budget_note = "Market rates are within budget range"
        
        # Generate location-specific proposal structure
        proposal = {
            "total_cost": final_cost,
            "item_breakdown": item_breakdown,
            "currency": location_context["currency"],
            "negotiation_strategy": negotiation_strategy,
            "cultural_approach": location_context["cultural_context"],
            "payment_recommendations": self._get_payment_recommendations(influencer_profile.location),
            "timeline_considerations": self._get_timeline_recommendations(influencer_profile.location),
            "budget_analysis": {
                "brand_budget": brand_budget,
                "market_cost": total_market_cost,
                "final_cost": final_cost,
                "note": budget_note
            }
        }
        
        # Add special considerations for specific markets
        if influencer_profile.location == LocationType.INDIA:
            proposal["india_specific"] = {
                "volume_discount_available": final_cost > 1000,
                "suggested_bundle_approach": True,
                "milestone_payment_preferred": True,
                "portfolio_value_emphasis": True,
                "relationship_building_priority": "high"
            }
        
        return proposal
    
    def generate_budget_constrained_proposal(
        self,
        influencer_profile: InfluencerProfile,
        content_requirements: Dict[str, int],
        brand_budget: float,  # Already in USD
        negotiation_flexibility_percent: float = 15.0  # Default 15% flexibility
    ) -> Dict[str, any]:
        """
        Generate a proposal that respects budget constraints with limited negotiation flexibility.
        
        Three scenarios:
        1. Market rates <= budget: Use market rates
        2. Market rates 10-20% above budget: Negotiate within flexibility range
        3. Market rates >20% above budget: Scale down to budget + max flexibility
        
        Args:
            influencer_profile: The influencer's profile
            content_requirements: Dictionary of content types and quantities
            brand_budget: Brand's maximum budget in USD
            negotiation_flexibility_percent: Maximum % above budget for negotiation (10-20%)
        
        Returns:
            Dictionary with proposal details and budget analysis
        """
        logger.info(f"Generating budget-constrained proposal for budget ${brand_budget:.2f} with {negotiation_flexibility_percent}% flexibility")
        
        # Calculate absolute maximum budget (budget + flexibility)
        max_negotiation_budget = brand_budget * (1 + negotiation_flexibility_percent / 100)
        
        # First, calculate pure market rates
        total_market_cost = 0.0
        item_breakdown = {}
        
        for content_key, quantity in content_requirements.items():
            try:
                parts = content_key.split('_', 1)
                if len(parts) == 2:
                    platform_str, content_str = parts
                    platform = PlatformType(platform_str.lower())
                    content_type = ContentType(content_str.lower())
                    
                    rate_data = self.calculate_location_aware_rate(
                        influencer_profile, platform, content_type
                    )
                    
                    item_total = rate_data.final_rate * quantity
                    total_market_cost += item_total
                    
                    item_breakdown[content_key] = {
                        "market_unit_rate": rate_data.final_rate,
                        "quantity": quantity,
                        "market_total": item_total,
                        "market_insights": rate_data.market_insights
                    }
            except (ValueError, KeyError):
                logger.warning(f"Invalid content key format: {content_key}")
                continue
        
        # Determine negotiation strategy based on market cost vs budget
        budget_ratio = total_market_cost / brand_budget if brand_budget > 0 else float('inf')
        
        if budget_ratio <= 1.0:
            # Scenario 1: Market rates are within budget - use market rates
            strategy = "within_budget"
            final_total_cost = total_market_cost
            negotiation_message = "Market rates are within your budget. This is an excellent opportunity!"
            
            # Keep market rates as final rates
            for content_key in item_breakdown:
                item_breakdown[content_key]["final_unit_rate"] = item_breakdown[content_key]["market_unit_rate"]
                item_breakdown[content_key]["final_total"] = item_breakdown[content_key]["market_total"]
                # COMPATIBILITY: Add legacy keys expected by conversation handler
                item_breakdown[content_key]["unit_rate"] = item_breakdown[content_key]["market_unit_rate"]
                item_breakdown[content_key]["total"] = item_breakdown[content_key]["market_total"]
                
        elif budget_ratio <= (1 + negotiation_flexibility_percent / 100):
            # Scenario 2: Market rates are 10-20% above budget - start negotiation at budget, allow up to flexibility
            strategy = "negotiable_above_budget"
            # CRITICAL FIX: Start at budget, not market rates, but allow negotiation up to max_negotiation_budget
            final_total_cost = brand_budget  # Start negotiation at budget level
            overage_percent = (budget_ratio - 1) * 100
            negotiation_message = f"Market rates are {overage_percent:.1f}% above budget. We'll start at your budget and negotiate up to {negotiation_flexibility_percent}% if needed."
            
            # Scale rates to budget level but mark as negotiable up to market rates
            budget_scaling_factor = brand_budget / total_market_cost
            for content_key in item_breakdown:
                market_rate = item_breakdown[content_key]["market_unit_rate"]
                budget_rate = market_rate * budget_scaling_factor
                quantity = item_breakdown[content_key]["quantity"]
                
                item_breakdown[content_key]["final_unit_rate"] = budget_rate
                item_breakdown[content_key]["final_total"] = budget_rate * quantity
                item_breakdown[content_key]["market_unit_rate_for_negotiation"] = market_rate
                item_breakdown[content_key]["negotiation_note"] = f"Starting at budget rate, can negotiate up to market rate (${market_rate:.2f})"
                # COMPATIBILITY: Add legacy keys expected by conversation handler
                item_breakdown[content_key]["unit_rate"] = budget_rate
                item_breakdown[content_key]["total"] = budget_rate * quantity
                
        else:
            # Scenario 3: Market rates are >20% above budget - scale down to max flexibility
            strategy = "scale_to_max_budget"
            final_total_cost = max_negotiation_budget
            scaling_factor = max_negotiation_budget / total_market_cost
            overage_percent = (budget_ratio - 1) * 100
            negotiation_message = f"Market rates are {overage_percent:.1f}% above budget. We've adjusted to our maximum flexibility of {negotiation_flexibility_percent}% above budget."
            
            # Scale down all rates proportionally to fit within max budget
            for content_key in item_breakdown:
                original_rate = item_breakdown[content_key]["market_unit_rate"]
                scaled_rate = original_rate * scaling_factor
                quantity = item_breakdown[content_key]["quantity"]
                
                item_breakdown[content_key]["final_unit_rate"] = scaled_rate
                item_breakdown[content_key]["final_total"] = scaled_rate * quantity
                item_breakdown[content_key]["scaling_factor"] = scaling_factor
                item_breakdown[content_key]["negotiation_note"] = f"Rate scaled by {scaling_factor:.2f} to fit within maximum budget flexibility"
                # COMPATIBILITY: Add legacy keys expected by conversation handler
                item_breakdown[content_key]["unit_rate"] = scaled_rate
                item_breakdown[content_key]["total"] = scaled_rate * quantity
        
        # Get location context for cultural approach
        location_context = self.get_location_context(influencer_profile.location)
        negotiation_strategy = self.get_negotiation_strategy(influencer_profile)
        
        # Generate comprehensive budget analysis
        budget_analysis = {
            "brand_budget": brand_budget,
            "negotiation_flexibility_percent": negotiation_flexibility_percent,
            "max_negotiation_budget": max_negotiation_budget,
            "total_market_cost": total_market_cost,
            "final_proposed_cost": final_total_cost,
            "budget_ratio": budget_ratio,
            "strategy": strategy,
            "negotiation_message": negotiation_message,
            "overage_amount": max(0, total_market_cost - brand_budget),
            "within_flexibility": budget_ratio <= (1 + negotiation_flexibility_percent / 100),
            "requires_scaling": strategy == "scale_to_max_budget"
        }
        
        # Add strategy-specific guidance for negotiations
        if strategy == "within_budget":
            negotiation_guidance = {
                "approach": "confident",
                "talking_points": [
                    "Market rates align perfectly with your budget",
                    "This represents excellent value for the deliverables",
                    "No budget constraints limit this collaboration"
                ],
                "flexibility": "Can offer additional value within budget"
            }
        elif strategy == "negotiable_above_budget":
            negotiation_guidance = {
                "approach": "collaborative",
                "talking_points": [
                    f"Market rates are {(budget_ratio - 1) * 100:.1f}% above budget",
                    "This is within our negotiation flexibility range",
                    "We can work together to find the right balance"
                ],
                "flexibility": f"Up to {negotiation_flexibility_percent}% above budget"
            }
        else:  # scale_to_max_budget
            negotiation_guidance = {
                "approach": "budget_conscious",
                "talking_points": [
                    f"Market rates exceed budget by {(budget_ratio - 1) * 100:.1f}%",
                    f"We've adjusted to our maximum flexibility of {negotiation_flexibility_percent}%",
                    "Rates have been scaled to fit within budget constraints"
                ],
                "flexibility": f"Maximum {negotiation_flexibility_percent}% above budget (${max_negotiation_budget:.2f})"
            }
        
        proposal = {
            "total_cost": final_total_cost,
            "item_breakdown": item_breakdown,
            "currency": location_context["currency"],
            "negotiation_strategy": negotiation_strategy,
            "budget_analysis": budget_analysis,
            "negotiation_guidance": negotiation_guidance,
            "cultural_approach": location_context["cultural_context"],
            "payment_recommendations": self._get_payment_recommendations(influencer_profile.location),
            "timeline_considerations": self._get_timeline_recommendations(influencer_profile.location)
        }
        
        # Add location-specific considerations
        if influencer_profile.location == LocationType.INDIA:
            proposal["india_specific"] = {
                "volume_discount_available": final_total_cost > 1000,
                "suggested_bundle_approach": True,
                "milestone_payment_preferred": True,
                "portfolio_value_emphasis": True,  # Added for conversation handler compatibility
                "budget_consciousness": "high",
                "relationship_building_priority": "very_high",
                "flexibility_note": "Indian market typically expects some negotiation flexibility"
            }
        
        logger.info(f"Budget-constrained proposal generated: ${final_total_cost:.2f} (strategy: {strategy})")
        return proposal

    def _get_payment_recommendations(self, location: LocationType) -> List[str]:
        """Get location-specific payment recommendations."""
        payment_recs = {
            LocationType.INDIA: [
                "50% advance, 50% on completion",
                "Milestone-based payments preferred",
                "UPI/bank transfer commonly used",
                "Consider early payment discount (2-3%)"
            ],
            LocationType.US: [
                "Standard NET-30 terms acceptable",
                "Wire transfer or ACH preferred",
                "50/50 split common for new relationships"
            ],
            LocationType.BRAZIL: [
                "Payment in USD preferred",
                "50% advance due to currency fluctuation",
                "Local bank transfer available"
            ]
        }
        return payment_recs.get(location, ["50% advance, 50% on completion"])
    
    def _get_timeline_recommendations(self, location: LocationType) -> List[str]:
        """Get location-specific timeline recommendations."""
        timeline_recs = {
            LocationType.INDIA: [
                "Allow 2-3 extra days for content creation",
                "Festival seasons may affect timeline",
                "Weekend work flexibility often available"
            ],
            LocationType.US: [
                "Standard business timelines expected",
                "Holiday seasons may impact delivery",
                "Rush jobs typically cost 25-50% extra"
            ],
            LocationType.BRAZIL: [
                "Carnival season affects February timeline",
                "Flexible timing for creative process",
                "Weekend work common"
            ]
        }
        return timeline_recs.get(location, ["Standard timeline expectations"])
