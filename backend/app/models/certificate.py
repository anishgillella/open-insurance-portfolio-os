"""Certificate model - Certificates of Insurance (COIs) and Evidence of Property (EOPs)."""

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Certificate(BaseModel):
    """Certificate model for COIs and EOPs.

    This model captures comprehensive certificate information including producer details,
    insured information, detailed coverage limits, and additional insured/waiver data.
    """

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
    revision_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Producer/Broker Information
    producer_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    producer_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    producer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    producer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    producer_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Insured Information (as shown on certificate)
    insured_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    insured_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Who It's For (Certificate Holder)
    holder_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    holder_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    holder_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Insurers mapping (A, B, C, D, E, F) - stores {letter: {name, naic}}
    insurers: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=dict, nullable=True)

    # Detailed policy references as JSONB array
    policies: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, default=list, nullable=True)

    # Property Coverage
    property_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # General Liability Coverage
    gl_each_occurrence: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_general_aggregate: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_products_completed: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_personal_advertising: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_damage_to_rented: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_medical_expense: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    gl_coverage_form: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gl_aggregate_limit_applies_per: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Auto Liability Coverage
    auto_combined_single: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    auto_bodily_injury_per_person: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    auto_bodily_injury_per_accident: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    auto_property_damage: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    auto_types: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Umbrella/Excess Coverage
    umbrella_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    umbrella_aggregate: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    umbrella_deductible: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    umbrella_retention: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    umbrella_coverage_form: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Workers Compensation Coverage
    workers_comp_each_accident: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    workers_comp_disease_ea_employee: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    workers_comp_disease_policy_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    workers_comp_per_statute: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    workers_comp_other: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    workers_comp_excluded_partners: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Description of Operations
    description_of_operations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Additional Insureds and Waivers
    additional_insureds: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    subrogation_waiver_applies: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Cancellation Terms
    cancellation_notice_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cancellation_terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Authorized Representative
    authorized_representative: Mapped[str | None] = mapped_column(String(255), nullable=True)

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
