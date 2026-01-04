"""Renewal Readiness model - Document readiness tracking for renewals."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.property import Property


class RenewalReadiness(BaseModel):
    """Renewal Readiness model for tracking document preparation status.

    Tracks which documents are ready for renewal, which are missing or stale,
    and provides LLM-verified assessment of document contents.
    """

    __tablename__ = "renewal_readiness"

    # Foreign Key
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Renewal Context
    target_renewal_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    assessment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Readiness Score
    readiness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    # 0-100 percentage
    readiness_grade: Mapped[str] = mapped_column(String(1), nullable=False)
    # A, B, C, D, F

    # Document Status (JSONB for flexibility)
    document_status: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Structure: {
    #   "required": [
    #     {"type": "current_policy", "status": "found", "document_id": "...", "age_days": 300, "verified": true},
    #     {"type": "loss_runs", "status": "found", "document_id": "...", "age_days": 45, "verified": true},
    #     {"type": "sov", "status": "missing", "document_id": null, "age_days": null, "verified": false}
    #   ],
    #   "recommended": [
    #     {"type": "property_valuation", "status": "stale", "document_id": "...", "age_days": 540, "verified": true},
    #     {"type": "photos", "status": "missing", "document_id": null, "age_days": null, "verified": false}
    #   ]
    # }

    # LLM Verification Results
    llm_verification: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Structure: {
    #   "verified_documents": [
    #     {"document_id": "...", "type": "loss_runs", "verified": true,
    #      "extracted_data": {"total_claims": 2, "total_paid": 45000, "period": "2022-2025"},
    #      "issues": []},
    #     {"document_id": "...", "type": "current_policy", "verified": true,
    #      "extracted_data": {"policy_number": "...", "carrier": "...", "limits": {...}},
    #      "issues": ["Named insured mismatch"]}
    #   ],
    #   "data_consistency_issues": ["Entity name differs between policy and loss runs"],
    #   "verification_summary": "..."
    # }

    # Issues & Recommendations
    issues: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Structure: [
    #   {"severity": "critical", "issue": "SOV missing", "impact": "Cannot verify property values"},
    #   {"severity": "warning", "issue": "Valuation outdated", "impact": "May affect coverage adequacy"}
    # ]

    recommendations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Structure: [
    #   {"priority": "high", "action": "Upload current Statement of Values", "deadline": "60 days before renewal"},
    #   {"priority": "medium", "action": "Request updated property appraisal", "deadline": "90 days before renewal"}
    # ]

    # Timeline Integration
    renewal_timeline: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Structure: {
    #   "days_until_renewal": 75,
    #   "milestones": [
    #     {"day": 90, "action": "Complete SOV", "status": "missed"},
    #     {"day": 60, "action": "Request quotes", "status": "upcoming"},
    #     {"day": 30, "action": "Finalize selection", "status": "upcoming"}
    #   ]
    # }

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="current", nullable=False, index=True
    )
    # Values: current, superseded, completed

    # LLM Metadata
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationship
    property: Mapped["Property"] = relationship(
        "Property", back_populates="renewal_readiness"
    )

    def __repr__(self) -> str:
        return (
            f"<RenewalReadiness(id={self.id}, property_id={self.property_id}, "
            f"readiness_score={self.readiness_score}, grade={self.readiness_grade})>"
        )
