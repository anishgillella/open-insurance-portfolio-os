"""Policy Comparison Service - Compare policies and programs for renewal analysis.

This service provides:
1. Policy-to-policy comparison (arbitrary or same-type)
2. Program-to-program comparison (year-over-year)
3. Coverage-level diff analysis
4. LLM-enhanced insights and recommendations

Uses Gemini 2.5 Flash via OpenRouter for LLM analysis.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.coverage import Coverage
from app.models.insurance_program import InsuranceProgram
from app.models.policy import Policy
from app.models.property import Property

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


class PolicyComparisonError(Exception):
    """Base exception for policy comparison errors."""
    pass


class PolicyComparisonAPIError(PolicyComparisonError):
    """Raised when LLM API returns an error."""
    pass


@dataclass
class CoverageComparison:
    """Comparison of a single coverage."""

    coverage_name: str
    status: str  # added, removed, changed, unchanged

    # Policy A values
    policy_a_limit: Decimal | None = None
    policy_a_deductible: Decimal | None = None
    policy_a_sublimit: Decimal | None = None

    # Policy B values
    policy_b_limit: Decimal | None = None
    policy_b_deductible: Decimal | None = None
    policy_b_sublimit: Decimal | None = None

    # Changes
    limit_change: Decimal | None = None
    limit_change_pct: float | None = None
    deductible_change: Decimal | None = None
    deductible_change_pct: float | None = None

    # LLM analysis
    impact_assessment: str | None = None


@dataclass
class PolicySummary:
    """Summary of a policy."""

    id: str
    policy_number: str | None
    policy_type: str
    carrier_name: str | None
    effective_date: date | None
    expiration_date: date | None
    premium: Decimal | None
    total_limit: Decimal | None
    coverage_count: int


@dataclass
class PolicyComparisonResult:
    """Result of policy-to-policy comparison."""

    comparison_id: str
    comparison_type: str  # yoy_renewal, arbitrary, quote_comparison
    comparison_date: datetime

    # Policies
    policy_a: PolicySummary
    policy_b: PolicySummary

    # Premium comparison
    premium_change: Decimal | None
    premium_change_pct: float | None

    # Coverage comparison
    coverages_added: list[str]
    coverages_removed: list[str]
    coverages_changed: list[CoverageComparison]
    coverages_unchanged: list[str]

    # Limit/Deductible summary
    total_limit_change: Decimal | None
    total_limit_change_pct: float | None
    avg_deductible_change_pct: float | None

    # LLM Analysis
    executive_summary: str | None
    key_changes: list[str]
    risk_implications: list[str]
    recommendations: list[str]

    # Metadata
    model_used: str | None
    latency_ms: int


@dataclass
class ProgramComparisonResult:
    """Result of program-to-program comparison."""

    comparison_id: str
    property_id: str
    property_name: str
    comparison_date: datetime

    # Programs
    program_a_year: int
    program_b_year: int
    program_a_id: str
    program_b_id: str

    # Aggregate comparison
    total_premium_a: Decimal | None
    total_premium_b: Decimal | None
    premium_change: Decimal | None
    premium_change_pct: float | None

    total_insured_value_a: Decimal | None
    total_insured_value_b: Decimal | None
    tiv_change: Decimal | None
    tiv_change_pct: float | None

    # Policy comparisons
    policy_comparisons: list[PolicyComparisonResult]
    policies_added: list[PolicySummary]
    policies_removed: list[PolicySummary]

    # LLM Analysis
    executive_summary: str | None
    key_changes: list[str]
    coverage_gaps_identified: list[str]
    recommendations: list[str]

    # Metadata
    model_used: str | None
    latency_ms: int


# LLM Prompts
POLICY_COMPARISON_SYSTEM_PROMPT = """You are an expert insurance analyst specializing in policy comparison and coverage analysis.

Analyze the comparison data between two insurance policies and provide insights. Focus on:
1. Significant changes in coverage limits and deductibles
2. Risk implications of any changes
3. Recommendations for addressing gaps or leveraging improvements

Respond in JSON format:
{
    "executive_summary": "2-3 sentence summary of the comparison highlighting the most important changes",
    "key_changes": [
        "Specific change 1 with numbers",
        "Specific change 2 with numbers"
    ],
    "risk_implications": [
        "Risk implication 1",
        "Risk implication 2"
    ],
    "recommendations": [
        "Actionable recommendation 1",
        "Actionable recommendation 2"
    ]
}"""

POLICY_COMPARISON_USER_PROMPT = """Compare these two {policy_type} policies:

POLICY A (Base/Previous):
{policy_a_context}

POLICY B (Compare/Current):
{policy_b_context}

COVERAGE CHANGES:
{coverage_changes}

Premium Change: {premium_change}

Provide analysis of this comparison."""


PROGRAM_COMPARISON_SYSTEM_PROMPT = """You are an expert insurance analyst specializing in year-over-year insurance program analysis.

Analyze the comparison data between two insurance program years and provide insights. Focus on:
1. Overall cost changes and value proposition
2. Coverage evolution across all policy types
3. Gaps that may have been introduced or resolved
4. Strategic recommendations for the upcoming renewal

Respond in JSON format:
{
    "executive_summary": "3-4 sentence executive summary for property managers/owners",
    "key_changes": [
        "Specific program-level change 1",
        "Specific program-level change 2"
    ],
    "coverage_gaps_identified": [
        "Gap 1 description",
        "Gap 2 description"
    ],
    "recommendations": [
        "Strategic recommendation 1",
        "Strategic recommendation 2"
    ]
}"""


class PolicyComparisonService:
    """Service for comparing policies and programs."""

    def __init__(self, session: AsyncSession, api_key: str | None = None):
        """Initialize policy comparison service.

        Args:
            session: Database session.
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.session = session
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL

        if not self.api_key:
            logger.warning("OpenRouter API key not configured for policy comparison")

    async def compare_policies(
        self,
        policy_a_id: str,
        policy_b_id: str,
        allow_cross_type: bool = False,
        include_llm_analysis: bool = True,
        comparison_type: str = "arbitrary",
    ) -> PolicyComparisonResult:
        """Compare two policies.

        Args:
            policy_a_id: Base policy ID.
            policy_b_id: Compare policy ID.
            allow_cross_type: Allow comparing different policy types.
            include_llm_analysis: Include LLM-generated insights.
            comparison_type: Type of comparison (yoy_renewal, arbitrary, quote_comparison).

        Returns:
            PolicyComparisonResult with comparison data.
        """
        # Load policies with coverages
        policy_a = await self._load_policy(policy_a_id)
        policy_b = await self._load_policy(policy_b_id)

        if not policy_a:
            raise PolicyComparisonError(f"Policy {policy_a_id} not found")
        if not policy_b:
            raise PolicyComparisonError(f"Policy {policy_b_id} not found")

        # Check policy types match (unless cross-type allowed)
        if not allow_cross_type and policy_a.policy_type != policy_b.policy_type:
            raise PolicyComparisonError(
                f"Policy types don't match: {policy_a.policy_type} vs {policy_b.policy_type}. "
                "Set allow_cross_type=True to compare different types."
            )

        # Build policy summaries
        summary_a = self._build_policy_summary(policy_a)
        summary_b = self._build_policy_summary(policy_b)

        # Compare premiums
        premium_change, premium_change_pct = self._compare_premiums(
            policy_a.premium, policy_b.premium
        )

        # Compare coverages
        coverages_added, coverages_removed, coverages_changed, coverages_unchanged = (
            self._compare_coverages(policy_a.coverages, policy_b.coverages)
        )

        # Calculate limit/deductible changes
        total_limit_change, total_limit_change_pct = self._calculate_total_limit_change(
            policy_a.coverages, policy_b.coverages
        )
        avg_deductible_change_pct = self._calculate_avg_deductible_change(
            coverages_changed
        )

        # LLM analysis
        executive_summary = None
        key_changes = []
        risk_implications = []
        recommendations = []
        latency_ms = 0

        if include_llm_analysis and self.api_key:
            start_time = time.time()
            llm_result = await self._analyze_policy_comparison(
                policy_a, policy_b, coverages_changed, premium_change, premium_change_pct
            )
            latency_ms = int((time.time() - start_time) * 1000)

            executive_summary = llm_result.get("executive_summary")
            key_changes = llm_result.get("key_changes", [])
            risk_implications = llm_result.get("risk_implications", [])
            recommendations = llm_result.get("recommendations", [])

        return PolicyComparisonResult(
            comparison_id=str(uuid4()),
            comparison_type=comparison_type,
            comparison_date=datetime.now(timezone.utc),
            policy_a=summary_a,
            policy_b=summary_b,
            premium_change=premium_change,
            premium_change_pct=premium_change_pct,
            coverages_added=coverages_added,
            coverages_removed=coverages_removed,
            coverages_changed=coverages_changed,
            coverages_unchanged=coverages_unchanged,
            total_limit_change=total_limit_change,
            total_limit_change_pct=total_limit_change_pct,
            avg_deductible_change_pct=avg_deductible_change_pct,
            executive_summary=executive_summary,
            key_changes=key_changes,
            risk_implications=risk_implications,
            recommendations=recommendations,
            model_used=self.model if include_llm_analysis else None,
            latency_ms=latency_ms,
        )

    async def compare_programs(
        self,
        property_id: str,
        program_a_year: int | None = None,
        program_b_year: int | None = None,
        include_policy_details: bool = True,
        include_llm_analysis: bool = True,
    ) -> ProgramComparisonResult:
        """Compare two insurance programs (year-over-year).

        Args:
            property_id: Property ID.
            program_a_year: Base year (defaults to previous year).
            program_b_year: Compare year (defaults to current year).
            include_policy_details: Include individual policy comparisons.
            include_llm_analysis: Include LLM-generated insights.

        Returns:
            ProgramComparisonResult with comparison data.
        """
        # Load property with programs
        prop = await self._load_property_with_programs(property_id)
        if not prop:
            raise PolicyComparisonError(f"Property {property_id} not found")

        # Determine years
        current_year = date.today().year
        if program_b_year is None:
            program_b_year = current_year
        if program_a_year is None:
            program_a_year = program_b_year - 1

        # Find programs
        program_a = next(
            (p for p in prop.insurance_programs if p.program_year == program_a_year),
            None,
        )
        program_b = next(
            (p for p in prop.insurance_programs if p.program_year == program_b_year),
            None,
        )

        if not program_a:
            raise PolicyComparisonError(
                f"No program found for year {program_a_year} on property {property_id}"
            )
        if not program_b:
            raise PolicyComparisonError(
                f"No program found for year {program_b_year} on property {property_id}"
            )

        # Compare aggregate values
        premium_change, premium_change_pct = self._compare_premiums(
            program_a.total_premium, program_b.total_premium
        )
        tiv_change, tiv_change_pct = self._compare_premiums(
            program_a.total_insured_value, program_b.total_insured_value
        )

        # Match and compare policies
        policy_comparisons = []
        policies_added = []
        policies_removed = []

        if include_policy_details:
            policy_comparisons, policies_added, policies_removed = (
                await self._compare_program_policies(
                    program_a, program_b, include_llm_analysis
                )
            )

        # LLM analysis
        executive_summary = None
        key_changes = []
        coverage_gaps = []
        recommendations = []
        latency_ms = 0

        if include_llm_analysis and self.api_key:
            start_time = time.time()
            llm_result = await self._analyze_program_comparison(
                prop,
                program_a,
                program_b,
                premium_change,
                premium_change_pct,
                policy_comparisons,
                policies_added,
                policies_removed,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            executive_summary = llm_result.get("executive_summary")
            key_changes = llm_result.get("key_changes", [])
            coverage_gaps = llm_result.get("coverage_gaps_identified", [])
            recommendations = llm_result.get("recommendations", [])

        return ProgramComparisonResult(
            comparison_id=str(uuid4()),
            property_id=property_id,
            property_name=prop.name,
            comparison_date=datetime.now(timezone.utc),
            program_a_year=program_a_year,
            program_b_year=program_b_year,
            program_a_id=program_a.id,
            program_b_id=program_b.id,
            total_premium_a=program_a.total_premium,
            total_premium_b=program_b.total_premium,
            premium_change=premium_change,
            premium_change_pct=premium_change_pct,
            total_insured_value_a=program_a.total_insured_value,
            total_insured_value_b=program_b.total_insured_value,
            tiv_change=tiv_change,
            tiv_change_pct=tiv_change_pct,
            policy_comparisons=policy_comparisons,
            policies_added=policies_added,
            policies_removed=policies_removed,
            executive_summary=executive_summary,
            key_changes=key_changes,
            coverage_gaps_identified=coverage_gaps,
            recommendations=recommendations,
            model_used=self.model if include_llm_analysis else None,
            latency_ms=latency_ms,
        )

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _load_policy(self, policy_id: str) -> Policy | None:
        """Load a policy with coverages."""
        stmt = (
            select(Policy)
            .options(selectinload(Policy.coverages))
            .where(
                Policy.id == policy_id,
                Policy.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_property_with_programs(self, property_id: str) -> Property | None:
        """Load property with all programs and policies."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                ).selectinload(Policy.coverages),
            )
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _build_policy_summary(self, policy: Policy) -> PolicySummary:
        """Build policy summary from policy model."""
        total_limit = sum(
            c.limit_amount or Decimal("0") for c in policy.coverages
        )

        return PolicySummary(
            id=policy.id,
            policy_number=policy.policy_number,
            policy_type=policy.policy_type,
            carrier_name=policy.carrier_name,
            effective_date=policy.effective_date,
            expiration_date=policy.expiration_date,
            premium=policy.premium,
            total_limit=total_limit,
            coverage_count=len(policy.coverages),
        )

    def _compare_premiums(
        self,
        premium_a: Decimal | None,
        premium_b: Decimal | None,
    ) -> tuple[Decimal | None, float | None]:
        """Compare two premium values."""
        if premium_a is None or premium_b is None:
            return None, None

        change = premium_b - premium_a
        change_pct = float((change / premium_a) * 100) if premium_a > 0 else None

        return change, change_pct

    def _compare_coverages(
        self,
        coverages_a: list[Coverage],
        coverages_b: list[Coverage],
    ) -> tuple[list[str], list[str], list[CoverageComparison], list[str]]:
        """Compare coverages between two policies.

        Returns:
            Tuple of (added, removed, changed, unchanged).
        """
        # Build coverage maps by name
        map_a = {c.coverage_name: c for c in coverages_a if c.coverage_name}
        map_b = {c.coverage_name: c for c in coverages_b if c.coverage_name}

        names_a = set(map_a.keys())
        names_b = set(map_b.keys())

        added = list(names_b - names_a)
        removed = list(names_a - names_b)
        common = names_a & names_b

        changed = []
        unchanged = []

        for name in common:
            cov_a = map_a[name]
            cov_b = map_b[name]

            # Check for changes
            limit_changed = cov_a.limit_amount != cov_b.limit_amount
            ded_changed = cov_a.deductible_amount != cov_b.deductible_amount
            sublimit_changed = cov_a.sublimit != cov_b.sublimit

            if limit_changed or ded_changed or sublimit_changed:
                # Calculate changes
                limit_change = None
                limit_change_pct = None
                if cov_a.limit_amount and cov_b.limit_amount:
                    limit_change = cov_b.limit_amount - cov_a.limit_amount
                    if cov_a.limit_amount > 0:
                        limit_change_pct = float(
                            (limit_change / cov_a.limit_amount) * 100
                        )

                ded_change = None
                ded_change_pct = None
                if cov_a.deductible_amount and cov_b.deductible_amount:
                    ded_change = cov_b.deductible_amount - cov_a.deductible_amount
                    if cov_a.deductible_amount > 0:
                        ded_change_pct = float(
                            (ded_change / cov_a.deductible_amount) * 100
                        )

                changed.append(CoverageComparison(
                    coverage_name=name,
                    status="changed",
                    policy_a_limit=cov_a.limit_amount,
                    policy_a_deductible=cov_a.deductible_amount,
                    policy_a_sublimit=cov_a.sublimit,
                    policy_b_limit=cov_b.limit_amount,
                    policy_b_deductible=cov_b.deductible_amount,
                    policy_b_sublimit=cov_b.sublimit,
                    limit_change=limit_change,
                    limit_change_pct=limit_change_pct,
                    deductible_change=ded_change,
                    deductible_change_pct=ded_change_pct,
                ))
            else:
                unchanged.append(name)

        return added, removed, changed, unchanged

    def _calculate_total_limit_change(
        self,
        coverages_a: list[Coverage],
        coverages_b: list[Coverage],
    ) -> tuple[Decimal | None, float | None]:
        """Calculate total limit change."""
        total_a = sum(c.limit_amount or Decimal("0") for c in coverages_a)
        total_b = sum(c.limit_amount or Decimal("0") for c in coverages_b)

        if total_a == 0 and total_b == 0:
            return None, None

        change = total_b - total_a
        change_pct = float((change / total_a) * 100) if total_a > 0 else None

        return change, change_pct

    def _calculate_avg_deductible_change(
        self,
        changed_coverages: list[CoverageComparison],
    ) -> float | None:
        """Calculate average deductible change percentage."""
        pcts = [
            c.deductible_change_pct
            for c in changed_coverages
            if c.deductible_change_pct is not None
        ]

        if not pcts:
            return None

        return sum(pcts) / len(pcts)

    async def _compare_program_policies(
        self,
        program_a: InsuranceProgram,
        program_b: InsuranceProgram,
        include_llm: bool,
    ) -> tuple[list[PolicyComparisonResult], list[PolicySummary], list[PolicySummary]]:
        """Compare policies between two programs.

        Matches policies by type and compares them.
        """
        # Group policies by type
        policies_a_by_type = {}
        for p in program_a.policies:
            policies_a_by_type.setdefault(p.policy_type, []).append(p)

        policies_b_by_type = {}
        for p in program_b.policies:
            policies_b_by_type.setdefault(p.policy_type, []).append(p)

        types_a = set(policies_a_by_type.keys())
        types_b = set(policies_b_by_type.keys())

        comparisons = []
        added = []
        removed = []

        # Types only in B = added
        for policy_type in types_b - types_a:
            for policy in policies_b_by_type[policy_type]:
                added.append(self._build_policy_summary(policy))

        # Types only in A = removed
        for policy_type in types_a - types_b:
            for policy in policies_a_by_type[policy_type]:
                removed.append(self._build_policy_summary(policy))

        # Common types = compare
        for policy_type in types_a & types_b:
            policies_a = policies_a_by_type[policy_type]
            policies_b = policies_b_by_type[policy_type]

            # Simple matching: compare first policy of each type
            # (More sophisticated matching could use policy numbers)
            policy_a = policies_a[0]
            policy_b = policies_b[0]

            comparison = await self.compare_policies(
                policy_a.id,
                policy_b.id,
                allow_cross_type=True,  # Already matched by type
                include_llm_analysis=include_llm,
                comparison_type="yoy_renewal",
            )
            comparisons.append(comparison)

            # Handle multiple policies of same type
            if len(policies_b) > len(policies_a):
                for policy in policies_b[len(policies_a):]:
                    added.append(self._build_policy_summary(policy))
            elif len(policies_a) > len(policies_b):
                for policy in policies_a[len(policies_b):]:
                    removed.append(self._build_policy_summary(policy))

        return comparisons, added, removed

    async def _analyze_policy_comparison(
        self,
        policy_a: Policy,
        policy_b: Policy,
        coverages_changed: list[CoverageComparison],
        premium_change: Decimal | None,
        premium_change_pct: float | None,
    ) -> dict:
        """Generate LLM analysis of policy comparison."""
        # Build context
        policy_a_context = self._build_policy_context(policy_a)
        policy_b_context = self._build_policy_context(policy_b)

        coverage_changes = self._build_coverage_changes_context(coverages_changed)

        premium_str = "No change"
        if premium_change is not None:
            sign = "+" if premium_change > 0 else ""
            premium_str = f"{sign}${float(premium_change):,.0f} ({premium_change_pct:+.1f}%)"

        user_prompt = POLICY_COMPARISON_USER_PROMPT.format(
            policy_type=policy_a.policy_type,
            policy_a_context=policy_a_context,
            policy_b_context=policy_b_context,
            coverage_changes=coverage_changes,
            premium_change=premium_str,
        )

        response = await self._call_llm(POLICY_COMPARISON_SYSTEM_PROMPT, user_prompt)
        return self._parse_llm_response(response)

    async def _analyze_program_comparison(
        self,
        prop: Property,
        program_a: InsuranceProgram,
        program_b: InsuranceProgram,
        premium_change: Decimal | None,
        premium_change_pct: float | None,
        policy_comparisons: list[PolicyComparisonResult],
        policies_added: list[PolicySummary],
        policies_removed: list[PolicySummary],
    ) -> dict:
        """Generate LLM analysis of program comparison."""
        context = f"""
PROPERTY: {prop.name}
Type: {prop.property_type or 'N/A'}
Location: {prop.city or ''}, {prop.state or ''}

PROGRAM {program_a.program_year} (Previous):
- Total Premium: ${float(program_a.total_premium or 0):,.0f}
- Total Insured Value: ${float(program_a.total_insured_value or 0):,.0f}
- Policies: {len(program_a.policies)}

PROGRAM {program_b.program_year} (Current):
- Total Premium: ${float(program_b.total_premium or 0):,.0f}
- Total Insured Value: ${float(program_b.total_insured_value or 0):,.0f}
- Policies: {len(program_b.policies)}

PREMIUM CHANGE: {f'+${float(premium_change):,.0f} ({premium_change_pct:+.1f}%)' if premium_change else 'N/A'}

POLICIES ADDED: {', '.join(p.policy_type for p in policies_added) or 'None'}
POLICIES REMOVED: {', '.join(p.policy_type for p in policies_removed) or 'None'}

KEY POLICY CHANGES:
"""
        for comp in policy_comparisons:
            context += f"\n{comp.policy_a.policy_type}:"
            if comp.premium_change:
                context += f" Premium {comp.premium_change_pct:+.1f}%"
            context += f" | Coverages: +{len(comp.coverages_added)}, -{len(comp.coverages_removed)}, ~{len(comp.coverages_changed)}"

        response = await self._call_llm(PROGRAM_COMPARISON_SYSTEM_PROMPT, context)
        return self._parse_llm_response(response)

    def _build_policy_context(self, policy: Policy) -> str:
        """Build policy context string."""
        lines = [
            f"Policy Number: {policy.policy_number or 'N/A'}",
            f"Carrier: {policy.carrier_name or 'Unknown'}",
            f"Period: {policy.effective_date or 'N/A'} to {policy.expiration_date or 'N/A'}",
            f"Premium: ${float(policy.premium or 0):,.0f}",
            "",
            "Coverages:",
        ]

        for cov in policy.coverages[:15]:
            limit = f"${float(cov.limit_amount or 0):,.0f}" if cov.limit_amount else "N/A"
            ded = f"${float(cov.deductible_amount or 0):,.0f}" if cov.deductible_amount else "N/A"
            lines.append(f"  - {cov.coverage_name or 'Coverage'}: Limit {limit}, Deductible {ded}")

        return "\n".join(lines)

    def _build_coverage_changes_context(
        self, changes: list[CoverageComparison]
    ) -> str:
        """Build coverage changes context."""
        if not changes:
            return "No coverage changes."

        lines = []
        for change in changes:
            line = f"- {change.coverage_name}:"
            if change.limit_change_pct is not None:
                line += f" Limit {change.limit_change_pct:+.1f}%"
            if change.deductible_change_pct is not None:
                line += f" Deductible {change.deductible_change_pct:+.1f}%"
            lines.append(line)

        return "\n".join(lines)

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call the LLM API."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Policy Comparison",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3,
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenRouter API error: {response.status_code} - {error_detail}")
                raise PolicyComparisonAPIError(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                raise PolicyComparisonError("No response from LLM")

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
                "executive_summary": response[:500] if response else "",
                "key_changes": [],
                "risk_implications": [],
                "recommendations": [],
            }


def get_policy_comparison_service(session: AsyncSession) -> PolicyComparisonService:
    """Factory function to create PolicyComparisonService.

    Args:
        session: Database session.

    Returns:
        PolicyComparisonService instance.
    """
    return PolicyComparisonService(session)
