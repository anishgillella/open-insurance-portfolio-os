"""Policy model - insurance policies."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Policy(BaseModel):
    """Insurance policy model."""

    __tablename__ = "policies"

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
    carrier_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("carriers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    named_insured_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("insured_entities.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Policy Identity
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    policy_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    carrier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Dates
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Premium
    premium: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    taxes: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    fees: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Policy Characteristics
    admitted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    form_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    policy_form: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Named Insured
    named_insured_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Extraction Quality
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_pages: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    program: Mapped["InsuranceProgram"] = relationship(  # noqa: F821
        "InsuranceProgram", back_populates="policies"
    )
    document: Mapped["Document | None"] = relationship(  # noqa: F821
        "Document", back_populates="policies"
    )
    carrier: Mapped["Carrier | None"] = relationship(  # noqa: F821
        "Carrier", back_populates="policies"
    )
    named_insured: Mapped["InsuredEntity | None"] = relationship(  # noqa: F821
        "InsuredEntity", back_populates="policies"
    )
    coverages: Mapped[list["Coverage"]] = relationship(  # noqa: F821
        "Coverage", back_populates="policy", lazy="selectin"
    )
    endorsements: Mapped[list["Endorsement"]] = relationship(  # noqa: F821
        "Endorsement", back_populates="policy", lazy="selectin"
    )
    claims: Mapped[list["Claim"]] = relationship(  # noqa: F821
        "Claim", back_populates="policy", lazy="selectin"
    )
    coverage_gaps: Mapped[list["CoverageGap"]] = relationship(  # noqa: F821
        "CoverageGap", back_populates="policy", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, policy_type={self.policy_type})>"
