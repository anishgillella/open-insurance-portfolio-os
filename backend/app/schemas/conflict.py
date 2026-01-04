"""Schemas for coverage conflicts."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ConflictSummarySchema(BaseModel):
    """Summary of conflicts by severity."""

    total_conflicts: int = 0
    critical: int = 0
    warning: int = 0
    info: int = 0


class AffectedPolicySchema(BaseModel):
    """Policy affected by a conflict."""

    id: str
    policy_number: str | None = None
    policy_type: str | None = None


class ConflictListItem(BaseModel):
    """Conflict item for list responses."""

    id: str
    conflict_type: str = Field(..., description="Type of conflict")
    severity: str = Field(..., description="Severity: critical, warning, info")
    title: str = Field(..., description="Brief title")
    description: str | None = Field(None, description="Detailed description")
    affected_policy_ids: list[str] = Field(default_factory=list, description="IDs of affected policies")
    gap_amount: Decimal | None = Field(None, description="Financial gap amount if applicable")
    potential_savings: Decimal | None = Field(None, description="Potential savings if overlap")
    recommendation: str | None = Field(None, description="Recommended action")
    status: str = Field(..., description="Status: open, acknowledged, resolved")
    detected_at: datetime

    class Config:
        from_attributes = True


class ConflictDetail(ConflictListItem):
    """Detailed conflict information."""

    property_id: str
    detection_method: str = Field(..., description="How detected: llm, rule, hybrid")
    llm_reasoning: str | None = Field(None, description="LLM reasoning for detection")
    llm_analysis: dict | None = Field(None, description="Full LLM analysis")
    llm_analyzed_at: datetime | None = None
    llm_model_used: str | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    acknowledged_notes: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ConflictListResponse(BaseModel):
    """Response for conflict list endpoint."""

    property_id: str
    property_name: str
    analysis_date: datetime
    summary: ConflictSummarySchema
    conflicts: list[ConflictListItem]
    cross_policy_analysis: str | None = None
    portfolio_recommendations: list[str] = Field(default_factory=list)


class AnalyzeConflictsRequest(BaseModel):
    """Request to trigger conflict analysis."""

    include_ai_analysis: bool = Field(True, description="Use LLM for detection")
    force_refresh: bool = Field(False, description="Clear existing and re-analyze")


class AnalyzeConflictsResponse(BaseModel):
    """Response from conflict analysis."""

    property_id: str
    analysis_id: str | None = None
    status: str = "completed"
    conflicts_found: int
    summary: ConflictSummarySchema
    cross_policy_analysis: str | None = None
    portfolio_recommendations: list[str] = Field(default_factory=list)
    duration_ms: int


class AcknowledgeRequest(BaseModel):
    """Request to acknowledge a conflict."""

    notes: str | None = Field(None, description="Optional acknowledgment notes")


class ResolveRequest(BaseModel):
    """Request to resolve a conflict."""

    notes: str | None = Field(None, description="Resolution notes")


class ConflictActionResponse(BaseModel):
    """Response from conflict action (acknowledge/resolve)."""

    id: str
    status: str
    message: str
    updated_at: datetime
