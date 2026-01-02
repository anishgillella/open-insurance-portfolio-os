"""Repository for Policy and Coverage operations."""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coverage import Coverage
from app.models.policy import Policy
from app.repositories.base import BaseRepository
from app.schemas.document import CoverageExtraction, PolicyExtraction

logger = logging.getLogger(__name__)


class PolicyRepository(BaseRepository[Policy]):
    """Repository for Policy CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Policy, session)

    async def create_from_extraction(
        self,
        extraction: PolicyExtraction,
        program_id: str,
        document_id: str | None = None,
    ) -> Policy:
        """Create a policy from extraction result.

        Args:
            extraction: Extracted policy data.
            program_id: Insurance program ID.
            document_id: Source document ID.

        Returns:
            Created Policy instance.
        """
        return await self.create(
            program_id=program_id,
            document_id=document_id,
            policy_type=extraction.policy_type.value,
            policy_number=extraction.policy_number,
            carrier_name=extraction.carrier_name,
            effective_date=extraction.effective_date,
            expiration_date=extraction.expiration_date,
            premium=Decimal(str(extraction.premium)) if extraction.premium else None,
            taxes=Decimal(str(extraction.taxes)) if extraction.taxes else None,
            fees=Decimal(str(extraction.fees)) if extraction.fees else None,
            total_cost=Decimal(str(extraction.total_cost)) if extraction.total_cost else None,
            admitted=extraction.admitted,
            form_type=extraction.form_type,
            policy_form=extraction.policy_form,
            named_insured_text=extraction.named_insured,
            extraction_confidence=extraction.confidence,
            source_pages=extraction.source_pages if extraction.source_pages else None,
            needs_review=extraction.confidence < 0.8,
        )

    async def get_by_program(
        self,
        program_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Policy]:
        """Get policies for an insurance program.

        Args:
            program_id: Insurance program ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of policies.
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            program_id=program_id,
        )

    async def get_by_policy_number(self, policy_number: str) -> Policy | None:
        """Get a policy by policy number.

        Args:
            policy_number: Policy number.

        Returns:
            Policy or None if not found.
        """
        stmt = select(self.model).where(
            self.model.deleted_at.is_(None),
            self.model.policy_number == policy_number,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class CoverageRepository(BaseRepository[Coverage]):
    """Repository for Coverage CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Coverage, session)

    async def create_from_extraction(
        self,
        extraction: CoverageExtraction,
        policy_id: str,
        document_id: str | None = None,
    ) -> Coverage:
        """Create a coverage from extraction result.

        Args:
            extraction: Extracted coverage data.
            policy_id: Parent policy ID.
            document_id: Source document ID.

        Returns:
            Created Coverage instance.
        """
        return await self.create(
            policy_id=policy_id,
            source_document_id=document_id,
            coverage_name=extraction.coverage_name,
            coverage_category=extraction.coverage_category,
            limit_amount=Decimal(str(extraction.limit_amount)) if extraction.limit_amount else None,
            limit_type=extraction.limit_type,
            sublimit=Decimal(str(extraction.sublimit)) if extraction.sublimit else None,
            sublimit_applies_to=extraction.sublimit_applies_to,
            deductible_amount=(
                Decimal(str(extraction.deductible_amount)) if extraction.deductible_amount else None
            ),
            deductible_type=extraction.deductible_type,
            deductible_pct=extraction.deductible_percentage,
            coinsurance_pct=extraction.coinsurance_percentage,
            waiting_period_hours=extraction.waiting_period_hours,
            valuation_type=extraction.valuation_type,
            exclusions_text="\n".join(extraction.exclusions) if extraction.exclusions else None,
            conditions_text="\n".join(extraction.conditions) if extraction.conditions else None,
            source_page=extraction.source_page,
            extraction_confidence=extraction.confidence,
        )

    async def create_many_from_extraction(
        self,
        extractions: list[CoverageExtraction],
        policy_id: str,
        document_id: str | None = None,
    ) -> list[Coverage]:
        """Create multiple coverages from extraction results.

        Args:
            extractions: List of extracted coverage data.
            policy_id: Parent policy ID.
            document_id: Source document ID.

        Returns:
            List of created Coverage instances.
        """
        coverages = []
        for extraction in extractions:
            coverage = await self.create_from_extraction(
                extraction=extraction,
                policy_id=policy_id,
                document_id=document_id,
            )
            coverages.append(coverage)
        return coverages

    async def get_by_policy(
        self,
        policy_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Coverage]:
        """Get coverages for a policy.

        Args:
            policy_id: Policy ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of coverages.
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            policy_id=policy_id,
        )
