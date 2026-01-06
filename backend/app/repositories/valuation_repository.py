"""Repository for Valuation operations."""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.valuation import Valuation
from app.repositories.base import BaseRepository
from app.schemas.document import SOVPropertyExtraction

logger = logging.getLogger(__name__)


class ValuationRepository(BaseRepository[Valuation]):
    """Repository for Valuation CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Valuation, session)

    async def create_from_extraction(
        self,
        extraction: SOVPropertyExtraction,
        property_id: str,
        document_id: str,
        valuation_date=None,
        valuation_source: str = "sov",
    ) -> Valuation:
        """Create a valuation record from SOV property extraction.

        Args:
            extraction: SOV property extraction data.
            property_id: Property ID.
            document_id: Source document ID.
            valuation_date: Optional valuation date.
            valuation_source: Source type (sov, appraisal, corelogic, etc.).

        Returns:
            Created Valuation record.
        """
        # Parse amounts safely
        def to_decimal(value) -> Decimal | None:
            if value is None:
                return None
            try:
                return Decimal(str(value))
            except (ValueError, TypeError):
                return None

        # Calculate price per sqft if we have both values
        price_per_sqft = None
        if extraction.total_insured_value and extraction.square_footage:
            try:
                price_per_sqft = Decimal(str(extraction.total_insured_value)) / Decimal(
                    str(extraction.square_footage)
                )
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        valuation = await self.create(
            property_id=property_id,
            document_id=document_id,
            valuation_date=valuation_date,
            valuation_method="replacement_cost",
            valuation_source=valuation_source,
            building_value=to_decimal(extraction.building_value),
            contents_value=to_decimal(extraction.contents_value),
            business_income_value=to_decimal(extraction.business_income_value),
            total_insured_value=to_decimal(extraction.total_insured_value),
            price_per_sqft=price_per_sqft,
            sq_ft_used=extraction.square_footage,
            extraction_confidence=0.85,  # Default confidence for SOV extractions
        )

        logger.info(
            f"Created valuation from SOV: {valuation.id} "
            f"(TIV: {valuation.total_insured_value})"
        )
        return valuation

    async def get_by_property(
        self,
        property_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Valuation]:
        """Get valuations for a property.

        Args:
            property_id: Property ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of valuations ordered by date descending.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.property_id == property_id,
            )
            .order_by(self.model.valuation_date.desc().nulls_last())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_property(
        self,
        property_id: str,
    ) -> Valuation | None:
        """Get the most recent valuation for a property.

        Args:
            property_id: Property ID.

        Returns:
            Latest Valuation or None.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.property_id == property_id,
            )
            .order_by(self.model.valuation_date.desc().nulls_last())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_document(
        self,
        document_id: str,
    ) -> Valuation | None:
        """Get valuation record for a document.

        Args:
            document_id: Document ID.

        Returns:
            Valuation or None.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.document_id == document_id,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
