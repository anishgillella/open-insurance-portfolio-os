"""Tests for RAG services (Phase 3).

These tests cover:
- ChunkingService (RAG-optimized)
- EmbeddingsService
- PineconeService
- RAGQueryService
- AnswerGenerationService
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.chunking_service import (
    ChunkingService,
    DocumentChunk,
    get_rag_chunking_service,
)
from app.services.embeddings_service import (
    EmbeddingsService,
    EmbeddingResult,
    BatchEmbeddingResult,
)
from app.services.pinecone_service import (
    PineconeService,
    VectorMatch,
    QueryResult,
)


# ============================================================================
# ChunkingService Tests
# ============================================================================


class TestChunkingService:
    """Tests for ChunkingService."""

    def test_single_chunk_for_small_document(self):
        """Small documents should be returned as single chunk."""
        service = ChunkingService(
            max_chars=4000,
            overlap_chars=400,
            single_pass_threshold=5000,
        )

        text = "This is a short document.\n\n<!-- Page 1 -->\nSome content here."
        chunks = service.chunk_document(text)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].index == 0
        assert chunks[0].char_start == 0
        assert chunks[0].char_end == len(text)

    def test_multiple_chunks_for_large_document(self):
        """Large documents should be split into multiple chunks."""
        service = ChunkingService(
            max_chars=100,
            overlap_chars=20,
            single_pass_threshold=150,
        )

        # Create a document larger than threshold
        text = "<!-- Page 1 -->\n" + "A" * 200 + "\n\n<!-- Page 2 -->\n" + "B" * 200

        chunks = service.chunk_document(text)

        assert len(chunks) > 1
        # Verify all content is covered
        assert all(chunk.content for chunk in chunks)
        # Verify ordering
        assert all(chunks[i].index == i for i in range(len(chunks)))

    def test_page_boundary_detection(self):
        """Chunks should respect page boundaries when possible."""
        service = ChunkingService(
            max_chars=100,
            overlap_chars=20,
            single_pass_threshold=50,
        )

        text = "<!-- Page 1 -->\nContent page 1\n\n<!-- Page 2 -->\nContent page 2"

        chunks = service.chunk_document(text)

        # Check page range is tracked
        for chunk in chunks:
            assert chunk.start_page is not None

    def test_chunk_type_detection_text(self):
        """Text-only chunks should be detected."""
        service = ChunkingService()

        text = "This is plain text without any tables.\nJust paragraphs."
        chunks = service.chunk_document(text)

        assert chunks[0].chunk_type == "text"

    def test_chunk_type_detection_table(self):
        """Table chunks should be detected."""
        service = ChunkingService()

        text = """| Header 1 | Header 2 |
| --- | --- |
| Cell 1 | Cell 2 |
| Cell 3 | Cell 4 |
| Cell 5 | Cell 6 |"""

        chunks = service.chunk_document(text)

        assert chunks[0].chunk_type == "table"

    def test_chunk_type_detection_mixed(self):
        """Mixed content should be detected."""
        service = ChunkingService()

        text = """Some introductory text.

| Header 1 | Header 2 |
| --- | --- |
| Cell 1 | Cell 2 |

More text after the table."""

        chunks = service.chunk_document(text)

        assert chunks[0].chunk_type == "mixed"

    def test_to_dict_method(self):
        """DocumentChunk.to_dict() should return proper dictionary."""
        chunk = DocumentChunk(
            index=0,
            content="Test content",
            start_page=1,
            end_page=2,
            char_start=0,
            char_end=100,
            chunk_type="text",
        )

        result = chunk.to_dict()

        assert result["index"] == 0
        assert result["content"] == "Test content"
        assert result["start_page"] == 1
        assert result["end_page"] == 2
        assert result["char_start"] == 0
        assert result["char_end"] == 100
        assert result["chunk_type"] == "text"

    def test_get_rag_chunking_service(self):
        """get_rag_chunking_service should return properly configured service."""
        service = get_rag_chunking_service()

        # Check RAG-optimized settings
        assert service.max_chars == 4000
        assert service.overlap_chars == 400
        assert service.single_pass_threshold == 5000


# ============================================================================
# EmbeddingsService Tests
# ============================================================================


class TestEmbeddingsService:
    """Tests for EmbeddingsService."""

    @pytest.mark.asyncio
    async def test_embed_text_success(self):
        """Test successful single text embedding."""
        service = EmbeddingsService(api_key="test-key")

        mock_response = {
            "data": [{"embedding": [0.1] * 1024, "index": 0}],
            "usage": {"total_tokens": 10},
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )

            result = await service.embed_text("Test text")

            assert isinstance(result, EmbeddingResult)
            assert len(result.embedding) == 1024
            assert result.token_count == 10

    @pytest.mark.asyncio
    async def test_embed_query_returns_vector(self):
        """Test embed_query returns just the vector."""
        service = EmbeddingsService(api_key="test-key")

        mock_response = {
            "data": [{"embedding": [0.1] * 1024, "index": 0}],
            "usage": {"total_tokens": 5},
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )

            result = await service.embed_query("What is my coverage?")

            assert isinstance(result, list)
            assert len(result) == 1024

    @pytest.mark.asyncio
    async def test_embed_texts_batch(self):
        """Test batch embedding of multiple texts."""
        service = EmbeddingsService(api_key="test-key")

        mock_response = {
            "data": [
                {"embedding": [0.1] * 1024, "index": 0},
                {"embedding": [0.2] * 1024, "index": 1},
            ],
            "usage": {"total_tokens": 20},
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )

            result = await service.embed_texts_batch(["Text 1", "Text 2"])

            assert isinstance(result, BatchEmbeddingResult)
            assert len(result.embeddings) == 2
            assert result.total_tokens == 20

    def test_estimate_tokens(self):
        """Test token estimation."""
        service = EmbeddingsService(api_key="test-key")

        # ~4 chars per token
        text = "This is a test"  # 14 chars
        estimate = service.estimate_tokens(text)

        assert estimate == 3  # 14 // 4

    def test_estimate_cost(self):
        """Test cost estimation."""
        service = EmbeddingsService(api_key="test-key")

        # $0.02 per 1M tokens
        cost = service.estimate_cost(1_000_000)

        assert cost == 0.02


# ============================================================================
# PineconeService Tests
# ============================================================================


class TestPineconeService:
    """Tests for PineconeService."""

    @pytest.mark.asyncio
    async def test_upsert_success(self):
        """Test successful vector upsert."""
        service = PineconeService(
            api_key="test-key",
            host="https://test.pinecone.io",
            index_name="test-index",
        )

        mock_response = {"upsertedCount": 2}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )

            vectors = [
                {"id": "v1", "values": [0.1] * 1024, "metadata": {"doc": "test"}},
                {"id": "v2", "values": [0.2] * 1024, "metadata": {"doc": "test2"}},
            ]

            count = await service.upsert(vectors)

            assert count == 2

    @pytest.mark.asyncio
    async def test_query_success(self):
        """Test successful vector query."""
        service = PineconeService(
            api_key="test-key",
            host="https://test.pinecone.io",
            index_name="test-index",
        )

        mock_response = {
            "matches": [
                {"id": "v1", "score": 0.95, "metadata": {"doc": "test"}},
                {"id": "v2", "score": 0.85, "metadata": {"doc": "test2"}},
            ],
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )

            result = await service.query(
                vector=[0.1] * 1024,
                top_k=5,
            )

            assert isinstance(result, QueryResult)
            assert len(result.matches) == 2
            assert result.matches[0].score == 0.95

    def test_build_metadata_filter_single(self):
        """Test building filter with single condition."""
        service = PineconeService(
            api_key="test-key",
            host="https://test.pinecone.io",
            index_name="test-index",
        )

        filter_dict = service.build_metadata_filter(document_type="policy")

        assert filter_dict == {"document_type": {"$eq": "policy"}}

    def test_build_metadata_filter_multiple(self):
        """Test building filter with multiple conditions."""
        service = PineconeService(
            api_key="test-key",
            host="https://test.pinecone.io",
            index_name="test-index",
        )

        filter_dict = service.build_metadata_filter(
            document_type="policy",
            carrier="Seneca",
        )

        assert "$and" in filter_dict
        assert len(filter_dict["$and"]) == 2

    def test_build_metadata_filter_empty(self):
        """Test building filter with no conditions returns None."""
        service = PineconeService(
            api_key="test-key",
            host="https://test.pinecone.io",
            index_name="test-index",
        )

        filter_dict = service.build_metadata_filter()

        assert filter_dict is None


# ============================================================================
# Integration-style Tests (mocked)
# ============================================================================


class TestRAGPipelineIntegration:
    """Integration tests for RAG pipeline (with mocks)."""

    @pytest.mark.asyncio
    async def test_chunk_and_embed_flow(self):
        """Test the chunking -> embedding flow."""
        # Chunk a document
        chunking_service = get_rag_chunking_service()
        text = "<!-- Page 1 -->\nThis is test content for the RAG pipeline."

        chunks = chunking_service.chunk_document(text)
        assert len(chunks) >= 1

        # Mock embedding generation
        embeddings_service = EmbeddingsService(api_key="test-key")

        mock_response = {
            "data": [{"embedding": [0.1] * 1024, "index": 0}],
            "usage": {"total_tokens": 15},
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )

            result = await embeddings_service.embed_texts_batch(
                [c.content for c in chunks]
            )

            assert len(result.embeddings) == len(chunks)

    @pytest.mark.asyncio
    async def test_query_and_retrieve_flow(self):
        """Test the query embedding -> search flow."""
        # Mock embedding service
        embeddings_service = EmbeddingsService(api_key="test-key")

        # Mock Pinecone service
        pinecone_service = PineconeService(
            api_key="test-key",
            host="https://test.pinecone.io",
            index_name="test-index",
        )

        # Mock query embedding
        mock_embed_response = {
            "data": [{"embedding": [0.1] * 1024, "index": 0}],
            "usage": {"total_tokens": 5},
        }

        # Mock Pinecone query
        mock_query_response = {
            "matches": [
                {
                    "id": "chunk-1",
                    "score": 0.92,
                    "metadata": {
                        "document_id": "doc-1",
                        "document_name": "Policy.pdf",
                        "page_start": 1,
                    },
                },
            ],
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            # Configure mock to return different responses based on URL
            def side_effect(*args, **kwargs):
                url = args[0] if args else kwargs.get("url", "")
                if "openai" in str(url):
                    return MagicMock(
                        status_code=200,
                        json=MagicMock(return_value=mock_embed_response),
                    )
                else:
                    return MagicMock(
                        status_code=200,
                        json=MagicMock(return_value=mock_query_response),
                    )

            mock_post.side_effect = side_effect

            # Generate query embedding
            query_vector = await embeddings_service.embed_query("What is my coverage?")
            assert len(query_vector) == 1024

            # Query Pinecone
            result = await pinecone_service.query(vector=query_vector, top_k=5)
            assert len(result.matches) == 1
            assert result.matches[0].score > 0.9
