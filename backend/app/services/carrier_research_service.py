"""Carrier Research Service.

Research carrier financial strength and market position using Parallel AI:
- A.M. Best ratings
- S&P/Moody's ratings
- Market specialty areas
- Recent news and developments
- Customer satisfaction
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.parallel_client import (
    ParallelClient,
    ParallelClientError,
    get_parallel_client,
)

logger = logging.getLogger(__name__)

# OpenRouter API for Gemini structuring
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL = "google/gemini-2.5-flash"


class CarrierResearchError(Exception):
    """Base exception for carrier research errors."""
    pass


@dataclass
class CarrierRatings:
    """Carrier financial ratings."""
    am_best_rating: str | None = None
    am_best_outlook: str | None = None  # positive, stable, negative
    sp_rating: str | None = None
    moodys_rating: str | None = None
    rating_date: str | None = None


@dataclass
class CarrierSpecialty:
    """Carrier specialty area."""
    line_of_business: str
    expertise_level: str = "moderate"  # limited, moderate, strong, specialty
    notes: str | None = None


@dataclass
class CarrierNews:
    """Recent carrier news item."""
    date: str | None
    headline: str
    summary: str | None
    sentiment: str = "neutral"  # positive, negative, neutral
    source: str | None = None


@dataclass
class CarrierResearchResult:
    """Complete carrier research result."""

    carrier_name: str
    research_date: datetime

    # Ratings
    ratings: CarrierRatings

    # Financial health
    financial_strength: str  # very_strong, strong, adequate, weak, unknown
    financial_summary: str | None

    # Specialties
    specialty_areas: list[CarrierSpecialty]
    primary_lines: list[str]

    # Market position
    market_position: str | None
    geographic_focus: list[str]
    target_segments: list[str]

    # Appetite
    commercial_property_appetite: str  # expanding, stable, contracting, selective, exiting
    appetite_notes: str | None

    # Recent news
    recent_news: list[CarrierNews]
    news_summary: str | None

    # Customer experience
    customer_satisfaction: str | None  # excellent, good, average, poor, unknown
    claims_reputation: str | None

    # Concerns
    concerns: list[str]
    regulatory_issues: list[str]

    # Sources
    sources: list[str]

    # Metadata
    parallel_latency_ms: int
    gemini_latency_ms: int
    total_latency_ms: int
    raw_research: str | None = None


# Gemini prompt for structuring carrier research
STRUCTURE_CARRIER_RESEARCH_PROMPT = """You are an expert at extracting structured carrier data from research.

Analyze the following carrier research and extract structured information.

CARRIER RESEARCH:
{research_text}

CARRIER NAME:
{carrier_name}

PROPERTY TYPE CONTEXT (if any):
{property_type}

Extract the following information and return as JSON:

{{
    "ratings": {{
        "am_best_rating": "<A.M. Best rating like A++, A+, A, A-, B++, etc. or null>",
        "am_best_outlook": "<positive|stable|negative|null>",
        "sp_rating": "<S&P rating like AAA, AA+, AA, AA-, A+, etc. or null>",
        "moodys_rating": "<Moody's rating or null>",
        "rating_date": "<date of most recent rating or null>"
    }},
    "financial_strength": "<very_strong|strong|adequate|weak|unknown>",
    "financial_summary": "<1-2 sentence summary of financial health>",
    "specialty_areas": [
        {{
            "line_of_business": "<line of business>",
            "expertise_level": "<limited|moderate|strong|specialty>",
            "notes": "<any notes>"
        }}
    ],
    "primary_lines": [
        "<primary line 1>",
        "<primary line 2>"
    ],
    "market_position": "<description of market position>",
    "geographic_focus": [
        "<region or state 1>",
        "<region or state 2>"
    ],
    "target_segments": [
        "<target segment 1>",
        "<target segment 2>"
    ],
    "commercial_property_appetite": "<expanding|stable|contracting|selective|exiting|unknown>",
    "appetite_notes": "<notes about appetite for commercial property>",
    "recent_news": [
        {{
            "date": "<date or null>",
            "headline": "<news headline>",
            "summary": "<brief summary>",
            "sentiment": "<positive|negative|neutral>",
            "source": "<source>"
        }}
    ],
    "news_summary": "<overall summary of recent news>",
    "customer_satisfaction": "<excellent|good|average|poor|unknown>",
    "claims_reputation": "<description of claims handling reputation>",
    "concerns": [
        "<concern 1>",
        "<concern 2>"
    ],
    "regulatory_issues": [
        "<regulatory issue 1>"
    ],
    "sources": [
        "<source 1>",
        "<source 2>"
    ]
}}

Return ONLY valid JSON. If information is not available, use null, empty arrays, or "unknown".
Be specific and cite actual ratings and data from the research."""


class CarrierResearchService:
    """Service for researching carrier information."""

    def __init__(
        self,
        session: AsyncSession,
        parallel_client: ParallelClient | None = None,
        openrouter_api_key: str | None = None,
    ):
        """Initialize carrier research service.

        Args:
            session: Database session.
            parallel_client: Parallel AI client.
            openrouter_api_key: OpenRouter API key for Gemini.
        """
        self.session = session
        self.parallel_client = parallel_client or get_parallel_client()
        self.openrouter_api_key = openrouter_api_key or settings.openrouter_api_key

    async def research_carrier(
        self,
        carrier_name: str,
        property_type: str | None = None,
        include_raw_research: bool = False,
    ) -> CarrierResearchResult:
        """Research a carrier's financial strength and market position.

        Args:
            carrier_name: Name of the carrier.
            property_type: Optional property type for context.
            include_raw_research: Include raw research text in result.

        Returns:
            CarrierResearchResult with carrier data.

        Raises:
            CarrierResearchError: If research fails.
        """
        if not self.parallel_client.api_key:
            raise CarrierResearchError("Parallel API key not configured")
        if not self.openrouter_api_key:
            raise CarrierResearchError("OpenRouter API key not configured")

        start_time = time.time()

        # Step 1: Research with Parallel AI
        try:
            parallel_result = await self.parallel_client.research_carrier(
                carrier_name=carrier_name,
                property_type=property_type,
            )
        except ParallelClientError as e:
            raise CarrierResearchError(f"Parallel AI research failed: {e}")

        parallel_latency = parallel_result.latency_ms

        # Step 2: Structure with Gemini
        gemini_start = time.time()
        structured_data = await self._structure_research(
            research_text=parallel_result.output,
            carrier_name=carrier_name,
            property_type=property_type,
        )
        gemini_latency = int((time.time() - gemini_start) * 1000)

        total_latency = int((time.time() - start_time) * 1000)

        # Build result
        result = CarrierResearchResult(
            carrier_name=carrier_name,
            research_date=datetime.now(timezone.utc),
            ratings=CarrierRatings(
                am_best_rating=structured_data.get("ratings", {}).get("am_best_rating"),
                am_best_outlook=structured_data.get("ratings", {}).get("am_best_outlook"),
                sp_rating=structured_data.get("ratings", {}).get("sp_rating"),
                moodys_rating=structured_data.get("ratings", {}).get("moodys_rating"),
                rating_date=structured_data.get("ratings", {}).get("rating_date"),
            ),
            financial_strength=structured_data.get("financial_strength", "unknown"),
            financial_summary=structured_data.get("financial_summary"),
            specialty_areas=[
                CarrierSpecialty(
                    line_of_business=s.get("line_of_business", "Unknown"),
                    expertise_level=s.get("expertise_level", "moderate"),
                    notes=s.get("notes"),
                )
                for s in structured_data.get("specialty_areas", [])
            ],
            primary_lines=structured_data.get("primary_lines", []),
            market_position=structured_data.get("market_position"),
            geographic_focus=structured_data.get("geographic_focus", []),
            target_segments=structured_data.get("target_segments", []),
            commercial_property_appetite=structured_data.get("commercial_property_appetite", "unknown"),
            appetite_notes=structured_data.get("appetite_notes"),
            recent_news=[
                CarrierNews(
                    date=n.get("date"),
                    headline=n.get("headline", ""),
                    summary=n.get("summary"),
                    sentiment=n.get("sentiment", "neutral"),
                    source=n.get("source"),
                )
                for n in structured_data.get("recent_news", [])
            ],
            news_summary=structured_data.get("news_summary"),
            customer_satisfaction=structured_data.get("customer_satisfaction"),
            claims_reputation=structured_data.get("claims_reputation"),
            concerns=structured_data.get("concerns", []),
            regulatory_issues=structured_data.get("regulatory_issues", []),
            sources=structured_data.get("sources", []),
            parallel_latency_ms=parallel_latency,
            gemini_latency_ms=gemini_latency,
            total_latency_ms=total_latency,
            raw_research=parallel_result.output if include_raw_research else None,
        )

        logger.info(
            f"Carrier research for {carrier_name}: "
            f"AM Best={result.ratings.am_best_rating}, "
            f"appetite={result.commercial_property_appetite}, "
            f"latency {total_latency}ms"
        )

        return result

    async def get_carrier_summary(
        self,
        carrier_name: str,
    ) -> dict[str, Any]:
        """Get a brief carrier summary suitable for embedding in other responses.

        Args:
            carrier_name: Name of the carrier.

        Returns:
            Dict with carrier summary.
        """
        try:
            result = await self.research_carrier(carrier_name)

            return {
                "carrier_name": result.carrier_name,
                "am_best_rating": result.ratings.am_best_rating,
                "am_best_outlook": result.ratings.am_best_outlook,
                "financial_strength": result.financial_strength,
                "commercial_property_appetite": result.commercial_property_appetite,
                "primary_lines": result.primary_lines[:3],
                "concerns": result.concerns[:2] if result.concerns else [],
                "research_date": result.research_date.isoformat(),
            }
        except CarrierResearchError as e:
            logger.warning(f"Carrier research unavailable: {e}")
            return {
                "carrier_name": carrier_name,
                "error": str(e),
                "available": False,
            }

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _structure_research(
        self,
        research_text: str,
        carrier_name: str,
        property_type: str | None,
    ) -> dict[str, Any]:
        """Structure raw research using Gemini."""
        prompt = STRUCTURE_CARRIER_RESEARCH_PROMPT.format(
            research_text=research_text,
            carrier_name=carrier_name,
            property_type=property_type or "Not specified",
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Carrier Research",
                },
                json={
                    "model": GEMINI_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.1,
                },
            )

            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code}")
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
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

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
            "ratings": {},
            "financial_strength": "unknown",
            "financial_summary": None,
            "specialty_areas": [],
            "primary_lines": [],
            "market_position": None,
            "geographic_focus": [],
            "target_segments": [],
            "commercial_property_appetite": "unknown",
            "appetite_notes": None,
            "recent_news": [],
            "news_summary": None,
            "customer_satisfaction": "unknown",
            "claims_reputation": None,
            "concerns": [],
            "regulatory_issues": [],
            "sources": [],
        }


def get_carrier_research_service(session: AsyncSession) -> CarrierResearchService:
    """Factory function to create CarrierResearchService.

    Args:
        session: Database session.

    Returns:
        CarrierResearchService instance.
    """
    return CarrierResearchService(session)
