"""Insured entity model - LLCs, LPs, and other legal entities that are named insureds."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class InsuredEntity(BaseModel):
    """Insured entity model for LLCs, LPs, and other legal entities."""

    __tablename__ = "insured_entities"

    # Foreign Keys
    organization_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_entity_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("insured_entities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Contact
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Tax
    ein: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="insured_entities"
    )
    parent_entity: Mapped["InsuredEntity | None"] = relationship(
        "InsuredEntity", remote_side="InsuredEntity.id", back_populates="child_entities"
    )
    child_entities: Mapped[list["InsuredEntity"]] = relationship(
        "InsuredEntity", back_populates="parent_entity", lazy="selectin"
    )
    policies: Mapped[list["Policy"]] = relationship(  # noqa: F821
        "Policy", back_populates="named_insured", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<InsuredEntity(id={self.id}, name={self.name})>"
