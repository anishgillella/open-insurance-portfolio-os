"""RAG Query Service.

This service handles the retrieval part of RAG:
1. Embed user query
2. Search Pinecone for relevant chunks
3. Fetch chunk details from database
4. Build context for LLM generation
"""

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.embeddings_service import EmbeddingsService, get_embeddings_service
from app.services.pinecone_service import PineconeService, VectorMatch, get_pinecone_service

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A chunk retrieved from vector search with full context."""

    chunk_id: str
    document_id: str
    document_name: str
    content: str
    page_start: int | None
    page_end: int | None
    score: float
    metadata: dict[str, Any]

    def to_citation_dict(self) -> dict[str, Any]:
        """Convert to citation format for response."""
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page": self.page_start,
            "page_end": self.page_end,
            "snippet": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "score": self.score,
        }


@dataclass
class QueryContext:
    """Context assembled from retrieved chunks for LLM."""

    query: str
    chunks: list[RetrievedChunk]
    total_tokens_estimate: int

    def to_prompt_context(self) -> str:
        """Format chunks as context for LLM prompt."""
        context_parts = []

        for i, chunk in enumerate(self.chunks, 1):
            page_info = ""
            if chunk.page_start:
                if chunk.page_end and chunk.page_end != chunk.page_start:
                    page_info = f" (pages {chunk.page_start}-{chunk.page_end})"
                else:
                    page_info = f" (page {chunk.page_start})"

            context_parts.append(
                f"[Source {i}: {chunk.document_name}{page_info}]\n"
                f"{chunk.content}\n"
            )

        return "\n---\n".join(context_parts)


class RAGQueryService:
    """Service for RAG query processing and retrieval."""

    def __init__(
        self,
        session: AsyncSession,
        embeddings_service: EmbeddingsService | None = None,
        pinecone_service: PineconeService | None = None,
    ):
        """Initialize RAG query service.

        Args:
            session: Database session.
            embeddings_service: Embeddings service instance.
            pinecone_service: Pinecone service instance.
        """
        self.session = session
        self.embeddings_service = embeddings_service or get_embeddings_service()
        self.pinecone_service = pinecone_service or get_pinecone_service()

        # Repositories
        self.chunk_repo = DocumentChunkRepository(session)
        self.document_repo = DocumentRepository(session)

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        property_id: str | None = None,
        document_type: str | None = None,
        policy_type: str | None = None,
        carrier: str | None = None,
        min_score: float = 0.0,
    ) -> QueryContext:
        """Retrieve relevant chunks for a query.

        Args:
            query: User query text.
            top_k: Number of chunks to retrieve.
            property_id: Optional filter by property.
            document_type: Optional filter by document type.
            policy_type: Optional filter by policy type.
            carrier: Optional filter by carrier.
            min_score: Minimum similarity score threshold.

        Returns:
            QueryContext with retrieved chunks.
        """
        logger.info(f"Retrieving chunks for query: {query[:100]}...")

        # Step 1: Embed the query
        query_embedding = await self.embeddings_service.embed_query(query)
        logger.debug(f"Generated query embedding (dim={len(query_embedding)})")

        # Step 2: Build filter
        filter_dict = self.pinecone_service.build_metadata_filter(
            property_id=property_id,
            document_type=document_type,
            policy_type=policy_type,
            carrier=carrier,
        )

        # Step 3: Query Pinecone
        query_result = await self.pinecone_service.query(
            vector=query_embedding,
            top_k=top_k,
            filter=filter_dict,
            include_metadata=True,
        )
        logger.info(f"Pinecone returned {len(query_result.matches)} matches")

        # Step 4: Filter by minimum score
        filtered_matches = [
            m for m in query_result.matches
            if m.score >= min_score
        ]
        logger.debug(f"After score filter: {len(filtered_matches)} matches")

        if not filtered_matches:
            return QueryContext(
                query=query,
                chunks=[],
                total_tokens_estimate=0,
            )

        # Step 5: Fetch chunk details from database
        chunk_ids = [m.id for m in filtered_matches]
        db_chunks = await self.chunk_repo.get_chunks_by_ids(chunk_ids)
        chunk_map = {c.id: c for c in db_chunks}

        # Step 6: Build RetrievedChunk objects
        retrieved_chunks = []
        total_chars = 0

        for match in filtered_matches:
            db_chunk = chunk_map.get(match.id)
            if not db_chunk:
                logger.warning(f"Chunk not found in database: {match.id}")
                continue

            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=match.id,
                    document_id=db_chunk.document_id,
                    document_name=match.metadata.get("document_name", "Unknown"),
                    content=db_chunk.chunk_text,
                    page_start=db_chunk.page_start,
                    page_end=db_chunk.page_end,
                    score=match.score,
                    metadata=match.metadata,
                )
            )
            total_chars += len(db_chunk.chunk_text)

        # Estimate tokens (rough: ~4 chars per token)
        total_tokens_estimate = total_chars // 4

        logger.info(
            f"Retrieved {len(retrieved_chunks)} chunks, "
            f"~{total_tokens_estimate} tokens"
        )

        return QueryContext(
            query=query,
            chunks=retrieved_chunks,
            total_tokens_estimate=total_tokens_estimate,
        )

    async def retrieve_with_context(
        self,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
        top_k: int = 5,
        property_id: str | None = None,
        document_type: str | None = None,
        min_score: float = 0.3,
    ) -> QueryContext:
        """Retrieve chunks with conversation context consideration.

        This method can optionally use conversation history to improve
        query understanding (e.g., resolving pronouns).

        Args:
            query: Current user query.
            conversation_history: Previous messages for context.
            top_k: Number of chunks to retrieve.
            property_id: Optional property filter.
            document_type: Optional document type filter.
            min_score: Minimum similarity score.

        Returns:
            QueryContext with retrieved chunks.
        """
        # For now, use the query directly
        # Future enhancement: Use conversation history to expand/rewrite query
        enhanced_query = query

        if conversation_history:
            # Simple approach: Append last user message for context
            last_messages = [
                m["content"] for m in conversation_history[-3:]
                if m.get("role") == "user"
            ]
            if last_messages:
                # Combine recent queries for better context
                context_queries = last_messages[-2:] + [query]
                enhanced_query = " ".join(context_queries)
                logger.debug(f"Enhanced query with history: {enhanced_query[:200]}")

        return await self.retrieve(
            query=enhanced_query,
            top_k=top_k,
            property_id=property_id,
            document_type=document_type,
            min_score=min_score,
        )

    async def get_similar_documents(
        self,
        document_id: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find documents similar to a given document.

        Args:
            document_id: Source document ID.
            top_k: Number of similar documents to find.

        Returns:
            List of similar document info.
        """
        # Get chunks from source document
        source_chunks = await self.chunk_repo.get_by_document_id(document_id)
        if not source_chunks:
            return []

        # Use first chunk as representative
        source_chunk = source_chunks[0]

        # Get embedding from Pinecone
        vectors = await self.pinecone_service.fetch([source_chunk.pinecone_id])
        if not vectors or source_chunk.pinecone_id not in vectors:
            return []

        source_vector = vectors[source_chunk.pinecone_id].get("values", [])
        if not source_vector:
            return []

        # Query for similar, excluding same document
        result = await self.pinecone_service.query(
            vector=source_vector,
            top_k=top_k * 3,  # Get more to filter
            include_metadata=True,
        )

        # Group by document and return unique documents
        seen_docs = {document_id}  # Exclude source
        similar_docs = []

        for match in result.matches:
            doc_id = match.metadata.get("document_id")
            if doc_id and doc_id not in seen_docs:
                seen_docs.add(doc_id)
                similar_docs.append({
                    "document_id": doc_id,
                    "document_name": match.metadata.get("document_name"),
                    "similarity_score": match.score,
                    "document_type": match.metadata.get("document_type"),
                })

                if len(similar_docs) >= top_k:
                    break

        return similar_docs


async def get_rag_query_service(session: AsyncSession) -> RAGQueryService:
    """Get RAG query service instance.

    Args:
        session: Database session.

    Returns:
        RAGQueryService instance.
    """
    return RAGQueryService(session)
