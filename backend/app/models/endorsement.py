"""Endorsement model - modifications to base policies."""

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Endorsement(BaseModel):
    """Endorsement model for policy modifications."""

    __tablename__ = "endorsements"

    # Foreign Keys
    policy_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Endorsement Identity
    endorsement_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    endorsement_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    endorsement_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Dates
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Content
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Impact
    affects_coverage: Mapped[str | None] = mapped_column(String(255), nullable=True)
    adds_exclusion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    adds_coverage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    modifies_limit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    modifies_deductible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Provenance
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    policy: Mapped["Policy"] = relationship(  # noqa: F821
        "Policy", back_populates="endorsements"
    )
    document: Mapped["Document | None"] = relationship(  # noqa: F821
        "Document", back_populates="endorsements"
    )

    def __repr__(self) -> str:
        return f"<Endorsement(id={self.id}, endorsement_number={self.endorsement_number})>"
