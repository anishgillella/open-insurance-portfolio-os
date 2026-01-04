"""Embedding Pipeline Service.

This service handles the chunking and embedding pipeline for documents:
1. Chunk OCR text into smaller pieces
2. Generate embeddings for each chunk
3. Store embeddings in Pinecone
4. Update database with embedding metadata

This pipeline runs after document ingestion is complete.
"""

import logging
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.chunking_service import get_rag_chunking_service
from app.services.embeddings_service import EmbeddingsService, get_embeddings_service
from app.services.pinecone_service import PineconeService, get_pinecone_service

logger = logging.getLogger(__name__)


class EmbeddingPipelineError(Exception):
    """Base exception for embedding pipeline errors."""

    pass


class EmbeddingPipelineService:
    """Service for generating and storing document embeddings."""

    def __init__(
        self,
        session: AsyncSession,
        embeddings_service: EmbeddingsService | None = None,
        pinecone_service: PineconeService | None = None,
    ):
        """Initialize embedding pipeline service.

        Args:
            session: Database session.
            embeddings_service: Embeddings service instance.
            pinecone_service: Pinecone service instance.
        """
        self.session = session
        self.embeddings_service = embeddings_service or get_embeddings_service()
        self.pinecone_service = pinecone_service or get_pinecone_service()
        self.chunking_service = get_rag_chunking_service()

        # Repositories
        self.document_repo = DocumentRepository(session)
        self.chunk_repo = DocumentChunkRepository(session)

    async def process_document(
        self,
        document_id: str,
        force_reprocess: bool = False,
    ) -> dict[str, Any]:
        """Process a document through the embedding pipeline.

        Args:
            document_id: Document ID to process.
            force_reprocess: If True, delete existing chunks and reprocess.

        Returns:
            Dictionary with processing statistics.
        """
        logger.info(f"Starting embedding pipeline for document {document_id}")

        # Get document
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise EmbeddingPipelineError(f"Document not found: {document_id}")

        if not document.ocr_markdown:
            raise EmbeddingPipelineError(f"Document has no OCR text: {document_id}")

        # Check if already processed
        existing_chunks = await self.chunk_repo.get_by_document_id(document_id)
        if existing_chunks and not force_reprocess:
            logger.info(f"Document already has {len(existing_chunks)} chunks, skipping")
            return {
                "document_id": document_id,
                "status": "skipped",
                "chunks_existing": len(existing_chunks),
            }

        # Delete existing chunks if force reprocess
        if existing_chunks and force_reprocess:
            # Delete from Pinecone first
            pinecone_ids = [c.pinecone_id for c in existing_chunks if c.pinecone_id]
            if pinecone_ids:
                await self.pinecone_service.delete(ids=pinecone_ids)
                logger.info(f"Deleted {len(pinecone_ids)} vectors from Pinecone")

            # Delete from database
            await self.chunk_repo.delete_by_document_id(document_id, hard=True)
            logger.info(f"Deleted {len(existing_chunks)} chunks from database")

        # Step 1: Chunk the document
        chunks = self.chunking_service.chunk_document(document.ocr_markdown)
        logger.info(f"Created {len(chunks)} chunks from document")

        # Step 2: Create chunk records in database
        chunk_dicts = [chunk.to_dict() for chunk in chunks]
        db_chunks = await self.chunk_repo.create_chunks_batch(
            document_id=document_id,
            chunks=chunk_dicts,
            property_id=document.property_id,
            document_type=document.document_type,
            carrier=document.carrier,
            effective_date=document.effective_date,
        )
        logger.info(f"Created {len(db_chunks)} chunk records in database")

        # Step 3: Generate embeddings
        chunk_texts = [chunk.content for chunk in chunks]
        embedding_result = await self.embeddings_service.embed_texts_batch(chunk_texts)
        logger.info(
            f"Generated {len(embedding_result.embeddings)} embeddings, "
            f"{embedding_result.total_tokens} tokens"
        )

        # Step 4: Prepare and upsert to Pinecone
        pinecone_vectors = []
        embedding_updates = []

        for db_chunk, emb_result in zip(db_chunks, embedding_result.embeddings):
            # Use chunk ID as Pinecone vector ID
            pinecone_id = db_chunk.id

            # Build metadata for filtering
            metadata = self._build_chunk_metadata(document, db_chunk)

            pinecone_vectors.append({
                "id": pinecone_id,
                "values": emb_result.embedding,
                "metadata": metadata,
            })

            embedding_updates.append({
                "chunk_id": db_chunk.id,
                "pinecone_id": pinecone_id,
            })

        # Upsert to Pinecone
        upserted_count = await self.pinecone_service.upsert(pinecone_vectors)
        logger.info(f"Upserted {upserted_count} vectors to Pinecone")

        # Step 5: Update database with embedding info
        await self.chunk_repo.update_embedding_info_batch(
            embedding_updates,
            embedding_model=embedding_result.model,
        )
        logger.info("Updated chunk records with embedding info")

        return {
            "document_id": document_id,
            "status": "completed",
            "chunks_created": len(db_chunks),
            "embeddings_generated": len(embedding_result.embeddings),
            "tokens_used": embedding_result.total_tokens,
            "vectors_upserted": upserted_count,
        }

    async def process_unembedded_documents(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Process documents that haven't been embedded yet.

        Args:
            limit: Maximum number of documents to process.

        Returns:
            List of processing results.
        """
        # Find documents with OCR text but no chunks
        # This is a simplified approach - in production you might want a dedicated status field
        documents = await self._get_unembedded_documents(limit)

        results = []
        for document in documents:
            try:
                result = await self.process_document(document.id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process document {document.id}: {e}")
                results.append({
                    "document_id": document.id,
                    "status": "failed",
                    "error": str(e),
                })

        return results

    async def _get_unembedded_documents(self, limit: int = 10) -> list[Document]:
        """Get documents that have OCR text but no chunks.

        Args:
            limit: Maximum number of documents to return.

        Returns:
            List of Document objects.
        """
        from sqlalchemy import select, not_, exists

        from app.models.document import Document
        from app.models.document_chunk import DocumentChunk

        # Subquery to check if document has chunks
        has_chunks = (
            select(DocumentChunk.id)
            .where(DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.deleted_at.is_(None))
            .exists()
        )

        stmt = (
            select(Document)
            .where(
                Document.ocr_markdown.isnot(None),
                Document.ocr_markdown != "",
                not_(has_chunks),
                Document.deleted_at.is_(None),
            )
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _build_chunk_metadata(
        self,
        document: Document,
        chunk: Any,
    ) -> dict[str, Any]:
        """Build Pinecone metadata for a chunk.

        Args:
            document: Source document.
            chunk: Chunk database record.

        Returns:
            Metadata dictionary for Pinecone.
        """
        metadata: dict[str, Any] = {
            "document_id": document.id,
            "document_name": document.file_name,
            "chunk_index": chunk.chunk_index,
        }

        # Add optional fields
        if document.property_id:
            metadata["property_id"] = document.property_id
        if document.document_type:
            metadata["document_type"] = document.document_type
        if document.carrier:
            metadata["carrier"] = document.carrier
        if document.policy_number:
            metadata["policy_number"] = document.policy_number
        if chunk.page_start is not None:
            metadata["page_start"] = chunk.page_start
        if chunk.page_end is not None:
            metadata["page_end"] = chunk.page_end
        if chunk.chunk_type:
            metadata["chunk_type"] = chunk.chunk_type
        if document.effective_date:
            metadata["effective_date"] = document.effective_date.isoformat()
        if document.expiration_date:
            metadata["expiration_date"] = document.expiration_date.isoformat()

        return metadata


# Singleton instance
_embedding_pipeline_service: EmbeddingPipelineService | None = None


async def get_embedding_pipeline_service(
    session: AsyncSession,
) -> EmbeddingPipelineService:
    """Get embedding pipeline service instance.

    Args:
        session: Database session.

    Returns:
        EmbeddingPipelineService instance.
    """
    return EmbeddingPipelineService(session)
