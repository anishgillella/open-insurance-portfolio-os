"""Gap Detection Service.

Automatically detects coverage gaps based on industry-standard thresholds:
1. Underinsurance - Coverage < 80-90% of building value
2. High Deductible - Deductibles > 3-5% of TIV
3. Expiration - Policies expiring within 30/60/90 days
4. Missing Coverage - Required coverages not present
5. Missing Flood - Properties in flood zones without flood insurance
6. Outdated Valuation - Property valuations > 2-3 years old
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.core.gap_thresholds import (
    COVERAGE_REQUIREMENTS,
    DEDUCTIBLE,
    EXPIRATION,
    UNDERINSURANCE,
    VALUATION,
    GapType,
    Severity,
)
from app.models.coverage import Coverage
from app.models.coverage_gap import CoverageGap
from app.models.insurance_program import InsuranceProgram
from app.models.policy import Policy
from app.models.property import Property
from app.models.valuation import Valuation
from app.repositories.gap_repository import GapRepository

logger = logging.getLogger(__name__)


class GapDetectionService:
    """Service for detecting coverage gaps."""

    def __init__(self, session: AsyncSession):
        """Initialize the service.

        Args:
            session: Database session.
        """
        self.session = session
        self.gap_repo = GapRepository(session)

    async def detect_gaps_for_property(
        self,
        property_id: str,
        clear_existing: bool = True,
    ) -> list[CoverageGap]:
        """Run all gap detection checks for a property.

        Args:
            property_id: Property ID to check.
            clear_existing: If True, clear existing open gaps before detection.

        Returns:
            List of detected gaps.
        """
        logger.info(f"Running gap detection for property {property_id}")

        # Load property with all related data
        prop = await self._load_property_with_details(property_id)
        if not prop:
            logger.warning(f"Property {property_id} not found")
            return []

        # Clear existing open gaps if requested
        if clear_existing:
            await self.gap_repo.clear_open_gaps_for_property(property_id)

        # Run all gap detection checks
        gaps: list[CoverageGap] = []

        # 1. Underinsurance detection
        underinsurance_gaps = await self._detect_underinsurance(prop)
        gaps.extend(underinsurance_gaps)

        # 2. High deductible detection
        deductible_gaps = await self._detect_high_deductibles(prop)
        gaps.extend(deductible_gaps)

        # 3. Expiration detection
        expiration_gaps = await self._detect_expirations(prop)
        gaps.extend(expiration_gaps)

        # 4. Missing coverage detection
        missing_coverage_gaps = await self._detect_missing_coverages(prop)
        gaps.extend(missing_coverage_gaps)

        # 5. Missing flood coverage detection
        flood_gaps = await self._detect_missing_flood(prop)
        gaps.extend(flood_gaps)

        # 6. Outdated valuation detection
        valuation_gaps = await self._detect_outdated_valuations(prop)
        gaps.extend(valuation_gaps)

        logger.info(
            f"Gap detection complete for property {property_id}: "
            f"{len(gaps)} gaps detected"
        )

        return gaps

    async def detect_gaps_for_organization(
        self,
        organization_id: str,
        clear_existing: bool = True,
    ) -> dict[str, list[CoverageGap]]:
        """Run gap detection for all properties in an organization.

        Args:
            organization_id: Organization ID.
            clear_existing: If True, clear existing open gaps before detection.

        Returns:
            Dictionary mapping property_id to list of gaps.
        """
        # Get all properties for the organization
        stmt = select(Property).where(
            Property.organization_id == organization_id,
            Property.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        properties = result.scalars().all()

        results: dict[str, list[CoverageGap]] = {}

        for prop in properties:
            gaps = await self.detect_gaps_for_property(
                prop.id, clear_existing=clear_existing
            )
            results[prop.id] = gaps

        total_gaps = sum(len(g) for g in results.values())
        logger.info(
            f"Gap detection complete for organization {organization_id}: "
            f"{len(properties)} properties, {total_gaps} total gaps"
        )

        return results

    async def _load_property_with_details(self, property_id: str) -> Property | None:
        """Load a property with all related data for gap detection.

        Args:
            property_id: Property ID.

        Returns:
            Property with loaded relationships or None.
        """
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

    async def _detect_underinsurance(self, prop: Property) -> list[CoverageGap]:
        """Detect underinsurance gaps.

        Checks if property coverage is less than building replacement cost.
        - Critical: < 80%
        - Warning: 80-90%

        Args:
            prop: Property with loaded data.

        Returns:
            List of underinsurance gaps.
        """
        gaps: list[CoverageGap] = []

        # Calculate total building value (used as replacement cost proxy)
        total_replacement_cost = Decimal("0")
        for building in prop.buildings:
            if building.building_value:
                total_replacement_cost += building.building_value

        if total_replacement_cost == 0:
            # No building value data, can't check underinsurance
            return gaps

        # Get total property coverage from active programs
        total_property_coverage = Decimal("0")
        for program in prop.insurance_programs:
            if program.status != "active":
                continue
            for policy in program.policies:
                if policy.policy_type and "property" in policy.policy_type.lower():
                    for coverage in policy.coverages:
                        if coverage.limit_amount and coverage.coverage_category == "property":
                            total_property_coverage += coverage.limit_amount

        if total_property_coverage == 0:
            # No property coverage found - this is a missing coverage gap, not underinsurance
            return gaps

        # Calculate coverage ratio
        coverage_ratio = float(total_property_coverage / total_replacement_cost)

        if coverage_ratio < UNDERINSURANCE.CRITICAL_PCT:
            # Critical underinsurance
            gap = await self.gap_repo.create_gap(
                property_id=prop.id,
                gap_type=GapType.UNDERINSURANCE,
                severity=Severity.CRITICAL,
                title="Critical Underinsurance",
                description=(
                    f"Property coverage ({total_property_coverage:,.0f}) is only "
                    f"{coverage_ratio:.0%} of replacement cost ({total_replacement_cost:,.0f}). "
                    f"Coverage should be at least 80% to avoid coinsurance penalties."
                ),
                coverage_name="Property Coverage",
                current_value=f"${total_property_coverage:,.0f}",
                recommended_value=f"${total_replacement_cost:,.0f}",
                gap_amount=float(total_replacement_cost - total_property_coverage),
            )
            gaps.append(gap)

        elif coverage_ratio < UNDERINSURANCE.WARNING_PCT:
            # Warning - coverage between 80-90%
            gap = await self.gap_repo.create_gap(
                property_id=prop.id,
                gap_type=GapType.UNDERINSURANCE,
                severity=Severity.WARNING,
                title="Potential Underinsurance",
                description=(
                    f"Property coverage ({total_property_coverage:,.0f}) is "
                    f"{coverage_ratio:.0%} of replacement cost ({total_replacement_cost:,.0f}). "
                    f"Consider increasing to 100% for full protection."
                ),
                coverage_name="Property Coverage",
                current_value=f"${total_property_coverage:,.0f}",
                recommended_value=f"${total_replacement_cost:,.0f}",
                gap_amount=float(total_replacement_cost - total_property_coverage),
            )
            gaps.append(gap)

        return gaps

    async def _detect_high_deductibles(self, prop: Property) -> list[CoverageGap]:
        """Detect high deductible gaps.

        Checks if deductibles exceed thresholds:
        - Critical: > 5% of TIV or > $500K flat
        - Warning: > 3% of TIV or > $250K flat

        Args:
            prop: Property with loaded data.

        Returns:
            List of high deductible gaps.
        """
        gaps: list[CoverageGap] = []

        # Calculate TIV from programs
        total_tiv = Decimal("0")
        for program in prop.insurance_programs:
            if program.status == "active" and program.total_insured_value:
                total_tiv += program.total_insured_value

        if total_tiv == 0:
            # No TIV data, skip percentage-based checks
            return gaps

        # Check each coverage for high deductibles
        for program in prop.insurance_programs:
            if program.status != "active":
                continue

            for policy in program.policies:
                for coverage in policy.coverages:
                    if not coverage.deductible_amount and not coverage.deductible_pct:
                        continue

                    severity = None
                    deductible_value = None
                    threshold_msg = ""

                    # Check percentage deductible
                    if coverage.deductible_pct:
                        pct = float(coverage.deductible_pct)
                        if pct > DEDUCTIBLE.CRITICAL_PCT * 100:
                            severity = Severity.CRITICAL
                            deductible_value = f"{pct}%"
                            threshold_msg = f"exceeds {DEDUCTIBLE.CRITICAL_PCT * 100}% threshold"
                        elif pct > DEDUCTIBLE.WARNING_PCT * 100:
                            severity = Severity.WARNING
                            deductible_value = f"{pct}%"
                            threshold_msg = f"exceeds {DEDUCTIBLE.WARNING_PCT * 100}% threshold"

                    # Check flat deductible
                    elif coverage.deductible_amount:
                        amount = coverage.deductible_amount
                        pct_of_tiv = float(amount / total_tiv) if total_tiv > 0 else 0

                        if amount > DEDUCTIBLE.CRITICAL_FLAT or pct_of_tiv > DEDUCTIBLE.CRITICAL_PCT:
                            severity = Severity.CRITICAL
                            deductible_value = f"${amount:,.0f}"
                            if pct_of_tiv > DEDUCTIBLE.CRITICAL_PCT:
                                threshold_msg = f"({pct_of_tiv:.1%} of TIV) exceeds 5% threshold"
                            else:
                                threshold_msg = f"exceeds ${DEDUCTIBLE.CRITICAL_FLAT:,.0f} threshold"

                        elif amount > DEDUCTIBLE.WARNING_FLAT or pct_of_tiv > DEDUCTIBLE.WARNING_PCT:
                            severity = Severity.WARNING
                            deductible_value = f"${amount:,.0f}"
                            if pct_of_tiv > DEDUCTIBLE.WARNING_PCT:
                                threshold_msg = f"({pct_of_tiv:.1%} of TIV) exceeds 3% threshold"
                            else:
                                threshold_msg = f"exceeds ${DEDUCTIBLE.WARNING_FLAT:,.0f} threshold"

                    if severity:
                        gap = await self.gap_repo.create_gap(
                            property_id=prop.id,
                            policy_id=policy.id,
                            program_id=program.id,
                            gap_type=GapType.HIGH_DEDUCTIBLE,
                            severity=severity,
                            title=f"High Deductible - {coverage.coverage_name or 'Coverage'}",
                            description=(
                                f"Deductible of {deductible_value} for "
                                f"{coverage.coverage_name or 'coverage'} {threshold_msg}. "
                                f"Consider negotiating lower deductibles."
                            ),
                            coverage_name=coverage.coverage_name,
                            current_value=deductible_value,
                            recommended_value="< 3% of TIV or $250,000",
                        )
                        gaps.append(gap)

        return gaps

    async def _detect_expirations(self, prop: Property) -> list[CoverageGap]:
        """Detect expiration gaps.

        Checks policies expiring soon:
        - Critical: <= 30 days
        - Warning: 31-60 days
        - Info: 61-90 days

        Args:
            prop: Property with loaded data.

        Returns:
            List of expiration gaps.
        """
        gaps: list[CoverageGap] = []
        today = date.today()

        for program in prop.insurance_programs:
            if program.status != "active":
                continue

            for policy in program.policies:
                if not policy.expiration_date:
                    continue

                days_until = (policy.expiration_date - today).days

                # Skip already expired policies (that's a different issue)
                if days_until < 0:
                    continue

                severity = None
                if days_until <= EXPIRATION.CRITICAL_DAYS:
                    severity = Severity.CRITICAL
                elif days_until <= EXPIRATION.WARNING_DAYS:
                    severity = Severity.WARNING
                elif days_until <= EXPIRATION.INFO_DAYS:
                    severity = Severity.INFO

                if severity:
                    policy_type = policy.policy_type or "Policy"
                    gap = await self.gap_repo.create_gap(
                        property_id=prop.id,
                        policy_id=policy.id,
                        program_id=program.id,
                        gap_type=GapType.EXPIRATION,
                        severity=severity,
                        title=f"{policy_type} Expiring Soon",
                        description=(
                            f"{policy_type} ({policy.policy_number or 'N/A'}) expires in "
                            f"{days_until} days on {policy.expiration_date.isoformat()}. "
                            f"Begin renewal process immediately."
                        ),
                        coverage_name=policy_type,
                        current_value=f"{days_until} days",
                        recommended_value="Renew before expiration",
                    )
                    gaps.append(gap)

        return gaps

    async def _detect_missing_coverages(self, prop: Property) -> list[CoverageGap]:
        """Detect missing required coverages.

        Checks for:
        - Missing property coverage
        - Missing general liability coverage
        - Missing umbrella (if TIV > $5M)

        Args:
            prop: Property with loaded data.

        Returns:
            List of missing coverage gaps.
        """
        gaps: list[CoverageGap] = []

        # Collect all coverage types from active policies
        coverage_types: set[str] = set()
        total_tiv = Decimal("0")

        for program in prop.insurance_programs:
            if program.status != "active":
                continue

            if program.total_insured_value:
                total_tiv += program.total_insured_value

            for policy in program.policies:
                if policy.policy_type:
                    coverage_types.add(policy.policy_type.lower())

        # Check required coverages
        for required in COVERAGE_REQUIREMENTS.REQUIRED:
            # Normalize matching (property, general_liability, gl, etc.)
            has_coverage = False
            if required == "property":
                has_coverage = any(
                    "property" in ct or "fire" in ct or "building" in ct
                    for ct in coverage_types
                )
            elif required == "general_liability":
                has_coverage = any(
                    "liability" in ct or "gl" in ct or "cgl" in ct
                    for ct in coverage_types
                )

            if not has_coverage:
                gap = await self.gap_repo.create_gap(
                    property_id=prop.id,
                    gap_type=GapType.MISSING_COVERAGE,
                    severity=Severity.CRITICAL,
                    title=f"Missing {required.replace('_', ' ').title()} Coverage",
                    description=(
                        f"No {required.replace('_', ' ')} policy found for this property. "
                        f"This is a required coverage type."
                    ),
                    coverage_name=required.replace("_", " ").title(),
                    current_value="None",
                    recommended_value="Required",
                )
                gaps.append(gap)

        # Check umbrella recommendation
        if total_tiv > COVERAGE_REQUIREMENTS.UMBRELLA_TIV_THRESHOLD:
            has_umbrella = any(
                "umbrella" in ct or "excess" in ct for ct in coverage_types
            )
            if not has_umbrella:
                gap = await self.gap_repo.create_gap(
                    property_id=prop.id,
                    gap_type=GapType.MISSING_COVERAGE,
                    severity=Severity.WARNING,
                    title="Missing Umbrella/Excess Coverage",
                    description=(
                        f"Property TIV ({total_tiv:,.0f}) exceeds $5M threshold. "
                        f"Umbrella or excess liability coverage is recommended."
                    ),
                    coverage_name="Umbrella/Excess Liability",
                    current_value="None",
                    recommended_value="Recommended for TIV > $5M",
                )
                gaps.append(gap)

        return gaps

    async def _detect_missing_flood(self, prop: Property) -> list[CoverageGap]:
        """Detect missing flood coverage for properties in flood zones.

        Args:
            prop: Property with loaded data.

        Returns:
            List of missing flood coverage gaps.
        """
        gaps: list[CoverageGap] = []

        # Check if property is in a high-risk flood zone
        if not prop.flood_zone:
            return gaps

        # Normalize flood zone check
        flood_zone_upper = prop.flood_zone.upper()
        is_high_risk = any(
            flood_zone_upper.startswith(zone) for zone in COVERAGE_REQUIREMENTS.FLOOD_ZONES
        )

        if not is_high_risk:
            return gaps

        # Check if flood coverage exists
        has_flood = False
        for program in prop.insurance_programs:
            if program.status != "active":
                continue
            for policy in program.policies:
                if policy.policy_type and "flood" in policy.policy_type.lower():
                    has_flood = True
                    break
                # Also check coverages within property policies
                for coverage in policy.coverages:
                    if coverage.coverage_name and "flood" in coverage.coverage_name.lower():
                        has_flood = True
                        break

        if not has_flood:
            gap = await self.gap_repo.create_gap(
                property_id=prop.id,
                gap_type=GapType.MISSING_FLOOD,
                severity=Severity.CRITICAL,
                title="Missing Flood Coverage in High-Risk Zone",
                description=(
                    f"Property is in flood zone {prop.flood_zone} (high-risk) "
                    f"but has no flood insurance coverage. "
                    f"Flood coverage is typically required by lenders for properties in this zone."
                ),
                coverage_name="Flood Insurance",
                current_value="None",
                recommended_value="Required for flood zone",
            )
            gaps.append(gap)

        return gaps

    async def _detect_outdated_valuations(self, prop: Property) -> list[CoverageGap]:
        """Detect outdated property valuations.

        Checks if last valuation is:
        - Critical: > 3 years old
        - Warning: > 2 years old

        Args:
            prop: Property with loaded data.

        Returns:
            List of outdated valuation gaps.
        """
        gaps: list[CoverageGap] = []
        today = date.today()

        # Find the most recent valuation
        latest_valuation: Valuation | None = None
        for valuation in prop.valuations:
            if valuation.deleted_at:
                continue
            if valuation.valuation_date:
                if not latest_valuation or valuation.valuation_date > latest_valuation.valuation_date:
                    latest_valuation = valuation

        if not latest_valuation or not latest_valuation.valuation_date:
            # No valuation on record - could be a gap
            gap = await self.gap_repo.create_gap(
                property_id=prop.id,
                gap_type=GapType.OUTDATED_VALUATION,
                severity=Severity.WARNING,
                title="No Property Valuation on Record",
                description=(
                    "No property valuation found. A current valuation is recommended "
                    "to ensure adequate coverage limits."
                ),
                coverage_name="Property Valuation",
                current_value="None",
                recommended_value="Annual valuation recommended",
            )
            gaps.append(gap)
            return gaps

        # Calculate age of valuation
        valuation_age_days = (today - latest_valuation.valuation_date).days
        valuation_age_years = valuation_age_days / 365.25

        if valuation_age_years > VALUATION.CRITICAL_YEARS:
            gap = await self.gap_repo.create_gap(
                property_id=prop.id,
                gap_type=GapType.OUTDATED_VALUATION,
                severity=Severity.CRITICAL,
                title="Critically Outdated Property Valuation",
                description=(
                    f"Last property valuation was {valuation_age_years:.1f} years ago "
                    f"({latest_valuation.valuation_date.isoformat()}). "
                    f"Values may be significantly understated. Update immediately."
                ),
                coverage_name="Property Valuation",
                current_value=f"{valuation_age_years:.1f} years old",
                recommended_value="Valuation within 1 year",
            )
            gaps.append(gap)

        elif valuation_age_years > VALUATION.WARNING_YEARS:
            gap = await self.gap_repo.create_gap(
                property_id=prop.id,
                gap_type=GapType.OUTDATED_VALUATION,
                severity=Severity.WARNING,
                title="Outdated Property Valuation",
                description=(
                    f"Last property valuation was {valuation_age_years:.1f} years ago "
                    f"({latest_valuation.valuation_date.isoformat()}). "
                    f"Consider updating to ensure adequate coverage."
                ),
                coverage_name="Property Valuation",
                current_value=f"{valuation_age_years:.1f} years old",
                recommended_value="Valuation within 1 year",
            )
            gaps.append(gap)

        return gaps


def get_gap_detection_service(session: AsyncSession) -> GapDetectionService:
    """Factory function to create GapDetectionService.

    Args:
        session: Database session.

    Returns:
        GapDetectionService instance.
    """
    return GapDetectionService(session)
