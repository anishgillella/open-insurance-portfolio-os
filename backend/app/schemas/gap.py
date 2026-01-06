"""Schemas for coverage gaps and compliance."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# Gap Schemas


class GapBase(BaseModel):
    """Base gap schema with common fields."""

    gap_type: str = Field(..., description="Type of gap (underinsurance, high_deductible, etc.)")
    severity: str = Field(..., description="Severity level (critical, warning, info)")
    title: str = Field(..., description="Short title describing the gap")
    description: str | None = Field(None, description="Detailed description")
    coverage_name: str | None = Field(None, description="Name of affected coverage")
    current_value: str | None = Field(None, description="Current value/status")
    recommended_value: str | None = Field(None, description="Recommended value/action")


class GapListItem(GapBase):
    """Gap item for list responses."""

    id: str
    property_id: str
    property_name: str | None = None
    policy_id: str | None = None
    status: str = Field(..., description="Status (open, acknowledged, resolved)")
    detected_at: datetime
    gap_amount: Decimal | None = None

    class Config:
        from_attributes = True


class GapDetail(GapListItem):
    """Detailed gap information."""

    program_id: str | None = None
    resolution_notes: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    detection_method: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    # LLM Analysis Fields (auto-populated after gap detection)
    llm_enhanced_description: str | None = Field(None, description="AI-enhanced explanation")
    llm_risk_assessment: str | None = Field(None, description="AI risk analysis")
    llm_risk_score: int | None = Field(None, ge=1, le=10, description="AI risk score 1-10")
    llm_recommendations: list[str] | None = Field(None, description="AI recommendations")
    llm_potential_consequences: list[str] | None = Field(None, description="AI consequences")
    llm_industry_context: str | None = Field(None, description="AI industry context")
    llm_action_priority: str | None = Field(None, description="AI priority: immediate/short_term/medium_term")
    llm_estimated_impact: str | None = Field(None, description="AI estimated financial impact")
    llm_analyzed_at: datetime | None = Field(None, description="When LLM analysis was run")
    llm_model_used: str | None = Field(None, description="LLM model used for analysis")


class GapListResponse(BaseModel):
    """Response for gap list endpoint."""

    gaps: list[GapListItem]
    total_count: int
    summary: "GapSummary"


class GapSummary(BaseModel):
    """Summary of gaps by severity."""

    total: int = 0
    critical: int = 0
    warning: int = 0
    info: int = 0


class GapDetectRequest(BaseModel):
    """Request to trigger gap detection."""

    property_id: str | None = Field(None, description="Specific property ID (optional)")
    organization_id: str | None = Field(None, description="Organization ID (optional)")
    clear_existing: bool = Field(True, description="Clear existing open gaps before detection")


class GapDetectResponse(BaseModel):
    """Response from gap detection."""

    properties_checked: int
    gaps_detected: int
    gaps_by_type: dict[str, int]
    gaps_by_severity: dict[str, int]


class GapAcknowledgeRequest(BaseModel):
    """Request to acknowledge a gap."""

    notes: str | None = Field(None, description="Optional acknowledgment notes")


class GapResolveRequest(BaseModel):
    """Request to resolve a gap."""

    notes: str | None = Field(None, description="Resolution notes")


class GapActionResponse(BaseModel):
    """Response for gap actions (acknowledge, resolve)."""

    id: str
    status: str
    message: str


# Compliance Schemas


class ComplianceIssueSchema(BaseModel):
    """A single compliance issue."""

    check_name: str = Field(..., description="Name of the compliance check")
    severity: str = Field(..., description="Severity (critical, warning, info)")
    message: str = Field(..., description="Description of the issue")
    current_value: str | None = None
    required_value: str | None = None


class ComplianceCheckResult(BaseModel):
    """Result of a compliance check."""

    property_id: str
    lender_requirement_id: str | None = None
    lender_name: str | None = None
    template_name: str
    status: str = Field(..., description="Overall status (compliant, non_compliant, partial)")
    is_compliant: bool
    issues: list[ComplianceIssueSchema]
    checked_at: datetime | None = None


class PropertyComplianceResponse(BaseModel):
    """Response for property compliance endpoint."""

    property_id: str
    property_name: str
    compliance_checks: list[ComplianceCheckResult]
    overall_status: str = Field(..., description="Worst status across all checks")
    total_issues: int


class LenderRequirementBase(BaseModel):
    """Base lender requirement schema."""

    loan_number: str | None = None
    loan_amount: Decimal | None = None
    min_property_limit: Decimal | None = None
    min_gl_limit: Decimal | None = None
    min_umbrella_limit: Decimal | None = None
    max_deductible_amount: Decimal | None = None
    max_deductible_pct: float | None = None
    requires_flood: bool = False
    requires_earthquake: bool = False
    requires_terrorism: bool = False


class LenderRequirementCreate(LenderRequirementBase):
    """Schema for creating a lender requirement."""

    lender_id: str | None = None


class LenderRequirementUpdate(LenderRequirementBase):
    """Schema for updating a lender requirement."""

    pass


class LenderRequirementResponse(LenderRequirementBase):
    """Response schema for lender requirement."""

    id: str
    property_id: str
    lender_id: str | None = None
    lender_name: str | None = None
    compliance_status: str | None = None
    compliance_checked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ComplianceTemplateInfo(BaseModel):
    """Information about a compliance template."""

    name: str = Field(..., description="Template identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Template description")


class ComplianceTemplatesResponse(BaseModel):
    """Response listing available compliance templates."""

    templates: list[ComplianceTemplateInfo]


class ComplianceCheckRequest(BaseModel):
    """Request to run compliance check."""

    template_name: str | None = Field(None, description="Template to check against (optional)")
    create_gaps: bool = Field(True, description="Create gap records for issues")


# LLM-Enhanced Gap Analysis Schemas


class GapAnalysisRequest(BaseModel):
    """Request for LLM-enhanced gap analysis."""

    include_recommendations: bool = Field(True, description="Include actionable recommendations")
    include_industry_context: bool = Field(True, description="Include industry benchmarks and context")


class GapAnalysisResult(BaseModel):
    """Result of LLM-enhanced gap analysis."""

    gap_id: str
    enhanced_description: str = Field(..., description="AI-enhanced explanation of the gap")
    risk_assessment: str = Field(..., description="Detailed risk analysis")
    risk_score: int = Field(..., ge=1, le=10, description="Risk score from 1-10")
    recommendations: list[str] = Field(default_factory=list, description="Actionable recommendations")
    potential_consequences: list[str] = Field(default_factory=list, description="What could happen if not addressed")
    industry_context: str = Field(..., description="How this compares to industry standards")
    action_priority: str = Field(..., description="immediate, short_term, or medium_term")
    estimated_impact: str = Field(..., description="Estimated financial impact")
    related_gaps: list[str] = Field(default_factory=list, description="IDs of related gaps")
    analysis_timestamp: datetime
    model_used: str
    latency_ms: int


class GapWithAnalysis(GapDetail):
    """Gap detail with LLM analysis included."""

    analysis: GapAnalysisResult | None = None


class PriorityAction(BaseModel):
    """A prioritized action item."""

    action: str
    priority: str = Field(..., description="immediate, short_term, or medium_term")
    estimated_effort: str | None = None
    expected_benefit: str | None = None


class CrossPolicyConflict(BaseModel):
    """A detected conflict between policies."""

    conflict_type: str
    description: str
    policies_involved: list[str] = Field(default_factory=list)
    severity: str


class PropertyAnalysisRequest(BaseModel):
    """Request for property-level gap analysis."""

    analyze_all_gaps: bool = Field(True, description="Analyze each gap individually first")
    include_conflicts: bool = Field(True, description="Detect cross-policy conflicts")
    include_portfolio_insights: bool = Field(True, description="Include portfolio-level patterns")


class PropertyAnalysisResult(BaseModel):
    """Result of property-level LLM analysis."""

    property_id: str
    property_name: str
    overall_risk_score: int = Field(..., ge=1, le=10, description="Overall risk score 1-10")
    risk_grade: str = Field(..., description="Letter grade A-F")
    executive_summary: str = Field(..., description="Brief summary for executives")
    gap_analyses: list[GapAnalysisResult] = Field(default_factory=list)
    cross_policy_conflicts: list[CrossPolicyConflict] = Field(default_factory=list)
    coverage_recommendations: list[str] = Field(default_factory=list)
    priority_actions: list[PriorityAction] = Field(default_factory=list)
    portfolio_insights: list[str] = Field(default_factory=list)
    analysis_timestamp: datetime
    model_used: str
    total_latency_ms: int


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status."""

    status: str = Field(..., description="pending, in_progress, completed, failed")
    message: str | None = None
    result: PropertyAnalysisResult | GapAnalysisResult | None = None


# Batch Compliance Schemas


class BatchComplianceRequest(BaseModel):
    """Request for batch compliance check across multiple properties."""

    property_ids: list[str] = Field(..., description="List of property IDs to check")
    create_gaps: bool = Field(False, description="Create gap records for issues")


class BatchComplianceItem(BaseModel):
    """Compliance result for a single property in batch response."""

    property_id: str
    property_name: str
    overall_status: str = Field(..., description="compliant, non_compliant, partial, no_requirements")
    total_issues: int = 0
    compliance_checks: list[ComplianceCheckResult] = Field(default_factory=list)


class BatchComplianceResponse(BaseModel):
    """Response for batch compliance check."""

    results: list[BatchComplianceItem]
    total_properties: int
    compliant_count: int
    non_compliant_count: int
    no_requirements_count: int
