"""Repository for Conversation and Message CRUD operations."""

import logging
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for conversation operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository.

        Args:
            session: Async database session.
        """
        super().__init__(Conversation, session)

    async def get_or_create(
        self,
        conversation_id: str,
        organization_id: str | None = None,
        property_id: str | None = None,
        policy_id: str | None = None,
        document_type: str | None = None,
    ) -> tuple[Conversation, bool]:
        """Get existing conversation or create new one.

        Args:
            conversation_id: Conversation ID (client-provided).
            organization_id: Optional organization scope.
            property_id: Optional property filter.
            policy_id: Optional policy filter.
            document_type: Optional document type filter.

        Returns:
            Tuple of (Conversation, created) where created is True if new.
        """
        # Try to get existing conversation
        existing = await self.get_by_id(conversation_id)
        if existing:
            return existing, False

        # Create new conversation
        conversation = Conversation(
            id=conversation_id,
            organization_id=organization_id,
            property_id=property_id,
            policy_id=policy_id,
            document_type=document_type,
            message_count=0,
        )
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)

        logger.info(f"Created new conversation {conversation_id}")
        return conversation, True

    async def get_with_messages(
        self,
        conversation_id: str,
        message_limit: int = 10,
    ) -> Conversation | None:
        """Get conversation with recent messages.

        Args:
            conversation_id: Conversation ID.
            message_limit: Maximum number of recent messages to include.

        Returns:
            Conversation with messages or None if not found.
        """
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation and message_limit:
            # Sort and limit messages (already ordered by created_at in relationship)
            conversation.messages = conversation.messages[-message_limit:]

        return conversation

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: list[dict[str, Any]] | None = None,
        confidence: float | None = None,
        tokens_used: int | None = None,
        latency_ms: int | None = None,
        model: str | None = None,
    ) -> Message:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation ID.
            role: Message role ('user', 'assistant', 'system').
            content: Message content.
            sources: Optional sources/citations for assistant messages.
            confidence: Optional confidence score.
            tokens_used: Optional token count.
            latency_ms: Optional latency in milliseconds.
            model: Optional model used for generation.

        Returns:
            Created Message instance.
        """
        message = Message(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources or [],
            confidence=confidence,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model=model,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)

        logger.debug(f"Added {role} message to conversation {conversation_id}")
        return message

    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[Message]:
        """Get recent messages for a conversation.

        Args:
            conversation_id: Conversation ID.
            limit: Maximum number of messages to return.

        Returns:
            List of Message instances, ordered by created_at.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        # Reverse to get chronological order
        return messages[::-1]

    async def update_title(
        self,
        conversation_id: str,
        title: str,
    ) -> Conversation | None:
        """Update conversation title.

        Args:
            conversation_id: Conversation ID.
            title: New title.

        Returns:
            Updated Conversation or None if not found.
        """
        return await self.update(conversation_id, title=title)

    async def get_recent_conversations(
        self,
        organization_id: str | None = None,
        limit: int = 20,
    ) -> list[Conversation]:
        """Get recent conversations.

        Args:
            organization_id: Optional organization filter.
            limit: Maximum number of conversations to return.

        Returns:
            List of Conversation instances.
        """
        stmt = (
            select(Conversation)
            .where(Conversation.deleted_at.is_(None))
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )

        if organization_id:
            stmt = stmt.where(Conversation.organization_id == organization_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
