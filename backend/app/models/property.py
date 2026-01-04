"""Property model - real estate properties that need insurance."""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Property(BaseModel):
    """Real estate property model."""

    __tablename__ = "properties"

    # Foreign Keys
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Address
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    zip: Mapped[str | None] = mapped_column(String(20), nullable=True)
    county: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default="US", nullable=False)

    # Property Characteristics
    property_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sq_ft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stories: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Construction
    construction_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    roof_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    roof_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Protection
    has_sprinklers: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sprinkler_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    protection_class: Mapped[str | None] = mapped_column(String(10), nullable=True)
    alarm_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Risk Factors
    flood_zone: Mapped[str | None] = mapped_column(String(10), nullable=True)
    earthquake_zone: Mapped[str | None] = mapped_column(String(10), nullable=True)
    wind_zone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crime_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    # Data Quality
    completeness_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="properties"
    )
    buildings: Mapped[list["Building"]] = relationship(  # noqa: F821
        "Building", back_populates="property", lazy="selectin"
    )
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="property", lazy="selectin"
    )
    insurance_programs: Mapped[list["InsuranceProgram"]] = relationship(  # noqa: F821
        "InsuranceProgram", back_populates="property", lazy="selectin"
    )
    claims: Mapped[list["Claim"]] = relationship(  # noqa: F821
        "Claim", back_populates="property", lazy="selectin"
    )
    valuations: Mapped[list["Valuation"]] = relationship(  # noqa: F821
        "Valuation", back_populates="property", lazy="selectin"
    )
    lender_requirements: Mapped[list["LenderRequirement"]] = relationship(  # noqa: F821
        "LenderRequirement", back_populates="property", lazy="selectin"
    )
    coverage_gaps: Mapped[list["CoverageGap"]] = relationship(  # noqa: F821
        "CoverageGap", back_populates="property", lazy="selectin"
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        "Conversation", back_populates="property", lazy="selectin"
    )
    health_scores: Mapped[list["HealthScore"]] = relationship(  # noqa: F821
        "HealthScore", back_populates="property", lazy="selectin"
    )
    coverage_conflicts: Mapped[list["CoverageConflict"]] = relationship(  # noqa: F821
        "CoverageConflict", back_populates="property", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Property(id={self.id}, name={self.name})>"
