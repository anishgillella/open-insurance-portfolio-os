"""Conversation model for RAG chat functionality."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.organization import Organization
    from app.models.policy import Policy
    from app.models.property import Property


class Conversation(BaseModel):
    """Conversation model for RAG chat sessions."""

    __tablename__ = "conversations"

    # Optional organization scope
    organization_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Conversation metadata
    title: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional filters applied to this conversation
    property_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="SET NULL"),
        nullable=True,
    )
    policy_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_type: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stats
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization",
        back_populates="conversations",
    )
    property: Mapped["Property | None"] = relationship(
        "Property",
        back_populates="conversations",
    )
    policy: Mapped["Policy | None"] = relationship(
        "Policy",
        back_populates="conversations",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
