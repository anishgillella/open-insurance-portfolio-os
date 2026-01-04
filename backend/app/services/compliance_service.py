"""Lender Compliance Checking Service.

Checks property insurance against lender requirements and detects compliance issues.
Supports multiple compliance templates:
- Standard Commercial
- Fannie Mae Multifamily
- Conservative

Compliance checks:
1. Property coverage adequacy (min limit)
2. General liability limits
3. Umbrella/excess coverage
4. Deductible maximums
5. Flood coverage requirements
6. Earthquake coverage requirements
7. Business income coverage
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.gap_thresholds import COMPLIANCE_TEMPLATES, GapType, Severity
from app.models.coverage_gap import CoverageGap
from app.models.insurance_program import InsuranceProgram
from app.models.lender_requirement import LenderRequirement
from app.models.policy import Policy
from app.models.property import Property
from app.repositories.gap_repository import GapRepository

logger = logging.getLogger(__name__)


class ComplianceIssue:
    """Represents a single compliance issue."""

    def __init__(
        self,
        check_name: str,
        severity: str,
        message: str,
        current_value: str | None = None,
        required_value: str | None = None,
    ):
        self.check_name = check_name
        self.severity = severity
        self.message = message
        self.current_value = current_value
        self.required_value = required_value

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "severity": self.severity,
            "message": self.message,
            "current_value": self.current_value,
            "required_value": self.required_value,
        }


class ComplianceResult:
    """Result of compliance check."""

    def __init__(
        self,
        property_id: str,
        lender_requirement_id: str | None,
        template_name: str,
        is_compliant: bool,
        issues: list[ComplianceIssue],
    ):
        self.property_id = property_id
        self.lender_requirement_id = lender_requirement_id
        self.template_name = template_name
        self.is_compliant = is_compliant
        self.issues = issues

    @property
    def status(self) -> str:
        if self.is_compliant:
            return "compliant"
        critical_count = sum(1 for i in self.issues if i.severity == Severity.CRITICAL)
        if critical_count > 0:
            return "non_compliant"
        return "partial"


class ComplianceService:
    """Service for checking lender compliance."""

    def __init__(self, session: AsyncSession):
        """Initialize the service.

        Args:
            session: Database session.
        """
        self.session = session
        self.gap_repo = GapRepository(session)

    async def check_compliance_for_property(
        self,
        property_id: str,
        create_gaps: bool = True,
    ) -> list[ComplianceResult]:
        """Check compliance against all lender requirements for a property.

        Args:
            property_id: Property ID.
            create_gaps: If True, create CoverageGap records for issues.

        Returns:
            List of ComplianceResult for each lender requirement.
        """
        logger.info(f"Checking compliance for property {property_id}")

        # Load property with data
        prop = await self._load_property_with_details(property_id)
        if not prop:
            logger.warning(f"Property {property_id} not found")
            return []

        # Get lender requirements for this property
        stmt = (
            select(LenderRequirement)
            .options(selectinload(LenderRequirement.lender))
            .where(
                LenderRequirement.property_id == property_id,
                LenderRequirement.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        requirements = result.scalars().all()

        if not requirements:
            logger.info(f"No lender requirements for property {property_id}")
            return []

        results: list[ComplianceResult] = []

        for req in requirements:
            compliance_result = await self._check_against_requirement(prop, req)
            results.append(compliance_result)

            # Update requirement with compliance status
            req.compliance_status = compliance_result.status
            req.compliance_checked_at = datetime.now(timezone.utc)
            req.compliance_issues = [i.to_dict() for i in compliance_result.issues]

            # Create gaps for issues if requested
            if create_gaps and compliance_result.issues:
                await self._create_compliance_gaps(prop, req, compliance_result.issues)

        await self.session.flush()

        logger.info(
            f"Compliance check complete for property {property_id}: "
            f"{len(results)} requirements checked"
        )

        return results

    async def check_against_template(
        self,
        property_id: str,
        template_name: str = "standard",
    ) -> ComplianceResult:
        """Check property compliance against a template (without lender requirement record).

        Useful for quick checks or when no specific lender requirement exists.

        Args:
            property_id: Property ID.
            template_name: Template name (standard, fannie_mae, conservative).

        Returns:
            ComplianceResult.
        """
        prop = await self._load_property_with_details(property_id)
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        # Get template
        template = self._get_template(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")

        # Build a mock requirement from template
        mock_req = LenderRequirement(
            property_id=property_id,
            min_property_limit=template.get("min_property_coverage_pct"),
            min_gl_limit=template.get("min_gl_limit"),
            min_umbrella_limit=template.get("min_umbrella_limit"),
            max_deductible_pct=template.get("max_deductible_pct"),
            max_deductible_amount=template.get("max_deductible_amount"),
            requires_flood=template.get("requires_flood", False),
            requires_earthquake=template.get("requires_earthquake", False),
        )

        return await self._check_against_requirement(prop, mock_req, template_name=template["name"])

    def get_available_templates(self) -> list[dict]:
        """Get list of available compliance templates.

        Returns:
            List of template info dictionaries.
        """
        return [
            {
                "name": "standard",
                "display_name": COMPLIANCE_TEMPLATES.STANDARD["name"],
                "description": "Common commercial lender requirements",
            },
            {
                "name": "fannie_mae",
                "display_name": COMPLIANCE_TEMPLATES.FANNIE_MAE["name"],
                "description": "Fannie Mae multifamily requirements",
            },
            {
                "name": "conservative",
                "display_name": COMPLIANCE_TEMPLATES.CONSERVATIVE["name"],
                "description": "Stricter lender requirements",
            },
        ]

    async def _load_property_with_details(self, property_id: str) -> Property | None:
        """Load property with insurance data."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.buildings),
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

    def _get_template(self, name: str) -> dict | None:
        """Get a compliance template by name."""
        templates = {
            "standard": COMPLIANCE_TEMPLATES.STANDARD,
            "fannie_mae": COMPLIANCE_TEMPLATES.FANNIE_MAE,
            "conservative": COMPLIANCE_TEMPLATES.CONSERVATIVE,
        }
        return templates.get(name.lower())

    async def _check_against_requirement(
        self,
        prop: Property,
        req: LenderRequirement,
        template_name: str | None = None,
    ) -> ComplianceResult:
        """Check property against a specific lender requirement.

        Args:
            prop: Property with loaded data.
            req: Lender requirement to check against.
            template_name: Optional template name for display.

        Returns:
            ComplianceResult.
        """
        issues: list[ComplianceIssue] = []

        # Gather property insurance data
        coverage_data = self._gather_coverage_data(prop)

        # 1. Check property coverage adequacy
        if req.min_property_limit:
            issue = self._check_property_coverage(coverage_data, req)
            if issue:
                issues.append(issue)

        # 2. Check GL limits
        if req.min_gl_limit:
            issue = self._check_gl_coverage(coverage_data, req)
            if issue:
                issues.append(issue)

        # 3. Check umbrella coverage
        if req.min_umbrella_limit:
            issue = self._check_umbrella_coverage(coverage_data, req, prop.units)
            if issue:
                issues.append(issue)

        # 4. Check deductible limits
        if req.max_deductible_pct or req.max_deductible_amount:
            deductible_issues = self._check_deductibles(coverage_data, req)
            issues.extend(deductible_issues)

        # 5. Check flood coverage
        if req.requires_flood and prop.flood_zone:
            issue = self._check_flood_coverage(coverage_data, prop)
            if issue:
                issues.append(issue)

        # 6. Check earthquake coverage
        if req.requires_earthquake:
            issue = self._check_earthquake_coverage(coverage_data)
            if issue:
                issues.append(issue)

        lender_name = req.lender.name if req.lender else template_name or "Lender"

        return ComplianceResult(
            property_id=prop.id,
            lender_requirement_id=req.id if hasattr(req, 'id') and req.id else None,
            template_name=lender_name,
            is_compliant=len(issues) == 0,
            issues=issues,
        )

    def _gather_coverage_data(self, prop: Property) -> dict:
        """Gather coverage data from property's insurance programs.

        Returns dict with:
        - total_property_limit
        - total_gl_limit
        - total_umbrella_limit
        - total_tiv
        - max_deductible_pct
        - max_deductible_amount
        - has_flood
        - has_earthquake
        - has_business_income
        """
        data = {
            "total_property_limit": Decimal("0"),
            "total_gl_limit": Decimal("0"),
            "total_umbrella_limit": Decimal("0"),
            "total_tiv": Decimal("0"),
            "max_deductible_pct": 0.0,
            "max_deductible_amount": Decimal("0"),
            "has_flood": False,
            "has_earthquake": False,
            "has_business_income": False,
            "deductibles": [],  # Track all deductibles for checking
        }

        for program in prop.insurance_programs:
            if program.status != "active":
                continue

            if program.total_insured_value:
                data["total_tiv"] += program.total_insured_value

            for policy in program.policies:
                policy_type = (policy.policy_type or "").lower()

                # Check policy type
                if "flood" in policy_type:
                    data["has_flood"] = True
                if "earthquake" in policy_type or "eq" in policy_type:
                    data["has_earthquake"] = True
                if "umbrella" in policy_type or "excess" in policy_type:
                    # Sum umbrella limits
                    for coverage in policy.coverages:
                        if coverage.limit_amount:
                            data["total_umbrella_limit"] += coverage.limit_amount

                for coverage in policy.coverages:
                    coverage_name = (coverage.coverage_name or "").lower()
                    category = (coverage.coverage_category or "").lower()

                    # Property coverage
                    if category == "property" or "building" in coverage_name:
                        if coverage.limit_amount:
                            data["total_property_limit"] += coverage.limit_amount

                    # GL coverage
                    if category == "liability" or "general liability" in coverage_name:
                        if coverage.limit_amount:
                            data["total_gl_limit"] += coverage.limit_amount

                    # Flood
                    if "flood" in coverage_name:
                        data["has_flood"] = True

                    # Earthquake
                    if "earthquake" in coverage_name or "eq" in coverage_name:
                        data["has_earthquake"] = True

                    # Business income
                    if "business income" in coverage_name or "bi" in coverage_name:
                        data["has_business_income"] = True

                    # Track deductibles
                    if coverage.deductible_pct:
                        data["max_deductible_pct"] = max(
                            data["max_deductible_pct"], float(coverage.deductible_pct)
                        )
                        data["deductibles"].append({
                            "name": coverage.coverage_name,
                            "pct": coverage.deductible_pct,
                            "amount": None,
                        })
                    if coverage.deductible_amount:
                        data["max_deductible_amount"] = max(
                            data["max_deductible_amount"], coverage.deductible_amount
                        )
                        data["deductibles"].append({
                            "name": coverage.coverage_name,
                            "pct": None,
                            "amount": coverage.deductible_amount,
                        })

        return data

    def _check_property_coverage(
        self, coverage_data: dict, req: LenderRequirement
    ) -> ComplianceIssue | None:
        """Check if property coverage meets minimum requirement."""
        actual = coverage_data["total_property_limit"]
        tiv = coverage_data["total_tiv"]

        # If requirement is a percentage (e.g., 1.0 = 100%)
        if req.min_property_limit and req.min_property_limit <= Decimal("1.0"):
            required_pct = float(req.min_property_limit)
            if tiv > 0:
                actual_pct = float(actual / tiv)
                if actual_pct < required_pct:
                    return ComplianceIssue(
                        check_name="Property Coverage",
                        severity=Severity.CRITICAL,
                        message=(
                            f"Property coverage is {actual_pct:.0%} of TIV, "
                            f"but {required_pct:.0%} is required."
                        ),
                        current_value=f"{actual_pct:.0%}",
                        required_value=f"{required_pct:.0%}",
                    )
        # If requirement is a flat amount
        elif req.min_property_limit and actual < req.min_property_limit:
            return ComplianceIssue(
                check_name="Property Coverage",
                severity=Severity.CRITICAL,
                message=(
                    f"Property coverage (${actual:,.0f}) is below "
                    f"minimum required (${req.min_property_limit:,.0f})."
                ),
                current_value=f"${actual:,.0f}",
                required_value=f"${req.min_property_limit:,.0f}",
            )

        return None

    def _check_gl_coverage(
        self, coverage_data: dict, req: LenderRequirement
    ) -> ComplianceIssue | None:
        """Check if GL coverage meets minimum requirement."""
        actual = coverage_data["total_gl_limit"]

        if actual < req.min_gl_limit:
            return ComplianceIssue(
                check_name="General Liability",
                severity=Severity.CRITICAL,
                message=(
                    f"GL coverage (${actual:,.0f}) is below "
                    f"minimum required (${req.min_gl_limit:,.0f})."
                ),
                current_value=f"${actual:,.0f}",
                required_value=f"${req.min_gl_limit:,.0f}",
            )

        return None

    def _check_umbrella_coverage(
        self,
        coverage_data: dict,
        req: LenderRequirement,
        unit_count: int | None,
    ) -> ComplianceIssue | None:
        """Check if umbrella coverage meets minimum requirement."""
        actual = coverage_data["total_umbrella_limit"]
        required = req.min_umbrella_limit

        # For Fannie Mae, requirement varies by unit count
        if not required and hasattr(req, "umbrella_unit_thresholds"):
            # This would be for template-based checks
            pass

        if required and actual < required:
            return ComplianceIssue(
                check_name="Umbrella/Excess Liability",
                severity=Severity.CRITICAL,
                message=(
                    f"Umbrella coverage (${actual:,.0f}) is below "
                    f"minimum required (${required:,.0f})."
                ),
                current_value=f"${actual:,.0f}",
                required_value=f"${required:,.0f}",
            )

        return None

    def _check_deductibles(
        self, coverage_data: dict, req: LenderRequirement
    ) -> list[ComplianceIssue]:
        """Check if deductibles are within limits."""
        issues: list[ComplianceIssue] = []
        tiv = coverage_data["total_tiv"]

        for deductible in coverage_data["deductibles"]:
            # Check percentage deductible
            if deductible["pct"] and req.max_deductible_pct:
                if float(deductible["pct"]) > req.max_deductible_pct * 100:
                    issues.append(
                        ComplianceIssue(
                            check_name=f"Deductible - {deductible['name'] or 'Coverage'}",
                            severity=Severity.WARNING,
                            message=(
                                f"Deductible of {deductible['pct']}% exceeds "
                                f"maximum allowed ({req.max_deductible_pct * 100}%)."
                            ),
                            current_value=f"{deductible['pct']}%",
                            required_value=f"<= {req.max_deductible_pct * 100}%",
                        )
                    )

            # Check flat deductible
            if deductible["amount"] and req.max_deductible_amount:
                if deductible["amount"] > req.max_deductible_amount:
                    issues.append(
                        ComplianceIssue(
                            check_name=f"Deductible - {deductible['name'] or 'Coverage'}",
                            severity=Severity.WARNING,
                            message=(
                                f"Deductible of ${deductible['amount']:,.0f} exceeds "
                                f"maximum allowed (${req.max_deductible_amount:,.0f})."
                            ),
                            current_value=f"${deductible['amount']:,.0f}",
                            required_value=f"<= ${req.max_deductible_amount:,.0f}",
                        )
                    )

            # Check flat deductible as percentage of TIV
            if deductible["amount"] and req.max_deductible_pct and tiv > 0:
                pct_of_tiv = float(deductible["amount"] / tiv)
                if pct_of_tiv > req.max_deductible_pct:
                    issues.append(
                        ComplianceIssue(
                            check_name=f"Deductible - {deductible['name'] or 'Coverage'}",
                            severity=Severity.WARNING,
                            message=(
                                f"Deductible of ${deductible['amount']:,.0f} "
                                f"({pct_of_tiv:.1%} of TIV) exceeds "
                                f"maximum allowed ({req.max_deductible_pct * 100}% of TIV)."
                            ),
                            current_value=f"{pct_of_tiv:.1%} of TIV",
                            required_value=f"<= {req.max_deductible_pct * 100}% of TIV",
                        )
                    )

        return issues

    def _check_flood_coverage(
        self, coverage_data: dict, prop: Property
    ) -> ComplianceIssue | None:
        """Check if flood coverage exists when required."""
        if not coverage_data["has_flood"]:
            return ComplianceIssue(
                check_name="Flood Coverage",
                severity=Severity.CRITICAL,
                message=(
                    f"Flood coverage is required (property in zone {prop.flood_zone}) "
                    f"but not found."
                ),
                current_value="None",
                required_value="Required",
            )
        return None

    def _check_earthquake_coverage(
        self, coverage_data: dict
    ) -> ComplianceIssue | None:
        """Check if earthquake coverage exists when required."""
        if not coverage_data["has_earthquake"]:
            return ComplianceIssue(
                check_name="Earthquake Coverage",
                severity=Severity.CRITICAL,
                message="Earthquake coverage is required but not found.",
                current_value="None",
                required_value="Required",
            )
        return None

    async def _create_compliance_gaps(
        self,
        prop: Property,
        req: LenderRequirement,
        issues: list[ComplianceIssue],
    ) -> list[CoverageGap]:
        """Create CoverageGap records for compliance issues.

        Args:
            prop: Property.
            req: Lender requirement.
            issues: List of compliance issues.

        Returns:
            Created CoverageGap records.
        """
        gaps: list[CoverageGap] = []
        lender_name = req.lender.name if req.lender else "Lender"

        for issue in issues:
            gap = await self.gap_repo.create_gap(
                property_id=prop.id,
                gap_type=GapType.COMPLIANCE,
                severity=issue.severity,
                title=f"Compliance: {issue.check_name}",
                description=f"[{lender_name}] {issue.message}",
                coverage_name=issue.check_name,
                current_value=issue.current_value,
                recommended_value=issue.required_value,
            )
            gaps.append(gap)

        return gaps


def get_compliance_service(session: AsyncSession) -> ComplianceService:
    """Factory function to create ComplianceService.

    Args:
        session: Database session.

    Returns:
        ComplianceService instance.
    """
    return ComplianceService(session)
