"""Repository for Property operations."""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class PropertyRepository(BaseRepository[Property]):
    """Repository for Property CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Property, session)

    async def find_by_name_and_org(
        self,
        name: str,
        organization_id: str,
    ) -> Property | None:
        """Find a property by name and organization.

        Args:
            name: Property name.
            organization_id: Organization ID.

        Returns:
            Property or None if not found.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.name == name,
                self.model.organization_id == organization_id,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        name: str,
        organization_id: str,
    ) -> tuple[Property, bool]:
        """Get existing property or create new one.

        Args:
            name: Property name.
            organization_id: Organization ID.

        Returns:
            Tuple of (Property, is_new).
        """
        existing = await self.find_by_name_and_org(name, organization_id)
        if existing:
            logger.info(f"Found existing property: {name} (id: {existing.id})")
            return existing, False

        # Create new property
        property = await self.create(
            name=name,
            organization_id=organization_id,
            status="active",
        )
        logger.info(f"Created new property: {name} (id: {property.id})")
        return property, True

    async def get_by_organization(
        self,
        organization_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Property]:
        """Get properties for an organization.

        Args:
            organization_id: Organization ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of properties.
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            organization_id=organization_id,
        )
