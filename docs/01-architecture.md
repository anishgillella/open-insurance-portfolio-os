# System Architecture

## Overview

This document describes the technical architecture of Open Insurance — how the pieces connect, what technologies we use, and why we made these choices.

---

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Client
        A[Next.js Frontend]
    end

    subgraph API Layer
        B[FastAPI Backend]
    end

    subgraph Processing
        C[Document Processor]
        D[Extraction Engine]
        E[RAG Engine]
    end

    subgraph Storage
        F[(PostgreSQL)]
        G[(Pinecone)]
        H[(AWS S3)]
    end

    subgraph External Services
        I[Mistral OCR]
        J[Gemini 2.5 Flash]
        K[OpenAI Embeddings]
    end

    A <-->|REST API| B
    B --> C
    B --> E
    C --> D
    C --> H
    D --> I
    D --> J
    D --> F
    D --> G
    E --> G
    E --> J
    E --> F
    D --> K
```

---

## Architecture Principles

Before diving into components, these principles guide our design decisions:

### 1. Separation of Concerns

Each component has a single responsibility:
- **API Layer** — Handles HTTP, auth, routing
- **Processing** — Handles document transformation
- **Storage** — Handles persistence

This allows independent scaling and testing.

### 2. Source Document as Truth

We never discard the original. Every extracted fact traces back to:
- Source document
- Page number
- Confidence score

This enables auditing, debugging, and reprocessing.

### 3. Progressive Enrichment

Data quality improves over time:
- Initial extraction may be 85% accurate
- Human corrections improve it
- Multiple documents corroborate facts
- Confidence scores reflect certainty

### 4. Fail Gracefully

When extraction fails or confidence is low:
- Store what we can
- Flag for human review
- Don't block the pipeline

### 5. Cost-Aware Design

AI services are priced per token/page. We optimize for:
- Batch processing where possible
- Caching repeated operations
- Right-sizing models for tasks

---

## Component Deep Dive

### Frontend (Next.js)

**Purpose:** User interface for property owners to manage their insurance portfolio.

**Responsibilities:**
- Document upload interface
- Property/policy dashboard
- Chat interface for RAG Q&A
- Gap detection alerts
- Compliance status views

**Tech Stack:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- React Query for data fetching

**Communication:**
- REST API calls to FastAPI backend
- File uploads direct to S3 (presigned URLs)

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant S3

    User->>Frontend: Select file to upload
    Frontend->>Backend: Request presigned URL
    Backend->>S3: Generate presigned URL
    S3-->>Backend: Return URL
    Backend-->>Frontend: Return URL
    Frontend->>S3: Upload file directly
    S3-->>Frontend: Upload complete
    Frontend->>Backend: Notify file uploaded
    Backend->>Backend: Queue for processing
```

---

### Backend (FastAPI)

**Purpose:** API layer and business logic orchestration.

**Responsibilities:**
- REST API endpoints
- Authentication/authorization
- Request validation
- Job orchestration
- Business logic

**Tech Stack:**
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- Pydantic v2
- Asyncpg (PostgreSQL driver)

**Key Design Patterns:**

**Repository Pattern:**
Database operations abstracted behind repository classes.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Router    │ --> │   Service    │ --> │ Repository  │ --> DB
│  (FastAPI)  │     │  (Logic)     │     │ (SQLAlchemy)│
└─────────────┘     └──────────────┘     └─────────────┘
```

**Dependency Injection:**
Services and repositories injected via FastAPI's DI system.

**Async Everywhere:**
All I/O operations are async for better throughput.

---

### Document Processor

**Purpose:** Handle document uploads and orchestrate processing pipeline.

**Responsibilities:**
- Receive upload notifications
- Detect file type
- Route to appropriate processor
- Track processing status
- Handle failures and retries

**Processing Flow:**

```mermaid
flowchart TD
    A[Document Uploaded] --> B{File Type?}
    B -->|PDF| C[Queue for OCR]
    B -->|Excel/CSV| D[Parse Directly]
    B -->|Image| E[Queue for OCR]

    C --> F[Mistral OCR]
    D --> G[Structured Data]
    E --> F

    F --> H[OCR Output]
    H --> I[Classification]
    I --> J{Document Type}

    J -->|Policy| K[Policy Extraction]
    J -->|COI| L[COI Extraction]
    J -->|Invoice| M[Invoice Extraction]
    J -->|Other| N[Generic Extraction]

    K --> O[Validate & Store]
    L --> O
    M --> O
    N --> O
    G --> O

    O --> P[Generate Embeddings]
    P --> Q[Store in Pinecone]
```

---

### Extraction Engine

**Purpose:** Convert unstructured document content into structured data.

**Responsibilities:**
- Call Mistral OCR for text extraction
- Classify document type
- Call Gemini for structured extraction
- Validate extracted data
- Calculate confidence scores
- Store results with provenance

**Two-Layer Extraction:**

We extract data into two forms:

| Layer | Storage | Purpose |
|-------|---------|---------|
| **Structured** | PostgreSQL | Queryable facts (limits, dates, premiums) |
| **Semantic** | Pinecone | Natural language search (policy clauses, exclusions) |

**Extraction Strategy:**

```mermaid
flowchart LR
    A[OCR Output] --> B[Document Classifier]
    B --> C{Type}

    C -->|Policy| D[Policy Schema]
    C -->|COI| E[COI Schema]
    C -->|Invoice| F[Invoice Schema]

    D --> G[Gemini Extraction]
    E --> G
    F --> G

    G --> H[Pydantic Validation]
    H --> I{Valid?}

    I -->|Yes| J[Store in DB]
    I -->|No| K[Flag for Review]

    J --> L[Generate Chunks]
    K --> L
    L --> M[Embed Chunks]
    M --> N[Store in Pinecone]
```

**Why Separate Schemas per Document Type?**

| Approach | Pros | Cons |
|----------|------|------|
| One giant schema | Simple to maintain | LLM hallucinates missing fields |
| Schema per type | Accurate, focused extraction | More schemas to maintain |

We chose schema per type because accuracy matters more than convenience.

---

### RAG Engine

**Purpose:** Answer natural language questions about insurance coverage.

**Responsibilities:**
- Parse user questions
- Retrieve relevant document chunks from Pinecone
- Construct prompts with context
- Generate answers via Gemini
- Cite sources

**RAG Flow:**

```mermaid
sequenceDiagram
    participant User
    participant API
    participant RAG Engine
    participant Pinecone
    participant Gemini
    participant PostgreSQL

    User->>API: "Is flood covered at Buffalo Run?"
    API->>RAG Engine: Process query

    RAG Engine->>PostgreSQL: Get property context
    PostgreSQL-->>RAG Engine: Property details, policy IDs

    RAG Engine->>RAG Engine: Generate query embedding
    RAG Engine->>Pinecone: Vector search (filtered by property)
    Pinecone-->>RAG Engine: Top 5 relevant chunks

    RAG Engine->>Gemini: Query + chunks + context
    Gemini-->>RAG Engine: Answer with citations

    RAG Engine->>API: Formatted response
    API->>User: "Based on your property policy (p.23), flood is excluded. However..."
```

**Retrieval Strategy:**

1. **Filter first** — Only search chunks belonging to the relevant property
2. **Semantic search** — Find chunks most similar to the question
3. **Re-rank** — Optionally re-rank by relevance (future enhancement)
4. **Deduplicate** — Remove redundant chunks from same source

**Prompt Construction:**

```
You are an insurance expert assistant. Answer the user's question based
ONLY on the provided document excerpts.

If the answer is not in the documents, say "I don't have enough information
to answer this question."

Always cite your sources using [Document Name, Page X] format.

Property Context:
{property_details}

Relevant Policy Excerpts:
{chunks}

User Question:
{question}

Answer:
```

---

## Data Stores

### PostgreSQL

**Purpose:** Primary database for structured data.

**What's stored:**
- Properties and their attributes
- Policies, coverages, limits
- Certificates, invoices
- Document metadata
- Extraction results
- User data (future)

**Why PostgreSQL:**
- Battle-tested, reliable
- Strong typing
- JSON support for flexible data
- Excellent tooling (migrations, ORMs)
- Can add pgvector if we want hybrid search later

**Connection:**
- Async via asyncpg
- Connection pooling
- SQLAlchemy 2.0 ORM

---

### Pinecone

**Purpose:** Vector database for semantic search.

**What's stored:**
- Document chunks with embeddings
- Metadata for filtering (property_id, policy_type, document_type)

**Why Pinecone:**
- Managed service (no infra to maintain)
- Fast vector search at scale
- Metadata filtering
- Simple API

**Index Configuration:**
- Dimensions: 1536 (OpenAI text-embedding-3-small)
- Metric: Cosine similarity
- Pods: Starter tier for MVP, scale as needed

**Chunk Metadata Schema:**

```json
{
  "property_id": "uuid",
  "document_id": "uuid",
  "document_type": "policy | coi | endorsement",
  "policy_type": "property | gl | umbrella",
  "chunk_type": "coverage | exclusion | condition | definition | general",
  "page_number": 12,
  "carrier": "Seneca Insurance",
  "effective_date": "2024-01-01"
}
```

This allows filtered searches like:
- "Search only in property policies for Buffalo Run"
- "Search only in exclusion sections"

---

### AWS S3

**Purpose:** Document storage.

**What's stored:**
- Original uploaded files (PDF, XLSX, images)
- OCR output files (for debugging/reprocessing)

**Why S3:**
- Cheap, durable storage
- Direct upload via presigned URLs
- Standard choice

**Bucket Structure:**

```
open-insurance-docs/
├── uploads/
│   └── {property_id}/
│       └── {document_id}/
│           ├── original.pdf
│           └── ocr_output.md
├── exports/
│   └── {export_id}/
│       └── report.pdf
```

---

## External Services

### Mistral OCR 3

**Purpose:** Extract text and tables from PDFs.

**Why Mistral OCR:**
- State-of-the-art accuracy on complex documents
- Handles tables with merged cells
- Works on scans and native PDFs
- Outputs markdown with HTML tables
- Cost: $1-2 per 1,000 pages

**Integration:**
- API call with PDF bytes
- Returns markdown text
- We parse tables from HTML in the markdown

---

### Gemini 2.5 Flash

**Purpose:** Structured data extraction and RAG responses.

**Why Gemini 2.5 Flash:**
- 1M token context window (entire policies fit)
- Fast and cost-effective
- Good at following schemas
- Cost: $0.50/M input, $3/M output tokens

**Usage:**
- Document classification
- Schema-based extraction
- RAG answer generation

---

### OpenAI Embeddings

**Purpose:** Generate vector embeddings for semantic search.

**Model:** text-embedding-3-small

**Why OpenAI:**
- High quality embeddings
- 1536 dimensions (good balance of quality/cost)
- Cost: $0.02 per 1M tokens
- Well-supported in Pinecone

---

## Request Flows

### Document Upload Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant S3
    participant Queue
    participant Worker
    participant Mistral
    participant Gemini
    participant DB
    participant Pinecone

    User->>Frontend: Upload policy.pdf
    Frontend->>API: POST /documents/presign
    API->>S3: Create presigned URL
    S3-->>API: Presigned URL
    API-->>Frontend: {upload_url, document_id}

    Frontend->>S3: PUT file
    Frontend->>API: POST /documents/{id}/uploaded
    API->>DB: Create document record (status: pending)
    API->>Queue: Enqueue processing job
    API-->>Frontend: {status: processing}

    Queue->>Worker: Process document
    Worker->>S3: Download file
    Worker->>Mistral: OCR request
    Mistral-->>Worker: Markdown output
    Worker->>DB: Update (ocr_status: complete)

    Worker->>Gemini: Classify document
    Gemini-->>Worker: Document type
    Worker->>Gemini: Extract with schema
    Gemini-->>Worker: Structured data

    Worker->>DB: Store policies, coverages
    Worker->>Worker: Chunk document
    Worker->>Pinecone: Store embeddings
    Worker->>DB: Update (status: complete)

    Note over Frontend: Polls for status or WebSocket update
    Frontend-->>User: Document processed!
```

### RAG Query Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant RAG
    participant DB
    participant Pinecone
    participant Gemini

    User->>Frontend: "Is flood covered at Buffalo Run?"
    Frontend->>API: POST /chat
    API->>RAG: Process query

    RAG->>DB: Get property by name
    DB-->>RAG: Property ID, basic info

    RAG->>RAG: Embed query
    RAG->>Pinecone: Search (filter: property_id)
    Pinecone-->>RAG: Top 5 chunks

    RAG->>Gemini: Generate answer
    Gemini-->>RAG: Response with citations

    RAG->>API: Formatted answer
    API->>Frontend: Response
    Frontend->>User: Display answer
```

---

## Scalability Considerations

### Current Scale (MVP)

- ~50-60 documents
- 7 properties
- Single user
- No real-time requirements

At this scale, we can run everything on minimal infrastructure:
- Single API server
- Starter Pinecone pod
- Small PostgreSQL instance
- Sync processing (no queue needed for MVP)

### Future Scale

When scaling to thousands of properties:

| Component | Scaling Strategy |
|-----------|------------------|
| API | Horizontal scaling behind load balancer |
| Document Processing | Queue-based (Redis/SQS) with worker pool |
| PostgreSQL | Vertical scaling → Read replicas → Sharding |
| Pinecone | Higher pod tier, more replicas |
| S3 | Infinite scale built-in |

---

## Security Considerations

### Authentication & Authorization

**MVP:**
- Simple API key or JWT-based auth
- Single tenant (one organization)

**Future:**
- Multi-tenant with organization isolation
- Role-based access control
- Audit logging

### Data Security

- All data encrypted at rest (S3, PostgreSQL)
- TLS for all API communication
- Presigned URLs expire quickly
- No PII in logs

### AI Security

- No sensitive data in prompts beyond what's needed
- Rate limiting on AI endpoints
- Cost caps on external API usage

---

## Development Environment

### Local Setup

```
┌─────────────────────────────────────────────────────────────┐
│  Local Machine                                              │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   FastAPI   │  │  PostgreSQL │  │   Next.js   │         │
│  │   :8000     │  │   :5432     │  │   :3000     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
          │                                    │
          ▼                                    ▼
┌─────────────────────┐            ┌─────────────────────────┐
│  External Services  │            │      Cloud Storage      │
│  • Mistral OCR      │            │      • S3 (or local)    │
│  • Gemini           │            │      • Pinecone         │
│  • OpenAI           │            │                         │
└─────────────────────┘            └─────────────────────────┘
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/open_insurance

# Storage
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_S3_BUCKET=open-insurance-docs

# Vector DB
PINECONE_API_KEY=xxx
PINECONE_INDEX_NAME=insurance-docs

# AI Services
MISTRAL_API_KEY=xxx
GEMINI_API_KEY=xxx
OPENAI_API_KEY=xxx

# App
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

---

## Deployment Architecture (Future)

For production deployment:

```mermaid
flowchart TB
    subgraph Internet
        A[Users]
    end

    subgraph CDN
        B[Vercel / Cloudflare]
    end

    subgraph Compute
        C[API Server 1]
        D[API Server 2]
        E[Worker 1]
        F[Worker 2]
    end

    subgraph Data
        G[(PostgreSQL)]
        H[(Redis)]
    end

    subgraph External
        I[S3]
        J[Pinecone]
        K[AI APIs]
    end

    A --> B
    B --> C
    B --> D
    C --> G
    D --> G
    C --> H
    D --> H
    H --> E
    H --> F
    E --> I
    F --> I
    E --> J
    F --> J
    E --> K
    F --> K
```

---

## Key Decisions

| Decision | Choice | Rationale | See Also |
|----------|--------|-----------|----------|
| Backend language | Python | Strong AI/ML ecosystem, team familiarity | [Decision Log](./09-decision-log.md#python-backend) |
| API framework | FastAPI | Async, fast, Pydantic-native | [Decision Log](./09-decision-log.md#fastapi) |
| Vector DB | Pinecone | Managed, simple, scales | [Decision Log](./09-decision-log.md#pinecone) |
| Primary LLM | Gemini 2.5 Flash | 1M context, cost-effective | [Decision Log](./09-decision-log.md#gemini) |
| OCR | Mistral OCR 3 | Best accuracy on tables | [Decision Log](./09-decision-log.md#mistral-ocr) |
| Embeddings | OpenAI text-embedding-3-small | Quality, cost balance | [Decision Log](./09-decision-log.md#embeddings) |

---

## Next Steps

Proceed to [02-database-schema.md](./02-database-schema.md) to understand the data model in detail.