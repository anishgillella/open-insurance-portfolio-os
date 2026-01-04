"""Repository for DocumentChunk CRUD operations."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """Repository for document chunk operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository.

        Args:
            session: Async database session.
        """
        super().__init__(DocumentChunk, session)

    async def create_chunks_batch(
        self,
        document_id: str,
        chunks: list[dict[str, Any]],
        property_id: str | None = None,
        document_type: str | None = None,
        policy_type: str | None = None,
        carrier: str | None = None,
        effective_date: Any | None = None,
    ) -> list[DocumentChunk]:
        """Create multiple chunks for a document in batch.

        Args:
            document_id: Document ID.
            chunks: List of chunk dictionaries with content and metadata.
            property_id: Optional property ID.
            document_type: Document type for filtering.
            policy_type: Policy type for filtering.
            carrier: Carrier name for filtering.
            effective_date: Effective date for filtering.

        Returns:
            List of created DocumentChunk instances.
        """
        created_chunks = []

        for chunk_data in chunks:
            chunk = DocumentChunk(
                id=str(uuid4()),
                document_id=document_id,
                property_id=property_id,
                chunk_text=chunk_data["content"],
                chunk_index=chunk_data["index"],
                chunk_type=chunk_data.get("chunk_type"),
                section_title=chunk_data.get("section_title"),
                page_start=chunk_data.get("start_page"),
                page_end=chunk_data.get("end_page"),
                char_start=chunk_data.get("char_start"),
                char_end=chunk_data.get("char_end"),
                document_type=document_type,
                policy_type=policy_type,
                carrier=carrier,
                effective_date=effective_date,
            )
            self.session.add(chunk)
            created_chunks.append(chunk)

        await self.session.flush()

        for chunk in created_chunks:
            await self.session.refresh(chunk)

        logger.info(f"Created {len(created_chunks)} chunks for document {document_id}")
        return created_chunks

    async def get_by_document_id(self, document_id: str) -> list[DocumentChunk]:
        """Get all chunks for a document.

        Args:
            document_id: Document ID.

        Returns:
            List of DocumentChunk instances.
        """
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.deleted_at.is_(None),
            )
            .order_by(DocumentChunk.chunk_index)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_unembedded_chunks(self, limit: int = 100) -> list[DocumentChunk]:
        """Get chunks that haven't been embedded yet.

        Args:
            limit: Maximum number of chunks to return.

        Returns:
            List of DocumentChunk instances without embeddings.
        """
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.pinecone_id.is_(None),
                DocumentChunk.deleted_at.is_(None),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_embedding_info(
        self,
        chunk_id: str,
        pinecone_id: str,
        embedding_model: str,
    ) -> DocumentChunk | None:
        """Update chunk with embedding information.

        Args:
            chunk_id: Chunk ID.
            pinecone_id: Pinecone vector ID.
            embedding_model: Model used for embedding.

        Returns:
            Updated DocumentChunk or None if not found.
        """
        stmt = (
            update(DocumentChunk)
            .where(DocumentChunk.id == chunk_id)
            .values(
                pinecone_id=pinecone_id,
                embedding_model=embedding_model,
                embedded_at=datetime.now(timezone.utc),
            )
            .returning(DocumentChunk)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def update_embedding_info_batch(
        self,
        updates: list[dict[str, str]],
        embedding_model: str,
    ) -> int:
        """Update multiple chunks with embedding information.

        Args:
            updates: List of dicts with 'chunk_id' and 'pinecone_id'.
            embedding_model: Model used for embedding.

        Returns:
            Number of chunks updated.
        """
        now = datetime.now(timezone.utc)
        count = 0

        for update_data in updates:
            stmt = (
                update(DocumentChunk)
                .where(DocumentChunk.id == update_data["chunk_id"])
                .values(
                    pinecone_id=update_data["pinecone_id"],
                    embedding_model=embedding_model,
                    embedded_at=now,
                )
            )
            await self.session.execute(stmt)
            count += 1

        await self.session.flush()
        logger.info(f"Updated embedding info for {count} chunks")
        return count

    async def delete_by_document_id(self, document_id: str, hard: bool = False) -> int:
        """Delete all chunks for a document.

        Args:
            document_id: Document ID.
            hard: If True, permanently delete. If False, soft delete.

        Returns:
            Number of chunks deleted.
        """
        if hard:
            stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
            result = await self.session.execute(stmt)
            count = result.rowcount
        else:
            stmt = (
                update(DocumentChunk)
                .where(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.deleted_at.is_(None),
                )
                .values(deleted_at=datetime.now(timezone.utc))
            )
            result = await self.session.execute(stmt)
            count = result.rowcount

        await self.session.flush()
        logger.info(f"Deleted {count} chunks for document {document_id} (hard={hard})")
        return count

    async def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[DocumentChunk]:
        """Get chunks by their IDs.

        Args:
            chunk_ids: List of chunk IDs.

        Returns:
            List of DocumentChunk instances.
        """
        if not chunk_ids:
            return []

        stmt = select(DocumentChunk).where(
            DocumentChunk.id.in_(chunk_ids),
            DocumentChunk.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_chunks_by_pinecone_ids(
        self, pinecone_ids: list[str]
    ) -> list[DocumentChunk]:
        """Get chunks by their Pinecone IDs.

        Args:
            pinecone_ids: List of Pinecone vector IDs.

        Returns:
            List of DocumentChunk instances.
        """
        if not pinecone_ids:
            return []

        stmt = select(DocumentChunk).where(
            DocumentChunk.pinecone_id.in_(pinecone_ids),
            DocumentChunk.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
