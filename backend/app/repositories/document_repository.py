"""Repository for Document operations."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.property import Property
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

    async def find_by_filename_and_org(
        self,
        file_name: str,
        organization_id: str,
    ) -> Document | None:
        """Find an existing document by filename and organization.

        Used for deduplication - checks if a document with the same name
        already exists for this organization.

        Args:
            file_name: The file name to search for.
            organization_id: Organization ID.

        Returns:
            Existing Document or None if not found.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.deleted_at.is_(None),
                self.model.file_name == file_name,
                self.model.organization_id == organization_id,
            )
            .order_by(self.model.created_at.desc())  # Get most recent if multiple
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def reset_for_reprocessing(
        self,
        document_id: str,
        file_url: str | None = None,
        file_size_bytes: int | None = None,
    ) -> Document | None:
        """Reset a document for reprocessing.

        Clears OCR and extraction data so the document can be reprocessed.

        Args:
            document_id: Document ID.
            file_url: Optional new file URL.
            file_size_bytes: Optional new file size.

        Returns:
            Updated Document or None if not found.
        """
        update_data = {
            "ocr_status": ProcessingStatus.PENDING.value,
            "extraction_status": ProcessingStatus.PENDING.value,
            "ocr_started_at": None,
            "ocr_completed_at": None,
            "extraction_started_at": None,
            "extraction_completed_at": None,
            "ocr_markdown": None,
            "ocr_error": None,
            "extraction_json": None,
            "extraction_error": None,
            "extraction_confidence": None,
            "document_type": None,
            "document_subtype": None,
            "carrier": None,
            "policy_number": None,
            "effective_date": None,
            "expiration_date": None,
        }

        if file_url:
            update_data["file_url"] = file_url
        if file_size_bytes:
            update_data["file_size_bytes"] = file_size_bytes

        return await self.update(document_id, **update_data)

    async def upsert_from_file(
        self,
        file_name: str,
        file_url: str,
        organization_id: str,
        property_id: str | None = None,
        file_size_bytes: int | None = None,
        file_type: str | None = None,
        mime_type: str | None = None,
    ) -> tuple[Document, bool]:
        """Create or update a document record (atomic upsert).

        Uses PostgreSQL ON CONFLICT to handle race conditions when
        multiple processes try to create the same document simultaneously.

        Args:
            file_name: Original file name.
            file_url: File URL or local path.
            organization_id: Organization ID.
            property_id: Optional property ID.
            file_size_bytes: File size in bytes.
            file_type: File extension.
            mime_type: MIME type.

        Returns:
            Tuple of (Document instance, is_new: bool).
            is_new is True if created, False if updated existing.
        """
        from uuid import uuid4

        new_id = str(uuid4())

        # Prepare insert values
        insert_values = {
            "id": new_id,
            "file_name": file_name,
            "file_url": file_url,
            "organization_id": organization_id,
            "property_id": property_id,
            "file_size_bytes": file_size_bytes,
            "file_type": file_type,
            "mime_type": mime_type,
            "upload_status": ProcessingStatus.COMPLETED.value,
            "ocr_status": ProcessingStatus.PENDING.value,
            "extraction_status": ProcessingStatus.PENDING.value,
        }

        # Prepare update values for ON CONFLICT (reset for reprocessing)
        update_on_conflict = {
            "file_url": file_url,
            "file_size_bytes": file_size_bytes,
            "ocr_status": ProcessingStatus.PENDING.value,
            "extraction_status": ProcessingStatus.PENDING.value,
            "ocr_started_at": None,
            "ocr_completed_at": None,
            "extraction_started_at": None,
            "extraction_completed_at": None,
            "ocr_markdown": None,
            "ocr_error": None,
            "extraction_json": None,
            "extraction_error": None,
            "extraction_confidence": None,
            "document_type": None,
            "document_subtype": None,
            "carrier": None,
            "policy_number": None,
            "effective_date": None,
            "expiration_date": None,
            "updated_at": datetime.now(timezone.utc),
        }

        # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
        stmt = (
            insert(Document)
            .values(**insert_values)
            .on_conflict_do_update(
                index_elements=["file_name", "organization_id"],
                index_where=Document.deleted_at.is_(None),
                set_=update_on_conflict,
            )
            .returning(Document.id, Document.created_at, Document.updated_at)
        )

        result = await self.session.execute(stmt)
        row = result.fetchone()
        await self.session.flush()

        # Fetch the full document
        document = await self.get_by_id(row[0])

        # Determine if it was created or updated
        # If created_at == updated_at (approximately), it's new
        is_new = row[1] == row[2] if row[1] and row[2] else True

        logger.info(
            f"{'Created' if is_new else 'Updated'} document: {file_name} (id: {document.id})"
        )

        return document, is_new

    async def list_all(
        self,
        organization_id: str | None = None,
        property_id: str | None = None,
        limit: int = 500,
    ) -> list[Document]:
        """List all documents with optional filtering.

        Args:
            organization_id: Optional filter by organization.
            property_id: Optional filter by property.
            limit: Maximum number of records.

        Returns:
            List of documents.
        """
        stmt = select(self.model).where(self.model.deleted_at.is_(None))

        if organization_id:
            stmt = stmt.where(self.model.organization_id == organization_id)

        if property_id:
            stmt = stmt.where(self.model.property_id == property_id)

        stmt = stmt.order_by(self.model.created_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_with_property_names(
        self,
        organization_id: str | None = None,
        property_id: str | None = None,
        limit: int = 500,
    ) -> list[tuple[Document, str | None]]:
        """List all documents with property names via JOIN.

        Args:
            organization_id: Optional filter by organization.
            property_id: Optional filter by property.
            limit: Maximum number of records.

        Returns:
            List of tuples (Document, property_name).
        """
        stmt = (
            select(Document, Property.name)
            .outerjoin(Property, Document.property_id == Property.id)
            .where(Document.deleted_at.is_(None))
        )

        if organization_id:
            stmt = stmt.where(Document.organization_id == organization_id)

        if property_id:
            stmt = stmt.where(Document.property_id == property_id)

        stmt = stmt.order_by(Document.created_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.all())
