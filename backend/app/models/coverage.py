"""Coverage model - specific coverages within a policy."""

from decimal import Decimal

from sqlalchemy import Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Coverage(BaseModel):
    """Coverage model for specific coverages within a policy."""

    __tablename__ = "coverages"

    # Foreign Keys
    policy_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_document_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Coverage Identity
    coverage_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    coverage_category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    coverage_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Limits
    limit_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    limit_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sublimit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    sublimit_applies_to: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Deductibles
    deductible_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    deductible_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    deductible_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    deductible_minimum: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    deductible_maximum: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    deductible_applies_to: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Special Conditions
    waiting_period_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coinsurance_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuation_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    margin_clause_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Exclusions/Limitations (stored as text for RAG)
    exclusions_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provenance
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    policy: Mapped["Policy"] = relationship(  # noqa: F821
        "Policy", back_populates="coverages"
    )

    def __repr__(self) -> str:
        return f"<Coverage(id={self.id}, coverage_name={self.coverage_name})>"
