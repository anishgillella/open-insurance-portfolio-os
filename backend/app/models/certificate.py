"""Certificate model - Certificates of Insurance (COIs) and Evidence of Property (EOPs)."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Certificate(BaseModel):
    """Certificate model for COIs and EOPs."""

    __tablename__ = "certificates"

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
    lender_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("lenders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Certificate Identity
    certificate_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    certificate_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Who It's For
    holder_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    holder_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Coverage Summary (as shown on cert)
    property_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_each_occurrence: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_general_aggregate: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_products_completed: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_personal_advertising: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_damage_to_rented: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_medical_expense: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    umbrella_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    umbrella_deductible: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    auto_combined_single: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    workers_comp_each_accident: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Dates
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Lender-Specific (for EOPs)
    loan_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mortgagee_clause: Mapped[str | None] = mapped_column(Text, nullable=True)
    loss_payee_clause: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provenance
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    program: Mapped["InsuranceProgram"] = relationship(  # noqa: F821
        "InsuranceProgram", back_populates="certificates"
    )
    document: Mapped["Document | None"] = relationship(  # noqa: F821
        "Document", back_populates="certificates"
    )
    lender: Mapped["Lender | None"] = relationship(  # noqa: F821
        "Lender", back_populates="certificates"
    )

    def __repr__(self) -> str:
        return f"<Certificate(id={self.id}, certificate_type={self.certificate_type})>"
