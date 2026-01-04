"""Repository for Financial operations."""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial import Financial
from app.repositories.base import BaseRepository
from app.schemas.document import InvoiceExtraction

logger = logging.getLogger(__name__)


class FinancialRepository(BaseRepository[Financial]):
    """Repository for Financial CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Financial, session)

    async def create_from_extraction(
        self,
        extraction: InvoiceExtraction,
        program_id: str,
        document_id: str,
    ) -> Financial:
        """Create a financial record from invoice extraction.

        Args:
            extraction: Invoice extraction data.
            program_id: Insurance program ID.
            document_id: Source document ID.

        Returns:
            Created Financial record.
        """
        # Parse amounts safely
        def to_decimal(value) -> Decimal | None:
            if value is None:
                return None
            try:
                return Decimal(str(value))
            except (ValueError, TypeError):
                return None

        financial = await self.create(
            program_id=program_id,
            document_id=document_id,
            record_type="invoice",
            total=to_decimal(extraction.total_amount),
            taxes=to_decimal(extraction.taxes),
            fees=to_decimal(extraction.fees),
            invoice_date=extraction.invoice_date,
            due_date=extraction.due_date,
            status="pending",
            extraction_confidence=extraction.confidence,
        )

        logger.info(
            f"Created financial record from invoice: {financial.id} "
            f"(total: {financial.total})"
        )
        return financial

    async def get_by_program(
        self,
        program_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Financial]:
        """Get financials for a program.

        Args:
            program_id: Insurance program ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of financials.
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            program_id=program_id,
        )

    async def get_by_document(
        self,
        document_id: str,
    ) -> Financial | None:
        """Get financial record for a document.

        Args:
            document_id: Document ID.

        Returns:
            Financial or None.
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
