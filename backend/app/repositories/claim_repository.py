"""Repository for Claim operations."""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.repositories.base import BaseRepository
from app.schemas.document import ClaimEntry

logger = logging.getLogger(__name__)


class ClaimRepository(BaseRepository[Claim]):
    """Repository for Claim CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Claim, session)

    async def create_from_extraction(
        self,
        extraction: ClaimEntry,
        property_id: str,
        document_id: str | None = None,
        policy_id: str | None = None,
    ) -> Claim:
        """Create a claim from extraction result.

        Args:
            extraction: Extracted claim data.
            property_id: Property ID.
            document_id: Source document ID.
            policy_id: Related policy ID if known.

        Returns:
            Created Claim instance.
        """
        return await self.create(
            property_id=property_id,
            policy_id=policy_id,
            document_id=document_id,
            claim_number=extraction.claim_number,
            claim_type=extraction.claim_type.value if extraction.claim_type else None,
            carrier_name=extraction.carrier_name,
            date_of_loss=extraction.date_of_loss,
            date_reported=extraction.date_reported,
            date_closed=extraction.date_closed,
            description=extraction.description,
            cause_of_loss=extraction.cause_of_loss,
            location_address=extraction.location_address,
            location_name=extraction.location_name,
            # Detailed paid amounts
            paid_loss=Decimal(str(extraction.paid_loss)) if extraction.paid_loss else None,
            paid_expense=Decimal(str(extraction.paid_expense)) if extraction.paid_expense else None,
            paid_medical=Decimal(str(extraction.paid_medical)) if extraction.paid_medical else None,
            paid_indemnity=Decimal(str(extraction.paid_indemnity)) if extraction.paid_indemnity else None,
            total_paid=Decimal(str(extraction.total_paid)) if extraction.total_paid else None,
            # Detailed reserve amounts
            reserve_loss=Decimal(str(extraction.reserve_loss)) if extraction.reserve_loss else None,
            reserve_expense=Decimal(str(extraction.reserve_expense)) if extraction.reserve_expense else None,
            reserve_medical=Decimal(str(extraction.reserve_medical)) if extraction.reserve_medical else None,
            reserve_indemnity=Decimal(str(extraction.reserve_indemnity)) if extraction.reserve_indemnity else None,
            total_reserve=Decimal(str(extraction.total_reserve)) if extraction.total_reserve else None,
            # Detailed incurred amounts
            incurred_loss=Decimal(str(extraction.incurred_loss)) if extraction.incurred_loss else None,
            incurred_expense=Decimal(str(extraction.incurred_expense)) if extraction.incurred_expense else None,
            total_incurred=Decimal(str(extraction.total_incurred)) if extraction.total_incurred else None,
            # Recovery
            subrogation_amount=Decimal(str(extraction.subrogation_amount)) if extraction.subrogation_amount else None,
            deductible_recovered=Decimal(str(extraction.deductible_recovered)) if extraction.deductible_recovered else None,
            salvage_amount=Decimal(str(extraction.salvage_amount)) if extraction.salvage_amount else None,
            net_incurred=Decimal(str(extraction.net_incurred)) if extraction.net_incurred else None,
            # Status
            status=extraction.claim_status.value if extraction.claim_status else None,
            litigation_status=extraction.litigation_status,
            # Claimant
            claimant_name=extraction.claimant_name,
            # Additional details
            injury_description=extraction.injury_description,
            notes=extraction.notes,
        )

    async def create_many_from_extraction(
        self,
        extractions: list[ClaimEntry],
        property_id: str,
        document_id: str | None = None,
    ) -> list[Claim]:
        """Create multiple claims from extraction results.

        Args:
            extractions: List of extracted claim data.
            property_id: Property ID.
            document_id: Source document ID.

        Returns:
            List of created Claim instances.
        """
        claims = []
        for extraction in extractions:
            claim = await self.create_from_extraction(
                extraction=extraction,
                property_id=property_id,
                document_id=document_id,
            )
            claims.append(claim)
        return claims

    async def get_by_property(
        self,
        property_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Claim]:
        """Get claims for a property.

        Args:
            property_id: Property ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of claims.
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            property_id=property_id,
        )

    async def get_by_claim_number(self, claim_number: str) -> Claim | None:
        """Get a claim by claim number.

        Args:
            claim_number: Claim number.

        Returns:
            Claim or None if not found.
        """
        stmt = select(self.model).where(
            self.model.deleted_at.is_(None),
            self.model.claim_number == claim_number,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_claims(
        self,
        property_id: str | None = None,
        limit: int = 100,
    ) -> list[Claim]:
        """Get open claims.

        Args:
            property_id: Optional filter by property.
            limit: Maximum records.

        Returns:
            List of open claims.
        """
        stmt = select(self.model).where(
            self.model.deleted_at.is_(None),
            self.model.status == "open",
        )
        if property_id:
            stmt = stmt.where(self.model.property_id == property_id)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
