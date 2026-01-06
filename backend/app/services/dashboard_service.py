"""Dashboard service for portfolio statistics and summaries.

This service aggregates data from multiple repositories to provide
dashboard summary statistics, expiration tracking, and alerts.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coverage_gap import CoverageGap
from app.models.policy import Policy
from app.models.property import Property
from app.repositories.policy_repository import PolicyRepository
from app.repositories.property_repository import PropertyRepository
from app.schemas.dashboard import (
    AlertCounts,
    AlertItem,
    AlertsResponse,
    ComplianceStats,
    CompletenessStats,
    DashboardSummary,
    ExpirationItem,
    ExpirationStats,
    ExpirationSummary,
    ExpirationTimelineResponse,
    GapStats,
    HealthScoreStats,
    NextExpiration,
    PortfolioStats,
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard data aggregation."""

    def __init__(self, session: AsyncSession):
        """Initialize dashboard service.

        Args:
            session: Async database session.
        """
        self.session = session
        self.property_repo = PropertyRepository(session)
        self.policy_repo = PolicyRepository(session)

    async def get_dashboard_summary(
        self, organization_id: str | None = None
    ) -> DashboardSummary:
        """Get complete dashboard summary.

        Args:
            organization_id: Optional organization filter.

        Returns:
            DashboardSummary with all statistics.
        """
        # Fetch properties once and reuse for multiple calculations
        # Don't include documents - they're expensive and not needed for summary
        properties = await self.property_repo.list_with_summary(
            organization_id=organization_id,
            limit=1000,
            include_buildings=True,
            include_programs=True,
            include_gaps=True,
            include_documents=False,
        )

        # Get base stats (counts only - fast query)
        base_stats = await self.property_repo.get_portfolio_stats(organization_id)

        # Calculate all stats from the cached properties list
        portfolio_stats = self._calculate_portfolio_stats(properties, base_stats)
        gap_stats = self._calculate_gap_stats(properties)
        health_score_stats = self._calculate_health_score_stats(properties)

        # Get expiration stats (requires policy repo query)
        expiration_stats = await self._get_expiration_stats(organization_id)

        # Placeholders
        compliance_stats = ComplianceStats()
        completeness_stats = CompletenessStats()

        return DashboardSummary(
            portfolio_stats=portfolio_stats,
            expiration_stats=expiration_stats,
            gap_stats=gap_stats,
            compliance_stats=compliance_stats,
            completeness_stats=completeness_stats,
            health_score=health_score_stats,
            generated_at=datetime.utcnow(),
        )

    def _calculate_portfolio_stats(
        self, properties: list, base_stats: dict
    ) -> PortfolioStats:
        """Calculate portfolio-level statistics from pre-fetched properties.

        Aggregates TIV and premium from insurance programs with fallback
        to document extraction data when program values are not populated.
        """
        total_tiv = Decimal("0")
        total_premium = Decimal("0")

        for prop in properties:
            prop_tiv = Decimal("0")
            prop_premium = Decimal("0")

            # First, try to get values from insurance programs
            for program in prop.insurance_programs:
                if program.status == "active":
                    if program.total_premium:
                        prop_premium += program.total_premium
                    if program.total_insured_value:
                        prop_tiv += program.total_insured_value

            # If no values from programs, try document extraction fallback
            if prop_premium == 0 and prop_tiv == 0 and prop.documents:
                doc_premium, doc_tiv = self._extract_financial_data_from_documents(
                    prop.documents
                )
                prop_premium = doc_premium
                prop_tiv = doc_tiv

            total_premium += prop_premium
            total_tiv += prop_tiv

        return PortfolioStats(
            total_properties=base_stats.get("total_properties", 0),
            total_buildings=base_stats.get("total_buildings", 0),
            total_units=base_stats.get("total_units", 0),
            total_insured_value=total_tiv or Decimal("0"),
            total_annual_premium=total_premium or Decimal("0"),
        )

    def _extract_financial_data_from_documents(
        self, documents
    ) -> tuple[Decimal, Decimal]:
        """Extract total premium and TIV from document extraction data.

        Falls back to extraction_json when program/policy totals are not populated.
        """
        total_premium = Decimal("0")
        total_tiv = Decimal("0")

        for doc in documents:
            if not doc.extraction_json:
                continue

            extraction = (
                doc.extraction_json if isinstance(doc.extraction_json, dict) else {}
            )

            # Try invoice data first (most reliable for premiums)
            invoice = extraction.get("invoice") or {}
            if invoice.get("total_amount"):
                try:
                    total_premium += Decimal(str(invoice["total_amount"]))
                except (ValueError, TypeError):
                    pass

            # Try SOV data for TIV
            sov = extraction.get("sov") or {}
            if sov.get("total_insured_value"):
                try:
                    total_tiv += Decimal(str(sov["total_insured_value"]))
                except (ValueError, TypeError):
                    pass

            # Try COI data for TIV
            coi = extraction.get("coi") or {}
            if total_tiv == 0 and coi.get("property_limit"):
                try:
                    total_tiv = Decimal(str(coi["property_limit"]))
                except (ValueError, TypeError):
                    pass

            # Try policy data
            policy = extraction.get("policy") or {}
            if policy.get("premium") and not invoice.get("total_amount"):
                try:
                    total_premium += Decimal(str(policy["premium"]))
                except (ValueError, TypeError):
                    pass
            if total_tiv == 0 and policy.get("total_insured_value"):
                try:
                    total_tiv = Decimal(str(policy["total_insured_value"]))
                except (ValueError, TypeError):
                    pass

        return total_premium, total_tiv

    def _calculate_health_score_stats(self, properties: list) -> HealthScoreStats:
        """Calculate portfolio-wide health score statistics from pre-fetched properties.

        Averages health scores from all properties in the portfolio.
        """
        if not properties:
            return HealthScoreStats()

        total_score = 0
        count = 0

        for prop in properties:
            score = self._calculate_property_health_score(prop)
            if score is not None:
                total_score += score
                count += 1

        if count == 0:
            return HealthScoreStats()

        avg_score = round(total_score / count)

        return HealthScoreStats(
            portfolio_average=avg_score,
            trend="stable",
            trend_delta=0,
        )

    def _calculate_property_health_score(self, prop) -> int:
        """Calculate health score for a single property.

        Based on gaps, coverage completeness, and policy status.
        """
        # Base score starts at 100
        score = 100

        # Deduct for gaps
        if prop.coverage_gaps:
            open_gaps = [
                g for g in prop.coverage_gaps
                if g.status == "open" and g.deleted_at is None
            ]
            for gap in open_gaps:
                if gap.severity == "critical":
                    score -= 15
                elif gap.severity == "warning":
                    score -= 8
                else:
                    score -= 3

        # Deduct for expired or expiring policies
        if prop.insurance_programs:
            for program in prop.insurance_programs:
                if program.status == "active":
                    for policy in program.policies:
                        if policy.expiration_date:
                            days_until = (policy.expiration_date - date.today()).days
                            if days_until < 0:
                                score -= 20  # Expired
                            elif days_until <= 14:
                                score -= 10  # Critical expiration
                            elif days_until <= 30:
                                score -= 5  # Warning expiration

        # Ensure score stays in 0-100 range
        return max(0, min(100, score))

    async def _get_expiration_stats(
        self, organization_id: str | None = None
    ) -> ExpirationStats:
        """Get expiration statistics.

        Args:
            organization_id: Optional organization filter.

        Returns:
            ExpirationStats with counts and next expiration.
        """
        # Get counts by window
        counts = await self.policy_repo.get_expiration_counts(organization_id)

        # Get next expiring policy
        expiring = await self.policy_repo.get_expiring_policies(
            days_ahead=90,
            organization_id=organization_id,
            limit=1,
        )

        next_expiration = None
        if expiring:
            policy = expiring[0]
            property_obj = (
                policy.program.property if policy.program else None
            )
            if policy.expiration_date:
                days_until = (policy.expiration_date - date.today()).days
                next_expiration = NextExpiration(
                    property_name=property_obj.name if property_obj else "Unknown",
                    policy_type=policy.policy_type,
                    expiration_date=policy.expiration_date,
                    days_until_expiration=days_until,
                )

        return ExpirationStats(
            expiring_30_days=counts.get("expiring_30_days", 0),
            expiring_60_days=counts.get("expiring_60_days", 0),
            expiring_90_days=counts.get("expiring_90_days", 0),
            next_expiration=next_expiration,
        )

    def _calculate_gap_stats(self, properties: list) -> GapStats:
        """Calculate coverage gap statistics from pre-fetched properties."""
        total_open = 0
        critical = 0
        warning = 0
        info = 0
        properties_with_gaps = 0

        for prop in properties:
            open_gaps = [
                g for g in prop.coverage_gaps
                if g.status == "open" and g.deleted_at is None
            ]
            if open_gaps:
                properties_with_gaps += 1
                total_open += len(open_gaps)
                for gap in open_gaps:
                    if gap.severity == "critical":
                        critical += 1
                    elif gap.severity == "warning":
                        warning += 1
                    else:
                        info += 1

        return GapStats(
            total_open_gaps=total_open,
            critical_gaps=critical,
            warning_gaps=warning,
            info_gaps=info,
            properties_with_gaps=properties_with_gaps,
        )

    async def get_expiration_timeline(
        self,
        days_ahead: int = 90,
        organization_id: str | None = None,
        limit: int = 50,
    ) -> ExpirationTimelineResponse:
        """Get expiration timeline for visualization.

        Args:
            days_ahead: Number of days to look ahead.
            organization_id: Optional organization filter.
            limit: Maximum results.

        Returns:
            ExpirationTimelineResponse with expiring policies.
        """
        policies = await self.policy_repo.get_expiring_policies(
            days_ahead=days_ahead,
            organization_id=organization_id,
            limit=limit,
        )

        today = date.today()
        expirations = []
        total_premium = Decimal("0")

        for policy in policies:
            property_obj = policy.program.property if policy.program else None
            days_until = (
                (policy.expiration_date - today).days
                if policy.expiration_date
                else 0
            )

            # Determine severity
            if days_until <= 30:
                severity = "critical"
            elif days_until <= 60:
                severity = "warning"
            else:
                severity = "info"

            expirations.append(
                ExpirationItem(
                    id=policy.id,
                    property_id=property_obj.id if property_obj else "",
                    property_name=property_obj.name if property_obj else "Unknown",
                    policy_id=policy.id,
                    policy_number=policy.policy_number,
                    policy_type=policy.policy_type,
                    carrier_name=policy.carrier_name,
                    expiration_date=policy.expiration_date,
                    days_until_expiration=days_until,
                    severity=severity,
                    annual_premium=policy.premium,
                )
            )

            if policy.premium:
                total_premium += policy.premium

        return ExpirationTimelineResponse(
            expirations=expirations,
            summary=ExpirationSummary(
                total_expiring=len(expirations),
                total_premium_at_risk=total_premium,
            ),
        )

    async def get_alerts(
        self,
        severity: str | None = None,
        alert_type: str | None = None,
        organization_id: str | None = None,
        limit: int = 20,
        _cached_properties: list | None = None,
    ) -> AlertsResponse:
        """Get active alerts.

        Args:
            severity: Optional severity filter.
            alert_type: Optional type filter.
            organization_id: Optional organization filter.
            limit: Maximum results.
            _cached_properties: Pre-fetched properties to avoid duplicate query.

        Returns:
            AlertsResponse with alerts and counts.
        """
        alerts: list[AlertItem] = []
        counts = AlertCounts()

        # Get expiration alerts
        if not alert_type or alert_type == "expiration":
            expiring = await self.policy_repo.get_expiring_policies(
                days_ahead=60,
                organization_id=organization_id,
                limit=limit,
            )

            today = date.today()
            for policy in expiring:
                days_until = (
                    (policy.expiration_date - today).days
                    if policy.expiration_date
                    else 0
                )
                alert_severity = "critical" if days_until <= 30 else "warning"

                if severity and severity != alert_severity:
                    continue

                property_obj = policy.program.property if policy.program else None

                alerts.append(
                    AlertItem(
                        id=f"exp-{policy.id}",
                        type="expiration",
                        severity=alert_severity,
                        title=f"Policy expiring in {days_until} days",
                        message=f"{policy.policy_type.title()} policy "
                                f"{policy.policy_number or ''} "
                                f"expires {policy.expiration_date}",
                        property_id=property_obj.id if property_obj else None,
                        property_name=property_obj.name if property_obj else None,
                        created_at=datetime.utcnow(),
                        action_url=f"/properties/{property_obj.id}/policies"
                                   if property_obj else None,
                    )
                )

                if alert_severity == "critical":
                    counts.critical += 1
                else:
                    counts.warning += 1

        # Get gap alerts
        if not alert_type or alert_type == "gap":
            # Use cached properties if provided, otherwise fetch
            # Only load gaps - that's all we need for alerts
            if _cached_properties is not None:
                properties = _cached_properties
            else:
                properties = await self.property_repo.list_with_summary(
                    organization_id=organization_id,
                    limit=1000,
                    include_buildings=False,
                    include_programs=False,
                    include_gaps=True,
                    include_documents=False,
                )

            for prop in properties:
                for gap in prop.coverage_gaps:
                    if gap.status != "open" or gap.deleted_at:
                        continue

                    if severity and severity != gap.severity:
                        continue

                    alerts.append(
                        AlertItem(
                            id=f"gap-{gap.id}",
                            type="gap",
                            severity=gap.severity or "info",
                            title=gap.gap_type or "Coverage Gap",
                            message=gap.description or "Coverage gap detected",
                            property_id=prop.id,
                            property_name=prop.name,
                            created_at=gap.created_at or datetime.utcnow(),
                            action_url=f"/properties/{prop.id}/gaps",
                        )
                    )

                    if gap.severity == "critical":
                        counts.critical += 1
                    elif gap.severity == "warning":
                        counts.warning += 1
                    else:
                        counts.info += 1

        # Sort by severity and limit
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda a: severity_order.get(a.severity, 3))
        alerts = alerts[:limit]

        return AlertsResponse(
            alerts=alerts,
            counts=counts,
        )
