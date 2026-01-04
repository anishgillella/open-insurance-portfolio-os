"""Property Risk Enrichment Service.

Enriches property data with external risk information using Parallel AI:
- FEMA flood zone data
- Fire protection class
- Weather/CAT exposure
- Crime statistics
- Environmental hazards
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.property import Property
from app.services.parallel_client import (
    ParallelClient,
    ParallelClientError,
    get_parallel_client,
)

logger = logging.getLogger(__name__)

# OpenRouter API for Gemini structuring
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL = "google/gemini-2.5-flash"


class PropertyRiskError(Exception):
    """Base exception for property risk service errors."""
    pass


@dataclass
class FloodRisk:
    """Flood risk assessment."""
    zone: str | None = None  # X, A, AE, V, VE, etc.
    zone_description: str | None = None
    risk_level: str = "unknown"  # low, moderate, high, very_high
    source: str | None = None


@dataclass
class FireProtection:
    """Fire protection assessment."""
    protection_class: str | None = None  # 1-10, 10 being worst
    fire_station_distance_miles: float | None = None
    hydrant_distance_feet: float | None = None
    source: str | None = None


@dataclass
class WeatherRisk:
    """Weather/CAT risk assessment."""
    hurricane_risk: str = "unknown"  # low, moderate, high, very_high
    tornado_risk: str = "unknown"
    hail_risk: str = "unknown"
    wildfire_risk: str = "unknown"
    earthquake_risk: str = "unknown"
    historical_events: list[str] = field(default_factory=list)


@dataclass
class CrimeRisk:
    """Crime risk assessment."""
    crime_index: int | None = None  # 0-100, 100 being worst
    crime_grade: str | None = None  # A, B, C, D, F
    risk_level: str = "unknown"
    notes: str | None = None


@dataclass
class EnvironmentalRisk:
    """Environmental hazard assessment."""
    hazards: list[str] = field(default_factory=list)
    superfund_nearby: bool = False
    industrial_nearby: bool = False
    risk_level: str = "unknown"


@dataclass
class PropertyRiskResult:
    """Complete property risk enrichment result."""

    property_id: str
    address: str
    enrichment_date: datetime

    # Risk assessments
    flood_risk: FloodRisk
    fire_protection: FireProtection
    weather_risk: WeatherRisk
    crime_risk: CrimeRisk
    environmental_risk: EnvironmentalRisk

    # Building/permit info
    recent_permits: list[str]
    violations: list[str]
    infrastructure_issues: list[str]

    # Overall assessment
    overall_risk_score: int | None  # 0-100
    risk_summary: str | None
    insurance_implications: list[str]

    # Sources
    sources: list[str]

    # Metadata
    parallel_latency_ms: int
    gemini_latency_ms: int
    total_latency_ms: int
    raw_research: str | None = None


# Gemini prompt for structuring property risk research
STRUCTURE_PROPERTY_RISK_PROMPT = """You are an expert at extracting structured property risk data from research.

Analyze the following property risk research and extract structured information.

PROPERTY RISK RESEARCH:
{research_text}

PROPERTY ADDRESS:
{address}

Extract the following information and return as JSON:

{{
    "flood_risk": {{
        "zone": "<FEMA flood zone like X, A, AE, V, VE or null>",
        "zone_description": "<description of what this zone means>",
        "risk_level": "<low|moderate|high|very_high|unknown>",
        "source": "<source of flood data>"
    }},
    "fire_protection": {{
        "protection_class": "<ISO PPC rating 1-10 or null>",
        "fire_station_distance_miles": <number or null>,
        "hydrant_distance_feet": <number or null>,
        "source": "<source of fire protection data>"
    }},
    "weather_risk": {{
        "hurricane_risk": "<low|moderate|high|very_high|unknown>",
        "tornado_risk": "<low|moderate|high|very_high|unknown>",
        "hail_risk": "<low|moderate|high|very_high|unknown>",
        "wildfire_risk": "<low|moderate|high|very_high|unknown>",
        "earthquake_risk": "<low|moderate|high|very_high|unknown>",
        "historical_events": [
            "<notable weather event 1>",
            "<notable weather event 2>"
        ]
    }},
    "crime_risk": {{
        "crime_index": <0-100 number or null>,
        "crime_grade": "<A|B|C|D|F or null>",
        "risk_level": "<low|moderate|high|very_high|unknown>",
        "notes": "<any notes about crime statistics>"
    }},
    "environmental_risk": {{
        "hazards": [
            "<environmental hazard 1>",
            "<environmental hazard 2>"
        ],
        "superfund_nearby": <true|false>,
        "industrial_nearby": <true|false>,
        "risk_level": "<low|moderate|high|very_high|unknown>"
    }},
    "recent_permits": [
        "<recent permit 1>",
        "<recent permit 2>"
    ],
    "violations": [
        "<violation 1>",
        "<violation 2>"
    ],
    "infrastructure_issues": [
        "<infrastructure issue 1>"
    ],
    "overall_risk_score": <0-100 number representing overall risk, 100 being highest risk>,
    "risk_summary": "<2-3 sentence summary of key risk factors>",
    "insurance_implications": [
        "<implication 1 for insurance coverage>",
        "<implication 2 for insurance coverage>"
    ],
    "sources": [
        "<source 1>",
        "<source 2>"
    ]
}}

Return ONLY valid JSON. If information is not available, use null, empty arrays, or "unknown".
Be specific and cite actual data points from the research."""


class PropertyRiskService:
    """Service for enriching property risk data."""

    def __init__(
        self,
        session: AsyncSession,
        parallel_client: ParallelClient | None = None,
        openrouter_api_key: str | None = None,
    ):
        """Initialize property risk service.

        Args:
            session: Database session.
            parallel_client: Parallel AI client.
            openrouter_api_key: OpenRouter API key for Gemini.
        """
        self.session = session
        self.parallel_client = parallel_client or get_parallel_client()
        self.openrouter_api_key = openrouter_api_key or settings.openrouter_api_key

    async def enrich_property_risk(
        self,
        property_id: str,
        include_raw_research: bool = False,
    ) -> PropertyRiskResult:
        """Enrich property with external risk data.

        Args:
            property_id: Property ID.
            include_raw_research: Include raw research text in result.

        Returns:
            PropertyRiskResult with risk enrichment data.

        Raises:
            PropertyRiskError: If enrichment fails.
        """
        if not self.parallel_client.api_key:
            raise PropertyRiskError("Parallel API key not configured")
        if not self.openrouter_api_key:
            raise PropertyRiskError("OpenRouter API key not configured")

        # Load property
        prop = await self._load_property(property_id)
        if not prop:
            raise PropertyRiskError(f"Property {property_id} not found")

        # Build address
        address = self._build_address(prop)
        if not address:
            raise PropertyRiskError(f"Property {property_id} has no address")

        start_time = time.time()

        # Step 1: Research with Parallel AI
        try:
            parallel_result = await self.parallel_client.research_property_risk(
                address=prop.address or "",
                city=prop.city or "",
                state=prop.state or "",
                zip_code=prop.zip or "",
            )
        except ParallelClientError as e:
            raise PropertyRiskError(f"Parallel AI research failed: {e}")

        parallel_latency = parallel_result.latency_ms

        # Step 2: Structure with Gemini
        gemini_start = time.time()
        structured_data = await self._structure_research(
            research_text=parallel_result.output,
            address=address,
        )
        gemini_latency = int((time.time() - gemini_start) * 1000)

        total_latency = int((time.time() - start_time) * 1000)

        # Build result
        result = PropertyRiskResult(
            property_id=property_id,
            address=address,
            enrichment_date=datetime.now(timezone.utc),
            flood_risk=FloodRisk(
                zone=structured_data.get("flood_risk", {}).get("zone"),
                zone_description=structured_data.get("flood_risk", {}).get("zone_description"),
                risk_level=structured_data.get("flood_risk", {}).get("risk_level", "unknown"),
                source=structured_data.get("flood_risk", {}).get("source"),
            ),
            fire_protection=FireProtection(
                protection_class=structured_data.get("fire_protection", {}).get("protection_class"),
                fire_station_distance_miles=structured_data.get("fire_protection", {}).get("fire_station_distance_miles"),
                hydrant_distance_feet=structured_data.get("fire_protection", {}).get("hydrant_distance_feet"),
                source=structured_data.get("fire_protection", {}).get("source"),
            ),
            weather_risk=WeatherRisk(
                hurricane_risk=structured_data.get("weather_risk", {}).get("hurricane_risk", "unknown"),
                tornado_risk=structured_data.get("weather_risk", {}).get("tornado_risk", "unknown"),
                hail_risk=structured_data.get("weather_risk", {}).get("hail_risk", "unknown"),
                wildfire_risk=structured_data.get("weather_risk", {}).get("wildfire_risk", "unknown"),
                earthquake_risk=structured_data.get("weather_risk", {}).get("earthquake_risk", "unknown"),
                historical_events=structured_data.get("weather_risk", {}).get("historical_events", []),
            ),
            crime_risk=CrimeRisk(
                crime_index=structured_data.get("crime_risk", {}).get("crime_index"),
                crime_grade=structured_data.get("crime_risk", {}).get("crime_grade"),
                risk_level=structured_data.get("crime_risk", {}).get("risk_level", "unknown"),
                notes=structured_data.get("crime_risk", {}).get("notes"),
            ),
            environmental_risk=EnvironmentalRisk(
                hazards=structured_data.get("environmental_risk", {}).get("hazards", []),
                superfund_nearby=structured_data.get("environmental_risk", {}).get("superfund_nearby", False),
                industrial_nearby=structured_data.get("environmental_risk", {}).get("industrial_nearby", False),
                risk_level=structured_data.get("environmental_risk", {}).get("risk_level", "unknown"),
            ),
            recent_permits=structured_data.get("recent_permits", []),
            violations=structured_data.get("violations", []),
            infrastructure_issues=structured_data.get("infrastructure_issues", []),
            overall_risk_score=structured_data.get("overall_risk_score"),
            risk_summary=structured_data.get("risk_summary"),
            insurance_implications=structured_data.get("insurance_implications", []),
            sources=structured_data.get("sources", []),
            parallel_latency_ms=parallel_latency,
            gemini_latency_ms=gemini_latency,
            total_latency_ms=total_latency,
            raw_research=parallel_result.output if include_raw_research else None,
        )

        logger.info(
            f"Property risk enrichment for {property_id}: "
            f"flood={result.flood_risk.zone}, "
            f"fire_class={result.fire_protection.protection_class}, "
            f"latency {total_latency}ms"
        )

        return result

    async def update_property_with_risk_data(
        self,
        property_id: str,
    ) -> Property:
        """Enrich and update property record with risk data.

        Args:
            property_id: Property ID.

        Returns:
            Updated Property object.
        """
        result = await self.enrich_property_risk(property_id)

        # Load property for update
        prop = await self._load_property(property_id)
        if not prop:
            raise PropertyRiskError(f"Property {property_id} not found")

        # Update property fields
        if result.flood_risk.zone:
            prop.flood_zone = result.flood_risk.zone

        if result.fire_protection.protection_class:
            prop.protection_class = result.fire_protection.protection_class

        # Store additional risk data in a JSON field if available
        # (This depends on the Property model having a risk_data JSON field)

        await self.session.flush()

        logger.info(f"Updated property {property_id} with risk data")
        return prop

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _load_property(self, property_id: str) -> Property | None:
        """Load property."""
        stmt = (
            select(Property)
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _build_address(self, prop: Property) -> str | None:
        """Build full address string."""
        parts = []
        if prop.address:
            parts.append(prop.address)
        if prop.city:
            parts.append(prop.city)
        if prop.state:
            parts.append(prop.state)
        if prop.zip:
            parts.append(prop.zip)

        return ", ".join(parts) if parts else None

    async def _structure_research(
        self,
        research_text: str,
        address: str,
    ) -> dict[str, Any]:
        """Structure raw research using Gemini."""
        prompt = STRUCTURE_PROPERTY_RISK_PROMPT.format(
            research_text=research_text,
            address=address,
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Property Risk",
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
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Try to find JSON object
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
            "flood_risk": {"risk_level": "unknown"},
            "fire_protection": {},
            "weather_risk": {},
            "crime_risk": {"risk_level": "unknown"},
            "environmental_risk": {"risk_level": "unknown"},
            "recent_permits": [],
            "violations": [],
            "infrastructure_issues": [],
            "overall_risk_score": None,
            "risk_summary": None,
            "insurance_implications": [],
            "sources": [],
        }


def get_property_risk_service(session: AsyncSession) -> PropertyRiskService:
    """Factory function to create PropertyRiskService.

    Args:
        session: Database session.

    Returns:
        PropertyRiskService instance.
    """
    return PropertyRiskService(session)
