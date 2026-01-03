"""Claim model - claims history from loss runs."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Claim(BaseModel):
    """Claim model for claims history.

    This model captures detailed claim information from loss runs, including
    comprehensive financial breakdowns for paid, reserved, and incurred amounts.
    """

    __tablename__ = "claims"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("policies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    document_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Claim Identity
    claim_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    claim_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    carrier_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Dates
    date_of_loss: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    date_reported: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_closed: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cause_of_loss: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location Information
    location_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Legacy Financial Fields (aggregate)
    amount_paid: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    amount_reserved: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    amount_incurred: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    deductible_applied: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    subrogation_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Detailed Paid Amounts
    paid_loss: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    paid_expense: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    paid_medical: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    paid_indemnity: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_paid: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Detailed Reserve Amounts
    reserve_loss: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    reserve_expense: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    reserve_medical: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    reserve_indemnity: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_reserve: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Detailed Incurred Amounts (paid + reserve)
    incurred_loss: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    incurred_expense: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_incurred: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Recovery Information
    deductible_recovered: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    salvage_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    net_incurred: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Status
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    litigation_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Claimant (for liability)
    claimant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claimant_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Additional Details
    injury_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provenance
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship(  # noqa: F821
        "Property", back_populates="claims"
    )
    policy: Mapped["Policy | None"] = relationship(  # noqa: F821
        "Policy", back_populates="claims"
    )
    document: Mapped["Document | None"] = relationship(  # noqa: F821
        "Document", back_populates="claims"
    )

    def __repr__(self) -> str:
        return f"<Claim(id={self.id}, claim_number={self.claim_number})>"
