"""Insurance program model - yearly insurance program for a property."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class InsuranceProgram(BaseModel):
    """Insurance program model - yearly collection of policies for a property."""

    __tablename__ = "insurance_programs"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Period
    program_year: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Aggregated Values (computed from policies)
    total_premium: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_insured_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_liability_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)

    # Data Quality
    completeness_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    policies_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    property: Mapped["Property"] = relationship(  # noqa: F821
        "Property", back_populates="insurance_programs"
    )
    policies: Mapped[list["Policy"]] = relationship(  # noqa: F821
        "Policy", back_populates="program", lazy="selectin"
    )
    certificates: Mapped[list["Certificate"]] = relationship(  # noqa: F821
        "Certificate", back_populates="program", lazy="selectin"
    )
    financials: Mapped[list["Financial"]] = relationship(  # noqa: F821
        "Financial", back_populates="program", lazy="selectin"
    )
    coverage_gaps: Mapped[list["CoverageGap"]] = relationship(  # noqa: F821
        "CoverageGap", back_populates="program", lazy="selectin"
    )

    # Unique constraint
    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<InsuranceProgram(id={self.id}, program_year={self.program_year})>"
