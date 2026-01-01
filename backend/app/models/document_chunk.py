"""Document chunk model - chunks for RAG semantic search."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DocumentChunk(BaseModel):
    """Document chunk model for RAG semantic search."""

    __tablename__ = "document_chunks"

    # Foreign Keys
    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Content
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Classification
    chunk_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Position
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Vector Reference
    pinecone_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    embedding_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata for Filtering (denormalized)
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    policy_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    carrier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship(  # noqa: F821
        "Document", back_populates="chunks"
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, chunk_index={self.chunk_index})>"
