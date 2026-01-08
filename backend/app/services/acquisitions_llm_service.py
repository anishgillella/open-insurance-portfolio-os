"""LLM Service for Acquisition Calculator.

This module provides AI-powered analysis for the acquisition calculator:
- Comparable property matching and scoring
- Risk factor identification from property characteristics
- Uniqueness detection for routing to human consultants

Follows existing patterns from classification_service.py and renewal_forecast_service.py.
"""

import asyncio
import json
import logging
import re
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.acquisitions import AcquisitionCalculateRequest

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


class AcquisitionsLLMService:
    """AI-powered acquisition analysis using LLM.

    This service uses the same patterns as other LLM services in the codebase:
    - OpenRouter API with Gemini 2.5 Flash model
    - Retry logic with exponential backoff
    - JSON mode for structured responses
    """

    MAX_RETRIES = 3
    INITIAL_DELAY = 1.0
    BACKOFF_MULTIPLIER = 2.0

    def __init__(self, api_key: str | None = None):
        """Initialize the LLM service.

        Args:
            api_key: OpenRouter API key. If not provided, uses settings.
        """
        self.api_key = api_key or settings.openrouter_api_key

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Make LLM call with retry logic and JSON parsing.

        Args:
            system_prompt: System role instructions
            user_prompt: User message with task details
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (lower = more deterministic)

        Returns:
            Parsed JSON response from LLM

        Raises:
            Exception: After all retries exhausted
        """
        delay = self.INITIAL_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        OPENROUTER_URL,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://open-insurance.app",
                            "X-Title": "Open Insurance",
                        },
                        json={
                            "model": MODEL,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "response_format": {"type": "json_object"},
                        },
                    )

                    if response.status_code != 200:
                        logger.warning(
                            f"LLM API error: {response.status_code} - {response.text}"
                        )
                        raise Exception(f"API error: {response.status_code}")

                    content = response.json()["choices"][0]["message"]["content"]
                    return self._parse_json_response(content)

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    delay *= self.BACKOFF_MULTIPLIER
                else:
                    raise

            except Exception as e:
                logger.warning(f"LLM call failed on attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    delay *= self.BACKOFF_MULTIPLIER
                else:
                    raise

        # Should not reach here, but just in case
        raise Exception("All retry attempts exhausted")

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from LLM response with fallback handling.

        Args:
            content: Raw response content from LLM

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If JSON cannot be parsed
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
            if json_match:
                return json.loads(json_match.group(1))

            # Try to find raw JSON object
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                return json.loads(json_match.group())

            raise

    def _format_candidates(
        self,
        candidates: list[dict],
        target_lat: float | None = None,
        target_lng: float | None = None,
    ) -> str:
        """Format candidate properties for LLM prompt with distance info.

        Args:
            candidates: List of property dictionaries
            target_lat: Target property latitude (optional)
            target_lng: Target property longitude (optional)

        Returns:
            Formatted string for prompt
        """
        lines = []
        for i, prop in enumerate(candidates, 1):
            address = prop.get("address", {})
            if isinstance(address, dict):
                address_str = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')}"
                city = address.get("city", "Unknown")
                state = address.get("state", "Unknown")
            else:
                address_str = str(address)
                city = "Unknown"
                state = "Unknown"

            premium_per_unit = prop.get("premium_per_unit", 0)
            if premium_per_unit == 0 and prop.get("total_premium") and prop.get("total_units"):
                premium_per_unit = prop["total_premium"] / prop["total_units"]

            # Calculate distance if coordinates available
            distance_str = "Unknown"
            prop_lat = prop.get("latitude")
            prop_lng = prop.get("longitude")
            if target_lat and target_lng and prop_lat and prop_lng:
                distance_miles = self._calculate_distance(
                    target_lat, target_lng, prop_lat, prop_lng
                )
                distance_str = f"{distance_miles:.1f} miles"

            # Calculate SF per unit if available
            total_sf = prop.get("total_sf", 0)
            total_units = prop.get("total_units", 0)
            sf_per_unit = total_sf / total_units if total_units > 0 and total_sf > 0 else 0

            lines.append(
                f"""
Property {i}:
- ID: {prop.get('id', 'unknown')}
- Name: {prop.get('name', 'Unknown')}
- Address: {address_str}
- City/State: {city}, {state}
- Distance from Target: {distance_str}
- Year Built: {prop.get('year_built', 'Unknown')}
- Units: {total_units}
- Buildings: {prop.get('total_buildings', 1)}
- Total SF: {total_sf:,} sq ft
- SF/Unit: {sf_per_unit:,.0f} sq ft
- Property Type: {prop.get('property_type', 'Unknown')}
- Total Insured Value: ${prop.get('total_insured_value', 0):,.0f}
- Premium: ${prop.get('total_premium', 0):,.0f}
- Premium/Unit: ${premium_per_unit:,.0f}
"""
            )
        return "\n".join(lines)

    def _calculate_distance(
        self,
        lat1: float,
        lng1: float,
        lat2: float,
        lng2: float,
    ) -> float:
        """Calculate distance between two points using Haversine formula.

        Args:
            lat1, lng1: First point coordinates
            lat2, lng2: Second point coordinates

        Returns:
            Distance in miles
        """
        import math

        # Earth's radius in miles
        R = 3959

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def find_comparable_properties(
        self,
        target: AcquisitionCalculateRequest,
        candidates: list[dict],
        target_lat: float | None = None,
        target_lng: float | None = None,
    ) -> dict[str, Any]:
        """Score and rank comparable properties using LLM with weighted criteria.

        The LLM evaluates each candidate property against the target
        using a detailed weighted scoring system.

        Args:
            target: The property being evaluated for acquisition
            candidates: List of existing properties to compare against
            target_lat: Optional latitude for distance-based scoring
            target_lng: Optional longitude for distance-based scoring

        Returns:
            {
                "comparables": [{"property_id": ..., "score": 85, "reasoning": ..., "factor_scores": {...}}],
                "overall_assessment": "..."
            }
        """
        # Calculate SF per unit for target
        target_sf_per_unit = (
            target.total_sf / target.unit_count
            if target.unit_count > 0
            else 0
        )

        system_prompt = """You are an expert commercial real estate insurance analyst specializing in multi-family property premium estimation.

Your task is to score comparable properties using a WEIGHTED SCORING SYSTEM. Each factor has a specific weight and scoring criteria.

## WEIGHTED SCORING CRITERIA (Total: 100 points)

### 1. GEOGRAPHIC PROXIMITY (25 points max)
Score based on distance from target property:
- Same city: 25 points
- Within 25 miles: 20 points
- Same state, 25-100 miles: 15 points
- Same state, 100-200 miles: 10 points
- Same region (Midwest, etc.): 5 points
- Different region: 0 points

### 2. BUILDING VINTAGE (20 points max)
Score based on year built difference:
- Within 5 years: 20 points
- Within 10 years: 16 points
- Within 15 years: 12 points
- Within 20 years: 8 points
- Within 30 years: 4 points
- More than 30 years apart: 0 points
*IMPORTANT: Also consider construction era (pre-1970 vs modern) - deduct 5 points if different era*

### 3. SIZE METRICS (20 points max)
Evaluate THREE sub-factors:
a) Unit count difference (8 points max):
   - Within 10%: 8 pts | Within 25%: 6 pts | Within 50%: 4 pts | Within 100%: 2 pts | >100%: 0 pts

b) Building count similarity (6 points max):
   - Exact match: 6 pts | Within 2: 4 pts | Within 5: 2 pts | >5 difference: 0 pts

c) SF per unit ratio (6 points max):
   - Within 10%: 6 pts | Within 25%: 4 pts | Within 50%: 2 pts | >50%: 0 pts

### 4. CONSTRUCTION TYPE (15 points max)
- Same property type (Multi-Family, Mixed-Use, etc.): 10 points
- Same construction quality tier: 5 points
*Consider number of stories as construction indicator: 1-3 vs 4+ vs high-rise*

### 5. PROPERTY CLASS (10 points max)
Infer class from age, location, and income:
- Same estimated class (A, B, C): 10 points
- Adjacent class (A vs B, or B vs C): 5 points
- Different class (A vs C): 0 points

### 6. RISK PROFILE (10 points max)
Based on notes and location:
- Similar flood zone exposure: 3 points
- Similar wind/storm exposure: 3 points
- Similar age-related risks (wiring, plumbing): 2 points
- Similar tort environment: 2 points

## FINAL SCORE CALCULATION
Sum all factor scores (max 100). Properties scoring:
- 80-100: Excellent match - highly reliable for premium estimation
- 65-79: Good match - useful for estimation with minor adjustments
- 50-64: Fair match - use with caution, consider other factors
- Below 50: Poor match - limited usefulness

Always return valid JSON with detailed factor breakdowns."""

        user_prompt = f"""Score each candidate property against this TARGET PROPERTY using the weighted scoring criteria.

## TARGET PROPERTY
- Address: {target.address}
- Year Built: {target.vintage}
- Construction Era: {"Pre-1970 (vintage)" if target.vintage < 1970 else "1970-1999 (transitional)" if target.vintage < 2000 else "2000+ (modern)"}
- Units: {target.unit_count}
- Total Square Feet: {target.total_sf:,}
- SF per Unit: {target_sf_per_unit:,.0f}
- Buildings: {target.total_buildings}
- Stories: {target.stories}
- Current Occupancy: {target.current_occupancy_pct}%
- Estimated Annual Income: ${target.estimated_annual_income:,.0f}
- Income per Unit: ${target.estimated_annual_income / target.unit_count if target.unit_count > 0 else 0:,.0f}
- Notes: {target.notes or 'None provided'}

## CANDIDATE PROPERTIES
{self._format_candidates(candidates, target_lat, target_lng)}

## OUTPUT FORMAT
Return JSON in this exact format:
{{
  "comparables": [
    {{
      "property_id": "prop-1",
      "score": 78,
      "factor_scores": {{
        "geographic": 20,
        "vintage": 16,
        "size": 18,
        "construction": 12,
        "property_class": 7,
        "risk_profile": 5
      }},
      "reasoning": "Same city (Fort Wayne, IN) +25, vintage within 8 years +16, unit count within 15% +6, buildings match +6, similar SF/unit +4, same property type +10, similar class B +5, no flood risk noted +0. Total: 78"
    }}
  ],
  "overall_assessment": "Brief summary of comparable quality and any concerns"
}}

IMPORTANT:
1. Show factor breakdown in reasoning
2. Sort by score descending
3. Include ALL properties with score >= 40
4. Be precise with numeric comparisons"""

        try:
            return await self._call_llm(system_prompt, user_prompt, max_tokens=3000)
        except Exception as e:
            logger.error(f"Failed to find comparable properties: {e}")
            return {
                "comparables": [],
                "overall_assessment": "Unable to analyze comparables at this time.",
            }

    async def analyze_risk_factors(
        self,
        target: AcquisitionCalculateRequest,
    ) -> dict[str, Any]:
        """Identify risk factors from property characteristics using LLM.

        The LLM analyzes the property details and notes to identify
        insurance risk factors that would affect premiums.

        Args:
            target: The property being evaluated

        Returns:
            {
                "risk_factors": [
                    {"name": "Flood Zone", "severity": "warning", "reason": "...", "premium_impact": "+10-15%"}
                ]
            }
        """
        # Determine construction era for prompt
        if target.vintage < 1970:
            era = "pre-1970 (vintage)"
            era_risks = "High risk of outdated electrical, plumbing, and structural issues"
        elif target.vintage < 1990:
            era = "1970-1989 (transitional)"
            era_risks = "Moderate risk of outdated systems, asbestos, and code compliance issues"
        elif target.vintage < 2010:
            era = "1990-2009 (modern)"
            era_risks = "Generally compliant but may have dated HVAC or roofing"
        else:
            era = "2010+ (contemporary)"
            era_risks = "Low age-related risk, modern codes and materials"

        system_prompt = """You are a senior insurance underwriter specializing in commercial property risk assessment.

Your task is to identify ALL applicable risk factors that would affect insurance premiums for a multi-family property.

## RISK CATEGORIES TO EVALUATE

### NATURAL HAZARD RISKS
1. **Flood Zone** (CRITICAL if applicable)
   - Triggers: lakefront, riverfront, creek, stream, flood plain, low-lying, wetland, coastal
   - FEMA zones: A, AE, VE, X500 indicate flood risk
   - Premium impact: +20-40% for high-risk zones

2. **Wind Exposure** (CRITICAL in hurricane zones)
   - Triggers: coastal, beach, oceanfront, Gulf, Atlantic, hurricane-prone states (FL, TX, LA, SC, NC)
   - Consider: distance from coast, building height
   - Premium impact: +15-50% depending on exposure

3. **Fire Exposure** (CRITICAL in WUI areas)
   - Triggers: wildfire zone, WUI (wildland-urban interface), rural, forested, California mountains
   - Consider: distance to fire station, fire hydrants
   - Premium impact: +10-30% for high-risk areas

4. **Earthquake Zone** (CRITICAL in seismic zones)
   - Triggers: California, Pacific Northwest, Alaska, fault lines
   - Consider: building construction type (wood-frame better than unreinforced masonry)
   - Premium impact: Often requires separate policy

5. **Hail/Tornado Alley** (WARNING for Midwest)
   - Triggers: Texas, Oklahoma, Kansas, Nebraska, Midwest
   - Consider: roof type and age
   - Premium impact: +5-15%

### BUILDING CONDITION RISKS
6. **Vintage Wiring** (WARNING if pre-1970)
   - Triggers: built before 1970, knob-and-tube, aluminum wiring, fuse boxes
   - Requires evidence of electrical updates
   - Premium impact: +10-20% without updates

7. **Vintage Plumbing** (WARNING if pre-1970)
   - Triggers: built before 1970, galvanized pipes, cast iron, lead pipes
   - Look for mentions of plumbing replacement
   - Premium impact: +5-15% without updates

8. **Roof Concerns** (WARNING if old)
   - Triggers: flat roof, old roof, roof age mentions, tar roof
   - Consider: building age without roof replacement mention
   - Premium impact: +5-20% for aged roofs

### OPERATIONAL RISKS
9. **Tort Environment** (WARNING in litigious states)
   - High-risk states: Florida, California, New York, New Jersey, Illinois, Texas
   - Consider: slip-and-fall exposure, premises liability
   - Premium impact: +10-25% in high-litigation states

10. **Crime Exposure** (INFO to WARNING)
    - Triggers: high-crime area, urban core, security mentions needed
    - Consider: city size, neighborhood indicators
    - Premium impact: +5-15%

11. **Vacancy Risk** (WARNING if occupancy < 80%)
    - Triggers: low occupancy mentioned, partially vacant, under renovation
    - Premium impact: +10-30% for high vacancy

## SEVERITY LEVELS
- **critical**: Major risk requiring immediate underwriting attention, potential declination risk
- **warning**: Moderate risk that WILL affect premium, requires documentation
- **info**: Minor consideration, may not significantly impact premium

## IMPORTANT RULES
1. Only include risks with CLEAR EVIDENCE from the property details
2. Consider the ADDRESS for geographic/state-based risks
3. Use YEAR BUILT to assess building condition risks
4. Parse NOTES carefully for any risk indicators
5. Do NOT include a risk if there's no supporting evidence

Always return valid JSON."""

        user_prompt = f"""Analyze this property for ALL applicable insurance risk factors:

## PROPERTY DETAILS
- Address: {target.address}
- Year Built: {target.vintage}
- Construction Era: {era}
- Era Risk Assessment: {era_risks}
- Stories: {target.stories}
- Total Buildings: {target.total_buildings}
- Total Units: {target.unit_count}
- Total SF: {target.total_sf:,}
- Current Occupancy: {target.current_occupancy_pct}%
- Notes: {target.notes or 'None provided'}

## ANALYSIS INSTRUCTIONS
1. Parse the address for state/city to determine geographic risks
2. Check year built against building condition risk thresholds
3. Analyze notes for any hazard keywords
4. Check occupancy rate for vacancy risk
5. Consider state for tort environment

## OUTPUT FORMAT
Return JSON in this exact format:
{{
  "risk_factors": [
    {{
      "name": "Flood Zone",
      "severity": "warning",
      "reason": "Property notes mention 'lakefront' indicating proximity to water body. Flood zone verification recommended.",
      "premium_impact": "+15-25%"
    }},
    {{
      "name": "Vintage Wiring",
      "severity": "warning",
      "reason": "Building constructed in 1965, pre-dating modern NEC electrical codes. Evidence of electrical system updates not provided.",
      "premium_impact": "+10-15%"
    }}
  ],
  "overall_risk_assessment": "Moderate risk profile. Primary concerns are age-related building systems. Geographic risks appear low based on location."
}}

Be thorough but only include risks with clear supporting evidence."""

        try:
            result = await self._call_llm(
                system_prompt,
                user_prompt,
                max_tokens=1500,
                temperature=0.2,
            )
            return result
        except Exception as e:
            logger.error(f"Failed to analyze risk factors: {e}")
            return {"risk_factors": []}

    def assess_uniqueness(
        self,
        comparables_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Determine if property is too unique for automated pricing.

        This is a deterministic function (no LLM call) that evaluates
        the quality of comparable properties found.

        Criteria for "unique":
        - Average similarity score < 50, OR
        - Fewer than 3 properties with score > 60

        Args:
            comparables_result: Output from find_comparable_properties()

        Returns:
            {
                "is_unique": bool,
                "reason": str | None,
                "confidence": "high" | "medium" | "low"
            }
        """
        comparables = comparables_result.get("comparables", [])

        if not comparables:
            return {
                "is_unique": True,
                "reason": "No comparable properties found in the portfolio.",
                "confidence": "low",
            }

        # Calculate metrics
        scores = [c.get("score", 0) for c in comparables]
        top_scores = scores[:5]  # Consider top 5
        avg_score = sum(top_scores) / len(top_scores) if top_scores else 0
        good_matches = len([s for s in top_scores if s > 60])

        # Determine uniqueness
        if avg_score < 50 or good_matches < 3:
            return {
                "is_unique": True,
                "reason": (
                    f"Property characteristics are unusual. Best comparables have "
                    f"low similarity (avg: {avg_score:.0f}/100, only {good_matches} good matches)."
                ),
                "confidence": "low",
            }

        # Determine confidence based on match quality
        if avg_score >= 75 and good_matches >= 4:
            confidence = "high"
        elif avg_score >= 60 and good_matches >= 3:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "is_unique": False,
            "reason": None,
            "confidence": confidence,
        }


# Singleton pattern (following existing service patterns)
_acquisitions_llm_service: AcquisitionsLLMService | None = None


def get_acquisitions_llm_service() -> AcquisitionsLLMService:
    """Get or create the AcquisitionsLLMService singleton.

    Returns:
        The singleton AcquisitionsLLMService instance
    """
    global _acquisitions_llm_service
    if _acquisitions_llm_service is None:
        _acquisitions_llm_service = AcquisitionsLLMService()
    return _acquisitions_llm_service
