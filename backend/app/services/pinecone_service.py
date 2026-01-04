"""Pinecone Service for vector storage and retrieval.

This service handles all interactions with Pinecone for storing
and querying document chunk embeddings.
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class PineconeServiceError(Exception):
    """Base exception for Pinecone service errors."""

    pass


class PineconeAPIError(PineconeServiceError):
    """Raised when Pinecone API returns an error."""

    pass


@dataclass
class VectorMatch:
    """A matched vector from Pinecone search."""

    id: str
    score: float
    metadata: dict[str, Any]


@dataclass
class QueryResult:
    """Result of a Pinecone query."""

    matches: list[VectorMatch]
    namespace: str


class PineconeService:
    """Service for vector storage and retrieval using Pinecone."""

    def __init__(
        self,
        api_key: str | None = None,
        host: str | None = None,
        index_name: str | None = None,
    ):
        """Initialize Pinecone service.

        Args:
            api_key: Pinecone API key. Defaults to settings.
            host: Pinecone host URL. Defaults to settings.
            index_name: Pinecone index name. Defaults to settings.
        """
        self.api_key = api_key or settings.pinecone_api_key
        self.host = host or settings.pinecone_host
        self.index_name = index_name or settings.pinecone_index_name
        self.dimensions = settings.pinecone_dimensions

        if not self.api_key:
            logger.warning("Pinecone API key not configured")
        if not self.host:
            logger.warning("Pinecone host not configured")

    def _get_headers(self) -> dict[str, str]:
        """Get headers for Pinecone API requests."""
        return {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def upsert(
        self,
        vectors: list[dict[str, Any]],
        namespace: str = "",
    ) -> int:
        """Upsert vectors to Pinecone.

        Args:
            vectors: List of vectors with id, values, and metadata.
                Example: [{"id": "chunk-1", "values": [...], "metadata": {...}}]
            namespace: Optional namespace for the vectors.

        Returns:
            Number of vectors upserted.

        Raises:
            PineconeAPIError: If API call fails.
        """
        if not self.api_key or not self.host:
            raise PineconeServiceError("Pinecone not configured")

        if not vectors:
            return 0

        url = f"{self.host}/vectors/upsert"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json={
                    "vectors": vectors,
                    "namespace": namespace,
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Pinecone upsert error: {response.status_code} - {error_detail}")
                raise PineconeAPIError(
                    f"Pinecone API error: {response.status_code} - {error_detail}"
                )

            result = response.json()

        upserted_count = result.get("upsertedCount", len(vectors))
        logger.info(f"Upserted {upserted_count} vectors to Pinecone")
        return upserted_count

    async def upsert_batch(
        self,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        metadata_list: list[dict[str, Any]],
        namespace: str = "",
        batch_size: int = 100,
    ) -> int:
        """Upsert vectors in batches.

        Args:
            chunk_ids: List of chunk IDs to use as vector IDs.
            embeddings: List of embedding vectors.
            metadata_list: List of metadata dicts for each vector.
            namespace: Optional namespace.
            batch_size: Vectors per batch.

        Returns:
            Total number of vectors upserted.
        """
        if len(chunk_ids) != len(embeddings) != len(metadata_list):
            raise PineconeServiceError("Mismatched lengths for ids, embeddings, and metadata")

        total_upserted = 0

        for i in range(0, len(chunk_ids), batch_size):
            batch_ids = chunk_ids[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]
            batch_metadata = metadata_list[i : i + batch_size]

            vectors = [
                {
                    "id": vid,
                    "values": emb,
                    "metadata": meta,
                }
                for vid, emb, meta in zip(batch_ids, batch_embeddings, batch_metadata)
            ]

            count = await self.upsert(vectors, namespace=namespace)
            total_upserted += count

        return total_upserted

    async def query(
        self,
        vector: list[float],
        top_k: int = 10,
        namespace: str = "",
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> QueryResult:
        """Query Pinecone for similar vectors.

        Args:
            vector: Query vector.
            top_k: Number of results to return.
            namespace: Optional namespace to query.
            filter: Optional metadata filter.
            include_metadata: Whether to include metadata in results.

        Returns:
            QueryResult with matched vectors.

        Raises:
            PineconeAPIError: If API call fails.
        """
        if not self.api_key or not self.host:
            raise PineconeServiceError("Pinecone not configured")

        url = f"{self.host}/query"

        request_body: dict[str, Any] = {
            "vector": vector,
            "topK": top_k,
            "namespace": namespace,
            "includeMetadata": include_metadata,
        }

        if filter:
            request_body["filter"] = filter

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=request_body,
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Pinecone query error: {response.status_code} - {error_detail}")
                raise PineconeAPIError(
                    f"Pinecone API error: {response.status_code} - {error_detail}"
                )

            result = response.json()

        matches = [
            VectorMatch(
                id=match["id"],
                score=match.get("score", 0.0),
                metadata=match.get("metadata", {}),
            )
            for match in result.get("matches", [])
        ]

        logger.debug(f"Pinecone query returned {len(matches)} matches")
        return QueryResult(matches=matches, namespace=namespace)

    async def delete(
        self,
        ids: list[str] | None = None,
        delete_all: bool = False,
        namespace: str = "",
        filter: dict[str, Any] | None = None,
    ) -> bool:
        """Delete vectors from Pinecone.

        Args:
            ids: List of vector IDs to delete.
            delete_all: If True, delete all vectors in namespace.
            namespace: Optional namespace.
            filter: Optional metadata filter for deletion.

        Returns:
            True if successful.

        Raises:
            PineconeAPIError: If API call fails.
        """
        if not self.api_key or not self.host:
            raise PineconeServiceError("Pinecone not configured")

        url = f"{self.host}/vectors/delete"

        request_body: dict[str, Any] = {"namespace": namespace}

        if delete_all:
            request_body["deleteAll"] = True
        elif ids:
            request_body["ids"] = ids
        elif filter:
            request_body["filter"] = filter
        else:
            raise PineconeServiceError("Must provide ids, filter, or delete_all=True")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=request_body,
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Pinecone delete error: {response.status_code} - {error_detail}")
                raise PineconeAPIError(
                    f"Pinecone API error: {response.status_code} - {error_detail}"
                )

        logger.info(f"Deleted vectors from Pinecone (ids={len(ids) if ids else 'all'})")
        return True

    async def fetch(
        self,
        ids: list[str],
        namespace: str = "",
    ) -> dict[str, dict[str, Any]]:
        """Fetch vectors by ID.

        Args:
            ids: List of vector IDs to fetch.
            namespace: Optional namespace.

        Returns:
            Dict mapping ID to vector data.

        Raises:
            PineconeAPIError: If API call fails.
        """
        if not self.api_key or not self.host:
            raise PineconeServiceError("Pinecone not configured")

        if not ids:
            return {}

        url = f"{self.host}/vectors/fetch"

        params = {"ids": ids}
        if namespace:
            params["namespace"] = namespace

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Pinecone fetch error: {response.status_code} - {error_detail}")
                raise PineconeAPIError(
                    f"Pinecone API error: {response.status_code} - {error_detail}"
                )

            result = response.json()

        return result.get("vectors", {})

    async def describe_index_stats(self) -> dict[str, Any]:
        """Get index statistics.

        Returns:
            Index statistics including vector count.

        Raises:
            PineconeAPIError: If API call fails.
        """
        if not self.api_key or not self.host:
            raise PineconeServiceError("Pinecone not configured")

        url = f"{self.host}/describe_index_stats"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json={},
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"Pinecone describe_index_stats error: {response.status_code} - {error_detail}"
                )
                raise PineconeAPIError(
                    f"Pinecone API error: {response.status_code} - {error_detail}"
                )

            return response.json()

    def build_metadata_filter(
        self,
        document_id: str | None = None,
        property_id: str | None = None,
        document_type: str | None = None,
        policy_type: str | None = None,
        carrier: str | None = None,
    ) -> dict[str, Any] | None:
        """Build a Pinecone metadata filter.

        Args:
            document_id: Filter by document ID.
            property_id: Filter by property ID.
            document_type: Filter by document type.
            policy_type: Filter by policy type.
            carrier: Filter by carrier name.

        Returns:
            Pinecone filter dict or None if no filters.
        """
        conditions = []

        if document_id:
            conditions.append({"document_id": {"$eq": document_id}})
        if property_id:
            conditions.append({"property_id": {"$eq": property_id}})
        if document_type:
            conditions.append({"document_type": {"$eq": document_type}})
        if policy_type:
            conditions.append({"policy_type": {"$eq": policy_type}})
        if carrier:
            conditions.append({"carrier": {"$eq": carrier}})

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}


# Singleton instance
_pinecone_service: PineconeService | None = None


def get_pinecone_service() -> PineconeService:
    """Get or create Pinecone service instance."""
    global _pinecone_service
    if _pinecone_service is None:
        _pinecone_service = PineconeService()
    return _pinecone_service
