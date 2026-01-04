"""Embeddings Service using OpenAI text-embedding-3-small.

This service generates vector embeddings for text chunks using OpenAI's
embedding model with reduced dimensionality (1024) for Pinecone storage.
"""

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# OpenAI API configuration
OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1024  # Reduced from 1536 for Pinecone
MAX_BATCH_SIZE = 100  # OpenAI batch limit
MAX_TOKENS_PER_REQUEST = 8191  # Model limit


class EmbeddingsServiceError(Exception):
    """Base exception for embeddings service errors."""

    pass


class EmbeddingsAPIError(EmbeddingsServiceError):
    """Raised when OpenAI API returns an error."""

    pass


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    text: str
    embedding: list[float]
    token_count: int
    index: int


@dataclass
class BatchEmbeddingResult:
    """Result of batch embedding generation."""

    embeddings: list[EmbeddingResult]
    total_tokens: int
    model: str


class EmbeddingsService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self, api_key: str | None = None):
        """Initialize embeddings service.

        Args:
            api_key: OpenAI API key. Defaults to settings.openai_api_key.
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = EMBEDDING_MODEL
        self.dimensions = EMBEDDING_DIMENSIONS

        if not self.api_key:
            logger.warning("OpenAI API key not configured")

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            EmbeddingResult with embedding vector.

        Raises:
            EmbeddingsAPIError: If API call fails.
        """
        if not self.api_key:
            raise EmbeddingsServiceError("OpenAI API key not configured")

        if not text.strip():
            raise EmbeddingsServiceError("Cannot embed empty text")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENAI_EMBEDDINGS_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": text,
                    "dimensions": self.dimensions,
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenAI embeddings API error: {response.status_code} - {error_detail}")
                raise EmbeddingsAPIError(
                    f"OpenAI API error: {response.status_code} - {error_detail}"
                )

            result = response.json()

        embedding_data = result["data"][0]
        usage = result.get("usage", {})

        return EmbeddingResult(
            text=text,
            embedding=embedding_data["embedding"],
            token_count=usage.get("total_tokens", 0),
            index=0,
        )

    async def embed_texts_batch(
        self,
        texts: list[str],
        batch_size: int = MAX_BATCH_SIZE,
    ) -> BatchEmbeddingResult:
        """Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed.
            batch_size: Number of texts per batch (max 100).

        Returns:
            BatchEmbeddingResult with all embeddings.

        Raises:
            EmbeddingsAPIError: If API call fails.
        """
        if not self.api_key:
            raise EmbeddingsServiceError("OpenAI API key not configured")

        if not texts:
            return BatchEmbeddingResult(embeddings=[], total_tokens=0, model=self.model)

        # Filter out empty texts
        valid_texts = [(i, t) for i, t in enumerate(texts) if t.strip()]
        if not valid_texts:
            raise EmbeddingsServiceError("All texts are empty")

        all_embeddings: list[EmbeddingResult] = []
        total_tokens = 0

        # Process in batches
        for batch_start in range(0, len(valid_texts), batch_size):
            batch = valid_texts[batch_start : batch_start + batch_size]
            batch_texts = [t for _, t in batch]
            batch_indices = [i for i, _ in batch]

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    OPENAI_EMBEDDINGS_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": batch_texts,
                        "dimensions": self.dimensions,
                    },
                )

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(
                        f"OpenAI embeddings API error: {response.status_code} - {error_detail}"
                    )
                    raise EmbeddingsAPIError(
                        f"OpenAI API error: {response.status_code} - {error_detail}"
                    )

                result = response.json()

            usage = result.get("usage", {})
            total_tokens += usage.get("total_tokens", 0)

            for j, embedding_data in enumerate(result["data"]):
                original_index = batch_indices[j]
                all_embeddings.append(
                    EmbeddingResult(
                        text=batch_texts[j],
                        embedding=embedding_data["embedding"],
                        token_count=0,  # Token count is at batch level
                        index=original_index,
                    )
                )

            logger.debug(
                f"Embedded batch {batch_start // batch_size + 1}: "
                f"{len(batch)} texts, {usage.get('total_tokens', 0)} tokens"
            )

        logger.info(
            f"Generated {len(all_embeddings)} embeddings, {total_tokens} total tokens"
        )

        return BatchEmbeddingResult(
            embeddings=all_embeddings,
            total_tokens=total_tokens,
            model=self.model,
        )

    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query.

        This is a convenience method that returns just the embedding vector.

        Args:
            query: Search query text.

        Returns:
            Embedding vector (list of floats).
        """
        result = await self.embed_text(query)
        return result.embedding

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        This is a rough estimate - actual tokens may vary.
        Rule of thumb: ~4 characters per token for English.

        Args:
            text: Text to estimate.

        Returns:
            Estimated token count.
        """
        return len(text) // 4

    def estimate_cost(self, token_count: int) -> float:
        """Estimate cost for embedding generation.

        Based on OpenAI pricing: $0.02 per 1M tokens for text-embedding-3-small.

        Args:
            token_count: Number of tokens.

        Returns:
            Estimated cost in USD.
        """
        return (token_count / 1_000_000) * 0.02


# Singleton instance
_embeddings_service: EmbeddingsService | None = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service instance."""
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service
