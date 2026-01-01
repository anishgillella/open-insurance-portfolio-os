"""Financial model - invoices, quotes, and payments."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Float, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Financial(BaseModel):
    """Financial model for invoices, quotes, and payments."""

    __tablename__ = "financials"

    # Foreign Keys
    program_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("insurance_programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Record Type
    record_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Line Items
    base_premium: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    taxes: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    fees: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    broker_commission: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    surplus_lines_tax: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    stamping_fee: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    policy_fee: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Dates
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Payment Details
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)

    # Provenance
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    program: Mapped["InsuranceProgram"] = relationship(  # noqa: F821
        "InsuranceProgram", back_populates="financials"
    )
    document: Mapped["Document | None"] = relationship(  # noqa: F821
        "Document", back_populates="financials"
    )

    def __repr__(self) -> str:
        return f"<Financial(id={self.id}, record_type={self.record_type})>"
