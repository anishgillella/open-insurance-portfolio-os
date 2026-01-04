"""Organization model - multi-tenancy support."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Organization(BaseModel):
    """Organization model for multi-tenant support."""

    __tablename__ = "organizations"

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # Contact
    primary_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Settings
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Subscription (future)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    properties: Mapped[list["Property"]] = relationship(  # noqa: F821
        "Property", back_populates="organization", lazy="selectin"
    )
    insured_entities: Mapped[list["InsuredEntity"]] = relationship(  # noqa: F821
        "InsuredEntity", back_populates="organization", lazy="selectin"
    )
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="organization", lazy="selectin"
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        "Conversation", back_populates="organization", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
