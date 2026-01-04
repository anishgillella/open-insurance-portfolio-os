"""LLM-Enhanced Gap Analysis Service.

This service provides AI-powered analysis on top of rule-based gap detection:
1. Enhanced recommendations for addressing gaps
2. Risk assessment and prioritization
3. Cross-policy conflict detection
4. Portfolio-level pattern analysis
5. Natural language explanations

Uses Gemini 2.5 Flash via OpenRouter for LLM calls.
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.coverage import Coverage
from app.models.coverage_gap import CoverageGap
from app.models.insurance_program import InsuranceProgram
from app.models.policy import Policy
from app.models.property import Property

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


class GapAnalysisError(Exception):
    """Base exception for gap analysis errors."""
    pass


class GapAnalysisAPIError(GapAnalysisError):
    """Raised when LLM API returns an error."""
    pass


@dataclass
class GapAnalysisResult:
    """Result of LLM-enhanced gap analysis."""

    gap_id: str
    enhanced_description: str
    risk_assessment: str
    risk_score: int  # 1-10
    recommendations: list[str]
    potential_consequences: list[str]
    industry_context: str
    action_priority: str  # immediate, short_term, medium_term
    estimated_impact: str
    related_gaps: list[str]  # IDs of related gaps
    analysis_timestamp: datetime
    model_used: str
    latency_ms: int


@dataclass
class PropertyAnalysisResult:
    """Result of property-level gap analysis."""

    property_id: str
    property_name: str
    overall_risk_score: int  # 1-10
    risk_grade: str  # A, B, C, D, F
    executive_summary: str
    gap_analyses: list[GapAnalysisResult]
    cross_policy_conflicts: list[dict]
    coverage_recommendations: list[str]
    priority_actions: list[dict]
    portfolio_insights: list[str]
    analysis_timestamp: datetime
    model_used: str
    total_latency_ms: int


# System prompts for different analysis types
SINGLE_GAP_ANALYSIS_PROMPT = """You are an expert commercial real estate insurance analyst. Analyze the following coverage gap and provide detailed, actionable insights.

IMPORTANT: Your analysis should be:
1. Specific to the property type and coverage details provided
2. Based on industry best practices and standards
3. Actionable with clear next steps
4. Quantified where possible (risk scores, estimated costs, timelines)

Respond in JSON format with these fields:
{
    "enhanced_description": "A clear, detailed explanation of what this gap means for the property owner",
    "risk_assessment": "Analysis of the financial and operational risks this gap creates",
    "risk_score": <1-10 integer, 10 being most critical>,
    "recommendations": ["Specific action 1", "Specific action 2", ...],
    "potential_consequences": ["What could happen if not addressed", ...],
    "industry_context": "How this compares to industry standards and what similar properties typically have",
    "action_priority": "immediate|short_term|medium_term",
    "estimated_impact": "Estimated financial impact or exposure amount"
}"""


PROPERTY_ANALYSIS_PROMPT = """You are an expert commercial real estate insurance analyst. Analyze all the coverage gaps for this property and provide a comprehensive assessment.

IMPORTANT: Your analysis should:
1. Look for patterns and relationships between gaps
2. Identify any coverage conflicts or overlaps
3. Prioritize issues by urgency and impact
4. Provide an overall risk assessment
5. Give actionable recommendations

Respond in JSON format with these fields:
{
    "overall_risk_score": <1-10 integer>,
    "risk_grade": "A|B|C|D|F",
    "executive_summary": "2-3 sentence summary for executives",
    "cross_policy_conflicts": [{"conflict_type": "...", "description": "...", "policies_involved": [...], "severity": "..."}],
    "coverage_recommendations": ["Recommendation 1", "Recommendation 2", ...],
    "priority_actions": [{"action": "...", "priority": "immediate|short_term|medium_term", "estimated_effort": "...", "expected_benefit": "..."}],
    "portfolio_insights": ["Pattern or insight 1", "Pattern or insight 2", ...]
}"""


class GapAnalysisService:
    """Service for LLM-enhanced gap analysis."""

    def __init__(self, session: AsyncSession, api_key: str | None = None):
        """Initialize gap analysis service.

        Args:
            session: Database session.
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.session = session
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL

        if not self.api_key:
            logger.warning("OpenRouter API key not configured for gap analysis")

    async def analyze_gap(self, gap_id: str) -> GapAnalysisResult:
        """Analyze a single gap with LLM enhancement.

        Args:
            gap_id: Gap ID to analyze.

        Returns:
            GapAnalysisResult with enhanced insights.
        """
        if not self.api_key:
            raise GapAnalysisError("OpenRouter API key not configured")

        # Load gap with related data
        gap = await self._load_gap_with_context(gap_id)
        if not gap:
            raise GapAnalysisError(f"Gap {gap_id} not found")

        # Build context for LLM
        context = self._build_gap_context(gap)

        # Call LLM
        start_time = time.time()
        analysis = await self._call_llm(
            SINGLE_GAP_ANALYSIS_PROMPT,
            f"Analyze this coverage gap:\n\n{context}",
        )
        latency_ms = int((time.time() - start_time) * 1000)

        # Parse response
        try:
            result = json.loads(analysis)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            result = self._extract_json_from_response(analysis)

        # Find related gaps
        related_gaps = await self._find_related_gaps(gap)

        # Build analysis result
        analysis_result = GapAnalysisResult(
            gap_id=gap_id,
            enhanced_description=result.get("enhanced_description", gap.description or ""),
            risk_assessment=result.get("risk_assessment", ""),
            risk_score=int(result.get("risk_score", 5)),
            recommendations=result.get("recommendations", []),
            potential_consequences=result.get("potential_consequences", []),
            industry_context=result.get("industry_context", ""),
            action_priority=result.get("action_priority", "medium_term"),
            estimated_impact=result.get("estimated_impact", "Unknown"),
            related_gaps=[g.id for g in related_gaps],
            analysis_timestamp=datetime.utcnow(),
            model_used=self.model,
            latency_ms=latency_ms,
        )

        # Persist analysis to database
        await self._save_analysis_to_gap(gap, analysis_result)

        return analysis_result

    async def _save_analysis_to_gap(
        self, gap: CoverageGap, analysis: GapAnalysisResult
    ) -> None:
        """Save LLM analysis results to the gap record.

        Args:
            gap: CoverageGap model instance.
            analysis: Analysis result to persist.
        """
        gap.llm_enhanced_description = analysis.enhanced_description
        gap.llm_risk_assessment = analysis.risk_assessment
        gap.llm_risk_score = analysis.risk_score
        gap.llm_recommendations = analysis.recommendations
        gap.llm_potential_consequences = analysis.potential_consequences
        gap.llm_industry_context = analysis.industry_context
        gap.llm_action_priority = analysis.action_priority
        gap.llm_estimated_impact = analysis.estimated_impact
        gap.llm_analyzed_at = analysis.analysis_timestamp
        gap.llm_model_used = analysis.model_used

        await self.session.flush()
        logger.debug(f"Saved LLM analysis to gap {gap.id}")

    async def analyze_property_gaps(self, property_id: str) -> PropertyAnalysisResult:
        """Analyze all gaps for a property with LLM enhancement.

        Args:
            property_id: Property ID to analyze.

        Returns:
            PropertyAnalysisResult with comprehensive insights.
        """
        if not self.api_key:
            raise GapAnalysisError("OpenRouter API key not configured")

        # Load property with all gaps and policies
        prop = await self._load_property_with_full_context(property_id)
        if not prop:
            raise GapAnalysisError(f"Property {property_id} not found")

        # Get all open gaps for this property
        gaps = await self._get_property_gaps(property_id)

        if not gaps:
            # No gaps - return clean analysis
            return PropertyAnalysisResult(
                property_id=property_id,
                property_name=prop.name,
                overall_risk_score=2,
                risk_grade="A",
                executive_summary="No coverage gaps detected. The property has comprehensive insurance coverage that meets industry standards.",
                gap_analyses=[],
                cross_policy_conflicts=[],
                coverage_recommendations=["Continue monitoring coverage as property values change", "Review policies annually before renewal"],
                priority_actions=[],
                portfolio_insights=["Property is well-protected with no identified coverage gaps"],
                analysis_timestamp=datetime.utcnow(),
                model_used=self.model,
                total_latency_ms=0,
            )

        # Analyze individual gaps first
        total_latency = 0
        gap_analyses = []
        for gap in gaps:
            try:
                analysis = await self.analyze_gap(gap.id)
                gap_analyses.append(analysis)
                total_latency += analysis.latency_ms
            except Exception as e:
                logger.warning(f"Failed to analyze gap {gap.id}: {e}")

        # Build comprehensive context for property-level analysis
        context = self._build_property_context(prop, gaps, gap_analyses)

        # Call LLM for property-level analysis
        start_time = time.time()
        property_analysis = await self._call_llm(
            PROPERTY_ANALYSIS_PROMPT,
            f"Analyze all coverage gaps for this property:\n\n{context}",
        )
        total_latency += int((time.time() - start_time) * 1000)

        # Parse response
        try:
            result = json.loads(property_analysis)
        except json.JSONDecodeError:
            result = self._extract_json_from_response(property_analysis)

        return PropertyAnalysisResult(
            property_id=property_id,
            property_name=prop.name,
            overall_risk_score=int(result.get("overall_risk_score", 5)),
            risk_grade=result.get("risk_grade", "C"),
            executive_summary=result.get("executive_summary", ""),
            gap_analyses=gap_analyses,
            cross_policy_conflicts=result.get("cross_policy_conflicts", []),
            coverage_recommendations=result.get("coverage_recommendations", []),
            priority_actions=result.get("priority_actions", []),
            portfolio_insights=result.get("portfolio_insights", []),
            analysis_timestamp=datetime.utcnow(),
            model_used=self.model,
            total_latency_ms=total_latency,
        )

    async def _load_gap_with_context(self, gap_id: str) -> CoverageGap | None:
        """Load a gap with all related context."""
        stmt = (
            select(CoverageGap)
            .options(
                selectinload(CoverageGap.property).selectinload(Property.buildings),
                selectinload(CoverageGap.policy).selectinload(Policy.coverages),
                selectinload(CoverageGap.program),
            )
            .where(
                CoverageGap.id == gap_id,
                CoverageGap.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_property_with_full_context(self, property_id: str) -> Property | None:
        """Load property with full insurance context."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.buildings),
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                ).selectinload(Policy.coverages),
                selectinload(Property.valuations),
            )
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_property_gaps(self, property_id: str) -> list[CoverageGap]:
        """Get all open gaps for a property."""
        stmt = (
            select(CoverageGap)
            .options(
                selectinload(CoverageGap.policy).selectinload(Policy.coverages),
            )
            .where(
                CoverageGap.property_id == property_id,
                CoverageGap.status == "open",
                CoverageGap.deleted_at.is_(None),
            )
            .order_by(CoverageGap.severity.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _find_related_gaps(self, gap: CoverageGap) -> list[CoverageGap]:
        """Find gaps related to the given gap."""
        stmt = (
            select(CoverageGap)
            .where(
                CoverageGap.property_id == gap.property_id,
                CoverageGap.id != gap.id,
                CoverageGap.status == "open",
                CoverageGap.deleted_at.is_(None),
            )
            .limit(5)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _build_gap_context(self, gap: CoverageGap) -> str:
        """Build context string for gap analysis."""
        lines = [
            f"Gap Type: {gap.gap_type}",
            f"Severity: {gap.severity}",
            f"Title: {gap.title}",
            f"Description: {gap.description or 'N/A'}",
            f"Coverage Name: {gap.coverage_name or 'N/A'}",
            f"Current Value: {gap.current_value or 'N/A'}",
            f"Recommended Value: {gap.recommended_value or 'N/A'}",
            f"Gap Amount: ${gap.gap_amount:,.2f}" if gap.gap_amount else "Gap Amount: N/A",
        ]

        if gap.property:
            lines.extend([
                "",
                "Property Information:",
                f"  Name: {gap.property.name}",
                f"  Type: {gap.property.property_type or 'N/A'}",
                f"  Address: {gap.property.address}, {gap.property.city}, {gap.property.state}",
                f"  Units: {gap.property.units or 'N/A'}",
                f"  Flood Zone: {gap.property.flood_zone or 'N/A'}",
            ])

            if gap.property.buildings:
                total_value = sum(b.building_value or 0 for b in gap.property.buildings)
                lines.append(f"  Total Building Value: ${total_value:,.2f}")

        if gap.policy:
            lines.extend([
                "",
                "Related Policy:",
                f"  Type: {gap.policy.policy_type or 'N/A'}",
                f"  Number: {gap.policy.policy_number or 'N/A'}",
                f"  Carrier: {gap.policy.carrier_name or 'N/A'}",
            ])

            if gap.policy.coverages:
                lines.append("  Coverages:")
                for cov in gap.policy.coverages[:5]:
                    limit = f"${cov.limit_amount:,.2f}" if cov.limit_amount else "N/A"
                    lines.append(f"    - {cov.coverage_name or 'Coverage'}: Limit {limit}")

        return "\n".join(lines)

    def _build_property_context(
        self,
        prop: Property,
        gaps: list[CoverageGap],
        gap_analyses: list[GapAnalysisResult],
    ) -> str:
        """Build comprehensive property context for analysis."""
        lines = [
            "PROPERTY INFORMATION:",
            f"Name: {prop.name}",
            f"Type: {prop.property_type or 'N/A'}",
            f"Address: {prop.address}, {prop.city}, {prop.state}",
            f"Units: {prop.units or 'N/A'}",
            f"Flood Zone: {prop.flood_zone or 'N/A'}",
        ]

        if prop.buildings:
            total_value = sum(b.building_value or 0 for b in prop.buildings)
            lines.append(f"Total Building Value: ${total_value:,.2f}")
            lines.append(f"Number of Buildings: {len(prop.buildings)}")

        # Add insurance program info
        lines.append("\nINSURANCE PROGRAMS:")
        for program in prop.insurance_programs:
            if program.status == "active":
                lines.append(f"  Program Year: {program.program_year}")
                lines.append(f"  Total Insured Value: ${program.total_insured_value:,.2f}" if program.total_insured_value else "  TIV: N/A")
                lines.append(f"  Policies: {len(program.policies)}")

                for policy in program.policies:
                    lines.append(f"    - {policy.policy_type}: {policy.policy_number} ({policy.carrier_name or 'Unknown carrier'})")

        # Add gap summary
        lines.append(f"\nIDENTIFIED GAPS ({len(gaps)} total):")
        for i, gap in enumerate(gaps, 1):
            lines.append(f"\n  Gap {i}:")
            lines.append(f"    Type: {gap.gap_type}")
            lines.append(f"    Severity: {gap.severity}")
            lines.append(f"    Title: {gap.title}")
            lines.append(f"    Current: {gap.current_value or 'N/A'}")
            lines.append(f"    Recommended: {gap.recommended_value or 'N/A'}")

            # Add LLM analysis if available
            matching_analysis = next((a for a in gap_analyses if a.gap_id == gap.id), None)
            if matching_analysis:
                lines.append(f"    Risk Score: {matching_analysis.risk_score}/10")
                lines.append(f"    Priority: {matching_analysis.action_priority}")

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
                    "X-Title": "Open Insurance Gap Analysis",
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
                raise GapAnalysisAPIError(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                raise GapAnalysisError("No response from LLM")

            return choices[0].get("message", {}).get("content", "")

    def _extract_json_from_response(self, response: str) -> dict:
        """Extract JSON from a response that may contain extra text."""
        # Try to find JSON in the response
        import re

        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Return default structure
        return {
            "enhanced_description": response[:500] if response else "",
            "risk_assessment": "",
            "risk_score": 5,
            "recommendations": [],
            "potential_consequences": [],
            "industry_context": "",
            "action_priority": "medium_term",
            "estimated_impact": "Unknown",
        }


def get_gap_analysis_service(session: AsyncSession) -> GapAnalysisService:
    """Factory function to create GapAnalysisService.

    Args:
        session: Database session.

    Returns:
        GapAnalysisService instance.
    """
    return GapAnalysisService(session)
