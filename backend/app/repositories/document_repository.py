"""Repository for Document operations."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base import BaseRepository
from app.schemas.document import DocumentClassification, ExtractionResult, ProcessingStatus

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)

    async def create_from_file(
        self,
        file_name: str,
        file_url: str,
        organization_id: str,
        property_id: str | None = None,
        file_size_bytes: int | None = None,
        file_type: str | None = None,
        mime_type: str | None = None,
    ) -> Document:
        """Create a document record from a file.

        Args:
            file_name: Original file name.
            file_url: File URL or local path.
            organization_id: Organization ID.
            property_id: Optional property ID.
            file_size_bytes: File size in bytes.
            file_type: File extension.
            mime_type: MIME type.

        Returns:
            Created Document instance.
        """
        return await self.create(
            file_name=file_name,
            file_url=file_url,
            organization_id=organization_id,
            property_id=property_id,
            file_size_bytes=file_size_bytes,
            file_type=file_type,
            mime_type=mime_type,
            upload_status=ProcessingStatus.COMPLETED.value,
            ocr_status=ProcessingStatus.PENDING.value,
            extraction_status=ProcessingStatus.PENDING.value,
        )

    async def update_ocr_status(
        self,
        document_id: str,
        status: ProcessingStatus,
        ocr_markdown: str | None = None,
        page_count: int | None = None,
        error: str | None = None,
    ) -> Document | None:
        """Update OCR processing status.

        Args:
            document_id: Document ID.
            status: New OCR status.
            ocr_markdown: Extracted markdown text.
            page_count: Number of pages.
            error: Error message if failed.

        Returns:
            Updated Document or None if not found.
        """
        update_data = {"ocr_status": status.value}

        if status == ProcessingStatus.PROCESSING:
            update_data["ocr_started_at"] = datetime.now(timezone.utc)
        elif status == ProcessingStatus.COMPLETED:
            update_data["ocr_completed_at"] = datetime.now(timezone.utc)
            if ocr_markdown:
                update_data["ocr_markdown"] = ocr_markdown
            if page_count:
                update_data["page_count"] = page_count
        elif status == ProcessingStatus.FAILED:
            update_data["ocr_error"] = error

        return await self.update(document_id, **update_data)

    async def update_classification(
        self,
        document_id: str,
        classification: DocumentClassification,
    ) -> Document | None:
        """Update document with classification results.

        Args:
            document_id: Document ID.
            classification: Classification result.

        Returns:
            Updated Document or None if not found.
        """
        return await self.update(
            document_id,
            document_type=classification.document_type.value,
            document_subtype=classification.document_subtype,
            carrier=classification.carrier_name,
            policy_number=classification.policy_number,
            effective_date=classification.effective_date,
            expiration_date=classification.expiration_date,
        )

    async def update_extraction_status(
        self,
        document_id: str,
        status: ProcessingStatus,
        extraction_result: ExtractionResult | None = None,
        error: str | None = None,
    ) -> Document | None:
        """Update extraction processing status.

        Args:
            document_id: Document ID.
            status: New extraction status.
            extraction_result: Extraction result.
            error: Error message if failed.

        Returns:
            Updated Document or None if not found.
        """
        update_data = {"extraction_status": status.value}

        if status == ProcessingStatus.PROCESSING:
            update_data["extraction_started_at"] = datetime.now(timezone.utc)
        elif status == ProcessingStatus.COMPLETED:
            update_data["extraction_completed_at"] = datetime.now(timezone.utc)
            if extraction_result:
                update_data["extraction_json"] = extraction_result.model_dump(mode="json")
                update_data["extraction_confidence"] = extraction_result.overall_confidence
                update_data["needs_human_review"] = extraction_result.overall_confidence < 0.8
        elif status == ProcessingStatus.FAILED:
            update_data["extraction_error"] = error

        return await self.update(document_id, **update_data)

    async def get_by_organization(
        self,
        organization_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """Get documents for an organization.

        Args:
            organization_id: Organization ID.
            limit: Maximum records.
            offset: Records to skip.

        Returns:
            List of documents.
        """
        return await self.get_all(
            limit=limit,
            offset=offset,
            organization_id=organization_id,
        )

    async def get_pending_ocr(self, limit: int = 10) -> list[Document]:
        """Get documents pending OCR processing.

        Args:
            limit: Maximum records.

        Returns:
            List of documents pending OCR.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.ocr_status == ProcessingStatus.PENDING.value,
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_extraction(self, limit: int = 10) -> list[Document]:
        """Get documents pending extraction.

        Args:
            limit: Maximum records.

        Returns:
            List of documents pending extraction.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.ocr_status == ProcessingStatus.COMPLETED.value,
                self.model.extraction_status == ProcessingStatus.PENDING.value,
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
