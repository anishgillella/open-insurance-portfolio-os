"""Schemas for Renewal Intelligence Engine (Phase 4.4)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# =============================================================================
# Forecast Schemas
# =============================================================================


class FactorBreakdownSchema(BaseModel):
    """Breakdown of a single forecasting factor."""

    weight: float = Field(..., ge=0, le=1, description="Factor weight (0-1)")
    impact: float = Field(..., description="Impact on premium change (%)")
    reasoning: str = Field(..., description="LLM reasoning for impact")


class ForecastRangeSchema(BaseModel):
    """LLM-predicted premium range."""

    low: Decimal = Field(..., description="Lower bound estimate")
    mid: Decimal = Field(..., description="Mid-point estimate")
    high: Decimal = Field(..., description="Upper bound estimate")


class RenewalForecastResponse(BaseModel):
    """Response for renewal forecast endpoint."""

    id: str
    property_id: str
    property_name: str
    program_id: str | None = None
    policy_id: str | None = None

    # Renewal context
    renewal_year: int
    current_expiration_date: date
    days_until_expiration: int
    current_premium: Decimal | None = None

    # Rule-based estimate
    rule_based_estimate: Decimal | None = Field(
        None, description="Deterministic point estimate"
    )
    rule_based_change_pct: float | None = Field(
        None, description="Percentage change from current premium"
    )

    # LLM predictions
    llm_prediction: ForecastRangeSchema | None = Field(
        None, description="LLM-predicted premium range"
    )
    llm_confidence_score: int | None = Field(
        None, ge=0, le=100, description="Confidence in prediction (0-100)"
    )

    # Factor breakdown
    factor_breakdown: dict[str, FactorBreakdownSchema] | None = Field(
        None, description="Factor-by-factor analysis"
    )

    # LLM analysis
    reasoning: str | None = Field(None, description="LLM reasoning narrative")
    market_context: str | None = Field(None, description="Market context analysis")
    negotiation_points: list[str] = Field(
        default_factory=list, description="Suggested negotiation leverage"
    )

    # Metadata
    status: str = Field(..., description="Forecast status: active, superseded, expired")
    forecast_date: datetime
    model_used: str | None = None
    latency_ms: int | None = None

    class Config:
        from_attributes = True


class ForecastListItem(BaseModel):
    """Summary item for forecast list."""

    id: str
    property_id: str
    property_name: str
    renewal_year: int
    current_expiration_date: date
    days_until_expiration: int
    current_premium: Decimal | None = None
    llm_predicted_mid: Decimal | None = None
    llm_confidence_score: int | None = None
    status: str
    forecast_date: datetime

    class Config:
        from_attributes = True


class ForecastListResponse(BaseModel):
    """Response for forecast list endpoint."""

    forecasts: list[ForecastListItem]
    total_count: int


class GenerateForecastRequest(BaseModel):
    """Request to generate a new forecast."""

    force: bool = Field(False, description="Force regeneration even if recent exists")
    include_market_context: bool = Field(
        True, description="Include market context analysis"
    )


class GenerateForecastResponse(BaseModel):
    """Response from forecast generation."""

    id: str
    property_id: str
    status: str
    message: str
    forecast: RenewalForecastResponse | None = None


# =============================================================================
# Timeline & Alert Schemas
# =============================================================================


class RenewalAlertResponse(BaseModel):
    """Response for a single renewal alert."""

    id: str
    property_id: str
    property_name: str
    policy_id: str
    policy_number: str | None = None
    policy_type: str | None = None
    carrier_name: str | None = None

    # Alert details
    threshold_days: int
    days_until_expiration: int
    expiration_date: datetime
    severity: str = Field(..., description="info, warning, critical")
    title: str
    message: str | None = None

    # Status
    status: str = Field(..., description="pending, acknowledged, resolved, expired")
    triggered_at: datetime
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    resolved_at: datetime | None = None

    # LLM enhancement
    llm_priority_score: int | None = Field(
        None, ge=1, le=10, description="Complexity/priority rating"
    )
    llm_renewal_strategy: str | None = None
    llm_key_actions: list[str] = Field(default_factory=list)

    created_at: datetime

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Response for alert list endpoint."""

    alerts: list[RenewalAlertResponse]
    total_count: int
    summary: "AlertSummarySchema"


class AlertSummarySchema(BaseModel):
    """Summary of alerts by severity."""

    total: int = Field(0, description="Total active alerts")
    critical: int = Field(0, description="Critical alerts (30 days)")
    warning: int = Field(0, description="Warning alerts (60 days)")
    info: int = Field(0, description="Info alerts (90 days)")
    pending: int = Field(0, description="Pending acknowledgement")


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert."""

    notes: str | None = Field(None, description="Acknowledgement notes")


class ResolveAlertRequest(BaseModel):
    """Request to resolve an alert."""

    notes: str | None = Field(None, description="Resolution notes")


class AlertActionResponse(BaseModel):
    """Response from alert action."""

    id: str
    status: str
    message: str
    updated_at: datetime


class AlertConfigSchema(BaseModel):
    """Alert configuration for a property."""

    property_id: str
    thresholds: list[int] = Field(
        default=[90, 60, 30], description="Days before expiration to trigger alerts"
    )
    enabled: bool = Field(True, description="Whether alerts are enabled")
    severity_mapping: dict[str, str] | None = Field(
        None, description="Custom severity per threshold"
    )


class UpdateAlertConfigRequest(BaseModel):
    """Request to update alert configuration."""

    thresholds: list[int] | None = Field(
        None, description="New thresholds (e.g., [120, 90, 60, 30])"
    )
    enabled: bool | None = None
    severity_mapping: dict[str, str] | None = None


class AlertConfigResponse(BaseModel):
    """Response for alert configuration."""

    property_id: str
    thresholds: list[int]
    enabled: bool
    severity_mapping: dict[str, str] | None = None
    message: str | None = None


# =============================================================================
# Renewal Timeline Schemas
# =============================================================================


class TimelineItemSchema(BaseModel):
    """Single item in renewal timeline."""

    property_id: str
    property_name: str
    policy_id: str
    policy_number: str | None = None
    policy_type: str
    carrier_name: str | None = None
    expiration_date: date
    days_until_expiration: int
    severity: str  # info, warning, critical
    current_premium: Decimal | None = None
    predicted_premium: Decimal | None = None
    has_forecast: bool = False
    has_active_alerts: bool = False
    alert_count: int = 0


class TimelineSummarySchema(BaseModel):
    """Summary of renewal timeline."""

    total_renewals: int
    expiring_30_days: int
    expiring_60_days: int
    expiring_90_days: int
    total_premium_at_risk: Decimal


class RenewalTimelineResponse(BaseModel):
    """Response for renewal timeline endpoint."""

    timeline: list[TimelineItemSchema]
    summary: TimelineSummarySchema


# =============================================================================
# Document Readiness Schemas
# =============================================================================


class DocumentStatusSchema(BaseModel):
    """Status of a single document for renewal."""

    type: str = Field(..., description="Document type identifier")
    label: str = Field(..., description="Human-readable label")
    status: str = Field(..., description="found, missing, stale, not_applicable")
    document_id: str | None = None
    filename: str | None = None
    age_days: int | None = None
    verified: bool = False
    extracted_data: dict | None = Field(
        None, description="Key data extracted by LLM"
    )
    issues: list[str] = Field(default_factory=list)


class ReadinessIssueSchema(BaseModel):
    """Issue identified in readiness assessment."""

    severity: str = Field(..., description="critical, warning, info")
    issue: str = Field(..., description="Issue description")
    impact: str = Field(..., description="Impact on renewal")


class ReadinessRecommendationSchema(BaseModel):
    """Recommendation for improving readiness."""

    priority: str = Field(..., description="high, medium, low")
    action: str = Field(..., description="Action to take")
    deadline: str | None = Field(None, description="Suggested deadline")


class TimelineMilestoneSchema(BaseModel):
    """Milestone in renewal timeline."""

    days_before_renewal: int
    action: str
    status: str = Field(..., description="completed, missed, upcoming")


class RenewalReadinessResponse(BaseModel):
    """Response for renewal readiness endpoint."""

    property_id: str
    property_name: str
    target_renewal_date: datetime
    days_until_renewal: int

    # Readiness score
    readiness_score: int = Field(..., ge=0, le=100)
    readiness_grade: str = Field(..., description="A, B, C, D, F")

    # Document status
    required_documents: list[DocumentStatusSchema]
    recommended_documents: list[DocumentStatusSchema]

    # LLM verification
    verification_summary: str | None = None
    data_consistency_issues: list[str] = Field(default_factory=list)

    # Issues and recommendations
    issues: list[ReadinessIssueSchema] = Field(default_factory=list)
    recommendations: list[ReadinessRecommendationSchema] = Field(default_factory=list)

    # Timeline
    milestones: list[TimelineMilestoneSchema] = Field(default_factory=list)

    # Metadata
    assessment_date: datetime
    status: str
    model_used: str | None = None
    latency_ms: int | None = None

    class Config:
        from_attributes = True


class AssessReadinessRequest(BaseModel):
    """Request to assess renewal readiness."""

    force: bool = Field(False, description="Force reassessment")
    verify_contents: bool = Field(
        True, description="Use LLM to verify document contents"
    )


class PortfolioReadinessPropertySchema(BaseModel):
    """Property readiness for portfolio view."""

    id: str
    name: str
    readiness_score: int
    readiness_grade: str
    days_until_renewal: int
    missing_required: int
    missing_recommended: int


class PortfolioReadinessResponse(BaseModel):
    """Response for portfolio readiness endpoint."""

    average_readiness: int
    average_grade: str
    property_count: int
    distribution: dict[str, int] = Field(
        default_factory=dict, description="Properties per grade"
    )
    common_missing_docs: list[str] = Field(default_factory=list)
    properties: list[PortfolioReadinessPropertySchema]


# =============================================================================
# Market Context Schemas
# =============================================================================


class PolicyAnalysisSchema(BaseModel):
    """Analysis of policy terms from structured data."""

    key_exclusions: list[str] = Field(default_factory=list)
    notable_sublimits: list[dict] = Field(default_factory=list)
    unusual_terms: list[str] = Field(default_factory=list)
    coverage_strengths: list[str] = Field(default_factory=list)
    coverage_weaknesses: list[str] = Field(default_factory=list)


class YoYChangeSchema(BaseModel):
    """Year-over-year change analysis."""

    premium_change_pct: float | None = None
    limit_changes: list[dict] = Field(default_factory=list)
    deductible_changes: list[dict] = Field(default_factory=list)
    new_exclusions: list[str] = Field(default_factory=list)
    removed_coverages: list[str] = Field(default_factory=list)


class NegotiationRecommendationSchema(BaseModel):
    """Recommendation for renewal negotiation."""

    action: str
    priority: str = Field(..., description="high, medium, low")
    rationale: str


class MarketContextResponse(BaseModel):
    """Response for market context endpoint."""

    property_id: str
    property_name: str
    analysis_date: datetime
    valid_until: datetime

    # Market assessment
    market_condition: str = Field(
        ..., description="hardening, softening, stable, volatile"
    )
    market_condition_reasoning: str | None = None

    # Property-specific analysis
    property_risk_profile: str | None = None
    carrier_relationship_assessment: str | None = None

    # Policy analysis
    policy_analysis: PolicyAnalysisSchema | None = None
    yoy_changes: YoYChangeSchema | None = None

    # Negotiation intelligence
    negotiation_leverage: list[str] = Field(default_factory=list)
    negotiation_recommendations: list[NegotiationRecommendationSchema] = Field(
        default_factory=list
    )

    # Risk insights
    risk_insights: list[str] = Field(default_factory=list)

    # Executive summary
    executive_summary: str | None = None

    # Status and metadata
    status: str
    model_used: str | None = None
    latency_ms: int | None = None

    class Config:
        from_attributes = True


class AnalyzeMarketContextRequest(BaseModel):
    """Request to analyze market context."""

    force: bool = Field(False, description="Force reanalysis")
    include_yoy: bool = Field(True, description="Include year-over-year analysis")
    include_negotiation: bool = Field(True, description="Include negotiation recommendations")


# =============================================================================
# Comprehensive Renewal Summary
# =============================================================================


class RenewalSummaryResponse(BaseModel):
    """Comprehensive renewal summary for a property."""

    property_id: str
    property_name: str

    # Timeline
    next_expiration_date: date | None = None
    days_until_expiration: int | None = None

    # Forecast summary
    forecast: RenewalForecastResponse | None = None

    # Readiness summary
    readiness_score: int | None = None
    readiness_grade: str | None = None
    missing_documents: int = 0

    # Market context summary
    market_condition: str | None = None
    negotiation_points: list[str] = Field(default_factory=list)

    # Alerts summary
    active_alerts: int = 0
    critical_alerts: int = 0

    # Overall status
    renewal_status: str = Field(
        ..., description="on_track, needs_attention, at_risk, expired"
    )
    priority_actions: list[str] = Field(default_factory=list)


# =============================================================================
# Policy Comparison Schemas (Phase 4.4.2)
# =============================================================================


class CoverageComparisonSchema(BaseModel):
    """Comparison of a single coverage between two policies."""

    coverage_name: str
    status: str = Field(..., description="added, removed, changed, unchanged")

    # Policy A (base/previous)
    policy_a_limit: Decimal | None = None
    policy_a_deductible: Decimal | None = None
    policy_a_sublimit: Decimal | None = None

    # Policy B (compare/current)
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


class PolicySummarySchema(BaseModel):
    """Summary of a policy for comparison."""

    id: str
    policy_number: str | None = None
    policy_type: str
    carrier_name: str | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    premium: Decimal | None = None
    total_limit: Decimal | None = None
    coverage_count: int = 0


class PolicyComparisonResponse(BaseModel):
    """Response for policy-to-policy comparison."""

    comparison_id: str
    comparison_type: str = Field(..., description="yoy_renewal, arbitrary, quote_comparison")
    comparison_date: datetime

    # Policies being compared
    policy_a: PolicySummarySchema = Field(..., description="Base/previous policy")
    policy_b: PolicySummarySchema = Field(..., description="Compare/current policy")

    # Premium comparison
    premium_change: Decimal | None = None
    premium_change_pct: float | None = None

    # Coverage comparison
    coverages_added: list[str] = Field(default_factory=list)
    coverages_removed: list[str] = Field(default_factory=list)
    coverages_changed: list[CoverageComparisonSchema] = Field(default_factory=list)
    coverages_unchanged: list[str] = Field(default_factory=list)

    # Limit/Deductible summary
    total_limit_change: Decimal | None = None
    total_limit_change_pct: float | None = None
    avg_deductible_change_pct: float | None = None

    # LLM Analysis
    executive_summary: str | None = None
    key_changes: list[str] = Field(default_factory=list)
    risk_implications: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    # Metadata
    model_used: str | None = None
    latency_ms: int | None = None

    class Config:
        from_attributes = True


class ProgramComparisonResponse(BaseModel):
    """Response for program-to-program (year-over-year) comparison."""

    comparison_id: str
    property_id: str
    property_name: str
    comparison_date: datetime

    # Programs being compared
    program_a_year: int = Field(..., description="Base/previous year")
    program_b_year: int = Field(..., description="Compare/current year")
    program_a_id: str
    program_b_id: str

    # Aggregate premium comparison
    total_premium_a: Decimal | None = None
    total_premium_b: Decimal | None = None
    premium_change: Decimal | None = None
    premium_change_pct: float | None = None

    # Aggregate TIV comparison
    total_insured_value_a: Decimal | None = None
    total_insured_value_b: Decimal | None = None
    tiv_change: Decimal | None = None
    tiv_change_pct: float | None = None

    # Policy-level comparisons
    policy_comparisons: list[PolicyComparisonResponse] = Field(default_factory=list)

    # Policies added/removed
    policies_added: list[PolicySummarySchema] = Field(default_factory=list)
    policies_removed: list[PolicySummarySchema] = Field(default_factory=list)

    # LLM Analysis
    executive_summary: str | None = None
    key_changes: list[str] = Field(default_factory=list)
    coverage_gaps_identified: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    # Metadata
    model_used: str | None = None
    latency_ms: int | None = None

    class Config:
        from_attributes = True


class ComparePoliciesRequest(BaseModel):
    """Request to compare two policies."""

    policy_a_id: str = Field(..., description="Base policy ID")
    policy_b_id: str = Field(..., description="Compare policy ID")
    allow_cross_type: bool = Field(
        False, description="Allow comparing different policy types"
    )
    include_llm_analysis: bool = Field(
        True, description="Include LLM-generated insights"
    )


class CompareProgramsRequest(BaseModel):
    """Request to compare two programs (year-over-year)."""

    property_id: str
    program_a_year: int | None = Field(
        None, description="Base year (defaults to previous year)"
    )
    program_b_year: int | None = Field(
        None, description="Compare year (defaults to current year)"
    )
    include_policy_details: bool = Field(
        True, description="Include individual policy comparisons"
    )
    include_llm_analysis: bool = Field(
        True, description="Include LLM-generated insights"
    )


class ComparisonListItem(BaseModel):
    """Summary item for comparison history."""

    comparison_id: str
    comparison_type: str
    property_id: str | None = None
    property_name: str | None = None
    policy_a_summary: str
    policy_b_summary: str
    premium_change_pct: float | None = None
    comparison_date: datetime


class ComparisonListResponse(BaseModel):
    """Response for comparison history."""

    comparisons: list[ComparisonListItem]
    total_count: int


# =============================================================================
# Batch Forecast Schemas
# =============================================================================


class BatchForecastRequest(BaseModel):
    """Request for batch forecast retrieval across multiple properties."""

    property_ids: list[str] = Field(..., description="List of property IDs to get forecasts for")


class BatchForecastItem(BaseModel):
    """Forecast summary for a single property in batch response."""

    property_id: str
    property_name: str
    has_forecast: bool = False
    current_premium: Decimal | None = None
    current_expiration_date: date | None = None
    days_until_expiration: int | None = None
    forecast_low: Decimal | None = None
    forecast_mid: Decimal | None = None
    forecast_high: Decimal | None = None
    forecast_change_pct: float | None = None
    confidence_score: int | None = None
    forecast_date: datetime | None = None


class BatchForecastResponse(BaseModel):
    """Response for batch forecast retrieval."""

    forecasts: list[BatchForecastItem]
    total_properties: int
    properties_with_forecasts: int
    total_premium_at_risk: Decimal | None = None
    avg_forecast_change_pct: float | None = None
