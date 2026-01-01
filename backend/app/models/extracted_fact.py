"""Extracted fact model - raw extracted facts before normalization."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExtractedFact(Base):
    """Extracted fact model for extraction audit trail."""

    __tablename__ = "extracted_facts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Foreign Keys
    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # What Was Extracted
    fact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Confidence & Source
    confidence: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    bounding_box: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="auto_accepted", nullable=False, index=True)
    reviewed_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Where It Went
    target_table: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship(  # noqa: F821
        "Document", back_populates="extracted_facts"
    )

    def __repr__(self) -> str:
        return f"<ExtractedFact(id={self.id}, fact_type={self.fact_type})>"
