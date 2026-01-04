"""Coverage Conflict Detection Service with LLM-Powered Analysis.

Detects conflicts, overlaps, and gaps between policies using LLM as the primary
detection method for all 6 conflict types:
1. Excess/Primary Gap - Umbrella doesn't attach to underlying coverage
2. Entity Name Mismatch - Different named insureds across policies
3. Valuation Method Conflict - Mixed RCV/ACV valuation methods
4. Coverage Overlap - Duplicate coverage (wasting premium)
5. Limit Tower Gap - Coverage limits don't stack properly
6. Exclusion Conflict - One policy covers what another excludes
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.coverage_conflict import CoverageConflict
from app.models.insurance_program import InsuranceProgram
from app.models.policy import Policy
from app.models.property import Property
from app.repositories.conflict_repository import ConflictRepository

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


class ConflictDetectionError(Exception):
    """Base exception for conflict detection errors."""
    pass


@dataclass
class ConflictResult:
    """Result of a single conflict detection."""
    conflict_type: str
    severity: str
    title: str
    description: str
    affected_policies: list[str]
    gap_amount: float | None = None
    potential_savings: float | None = None
    recommendation: str | None = None
    reasoning: str | None = None


@dataclass
class ConflictDetectionResult:
    """Result of conflict detection for a property."""
    property_id: str
    property_name: str
    conflicts: list[CoverageConflict]
    summary: dict[str, int]
    cross_policy_analysis: str | None
    portfolio_recommendations: list[str]
    detection_timestamp: datetime
    model_used: str
    latency_ms: int


# LLM Prompt for conflict detection
CONFLICT_DETECTION_PROMPT = """You are an expert insurance analyst specializing in coverage conflicts. Analyze these policies for a single property and identify ALL conflicts, overlaps, and gaps.

PROPERTY:
{property_context}

POLICIES:
{policies_context}

NAMED INSUREDS:
{insureds_context}

COVERAGE DETAILS:
{coverages_context}

Analyze for these 6 conflict types:

1. EXCESS/PRIMARY GAP: Does umbrella/excess policy properly attach to underlying policies? Check if umbrella underlying requirements match actual primary policy limits.

2. ENTITY MISMATCH: Are named insureds consistent across all policies? Check for different entity names, missing entities, or typos that could cause claim denials.

3. VALUATION CONFLICT: Are valuation methods (Replacement Cost Value vs Actual Cash Value) consistent across buildings and policies? Mixed valuations can cause claim issues.

4. COVERAGE OVERLAP: Is any coverage duplicated across multiple policies? This wastes premium dollars. Look for equipment breakdown, business income, or other coverages on multiple policies.

5. LIMIT TOWER GAP: Do coverage limits stack properly without gaps? Check if excess layers attach at the right points and if there are any uninsured gaps in the coverage tower.

6. EXCLUSION CONFLICT: Does any policy exclude coverage that another policy provides? This can create confusion at claim time about which policy responds.

For EACH conflict found, provide detailed analysis:
{{
    "conflicts": [
        {{
            "conflict_type": "excess_primary_gap|entity_mismatch|valuation_conflict|coverage_overlap|limit_tower_gap|exclusion_conflict",
            "severity": "critical|warning|info",
            "title": "Brief descriptive title",
            "description": "Detailed explanation of the conflict and its implications",
            "affected_policies": ["policy_number_1", "policy_number_2"],
            "gap_amount": <number or null - financial gap amount if applicable>,
            "potential_savings": <number or null - potential premium savings if overlap>,
            "recommendation": "Specific action to resolve this conflict",
            "reasoning": "How you detected this conflict and why it matters"
        }}
    ],
    "summary": {{
        "total_conflicts": <count>,
        "critical": <count>,
        "warning": <count>,
        "info": <count>
    }},
    "cross_policy_analysis": "Overall assessment of how these policies work together as a program",
    "portfolio_recommendations": ["Strategic recommendation 1", "Strategic recommendation 2"]
}}

If no conflicts are found, return an empty conflicts array with an explanation in cross_policy_analysis.

Severity Guidelines:
- CRITICAL: Could result in claim denial or significant uninsured loss
- WARNING: May cause issues or inefficiencies that should be addressed
- INFO: Minor issues or opportunities for optimization

Be specific and reference actual policy numbers and amounts where possible."""


class ConflictDetectionService:
    """Service for LLM-powered conflict detection."""

    CONFLICT_TYPES = [
        "excess_primary_gap",
        "entity_mismatch",
        "valuation_conflict",
        "coverage_overlap",
        "limit_tower_gap",
        "exclusion_conflict",
    ]

    def __init__(self, session: AsyncSession, api_key: str | None = None):
        """Initialize conflict detection service.

        Args:
            session: Database session.
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.session = session
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL
        self.conflict_repo = ConflictRepository(session)

    async def detect_conflicts(
        self,
        property_id: str,
        clear_existing: bool = True,
    ) -> ConflictDetectionResult:
        """Detect all conflicts for a property using LLM.

        Args:
            property_id: Property ID.
            clear_existing: Whether to clear existing open conflicts first.

        Returns:
            ConflictDetectionResult with all detected conflicts.
        """
        if not self.api_key:
            raise ConflictDetectionError("OpenRouter API key not configured")

        # Load property with all policy context
        prop = await self._load_property_with_policies(property_id)
        if not prop:
            raise ConflictDetectionError(f"Property {property_id} not found")

        # Check if we have any policies to analyze
        policies = self._get_active_policies(prop)
        if not policies:
            logger.info(f"No active policies for property {property_id}")
            return ConflictDetectionResult(
                property_id=property_id,
                property_name=prop.name,
                conflicts=[],
                summary={"total_conflicts": 0, "critical": 0, "warning": 0, "info": 0},
                cross_policy_analysis="No active policies found for conflict analysis.",
                portfolio_recommendations=[],
                detection_timestamp=datetime.now(timezone.utc),
                model_used=self.model,
                latency_ms=0,
            )

        # Need at least 2 policies for conflict detection
        if len(policies) < 2:
            return ConflictDetectionResult(
                property_id=property_id,
                property_name=prop.name,
                conflicts=[],
                summary={"total_conflicts": 0, "critical": 0, "warning": 0, "info": 0},
                cross_policy_analysis="Only one active policy found. Conflict detection requires multiple policies to analyze cross-policy issues.",
                portfolio_recommendations=["Consider adding additional coverage types for comprehensive protection."],
                detection_timestamp=datetime.now(timezone.utc),
                model_used=self.model,
                latency_ms=0,
            )

        # Clear existing open conflicts if requested
        if clear_existing:
            await self.conflict_repo.clear_open_conflicts(property_id)

        # Build context for LLM
        property_context = self._build_property_context(prop)
        policies_context = self._build_policies_context(policies)
        insureds_context = self._build_insureds_context(policies)
        coverages_context = self._build_coverages_context(policies)

        # Format prompt
        prompt = CONFLICT_DETECTION_PROMPT.format(
            property_context=property_context,
            policies_context=policies_context,
            insureds_context=insureds_context,
            coverages_context=coverages_context,
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

        # Create conflict records
        conflicts = []
        for conflict_data in result.get("conflicts", []):
            conflict = await self.conflict_repo.create_conflict(
                property_id=property_id,
                conflict_type=conflict_data.get("conflict_type", "unknown"),
                severity=conflict_data.get("severity", "info"),
                title=conflict_data.get("title", "Unnamed conflict"),
                description=conflict_data.get("description"),
                affected_policy_ids=self._resolve_policy_ids(
                    conflict_data.get("affected_policies", []),
                    policies,
                ),
                gap_amount=conflict_data.get("gap_amount"),
                potential_savings=conflict_data.get("potential_savings"),
                recommendation=conflict_data.get("recommendation"),
                detection_method="llm",
                llm_reasoning=conflict_data.get("reasoning"),
                llm_analysis=conflict_data,
                llm_model_used=self.model,
            )
            conflicts.append(conflict)

        # Build summary
        summary = result.get("summary", {
            "total_conflicts": len(conflicts),
            "critical": sum(1 for c in conflicts if c.severity == "critical"),
            "warning": sum(1 for c in conflicts if c.severity == "warning"),
            "info": sum(1 for c in conflicts if c.severity == "info"),
        })

        logger.info(
            f"Detected {len(conflicts)} conflicts for property {property_id}: "
            f"{summary.get('critical', 0)} critical, {summary.get('warning', 0)} warning, {summary.get('info', 0)} info"
        )

        return ConflictDetectionResult(
            property_id=property_id,
            property_name=prop.name,
            conflicts=conflicts,
            summary=summary,
            cross_policy_analysis=result.get("cross_policy_analysis"),
            portfolio_recommendations=result.get("portfolio_recommendations", []),
            detection_timestamp=datetime.now(timezone.utc),
            model_used=self.model,
            latency_ms=latency_ms,
        )

    async def get_property_conflicts(
        self,
        property_id: str,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[CoverageConflict]:
        """Get existing conflicts for a property.

        Args:
            property_id: Property ID.
            status: Optional status filter.
            severity: Optional severity filter.

        Returns:
            List of CoverageConflict records.
        """
        return await self.conflict_repo.get_by_property(
            property_id,
            status=status,
            severity=severity,
        )

    async def _load_property_with_policies(self, property_id: str) -> Property | None:
        """Load property with full policy context."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                ).selectinload(Policy.coverages),
                selectinload(Property.buildings),
            )
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _get_active_policies(self, prop: Property) -> list[Policy]:
        """Get all active policies for a property."""
        policies = []
        for program in prop.insurance_programs:
            if program.status == "active":
                policies.extend(program.policies)
        return policies

    def _build_property_context(self, prop: Property) -> str:
        """Build property context string for LLM."""
        lines = [
            f"Name: {prop.name}",
            f"Type: {prop.property_type or 'N/A'}",
            f"Address: {prop.address}, {prop.city}, {prop.state}",
            f"Flood Zone: {prop.flood_zone or 'N/A'}",
        ]

        if prop.buildings:
            total_value = sum(b.building_value or 0 for b in prop.buildings)
            lines.append(f"Total Building Value: ${total_value:,.2f}")
            lines.append(f"Number of Buildings: {len(prop.buildings)}")

            for i, b in enumerate(prop.buildings, 1):
                val_method = getattr(b, 'valuation_type', None) or "Not specified"
                lines.append(f"  Building {i}: {b.building_name or 'Unnamed'} - Value: ${b.building_value or 0:,.2f}, Valuation: {val_method}")

        return "\n".join(lines)

    def _build_policies_context(self, policies: list[Policy]) -> str:
        """Build policies context string for LLM."""
        lines = []
        for policy in policies:
            exp_date = policy.expiration_date.strftime("%Y-%m-%d") if policy.expiration_date else "N/A"
            lines.append(f"\nPolicy: {policy.policy_number or 'Unknown'}")
            lines.append(f"  Type: {policy.policy_type}")
            lines.append(f"  Carrier: {policy.carrier_name or 'Unknown'}")
            lines.append(f"  Expiration: {exp_date}")
            lines.append(f"  Premium: ${policy.premium:,.2f}" if policy.premium else "  Premium: N/A")

            # Add any umbrella/excess specific info
            if policy.policy_type in ("umbrella", "excess"):
                # Look for underlying requirements if stored
                lines.append("  Layer Type: Excess/Umbrella")

        return "\n".join(lines) if lines else "No policies available"

    def _build_insureds_context(self, policies: list[Policy]) -> str:
        """Build named insureds context for entity mismatch detection."""
        insureds = {}
        for policy in policies:
            # Get named insured from policy if available
            insured_name = None
            if policy.named_insured:
                insured_name = policy.named_insured.name if hasattr(policy.named_insured, 'name') else str(policy.named_insured)

            if insured_name:
                if insured_name not in insureds:
                    insureds[insured_name] = []
                insureds[insured_name].append(policy.policy_number or policy.policy_type)

        if not insureds:
            return "Named insured information not available in policy data"

        lines = []
        for name, policy_nums in insureds.items():
            lines.append(f"'{name}' appears on: {', '.join(policy_nums)}")

        return "\n".join(lines)

    def _build_coverages_context(self, policies: list[Policy]) -> str:
        """Build coverages context for overlap and gap detection."""
        lines = []
        coverage_map: dict[str, list[tuple[str, Any]]] = {}

        for policy in policies:
            policy_ref = policy.policy_number or policy.policy_type
            lines.append(f"\n{policy_ref} ({policy.policy_type}):")

            if policy.coverages:
                for cov in policy.coverages:
                    limit = f"${cov.limit_amount:,.2f}" if cov.limit_amount else "N/A"
                    ded = f"${cov.deductible_amount:,.2f}" if cov.deductible_amount else "N/A"
                    ded_pct = f"{cov.deductible_pct * 100:.1f}%" if cov.deductible_pct else ""
                    valuation = cov.valuation_type or "Not specified"

                    lines.append(f"  - {cov.coverage_name or 'Coverage'}: Limit {limit}, Deductible {ded} {ded_pct}, Valuation: {valuation}")

                    # Track for overlap detection
                    cov_key = (cov.coverage_name or "").lower()
                    if cov_key:
                        if cov_key not in coverage_map:
                            coverage_map[cov_key] = []
                        coverage_map[cov_key].append((policy_ref, cov.limit_amount))
            else:
                lines.append("  No coverage details available")

        # Add summary of potential overlaps
        overlaps = [(k, v) for k, v in coverage_map.items() if len(v) > 1]
        if overlaps:
            lines.append("\n\nCoverages appearing on multiple policies (potential overlaps):")
            for cov_name, policies_with_cov in overlaps:
                lines.append(f"  {cov_name}: {len(policies_with_cov)} policies")

        return "\n".join(lines)

    def _resolve_policy_ids(
        self,
        policy_refs: list[str],
        policies: list[Policy],
    ) -> list[str]:
        """Resolve policy references to policy IDs.

        Args:
            policy_refs: List of policy numbers or types from LLM.
            policies: List of actual policies.

        Returns:
            List of resolved policy IDs.
        """
        resolved = []
        for ref in policy_refs:
            ref_lower = ref.lower()
            for policy in policies:
                if (policy.policy_number and ref_lower in policy.policy_number.lower()) or \
                   (policy.policy_type and ref_lower in policy.policy_type.lower()):
                    resolved.append(policy.id)
                    break
        return resolved

    async def _call_llm(self, user_message: str) -> str:
        """Call the LLM API."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Conflict Detection",
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
                raise ConflictDetectionError(f"LLM API error: {response.status_code}")

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                raise ConflictDetectionError("No response from LLM")

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
            "conflicts": [],
            "summary": {"total_conflicts": 0, "critical": 0, "warning": 0, "info": 0},
            "cross_policy_analysis": "Unable to complete conflict analysis.",
            "portfolio_recommendations": [],
        }


def get_conflict_detection_service(session: AsyncSession) -> ConflictDetectionService:
    """Factory function to create ConflictDetectionService.

    Args:
        session: Database session.

    Returns:
        ConflictDetectionService instance.
    """
    return ConflictDetectionService(session)
