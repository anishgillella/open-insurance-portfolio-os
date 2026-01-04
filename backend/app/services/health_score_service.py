"""Insurance Health Score Service with LLM-Powered Analysis.

Calculates the proprietary 0-100 Insurance Health Score with 6 components,
all determined by LLM analysis for maximum explainability and nuance.

Components:
1. Coverage Adequacy (25 points) - Building coverage vs replacement cost
2. Policy Currency (20 points) - Expiration status and renewal readiness
3. Deductible Risk (15 points) - Deductible amounts relative to TIV
4. Coverage Breadth (15 points) - Required and recommended coverages
5. Lender Compliance (15 points) - Lender requirements satisfaction
6. Documentation Quality (10 points) - Document completeness
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
from app.models.building import Building
from app.models.coverage_gap import CoverageGap
from app.models.health_score import HealthScore
from app.models.insurance_program import InsuranceProgram
from app.models.lender_requirement import LenderRequirement
from app.models.policy import Policy
from app.models.property import Property
from app.repositories.health_score_repository import HealthScoreRepository
from app.services.completeness_service import CompletenessService
from app.services.property_risk_service import (
    PropertyRiskService,
    PropertyRiskError,
    PropertyRiskResult,
    get_property_risk_service,
)

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


class HealthScoreError(Exception):
    """Base exception for health score service errors."""
    pass


@dataclass
class ComponentScore:
    """Score for a single health score component."""
    score: float
    max_points: float
    percentage: float
    reasoning: str
    key_findings: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)


@dataclass
class HealthScoreResult:
    """Result of health score calculation."""
    property_id: str
    property_name: str
    score: int
    grade: str
    components: dict[str, ComponentScore]
    executive_summary: str
    recommendations: list[dict]
    risk_factors: list[str]
    strengths: list[str]
    trend_direction: str
    trend_delta: int | None
    calculated_at: datetime
    model_used: str
    latency_ms: int

    # External risk data (from Parallel AI)
    external_risk_data: dict | None = None
    risk_enrichment_latency_ms: int | None = None


@dataclass
class PortfolioHealthScoreResult:
    """Portfolio-wide health score summary."""
    portfolio_score: int
    portfolio_grade: str
    property_count: int
    distribution: dict[str, int]
    component_averages: dict[str, float]
    trend_direction: str
    trend_delta: int | None
    properties: list[dict]
    calculated_at: datetime


# LLM Prompt for health score calculation
HEALTH_SCORE_PROMPT = """You are an expert commercial real estate insurance analyst. Evaluate this property's insurance health and provide scores for each component.

PROPERTY DATA:
{property_context}

BUILDINGS:
{buildings_context}

POLICIES & COVERAGES:
{policies_context}

LENDER REQUIREMENTS:
{lender_context}

DOCUMENTS:
{documents_context}

EXISTING GAPS:
{gaps_context}

EXTERNAL RISK DATA (from live web research):
{external_risk_context}

Evaluate each of the 6 components and provide your analysis. Each component has a maximum score:
1. COVERAGE ADEQUACY (25 points max): Is building coverage sufficient for replacement cost? Is business income adequate? Are liability limits appropriate?
2. POLICY CURRENCY (20 points max): Are all policies current? How close are policies to expiration? Any lapse risk?
3. DEDUCTIBLE RISK (15 points max): Are deductibles reasonable relative to property value? What's the out-of-pocket exposure?
4. COVERAGE BREADTH (15 points max): Are required coverages present (property, GL)? Are recommended coverages present based on property type/location (umbrella, flood, earthquake)?
5. LENDER COMPLIANCE (15 points max): Does coverage meet lender requirements? Is mortgagee properly listed?
6. DOCUMENTATION QUALITY (10 points max): Are required documents present? Are documents current?

Respond in JSON format:
{{
    "total_score": <0-100 integer>,
    "grade": "A|B|C|D|F",
    "components": {{
        "coverage_adequacy": {{
            "score": <0-25>,
            "reasoning": "Detailed explanation of score",
            "key_findings": ["finding 1", "finding 2"],
            "concerns": ["concern 1 if any"]
        }},
        "policy_currency": {{
            "score": <0-20>,
            "reasoning": "Detailed explanation of score",
            "key_findings": ["finding 1"],
            "concerns": ["concern if any"]
        }},
        "deductible_risk": {{
            "score": <0-15>,
            "reasoning": "Detailed explanation of score",
            "key_findings": ["finding 1"],
            "concerns": ["concern if any"]
        }},
        "coverage_breadth": {{
            "score": <0-15>,
            "reasoning": "Detailed explanation of score",
            "key_findings": ["finding 1"],
            "concerns": ["concern if any"]
        }},
        "lender_compliance": {{
            "score": <0-15>,
            "reasoning": "Detailed explanation of score",
            "key_findings": ["finding 1"],
            "concerns": ["concern if any"]
        }},
        "documentation_quality": {{
            "score": <0-10>,
            "reasoning": "Detailed explanation of score",
            "key_findings": ["finding 1"],
            "concerns": ["concern if any"]
        }}
    }},
    "executive_summary": "2-3 sentence overall assessment for executives",
    "recommendations": [
        {{"priority": "high|medium|low", "action": "specific action", "impact": "expected improvement", "component": "affected component"}}
    ],
    "risk_factors": ["key risk 1", "key risk 2"],
    "strengths": ["strength 1", "strength 2"]
}}

Grade thresholds: A (90-100), B (80-89), C (70-79), D (60-69), F (0-59)
Be specific and quantitative where possible. Base your analysis on industry standards for commercial real estate insurance."""


class HealthScoreService:
    """Service for calculating LLM-powered Insurance Health Scores."""

    COMPONENT_MAX_SCORES = {
        "coverage_adequacy": 25,
        "policy_currency": 20,
        "deductible_risk": 15,
        "coverage_breadth": 15,
        "lender_compliance": 15,
        "documentation_quality": 10,
    }

    def __init__(self, session: AsyncSession, api_key: str | None = None):
        """Initialize health score service.

        Args:
            session: Database session.
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.session = session
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL
        self.health_repo = HealthScoreRepository(session)
        self.completeness_service = CompletenessService(session, api_key)
        self.property_risk_service = get_property_risk_service(session)

    async def calculate_health_score(
        self,
        property_id: str,
        trigger: str = "manual",
        use_external_risk_data: bool = True,
    ) -> HealthScoreResult:
        """Calculate comprehensive health score for a property using LLM.

        Args:
            property_id: Property ID.
            trigger: What triggered the calculation (manual, ingestion, gap_resolved).
            use_external_risk_data: Fetch external risk data from Parallel AI.

        Returns:
            HealthScoreResult with full analysis.
        """
        if not self.api_key:
            raise HealthScoreError("OpenRouter API key not configured")

        # Load property with all context
        prop = await self._load_property_with_full_context(property_id)
        if not prop:
            raise HealthScoreError(f"Property {property_id} not found")

        # Fetch external risk data from Parallel AI
        external_risk_data: dict | None = None
        risk_enrichment_latency: int | None = None
        external_risk_context = "External risk data not available."

        if use_external_risk_data:
            try:
                logger.info(f"Fetching external risk data for property {property_id}")
                risk_start = time.time()
                risk_result = await self.property_risk_service.enrich_property_risk(
                    property_id=property_id,
                    include_raw_research=False,
                )
                risk_enrichment_latency = int((time.time() - risk_start) * 1000)

                external_risk_data = self._risk_result_to_dict(risk_result)
                external_risk_context = self._format_external_risk_context(risk_result)
                logger.info(
                    f"External risk data fetched for {property_id}: "
                    f"flood={risk_result.flood_risk.zone}, "
                    f"overall_score={risk_result.overall_risk_score}, "
                    f"latency {risk_enrichment_latency}ms"
                )
            except PropertyRiskError as e:
                logger.warning(f"Failed to fetch external risk data: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching external risk data: {e}")

        # Build context for LLM
        property_context = self._build_property_context(prop)
        buildings_context = self._build_buildings_context(prop)
        policies_context = self._build_policies_context(prop)
        lender_context = await self._build_lender_context(property_id)
        documents_context = await self._build_documents_context(property_id)
        gaps_context = await self._build_gaps_context(property_id)

        # Format prompt
        prompt = HEALTH_SCORE_PROMPT.format(
            property_context=property_context,
            buildings_context=buildings_context,
            policies_context=policies_context,
            lender_context=lender_context,
            documents_context=documents_context,
            gaps_context=gaps_context,
            external_risk_context=external_risk_context,
        )

        # Call LLM
        start_time = time.time()
        response = await self._call_llm(prompt)
        latency_ms = int((time.time() - start_time) * 1000)

        # Parse response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = self._extract_json_from_response(response)

        # Build component scores
        components = {}
        for comp_name, max_score in self.COMPONENT_MAX_SCORES.items():
            comp_data = result.get("components", {}).get(comp_name, {})
            score = float(comp_data.get("score", 0))
            components[comp_name] = ComponentScore(
                score=score,
                max_points=max_score,
                percentage=round(score / max_score * 100, 1) if max_score > 0 else 0,
                reasoning=comp_data.get("reasoning", ""),
                key_findings=comp_data.get("key_findings", []),
                concerns=comp_data.get("concerns", []),
            )

        total_score = int(result.get("total_score", sum(c.score for c in components.values())))
        grade = result.get("grade", self._calculate_grade(total_score))

        # Persist to database
        health_score = await self.health_repo.create_score(
            property_id=property_id,
            score=total_score,
            grade=grade,
            components={
                name: {
                    "score": comp.score,
                    "max": comp.max_points,
                    "percentage": comp.percentage,
                    "reasoning": comp.reasoning,
                    "key_findings": comp.key_findings,
                    "concerns": comp.concerns,
                }
                for name, comp in components.items()
            },
            calculated_at=datetime.now(timezone.utc),
            trigger=trigger,
            executive_summary=result.get("executive_summary"),
            recommendations=result.get("recommendations", []),
            risk_factors=result.get("risk_factors", []),
            strengths=result.get("strengths", []),
            llm_model_used=self.model,
            llm_latency_ms=latency_ms,
        )

        return HealthScoreResult(
            property_id=property_id,
            property_name=prop.name,
            score=total_score,
            grade=grade,
            components=components,
            executive_summary=result.get("executive_summary", ""),
            recommendations=result.get("recommendations", []),
            risk_factors=result.get("risk_factors", []),
            strengths=result.get("strengths", []),
            trend_direction=health_score.trend_direction or "new",
            trend_delta=health_score.trend_delta,
            calculated_at=health_score.calculated_at,
            model_used=self.model,
            latency_ms=latency_ms,
            external_risk_data=external_risk_data,
            risk_enrichment_latency_ms=risk_enrichment_latency,
        )

    async def get_latest_score(self, property_id: str) -> HealthScoreResult | None:
        """Get the latest health score for a property.

        Args:
            property_id: Property ID.

        Returns:
            HealthScoreResult or None if no score exists.
        """
        score = await self.health_repo.get_latest_for_property(property_id)
        if not score:
            return None

        # Load property name
        prop = await self._load_property_basic(property_id)
        if not prop:
            return None

        # Convert stored data to result
        components = {}
        for name, data in (score.components or {}).items():
            components[name] = ComponentScore(
                score=data.get("score", 0),
                max_points=data.get("max", self.COMPONENT_MAX_SCORES.get(name, 0)),
                percentage=data.get("percentage", 0),
                reasoning=data.get("reasoning", ""),
                key_findings=data.get("key_findings", []),
                concerns=data.get("concerns", []),
            )

        return HealthScoreResult(
            property_id=property_id,
            property_name=prop.name,
            score=score.score,
            grade=score.grade,
            components=components,
            executive_summary=score.executive_summary or "",
            recommendations=score.recommendations or [],
            risk_factors=score.risk_factors or [],
            strengths=score.strengths or [],
            trend_direction=score.trend_direction or "new",
            trend_delta=score.trend_delta,
            calculated_at=score.calculated_at,
            model_used=score.llm_model_used or self.model,
            latency_ms=score.llm_latency_ms or 0,
        )

    async def get_score_history(
        self,
        property_id: str,
        days: int = 90,
    ) -> dict[str, Any]:
        """Get health score history for trend analysis.

        Args:
            property_id: Property ID.
            days: Number of days of history.

        Returns:
            Dictionary with current score, history, and trend analysis.
        """
        scores = await self.health_repo.get_history(property_id, days)

        if not scores:
            return {
                "property_id": property_id,
                "current_score": None,
                "history": [],
                "trend_analysis": {},
            }

        current = scores[0]
        history = [
            {
                "date": s.calculated_at.isoformat(),
                "score": s.score,
                "grade": s.grade,
            }
            for s in scores
        ]

        # Calculate trend analysis
        if len(scores) >= 2:
            first_score = scores[-1].score
            last_score = scores[0].score
            change = last_score - first_score

            trend_analysis = {
                f"{days}_day_change": change,
                "direction": "improving" if change > 0 else "declining" if change < 0 else "stable",
                "first_score": first_score,
                "last_score": last_score,
            }
        else:
            trend_analysis = {
                "direction": "new",
                "note": "Not enough history for trend analysis",
            }

        return {
            "property_id": property_id,
            "current_score": current.score,
            "history": history,
            "trend_analysis": trend_analysis,
        }

    async def calculate_portfolio_score(
        self,
        organization_id: str | None = None,
    ) -> PortfolioHealthScoreResult:
        """Calculate aggregate health score for portfolio.

        Args:
            organization_id: Optional organization filter.

        Returns:
            PortfolioHealthScoreResult with aggregated data.
        """
        scores = await self.health_repo.get_portfolio_scores(organization_id)

        if not scores:
            return PortfolioHealthScoreResult(
                portfolio_score=0,
                portfolio_grade="F",
                property_count=0,
                distribution={"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
                component_averages={},
                trend_direction="new",
                trend_delta=None,
                properties=[],
                calculated_at=datetime.now(timezone.utc),
            )

        # Calculate averages
        total_score = sum(s.score for s in scores)
        avg_score = round(total_score / len(scores))

        # Grade distribution
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for s in scores:
            if s.grade in distribution:
                distribution[s.grade] += 1

        # Component averages
        component_totals: dict[str, float] = {}
        component_counts: dict[str, int] = {}
        for s in scores:
            for comp_name, comp_data in (s.components or {}).items():
                if comp_name not in component_totals:
                    component_totals[comp_name] = 0
                    component_counts[comp_name] = 0
                component_totals[comp_name] += comp_data.get("score", 0)
                component_counts[comp_name] += 1

        component_averages = {
            name: round(total / component_counts[name], 1)
            for name, total in component_totals.items()
            if component_counts.get(name, 0) > 0
        }

        # Build properties list
        properties = [
            {
                "id": s.property_id,
                "name": s.property.name if s.property else "Unknown",
                "score": s.score,
                "grade": s.grade,
                "trend": s.trend_direction,
            }
            for s in scores
        ]

        return PortfolioHealthScoreResult(
            portfolio_score=avg_score,
            portfolio_grade=self._calculate_grade(avg_score),
            property_count=len(scores),
            distribution=distribution,
            component_averages=component_averages,
            trend_direction="stable",  # Would need historical portfolio data
            trend_delta=None,
            properties=properties,
            calculated_at=datetime.now(timezone.utc),
        )

    async def _load_property_with_full_context(self, property_id: str) -> Property | None:
        """Load property with all insurance context."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.buildings),
                selectinload(Property.documents),
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                ).selectinload(Policy.coverages),
                selectinload(Property.lender_requirements),
                selectinload(Property.coverage_gaps),
            )
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_property_basic(self, property_id: str) -> Property | None:
        """Load property with basic info only."""
        stmt = (
            select(Property)
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _build_property_context(self, prop: Property) -> str:
        """Build property context string for LLM."""
        lines = [
            f"Name: {prop.name}",
            f"Type: {prop.property_type or 'N/A'}",
            f"Address: {prop.address}, {prop.city}, {prop.state} {prop.zip}",
            f"Units: {prop.units or 'N/A'}",
            f"Square Feet: {prop.sq_ft:,}" if prop.sq_ft else "Square Feet: N/A",
            f"Year Built: {prop.year_built or 'N/A'}",
            f"Construction Type: {prop.construction_type or 'N/A'}",
            f"Flood Zone: {prop.flood_zone or 'N/A'}",
            f"Earthquake Zone: {prop.earthquake_zone or 'N/A'}",
            f"Has Sprinklers: {prop.has_sprinklers or 'Unknown'}",
        ]
        return "\n".join(lines)

    def _build_buildings_context(self, prop: Property) -> str:
        """Build buildings context string for LLM."""
        if not prop.buildings:
            return "No building data available"

        lines = []
        total_value = Decimal(0)
        for i, building in enumerate(prop.buildings, 1):
            value = building.building_value or Decimal(0)
            total_value += value
            lines.append(
                f"Building {i}: {building.building_name or 'Unnamed'} - "
                f"Value: ${value:,.2f}, "
                f"Sq Ft: {building.sq_ft or 'N/A'}"
            )

        lines.append(f"\nTotal Building Value: ${total_value:,.2f}")
        return "\n".join(lines)

    def _build_policies_context(self, prop: Property) -> str:
        """Build policies context string for LLM."""
        lines = []
        for program in prop.insurance_programs:
            if program.status == "active":
                lines.append(f"Program Year: {program.program_year}")
                lines.append(f"Total Insured Value: ${program.total_insured_value:,.2f}" if program.total_insured_value else "TIV: N/A")

                for policy in program.policies:
                    exp_date = policy.expiration_date.strftime("%Y-%m-%d") if policy.expiration_date else "N/A"
                    lines.append(f"\n  Policy: {policy.policy_type}")
                    lines.append(f"    Number: {policy.policy_number or 'N/A'}")
                    lines.append(f"    Carrier: {policy.carrier_name or 'Unknown'}")
                    lines.append(f"    Expiration: {exp_date}")
                    lines.append(f"    Premium: ${policy.premium:,.2f}" if policy.premium else "    Premium: N/A")

                    if policy.coverages:
                        lines.append("    Coverages:")
                        for cov in policy.coverages[:10]:  # Limit to 10 coverages
                            limit = f"${cov.limit_amount:,.2f}" if cov.limit_amount else "N/A"
                            ded = f"${cov.deductible_amount:,.2f}" if cov.deductible_amount else "N/A"
                            lines.append(f"      - {cov.coverage_name}: Limit {limit}, Deductible {ded}")

        return "\n".join(lines) if lines else "No active insurance programs found"

    async def _build_lender_context(self, property_id: str) -> str:
        """Build lender requirements context string."""
        stmt = (
            select(LenderRequirement)
            .where(
                LenderRequirement.property_id == property_id,
                LenderRequirement.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        requirements = list(result.scalars().all())

        if not requirements:
            return "No lender requirements on file"

        lines = []
        for req in requirements:
            lines.append(f"Lender: {req.lender.name if req.lender else 'Unknown'}")
            lines.append(f"  Loan Number: {req.loan_number or 'N/A'}")
            lines.append(f"  Loan Amount: ${req.loan_amount:,.2f}" if req.loan_amount else "  Loan Amount: N/A")
            lines.append(f"  Min Property Limit: ${req.min_property_limit:,.2f}" if req.min_property_limit else "  Min Property Limit: N/A")
            lines.append(f"  Max Deductible: {req.max_deductible_pct * 100:.1f}%" if req.max_deductible_pct else "  Max Deductible: N/A")
            lines.append(f"  Requires Flood: {req.requires_flood or False}")
            lines.append(f"  Compliance Status: {req.compliance_status or 'Unknown'}")

        return "\n".join(lines)

    async def _build_documents_context(self, property_id: str) -> str:
        """Build documents context using completeness service."""
        try:
            completeness = await self.completeness_service.get_completeness(
                property_id,
                include_llm_analysis=False,
            )
            lines = [
                f"Document Completeness: {completeness.percentage}% ({completeness.grade})",
                f"Required Documents: {completeness.required_present}/{completeness.required_total}",
                f"Optional Documents: {completeness.optional_present}/{completeness.optional_total}",
            ]

            missing = [d for d in completeness.required_documents + completeness.optional_documents if d.status == "missing"]
            if missing:
                lines.append("Missing Documents:")
                for doc in missing:
                    lines.append(f"  - {doc.label}")

            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Failed to get completeness for {property_id}: {e}")
            return "Document completeness data unavailable"

    async def _build_gaps_context(self, property_id: str) -> str:
        """Build coverage gaps context string."""
        stmt = (
            select(CoverageGap)
            .where(
                CoverageGap.property_id == property_id,
                CoverageGap.status == "open",
                CoverageGap.deleted_at.is_(None),
            )
            .order_by(CoverageGap.severity.desc())
            .limit(10)
        )
        result = await self.session.execute(stmt)
        gaps = list(result.scalars().all())

        if not gaps:
            return "No open coverage gaps detected"

        lines = [f"Open Coverage Gaps ({len(gaps)} total):"]
        for gap in gaps:
            lines.append(f"\n  {gap.severity.upper()}: {gap.title}")
            lines.append(f"    Type: {gap.gap_type}")
            if gap.gap_amount:
                lines.append(f"    Gap Amount: ${gap.gap_amount:,.2f}")
            if gap.current_value and gap.recommended_value:
                lines.append(f"    Current: {gap.current_value} -> Recommended: {gap.recommended_value}")

        return "\n".join(lines)

    def _format_external_risk_context(self, risk_result: PropertyRiskResult) -> str:
        """Format external risk data for the LLM prompt.

        Args:
            risk_result: Property risk enrichment result from Parallel AI.

        Returns:
            Formatted string for inclusion in the prompt.
        """
        lines = []

        # Flood risk
        flood = risk_result.flood_risk
        if flood.zone:
            lines.append(f"Flood Zone: {flood.zone} ({flood.zone_description or 'N/A'})")
            lines.append(f"Flood Risk Level: {flood.risk_level}")
        else:
            lines.append("Flood Zone: Not determined")

        # Fire protection
        fire = risk_result.fire_protection
        if fire.protection_class:
            lines.append(f"\nFire Protection Class: {fire.protection_class}")
            if fire.fire_station_distance_miles:
                lines.append(f"Fire Station Distance: {fire.fire_station_distance_miles} miles")
            if fire.hydrant_distance_feet:
                lines.append(f"Hydrant Distance: {fire.hydrant_distance_feet} feet")

        # Weather/CAT risks
        weather = risk_result.weather_risk
        lines.append("\nWeather/CAT Exposure:")
        lines.append(f"  Hurricane Risk: {weather.hurricane_risk}")
        lines.append(f"  Tornado Risk: {weather.tornado_risk}")
        lines.append(f"  Hail Risk: {weather.hail_risk}")
        lines.append(f"  Wildfire Risk: {weather.wildfire_risk}")
        lines.append(f"  Earthquake Risk: {weather.earthquake_risk}")

        if weather.historical_events:
            lines.append("  Historical Events:")
            for event in weather.historical_events[:3]:
                lines.append(f"    - {event}")

        # Crime risk
        crime = risk_result.crime_risk
        if crime.crime_index is not None or crime.crime_grade:
            lines.append(f"\nCrime Risk: {crime.risk_level}")
            if crime.crime_index:
                lines.append(f"  Crime Index: {crime.crime_index}/100")
            if crime.crime_grade:
                lines.append(f"  Crime Grade: {crime.crime_grade}")

        # Environmental risk
        env = risk_result.environmental_risk
        if env.hazards or env.superfund_nearby or env.industrial_nearby:
            lines.append(f"\nEnvironmental Risk: {env.risk_level}")
            if env.superfund_nearby:
                lines.append("  ⚠️ Superfund site nearby")
            if env.industrial_nearby:
                lines.append("  ⚠️ Industrial facilities nearby")
            if env.hazards:
                lines.append("  Hazards: " + ", ".join(env.hazards[:3]))

        # Overall score and implications
        if risk_result.overall_risk_score is not None:
            lines.append(f"\nOverall Risk Score: {risk_result.overall_risk_score}/100")

        if risk_result.risk_summary:
            lines.append(f"\nRisk Summary: {risk_result.risk_summary}")

        if risk_result.insurance_implications:
            lines.append("\nInsurance Implications:")
            for implication in risk_result.insurance_implications[:5]:
                lines.append(f"  - {implication}")

        return "\n".join(lines) if lines else "No external risk data available."

    def _risk_result_to_dict(self, risk_result: PropertyRiskResult) -> dict:
        """Convert PropertyRiskResult to a dictionary for storage.

        Args:
            risk_result: Property risk enrichment result.

        Returns:
            Dictionary representation of the risk data.
        """
        return {
            "address": risk_result.address,
            "enrichment_date": risk_result.enrichment_date.isoformat(),
            "flood_risk": {
                "zone": risk_result.flood_risk.zone,
                "zone_description": risk_result.flood_risk.zone_description,
                "risk_level": risk_result.flood_risk.risk_level,
            },
            "fire_protection": {
                "protection_class": risk_result.fire_protection.protection_class,
                "fire_station_distance_miles": risk_result.fire_protection.fire_station_distance_miles,
                "hydrant_distance_feet": risk_result.fire_protection.hydrant_distance_feet,
            },
            "weather_risk": {
                "hurricane_risk": risk_result.weather_risk.hurricane_risk,
                "tornado_risk": risk_result.weather_risk.tornado_risk,
                "hail_risk": risk_result.weather_risk.hail_risk,
                "wildfire_risk": risk_result.weather_risk.wildfire_risk,
                "earthquake_risk": risk_result.weather_risk.earthquake_risk,
                "historical_events": risk_result.weather_risk.historical_events,
            },
            "crime_risk": {
                "crime_index": risk_result.crime_risk.crime_index,
                "crime_grade": risk_result.crime_risk.crime_grade,
                "risk_level": risk_result.crime_risk.risk_level,
            },
            "environmental_risk": {
                "hazards": risk_result.environmental_risk.hazards,
                "superfund_nearby": risk_result.environmental_risk.superfund_nearby,
                "industrial_nearby": risk_result.environmental_risk.industrial_nearby,
                "risk_level": risk_result.environmental_risk.risk_level,
            },
            "overall_risk_score": risk_result.overall_risk_score,
            "risk_summary": risk_result.risk_summary,
            "insurance_implications": risk_result.insurance_implications,
            "sources": risk_result.sources,
            "latency_ms": risk_result.total_latency_ms,
        }

    async def _call_llm(self, user_message: str) -> str:
        """Call the LLM API."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Health Score",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 3000,
                    "temperature": 0.3,
                },
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                raise HealthScoreError(f"LLM API error: {response.status_code}")

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                raise HealthScoreError("No response from LLM")

            return choices[0].get("message", {}).get("content", "")

    def _extract_json_from_response(self, response: str) -> dict:
        """Extract JSON from a response that may contain extra text."""
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Return default structure
        return {
            "total_score": 50,
            "grade": "C",
            "components": {
                name: {"score": max_score / 2, "reasoning": "Unable to analyze"}
                for name, max_score in self.COMPONENT_MAX_SCORES.items()
            },
            "executive_summary": "Unable to complete health score analysis.",
            "recommendations": [],
            "risk_factors": [],
            "strengths": [],
        }

    def _calculate_grade(self, score: int) -> str:
        """Calculate letter grade from score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


def get_health_score_service(session: AsyncSession) -> HealthScoreService:
    """Factory function to create HealthScoreService.

    Args:
        session: Database session.

    Returns:
        HealthScoreService instance.
    """
    return HealthScoreService(session)
