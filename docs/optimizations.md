# Open Insurance Platform - Optimization Roadmap

> **Status**: Phase 3 (RAG Intelligence Layer) Complete
> **Last Updated**: January 2026
> **Priority**: Reference document for future iterations

---

## Current Implementation Assessment

### What's Built (Phase 1-3)

| Component | Status | Quality |
|-----------|--------|---------|
| Database Schema | ✅ Complete | 25 tables, proper relationships, RLS |
| Document Pipeline | ✅ Complete | OCR → Classification → Extraction → Storage |
| RAG System | ✅ Complete | Embeddings, vector search, LLM generation, streaming |
| API Layer | ✅ Complete | RESTful, proper schemas, SSE streaming |
| Conversation History | ✅ Complete | Multi-turn chat with context |

### Current Performance Metrics

| Metric | Value | Target |
|--------|-------|--------|
| End-to-end chat latency | ~6-7 seconds | < 5 seconds |
| Embedding generation | ~2 seconds/batch | Acceptable |
| Document ingestion | ~10-15 seconds/doc | Acceptable |
| Retrieval precision | Good (manual assessment) | Needs metrics |

---

## Optimization Categories

### 1. Production Hardening (Priority: HIGH)

These should be implemented before production deployment.

#### 1.1 Error Monitoring
```python
# Add Sentry integration
# pip install sentry-sdk[fastapi]

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)
```

**Files to modify:**
- `app/main.py` - Initialize Sentry
- `app/core/config.py` - Add Sentry DSN config

#### 1.2 Structured Logging with Correlation IDs
```python
# Add request ID middleware
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

**Benefits:**
- Trace requests across services
- Debug production issues faster
- Correlate logs with user sessions

#### 1.3 Rate Limiting
```python
# Add slowapi for rate limiting
# pip install slowapi

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/")
@limiter.limit("10/minute")
async def chat(request: ChatRequest, ...):
    ...
```

**Recommended limits:**
- Chat endpoint: 10 requests/minute per IP
- Embed endpoint: 5 requests/minute per IP
- Ingest endpoint: 20 requests/minute per IP

#### 1.4 Input Validation & Sanitization
- Max message length validation (already done: 10,000 chars)
- SQL injection protection (SQLAlchemy handles this)
- XSS prevention in stored content
- File type validation on upload

---

### 2. Observability & Metrics (Priority: HIGH)

#### 2.1 RAG Quality Metrics

Create `app/services/metrics_service.py`:
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RAGMetrics:
    query: str
    retrieval_count: int
    avg_similarity_score: float
    min_similarity_score: float
    max_similarity_score: float
    retrieval_latency_ms: int
    generation_latency_ms: int
    total_latency_ms: int
    tokens_used: int
    estimated_cost: float
    timestamp: datetime

class MetricsService:
    async def record_rag_query(self, metrics: RAGMetrics):
        # Store in DB or send to analytics
        pass

    async def get_quality_dashboard(self) -> dict:
        # Return aggregated metrics
        pass
```

**Metrics to track:**
- Average retrieval score per query
- Retrieval latency (P50, P95, P99)
- Generation latency
- Token usage and cost
- Queries with no relevant results
- User feedback (thumbs up/down)

#### 2.2 Cost Tracking

| Service | Cost | Tracking Method |
|---------|------|-----------------|
| OpenAI Embeddings | $0.02/1M tokens | Count tokens per batch |
| OpenRouter (Gemini) | ~$0.30/1M input, $2.50/1M output | Parse usage from response |
| Pinecone | $0.0004/query | Count queries |

```python
# Add to answer_generation_service.py
def _track_costs(self, usage: dict):
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    cost = (input_tokens * 0.30 + output_tokens * 2.50) / 1_000_000
    logger.info(f"LLM cost: ${cost:.6f}")
```

#### 2.3 Health Dashboard Endpoint

Add to `app/api/v1/endpoints/health.py`:
```python
@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_async_session)):
    return {
        "documents": await count_documents(db),
        "chunks": await count_chunks(db),
        "embedded_chunks": await count_embedded_chunks(db),
        "conversations": await count_conversations(db),
        "messages_today": await count_messages_today(db),
        "avg_latency_ms": await get_avg_latency(db),
        "pinecone_vectors": await get_pinecone_stats(),
    }
```

---

### 3. Advanced RAG Features (Priority: MEDIUM)

#### 3.1 Query Rewriting

Improve retrieval by expanding/rewriting user queries:

```python
async def rewrite_query(self, query: str, history: list) -> str:
    """Expand query with context from conversation history."""
    if not history:
        return query

    # Use LLM to rewrite query with context
    prompt = f"""Given this conversation history and current question,
    rewrite the question to be self-contained:

    History: {history[-3:]}
    Question: {query}

    Rewritten question:"""

    return await self._call_llm(prompt)
```

**When to implement:** If users report follow-up questions not working well.

#### 3.2 Hybrid Search (Keyword + Vector)

Combine BM25/keyword search with vector search:

```python
async def hybrid_search(self, query: str, top_k: int = 5):
    # Vector search
    vector_results = await self.pinecone_service.query(
        vector=await self.embed_query(query),
        top_k=top_k * 2,
    )

    # Keyword search (PostgreSQL full-text)
    keyword_results = await self.chunk_repo.search_by_keywords(
        query=query,
        limit=top_k * 2,
    )

    # Reciprocal Rank Fusion to combine
    return self._rrf_combine(vector_results, keyword_results, k=60)
```

**When to implement:** If vector search misses exact policy numbers or specific terms.

#### 3.3 Re-ranking with Cross-Encoder

Add Cohere Rerank or cross-encoder for better precision:

```python
# pip install cohere
import cohere

async def rerank_chunks(self, query: str, chunks: list, top_k: int = 5):
    co = cohere.Client(api_key=settings.cohere_api_key)

    results = co.rerank(
        query=query,
        documents=[c.content for c in chunks],
        top_n=top_k,
        model="rerank-english-v2.0",
    )

    return [chunks[r.index] for r in results]
```

**Cost:** ~$1 per 1000 searches
**When to implement:** If retrieval precision is consistently low.

#### 3.4 Confidence Thresholds

```python
MIN_CONFIDENCE_THRESHOLD = 0.4

async def retrieve(self, query: str, ...):
    context = await self._retrieve_chunks(query)

    if not context.chunks:
        return self._no_results_response()

    avg_score = sum(c.score for c in context.chunks) / len(context.chunks)

    if avg_score < MIN_CONFIDENCE_THRESHOLD:
        return self._low_confidence_response(context)

    return context
```

#### 3.5 User Feedback Loop

Add thumbs up/down to messages:

```sql
-- Add to messages table
ALTER TABLE messages ADD COLUMN feedback VARCHAR(10); -- 'positive', 'negative', null
ALTER TABLE messages ADD COLUMN feedback_at TIMESTAMP WITH TIME ZONE;
```

```python
@router.post("/messages/{message_id}/feedback")
async def submit_feedback(
    message_id: str,
    feedback: Literal["positive", "negative"],
    db: AsyncSession = Depends(get_async_session),
):
    await update_message_feedback(db, message_id, feedback)
    return {"status": "ok"}
```

---

### 4. Performance Optimizations (Priority: LOW)

#### 4.1 Query Embedding Cache

Cache embeddings for repeated queries:

```python
from functools import lru_cache
import hashlib

class EmbeddingsService:
    _cache: dict[str, list[float]] = {}

    async def embed_query(self, query: str) -> list[float]:
        cache_key = hashlib.md5(query.encode()).hexdigest()

        if cache_key in self._cache:
            return self._cache[cache_key]

        embedding = await self._generate_embedding(query)
        self._cache[cache_key] = embedding
        return embedding
```

**Savings:** ~200ms per cached query

#### 4.2 Async Embedding in Ingestion

Run embedding generation as background task:

```python
from fastapi import BackgroundTasks

@router.post("/ingest")
async def ingest_document(
    ...,
    background_tasks: BackgroundTasks,
):
    # Ingest document (OCR, classification, extraction)
    result = await ingestion_service.ingest_file(...)

    # Queue embedding for background processing
    background_tasks.add_task(
        embedding_pipeline.process_document,
        document_id=result.document_id,
    )

    return result
```

#### 4.3 Connection Pooling Optimization

```python
# In app/core/database.py
engine = create_async_engine(
    settings.database_url,
    pool_size=20,          # Increase from default 5
    max_overflow=30,       # Increase from default 10
    pool_timeout=30,
    pool_recycle=1800,     # Recycle connections every 30 min
    pool_pre_ping=True,
)
```

---

### 5. Testing & CI/CD (Priority: HIGH)

#### 5.1 Integration Tests

```python
# tests/test_rag_integration.py
@pytest.mark.asyncio
async def test_full_rag_pipeline():
    # 1. Ingest a test document
    ingest_response = await client.post("/v1/documents/ingest", ...)

    # 2. Embed the document
    embed_response = await client.post("/v1/chat/embed", ...)

    # 3. Query the document
    chat_response = await client.post("/v1/chat/", json={
        "message": "What is the coverage limit?",
        "stream": False,
    })

    # 4. Verify response quality
    assert chat_response.status_code == 200
    assert "coverage" in chat_response.json()["content"].lower()
    assert len(chat_response.json()["sources"]) > 0
```

#### 5.2 Load Testing

```bash
# Using locust
# pip install locust

# locustfile.py
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def chat(self):
        self.client.post("/v1/chat/", json={
            "message": "What is my liability coverage?",
            "stream": False,
        })
```

**Targets:**
- 10 concurrent users
- < 10 second P95 latency
- < 1% error rate

#### 5.3 GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pytest tests/ -v --cov=app

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff
      - run: ruff check app/
```

---

### 6. Frontend Demo (Priority: HIGH for Demo)

#### 6.1 Minimal Next.js Chat UI

```
frontend/
├── app/
│   ├── page.tsx          # Chat interface
│   ├── layout.tsx        # App layout
│   └── globals.css       # Tailwind styles
├── components/
│   ├── ChatInput.tsx
│   ├── MessageList.tsx
│   └── SourceCard.tsx
├── package.json
└── tailwind.config.js
```

**Key features:**
- Real-time streaming with SSE
- Source citations with page links
- Conversation history sidebar
- Document upload interface

#### 6.2 Tech Stack

- Next.js 14 (App Router)
- Tailwind CSS
- shadcn/ui components
- Vercel deployment

---

## Implementation Priority Matrix

| Optimization | Impact | Effort | Priority | When to Implement |
|-------------|--------|--------|----------|-------------------|
| Error monitoring (Sentry) | High | Low | P0 | Before production |
| Structured logging | High | Low | P0 | Before production |
| Rate limiting | Medium | Low | P0 | Before production |
| Frontend demo | High | Medium | P0 | For demo/investor meetings |
| RAG metrics tracking | High | Medium | P1 | First week of production |
| Cost tracking | Medium | Low | P1 | First week of production |
| Integration tests | High | Medium | P1 | Before production |
| CI/CD pipeline | High | Low | P1 | Before production |
| Query rewriting | Medium | Medium | P2 | If follow-ups fail |
| Hybrid search | Medium | High | P2 | If keyword search needed |
| Re-ranker | Medium | Medium | P2 | If precision issues |
| User feedback | Medium | Low | P2 | After initial users |
| Embedding cache | Low | Low | P3 | At scale |
| Async embedding | Low | Medium | P3 | If ingestion is slow |

---

## Decision Log

### Why We Skipped These for MVP

1. **Re-ranker**: Vector search with metadata filtering is sufficient for insurance documents which have structured, domain-specific content.

2. **Hybrid Search**: Most queries are semantic ("What's my coverage?") not keyword-based ("Policy number ABC123"). Add if users request exact term matching.

3. **Embedding Cache**: Query volume is low enough that 200ms savings isn't worth the complexity.

4. **Async Embedding**: Ingestion is typically batch (many documents at once), not real-time. Current sync approach is fine.

### Why We Chose These Approaches

1. **OpenAI Embeddings**: Best quality/cost ratio. text-embedding-3-small at 1024 dims is optimal for Pinecone.

2. **Gemini 2.5 Flash via OpenRouter**: 1M+ context window, fast, cost-effective. OpenRouter provides fallback to other providers.

3. **Pinecone Serverless**: No infrastructure management, auto-scales, fast queries.

4. **Chunk Size 4000 chars**: Balances context (enough info per chunk) with precision (not too broad).

---

## Metrics to Watch

Once in production, monitor these weekly:

1. **Retrieval Quality**
   - Average top-5 similarity score
   - % of queries with no results
   - % of queries with < 0.3 similarity

2. **User Engagement**
   - Messages per conversation
   - Feedback ratio (positive/negative)
   - Repeat users

3. **Cost**
   - OpenAI embedding cost per day
   - OpenRouter LLM cost per day
   - Cost per query

4. **Performance**
   - P50, P95, P99 latency
   - Error rate
   - Timeout rate

---

## Resources

- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Pinecone Query Optimization](https://docs.pinecone.io/docs/query-data)
- [LangChain RAG Patterns](https://python.langchain.com/docs/tutorials/rag/)
