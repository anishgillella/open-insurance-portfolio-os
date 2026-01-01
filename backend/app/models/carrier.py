"""Carrier model - insurance companies that issue policies."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Carrier(Base):
    """Insurance carrier model."""

    __tablename__ = "carriers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    short_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    naic_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Ratings
    am_best_rating: Mapped[str | None] = mapped_column(String(10), nullable=True)
    am_best_outlook: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sp_rating: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Status
    admitted_states: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    surplus_lines_states: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Contact
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claims_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

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
    policies: Mapped[list["Policy"]] = relationship(  # noqa: F821
        "Policy", back_populates="carrier", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Carrier(id={self.id}, name={self.name})>"
