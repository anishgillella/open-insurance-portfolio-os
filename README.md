# Open Insurance

**AI-powered insurance management platform for commercial real estate owners.**

Open Insurance gives property owners visibility and control over their insurance portfolio — replacing scattered policies, opaque pricing, and renewal chaos with a single source of truth.

---

## The Problem

Commercial real estate insurance is broken:

- **No visibility** — Policies buried in emails, ShareFiles, and Google Drives. Owners don't know what they're covered for or what they're paying.
- **Hidden fees** — 20-40% of premiums go to intermediaries (brokers, wholesalers, MGAs). None of this is transparent.
- **Renewal chaos** — Every year is a scramble. No data, no leverage, no time to shop around.
- **Coverage gaps** — Owners discover they're underinsured only when they file a claim.
- **No benchmarking** — Is $1,200/unit a good price? No one knows because there's no shared data.

> "If you don't know anything about insurance, you're better off — that's how bad it is."
> — Every commercial real estate owner

---

## The Solution

Open Insurance is the **operating system for CRE insurance**.

### Core Capabilities

| Capability | What It Does |
|------------|--------------|
| **Document Ingestion** | Upload policies, SOVs, dec pages — or forward emails. We handle the rest. |
| **AI Extraction** | LLMs parse unstructured insurance documents into structured, searchable data. |
| **Portfolio Dashboard** | See all properties, policies, coverages, and premiums in one place. |
| **Coverage Gap Detection** | Automatic identification of underinsurance, missing coverages, and expiring policies. |
| **Health Score** | 0-100 proprietary score with 6 weighted components and LLM-powered analysis. |
| **Climate Risk Intelligence** | Property-specific risk scoring for flood, wildfire, hurricane, and more. |
| **Renewal Intelligence** | Premium forecasting, market intelligence, and negotiation leverage. |
| **Policy Comparison** | Year-over-year program analysis with coverage diffs and LLM insights. |
| **AI Assistant** | Ask questions in plain English with citation-backed answers. |

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   1. UPLOAD              2. EXTRACT             3. ORGANIZE                 │
│   ────────               ─────────              ─────────                   │
│   Drop your files        AI reads and           See everything              │
│   or forward emails      structures data        in one dashboard            │
│                                                                             │
│   ┌─────────┐           ┌─────────┐            ┌─────────┐                  │
│   │   PDF   │ ────────▶ │   AI    │ ────────▶  │ Portfolio│                 │
│   │  Excel  │           │ Engine  │            │   View   │                 │
│   │  Email  │           │         │            │          │                 │
│   └─────────┘           └─────────┘            └─────────┘                  │
│                                                                             │
│   4. ANALYZE             5. ACT                                             │
│   ─────────              ────                                               │
│   Get insights and       Make better                                        │
│   recommendations        decisions                                          │
│                                                                             │
│   ┌─────────┐           ┌─────────┐                                         │
│   │ Health  │           │ Renew   │                                         │
│   │ Scores  │           │ Compare │                                         │
│   │ Gaps    │           │ Comply  │                                         │
│   └─────────┘           └─────────┘                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implemented Features

### 1. Document Intelligence

**Input:** PDFs, Excel files, scanned documents, images, forwarded emails
**Output:** Structured, searchable insurance data

#### Supported Document Types
| Document Type | Description | Data Extracted |
|---------------|-------------|----------------|
| **Declaration Pages** | Policy summary | Carrier, policy number, effective/expiration dates, premiums, coverages |
| **Statements of Value (SOV)** | Property schedules | Building values, locations, construction type, TIV |
| **Certificates of Insurance (COI)** | Compliance proof | Certificate holder, coverages, limits, additional insureds |
| **Loss Runs** | Claims history | Claim dates, types, amounts paid/reserved, status |
| **Invoices** | Premium billing | Premium breakdowns, taxes, fees, due dates |
| **Proposals/Quotes** | Renewal options | Quoted premiums, coverage options, carrier terms |
| **Endorsements** | Policy modifications | Coverage changes, effective dates, premium impact |
| **Program Documents** | Umbrella/excess liability | Layering structure, attachment points, limits |

#### Processing Pipeline
1. **Upload** — User uploads document (PDF, image, Excel) or forwards email
2. **File Type Detection** — Excel/CSV parsed directly via SheetJS, others go to OCR
3. **OCR Processing** — Mistral OCR extracts text with table structure preserved
4. **Document Classification** — LLM auto-detects document type
5. **Chunked Extraction** — Large documents split into ~50K character chunks for parallel processing
6. **Structured Extraction** — LLM (Claude/Gemini via OpenRouter) converts to structured JSON using Pydantic schemas
7. **Validation** — Math checks (premiums sum correctly), date logic, confidence scoring
8. **Storage & Indexing** — PostgreSQL + vector embeddings in Pinecone for RAG

---

### 2. Coverage Gap Detection

**Automatic identification of coverage issues based on industry-standard thresholds.**

#### Gap Types & Thresholds

| Gap Type | Severity | Condition | Standard |
|----------|----------|-----------|----------|
| **Underinsurance** | 🔴 Critical | Coverage < 80% of building replacement cost | Fannie Mae, NAIOP |
| **Underinsurance** | 🟡 Warning | Coverage 80-90% of building replacement cost | Industry best practice |
| **High Deductible** | 🔴 Critical | Deductible > 5% of TIV or > $500,000 flat | Commercial RE standards |
| **High Deductible** | 🟡 Warning | Deductible > 3% of TIV or > $250,000 flat | Lender requirements |
| **Policy Expiration** | 🔴 Critical | Policy expires in ≤ 30 days | Immediate action needed |
| **Policy Expiration** | 🟡 Warning | Policy expires in 31-60 days | Begin renewal process |
| **Policy Expiration** | 🔵 Info | Policy expires in 61-90 days | Plan ahead |
| **Missing Coverage** | 🔴 Critical | No property or general liability coverage | Required minimums |
| **Missing Umbrella** | 🟡 Warning | TIV > $5,000,000 without umbrella/excess | Recommended protection |
| **Missing Flood** | 🔴 Critical | Property in high-risk flood zone (A, AE, V, VE, etc.) without flood insurance | FEMA/Lender requirement |
| **Outdated Valuation** | 🔴 Critical | Last valuation > 3 years old | Risk of underinsurance |
| **Outdated Valuation** | 🟡 Warning | Last valuation > 2 years old | Update recommended |

#### Compliance Templates

**Standard Commercial Lender:**
- 100% replacement cost coverage
- $1M minimum GL limit
- 5% maximum deductible
- Flood required if in flood zone

**Fannie Mae Multifamily:**
- 100% replacement cost coverage
- $1M minimum GL limit
- Umbrella based on unit count:
  - 1-50 units: $1M
  - 51-100 units: $2M
  - 101-200 units: $5M
  - 200+ units: $10M
- 5% max deductible or $100K, whichever greater
- 12 months business income required

**Conservative:**
- 100% replacement cost
- $2M GL limit
- $5M umbrella always required
- 2% max deductible or $50K
- Flood, earthquake, terrorism required

---

### 3. Insurance Health Score

**Proprietary 0-100 score with 6 weighted components, powered by LLM analysis.**

#### Component Breakdown

| Component | Max Points | What It Measures |
|-----------|------------|------------------|
| **Coverage Adequacy** | 25 | Building coverage vs replacement cost, business income adequacy, liability limits |
| **Policy Currency** | 20 | All policies current, time to expiration, lapse risk |
| **Deductible Risk** | 15 | Deductibles relative to property value, out-of-pocket exposure |
| **Coverage Breadth** | 15 | Required coverages (property, GL) + recommended (umbrella, flood, earthquake) |
| **Lender Compliance** | 15 | Coverage meets lender requirements, mortgagee properly listed |
| **Documentation Quality** | 10 | Required documents present and current |

#### Grade Thresholds
| Grade | Score Range | Status |
|-------|-------------|--------|
| **A** | 90-100 | Excellent coverage |
| **B** | 80-89 | Good, minor improvements possible |
| **C** | 70-79 | Adequate, attention needed |
| **D** | 60-69 | Below standard, action required |
| **F** | 0-59 | Critical gaps, immediate attention |

#### Output Includes
- Per-component scores with detailed reasoning
- Executive summary for stakeholders
- Prioritized recommendations with expected impact
- Risk factors and strengths
- Trend direction vs previous calculation

---

### 4. Climate Risk Intelligence

**Property-specific risk assessment using Parallel AI web research + Gemini structuring.**

#### Risk Categories Assessed

| Risk Type | Data Points | Risk Levels |
|-----------|-------------|-------------|
| **Flood Risk** | FEMA zone (X, A, AE, V, VE), zone description | Low, Moderate, High, Very High |
| **Fire Protection** | ISO PPC rating (1-10), fire station distance, hydrant distance | Class 1 (best) to 10 (worst) |
| **Hurricane Risk** | Historical events, coastal exposure | Low to Very High |
| **Tornado Risk** | Regional corridor analysis | Low to Very High |
| **Hail Risk** | Historical frequency and severity | Low to Very High |
| **Wildfire Risk** | Vegetation, terrain, fire history | Low to Very High |
| **Earthquake Risk** | Fault proximity, soil type | Low to Very High |
| **Crime Risk** | Crime index (0-100), crime grade (A-F) | Low to Very High |
| **Environmental Risk** | Superfund sites, industrial proximity | Low to Very High |

#### Additional Data Enrichment
- Recent building permits
- Code violations
- Infrastructure issues
- Overall risk score (0-100)
- Insurance implications and recommendations
- Cited sources

---

### 5. Renewal Intelligence

**Premium forecasting with rule-based estimates + LLM-powered analysis.**

#### Forecasting Components

**Rule-Based Estimate:**
- Base market trend: +5% (assuming hardening market)
- Property age adjustment: +0.5% per year over 30 years (max 5%)
- Claims adjustment: +2% per open claim (max 10%)

**LLM Factor Analysis (weighted):**
| Factor | Weight | What It Considers |
|--------|--------|-------------------|
| Loss History | 30% | Claims in past 3 years, total paid/reserved |
| Market Trends | 25% | Regional rate movements, carrier behavior |
| Property Changes | 15% | Valuation updates, risk profile changes |
| Coverage Changes | 15% | Limit increases, coverage additions |
| Carrier Appetite | 15% | Carrier's appetite for property type/region |

#### Output Includes
- Current premium and expiration date
- Rule-based point estimate with % change
- LLM predictions: Low / Mid / High range
- Confidence score (0-100)
- Factor-by-factor breakdown with reasoning
- Market context analysis
- Specific negotiation leverage points
- Live market intelligence (from Parallel AI)

---

### 6. Market Intelligence

**Real-time market research using Parallel AI + Gemini structuring.**

#### Data Retrieved
| Category | Information |
|----------|-------------|
| **Rate Trends** | YoY rate change %, direction (increasing/decreasing/stable/volatile), confidence level |
| **Key Factors** | Market drivers affecting the property type/region |
| **Carrier Appetite** | Per-carrier appetite (expanding/stable/contracting/exiting) |
| **Forecasts** | 6-month and 12-month predictions |
| **Regulatory Changes** | Recent or upcoming regulatory impacts |
| **Market Developments** | Industry news and trends |
| **Benchmarks** | Premium per $100 TIV, rate per sqft |

---

### 7. Policy & Program Comparison

**Intelligent year-over-year analysis with LLM-generated insights.**

#### Comparison Types

**Policy-to-Policy:**
- Premium change ($ and %)
- Coverages added/removed/changed
- Limit and deductible changes per coverage
- Total limit change
- LLM executive summary and recommendations

**Program-to-Program (Year-over-Year):**
- Total premium change across all policies
- Total insured value change
- Policy-level comparisons
- Policies added or removed
- Coverage gap identification
- Strategic recommendations for upcoming renewal

#### Output Format
```
Program 2024 vs 2025:
├── Total Premium: $125,000 → $142,500 (+14%)
├── Total Insured Value: $15M → $16.2M (+8%)
├── Policies:
│   ├── Property: Premium +12%, Wind deductible increased 50%
│   ├── GL: Premium +8%, Limits unchanged
│   └── Umbrella: Added new $5M policy
└── LLM Analysis:
    ├── Executive Summary
    ├── Key Changes (with specific numbers)
    ├── Coverage Gaps Identified
    └── Recommendations
```

---

### 8. AI Assistant ("Insurance Buddy")

**RAG-powered Q&A with citation-backed answers.**

#### Capabilities
- Semantic search across all uploaded documents
- Vector search via Pinecone (1024 dimensions)
- Context-aware retrieval using conversation history
- Citation of specific document pages and snippets
- Uncertainty flagging when confidence is low

#### Example Questions
```
"What's my total insured value across all properties?"
"Which properties don't have flood coverage?"
"What changed between this year and last year's policy?"
"Am I covered if a pipe bursts and floods three units?"
"What are my deductibles for wind damage?"
"When does my umbrella policy expire?"
```

#### Retrieval Parameters
- Top-K chunks retrieved: 5 (configurable)
- Minimum similarity score threshold: 0.3
- Filters: property_id, document_type, policy_type, carrier
- Context window: ~4 chars/token estimation

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│      Next.js 14 · React 19 · TypeScript · Tailwind · shadcn/ui  │
│              Zustand (state) · React Query (data fetching)      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          BACKEND                                │
│              FastAPI · Python 3.11 · SQLAlchemy 2.0             │
│                  Pydantic v2 · Async/Await                      │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│   DOCUMENTS   │       │   DATABASE    │       │   AI/ML       │
│               │       │               │       │               │
│ • S3 Storage  │       │ • PostgreSQL  │       │ • Mistral OCR │
│ • Mistral OCR │       │ • SQLAlchemy  │       │ • OpenRouter  │
│ • SheetJS     │       │ • pgvector    │       │ • Pinecone    │
│               │       │ • Alembic     │       │ • Parallel AI │
└───────────────┘       └───────────────┘       └───────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14 (App Router) | Modern React with server components |
| **UI Components** | shadcn/ui + Tailwind CSS 4 | Consistent, accessible design |
| **State Management** | Zustand + React Query | Client state + server state |
| **Visualizations** | Nivo, Recharts, Three.js | Charts, graphs, 3D visualizations |
| **Backend** | FastAPI (Python 3.11) | Async API with automatic OpenAPI docs |
| **Database** | PostgreSQL + pgvector | Relational data + vector embeddings |
| **ORM** | SQLAlchemy 2.0 (async) | Type-safe database access |
| **Migrations** | Alembic | Database schema versioning |
| **Vector Search** | Pinecone | Semantic search for RAG |
| **OCR** | Mistral OCR | Universal document extraction |
| **LLM** | OpenRouter (Claude/Gemini) | Extraction, analysis, chat |
| **Web Research** | Parallel AI | Market intelligence, property risk |
| **Storage** | AWS S3 | Document storage |
| **Spreadsheets** | SheetJS | Native Excel/CSV parsing |

---

## Data Model

```
Organization (Owner/PM)
    │
    ├── Properties (31 models total)
    │       │
    │       ├── Core: address, type, units, sq_ft, year_built
    │       ├── Construction: construction_type, sprinklers, protection_class
    │       ├── Risk: flood_zone, risk factors (from Parallel AI)
    │       ├── Buildings: individual building records with values
    │       └── Valuations: building_value, contents_value, bi_value
    │
    ├── Insurance Programs (per policy year)
    │       │
    │       ├── Policies
    │       │       │
    │       │       ├── Policy details: number, carrier, dates, premium
    │       │       ├── Coverages: limits, deductibles, sublimits
    │       │       └── Endorsements: modifications
    │       │
    │       └── Aggregate: total_premium, total_insured_value
    │
    ├── Documents
    │       │
    │       ├── Original file (S3 storage)
    │       ├── Document type (classified)
    │       ├── Extracted data (JSON)
    │       ├── Document chunks (for RAG)
    │       └── Confidence scores
    │
    ├── Coverage Gaps
    │       │
    │       ├── Gap type, severity, description
    │       ├── Current vs recommended values
    │       ├── LLM enrichment (recommendations)
    │       └── Resolution status
    │
    ├── Health Scores
    │       │
    │       ├── Total score (0-100) and grade (A-F)
    │       ├── Component breakdown (6 components)
    │       ├── Executive summary
    │       └── Recommendations
    │
    ├── Renewal Forecasts
    │       │
    │       ├── Rule-based and LLM predictions
    │       ├── Factor breakdown
    │       ├── Market context
    │       └── Negotiation points
    │
    ├── Claims
    │       │
    │       ├── Claim details, dates, amounts
    │       └── Status tracking
    │
    └── Conversations
            │
            ├── Chat history for AI assistant
            └── Message threading
```

---

## API Endpoints

### Core Resources
```
Documents:
  POST   /v1/documents/upload           Upload insurance document
  GET    /v1/documents                  List documents
  GET    /v1/documents/{id}             Get document details
  DELETE /v1/documents/{id}             Delete document

Properties:
  GET    /v1/properties                 List properties
  POST   /v1/properties                 Create property
  GET    /v1/properties/{id}            Get property details
  GET    /v1/properties/{id}/overview   Property overview metrics
  GET    /v1/properties/{id}/health     Property health score
  DELETE /v1/properties/{id}            Delete with cascade
```

### Intelligence & Analysis
```
Gaps:
  GET    /v1/gaps                       List coverage gaps
  GET    /v1/gaps/by-property           Gaps grouped by property
  POST   /v1/gaps/{id}/resolve          Resolve a gap

Health Score:
  GET    /v1/health-score/properties    All property health scores
  POST   /v1/health-score/calculate     Calculate health score

Renewals:
  GET    /v1/renewals                   List renewal timeline
  GET    /v1/renewals/forecast          Forecast renewals
  POST   /v1/renewals/{id}/compare      Compare quotes

Enrichment:
  POST   /v1/enrichment/property-risk   Get property risk data
  POST   /v1/enrichment/market-intel    Get market intelligence
```

### Chat & Dashboard
```
Chat:
  POST   /v1/chat/query                 Ask AI assistant
  GET    /v1/chat/conversations         List conversations
  GET    /v1/chat/conversations/{id}    Get conversation history

Dashboard:
  GET    /v1/dashboard/summary          Dashboard summary stats
  GET    /v1/dashboard/expirations      Upcoming expirations
```

---

## Services Architecture

### Backend Services (33 modules)

**Document Processing:**
- `extraction_service.py` — LLM-based structured data extraction
- `ocr_service.py` — Mistral OCR integration
- `classification_service.py` — Document type classification
- `chunking_service.py` — Document chunking for large files
- `ingestion_service.py` — End-to-end document pipeline
- `merge_service.py` — Merging extracted data from chunks

**AI & Intelligence:**
- `gap_detection_service.py` — Automated gap detection (6 gap types)
- `gap_analysis_service.py` — Gap enrichment and recommendations
- `health_score_service.py` — 6-component health scoring
- `compliance_service.py` — Lender requirement checking
- `conflict_detection_service.py` — Coverage conflict detection

**Renewals & Forecasting:**
- `renewal_forecast_service.py` — Premium predictions
- `renewal_readiness_service.py` — Renewal preparation status
- `renewal_timeline_service.py` — Timeline management
- `policy_comparison_service.py` — Policy/program comparison

**Market & Risk:**
- `market_intelligence_service.py` — Live market research
- `market_context_service.py` — Market context enrichment
- `property_risk_service.py` — Climate/property risk scoring
- `carrier_research_service.py` — Carrier rate trends

**RAG & Embeddings:**
- `embedding_pipeline_service.py` — Vector embedding generation
- `rag_query_service.py` — RAG retrieval implementation
- `answer_generation_service.py` — LLM answer generation
- `pinecone_service.py` — Pinecone vector DB integration

---

## Getting Started (Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- Redis (optional, for caching)

### Running the Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000

# API docs at http://localhost:8000/docs
```

### Running the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend at http://localhost:3000
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/open_insurance

# AWS (Document Storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET=open-insurance-docs

# AI Services
MISTRAL_API_KEY=              # Mistral OCR
OPENROUTER_API_KEY=           # LLM (Claude/Gemini)
PINECONE_API_KEY=             # Vector search
PARALLEL_API_KEY=             # Market intelligence

# Optional
REDIS_URL=                    # Caching
```

---

## Cost Projections

### Processing Costs Per Property Per Year

| Component | Calculation | Cost |
|-----------|-------------|------|
| Mistral OCR | 100 pages × $0.001 | $0.10 |
| LLM extraction | 30 docs × ~$0.004 | $0.12 |
| LLM assistant | 50 queries × ~$0.001 | $0.05 |
| **Total AI/Processing** | | **$0.27** |

### Scaling Projections

| Scale | Properties | Monthly AI Cost | Monthly Infra | Total Monthly |
|-------|------------|-----------------|---------------|---------------|
| **MVP** | 50 | $1 | $50 | **$51** |
| **Seed** | 500 | $10 | $100 | **$110** |
| **Series A** | 5,000 | $100 | $300 | **$400** |
| **Growth** | 25,000 | $500 | $1,000 | **$1,500** |

**At scale, platform cost is ~$0.02/unit/year** — negligible compared to insurance premiums.

---

## Roadmap

### Phase 1: Owner Portal ✅ (Current)
- [x] Document upload and AI extraction
- [x] Portfolio dashboard
- [x] Coverage gap detection (6 gap types)
- [x] Health score (6 components)
- [x] Climate risk intelligence
- [x] Renewal forecasting
- [x] Policy/program comparison
- [x] AI Q&A assistant (RAG)
- [x] Market intelligence

### Phase 2: Advanced Intelligence (Planned)
- [ ] Fraud/anomaly detection
- [ ] Agentic AI claims assistant
- [ ] IoT integration layer
- [ ] Real-time underwriting copilot
- [ ] Portfolio-wide benchmarking

### Phase 3: Marketplace (Future)
- [ ] Carrier-facing portal
- [ ] Quote comparison and binding
- [ ] API for third-party access
- [ ] Industry-wide data standards

---

## License

Proprietary. All rights reserved.

---

## Contact

**Open Insurance, Inc.**

- Website: [openinsurance.com](https://openinsurance.com)
- Email: hello@openinsurance.com
