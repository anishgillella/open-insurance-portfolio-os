"""Schemas for document completeness."""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentStatusSchema(BaseModel):
    """Status of a single document type."""

    type: str = Field(..., description="Document type identifier")
    label: str = Field(..., description="Human-readable label")
    status: str = Field(..., description="Status: present, missing, or not_applicable")
    document_id: str | None = Field(None, description="Document ID if present")
    filename: str | None = Field(None, description="Filename if present")
    importance: str | None = Field(None, description="Why this document matters")
    uploaded_at: datetime | None = Field(None, description="When document was uploaded")


class MissingDocumentImpactSchema(BaseModel):
    """LLM-generated impact analysis for a missing document."""

    document: str = Field(..., description="Document type")
    impact: str = Field(..., description="Impact of missing this document")
    priority: str = Field(..., description="Priority to obtain: high, medium, low")
    reason: str = Field(..., description="Why this priority level")


class CompletenessDataSchema(BaseModel):
    """Completeness calculation data."""

    percentage: float = Field(..., ge=0, le=100, description="Completeness percentage")
    grade: str = Field(..., description="Letter grade: A, B, C, D, F")
    required_present: int = Field(..., ge=0, description="Number of required docs present")
    required_total: int = Field(..., ge=0, description="Total required docs")
    optional_present: int = Field(..., ge=0, description="Number of optional docs present")
    optional_total: int = Field(..., ge=0, description="Total optional docs")


class CompletenessResponse(BaseModel):
    """Response for property completeness endpoint."""

    property_id: str
    property_name: str
    completeness: CompletenessDataSchema
    documents: dict  # required: [...], optional: [...]
    # LLM-enhanced fields
    missing_document_impacts: list[MissingDocumentImpactSchema] | None = None
    overall_risk_summary: str | None = None
    recommended_actions: list[str] | None = None
    llm_analyzed: bool = False
    calculated_at: datetime

    class Config:
        from_attributes = True


class PortfolioCompletenessPropertySchema(BaseModel):
    """Property summary for portfolio completeness."""

    id: str
    name: str
    completeness: float
    grade: str
    missing_required: int
    missing_optional: int


class MissingDocumentSummarySchema(BaseModel):
    """Summary of commonly missing documents."""

    type: str
    label: str
    missing_count: int
    percentage_missing: float


class PortfolioCompletenessResponse(BaseModel):
    """Response for portfolio completeness summary."""

    summary: dict  # average_completeness, fully_complete_count, etc.
    distribution: dict[str, int]  # A: 1, B: 2, etc.
    most_common_missing: list[MissingDocumentSummarySchema]
    properties: list[PortfolioCompletenessPropertySchema]


class MarkNotApplicableRequest(BaseModel):
    """Request to mark a document as not applicable."""

    document_type: str = Field(..., description="Document type to mark as N/A")
    reason: str = Field(..., description="Reason why document is not applicable")


class MarkNotApplicableResponse(BaseModel):
    """Response after marking document as N/A."""

    property_id: str
    document_type: str
    status: str = "not_applicable"
    reason: str
    marked_at: datetime
