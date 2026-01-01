# Decision Log

## Overview

This document records key technical and product decisions made during the design of Open Insurance. Each decision includes context, options considered, the choice made, and rationale.

---

## Decision Format

Each decision follows this template:

```
## [DECISION-ID] Decision Title

**Date:** YYYY-MM-DD
**Status:** Accepted | Superseded | Deprecated
**Deciders:** [Names/Roles]

### Context
What is the issue we're facing?

### Options Considered
1. Option A
2. Option B
3. Option C

### Decision
What did we decide?

### Rationale
Why did we make this decision?

### Consequences
What are the implications?
```

---

## Architecture Decisions

### ADR-001: Python Backend

**Date:** 2024-01-15
**Status:** Accepted

#### Context
We need to choose a backend language for the API and processing pipeline.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Python** | Strong AI/ML ecosystem, Pydantic native, team familiarity | Slower than compiled languages |
| **TypeScript/Node** | Same language as frontend, type safety | Less mature AI/ML libraries |
| **Go** | Fast, simple deployment | Less AI/ML tooling |

#### Decision
Use **Python** for the backend.

#### Rationale
1. **AI/ML ecosystem** — All major AI SDKs (OpenAI, Google, Mistral) are Python-first
2. **Pydantic** — Native tool for both API validation and LLM structured output
3. **Team familiarity** — Faster development with known technology
4. **Industry standard** — Most AI-focused startups use Python

#### Consequences
- Need to manage Python dependency complexity
- Async code patterns required for performance
- Frontend (TypeScript) and backend (Python) are separate

---

### ADR-002: FastAPI Framework

**Date:** 2024-01-15
**Status:** Accepted

#### Context
We need a Python web framework for the API.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **FastAPI** | Async native, Pydantic integration, auto docs | Newer, smaller community than Flask |
| **Flask** | Simple, mature, huge community | Sync by default, no native validation |
| **Django** | Batteries included, admin panel | Heavy for API-only use |

#### Decision
Use **FastAPI**.

#### Rationale
1. **Async native** — I/O heavy operations (OCR, LLM calls) benefit from async
2. **Pydantic integration** — Request/response validation matches our extraction schemas
3. **Auto documentation** — OpenAPI/Swagger generated automatically
4. **Modern** — Designed for current Python patterns

#### Consequences
- Team needs async Python knowledge
- Ecosystem slightly smaller than Flask
- Great developer experience

---

### ADR-003: PostgreSQL Database

**Date:** 2024-01-15
**Status:** Accepted

#### Context
We need a primary database for structured data.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **PostgreSQL** | Robust, JSON support, pgvector available | Need to manage/host |
| **MySQL** | Popular, well-known | Less JSON support |
| **MongoDB** | Flexible schema, good for documents | Harder to query relationally |

#### Decision
Use **PostgreSQL**.

#### Rationale
1. **Relational model fits domain** — Insurance data is highly relational
2. **JSON support** — Can store flexible data when needed
3. **pgvector option** — Could add vector search later if needed
4. **Reliability** — Battle-tested, excellent tooling

#### Consequences
- Need managed PostgreSQL (Railway, Supabase, AWS RDS)
- Schema migrations required
- SQL expertise needed

---

### ADR-004: Pinecone for Vector Storage

**Date:** 2024-01-15
**Status:** Accepted

#### Context
We need a vector database for semantic search (RAG).

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Pinecone** | Managed, simple, scales | Another service to manage, cost |
| **pgvector** | Uses existing PostgreSQL | Performance at scale unknown |
| **Weaviate** | Open source, self-host | Operational overhead |
| **Qdrant** | Open source, fast | Need to host and manage |

#### Decision
Use **Pinecone**.

#### Rationale
1. **Managed service** — No infrastructure to manage
2. **Simple API** — Easy to integrate
3. **Metadata filtering** — Filter before vector search (efficient)
4. **Starter tier** — Free for MVP scale

#### Consequences
- Vendor dependency
- Cost at scale (~$70/mo for production tier)
- Need to sync data between PostgreSQL and Pinecone

---

### ADR-005: SQLAlchemy ORM

**Date:** 2024-01-15
**Status:** Accepted

#### Context
We need an ORM for database operations.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **SQLAlchemy 2.0** | Industry standard, mature, async support | Verbose, learning curve |
| **SQLModel** | Pydantic + SQLAlchemy combined | Newer, smaller community |
| **Tortoise ORM** | Django-like, async native | Less mature |
| **Raw SQL** | Full control, no abstraction | Tedious, error-prone |

#### Decision
Use **SQLAlchemy 2.0** with async support.

#### Rationale
1. **Maturity** — Most widely used Python ORM
2. **Async support** — 2.0 added native async
3. **Ecosystem** — Alembic migrations, extensive documentation
4. **Flexibility** — Can drop to raw SQL when needed

#### Consequences
- More boilerplate than SQLModel
- Need to learn SQLAlchemy patterns
- Excellent long-term maintainability

---

## AI/ML Decisions

### ADR-006: Mistral OCR 3

**Date:** 2024-01-15
**Status:** Accepted

#### Context
We need OCR to extract text from insurance PDFs.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Mistral OCR 3** | State-of-the-art accuracy, handles tables | Newer service |
| **AWS Textract** | AWS ecosystem, good for forms | Expensive, complex output |
| **Google Document AI** | Good accuracy, table support | Complex pricing |
| **Tesseract** | Free, open source | Poor on complex layouts |
| **Vision LLM (GPT-4V)** | No OCR step needed | Expensive, slower |

#### Decision
Use **Mistral OCR 3**.

#### Rationale
1. **Table handling** — Insurance docs are table-heavy; Mistral preserves structure
2. **Cost** — $1-2 per 1,000 pages is reasonable
3. **Output format** — Markdown with HTML tables is clean
4. **Accuracy** — Benchmarks show strong performance on forms/tables

#### Consequences
- Dependency on Mistral API
- Need to parse HTML tables from markdown
- Excellent accuracy on insurance documents

---

### ADR-007: Gemini 2.5 Flash for Extraction

**Date:** 2024-01-15
**Status:** Accepted

#### Context
We need an LLM for structured data extraction from documents.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Gemini 2.5 Flash** | 1M context, cheap, fast | Newer model |
| **GPT-4 Turbo** | High accuracy, well-tested | More expensive, 128K context |
| **Claude 3 Sonnet** | Good at documents | 200K context limit |
| **Mistral Large** | Cheap | Smaller context |

#### Decision
Use **Gemini 2.5 Flash**.

#### Rationale
1. **Context window** — 1M tokens fits entire policies without chunking
2. **Cost** — $0.50/M input, $3/M output is very reasonable
3. **Speed** — Flash variant is optimized for throughput
4. **Structured output** — Good at following schemas

#### Consequences
- Dependency on Google AI
- Need to handle occasional inconsistencies
- Excellent cost-performance ratio

---

### ADR-008: OpenAI Embeddings

**Date:** 2024-01-15
**Status:** Accepted

#### Context
We need an embedding model for semantic search.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **text-embedding-3-small** | Good quality, reasonable cost | 1536 dims (medium) |
| **text-embedding-3-large** | Best quality | More expensive, 3072 dims |
| **Gemini embedding** | Free tier, same vendor | Lower quality than OpenAI |
| **Voyage AI** | Document-optimized | Another vendor |

#### Decision
Use **OpenAI text-embedding-3-small**.

#### Rationale
1. **Quality** — Strong performance on document retrieval
2. **Cost** — $0.02 per 1M tokens is cheap
3. **Dimensions** — 1536 balances quality and storage
4. **Pinecone support** — Well-tested together

#### Consequences
- OpenAI dependency (in addition to Google for LLM)
- Need to manage API keys for multiple services
- Reliable, production-ready

---

## Product Decisions

### ADR-009: Two-Pass Extraction

**Date:** 2024-01-15
**Status:** Accepted

#### Context
How should we extract structured data from documents?

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Single pass** | One LLM call with giant schema | Simple | Hallucinates, low accuracy |
| **Two pass** | Classify first, then extract | Higher accuracy | More complexity, more calls |
| **Template matching** | Carrier-specific templates | Very accurate | Doesn't scale, high maintenance |

#### Decision
Use **two-pass extraction**: classify document type first, then use type-specific schemas.

#### Rationale
1. **Accuracy** — Focused schemas prevent hallucination
2. **Maintainability** — Each schema can be tuned independently
3. **Debuggability** — Clear failure points
4. **Extensibility** — Easy to add new document types

#### Consequences
- Two LLM calls per document (minimal cost impact)
- Need to maintain multiple schemas
- Significantly better extraction quality

---

### ADR-010: Store OCR Output

**Date:** 2024-01-15
**Status:** Accepted

#### Context
Should we store the raw OCR output or just the extracted data?

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Store OCR output** | Can reprocess, debug, audit | Storage cost, complexity |
| **Discard after extraction** | Simpler, less storage | Can't reprocess without re-OCR |

#### Decision
**Store OCR output** (markdown) alongside documents.

#### Rationale
1. **Reprocessing** — Can re-extract when schemas improve without re-OCR
2. **Debugging** — Can see exactly what OCR produced
3. **Cost** — Text storage is cheap (~$0.02/GB)
4. **RAG chunking** — Need the text anyway for embeddings

#### Consequences
- Additional storage (~50KB per document average)
- Need to manage OCR output files
- Enables significant operational flexibility

---

### ADR-011: Separate Structured + Semantic Layers

**Date:** 2024-01-15
**Status:** Accepted

#### Context
How should we organize data for querying?

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Structured only** | Everything in PostgreSQL | Simple queries | Can't answer interpretive questions |
| **Semantic only** | Everything in vector DB | Natural language queries | Hard to do exact lookups |
| **Hybrid** | Structured for facts, semantic for interpretation | Best of both | More complexity |

#### Decision
Use **hybrid approach**: structured data in PostgreSQL, semantic chunks in Pinecone.

#### Rationale
1. **Right tool for job** — SQL for "what's my limit?", RAG for "am I covered?"
2. **Performance** — Structured queries are faster for known fields
3. **Flexibility** — Can answer any question type
4. **User experience** — Meets different user intents

#### Consequences
- Need to maintain two data stores
- Sync logic between PostgreSQL and Pinecone
- Best possible query capability

---

### ADR-012: MVP Feature Scope

**Date:** 2024-01-15
**Status:** Accepted

#### Context
What features should be in the MVP?

#### Options Considered

Features considered:
1. Document upload & extraction ✓
2. Property/policy dashboard ✓
3. RAG Q&A ✓
4. Coverage gap detection ✓
5. Document completeness tracker ✓
6. Lender compliance checking ✓
7. Insurance score ✗ (deferred)
8. Policy comparison ✗ (deferred)
9. Premium benchmarking ✗ (deferred)

#### Decision
Include **6 features** in MVP; defer Insurance Score, Policy Comparison, and Benchmarking.

#### Rationale
1. **Core value** — First 6 features deliver the core promise
2. **Complexity** — Insurance Score needs data calibration
3. **Dependencies** — Benchmarking needs data from multiple customers
4. **Time** — 6 features is achievable for MVP

#### Consequences
- Focused MVP
- Clear post-MVP roadmap
- Room for iteration based on user feedback

---

### ADR-013: Confidence Scoring

**Date:** 2024-01-15
**Status:** Accepted

#### Context
How should we handle extraction uncertainty?

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **No confidence** | Trust all extractions | Simple | Silent failures |
| **Binary confidence** | Confident or not | Simple | Too coarse |
| **Continuous confidence** | 0-1 score per field | Nuanced | More complex |

#### Decision
Use **continuous confidence scores** (0-1) per extracted field.

#### Rationale
1. **Nuance** — Some extractions are more certain than others
2. **Human review** — Can queue low-confidence for review
3. **Quality metrics** — Can track extraction quality over time
4. **User trust** — Users can see confidence levels

#### Consequences
- LLM prompts must ask for confidence
- UI needs confidence indicators
- Better user trust in the system

---

### ADR-014: Provenance Tracking

**Date:** 2024-01-15
**Status:** Accepted

#### Context
Should we track where extracted data came from?

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **No provenance** | Simpler schema | Can't audit or cite |
| **Document-level provenance** | Know which doc | Can't find specific page |
| **Full provenance** | Document + page + text | More storage, complexity |

#### Decision
Track **full provenance**: source document, page number, and original text.

#### Rationale
1. **Auditability** — Can verify any extracted value
2. **Citations** — RAG answers can cite specific pages
3. **Debugging** — Can see why extraction was wrong
4. **Trust** — Users can verify information

#### Consequences
- Additional fields on most tables
- Need to track page numbers during extraction
- Significantly better user experience

---

## Infrastructure Decisions

### ADR-015: Presigned URLs for Upload

**Date:** 2024-01-15
**Status:** Accepted

#### Context
How should users upload documents?

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Direct to API** | Simple | Server memory pressure |
| **Presigned URL to S3** | Scalable, reliable | Two-step process |
| **Chunked upload** | Handles huge files | Complex |

#### Decision
Use **presigned URLs** for direct upload to S3.

#### Rationale
1. **Scalability** — Large files don't hit API server
2. **Reliability** — S3 handles upload reliably
3. **Simplicity** — Well-understood pattern
4. **Cost** — Reduces API server resources

#### Consequences
- Two-step upload process (get URL, then upload)
- Need to handle upload completion notification
- Better performance at scale

---

### ADR-016: Database-Backed Queue (MVP)

**Date:** 2024-01-15
**Status:** Accepted

#### Context
How should we handle async processing jobs?

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **PostgreSQL table** | Simple, no new infra | Polling, less scalable |
| **Redis + Bull** | Fast, good features | Another service |
| **AWS SQS** | Managed, scales | AWS lock-in |
| **Celery** | Full-featured | Complex |

#### Decision
Use **PostgreSQL table as queue** for MVP.

#### Rationale
1. **Simplicity** — No new infrastructure
2. **Scale fit** — ~50-60 documents doesn't need Redis
3. **Transactional** — Jobs and data in same transaction
4. **Migration path** — Can move to Redis later

#### Consequences
- Polling for new jobs (acceptable for MVP)
- Less sophisticated than dedicated queue
- Easy to upgrade when needed

---

## Summary

| ID | Decision | Category |
|----|----------|----------|
| ADR-001 | Python backend | Architecture |
| ADR-002 | FastAPI framework | Architecture |
| ADR-003 | PostgreSQL database | Architecture |
| ADR-004 | Pinecone for vectors | Architecture |
| ADR-005 | SQLAlchemy ORM | Architecture |
| ADR-006 | Mistral OCR 3 | AI/ML |
| ADR-007 | Gemini 2.5 Flash | AI/ML |
| ADR-008 | OpenAI embeddings | AI/ML |
| ADR-009 | Two-pass extraction | Product |
| ADR-010 | Store OCR output | Product |
| ADR-011 | Hybrid data layers | Product |
| ADR-012 | MVP feature scope | Product |
| ADR-013 | Confidence scoring | Product |
| ADR-014 | Provenance tracking | Product |
| ADR-015 | Presigned URLs | Infrastructure |
| ADR-016 | Database-backed queue | Infrastructure |

---

## Updating This Log

When making new decisions:

1. Add a new ADR with next number
2. Use the standard template
3. Document ALL options considered
4. Explain rationale clearly
5. Note consequences

When revisiting decisions:

1. Don't delete old decisions
2. Add new decision that supersedes
3. Update status of old decision to "Superseded"
4. Reference the superseding decision