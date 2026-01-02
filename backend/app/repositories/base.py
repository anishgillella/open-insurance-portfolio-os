"""Base repository with common CRUD operations."""

import logging
from typing import Any, Generic, TypeVar
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: type[ModelT], session: AsyncSession):
        """Initialize repository.

        Args:
            model: SQLAlchemy model class.
            session: Async database session.
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs: Any) -> ModelT:
        """Create a new record.

        Args:
            **kwargs: Model field values.

        Returns:
            Created model instance.
        """
        if "id" not in kwargs:
            kwargs["id"] = str(uuid4())

        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)

        logger.debug(f"Created {self.model.__name__} with id={instance.id}")
        return instance

    async def get_by_id(self, id: str) -> ModelT | None:
        """Get a record by ID.

        Args:
            id: Record ID.

        Returns:
            Model instance or None if not found.
        """
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> list[ModelT]:
        """Get all records with optional filtering.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.
            **filters: Field filters (field_name=value).

        Returns:
            List of model instances.
        """
        stmt = select(self.model).where(self.model.deleted_at.is_(None))

        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: str, **kwargs: Any) -> ModelT | None:
        """Update a record by ID.

        Args:
            id: Record ID.
            **kwargs: Fields to update.

        Returns:
            Updated model instance or None if not found.
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return None

        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        await self.session.flush()
        await self.session.refresh(instance)

        logger.debug(f"Updated {self.model.__name__} with id={id}")
        return instance

    async def delete(self, id: str, soft: bool = True) -> bool:
        """Delete a record by ID.

        Args:
            id: Record ID.
            soft: If True, soft delete (set deleted_at). If False, hard delete.

        Returns:
            True if deleted, False if not found.
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return False

        if soft:
            from datetime import datetime, timezone

            instance.deleted_at = datetime.now(timezone.utc)
        else:
            await self.session.delete(instance)

        await self.session.flush()
        logger.debug(f"Deleted {self.model.__name__} with id={id} (soft={soft})")
        return True
