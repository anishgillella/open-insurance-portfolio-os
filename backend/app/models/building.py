"""Building model - individual buildings within properties."""

from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Building(BaseModel):
    """Building model for properties with multiple buildings."""

    __tablename__ = "buildings"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identity
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    building_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Characteristics
    sq_ft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    construction_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    occupancy_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Values
    building_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    contents_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship(  # noqa: F821
        "Property", back_populates="buildings"
    )
    valuations: Mapped[list["Valuation"]] = relationship(  # noqa: F821
        "Valuation", back_populates="building", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Building(id={self.id}, name={self.name})>"
