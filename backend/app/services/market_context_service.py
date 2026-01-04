"""Market Context Service - LLM-synthesized market analysis and negotiation intelligence.

This service provides:
1. Market condition assessment (hardening, softening, stable)
2. Policy analysis from structured data
3. Year-over-year change analysis
4. Negotiation leverage and recommendations

Uses Gemini 2.5 Flash via OpenRouter for LLM synthesis.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.claim import Claim
from app.models.coverage import Coverage
from app.models.insurance_program import InsuranceProgram
from app.models.market_context import MarketContext
from app.models.policy import Policy
from app.models.property import Property

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"

# Cache validity (days)
CACHE_VALIDITY_DAYS = 7


class MarketContextError(Exception):
    """Base exception for market context errors."""
    pass


class MarketContextAPIError(MarketContextError):
    """Raised when LLM API returns an error."""
    pass


@dataclass
class PolicyAnalysis:
    """Analysis of policy terms."""

    key_exclusions: list[str] = field(default_factory=list)
    notable_sublimits: list[dict] = field(default_factory=list)
    unusual_terms: list[str] = field(default_factory=list)
    coverage_strengths: list[str] = field(default_factory=list)
    coverage_weaknesses: list[str] = field(default_factory=list)


@dataclass
class YoYChange:
    """Year-over-year change analysis."""

    premium_change_pct: float | None = None
    limit_changes: list[dict] = field(default_factory=list)
    deductible_changes: list[dict] = field(default_factory=list)
    new_exclusions: list[str] = field(default_factory=list)
    removed_coverages: list[str] = field(default_factory=list)


@dataclass
class NegotiationRecommendation:
    """Recommendation for renewal negotiation."""

    action: str
    priority: str  # high, medium, low
    rationale: str


@dataclass
class MarketContextResult:
    """Result of market context analysis."""

    property_id: str
    property_name: str
    analysis_date: datetime
    valid_until: datetime

    # Market assessment
    market_condition: str  # hardening, softening, stable, volatile
    market_condition_reasoning: str | None

    # Property-specific analysis
    property_risk_profile: str | None
    carrier_relationship_assessment: str | None

    # Policy analysis
    policy_analysis: PolicyAnalysis | None
    yoy_changes: YoYChange | None

    # Negotiation intelligence
    negotiation_leverage: list[str]
    negotiation_recommendations: list[NegotiationRecommendation]

    # Risk insights
    risk_insights: list[str]

    # Executive summary
    executive_summary: str | None

    # Metadata
    status: str
    model_used: str | None
    latency_ms: int


# LLM Prompts
MARKET_ANALYSIS_SYSTEM_PROMPT = """You are an expert commercial real estate insurance market analyst. Analyze the provided property and policy data to provide comprehensive market context and negotiation intelligence.

Your analysis should:
1. Assess current market conditions based on the data patterns
2. Identify policy strengths and weaknesses
3. Provide specific, actionable negotiation recommendations
4. Be grounded in the actual data provided - cite specific numbers

Respond in JSON format:
{
    "market_condition": "hardening|softening|stable|volatile",
    "market_condition_reasoning": "2-3 sentences explaining the assessment based on data",
    "property_risk_profile": "Assessment of property-specific risk factors",
    "carrier_relationship_assessment": "Assessment of carrier relationship based on policy history",
    "policy_analysis": {
        "key_exclusions": ["List of significant exclusions"],
        "notable_sublimits": [{"coverage": "...", "limit": <number>, "concern": "..."}],
        "unusual_terms": ["Any unusual policy terms"],
        "coverage_strengths": ["Positive aspects of current coverage"],
        "coverage_weaknesses": ["Areas needing improvement"]
    },
    "yoy_changes": {
        "premium_change_pct": <percentage change>,
        "limit_changes": [{"coverage": "...", "old": <number>, "new": <number>}],
        "deductible_changes": [{"coverage": "...", "old": <number>, "new": <number>}],
        "new_exclusions": ["Any new exclusions added"],
        "removed_coverages": ["Any coverages that were removed"]
    },
    "negotiation_leverage": [
        "Specific leverage point 1 based on data",
        "Specific leverage point 2"
    ],
    "negotiation_recommendations": [
        {
            "action": "Specific negotiation action",
            "priority": "high|medium|low",
            "rationale": "Why this action and expected outcome"
        }
    ],
    "risk_insights": [
        "Market trend insight 1",
        "Property-specific risk insight 2"
    ],
    "executive_summary": "3-5 sentence executive summary of the market context and key recommendations"
}"""

MARKET_ANALYSIS_USER_PROMPT = """Analyze the market context for this property's insurance renewal.

PROPERTY INFORMATION:
{property_context}

BUILDINGS:
{buildings_context}

CURRENT INSURANCE PROGRAM:
{program_context}

POLICIES & COVERAGES (Current Year):
{current_policies_context}

POLICIES & COVERAGES (Previous Year):
{previous_policies_context}

LOSS HISTORY:
{claims_context}

PREMIUM HISTORY:
{premium_history}

Provide comprehensive market context analysis and negotiation intelligence for the upcoming renewal."""


class MarketContextService:
    """Service for generating market context analysis."""

    def __init__(self, session: AsyncSession, api_key: str | None = None):
        """Initialize market context service.

        Args:
            session: Database session.
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.session = session
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL

        if not self.api_key:
            logger.warning("OpenRouter API key not configured for market context")

    async def analyze_market_context(
        self,
        property_id: str,
        force: bool = False,
        include_yoy: bool = True,
        include_negotiation: bool = True,
    ) -> MarketContextResult:
        """Analyze market context for a property.

        Args:
            property_id: Property ID.
            force: Force reanalysis.
            include_yoy: Include year-over-year analysis.
            include_negotiation: Include negotiation recommendations.

        Returns:
            MarketContextResult with analysis.
        """
        if not self.api_key:
            raise MarketContextError("OpenRouter API key not configured")

        # Load property with full context
        prop = await self._load_property_with_context(property_id)
        if not prop:
            raise MarketContextError(f"Property {property_id} not found")

        # Check for valid cached analysis
        if not force:
            cached = await self._get_cached_analysis(property_id)
            if cached and cached.valid_until > datetime.now(timezone.utc):
                logger.info(f"Using cached market context for property {property_id}")
                return self._model_to_result(cached, prop)

        # Get current and previous programs
        current_program, previous_program = self._get_programs(prop)
        if not current_program:
            raise MarketContextError(
                f"No active insurance program found for property {property_id}"
            )

        # Build context
        property_context = self._build_property_context(prop)
        buildings_context = self._build_buildings_context(prop)
        program_context = self._build_program_context(current_program)
        current_policies = self._build_policies_context(current_program.policies)
        previous_policies = (
            self._build_policies_context(previous_program.policies)
            if previous_program
            else "No previous year data available."
        )
        claims_context = self._build_claims_context(prop)
        premium_history = self._build_premium_history(prop)

        # Build user prompt
        user_prompt = MARKET_ANALYSIS_USER_PROMPT.format(
            property_context=property_context,
            buildings_context=buildings_context,
            program_context=program_context,
            current_policies_context=current_policies,
            previous_policies_context=previous_policies,
            claims_context=claims_context,
            premium_history=premium_history,
        )

        # Call LLM
        start_time = time.time()
        llm_response = await self._call_llm(MARKET_ANALYSIS_SYSTEM_PROMPT, user_prompt)
        latency_ms = int((time.time() - start_time) * 1000)

        # Parse response
        analysis = self._parse_llm_response(llm_response)

        # Build result
        now = datetime.now(timezone.utc)
        result = MarketContextResult(
            property_id=property_id,
            property_name=prop.name,
            analysis_date=now,
            valid_until=now + timedelta(days=CACHE_VALIDITY_DAYS),
            market_condition=analysis.get("market_condition", "stable"),
            market_condition_reasoning=analysis.get("market_condition_reasoning"),
            property_risk_profile=analysis.get("property_risk_profile"),
            carrier_relationship_assessment=analysis.get("carrier_relationship_assessment"),
            policy_analysis=self._build_policy_analysis(analysis.get("policy_analysis", {})),
            yoy_changes=self._build_yoy_changes(analysis.get("yoy_changes", {})) if include_yoy else None,
            negotiation_leverage=analysis.get("negotiation_leverage", []) if include_negotiation else [],
            negotiation_recommendations=self._build_negotiation_recommendations(
                analysis.get("negotiation_recommendations", [])
            ) if include_negotiation else [],
            risk_insights=analysis.get("risk_insights", []),
            executive_summary=analysis.get("executive_summary"),
            status="current",
            model_used=self.model,
            latency_ms=latency_ms,
        )

        # Save to database
        await self._save_analysis(result)

        return result

    async def get_market_context(self, property_id: str) -> MarketContextResult | None:
        """Get cached market context for a property.

        Args:
            property_id: Property ID.

        Returns:
            MarketContextResult or None.
        """
        cached = await self._get_cached_analysis(property_id)
        if not cached:
            return None

        prop = await self._load_property_with_context(property_id)
        if not prop:
            return None

        return self._model_to_result(cached, prop)

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _load_property_with_context(self, property_id: str) -> Property | None:
        """Load property with full context."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.buildings),
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                ).selectinload(Policy.coverages),
                selectinload(Property.claims),
            )
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_cached_analysis(self, property_id: str) -> MarketContext | None:
        """Get cached analysis if still valid."""
        stmt = (
            select(MarketContext)
            .where(
                MarketContext.property_id == property_id,
                MarketContext.status == "current",
                MarketContext.deleted_at.is_(None),
            )
            .order_by(MarketContext.analysis_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _get_programs(
        self, prop: Property
    ) -> tuple[InsuranceProgram | None, InsuranceProgram | None]:
        """Get current and previous insurance programs."""
        programs = sorted(
            prop.insurance_programs,
            key=lambda p: p.program_year,
            reverse=True,
        )

        current = next((p for p in programs if p.status == "active"), None)
        if not current and programs:
            current = programs[0]

        previous = None
        if current and len(programs) > 1:
            previous = next(
                (p for p in programs if p.program_year == current.program_year - 1),
                None,
            )

        return current, previous

    def _build_property_context(self, prop: Property) -> str:
        """Build property context string."""
        lines = [
            f"Name: {prop.name}",
            f"Type: {prop.property_type or 'N/A'}",
            f"Address: {prop.address or 'N/A'}, {prop.city or ''}, {prop.state or ''}",
            f"Units: {prop.units or 'N/A'}",
            f"Square Feet: {prop.sq_ft:,}" if prop.sq_ft else "Square Feet: N/A",
            f"Year Built: {prop.year_built or 'N/A'}",
            f"Construction: {prop.construction_type or 'N/A'}",
            f"Roof Type: {prop.roof_type or 'N/A'}",
            f"Roof Year: {prop.roof_year or 'N/A'}",
            f"Flood Zone: {prop.flood_zone or 'N/A'}",
            f"Protection Class: {prop.protection_class or 'N/A'}",
            f"Sprinklers: {'Yes' if prop.has_sprinklers else 'No' if prop.has_sprinklers is False else 'Unknown'}",
        ]
        return "\n".join(lines)

    def _build_buildings_context(self, prop: Property) -> str:
        """Build buildings context string."""
        if not prop.buildings:
            return "No building data available."

        lines = []
        total_value = Decimal("0")
        for i, bldg in enumerate(prop.buildings, 1):
            value = bldg.building_value or Decimal("0")
            total_value += value
            lines.append(
                f"Building {i}: {bldg.name or 'Unnamed'}\n"
                f"  Value: ${float(value):,.0f}\n"
                f"  Type: {bldg.construction_type or 'N/A'}\n"
                f"  Year: {bldg.year_built or 'N/A'}\n"
                f"  SqFt: {bldg.sq_ft or 'N/A'}"
            )

        lines.append(f"\nTotal Building Value: ${float(total_value):,.0f}")
        return "\n".join(lines)

    def _build_program_context(self, program: InsuranceProgram) -> str:
        """Build program context string."""
        lines = [
            f"Program Year: {program.program_year}",
            f"Effective: {program.effective_date or 'N/A'}",
            f"Expiration: {program.expiration_date or 'N/A'}",
            f"Total Insured Value: ${float(program.total_insured_value or 0):,.0f}",
            f"Total Premium: ${float(program.total_premium or 0):,.0f}",
            f"Number of Policies: {len(program.policies)}",
        ]
        return "\n".join(lines)

    def _build_policies_context(self, policies: list[Policy]) -> str:
        """Build policies and coverages context string."""
        if not policies:
            return "No policy data available."

        lines = []
        for policy in policies:
            lines.append(
                f"\n{policy.policy_type.upper()} POLICY"
            )
            lines.append(f"  Carrier: {policy.carrier_name or 'Unknown'}")
            lines.append(f"  Number: {policy.policy_number or 'N/A'}")
            lines.append(f"  Premium: ${float(policy.premium or 0):,.0f}")
            lines.append(f"  Period: {policy.effective_date or 'N/A'} to {policy.expiration_date or 'N/A'}")

            if policy.coverages:
                lines.append("  Coverages:")
                for cov in policy.coverages[:15]:  # Limit to avoid token overflow
                    limit = f"${float(cov.limit_amount or 0):,.0f}" if cov.limit_amount else "N/A"
                    ded = f"${float(cov.deductible_amount or 0):,.0f}" if cov.deductible_amount else "N/A"
                    lines.append(f"    - {cov.coverage_name or 'Coverage'}: Limit {limit}, Deductible {ded}")

                    # Include sublimits if present
                    if cov.sublimit:
                        lines.append(f"      Sublimit: ${float(cov.sublimit):,.0f}")

                    # Include exclusions text if present
                    if cov.exclusions_text:
                        lines.append(f"      Exclusions: {cov.exclusions_text[:200]}")

        return "\n".join(lines)

    def _build_claims_context(self, prop: Property) -> str:
        """Build claims/loss history context."""
        if not prop.claims:
            return "No claims in the past 5 years. Clean loss history."

        # Filter to last 5 years
        five_years_ago = date.today().replace(year=date.today().year - 5)
        recent_claims = [
            c for c in prop.claims
            if c.loss_date and c.loss_date >= five_years_ago
        ]

        if not recent_claims:
            return "No claims in the past 5 years. Clean loss history."

        total_paid = sum(float(c.paid_amount or 0) for c in recent_claims)
        total_reserved = sum(float(c.reserved_amount or 0) for c in recent_claims)
        total_incurred = total_paid + total_reserved

        lines = [
            f"Claims in past 5 years: {len(recent_claims)}",
            f"Total Paid: ${total_paid:,.0f}",
            f"Total Reserved: ${total_reserved:,.0f}",
            f"Total Incurred: ${total_incurred:,.0f}",
            "",
            "Claim Details:",
        ]

        for claim in sorted(recent_claims, key=lambda c: c.loss_date or date.min, reverse=True)[:10]:
            lines.append(
                f"  - {claim.loss_date}: {claim.claim_type or 'Unknown'}\n"
                f"    Paid: ${float(claim.paid_amount or 0):,.0f}, "
                f"Reserved: ${float(claim.reserved_amount or 0):,.0f}\n"
                f"    Status: {claim.status or 'Unknown'}\n"
                f"    Description: {(claim.description or 'N/A')[:100]}"
            )

        return "\n".join(lines)

    def _build_premium_history(self, prop: Property) -> str:
        """Build premium history."""
        programs = sorted(
            prop.insurance_programs,
            key=lambda p: p.program_year,
            reverse=True,
        )[:5]  # Last 5 years

        if not programs:
            return "No premium history available."

        lines = ["Premium by Year:"]
        premiums = []
        for program in programs:
            premium = float(program.total_premium or 0)
            premiums.append(premium)
            lines.append(f"  {program.program_year}: ${premium:,.0f}")

        # Calculate trends
        if len(premiums) >= 2:
            latest = premiums[0]
            previous = premiums[1]
            if previous > 0:
                yoy_change = ((latest - previous) / previous) * 100
                lines.append(f"\nYear-over-year change: {yoy_change:+.1f}%")

        if len(premiums) >= 3:
            # Calculate CAGR
            first = premiums[-1]
            last = premiums[0]
            years = len(premiums) - 1
            if first > 0 and years > 0:
                cagr = ((last / first) ** (1 / years) - 1) * 100
                lines.append(f"Compound annual growth rate: {cagr:+.1f}%")

        return "\n".join(lines)

    def _build_policy_analysis(self, data: dict) -> PolicyAnalysis:
        """Build PolicyAnalysis from LLM data."""
        return PolicyAnalysis(
            key_exclusions=data.get("key_exclusions", []),
            notable_sublimits=data.get("notable_sublimits", []),
            unusual_terms=data.get("unusual_terms", []),
            coverage_strengths=data.get("coverage_strengths", []),
            coverage_weaknesses=data.get("coverage_weaknesses", []),
        )

    def _build_yoy_changes(self, data: dict) -> YoYChange:
        """Build YoYChange from LLM data."""
        return YoYChange(
            premium_change_pct=data.get("premium_change_pct"),
            limit_changes=data.get("limit_changes", []),
            deductible_changes=data.get("deductible_changes", []),
            new_exclusions=data.get("new_exclusions", []),
            removed_coverages=data.get("removed_coverages", []),
        )

    def _build_negotiation_recommendations(
        self, data: list[dict]
    ) -> list[NegotiationRecommendation]:
        """Build NegotiationRecommendation list from LLM data."""
        return [
            NegotiationRecommendation(
                action=item.get("action", ""),
                priority=item.get("priority", "medium"),
                rationale=item.get("rationale", ""),
            )
            for item in data
        ]

    async def _save_analysis(self, result: MarketContextResult) -> MarketContext:
        """Save analysis to database."""
        # Mark existing as superseded
        stmt = (
            select(MarketContext)
            .where(
                MarketContext.property_id == result.property_id,
                MarketContext.status == "current",
                MarketContext.deleted_at.is_(None),
            )
        )
        existing = await self.session.execute(stmt)
        for analysis in existing.scalars().all():
            analysis.status = "superseded"

        # Create new analysis
        analysis = MarketContext(
            property_id=result.property_id,
            analysis_date=result.analysis_date,
            valid_until=result.valid_until,
            market_condition=result.market_condition,
            market_condition_reasoning=result.market_condition_reasoning,
            property_risk_profile=result.property_risk_profile,
            carrier_relationship_assessment=result.carrier_relationship_assessment,
            policy_analysis={
                "key_exclusions": result.policy_analysis.key_exclusions if result.policy_analysis else [],
                "notable_sublimits": result.policy_analysis.notable_sublimits if result.policy_analysis else [],
                "unusual_terms": result.policy_analysis.unusual_terms if result.policy_analysis else [],
                "coverage_strengths": result.policy_analysis.coverage_strengths if result.policy_analysis else [],
                "coverage_weaknesses": result.policy_analysis.coverage_weaknesses if result.policy_analysis else [],
            } if result.policy_analysis else None,
            yoy_changes={
                "premium_change_pct": result.yoy_changes.premium_change_pct,
                "limit_changes": result.yoy_changes.limit_changes,
                "deductible_changes": result.yoy_changes.deductible_changes,
                "new_exclusions": result.yoy_changes.new_exclusions,
                "removed_coverages": result.yoy_changes.removed_coverages,
            } if result.yoy_changes else None,
            negotiation_leverage=result.negotiation_leverage,
            negotiation_recommendations=[
                {"action": r.action, "priority": r.priority, "rationale": r.rationale}
                for r in result.negotiation_recommendations
            ],
            risk_insights=result.risk_insights,
            executive_summary=result.executive_summary,
            status="current",
            llm_model_used=result.model_used,
            llm_latency_ms=result.latency_ms,
        )

        self.session.add(analysis)
        await self.session.flush()

        logger.info(f"Saved market context analysis for property {result.property_id}")
        return analysis

    def _model_to_result(
        self, model: MarketContext, prop: Property
    ) -> MarketContextResult:
        """Convert database model to result dataclass."""
        policy_data = model.policy_analysis or {}
        yoy_data = model.yoy_changes or {}

        return MarketContextResult(
            property_id=model.property_id,
            property_name=prop.name,
            analysis_date=model.analysis_date,
            valid_until=model.valid_until,
            market_condition=model.market_condition,
            market_condition_reasoning=model.market_condition_reasoning,
            property_risk_profile=model.property_risk_profile,
            carrier_relationship_assessment=model.carrier_relationship_assessment,
            policy_analysis=PolicyAnalysis(
                key_exclusions=policy_data.get("key_exclusions", []),
                notable_sublimits=policy_data.get("notable_sublimits", []),
                unusual_terms=policy_data.get("unusual_terms", []),
                coverage_strengths=policy_data.get("coverage_strengths", []),
                coverage_weaknesses=policy_data.get("coverage_weaknesses", []),
            ) if policy_data else None,
            yoy_changes=YoYChange(
                premium_change_pct=yoy_data.get("premium_change_pct"),
                limit_changes=yoy_data.get("limit_changes", []),
                deductible_changes=yoy_data.get("deductible_changes", []),
                new_exclusions=yoy_data.get("new_exclusions", []),
                removed_coverages=yoy_data.get("removed_coverages", []),
            ) if yoy_data else None,
            negotiation_leverage=model.negotiation_leverage or [],
            negotiation_recommendations=[
                NegotiationRecommendation(
                    action=r.get("action", ""),
                    priority=r.get("priority", "medium"),
                    rationale=r.get("rationale", ""),
                )
                for r in (model.negotiation_recommendations or [])
            ],
            risk_insights=model.risk_insights or [],
            executive_summary=model.executive_summary,
            status=model.status,
            model_used=model.llm_model_used,
            latency_ms=model.llm_latency_ms or 0,
        )

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call the LLM API."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Market Context",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 3000,
                    "temperature": 0.3,
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenRouter API error: {response.status_code} - {error_detail}")
                raise MarketContextAPIError(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                raise MarketContextError("No response from LLM")

            return choices[0].get("message", {}).get("content", "")

    def _parse_llm_response(self, response: str) -> dict:
        """Parse LLM response JSON."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            logger.warning("Failed to parse LLM response, using defaults")
            return {
                "market_condition": "stable",
                "market_condition_reasoning": response[:500] if response else "",
                "policy_analysis": {},
                "yoy_changes": {},
                "negotiation_leverage": [],
                "negotiation_recommendations": [],
                "risk_insights": [],
                "executive_summary": "",
            }


def get_market_context_service(session: AsyncSession) -> MarketContextService:
    """Factory function to create MarketContextService.

    Args:
        session: Database session.

    Returns:
        MarketContextService instance.
    """
    return MarketContextService(session)
