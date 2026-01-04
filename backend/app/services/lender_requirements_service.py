"""Lender Requirements Lookup Service.

Research lender-specific insurance requirements using Parallel AI:
- Coverage minimums
- Deductible maximums
- Required endorsements
- Carrier rating requirements
- Flood/wind requirements
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


class LenderRequirementsError(Exception):
    """Base exception for lender requirements errors."""
    pass


@dataclass
class CoverageRequirement:
    """Coverage requirement specification."""
    coverage_type: str
    minimum_limit: Decimal | None = None
    limit_description: str | None = None  # e.g., "100% of replacement cost"
    required: bool = True
    notes: str | None = None


@dataclass
class DeductibleRequirement:
    """Deductible requirement specification."""
    coverage_type: str
    maximum_amount: Decimal | None = None
    maximum_percentage: float | None = None  # As percentage of TIV
    description: str | None = None


@dataclass
class EndorsementRequirement:
    """Required endorsement specification."""
    endorsement_name: str
    description: str | None = None
    required: bool = True


@dataclass
class LenderRequirementsResult:
    """Complete lender requirements result."""

    lender_name: str
    loan_type: str | None
    research_date: datetime

    # Coverage requirements
    property_coverage: CoverageRequirement | None
    liability_coverage: CoverageRequirement | None
    umbrella_coverage: CoverageRequirement | None
    flood_coverage: CoverageRequirement | None
    wind_coverage: CoverageRequirement | None
    other_coverages: list[CoverageRequirement]

    # Deductible requirements
    deductible_requirements: list[DeductibleRequirement]
    max_property_deductible_pct: float | None  # As % of TIV
    max_property_deductible_flat: Decimal | None

    # Endorsements
    required_endorsements: list[EndorsementRequirement]
    mortgagee_clause_required: bool
    notice_of_cancellation_days: int | None
    waiver_of_subrogation_required: bool

    # Carrier requirements
    minimum_carrier_rating: str | None  # A.M. Best minimum
    acceptable_rating_agencies: list[str]

    # Special requirements
    special_requirements: list[str]
    coastal_requirements: str | None
    earthquake_requirements: str | None

    # Source information
    source_document: str | None  # e.g., "Fannie Mae Multifamily Guide"
    source_section: str | None
    sources: list[str]

    # Metadata
    parallel_latency_ms: int
    gemini_latency_ms: int
    total_latency_ms: int
    raw_research: str | None = None


# Gemini prompt for structuring lender requirements research
STRUCTURE_LENDER_REQUIREMENTS_PROMPT = """You are an expert at extracting structured lender insurance requirements from research.

Analyze the following lender requirements research and extract structured information.

LENDER REQUIREMENTS RESEARCH:
{research_text}

LENDER NAME:
{lender_name}

LOAN TYPE (if specified):
{loan_type}

Extract the following information and return as JSON:

{{
    "property_coverage": {{
        "coverage_type": "property",
        "minimum_limit": <number in dollars or null>,
        "limit_description": "<e.g., '100% of replacement cost'>",
        "required": true,
        "notes": "<any notes>"
    }},
    "liability_coverage": {{
        "coverage_type": "general_liability",
        "minimum_limit": <number in dollars or null>,
        "limit_description": "<e.g., '$1M per occurrence, $2M aggregate'>",
        "required": true,
        "notes": "<any notes>"
    }},
    "umbrella_coverage": {{
        "coverage_type": "umbrella",
        "minimum_limit": <number in dollars or null>,
        "limit_description": "<description>",
        "required": <true|false>,
        "notes": "<any notes>"
    }},
    "flood_coverage": {{
        "coverage_type": "flood",
        "minimum_limit": <number in dollars or null>,
        "limit_description": "<e.g., 'Maximum available under NFIP or 80% of building value'>",
        "required": <true|false>,
        "notes": "<when required, e.g., 'Required in SFHA zones'>"
    }},
    "wind_coverage": {{
        "coverage_type": "wind",
        "minimum_limit": <number in dollars or null>,
        "limit_description": "<description>",
        "required": <true|false>,
        "notes": "<e.g., 'Required for coastal properties'>"
    }},
    "other_coverages": [
        {{
            "coverage_type": "<coverage type>",
            "minimum_limit": <number or null>,
            "limit_description": "<description>",
            "required": <true|false>,
            "notes": "<notes>"
        }}
    ],
    "deductible_requirements": [
        {{
            "coverage_type": "<coverage type>",
            "maximum_amount": <number in dollars or null>,
            "maximum_percentage": <percentage as decimal or null>,
            "description": "<description>"
        }}
    ],
    "max_property_deductible_pct": <max property deductible as % of TIV, e.g., 5 for 5%>,
    "max_property_deductible_flat": <max flat dollar deductible or null>,
    "required_endorsements": [
        {{
            "endorsement_name": "<endorsement name>",
            "description": "<description>",
            "required": true
        }}
    ],
    "mortgagee_clause_required": true,
    "notice_of_cancellation_days": <number of days notice required, e.g., 30>,
    "waiver_of_subrogation_required": <true|false>,
    "minimum_carrier_rating": "<minimum A.M. Best rating, e.g., 'A-' or 'B+'>",
    "acceptable_rating_agencies": [
        "A.M. Best",
        "S&P"
    ],
    "special_requirements": [
        "<special requirement 1>",
        "<special requirement 2>"
    ],
    "coastal_requirements": "<requirements for coastal properties or null>",
    "earthquake_requirements": "<requirements for earthquake zones or null>",
    "source_document": "<name of source document, e.g., 'Fannie Mae Multifamily Guide'>",
    "source_section": "<section reference if available>",
    "sources": [
        "<source 1>",
        "<source 2>"
    ]
}}

Return ONLY valid JSON. If information is not available, use null, empty arrays, or appropriate defaults.
Be specific about dollar amounts and percentages where the research provides them."""


class LenderRequirementsService:
    """Service for researching lender insurance requirements."""

    def __init__(
        self,
        session: AsyncSession,
        parallel_client: ParallelClient | None = None,
        openrouter_api_key: str | None = None,
    ):
        """Initialize lender requirements service.

        Args:
            session: Database session.
            parallel_client: Parallel AI client.
            openrouter_api_key: OpenRouter API key for Gemini.
        """
        self.session = session
        self.parallel_client = parallel_client or get_parallel_client()
        self.openrouter_api_key = openrouter_api_key or settings.openrouter_api_key

    async def lookup_requirements(
        self,
        lender_name: str,
        loan_type: str | None = None,
        include_raw_research: bool = False,
    ) -> LenderRequirementsResult:
        """Lookup lender-specific insurance requirements.

        Args:
            lender_name: Name of the lender.
            loan_type: Optional loan type for context.
            include_raw_research: Include raw research text in result.

        Returns:
            LenderRequirementsResult with requirements data.

        Raises:
            LenderRequirementsError: If lookup fails.
        """
        if not self.parallel_client.api_key:
            raise LenderRequirementsError("Parallel API key not configured")
        if not self.openrouter_api_key:
            raise LenderRequirementsError("OpenRouter API key not configured")

        start_time = time.time()

        # Step 1: Research with Parallel AI
        try:
            parallel_result = await self.parallel_client.research_lender_requirements(
                lender_name=lender_name,
                loan_type=loan_type,
            )
        except ParallelClientError as e:
            raise LenderRequirementsError(f"Parallel AI research failed: {e}")

        parallel_latency = parallel_result.latency_ms

        # Step 2: Structure with Gemini
        gemini_start = time.time()
        structured_data = await self._structure_research(
            research_text=parallel_result.output,
            lender_name=lender_name,
            loan_type=loan_type,
        )
        gemini_latency = int((time.time() - gemini_start) * 1000)

        total_latency = int((time.time() - start_time) * 1000)

        # Build result
        result = LenderRequirementsResult(
            lender_name=lender_name,
            loan_type=loan_type,
            research_date=datetime.now(timezone.utc),
            property_coverage=self._build_coverage_req(structured_data.get("property_coverage")),
            liability_coverage=self._build_coverage_req(structured_data.get("liability_coverage")),
            umbrella_coverage=self._build_coverage_req(structured_data.get("umbrella_coverage")),
            flood_coverage=self._build_coverage_req(structured_data.get("flood_coverage")),
            wind_coverage=self._build_coverage_req(structured_data.get("wind_coverage")),
            other_coverages=[
                self._build_coverage_req(c)
                for c in structured_data.get("other_coverages", [])
                if c
            ],
            deductible_requirements=[
                DeductibleRequirement(
                    coverage_type=d.get("coverage_type", "property"),
                    maximum_amount=Decimal(str(d["maximum_amount"])) if d.get("maximum_amount") else None,
                    maximum_percentage=d.get("maximum_percentage"),
                    description=d.get("description"),
                )
                for d in structured_data.get("deductible_requirements", [])
            ],
            max_property_deductible_pct=structured_data.get("max_property_deductible_pct"),
            max_property_deductible_flat=(
                Decimal(str(structured_data["max_property_deductible_flat"]))
                if structured_data.get("max_property_deductible_flat")
                else None
            ),
            required_endorsements=[
                EndorsementRequirement(
                    endorsement_name=e.get("endorsement_name", ""),
                    description=e.get("description"),
                    required=e.get("required", True),
                )
                for e in structured_data.get("required_endorsements", [])
            ],
            mortgagee_clause_required=structured_data.get("mortgagee_clause_required", True),
            notice_of_cancellation_days=structured_data.get("notice_of_cancellation_days"),
            waiver_of_subrogation_required=structured_data.get("waiver_of_subrogation_required", False),
            minimum_carrier_rating=structured_data.get("minimum_carrier_rating"),
            acceptable_rating_agencies=structured_data.get("acceptable_rating_agencies", ["A.M. Best"]),
            special_requirements=structured_data.get("special_requirements", []),
            coastal_requirements=structured_data.get("coastal_requirements"),
            earthquake_requirements=structured_data.get("earthquake_requirements"),
            source_document=structured_data.get("source_document"),
            source_section=structured_data.get("source_section"),
            sources=structured_data.get("sources", []),
            parallel_latency_ms=parallel_latency,
            gemini_latency_ms=gemini_latency,
            total_latency_ms=total_latency,
            raw_research=parallel_result.output if include_raw_research else None,
        )

        logger.info(
            f"Lender requirements for {lender_name}: "
            f"min rating={result.minimum_carrier_rating}, "
            f"max ded={result.max_property_deductible_pct}%, "
            f"latency {total_latency}ms"
        )

        return result

    async def get_requirements_for_compliance(
        self,
        lender_name: str,
        loan_type: str | None = None,
    ) -> dict[str, Any]:
        """Get lender requirements in format suitable for compliance checking.

        Args:
            lender_name: Name of the lender.
            loan_type: Optional loan type.

        Returns:
            Dict with requirements for compliance service.
        """
        try:
            result = await self.lookup_requirements(lender_name, loan_type)

            requirements = {
                "lender_name": result.lender_name,
                "loan_type": result.loan_type,
                "coverage_requirements": {},
                "deductible_requirements": {},
                "carrier_requirements": {},
                "endorsement_requirements": [],
                "research_date": result.research_date.isoformat(),
            }

            # Property coverage
            if result.property_coverage:
                requirements["coverage_requirements"]["property"] = {
                    "minimum_limit": float(result.property_coverage.minimum_limit) if result.property_coverage.minimum_limit else None,
                    "description": result.property_coverage.limit_description,
                    "required": result.property_coverage.required,
                }

            # Liability coverage
            if result.liability_coverage:
                requirements["coverage_requirements"]["general_liability"] = {
                    "minimum_limit": float(result.liability_coverage.minimum_limit) if result.liability_coverage.minimum_limit else None,
                    "description": result.liability_coverage.limit_description,
                    "required": result.liability_coverage.required,
                }

            # Umbrella coverage
            if result.umbrella_coverage:
                requirements["coverage_requirements"]["umbrella"] = {
                    "minimum_limit": float(result.umbrella_coverage.minimum_limit) if result.umbrella_coverage.minimum_limit else None,
                    "description": result.umbrella_coverage.limit_description,
                    "required": result.umbrella_coverage.required,
                }

            # Flood coverage
            if result.flood_coverage:
                requirements["coverage_requirements"]["flood"] = {
                    "minimum_limit": float(result.flood_coverage.minimum_limit) if result.flood_coverage.minimum_limit else None,
                    "description": result.flood_coverage.limit_description,
                    "required": result.flood_coverage.required,
                    "notes": result.flood_coverage.notes,
                }

            # Deductible requirements
            requirements["deductible_requirements"] = {
                "max_percentage_of_tiv": result.max_property_deductible_pct,
                "max_flat_amount": float(result.max_property_deductible_flat) if result.max_property_deductible_flat else None,
            }

            # Carrier requirements
            requirements["carrier_requirements"] = {
                "minimum_am_best_rating": result.minimum_carrier_rating,
                "acceptable_agencies": result.acceptable_rating_agencies,
            }

            # Endorsements
            requirements["endorsement_requirements"] = [
                {
                    "name": e.endorsement_name,
                    "required": e.required,
                }
                for e in result.required_endorsements
            ]

            requirements["notice_of_cancellation_days"] = result.notice_of_cancellation_days

            return requirements

        except LenderRequirementsError as e:
            logger.warning(f"Lender requirements unavailable: {e}")
            return {
                "lender_name": lender_name,
                "error": str(e),
                "available": False,
            }

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    def _build_coverage_req(self, data: dict | None) -> CoverageRequirement | None:
        """Build CoverageRequirement from dict."""
        if not data:
            return None

        return CoverageRequirement(
            coverage_type=data.get("coverage_type", "unknown"),
            minimum_limit=Decimal(str(data["minimum_limit"])) if data.get("minimum_limit") else None,
            limit_description=data.get("limit_description"),
            required=data.get("required", True),
            notes=data.get("notes"),
        )

    async def _structure_research(
        self,
        research_text: str,
        lender_name: str,
        loan_type: str | None,
    ) -> dict[str, Any]:
        """Structure raw research using Gemini."""
        prompt = STRUCTURE_LENDER_REQUIREMENTS_PROMPT.format(
            research_text=research_text,
            lender_name=lender_name,
            loan_type=loan_type or "Not specified",
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Lender Requirements",
                },
                json={
                    "model": GEMINI_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2500,
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
            "property_coverage": None,
            "liability_coverage": None,
            "umbrella_coverage": None,
            "flood_coverage": None,
            "wind_coverage": None,
            "other_coverages": [],
            "deductible_requirements": [],
            "max_property_deductible_pct": None,
            "max_property_deductible_flat": None,
            "required_endorsements": [],
            "mortgagee_clause_required": True,
            "notice_of_cancellation_days": 30,
            "waiver_of_subrogation_required": False,
            "minimum_carrier_rating": None,
            "acceptable_rating_agencies": ["A.M. Best"],
            "special_requirements": [],
            "coastal_requirements": None,
            "earthquake_requirements": None,
            "source_document": None,
            "source_section": None,
            "sources": [],
        }


def get_lender_requirements_service(session: AsyncSession) -> LenderRequirementsService:
    """Factory function to create LenderRequirementsService.

    Args:
        session: Database session.

    Returns:
        LenderRequirementsService instance.
    """
    return LenderRequirementsService(session)
