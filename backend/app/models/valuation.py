"""Valuation model - property valuations from SOVs and appraisals."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Valuation(BaseModel):
    """Valuation model for property valuations."""

    __tablename__ = "valuations"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    building_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("buildings.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Valuation Context
    valuation_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    valuation_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    valuation_source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Values
    building_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    contents_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    business_income_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    rental_income_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    extra_expense_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_insured_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Supporting Data
    price_per_sqft: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    sq_ft_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Provenance
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship(  # noqa: F821
        "Property", back_populates="valuations"
    )
    building: Mapped["Building | None"] = relationship(  # noqa: F821
        "Building", back_populates="valuations"
    )
    document: Mapped["Document | None"] = relationship(  # noqa: F821
        "Document", back_populates="valuations"
    )

    def __repr__(self) -> str:
        return f"<Valuation(id={self.id}, valuation_date={self.valuation_date})>"
