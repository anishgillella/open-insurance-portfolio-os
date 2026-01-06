"""Repository for Policy and Coverage operations."""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Union

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.coverage import Coverage
from app.models.insurance_program import InsuranceProgram
from app.models.policy import Policy
from app.models.property import Property
from app.repositories.base import BaseRepository
from app.schemas.document import COIPolicyReference, CoverageExtraction, PolicyExtraction

logger = logging.getLogger(__name__)


class PolicyRepository(BaseRepository[Policy]):
    """Repository for Policy CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Policy, session)

    async def create_from_extraction(
        self,
        extraction: Union[PolicyExtraction, COIPolicyReference],
        program_id: str,
        document_id: str | None = None,
    ) -> Policy:
        """Create a policy from extraction result.

        Supports both full PolicyExtraction (from policy documents) and
        COIPolicyReference (from certificates of insurance).

        Args:
            extraction: Extracted policy data (PolicyExtraction or COIPolicyReference).
            program_id: Insurance program ID.
            document_id: Source document ID.

        Returns:
            Created Policy instance.
        """
        # Handle COIPolicyReference (from COI documents)
        if isinstance(extraction, COIPolicyReference):
            return await self.create(
                program_id=program_id,
                document_id=document_id,
                policy_type=extraction.policy_type.value,
                policy_number=extraction.policy_number,
                carrier_name=extraction.carrier_name,
                effective_date=extraction.effective_date,
                expiration_date=extraction.expiration_date,
                form_type=extraction.coverage_form,
                extraction_confidence=extraction.confidence,
                needs_review=extraction.confidence < 0.8,
            )

        # Handle full PolicyExtraction (from policy documents)
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
        """Get policies for an insurance program with coverages loaded.

        Args:
            program_id: Insurance program ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of policies with coverages eager-loaded.
        """
        stmt = (
            select(self.model)
            .options(selectinload(Policy.coverages))
            .where(
                self.model.deleted_at.is_(None),
                self.model.program_id == program_id,
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

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

    async def get_by_property(
        self,
        property_id: str,
        limit: int = 100,
    ) -> list[Policy]:
        """Get all policies for a property via insurance programs.

        Args:
            property_id: Property ID.
            limit: Maximum records.

        Returns:
            List of policies.
        """
        stmt = (
            select(Policy)
            .join(InsuranceProgram, Policy.program_id == InsuranceProgram.id)
            .options(selectinload(Policy.coverages))
            .where(
                InsuranceProgram.property_id == property_id,
                Policy.deleted_at.is_(None),
            )
            .order_by(Policy.expiration_date.desc().nullslast())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_with_details(self, policy_id: str) -> Policy | None:
        """Get policy with all related data for detail view.

        Args:
            policy_id: Policy ID.

        Returns:
            Policy with eager-loaded relationships or None.
        """
        stmt = (
            select(Policy)
            .options(
                selectinload(Policy.coverages),
                selectinload(Policy.endorsements),
                selectinload(Policy.document),
                selectinload(Policy.carrier),
                selectinload(Policy.named_insured),
                selectinload(Policy.program).selectinload(InsuranceProgram.property),
            )
            .where(
                Policy.id == policy_id,
                Policy.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all_with_property(
        self,
        organization_id: str | None = None,
        policy_type: str | None = None,
        sort_by: str = "expiration_date",
        sort_order: str = "asc",
        limit: int = 100,
    ) -> list[Policy]:
        """Get all policies with property info for list view.

        Args:
            organization_id: Optional organization filter.
            policy_type: Optional policy type filter.
            sort_by: Sort field.
            sort_order: Sort direction.
            limit: Maximum records.

        Returns:
            List of policies with property info.
        """
        stmt = (
            select(Policy)
            .join(InsuranceProgram, Policy.program_id == InsuranceProgram.id)
            .join(Property, InsuranceProgram.property_id == Property.id)
            .options(
                selectinload(Policy.coverages),
                selectinload(Policy.program).selectinload(InsuranceProgram.property),
            )
            .where(
                Policy.deleted_at.is_(None),
                Property.deleted_at.is_(None),
            )
        )

        if organization_id:
            stmt = stmt.where(Property.organization_id == organization_id)
        if policy_type:
            stmt = stmt.where(Policy.policy_type == policy_type)

        # Apply sorting
        sort_column = getattr(Policy, sort_by, Policy.expiration_date)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc().nullslast())
        else:
            stmt = stmt.order_by(sort_column.asc().nullsfirst())

        stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_expiring_policies(
        self,
        days_ahead: int = 90,
        organization_id: str | None = None,
        limit: int = 50,
    ) -> list[Policy]:
        """Get policies expiring within a certain number of days.

        Args:
            days_ahead: Number of days to look ahead.
            organization_id: Optional organization filter.
            limit: Maximum records.

        Returns:
            List of expiring policies ordered by expiration date.
        """
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        stmt = (
            select(Policy)
            .join(InsuranceProgram, Policy.program_id == InsuranceProgram.id)
            .join(Property, InsuranceProgram.property_id == Property.id)
            .options(
                selectinload(Policy.program).selectinload(InsuranceProgram.property),
            )
            .where(
                Policy.deleted_at.is_(None),
                Property.deleted_at.is_(None),
                Policy.expiration_date.isnot(None),
                Policy.expiration_date >= today,
                Policy.expiration_date <= end_date,
            )
            .order_by(Policy.expiration_date.asc())
        )

        if organization_id:
            stmt = stmt.where(Property.organization_id == organization_id)

        stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_expiration_counts(
        self, organization_id: str | None = None
    ) -> dict[str, int]:
        """Get count of policies expiring in 30/60/90 day windows.

        Args:
            organization_id: Optional organization filter.

        Returns:
            Dictionary with expiration counts.
        """
        today = date.today()

        base_stmt = (
            select(func.count(Policy.id))
            .join(InsuranceProgram, Policy.program_id == InsuranceProgram.id)
            .join(Property, InsuranceProgram.property_id == Property.id)
            .where(
                Policy.deleted_at.is_(None),
                Property.deleted_at.is_(None),
                Policy.expiration_date.isnot(None),
                Policy.expiration_date >= today,
            )
        )

        if organization_id:
            base_stmt = base_stmt.where(Property.organization_id == organization_id)

        # 30 days
        stmt_30 = base_stmt.where(
            Policy.expiration_date <= today + timedelta(days=30)
        )
        result_30 = await self.session.execute(stmt_30)
        count_30 = result_30.scalar() or 0

        # 60 days (31-60)
        stmt_60 = base_stmt.where(
            Policy.expiration_date > today + timedelta(days=30),
            Policy.expiration_date <= today + timedelta(days=60),
        )
        result_60 = await self.session.execute(stmt_60)
        count_60 = result_60.scalar() or 0

        # 90 days (61-90)
        stmt_90 = base_stmt.where(
            Policy.expiration_date > today + timedelta(days=60),
            Policy.expiration_date <= today + timedelta(days=90),
        )
        result_90 = await self.session.execute(stmt_90)
        count_90 = result_90.scalar() or 0

        return {
            "expiring_30_days": count_30,
            "expiring_60_days": count_60,
            "expiring_90_days": count_90,
        }

    async def count_all(self, organization_id: str | None = None) -> int:
        """Count all policies.

        Args:
            organization_id: Optional organization filter.

        Returns:
            Total count of policies.
        """
        stmt = (
            select(func.count(Policy.id))
            .join(InsuranceProgram, Policy.program_id == InsuranceProgram.id)
            .join(Property, InsuranceProgram.property_id == Property.id)
            .where(
                Policy.deleted_at.is_(None),
                Property.deleted_at.is_(None),
            )
        )
        if organization_id:
            stmt = stmt.where(Property.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0


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
            deductible_pct=extraction.deductible_pct,
            deductible_minimum=(
                Decimal(str(extraction.deductible_minimum)) if extraction.deductible_minimum else None
            ),
            deductible_maximum=(
                Decimal(str(extraction.deductible_maximum)) if extraction.deductible_maximum else None
            ),
            coinsurance_pct=extraction.coinsurance_pct,
            waiting_period_hours=extraction.waiting_period_hours,
            valuation_type=extraction.valuation_type,
            margin_clause_pct=extraction.margin_clause_pct,
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
