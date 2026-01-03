"""Repository for Certificate operations."""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificate import Certificate
from app.repositories.base import BaseRepository
from app.schemas.document import COIExtraction

logger = logging.getLogger(__name__)


class CertificateRepository(BaseRepository[Certificate]):
    """Repository for Certificate CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Certificate, session)

    async def create_from_extraction(
        self,
        extraction: COIExtraction,
        program_id: str,
        document_id: str | None = None,
        lender_id: str | None = None,
        certificate_type: str = "coi",
    ) -> Certificate:
        """Create a certificate from extraction result.

        Args:
            extraction: Extracted COI/EOP data.
            program_id: Insurance program ID.
            document_id: Source document ID.
            lender_id: Lender ID if this is an EOP.
            certificate_type: Type of certificate (coi or eop).

        Returns:
            Created Certificate instance.
        """
        # Convert policies list to JSONB-compatible format
        policies_data = None
        if extraction.policies:
            policies_data = [
                pol.model_dump(mode="json") for pol in extraction.policies
            ]

        return await self.create(
            program_id=program_id,
            document_id=document_id,
            lender_id=lender_id,
            certificate_type=certificate_type,
            certificate_number=extraction.certificate_number,
            revision_number=extraction.revision_number,
            # Producer info
            producer_name=extraction.producer_name,
            producer_address=extraction.producer_address,
            producer_phone=extraction.producer_phone,
            producer_email=extraction.producer_email,
            producer_reference=extraction.producer_reference,
            # Insured info
            insured_name=extraction.insured_name,
            insured_address=extraction.insured_address,
            # Holder info
            holder_name=extraction.holder_name,
            holder_address=extraction.holder_address,
            # Insurers mapping
            insurers=extraction.insurers if extraction.insurers else {},
            # Policies JSONB
            policies=policies_data,
            # Property coverage
            property_limit=Decimal(str(extraction.property_limit)) if extraction.property_limit else None,
            # GL coverage
            gl_each_occurrence=Decimal(str(extraction.gl_each_occurrence)) if extraction.gl_each_occurrence else None,
            gl_general_aggregate=Decimal(str(extraction.gl_general_aggregate)) if extraction.gl_general_aggregate else None,
            gl_products_completed=Decimal(str(extraction.gl_products_completed)) if extraction.gl_products_completed else None,
            gl_personal_advertising=Decimal(str(extraction.gl_personal_advertising)) if extraction.gl_personal_advertising else None,
            gl_damage_to_rented=Decimal(str(extraction.gl_damage_to_rented)) if extraction.gl_damage_to_rented else None,
            gl_medical_expense=Decimal(str(extraction.gl_medical_expense)) if extraction.gl_medical_expense else None,
            gl_coverage_form=extraction.gl_coverage_form,
            gl_aggregate_limit_applies_per=extraction.gl_aggregate_limit_applies_per,
            # Auto coverage
            auto_combined_single=Decimal(str(extraction.auto_combined_single)) if extraction.auto_combined_single else None,
            auto_bodily_injury_per_person=Decimal(str(extraction.auto_bodily_injury_per_person)) if extraction.auto_bodily_injury_per_person else None,
            auto_bodily_injury_per_accident=Decimal(str(extraction.auto_bodily_injury_per_accident)) if extraction.auto_bodily_injury_per_accident else None,
            auto_property_damage=Decimal(str(extraction.auto_property_damage)) if extraction.auto_property_damage else None,
            auto_types=extraction.auto_types if extraction.auto_types else None,
            # Umbrella coverage
            umbrella_limit=Decimal(str(extraction.umbrella_limit)) if extraction.umbrella_limit else None,
            umbrella_aggregate=Decimal(str(extraction.umbrella_aggregate)) if extraction.umbrella_aggregate else None,
            umbrella_deductible=Decimal(str(extraction.umbrella_deductible)) if extraction.umbrella_deductible else None,
            umbrella_retention=Decimal(str(extraction.umbrella_retention)) if extraction.umbrella_retention else None,
            umbrella_coverage_form=extraction.umbrella_coverage_form,
            # Workers comp
            workers_comp_each_accident=Decimal(str(extraction.workers_comp_each_accident)) if extraction.workers_comp_each_accident else None,
            workers_comp_disease_ea_employee=Decimal(str(extraction.workers_comp_disease_ea_employee)) if extraction.workers_comp_disease_ea_employee else None,
            workers_comp_disease_policy_limit=Decimal(str(extraction.workers_comp_disease_policy_limit)) if extraction.workers_comp_disease_policy_limit else None,
            workers_comp_per_statute=extraction.workers_comp_per_statute,
            workers_comp_other=extraction.workers_comp_other,
            workers_comp_excluded_partners=extraction.workers_comp_excluded_partners,
            # Description of operations
            description_of_operations=extraction.description_of_operations,
            # Additional insureds
            additional_insureds=extraction.additional_insureds if extraction.additional_insureds else None,
            subrogation_waiver_applies=extraction.subrogation_waiver_applies or False,
            # Cancellation
            cancellation_notice_days=extraction.cancellation_notice_days,
            cancellation_terms=extraction.cancellation_terms,
            # Authorized rep
            authorized_representative=extraction.authorized_representative,
            # Dates
            issue_date=extraction.issue_date,
            # Lender-specific (for EOPs)
            loan_number=extraction.loan_number,
            mortgagee_clause=extraction.mortgagee_clause,
            loss_payee_clause=extraction.loss_payee_clause,
            # Confidence
            extraction_confidence=extraction.confidence,
        )

    async def get_by_program(
        self,
        program_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Certificate]:
        """Get certificates for an insurance program.

        Args:
            program_id: Insurance program ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of certificates.
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            program_id=program_id,
        )

    async def get_by_lender(
        self,
        lender_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Certificate]:
        """Get certificates for a lender.

        Args:
            lender_id: Lender ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of certificates.
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            lender_id=lender_id,
        )

    async def get_by_certificate_number(self, certificate_number: str) -> Certificate | None:
        """Get a certificate by certificate number.

        Args:
            certificate_number: Certificate number.

        Returns:
            Certificate or None if not found.
        """
        stmt = select(self.model).where(
            self.model.deleted_at.is_(None),
            self.model.certificate_number == certificate_number,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
