"""Answer Generation Service using Gemini 2.5 Flash via OpenRouter.

This service handles the generation part of RAG:
1. Build prompt from context and query
2. Stream response from LLM
3. Extract citations and confidence
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx

from app.core.config import settings
from app.services.rag_query_service import QueryContext, RetrievedChunk

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


class AnswerGenerationError(Exception):
    """Base exception for answer generation errors."""

    pass


class AnswerGenerationAPIError(AnswerGenerationError):
    """Raised when OpenRouter API returns an error."""

    pass


@dataclass
class GeneratedAnswer:
    """A generated answer with sources."""

    content: str
    sources: list[dict[str, Any]]
    confidence: float
    tokens_used: int
    latency_ms: int
    model: str


@dataclass
class StreamChunk:
    """A chunk of streamed response."""

    content: str
    is_final: bool = False
    sources: list[dict[str, Any]] | None = None
    confidence: float | None = None


SYSTEM_PROMPT = """You are an AI assistant specialized in analyzing commercial real estate insurance documents. Your role is to help users understand their insurance coverage, policies, and certificates.

IMPORTANT GUIDELINES:
1. Answer questions based ONLY on the provided context documents
2. If the answer is not in the context, say "I don't have information about that in the provided documents"
3. Always cite your sources by referring to the document name and page number
4. Be precise with numbers, dates, limits, and coverage details
5. When discussing coverage limits, always specify the type (per occurrence, aggregate, etc.)
6. If information seems unclear or conflicting, point this out to the user
7. Use clear, professional language appropriate for insurance discussions

When citing sources, use this format: [Source: Document Name, Page X]"""


class AnswerGenerationService:
    """Service for generating answers using LLM."""

    def __init__(self, api_key: str | None = None):
        """Initialize answer generation service.

        Args:
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL

        if not self.api_key:
            logger.warning("OpenRouter API key not configured")

    def _build_messages(
        self,
        query: str,
        context: QueryContext,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        """Build message list for LLM.

        Args:
            query: User query.
            context: Retrieved context.
            conversation_history: Previous messages.

        Returns:
            List of message dicts.
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add context as a system message
        if context.chunks:
            context_content = f"""Here are the relevant documents to answer the user's question:

{context.to_prompt_context()}

Use only information from these documents to answer the question. Cite sources appropriately."""
            messages.append({"role": "system", "content": context_content})

        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        # Add current query
        messages.append({"role": "user", "content": query})

        return messages

    async def generate(
        self,
        query: str,
        context: QueryContext,
        conversation_history: list[dict[str, str]] | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> GeneratedAnswer:
        """Generate an answer for a query.

        Args:
            query: User query.
            context: Retrieved context with chunks.
            conversation_history: Previous conversation messages.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            GeneratedAnswer with content and metadata.
        """
        if not self.api_key:
            raise AnswerGenerationError("OpenRouter API key not configured")

        start_time = time.time()

        messages = self._build_messages(query, context, conversation_history)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )
                raise AnswerGenerationAPIError(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )

            result = response.json()

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract response
        choices = result.get("choices", [])
        if not choices:
            raise AnswerGenerationError("No response from LLM")

        content = choices[0].get("message", {}).get("content", "")
        usage = result.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)

        # Build sources from context
        sources = [chunk.to_citation_dict() for chunk in context.chunks]

        # Estimate confidence based on context relevance
        confidence = self._estimate_confidence(context, content)

        return GeneratedAnswer(
            content=content,
            sources=sources,
            confidence=confidence,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model=self.model,
        )

    async def generate_stream(
        self,
        query: str,
        context: QueryContext,
        conversation_history: list[dict[str, str]] | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> AsyncIterator[StreamChunk]:
        """Stream generate an answer for a query.

        Args:
            query: User query.
            context: Retrieved context with chunks.
            conversation_history: Previous conversation messages.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Yields:
            StreamChunk objects with content pieces.
        """
        if not self.api_key:
            raise AnswerGenerationError("OpenRouter API key not configured")

        messages = self._build_messages(query, context, conversation_history)

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise AnswerGenerationAPIError(
                        f"OpenRouter API error: {response.status_code} - {error_text.decode()}"
                    )

                full_content = ""
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data = line[6:]  # Remove "data: " prefix

                    if data == "[DONE]":
                        # Final chunk with sources
                        sources = [chunk.to_citation_dict() for chunk in context.chunks]
                        confidence = self._estimate_confidence(context, full_content)
                        yield StreamChunk(
                            content="",
                            is_final=True,
                            sources=sources,
                            confidence=confidence,
                        )
                        break

                    try:
                        chunk_data = json.loads(data)
                        delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_content += content
                            yield StreamChunk(content=content)
                    except json.JSONDecodeError:
                        continue

    def _estimate_confidence(self, context: QueryContext, answer: str) -> float:
        """Estimate confidence based on context relevance.

        Args:
            context: Retrieved context.
            answer: Generated answer.

        Returns:
            Confidence score between 0 and 1.
        """
        if not context.chunks:
            return 0.3  # Low confidence without context

        # Average similarity scores of chunks
        avg_score = sum(c.score for c in context.chunks) / len(context.chunks)

        # Adjust based on answer content
        if "I don't have information" in answer or "not found" in answer.lower():
            return min(0.5, avg_score)

        # Higher confidence if answer cites sources
        if "[Source:" in answer or "page" in answer.lower():
            avg_score = min(1.0, avg_score + 0.1)

        return round(avg_score, 2)


# Singleton instance
_answer_generation_service: AnswerGenerationService | None = None


def get_answer_generation_service() -> AnswerGenerationService:
    """Get or create answer generation service instance."""
    global _answer_generation_service
    if _answer_generation_service is None:
        _answer_generation_service = AnswerGenerationService()
    return _answer_generation_service
