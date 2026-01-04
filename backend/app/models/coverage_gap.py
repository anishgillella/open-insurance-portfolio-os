"""Coverage gap model - detected coverage gaps and issues."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CoverageGap(BaseModel):
    """Coverage gap model for detected coverage issues."""

    __tablename__ = "coverage_gaps"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("insurance_programs.id", ondelete="SET NULL"),
        nullable=True,
    )
    policy_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("policies.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Gap Details
    gap_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Specifics
    coverage_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recommended_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gap_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Detection
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    detection_method: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # LLM Analysis Fields
    llm_enhanced_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_risk_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_recommendations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    llm_potential_consequences: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    llm_industry_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_action_priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    llm_estimated_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship(  # noqa: F821
        "Property", back_populates="coverage_gaps"
    )
    program: Mapped["InsuranceProgram | None"] = relationship(  # noqa: F821
        "InsuranceProgram", back_populates="coverage_gaps"
    )
    policy: Mapped["Policy | None"] = relationship(  # noqa: F821
        "Policy", back_populates="coverage_gaps"
    )

    def __repr__(self) -> str:
        return f"<CoverageGap(id={self.id}, gap_type={self.gap_type})>"
