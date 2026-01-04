"""Renewal Forecast Service - Premium predictions with rule-based and LLM analysis.

This service provides:
1. Rule-based point estimates for premium forecasting
2. LLM-generated range predictions with reasoning
3. Factor-by-factor analysis (loss history, market trends, property changes, etc.)
4. Negotiation leverage points

Uses Gemini 2.5 Flash via OpenRouter for LLM calls.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
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
from app.models.policy import Policy
from app.models.property import Property
from app.models.renewal_forecast import RenewalForecast
from app.services.market_intelligence_service import (
    MarketIntelligenceService,
    MarketIntelligenceError,
    get_market_intelligence_service,
)

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"

# Forecasting weights
FACTOR_WEIGHTS = {
    "loss_history": 0.30,
    "market_trends": 0.25,
    "property_changes": 0.15,
    "coverage_changes": 0.15,
    "carrier_appetite": 0.15,
}


class RenewalForecastError(Exception):
    """Base exception for renewal forecast errors."""
    pass


class RenewalForecastAPIError(RenewalForecastError):
    """Raised when LLM API returns an error."""
    pass


@dataclass
class FactorAnalysis:
    """Analysis of a single forecasting factor."""

    weight: float
    impact: float  # Percentage impact on premium
    reasoning: str


@dataclass
class ForecastResult:
    """Result of renewal forecast generation."""

    property_id: str
    property_name: str
    program_id: str | None
    policy_id: str | None

    # Context
    renewal_year: int
    current_expiration_date: date
    current_premium: Decimal | None

    # Rule-based estimate
    rule_based_estimate: Decimal | None
    rule_based_change_pct: float | None

    # LLM predictions
    llm_predicted_low: Decimal | None
    llm_predicted_mid: Decimal | None
    llm_predicted_high: Decimal | None
    llm_confidence_score: int | None

    # Factor breakdown
    factor_breakdown: dict[str, FactorAnalysis]

    # LLM analysis
    reasoning: str
    market_context: str
    negotiation_points: list[str]

    # Metadata
    forecast_date: datetime
    model_used: str
    latency_ms: int

    # Live market intelligence (from Parallel AI) - optional fields at end
    live_market_data: dict[str, Any] | None = None
    market_intel_latency_ms: int | None = None


# LLM Prompts
FORECAST_SYSTEM_PROMPT = """You are an expert commercial real estate insurance analyst specializing in premium forecasting and renewal intelligence.

Your task is to analyze the provided property and insurance data to predict renewal premiums. Your analysis must be:
1. Grounded in the actual data provided - cite specific numbers
2. Conservative but realistic in predictions
3. Clear about uncertainty and assumptions
4. Actionable with specific negotiation strategies

Respond in JSON format with these exact fields:
{
    "predicted_premium_low": <number - lower bound estimate>,
    "predicted_premium_mid": <number - most likely estimate>,
    "predicted_premium_high": <number - upper bound estimate>,
    "confidence_score": <1-100 - confidence in prediction>,
    "factor_analysis": {
        "loss_history": {
            "impact": <percentage impact, e.g., 2.5 means +2.5%>,
            "reasoning": "Explanation citing specific claims data"
        },
        "market_trends": {
            "impact": <percentage>,
            "reasoning": "Explanation of market conditions"
        },
        "property_changes": {
            "impact": <percentage>,
            "reasoning": "Explanation of property value/risk changes"
        },
        "coverage_changes": {
            "impact": <percentage>,
            "reasoning": "Explanation of coverage adjustments"
        },
        "carrier_appetite": {
            "impact": <percentage>,
            "reasoning": "Assessment of carrier relationship and appetite"
        }
    },
    "reasoning": "Comprehensive 3-5 sentence explanation of the prediction synthesizing all factors",
    "market_context": "2-3 sentences on current market conditions affecting this property type/region",
    "negotiation_points": [
        "Specific leverage point 1 based on the data",
        "Specific leverage point 2",
        "..."
    ]
}"""

FORECAST_USER_PROMPT = """Analyze this property's insurance data and predict the renewal premium.

PROPERTY INFORMATION:
{property_context}

BUILDINGS:
{buildings_context}

CURRENT INSURANCE PROGRAM:
{program_context}

POLICIES & COVERAGES:
{policies_context}

LOSS HISTORY (Claims):
{claims_context}

PREMIUM HISTORY:
{premium_history}

LIVE MARKET INTELLIGENCE (from real-time web research):
{market_intelligence}

Current Premium: ${current_premium:,.2f}
Expiration Date: {expiration_date}
Days Until Renewal: {days_until_renewal}

Based on this data AND the live market intelligence, predict the renewal premium and provide factor-by-factor analysis.
Pay special attention to the market trends and carrier appetite data from the live research."""


class RenewalForecastService:
    """Service for generating renewal premium forecasts."""

    def __init__(self, session: AsyncSession, api_key: str | None = None):
        """Initialize renewal forecast service.

        Args:
            session: Database session.
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.session = session
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL
        self.market_intel_service = get_market_intelligence_service(session)

        if not self.api_key:
            logger.warning("OpenRouter API key not configured for renewal forecasting")

    async def generate_forecast(
        self,
        property_id: str,
        force: bool = False,
        include_market_context: bool = True,
        use_live_market_intel: bool = True,
    ) -> ForecastResult:
        """Generate a renewal forecast for a property.

        Args:
            property_id: Property ID to forecast.
            force: Force regeneration even if recent forecast exists.
            include_market_context: Include market context analysis.
            use_live_market_intel: Fetch live market intelligence from Parallel AI.

        Returns:
            ForecastResult with predictions and analysis.
        """
        if not self.api_key:
            raise RenewalForecastError("OpenRouter API key not configured")

        # Load property with full context
        prop = await self._load_property_with_context(property_id)
        if not prop:
            raise RenewalForecastError(f"Property {property_id} not found")

        # Find the active program and primary policy
        program, policy = self._get_active_program_and_policy(prop)
        if not program or not policy:
            raise RenewalForecastError(
                f"No active insurance program found for property {property_id}"
            )

        # Check for recent forecast
        if not force:
            existing = await self._get_recent_forecast(property_id)
            if existing:
                logger.info(f"Using existing forecast for property {property_id}")
                return self._forecast_model_to_result(existing, prop)

        # Calculate rule-based estimate first
        current_premium = self._calculate_total_premium(program)
        rule_estimate, rule_change_pct = self._calculate_rule_based_estimate(
            prop, program, current_premium
        )

        # Fetch live market intelligence from Parallel AI
        live_market_data: dict[str, Any] | None = None
        market_intel_latency: int | None = None
        market_intelligence_text = "Live market data not available."

        if use_live_market_intel:
            try:
                logger.info(f"Fetching live market intelligence for property {property_id}")
                market_intel_start = time.time()
                live_market_data = await self.market_intel_service.get_market_intelligence_for_renewal(
                    property_id
                )
                market_intel_latency = int((time.time() - market_intel_start) * 1000)

                if live_market_data and not live_market_data.get("error"):
                    market_intelligence_text = self._format_market_intelligence(live_market_data)
                    logger.info(
                        f"Live market intel fetched for {property_id}: "
                        f"rate trend {live_market_data.get('rate_direction', 'N/A')}, "
                        f"latency {market_intel_latency}ms"
                    )
                else:
                    logger.warning(f"Market intelligence unavailable: {live_market_data.get('error', 'Unknown error')}")
            except MarketIntelligenceError as e:
                logger.warning(f"Failed to fetch market intelligence: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching market intelligence: {e}")

        # Build context for LLM
        property_context = self._build_property_context(prop)
        buildings_context = self._build_buildings_context(prop)
        program_context = self._build_program_context(program)
        policies_context = self._build_policies_context(program.policies)
        claims_context = await self._build_claims_context(prop)
        premium_history = await self._build_premium_history(prop)

        # Prepare user prompt
        expiration_date = policy.expiration_date or program.expiration_date
        days_until = (
            (expiration_date - date.today()).days if expiration_date else 0
        )

        user_prompt = FORECAST_USER_PROMPT.format(
            property_context=property_context,
            buildings_context=buildings_context,
            program_context=program_context,
            policies_context=policies_context,
            claims_context=claims_context,
            premium_history=premium_history,
            market_intelligence=market_intelligence_text,
            current_premium=float(current_premium or 0),
            expiration_date=expiration_date or "Unknown",
            days_until_renewal=days_until,
        )

        # Call LLM
        start_time = time.time()
        llm_response = await self._call_llm(FORECAST_SYSTEM_PROMPT, user_prompt)
        latency_ms = int((time.time() - start_time) * 1000)

        # Parse LLM response
        llm_result = self._parse_llm_response(llm_response)

        # Build factor breakdown
        factor_breakdown = self._build_factor_breakdown(llm_result)

        # Create result
        result = ForecastResult(
            property_id=property_id,
            property_name=prop.name,
            program_id=program.id,
            policy_id=policy.id,
            renewal_year=self._calculate_renewal_year(expiration_date),
            current_expiration_date=expiration_date,
            current_premium=current_premium,
            rule_based_estimate=rule_estimate,
            rule_based_change_pct=rule_change_pct,
            llm_predicted_low=Decimal(str(llm_result.get("predicted_premium_low", 0))),
            llm_predicted_mid=Decimal(str(llm_result.get("predicted_premium_mid", 0))),
            llm_predicted_high=Decimal(str(llm_result.get("predicted_premium_high", 0))),
            llm_confidence_score=int(llm_result.get("confidence_score", 50)),
            factor_breakdown=factor_breakdown,
            reasoning=llm_result.get("reasoning", ""),
            market_context=llm_result.get("market_context", ""),
            negotiation_points=llm_result.get("negotiation_points", []),
            live_market_data=live_market_data,
            forecast_date=datetime.now(timezone.utc),
            model_used=self.model,
            latency_ms=latency_ms,
            market_intel_latency_ms=market_intel_latency,
        )

        # Persist to database
        await self._save_forecast(result)

        return result

    async def get_forecast(self, property_id: str) -> ForecastResult | None:
        """Get the most recent forecast for a property.

        Args:
            property_id: Property ID.

        Returns:
            ForecastResult or None if no forecast exists.
        """
        forecast = await self._get_recent_forecast(property_id)
        if not forecast:
            return None

        prop = await self._load_property_with_context(property_id)
        if not prop:
            return None

        return self._forecast_model_to_result(forecast, prop)

    async def list_forecasts(
        self,
        organization_id: str | None = None,
        status: str = "active",
    ) -> list[RenewalForecast]:
        """List forecasts, optionally filtered.

        Args:
            organization_id: Filter by organization.
            status: Filter by status (active, superseded, expired).

        Returns:
            List of RenewalForecast models.
        """
        stmt = (
            select(RenewalForecast)
            .options(selectinload(RenewalForecast.property))
            .where(
                RenewalForecast.status == status,
                RenewalForecast.deleted_at.is_(None),
            )
            .order_by(RenewalForecast.current_expiration_date.asc())
        )

        if organization_id:
            stmt = stmt.join(Property).where(
                Property.organization_id == organization_id
            )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _load_property_with_context(self, property_id: str) -> Property | None:
        """Load property with full insurance context."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.buildings),
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                ).selectinload(Policy.coverages),
                selectinload(Property.claims),
                selectinload(Property.valuations),
            )
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _get_active_program_and_policy(
        self, prop: Property
    ) -> tuple[InsuranceProgram | None, Policy | None]:
        """Get the active insurance program and primary policy."""
        active_programs = [
            p for p in prop.insurance_programs if p.status == "active"
        ]
        if not active_programs:
            return None, None

        # Get most recent by expiration date
        program = max(
            active_programs,
            key=lambda p: p.expiration_date or date.min,
        )

        # Find primary policy (property policy or first available)
        policies = program.policies
        primary = next(
            (p for p in policies if p.policy_type.lower() == "property"),
            policies[0] if policies else None,
        )

        return program, primary

    async def _get_recent_forecast(
        self, property_id: str
    ) -> RenewalForecast | None:
        """Get the most recent active forecast."""
        stmt = (
            select(RenewalForecast)
            .where(
                RenewalForecast.property_id == property_id,
                RenewalForecast.status == "active",
                RenewalForecast.deleted_at.is_(None),
            )
            .order_by(RenewalForecast.forecast_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _calculate_total_premium(self, program: InsuranceProgram) -> Decimal:
        """Calculate total premium for a program."""
        total = Decimal("0")
        for policy in program.policies:
            if policy.premium:
                total += policy.premium
        return total

    def _calculate_rule_based_estimate(
        self,
        prop: Property,
        program: InsuranceProgram,
        current_premium: Decimal,
    ) -> tuple[Decimal | None, float | None]:
        """Calculate rule-based premium estimate.

        Applies simple heuristics:
        - Base market trend: +5% (assuming hardening market)
        - Loss adjustment: +/- based on claims
        - Age adjustment: +0.5% per year over 30
        """
        if not current_premium or current_premium <= 0:
            return None, None

        adjustment = 0.0

        # Base market trend (conservative 5% increase)
        adjustment += 5.0

        # Property age adjustment
        if prop.year_built:
            age = date.today().year - prop.year_built
            if age > 30:
                adjustment += min((age - 30) * 0.5, 5.0)  # Max 5% for age

        # Claims adjustment (simplified)
        claims_count = len([c for c in prop.claims if c.status != "closed"])
        if claims_count > 0:
            adjustment += min(claims_count * 2.0, 10.0)  # Max 10% for claims

        # Calculate estimate
        estimate = current_premium * (1 + adjustment / 100)
        return estimate.quantize(Decimal("0.01")), adjustment

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
                f"Building {i}: {bldg.name or 'Unnamed'} - "
                f"Value: ${float(value):,.0f}, "
                f"Type: {bldg.construction_type or 'N/A'}, "
                f"Year: {bldg.year_built or 'N/A'}"
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
            f"Policies: {len(program.policies)}",
        ]
        return "\n".join(lines)

    def _build_policies_context(self, policies: list[Policy]) -> str:
        """Build policies and coverages context string."""
        if not policies:
            return "No policy data available."

        lines = []
        for policy in policies:
            lines.append(
                f"\n{policy.policy_type.upper()} POLICY ({policy.carrier_name or 'Unknown Carrier'}):"
            )
            lines.append(f"  Number: {policy.policy_number or 'N/A'}")
            lines.append(f"  Premium: ${float(policy.premium or 0):,.0f}")
            lines.append(f"  Effective: {policy.effective_date or 'N/A'} to {policy.expiration_date or 'N/A'}")

            if policy.coverages:
                lines.append("  Coverages:")
                for cov in policy.coverages[:10]:  # Limit to avoid token overflow
                    limit = f"${float(cov.limit_amount or 0):,.0f}" if cov.limit_amount else "N/A"
                    ded = f"${float(cov.deductible_amount or 0):,.0f}" if cov.deductible_amount else "N/A"
                    lines.append(f"    - {cov.coverage_name or 'Coverage'}: Limit {limit}, Deductible {ded}")

        return "\n".join(lines)

    async def _build_claims_context(self, prop: Property) -> str:
        """Build claims/loss history context."""
        if not prop.claims:
            return "No claims in the past 3 years. Clean loss history."

        # Filter to last 3 years
        three_years_ago = date.today().replace(year=date.today().year - 3)
        recent_claims = [
            c for c in prop.claims
            if c.loss_date and c.loss_date >= three_years_ago
        ]

        if not recent_claims:
            return "No claims in the past 3 years. Clean loss history."

        total_paid = sum(float(c.paid_amount or 0) for c in recent_claims)
        total_reserved = sum(float(c.reserved_amount or 0) for c in recent_claims)

        lines = [
            f"Claims in past 3 years: {len(recent_claims)}",
            f"Total Paid: ${total_paid:,.0f}",
            f"Total Reserved: ${total_reserved:,.0f}",
            "",
            "Claim Details:",
        ]

        for claim in recent_claims[:5]:  # Limit to 5 most recent
            lines.append(
                f"  - {claim.loss_date}: {claim.claim_type or 'Unknown'} - "
                f"Paid: ${float(claim.paid_amount or 0):,.0f}, "
                f"Status: {claim.status or 'Unknown'}"
            )

        return "\n".join(lines)

    async def _build_premium_history(self, prop: Property) -> str:
        """Build premium history from past programs."""
        programs = sorted(
            prop.insurance_programs,
            key=lambda p: p.program_year,
            reverse=True,
        )[:3]  # Last 3 years

        if not programs:
            return "No premium history available."

        lines = []
        for program in programs:
            premium = program.total_premium or Decimal("0")
            lines.append(
                f"  {program.program_year}: ${float(premium):,.0f}"
            )

        # Calculate trend if we have multiple years
        if len(programs) >= 2:
            latest = float(programs[0].total_premium or 0)
            previous = float(programs[1].total_premium or 0)
            if previous > 0:
                change = ((latest - previous) / previous) * 100
                lines.append(f"\nYear-over-year change: {change:+.1f}%")

        return "\n".join(lines)

    def _format_market_intelligence(self, market_data: dict[str, Any]) -> str:
        """Format live market intelligence for the LLM prompt.

        Args:
            market_data: Market intelligence data from Parallel AI.

        Returns:
            Formatted string for inclusion in the prompt.
        """
        lines = []

        # Rate trends
        rate_trend = market_data.get("rate_trend_range") or market_data.get("rate_trend_pct")
        direction = market_data.get("rate_direction", "stable")
        if rate_trend:
            lines.append(f"Current Rate Trend: {rate_trend} ({direction})")
        else:
            lines.append(f"Market Direction: {direction}")

        # Key factors
        key_factors = market_data.get("key_factors", [])
        if key_factors:
            lines.append("\nKey Market Factors:")
            for factor in key_factors[:5]:
                lines.append(f"  - {factor}")

        # Carrier appetite
        carrier_appetite = market_data.get("carrier_appetite", {})
        if carrier_appetite:
            lines.append("\nCarrier Appetite:")
            for carrier, appetite in list(carrier_appetite.items())[:5]:
                lines.append(f"  - {carrier}: {appetite}")

        # 6-month forecast
        forecast = market_data.get("forecast_6mo")
        if forecast:
            lines.append(f"\n6-Month Forecast: {forecast}")

        # Regulatory changes
        regulatory = market_data.get("regulatory_changes", [])
        if regulatory:
            lines.append("\nRecent Regulatory Changes:")
            for change in regulatory[:3]:
                lines.append(f"  - {change}")

        # Research date
        research_date = market_data.get("research_date")
        if research_date:
            lines.append(f"\n(Market data as of: {research_date})")

        return "\n".join(lines) if lines else "No live market data available."

    def _calculate_renewal_year(self, expiration_date: date | None) -> int:
        """Calculate the renewal year."""
        if expiration_date:
            return expiration_date.year
        return date.today().year + 1

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call the LLM API."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Renewal Intelligence",
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
                raise RenewalForecastAPIError(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                raise RenewalForecastError("No response from LLM")

            return choices[0].get("message", {}).get("content", "")

    def _parse_llm_response(self, response: str) -> dict:
        """Parse LLM response JSON."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Return default structure
            logger.warning("Failed to parse LLM response, using defaults")
            return {
                "predicted_premium_low": 0,
                "predicted_premium_mid": 0,
                "predicted_premium_high": 0,
                "confidence_score": 50,
                "factor_analysis": {},
                "reasoning": response[:500] if response else "",
                "market_context": "",
                "negotiation_points": [],
            }

    def _build_factor_breakdown(self, llm_result: dict) -> dict[str, FactorAnalysis]:
        """Build factor breakdown from LLM result."""
        factor_analysis = llm_result.get("factor_analysis", {})
        breakdown = {}

        for factor, weight in FACTOR_WEIGHTS.items():
            factor_data = factor_analysis.get(factor, {})
            breakdown[factor] = FactorAnalysis(
                weight=weight,
                impact=float(factor_data.get("impact", 0)),
                reasoning=factor_data.get("reasoning", ""),
            )

        return breakdown

    async def _save_forecast(self, result: ForecastResult) -> RenewalForecast:
        """Save forecast to database."""
        # Mark existing forecasts as superseded
        stmt = (
            select(RenewalForecast)
            .where(
                RenewalForecast.property_id == result.property_id,
                RenewalForecast.status == "active",
                RenewalForecast.deleted_at.is_(None),
            )
        )
        existing = await self.session.execute(stmt)
        for forecast in existing.scalars().all():
            forecast.status = "superseded"

        # Create new forecast
        forecast = RenewalForecast(
            property_id=result.property_id,
            program_id=result.program_id,
            policy_id=result.policy_id,
            renewal_year=result.renewal_year,
            current_expiration_date=result.current_expiration_date,
            current_premium=result.current_premium,
            rule_based_estimate=result.rule_based_estimate,
            rule_based_change_pct=result.rule_based_change_pct,
            llm_predicted_low=result.llm_predicted_low,
            llm_predicted_mid=result.llm_predicted_mid,
            llm_predicted_high=result.llm_predicted_high,
            llm_confidence_score=result.llm_confidence_score,
            factor_breakdown={
                k: {"weight": v.weight, "impact": v.impact, "reasoning": v.reasoning}
                for k, v in result.factor_breakdown.items()
            },
            llm_reasoning=result.reasoning,
            llm_market_context=result.market_context,
            llm_negotiation_points=result.negotiation_points,
            status="active",
            forecast_date=result.forecast_date,
            forecast_trigger="manual",
            llm_model_used=result.model_used,
            llm_latency_ms=result.latency_ms,
        )

        self.session.add(forecast)
        await self.session.flush()

        logger.info(f"Saved renewal forecast for property {result.property_id}")
        return forecast

    def _forecast_model_to_result(
        self, forecast: RenewalForecast, prop: Property
    ) -> ForecastResult:
        """Convert database model to result dataclass."""
        factor_breakdown = {}
        if forecast.factor_breakdown:
            for k, v in forecast.factor_breakdown.items():
                factor_breakdown[k] = FactorAnalysis(
                    weight=v.get("weight", 0),
                    impact=v.get("impact", 0),
                    reasoning=v.get("reasoning", ""),
                )

        return ForecastResult(
            property_id=forecast.property_id,
            property_name=prop.name,
            program_id=forecast.program_id,
            policy_id=forecast.policy_id,
            renewal_year=forecast.renewal_year,
            current_expiration_date=forecast.current_expiration_date,
            current_premium=forecast.current_premium,
            rule_based_estimate=forecast.rule_based_estimate,
            rule_based_change_pct=float(forecast.rule_based_change_pct) if forecast.rule_based_change_pct else None,
            llm_predicted_low=forecast.llm_predicted_low,
            llm_predicted_mid=forecast.llm_predicted_mid,
            llm_predicted_high=forecast.llm_predicted_high,
            llm_confidence_score=forecast.llm_confidence_score,
            factor_breakdown=factor_breakdown,
            reasoning=forecast.llm_reasoning or "",
            market_context=forecast.llm_market_context or "",
            negotiation_points=forecast.llm_negotiation_points or [],
            forecast_date=forecast.forecast_date,
            model_used=forecast.llm_model_used or MODEL,
            latency_ms=forecast.llm_latency_ms or 0,
        )


def get_renewal_forecast_service(session: AsyncSession) -> RenewalForecastService:
    """Factory function to create RenewalForecastService.

    Args:
        session: Database session.

    Returns:
        RenewalForecastService instance.
    """
    return RenewalForecastService(session)
