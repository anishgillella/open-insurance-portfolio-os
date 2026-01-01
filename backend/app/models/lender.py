"""Lender model - banks and mortgage companies that require insurance."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Lender(Base):
    """Lender model for banks and mortgage companies."""

    __tablename__ = "lenders"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    short_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Requirements (standard/default)
    min_property_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    min_gl_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    max_deductible_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    max_deductible_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    requires_flood: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_earthquake: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_umbrella: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_umbrella_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Mortgagee Clause
    mortgagee_clause: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Contact
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    certificates: Mapped[list["Certificate"]] = relationship(  # noqa: F821
        "Certificate", back_populates="lender", lazy="selectin"
    )
    lender_requirements: Mapped[list["LenderRequirement"]] = relationship(  # noqa: F821
        "LenderRequirement", back_populates="lender", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Lender(id={self.id}, name={self.name})>"
