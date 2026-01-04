"""Coverage conflict model - cross-policy conflict detection with LLM analysis."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.property import Property


class CoverageConflict(BaseModel):
    """Coverage conflict model for cross-policy issues detected by LLM.

    Conflict Types:
    - excess_primary_gap: Umbrella doesn't attach to underlying coverage
    - entity_mismatch: Different named insureds across policies
    - valuation_conflict: Mixed RCV/ACV valuation methods
    - coverage_overlap: Duplicate coverage (wasting premium)
    - limit_tower_gap: Coverage limits don't stack properly
    - exclusion_conflict: One policy covers what another excludes
    """

    __tablename__ = "coverage_conflicts"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Conflict Details
    conflict_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Values: critical, warning, info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Affected Policies (JSONB array of policy IDs)
    affected_policy_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Conflict Specifics
    gap_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    potential_savings: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # LLM Analysis
    detection_method: Mapped[str] = mapped_column(String(20), default="llm", nullable=False)
    # Values: llm, rule, hybrid
    llm_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Structure: Full LLM response context for debugging/audit
    llm_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False, index=True)
    # Values: open, acknowledged, resolved
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Acknowledgment
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    acknowledged_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Resolution
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship(
        "Property", back_populates="coverage_conflicts"
    )

    def __repr__(self) -> str:
        return f"<CoverageConflict(id={self.id}, type={self.conflict_type}, severity={self.severity})>"
