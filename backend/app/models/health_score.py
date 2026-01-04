"""Health score model - Insurance Health Score tracking with LLM-generated analysis."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.property import Property


class HealthScore(BaseModel):
    """Insurance Health Score model for tracking property insurance health over time.

    The Health Score is a proprietary 0-100 metric measuring how well-protected
    a property is, based on 6 components evaluated by LLM:
    - Coverage Adequacy (25 points)
    - Policy Currency (20 points)
    - Deductible Risk (15 points)
    - Coverage Breadth (15 points)
    - Lender Compliance (15 points)
    - Documentation Quality (10 points)
    """

    __tablename__ = "health_scores"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Score Data
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    grade: Mapped[str] = mapped_column(String(1), nullable=False)  # A, B, C, D, F

    # Component Scores (JSONB for flexibility)
    # Structure: {
    #   "coverage_adequacy": {"score": 18.5, "max": 25, "reasoning": "...", "key_findings": [...], "concerns": [...]},
    #   "policy_currency": {"score": 20, "max": 20, "reasoning": "...", ...},
    #   ... all 6 components
    # }
    components: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # LLM-Generated Summary & Recommendations
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Structure: [{"priority": "high", "action": "...", "impact": "...", "component": "..."}]
    risk_factors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    strengths: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Trend Data
    trend_direction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Values: improving, declining, stable, new
    trend_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_score_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("health_scores.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Calculation Metadata
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    calculation_trigger: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Values: ingestion, gap_resolved, manual, scheduled

    # LLM Metadata
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship(
        "Property", back_populates="health_scores"
    )
    previous_score: Mapped["HealthScore | None"] = relationship(
        "HealthScore",
        remote_side="HealthScore.id",
        foreign_keys=[previous_score_id],
    )

    def __repr__(self) -> str:
        return f"<HealthScore(id={self.id}, property_id={self.property_id}, score={self.score}, grade={self.grade})>"
