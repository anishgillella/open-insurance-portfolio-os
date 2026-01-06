"""Repository for Property operations."""

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.building import Building
from app.models.coverage_gap import CoverageGap
from app.models.document import Document
from app.models.insurance_program import InsuranceProgram
from app.models.policy import Policy
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

    async def list_basic(
        self,
        organization_id: str | None = None,
        state: str | None = None,
        search: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 100,
    ) -> list[Property]:
        """Get properties without eager-loading relationships.

        Use this for simple list views where only property data is needed.
        Much faster than list_with_summary.

        Args:
            organization_id: Optional organization filter.
            state: Optional state filter.
            search: Optional search term.
            sort_by: Sort field.
            sort_order: Sort direction.
            limit: Maximum records.

        Returns:
            List of properties (relationships not loaded).
        """
        stmt = select(Property).where(Property.deleted_at.is_(None))

        # Apply filters
        if organization_id:
            stmt = stmt.where(Property.organization_id == organization_id)
        if state:
            stmt = stmt.where(Property.state == state)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                (Property.name.ilike(search_term))
                | (Property.address.ilike(search_term))
                | (Property.city.ilike(search_term))
            )

        # Apply sorting
        sort_column = getattr(Property, sort_by, Property.name)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_with_summary(
        self,
        organization_id: str | None = None,
        state: str | None = None,
        search: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 100,
        include_buildings: bool = True,
        include_programs: bool = True,
        include_gaps: bool = True,
        include_documents: bool = False,
    ) -> list[Property]:
        """Get properties with selectively loaded related data.

        Args:
            organization_id: Optional organization filter.
            state: Optional state filter.
            search: Optional search term.
            sort_by: Sort field.
            sort_order: Sort direction.
            limit: Maximum records.
            include_buildings: Load building relationships (default True).
            include_programs: Load insurance programs and policies (default True).
            include_gaps: Load coverage gaps (default True).
            include_documents: Load documents (default False - expensive!).

        Returns:
            List of properties with selectively eager-loaded relationships.
        """
        # Build options list based on what's needed
        options = []
        if include_buildings:
            options.append(selectinload(Property.buildings))
        if include_programs:
            options.append(
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                )
            )
        if include_gaps:
            options.append(selectinload(Property.coverage_gaps))
        if include_documents:
            options.append(selectinload(Property.documents))

        stmt = select(Property).where(Property.deleted_at.is_(None))

        if options:
            stmt = stmt.options(*options)

        # Apply filters
        if organization_id:
            stmt = stmt.where(Property.organization_id == organization_id)
        if state:
            stmt = stmt.where(Property.state == state)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                (Property.name.ilike(search_term))
                | (Property.address.ilike(search_term))
                | (Property.city.ilike(search_term))
            )

        # Apply sorting
        sort_column = getattr(Property, sort_by, Property.name)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_with_details(self, property_id: str) -> Property | None:
        """Get property with all related data for detail view.

        Args:
            property_id: Property ID.

        Returns:
            Property with eager-loaded relationships or None.
        """
        stmt = (
            select(Property)
            .options(
                selectinload(Property.buildings),
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                ),
                selectinload(Property.coverage_gaps),
                selectinload(Property.documents),
                selectinload(Property.lender_requirements),
            )
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_all(self, organization_id: str | None = None) -> int:
        """Count all properties.

        Args:
            organization_id: Optional organization filter.

        Returns:
            Total count of properties.
        """
        stmt = select(func.count(Property.id)).where(Property.deleted_at.is_(None))
        if organization_id:
            stmt = stmt.where(Property.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_portfolio_stats(
        self, organization_id: str | None = None
    ) -> dict[str, Any]:
        """Get aggregated portfolio statistics.

        Args:
            organization_id: Optional organization filter.

        Returns:
            Dictionary with portfolio stats.
        """
        # Base query for properties
        property_stmt = select(
            func.count(Property.id).label("total_properties"),
            func.coalesce(func.sum(Property.units), 0).label("total_units"),
        ).where(Property.deleted_at.is_(None))

        if organization_id:
            property_stmt = property_stmt.where(
                Property.organization_id == organization_id
            )

        property_result = await self.session.execute(property_stmt)
        property_stats = property_result.one()

        # Count buildings
        building_stmt = (
            select(func.count(Building.id))
            .join(Property, Building.property_id == Property.id)
            .where(Property.deleted_at.is_(None))
        )
        if organization_id:
            building_stmt = building_stmt.where(
                Property.organization_id == organization_id
            )
        building_result = await self.session.execute(building_stmt)
        total_buildings = building_result.scalar() or 0

        # Get premium and TIV from insurance programs
        program_stmt = (
            select(
                func.coalesce(func.sum(InsuranceProgram.total_premium), 0).label(
                    "total_premium"
                ),
                func.coalesce(func.sum(InsuranceProgram.total_insured_value), 0).label(
                    "total_tiv"
                ),
            )
            .join(Property, InsuranceProgram.property_id == Property.id)
            .where(
                Property.deleted_at.is_(None),
                InsuranceProgram.status == "active",
            )
        )
        if organization_id:
            program_stmt = program_stmt.where(
                Property.organization_id == organization_id
            )
        program_result = await self.session.execute(program_stmt)
        program_stats = program_result.one()

        return {
            "total_properties": property_stats.total_properties or 0,
            "total_buildings": total_buildings,
            "total_units": property_stats.total_units or 0,
            "total_insured_value": Decimal(str(program_stats.total_tiv or 0)),
            "total_annual_premium": Decimal(str(program_stats.total_premium or 0)),
        }

    async def get_documents_by_property(
        self, property_id: str, limit: int = 100
    ) -> list[Document]:
        """Get documents for a property.

        Args:
            property_id: Property ID.
            limit: Maximum records.

        Returns:
            List of documents.
        """
        stmt = (
            select(Document)
            .where(
                Document.property_id == property_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
