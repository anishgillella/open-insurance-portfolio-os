"""Document model - source documents uploaded to the system."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Document(BaseModel):
    """Source document model."""

    __tablename__ = "documents"

    # Unique constraint to prevent duplicate documents per organization
    # Only applies to non-deleted documents (partial index)
    __table_args__ = (
        Index(
            "ix_documents_unique_filename_org",
            "file_name",
            "organization_id",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    # Foreign Keys
    property_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File Information
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Classification
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    document_subtype: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Key Metadata (extracted)
    carrier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    policy_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Processing Status
    upload_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    ocr_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    ocr_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ocr_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extraction_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    extraction_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extraction_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Processing Outputs
    ocr_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Quality Metrics
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    human_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    human_reviewed_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    # Upload Context
    uploaded_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    upload_source: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="documents"
    )
    property: Mapped["Property | None"] = relationship(  # noqa: F821
        "Property", back_populates="documents"
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(  # noqa: F821
        "DocumentChunk", back_populates="document", lazy="selectin"
    )
    policies: Mapped[list["Policy"]] = relationship(  # noqa: F821
        "Policy", back_populates="document", lazy="selectin"
    )
    endorsements: Mapped[list["Endorsement"]] = relationship(  # noqa: F821
        "Endorsement", back_populates="document", lazy="selectin"
    )
    certificates: Mapped[list["Certificate"]] = relationship(  # noqa: F821
        "Certificate", back_populates="document", lazy="selectin"
    )
    financials: Mapped[list["Financial"]] = relationship(  # noqa: F821
        "Financial", back_populates="document", lazy="selectin"
    )
    claims: Mapped[list["Claim"]] = relationship(  # noqa: F821
        "Claim", back_populates="document", lazy="selectin"
    )
    valuations: Mapped[list["Valuation"]] = relationship(  # noqa: F821
        "Valuation", back_populates="document", lazy="selectin"
    )
    extracted_facts: Mapped[list["ExtractedFact"]] = relationship(  # noqa: F821
        "ExtractedFact", back_populates="document", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, file_name={self.file_name})>"
