"""Market Intelligence Service - Live market research using Parallel AI.

This service provides real-time market intelligence by:
1. Using Parallel AI Task API to research current market conditions
2. Using Gemini to structure the raw research into typed schemas

This enhances the existing market_context_service.py which analyzes
internal policy data. This service adds external market research.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.property import Property
from app.models.insurance_program import InsuranceProgram
from app.models.policy import Policy
from app.services.parallel_client import (
    ParallelClient,
    ParallelClientError,
    ParallelTaskResult,
    get_parallel_client,
)

logger = logging.getLogger(__name__)

# OpenRouter API for Gemini structuring
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL = "google/gemini-2.5-flash"


class MarketIntelligenceError(Exception):
    """Base exception for market intelligence errors."""
    pass


@dataclass
class MarketTrend:
    """Market trend information."""
    rate_change_pct: float | None = None
    rate_change_range: str | None = None
    direction: str = "stable"  # increasing, decreasing, stable, volatile
    confidence: str = "medium"  # low, medium, high


@dataclass
class CarrierAppetite:
    """Carrier appetite assessment."""
    carrier_name: str
    appetite: str  # expanding, stable, contracting, exiting
    notes: str | None = None


@dataclass
class MarketIntelligenceResult:
    """Result from market intelligence research."""

    property_id: str
    property_type: str
    state: str
    research_date: datetime

    # Rate trends
    rate_trend: MarketTrend
    rate_trend_reasoning: str | None

    # Key market factors
    key_factors: list[str]
    factor_details: dict[str, str]

    # Carrier landscape
    carrier_appetite: list[CarrierAppetite]
    carrier_summary: str | None

    # Forecasts
    forecast_6mo: str | None
    forecast_12mo: str | None

    # Regulatory and market changes
    regulatory_changes: list[str]
    market_developments: list[str]

    # Benchmarks
    premium_benchmark: str | None
    rate_per_sqft: float | None

    # Sources
    sources: list[str]

    # Metadata
    parallel_latency_ms: int
    gemini_latency_ms: int
    total_latency_ms: int
    raw_research: str | None = None


# Gemini prompt for structuring market research
STRUCTURE_MARKET_RESEARCH_PROMPT = """You are an expert at extracting structured data from insurance market research.

Analyze the following market research and extract structured information.

MARKET RESEARCH:
{research_text}

PROPERTY CONTEXT:
- Property Type: {property_type}
- State: {state}
- TIV: {tiv}

Extract the following information and return as JSON:

{{
    "rate_trend": {{
        "rate_change_pct": <number or null - estimated YoY rate change percentage>,
        "rate_change_range": "<string like '5-10%' or '8-12%' or null>",
        "direction": "<increasing|decreasing|stable|volatile>",
        "confidence": "<low|medium|high>"
    }},
    "rate_trend_reasoning": "<2-3 sentence explanation of why rates are moving this direction>",
    "key_factors": [
        "<factor 1 - brief description>",
        "<factor 2 - brief description>"
    ],
    "factor_details": {{
        "<factor name>": "<detailed explanation>",
    }},
    "carrier_appetite": [
        {{
            "carrier_name": "<carrier name>",
            "appetite": "<expanding|stable|contracting|exiting>",
            "notes": "<brief notes>"
        }}
    ],
    "carrier_summary": "<1-2 sentence summary of carrier landscape>",
    "forecast_6mo": "<prediction for next 6 months>",
    "forecast_12mo": "<prediction for next 12 months or null>",
    "regulatory_changes": [
        "<regulatory change 1>",
        "<regulatory change 2>"
    ],
    "market_developments": [
        "<market development 1>",
        "<market development 2>"
    ],
    "premium_benchmark": "<any premium benchmarks mentioned like '$X per $100 TIV' or rate per sqft>",
    "rate_per_sqft": <number or null - rate per square foot if mentioned>,
    "sources": [
        "<source 1>",
        "<source 2>"
    ]
}}

Return ONLY valid JSON. If information is not available in the research, use null or empty arrays.
Be specific and cite actual numbers from the research where available."""


class MarketIntelligenceService:
    """Service for researching live market intelligence."""

    def __init__(
        self,
        session: AsyncSession,
        parallel_client: ParallelClient | None = None,
        openrouter_api_key: str | None = None,
    ):
        """Initialize market intelligence service.

        Args:
            session: Database session.
            parallel_client: Parallel AI client. Created if not provided.
            openrouter_api_key: OpenRouter API key for Gemini. Defaults to settings.
        """
        self.session = session
        self.parallel_client = parallel_client or get_parallel_client()
        self.openrouter_api_key = openrouter_api_key or settings.openrouter_api_key

        if not self.parallel_client.api_key:
            logger.warning("Parallel API key not configured for market intelligence")
        if not self.openrouter_api_key:
            logger.warning("OpenRouter API key not configured for structuring")

    async def get_market_intelligence(
        self,
        property_id: str,
        include_raw_research: bool = False,
    ) -> MarketIntelligenceResult:
        """Get live market intelligence for a property.

        This method:
        1. Loads property data to understand context
        2. Calls Parallel AI to research market conditions
        3. Uses Gemini to structure the research into typed data

        Args:
            property_id: Property ID.
            include_raw_research: Include raw research text in result.

        Returns:
            MarketIntelligenceResult with structured market data.

        Raises:
            MarketIntelligenceError: If research fails.
        """
        if not self.parallel_client.api_key:
            raise MarketIntelligenceError("Parallel API key not configured")
        if not self.openrouter_api_key:
            raise MarketIntelligenceError("OpenRouter API key not configured")

        # Load property
        prop = await self._load_property(property_id)
        if not prop:
            raise MarketIntelligenceError(f"Property {property_id} not found")

        # Get property context
        property_type = prop.property_type or "commercial property"
        state = prop.state or "unknown"
        tiv = await self._calculate_tiv(prop)
        carrier = await self._get_primary_carrier(prop)

        start_time = time.time()

        # Step 1: Research with Parallel AI
        try:
            parallel_result = await self.parallel_client.research_market_conditions(
                property_type=property_type,
                state=state,
                tiv=float(tiv) if tiv else None,
                carrier=carrier,
            )
        except ParallelClientError as e:
            raise MarketIntelligenceError(f"Parallel AI research failed: {e}")

        parallel_latency = parallel_result.latency_ms

        # Step 2: Structure with Gemini
        gemini_start = time.time()
        structured_data = await self._structure_research(
            research_text=parallel_result.output,
            property_type=property_type,
            state=state,
            tiv=tiv,
        )
        gemini_latency = int((time.time() - gemini_start) * 1000)

        total_latency = int((time.time() - start_time) * 1000)

        # Build result
        result = MarketIntelligenceResult(
            property_id=property_id,
            property_type=property_type,
            state=state,
            research_date=datetime.now(timezone.utc),
            rate_trend=MarketTrend(
                rate_change_pct=structured_data.get("rate_trend", {}).get("rate_change_pct"),
                rate_change_range=structured_data.get("rate_trend", {}).get("rate_change_range"),
                direction=structured_data.get("rate_trend", {}).get("direction", "stable"),
                confidence=structured_data.get("rate_trend", {}).get("confidence", "medium"),
            ),
            rate_trend_reasoning=structured_data.get("rate_trend_reasoning"),
            key_factors=structured_data.get("key_factors", []),
            factor_details=structured_data.get("factor_details", {}),
            carrier_appetite=[
                CarrierAppetite(
                    carrier_name=ca.get("carrier_name", "Unknown"),
                    appetite=ca.get("appetite", "stable"),
                    notes=ca.get("notes"),
                )
                for ca in structured_data.get("carrier_appetite", [])
            ],
            carrier_summary=structured_data.get("carrier_summary"),
            forecast_6mo=structured_data.get("forecast_6mo"),
            forecast_12mo=structured_data.get("forecast_12mo"),
            regulatory_changes=structured_data.get("regulatory_changes", []),
            market_developments=structured_data.get("market_developments", []),
            premium_benchmark=structured_data.get("premium_benchmark"),
            rate_per_sqft=structured_data.get("rate_per_sqft"),
            sources=structured_data.get("sources", []) or (
                [s.get("url", s.get("title", str(s))) for s in parallel_result.sources]
                if parallel_result.sources
                else []
            ),
            parallel_latency_ms=parallel_latency,
            gemini_latency_ms=gemini_latency,
            total_latency_ms=total_latency,
            raw_research=parallel_result.output if include_raw_research else None,
        )

        logger.info(
            f"Market intelligence for {property_id}: "
            f"rate trend {result.rate_trend.direction} ({result.rate_trend.rate_change_range}), "
            f"latency {total_latency}ms"
        )

        return result

    async def get_market_intelligence_for_renewal(
        self,
        property_id: str,
    ) -> dict[str, Any]:
        """Get market intelligence formatted for renewal context.

        Returns a simplified dict suitable for including in renewal forecasts.

        Args:
            property_id: Property ID.

        Returns:
            Dict with market intelligence for renewals.
        """
        try:
            result = await self.get_market_intelligence(property_id)

            return {
                "rate_trend_pct": result.rate_trend.rate_change_pct,
                "rate_trend_range": result.rate_trend.rate_change_range,
                "rate_direction": result.rate_trend.direction,
                "key_factors": result.key_factors[:5],  # Top 5 factors
                "carrier_appetite": {
                    ca.carrier_name: ca.appetite
                    for ca in result.carrier_appetite[:5]
                },
                "forecast_6mo": result.forecast_6mo,
                "regulatory_changes": result.regulatory_changes[:3],
                "sources": result.sources[:5],
                "research_date": result.research_date.isoformat(),
            }
        except MarketIntelligenceError as e:
            logger.warning(f"Market intelligence unavailable: {e}")
            return {
                "error": str(e),
                "available": False,
            }

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _load_property(self, property_id: str) -> Property | None:
        """Load property with context."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.buildings),
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                ),
            )
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _calculate_tiv(self, prop: Property) -> Decimal | None:
        """Calculate total insured value for property."""
        # Try to get from active program
        if prop.insurance_programs:
            active = next(
                (p for p in prop.insurance_programs if p.status == "active"),
                None
            )
            if active and active.total_insured_value:
                return active.total_insured_value

        # Fall back to building values
        if prop.buildings:
            total = sum(
                b.building_value or Decimal("0")
                for b in prop.buildings
            )
            if total > 0:
                return total

        return None

    async def _get_primary_carrier(self, prop: Property) -> str | None:
        """Get primary carrier name from active program."""
        if not prop.insurance_programs:
            return None

        active = next(
            (p for p in prop.insurance_programs if p.status == "active"),
            None
        )
        if not active:
            return None

        # Find property policy for primary carrier
        for policy in active.policies:
            if policy.policy_type in ("property", "package"):
                return policy.carrier_name

        # Fall back to first policy
        if active.policies:
            return active.policies[0].carrier_name

        return None

    async def _structure_research(
        self,
        research_text: str,
        property_type: str,
        state: str,
        tiv: Decimal | None,
    ) -> dict[str, Any]:
        """Structure raw research using Gemini.

        Args:
            research_text: Raw research from Parallel AI.
            property_type: Property type.
            state: State code.
            tiv: Total insured value.

        Returns:
            Structured dict with extracted data.
        """
        tiv_str = f"${float(tiv):,.0f}" if tiv else "Not specified"

        prompt = STRUCTURE_MARKET_RESEARCH_PROMPT.format(
            research_text=research_text,
            property_type=property_type,
            state=state,
            tiv=tiv_str,
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Market Intelligence",
                },
                json={
                    "model": GEMINI_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.1,  # Low temperature for structured extraction
                },
            )

            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return self._default_structure()

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                return self._default_structure()

            content = choices[0].get("message", {}).get("content", "")
            return self._parse_json_response(content)

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Try to find JSON object in content
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            logger.warning("Failed to parse Gemini response as JSON")
            return self._default_structure()

    def _default_structure(self) -> dict[str, Any]:
        """Return default structure when parsing fails."""
        return {
            "rate_trend": {
                "rate_change_pct": None,
                "rate_change_range": None,
                "direction": "stable",
                "confidence": "low",
            },
            "rate_trend_reasoning": None,
            "key_factors": [],
            "factor_details": {},
            "carrier_appetite": [],
            "carrier_summary": None,
            "forecast_6mo": None,
            "forecast_12mo": None,
            "regulatory_changes": [],
            "market_developments": [],
            "premium_benchmark": None,
            "rate_per_sqft": None,
            "sources": [],
        }


def get_market_intelligence_service(
    session: AsyncSession,
) -> MarketIntelligenceService:
    """Factory function to create MarketIntelligenceService.

    Args:
        session: Database session.

    Returns:
        MarketIntelligenceService instance.
    """
    return MarketIntelligenceService(session)
