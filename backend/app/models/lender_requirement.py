"""Lender requirement model - specific requirements for a loan."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LenderRequirement(BaseModel):
    """Lender requirement model for specific loan requirements."""

    __tablename__ = "lender_requirements"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lender_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("lenders.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Loan Details
    loan_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    loan_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Requirements
    min_property_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    min_gl_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    min_umbrella_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    max_deductible_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    max_deductible_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    requires_flood: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_earthquake: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_terrorism: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    additional_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Compliance Status (computed)
    compliance_status: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    compliance_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    compliance_issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship(  # noqa: F821
        "Property", back_populates="lender_requirements"
    )
    lender: Mapped["Lender | None"] = relationship(  # noqa: F821
        "Lender", back_populates="lender_requirements"
    )

    def __repr__(self) -> str:
        return f"<LenderRequirement(id={self.id}, loan_number={self.loan_number})>"
