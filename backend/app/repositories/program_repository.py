"""Repository for InsuranceProgram operations."""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insurance_program import InsuranceProgram
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ProgramRepository(BaseRepository[InsuranceProgram]):
    """Repository for InsuranceProgram CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(InsuranceProgram, session)

    async def find_by_property_and_year(
        self,
        property_id: str,
        program_year: int,
    ) -> InsuranceProgram | None:
        """Find a program by property and year.

        Args:
            property_id: Property ID.
            program_year: Program year.

        Returns:
            InsuranceProgram or None if not found.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.property_id == property_id,
                self.model.program_year == program_year,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        property_id: str,
        program_year: int | None = None,
        effective_date: date | None = None,
        expiration_date: date | None = None,
    ) -> tuple[InsuranceProgram, bool]:
        """Get existing program or create new one.

        Args:
            property_id: Property ID.
            program_year: Program year (defaults to current year).
            effective_date: Optional effective date.
            expiration_date: Optional expiration date.

        Returns:
            Tuple of (InsuranceProgram, is_new).
        """
        if program_year is None:
            program_year = date.today().year

        existing = await self.find_by_property_and_year(property_id, program_year)
        if existing:
            logger.info(f"Found existing program: {program_year} (id: {existing.id})")
            return existing, False

        # Create new program
        program = await self.create(
            property_id=property_id,
            program_year=program_year,
            effective_date=effective_date,
            expiration_date=expiration_date,
            status="active",
        )
        logger.info(f"Created new program: {program_year} (id: {program.id})")
        return program, True

    async def get_by_property(
        self,
        property_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[InsuranceProgram]:
        """Get programs for a property.

        Args:
            property_id: Property ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of programs.
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            property_id=property_id,
        )

    async def get_current_program(
        self,
        property_id: str,
    ) -> InsuranceProgram | None:
        """Get the current active program for a property.

        Args:
            property_id: Property ID.

        Returns:
            Current program or None.
        """
        today = date.today()
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.property_id == property_id,
                self.model.status == "active",
            )
            .order_by(self.model.program_year.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
