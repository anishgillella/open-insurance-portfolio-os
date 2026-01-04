"""Dashboard API schemas.

Schemas for portfolio dashboard summary statistics, expiration tracking,
and alert management.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Portfolio Statistics
# ---------------------------------------------------------------------------


class PortfolioStats(BaseModel):
    """Portfolio-wide statistics."""

    total_properties: int = Field(default=0, description="Total number of properties")
    total_buildings: int = Field(default=0, description="Total number of buildings")
    total_units: int = Field(default=0, description="Total number of units")
    total_insured_value: Decimal = Field(
        default=Decimal("0"), description="Total insured value (TIV)"
    )
    total_annual_premium: Decimal = Field(
        default=Decimal("0"), description="Total annual premium"
    )


# ---------------------------------------------------------------------------
# Expiration Statistics
# ---------------------------------------------------------------------------


class NextExpiration(BaseModel):
    """Information about the next expiring policy."""

    property_name: str = Field(..., description="Property name")
    policy_type: str = Field(..., description="Policy type")
    expiration_date: date = Field(..., description="Expiration date")
    days_until_expiration: int = Field(..., description="Days until expiration")


class ExpirationStats(BaseModel):
    """Policy expiration statistics."""

    expiring_30_days: int = Field(
        default=0, description="Policies expiring in <= 30 days"
    )
    expiring_60_days: int = Field(
        default=0, description="Policies expiring in 31-60 days"
    )
    expiring_90_days: int = Field(
        default=0, description="Policies expiring in 61-90 days"
    )
    next_expiration: NextExpiration | None = Field(
        default=None, description="Next expiring policy"
    )


# ---------------------------------------------------------------------------
# Gap Statistics
# ---------------------------------------------------------------------------


class GapStats(BaseModel):
    """Coverage gap statistics."""

    total_open_gaps: int = Field(default=0, description="Total open gaps")
    critical_gaps: int = Field(default=0, description="Critical severity gaps")
    warning_gaps: int = Field(default=0, description="Warning severity gaps")
    info_gaps: int = Field(default=0, description="Info severity gaps")
    properties_with_gaps: int = Field(
        default=0, description="Number of properties with gaps"
    )


# ---------------------------------------------------------------------------
# Compliance Statistics
# ---------------------------------------------------------------------------


class ComplianceStats(BaseModel):
    """Lender compliance statistics."""

    compliant_properties: int = Field(default=0, description="Compliant properties")
    non_compliant_properties: int = Field(
        default=0, description="Non-compliant properties"
    )
    properties_without_requirements: int = Field(
        default=0, description="Properties without lender requirements"
    )


# ---------------------------------------------------------------------------
# Completeness Statistics
# ---------------------------------------------------------------------------


class CompletenessStats(BaseModel):
    """Document completeness statistics."""

    average_completeness: float = Field(
        default=0.0, description="Average completeness percentage"
    )
    fully_complete_properties: int = Field(
        default=0, description="Properties with 100% completeness"
    )
    properties_missing_required_docs: int = Field(
        default=0, description="Properties missing required documents"
    )


# ---------------------------------------------------------------------------
# Health Score Statistics
# ---------------------------------------------------------------------------


class HealthScoreStats(BaseModel):
    """Portfolio health score statistics."""

    portfolio_average: int = Field(
        default=0, description="Average health score (0-100)"
    )
    trend: str = Field(
        default="stable", description="Trend: improving, stable, declining"
    )
    trend_delta: int = Field(default=0, description="Change from previous period")


# ---------------------------------------------------------------------------
# Dashboard Summary Response
# ---------------------------------------------------------------------------


class DashboardSummary(BaseModel):
    """Complete dashboard summary response."""

    portfolio_stats: PortfolioStats = Field(
        default_factory=PortfolioStats, description="Portfolio statistics"
    )
    expiration_stats: ExpirationStats = Field(
        default_factory=ExpirationStats, description="Expiration statistics"
    )
    gap_stats: GapStats = Field(default_factory=GapStats, description="Gap statistics")
    compliance_stats: ComplianceStats = Field(
        default_factory=ComplianceStats, description="Compliance statistics"
    )
    completeness_stats: CompletenessStats = Field(
        default_factory=CompletenessStats, description="Completeness statistics"
    )
    health_score: HealthScoreStats = Field(
        default_factory=HealthScoreStats, description="Health score statistics"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )


# ---------------------------------------------------------------------------
# Expiration Timeline
# ---------------------------------------------------------------------------


class ExpirationItem(BaseModel):
    """Single expiration item for timeline."""

    id: str = Field(..., description="Policy ID")
    property_id: str = Field(..., description="Property ID")
    property_name: str = Field(..., description="Property name")
    policy_id: str = Field(..., description="Policy ID")
    policy_number: str | None = Field(default=None, description="Policy number")
    policy_type: str = Field(..., description="Policy type")
    carrier_name: str | None = Field(default=None, description="Carrier name")
    expiration_date: date = Field(..., description="Expiration date")
    days_until_expiration: int = Field(..., description="Days until expiration")
    severity: str = Field(..., description="Severity: critical, warning, info")
    annual_premium: Decimal | None = Field(default=None, description="Annual premium")


class ExpirationSummary(BaseModel):
    """Summary of expiring policies."""

    total_expiring: int = Field(default=0, description="Total expiring policies")
    total_premium_at_risk: Decimal = Field(
        default=Decimal("0"), description="Total premium at risk"
    )


class ExpirationTimelineResponse(BaseModel):
    """Response for expiration timeline endpoint."""

    expirations: list[ExpirationItem] = Field(
        default_factory=list, description="List of expiring policies"
    )
    summary: ExpirationSummary = Field(
        default_factory=ExpirationSummary, description="Expiration summary"
    )


# ---------------------------------------------------------------------------
# Dashboard Alerts
# ---------------------------------------------------------------------------


class AlertItem(BaseModel):
    """Single alert item."""

    id: str = Field(..., description="Alert ID")
    type: str = Field(..., description="Alert type: gap, expiration, compliance")
    severity: str = Field(..., description="Severity: critical, warning, info")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    property_id: str | None = Field(default=None, description="Related property ID")
    property_name: str | None = Field(
        default=None, description="Related property name"
    )
    created_at: datetime = Field(..., description="Alert creation time")
    action_url: str | None = Field(default=None, description="URL for action")


class AlertCounts(BaseModel):
    """Alert counts by severity."""

    critical: int = Field(default=0, description="Critical alerts")
    warning: int = Field(default=0, description="Warning alerts")
    info: int = Field(default=0, description="Info alerts")


class AlertsResponse(BaseModel):
    """Response for alerts endpoint."""

    alerts: list[AlertItem] = Field(default_factory=list, description="List of alerts")
    counts: AlertCounts = Field(default_factory=AlertCounts, description="Alert counts")
