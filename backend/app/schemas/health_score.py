"""Schemas for Insurance Health Score."""

from datetime import datetime

from pydantic import BaseModel, Field


class ComponentScoreSchema(BaseModel):
    """Score for a single health score component."""

    score: float = Field(..., ge=0, description="Component score")
    max: float = Field(..., ge=0, description="Maximum possible score")
    percentage: float = Field(..., ge=0, le=100, description="Score as percentage")
    reasoning: str = Field(..., description="LLM reasoning for score")
    key_findings: list[str] = Field(default_factory=list, description="Key positive findings")
    concerns: list[str] = Field(default_factory=list, description="Identified concerns")


class RecommendationSchema(BaseModel):
    """LLM-generated recommendation."""

    priority: str = Field(..., description="Priority: high, medium, low")
    action: str = Field(..., description="Specific action to take")
    impact: str = Field(..., description="Expected improvement")
    component: str = Field(..., description="Affected component")


class TrendSchema(BaseModel):
    """Score trend information."""

    direction: str = Field(..., description="Trend: improving, declining, stable, new")
    delta: int | None = Field(None, description="Change from previous score")
    previous_score: int | None = Field(None, description="Previous score value")
    previous_date: datetime | None = Field(None, description="Date of previous score")


class HealthScoreResponse(BaseModel):
    """Response for property health score endpoint."""

    property_id: str
    property_name: str
    score: int = Field(..., ge=0, le=100, description="Total health score")
    grade: str = Field(..., description="Letter grade: A, B, C, D, F")
    components: dict[str, ComponentScoreSchema] = Field(
        ..., description="Score breakdown by component"
    )
    executive_summary: str = Field(..., description="LLM executive summary")
    recommendations: list[RecommendationSchema] = Field(
        default_factory=list, description="LLM recommendations"
    )
    risk_factors: list[str] = Field(default_factory=list, description="Identified risk factors")
    strengths: list[str] = Field(default_factory=list, description="Identified strengths")
    trend: TrendSchema
    calculated_at: datetime
    model_used: str | None = None
    latency_ms: int | None = None

    class Config:
        from_attributes = True


class HistoryEntrySchema(BaseModel):
    """Single entry in health score history."""

    date: str  # ISO format date
    score: int
    grade: str


class TrendAnalysisSchema(BaseModel):
    """Trend analysis over time."""

    direction: str
    first_score: int | None = None
    last_score: int | None = None
    change: int | None = None
    note: str | None = None


class HealthScoreHistoryResponse(BaseModel):
    """Response for health score history endpoint."""

    property_id: str
    current_score: int | None
    history: list[HistoryEntrySchema]
    trend_analysis: TrendAnalysisSchema


class PortfolioPropertyScoreSchema(BaseModel):
    """Property score summary for portfolio."""

    id: str
    name: str
    score: int
    grade: str
    trend: str | None = None


class PortfolioHealthScoreResponse(BaseModel):
    """Response for portfolio health score endpoint."""

    portfolio_score: int = Field(..., ge=0, le=100, description="Average portfolio score")
    portfolio_grade: str = Field(..., description="Portfolio letter grade")
    property_count: int = Field(..., ge=0, description="Number of properties")
    distribution: dict[str, int] = Field(..., description="Properties per grade: A, B, C, D, F")
    component_averages: dict[str, float] = Field(
        default_factory=dict, description="Average score per component"
    )
    trend: TrendSchema
    properties: list[PortfolioPropertyScoreSchema] = Field(
        default_factory=list, description="Individual property scores"
    )
    calculated_at: datetime


class RecalculateRequest(BaseModel):
    """Request to recalculate health score."""

    force: bool = Field(False, description="Force recalculation even if recent score exists")
    use_external_risk_data: bool = Field(
        True, description="Fetch external risk data from Parallel AI"
    )


class RecalculateResponse(BaseModel):
    """Response from health score recalculation."""

    property_id: str
    score: int
    grade: str
    previous_score: int | None = None
    change: int | None = None
    trend_direction: str
    calculated_at: datetime
    latency_ms: int
    external_risk_data: dict | None = Field(
        None, description="External risk data from Parallel AI"
    )
    risk_enrichment_latency_ms: int | None = Field(
        None, description="Latency of external risk data fetch in milliseconds"
    )
