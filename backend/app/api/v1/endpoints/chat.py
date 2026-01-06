"""Chat API endpoints for RAG-based Q&A.

This module provides endpoints for:
- Chat with streaming response (SSE)
- Conversation history
- Document embedding management
"""

import json
import logging
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.repositories.conversation_repository import ConversationRepository
from app.services.answer_generation_service import (
    AnswerGenerationService,
    get_answer_generation_service,
)
from app.services.embedding_pipeline_service import (
    EmbeddingPipelineService,
    get_embedding_pipeline_service,
)
from app.services.rag_query_service import RAGQueryService, get_rag_query_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: str | None = Field(
        default=None,
        description="Conversation ID. If not provided, a new conversation is created.",
    )
    property_id: str | None = Field(
        default=None,
        description="Optional: Filter to specific property",
    )
    document_type: str | None = Field(
        default=None,
        description="Optional: Filter by document type (policy, coi, invoice, etc.)",
    )
    stream: bool = Field(
        default=True,
        description="Whether to stream the response (SSE)",
    )


class ChatSource(BaseModel):
    """A source citation in chat response."""

    document_id: str
    document_name: str
    page: int | None = None
    page_end: int | None = None
    snippet: str
    score: float


class ChatResponse(BaseModel):
    """Response body for non-streaming chat."""

    conversation_id: str
    message_id: str
    content: str
    sources: list[ChatSource]
    confidence: float
    tokens_used: int
    latency_ms: int


class ConversationMessage(BaseModel):
    """A message in conversation history."""

    id: str
    role: str
    content: str
    sources: list[ChatSource] | None = None
    created_at: str


class ConversationResponse(BaseModel):
    """Response for conversation history."""

    conversation_id: str
    messages: list[ConversationMessage]
    message_count: int


class EmbedDocumentRequest(BaseModel):
    """Request to embed a document."""

    document_id: str
    force_reprocess: bool = False


class EmbedDocumentResponse(BaseModel):
    """Response from document embedding."""

    document_id: str
    status: str
    chunks_created: int | None = None
    embeddings_generated: int | None = None
    tokens_used: int | None = None
    error: str | None = None


# ============================================================================
# Chat Endpoints
# ============================================================================


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_async_session),
) -> ChatResponse | StreamingResponse:
    """
    Chat with the insurance documents using RAG.

    This endpoint:
    1. Retrieves relevant document chunks based on the query
    2. Generates an answer using Gemini 2.5 Flash
    3. Returns the answer with source citations

    If `stream=True` (default), returns a Server-Sent Events stream.
    If `stream=False`, returns a JSON response.
    """
    start_time = time.time()

    # Get or create conversation
    conversation_id = request.conversation_id or str(uuid4())
    conv_repo = ConversationRepository(db)
    conversation, is_new = await conv_repo.get_or_create(
        conversation_id=conversation_id,
        property_id=request.property_id,
        document_type=request.document_type,
    )

    # Get conversation history
    history_messages = []
    if not is_new:
        recent_messages = await conv_repo.get_recent_messages(
            conversation_id=conversation_id,
            limit=10,
        )
        history_messages = [
            {"role": m.role, "content": m.content}
            for m in recent_messages
        ]

    # Save user message
    user_message = await conv_repo.add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )

    # Initialize services
    rag_service = await get_rag_query_service(db)
    answer_service = get_answer_generation_service()

    # Retrieve relevant chunks
    context = await rag_service.retrieve_with_context(
        query=request.message,
        conversation_history=history_messages,
        top_k=10,
        property_id=request.property_id,
        document_type=request.document_type,
        min_score=0.15,
    )

    if request.stream:
        # Return streaming response
        return StreamingResponse(
            _stream_response(
                query=request.message,
                context=context,
                conversation_history=history_messages,
                conversation_id=conversation_id,
                conv_repo=conv_repo,
                answer_service=answer_service,
                db=db,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming response
    answer = await answer_service.generate(
        query=request.message,
        context=context,
        conversation_history=history_messages,
    )

    # Save assistant message
    assistant_message = await conv_repo.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer.content,
        sources=answer.sources,
        confidence=answer.confidence,
        tokens_used=answer.tokens_used,
        latency_ms=answer.latency_ms,
        model=answer.model,
    )

    await db.commit()

    latency_ms = int((time.time() - start_time) * 1000)

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=assistant_message.id,
        content=answer.content,
        sources=[ChatSource(**s) for s in answer.sources],
        confidence=answer.confidence,
        tokens_used=answer.tokens_used,
        latency_ms=latency_ms,
    )


async def _stream_response(
    query: str,
    context: Any,
    conversation_history: list[dict[str, str]],
    conversation_id: str,
    conv_repo: ConversationRepository,
    answer_service: AnswerGenerationService,
    db: AsyncSession,
):
    """Stream SSE response for chat.

    Yields Server-Sent Events with the following event types:
    - content: Text content chunk
    - sources: Source citations (at end)
    - done: Final event with metadata
    - error: Error event
    """
    full_content = ""
    sources = []
    confidence = 0.0

    try:
        async for chunk in answer_service.generate_stream(
            query=query,
            context=context,
            conversation_history=conversation_history,
        ):
            if chunk.is_final:
                sources = chunk.sources or []
                confidence = chunk.confidence or 0.0

                # Send sources event
                yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

                # Send done event
                done_data = {
                    "conversation_id": conversation_id,
                    "confidence": confidence,
                }
                yield f"event: done\ndata: {json.dumps(done_data)}\n\n"
            else:
                full_content += chunk.content
                # Send content event
                yield f"event: content\ndata: {json.dumps({'text': chunk.content})}\n\n"

        # Save assistant message after streaming completes
        await conv_repo.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_content,
            sources=sources,
            confidence=confidence,
        )
        await db.commit()

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_data = {"error": str(e)}
        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    limit: int = Query(default=50, le=100, description="Max messages to return"),
    db: AsyncSession = Depends(get_async_session),
) -> ConversationResponse:
    """
    Get conversation history.

    Returns the messages in a conversation, ordered by creation time.
    """
    conv_repo = ConversationRepository(db)

    conversation = await conv_repo.get_with_messages(
        conversation_id=conversation_id,
        message_limit=limit,
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = [
        ConversationMessage(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=[ChatSource(**s) for s in (m.sources or [])] if m.sources else None,
            created_at=m.created_at.isoformat(),
        )
        for m in conversation.messages
    ]

    return ConversationResponse(
        conversation_id=conversation_id,
        messages=messages,
        message_count=conversation.message_count,
    )


# ============================================================================
# Embedding Management Endpoints
# ============================================================================


@router.post("/embed", response_model=EmbedDocumentResponse)
async def embed_document(
    request: EmbedDocumentRequest,
    db: AsyncSession = Depends(get_async_session),
) -> EmbedDocumentResponse:
    """
    Generate embeddings for a document.

    This endpoint:
    1. Chunks the document's OCR text
    2. Generates embeddings for each chunk
    3. Stores embeddings in Pinecone
    4. Updates database with embedding metadata

    Use this to embed documents after ingestion, or to re-embed
    with updated chunking settings.
    """
    try:
        pipeline_service = await get_embedding_pipeline_service(db)

        result = await pipeline_service.process_document(
            document_id=request.document_id,
            force_reprocess=request.force_reprocess,
        )

        await db.commit()

        return EmbedDocumentResponse(
            document_id=result["document_id"],
            status=result["status"],
            chunks_created=result.get("chunks_created"),
            embeddings_generated=result.get("embeddings_generated"),
            tokens_used=result.get("tokens_used"),
        )

    except Exception as e:
        logger.error(f"Embedding error: {e}")
        return EmbedDocumentResponse(
            document_id=request.document_id,
            status="failed",
            error=str(e),
        )


@router.post("/embed-all", response_model=list[EmbedDocumentResponse])
async def embed_all_documents(
    limit: int = Query(default=10, le=50, description="Max documents to process"),
    db: AsyncSession = Depends(get_async_session),
) -> list[EmbedDocumentResponse]:
    """
    Generate embeddings for all unembedded documents.

    Processes documents that have OCR text but no embeddings yet.
    """
    try:
        pipeline_service = await get_embedding_pipeline_service(db)

        results = await pipeline_service.process_unembedded_documents(limit=limit)

        await db.commit()

        return [
            EmbedDocumentResponse(
                document_id=r["document_id"],
                status=r["status"],
                chunks_created=r.get("chunks_created"),
                embeddings_generated=r.get("embeddings_generated"),
                tokens_used=r.get("tokens_used"),
                error=r.get("error"),
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Batch embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
