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
| **Coverage Analysis** | Identify gaps, redundancies, and underinsurance before it's a problem. |
| **Premium Benchmarking** | Compare your costs to similar properties. Know if you're overpaying. |
| **Renewal Intelligence** | Timelines, market conditions, and negotiation leverage — months ahead. |
| **AI Assistant** | Ask questions in plain English: "Am I covered for flood at 123 Main St?" |

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
│   │ Alerts  │           │ Renew   │                                         │
│   │ Gaps    │           │ Optimize│                                         │
│   │ Savings │           │ Comply  │                                         │
│   └─────────┘           └─────────┘                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Document Intelligence

**Input:** PDFs, Excel files, scanned documents, forwarded emails
**Output:** Structured, searchable insurance data

- Declaration pages → Policy details, coverages, premiums
- Statements of Value (SOV) → Property schedules with values
- Certificates of Insurance → Compliance tracking
- Loss runs → Claims history analysis

The AI handles carrier-specific formats, handwritten notes, and messy scans.

### 2. Portfolio Dashboard

One view of your entire insurance portfolio:

- **Property Map** — See all locations with coverage status
- **Policy Timeline** — Expirations, renewals, key dates
- **Coverage Matrix** — What's covered, what's not, across all properties
- **Premium Breakdown** — Where every dollar goes

### 3. Coverage Gap Detection

Automatic identification of:

- **Underinsurance** — Building values below replacement cost
- **Coinsurance penalties** — Will you get penalized at claim time?
- **Missing coverages** — Flood in flood zones, ordinance/law, equipment breakdown
- **Deductible exposure** — Can you absorb a $500K wind deductible?

### 4. Premium Benchmarking

Compare your insurance costs to the market:

- **$/unit** — How does your cost per apartment compare?
- **$/sqft** — Normalized comparison across property sizes
- **% of NOI** — Insurance as a percentage of net operating income
- **YoY trend** — Are your increases above or below market?

Data is anonymized and aggregated across the platform. Every policy uploaded makes the benchmarks smarter.

### 5. Renewal Command Center

Stop scrambling 30 days before expiration:

- **120-day timeline** — Automated reminders and milestones
- **Market intelligence** — What's happening to rates in your segment?
- **Document prep** — SOVs, loss runs, and submissions ready to go
- **Negotiation leverage** — Benchmarks and competing quotes in hand

### 6. AI Assistant ("Insurance Buddy")

Ask questions in plain English:

```
"What's my total insured value across all properties?"
"Which properties don't have flood coverage?"
"What changed between this year and last year's policy?"
"Am I covered if a pipe bursts and floods three units?"
"How much am I paying in broker fees?"
```

The AI cites specific policy language and flags when it's uncertain.

---

## Who It's For

### Property Owners (Primary User)

- Own 5-500+ multifamily units
- Spend $50K-$5M+ annually on insurance
- Tired of not understanding what they're paying for
- Want control over their renewals

### Property Managers

- Manage insurance across multiple owner portfolios
- Need compliance tracking and COI management
- Want centralized document storage

### Lenders (Future)

- Require proof of coverage for loan compliance
- Need to verify insurance meets loan covenants
- Want automated monitoring of borrower coverage

---

## Data Model

```
Organization (Owner/PM)
    │
    ├── Properties
    │       │
    │       ├── Address, Type, Units, Sq Ft, Year Built
    │       ├── Construction, Sprinklers, Protection Class
    │       ├── Flood Zone, Risk Factors
    │       └── Building Value, Contents Value, BI Value
    │
    ├── Policies
    │       │
    │       ├── Policy Number, Carrier, Effective/Expiration
    │       ├── Coverages (limits, deductibles, premiums)
    │       ├── Fees (taxes, broker commission, surcharges)
    │       └── Linked Properties (from SOV)
    │
    ├── Documents
    │       │
    │       ├── Original file (S3)
    │       ├── Document type (dec page, SOV, COI, etc.)
    │       ├── Extracted data (JSON)
    │       └── Confidence scores
    │
    └── Alerts
            │
            ├── Coverage gaps
            ├── Renewal reminders
            ├── Premium anomalies
            └── Compliance issues
```

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│         Next.js 14 · TypeScript · Tailwind · shadcn/ui          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API LAYER                              │
│              tRPC or REST · Auth (Clerk) · File Upload          │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│   DOCUMENTS   │       │   DATABASE    │       │   AI/ML       │
│               │       │               │       │               │
│ • S3 Storage  │       │ • PostgreSQL  │       │ • Mistral OCR │
│ • Mistral OCR │       │ • Drizzle ORM │       │ • Claude API  │
│ • SheetJS     │       │ • Redis       │       │ • pgvector    │
│ • Queue       │       │               │       │ • RAG         │
└───────────────┘       └───────────────┘       └───────────────┘
```

### Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Frontend | Next.js 14 (App Router) | Modern React, great DX, Vercel deploy |
| Styling | Tailwind + shadcn/ui | Fast iteration, consistent design |
| API | tRPC | End-to-end type safety |
| Database | PostgreSQL + pgvector | Relational data + vector embeddings |
| ORM | Drizzle | Type-safe, lightweight |
| Auth | Clerk | Fast setup, handles everything |
| Storage | AWS S3 | Reliable, cheap document storage |
| Queue | Inngest or Trigger.dev | Serverless background jobs |
| OCR | Mistral OCR | Universal document extraction |
| LLM | OpenRouter | $0.50/M input, $3/M output tokens |
| Spreadsheets | SheetJS | Native Excel/CSV parsing |
| Hosting | Vercel + Railway | Simple deployment |

---

## Document Processing Pipeline

We use a **unified extraction pipeline** powered by Mistral OCR that handles all document types — PDFs, scanned documents, images, complex tables, and handwritten content.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DOCUMENT PROCESSING PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐                                                              │
│   │  UPLOAD  │                                                              │
│   │  (Any    │                                                              │
│   │  Format) │                                                              │
│   └────┬─────┘                                                              │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────────────┐     Is Excel/CSV?     ┌─────────────────┐             │
│   │  FILE TYPE      │─────── YES ──────────▶│    SheetJS      │             │
│   │  DETECTION      │                       │  (Direct Parse) │             │
│   └────────┬────────┘                       └────────┬────────┘             │
│            │ NO                                      │                      │
│            ▼                                         │                      │
│   ┌─────────────────┐                                │                      │
│   │   MISTRAL OCR   │                                │                      │
│   │                 │                                │                      │
│   │  Handles:       │                                │                      │
│   │  • Native PDFs  │                                │                      │
│   │  • Scanned PDFs │                                │                      │
│   │  • Images       │                                │                      │
│   │  • Tables       │                                │                      │
│   │  • Handwriting  │                                │                      │
│   │                 │                                │                      │
│   │  Output:        │                                │                      │
│   │  Markdown +     │                                │                      │
│   │  HTML Tables    │                                │                      │
│   └────────┬────────┘                                │                      │
│            │                                         │                      │
│            └──────────────────┬───────────────────────                      │
│                               │                                             │
│                               ▼                                             │
│                      ┌─────────────────┐                                    │
│                      │   OPENROUTER    │                                    │
│                      │      LLM        │                                    │
│                      │  Structured     │                                    │
│                      │  Extraction     │                                    │
│                      │  (Zod Schema)   │                                    │
│                      └────────┬────────┘                                    │
│                               │                                             │
│                               ▼                                             │
│                      ┌─────────────────┐                                    │
│                      │    VALIDATE     │                                    │
│                      │                 │                                    │
│                      │  • Math checks  │                                    │
│                      │  • Date logic   │                                    │
│                      │  • Confidence   │                                    │
│                      │    scoring      │                                    │
│                      └────────┬────────┘                                    │
│                               │                                             │
│                               ▼                                             │
│                      ┌─────────────────┐                                    │
│                      │     STORE       │                                    │
│                      │                 │                                    │
│                      │  PostgreSQL +   │                                    │
│                      │  pgvector       │                                    │
│                      └─────────────────┘                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Mistral OCR?

| Capability | Mistral OCR |
|------------|-------------|
| Native PDFs | ✅ |
| Scanned PDFs | ✅ |
| Complex tables (merged cells, colspan/rowspan) | ✅ |
| Handwritten content | ✅ |
| Low-quality scans | ✅ |
| Forms and invoices | ✅ |
| Output format | Markdown + HTML tables |
| Pricing | $1-2 per 1,000 pages |

One tool handles everything except native spreadsheets (Excel/CSV), which we parse directly with SheetJS.

### Extraction Steps

1. **Upload** — User uploads document (PDF, image, Excel) or forwards email
2. **Detect** — Determine if it's a spreadsheet (direct parse) or document (OCR)
3. **OCR** — Mistral OCR extracts text with table structure preserved
4. **Structure** — LLM (via OpenRouter) converts markdown to structured JSON using Zod schemas
5. **Validate** — Cross-check extracted data (premiums add up, dates logical)
6. **Store** — Save structured data linked to original document

---

## Cost Projections & Scaling

### Documents Per Property

A typical multifamily property generates these insurance documents annually:

| Document Type | Frequency | Pages (Avg) | Purpose |
|---------------|-----------|-------------|---------|
| Declaration Page | 1/year | 5 | Policy summary |
| Full Policy | 1/year | 50 | Complete terms (optional upload) |
| Statement of Values (SOV) | 1-2/year | 2 | Property schedule |
| Certificate of Insurance (COI) | 5-20/year | 1 | Lender/tenant compliance |
| Loss Run | 1/year | 3 | Claims history |
| Endorsements | 2-5/year | 2 | Policy modifications |
| Renewal Quote Comparisons | 3-5/year | 5 | Shopping quotes |

**Estimated documents per property per year:** 15-35 documents
**Estimated pages per property per year:** 50-150 pages

### Processing Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| **Mistral OCR** | $1/1,000 pages (batch) | $2/1,000 real-time |
| **LLM (via OpenRouter)** | $0.50/M input, $3/M output | Claude Sonnet for extraction |
| **S3 Storage** | $0.023/GB/month | Document storage |
| **pgvector/PostgreSQL** | ~$20-50/month | Managed database |
| **Vercel/Hosting** | $20-50/month | Pro tier |

### Cost Per Property Per Year

Assuming 100 pages/property/year and average extraction complexity:

| Component | Calculation | Cost/Property/Year |
|-----------|-------------|-------------------|
| Mistral OCR | 100 pages × $0.001 | $0.10 |
| LLM extraction (~2K input, ~1K output per doc) | 30 docs × ~$0.004 | $0.12 |
| LLM assistant queries (~500 input, ~300 output) | 50 queries × ~$0.001 | $0.05 |
| **Total AI/Processing** | | **$0.27** |

### Scaling Projections

| Scale | Properties | Units (est.) | Pages/Month | Monthly AI Cost | Monthly Infra | Total Monthly |
|-------|------------|--------------|-------------|-----------------|---------------|---------------|
| **MVP** | 50 | 2,500 | 400 | $1 | $50 | **$51** |
| **Seed** | 500 | 25,000 | 4,000 | $10 | $100 | **$110** |
| **Series A** | 5,000 | 250,000 | 40,000 | $100 | $300 | **$400** |
| **Growth** | 25,000 | 1,250,000 | 200,000 | $500 | $1,000 | **$1,500** |
| **Scale** | 100,000 | 5,000,000 | 800,000 | $2,000 | $3,000 | **$5,000** |

### Detailed Cost Model by Scale

#### MVP (50 Properties / ~2,500 Units)
```
Monthly Documents: ~75 (1.5/property)
Monthly Pages: ~400

Mistral OCR:        $0.40   (400 pages × $0.001)
LLM Extraction:     $0.30   (75 docs × ~$0.004)
LLM Assistant:      $0.20   (~200 queries × ~$0.001)
S3 Storage:         $0.50   (~20MB new docs)
Database:           $25.00  (Railway/Neon starter)
Hosting:            $20.00  (Vercel Pro)
Auth (Clerk):       $0.00   (free tier)
────────────────────────────
Total:              ~$46/month
Per Property:       ~$0.92/month
```

#### Seed Stage (500 Properties / ~25,000 Units)
```
Monthly Documents: ~750
Monthly Pages: ~4,000

Mistral OCR:        $4.00
LLM Extraction:     $3.00   (750 docs × ~$0.004)
LLM Assistant:      $2.00   (~2,000 queries)
S3 Storage:         $2.00
Database:           $50.00  (managed PostgreSQL)
Hosting:            $50.00
Auth (Clerk):       $25.00
Redis Cache:        $20.00
────────────────────────────
Total:              ~$156/month
Per Property:       ~$0.31/month
```

#### Series A (5,000 Properties / ~250,000 Units)
```
Monthly Documents: ~7,500
Monthly Pages: ~40,000

Mistral OCR:        $40.00
LLM Extraction:     $30.00  (7,500 docs × ~$0.004)
LLM Assistant:      $20.00  (~20,000 queries)
S3 Storage:         $15.00
Database:           $200.00 (production PostgreSQL)
Hosting:            $200.00
Auth (Clerk):       $100.00
Redis/Queue:        $50.00
Monitoring:         $50.00
────────────────────────────
Total:              ~$705/month
Per Property:       ~$0.14/month
```

#### Growth (25,000 Properties / ~1.25M Units)
```
Monthly Documents: ~37,500
Monthly Pages: ~200,000

Mistral OCR:        $200.00  (batch pricing)
LLM Extraction:     $150.00  (37,500 docs × ~$0.004)
LLM Assistant:      $100.00  (~100,000 queries)
S3 Storage:         $50.00
Database:           $500.00
Hosting:            $500.00
Auth:               $300.00
Queue/Workers:      $200.00
Monitoring/Ops:     $200.00
────────────────────────────
Total:              ~$2,200/month
Per Property:       ~$0.09/month
```

### Cost Per Unit Economics

| Scale | Properties | Units | Monthly Cost | Cost/Unit/Month | Cost/Unit/Year |
|-------|------------|-------|--------------|-----------------|----------------|
| MVP | 50 | 2,500 | $46 | $0.018 | $0.22 |
| Seed | 500 | 25,000 | $156 | $0.006 | $0.07 |
| Series A | 5,000 | 250,000 | $705 | $0.003 | $0.03 |
| Growth | 25,000 | 1,250,000 | $2,200 | $0.002 | $0.02 |

**At scale, platform cost is ~$0.02/unit/year** — negligible compared to insurance premiums of $1,000-5,000/unit/year.

### Revenue vs Cost (Phase 2+)

Assuming Cost + 10% model with average premium of $1,500/unit/year:

| Scale | Units | Insurance Premium | Platform Fee (10%) | Platform Cost | Gross Margin |
|-------|-------|-------------------|-------------------|---------------|--------------|
| Seed | 25,000 | $37.5M | $3.75M | $1.9K/yr | **99.9%** |
| Series A | 250,000 | $375M | $37.5M | $8.5K/yr | **99.9%** |
| Growth | 1,250,000 | $1.875B | $187.5M | $26K/yr | **99.9%** |

The platform cost is essentially a rounding error compared to potential revenue. This is a **software-like margin business**.

### Burst Capacity Planning

Renewal season creates predictable spikes:

| Period | Normal Load | Renewal Season Peak |
|--------|-------------|---------------------|
| Documents/day | X | 5-10X |
| When | Year-round | Q4 + Q1 (most policies renew Jan 1) |

**Mitigation:**
- Use Mistral OCR batch API ($1/1000 vs $2/1000) for non-urgent processing
- Queue-based architecture handles spikes gracefully
- Pre-warm capacity for known renewal dates

---

## Roadmap

### Phase 1: Owner Portal ("Insurance Buddy")

**Goal:** Give owners visibility into their insurance portfolio.

- [ ] Document upload and storage
- [ ] AI extraction of dec pages and SOVs
- [ ] Portfolio dashboard with property/policy views
- [ ] Coverage gap detection
- [ ] Basic premium benchmarking
- [ ] AI Q&A assistant
- [ ] Renewal timeline and alerts

**Success metric:** Owners can answer "What am I paying and what am I covered for?" in under 60 seconds.

### Phase 2: Insurer Sandbox + MGA Layer

**Goal:** Enable carriers to underwrite directly on the platform.

- [ ] Carrier-facing portal
- [ ] Submission workflow
- [ ] Quote comparison
- [ ] Bind/issue integration
- [ ] Continuous underwriting signals
- [ ] MGA partnerships

**Success metric:** Renewals placed through platform with transparent pricing.

### Phase 3: Open Insurance Marketplace

**Goal:** Become the infrastructure layer for CRE insurance.

- [ ] API for third-party access
- [ ] Risk capital connections
- [ ] Industry-wide data standards
- [ ] Marketplace dynamics (bidding, competition)

**Success metric:** Platform is the default system of record for CRE insurance.

---

## Business Model

**Cost + 10%**

```
┌─────────────────────────────────────────┐
│                                         │
│   Insurer Risk Cost                     │
│   + 10% Platform Fee                    │
│   ─────────────────                     │
│   = Total Premium                       │
│                                         │
│   No hidden fees. No layers.            │
│   Transparent pricing.                  │
│                                         │
└─────────────────────────────────────────┘
```

This mirrors the Cost Plus Drugs model for healthcare — eliminate the middlemen markup and pass savings to the customer.

**Phase 1 (MVP):** Free for owners. Build the dataset.
**Phase 2+:** Platform fee on bound policies.

---

## Why Now?

1. **Premiums have exploded** — Multifamily insurance up 200-300% since 2021
2. **Owners are demanding change** — The industry is openly calling for transparency
3. **AI can finally read policies** — LLMs make document understanding viable
4. **Data network effects** — Every policy uploaded makes the platform smarter
5. **Incumbent inertia** — $300B+ market cap built on opacity won't self-disrupt

---

## Competitive Landscape

| Player | What They Do | Why We're Different |
|--------|--------------|---------------------|
| **Brokers** (Marsh, AON, etc.) | Traditional intermediaries | We're transparent; they profit from opacity |
| **Insurtech MGAs** | Tech-enabled underwriting | We're platform-first; they're carriers with apps |
| **Policy management tools** | Document storage | We extract intelligence; they just store files |
| **Vertical SaaS** (Yardi, RealPage) | Property management | Insurance is an afterthought; it's our core |

**Our moat:** Data. Every policy uploaded trains our models, improves benchmarks, and makes the platform more valuable. Network effects compound over time.

---

## Getting Started (Development)

```bash
# Clone the repository
git clone https://github.com/open-insurance/platform.git
cd platform

# Install dependencies
pnpm install

# Set up environment variables
cp .env.example .env.local
# Add your API keys (Clerk, AWS, Anthropic, Database)

# Run database migrations
pnpm db:migrate

# Start development server
pnpm dev
```

### Running Frontend & Backend

**Frontend (Next.js):**
```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:3000
```

**Backend (FastAPI):**
```bash
cd backend

# Create virtual environment (first time)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn app.main:app --reload --port 8000
# Backend runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Run Both (from project root):**
```bash
# Terminal 1 - Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev
```

### Environment Variables

```bash
# Auth
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=

# Database
DATABASE_URL=

# AWS (Document Storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
AWS_S3_BUCKET=

# AI - Document Processing
MISTRAL_API_KEY=              # Mistral OCR for document extraction
OPENROUTER_API_KEY=           # LLM for structured data extraction ($0.50/M in, $3/M out)

# Optional: Redis (caching/queues)
REDIS_URL=
```

---

## Project Structure

```
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/             # Auth pages (sign-in, sign-up)
│   │   ├── (dashboard)/        # Protected dashboard routes
│   │   │   ├── properties/     # Property management
│   │   │   ├── policies/       # Policy management
│   │   │   ├── documents/      # Document upload & viewer
│   │   │   ├── analytics/      # Benchmarking & insights
│   │   │   └── assistant/      # AI chat interface
│   │   └── api/                # API routes
│   │
│   ├── components/             # React components
│   │   ├── ui/                 # shadcn/ui primitives
│   │   ├── dashboard/          # Dashboard-specific components
│   │   ├── documents/          # Document upload & display
│   │   └── chat/               # AI assistant components
│   │
│   ├── lib/                    # Shared utilities
│   │   ├── db/                 # Database client & schema
│   │   ├── ai/                 # AI/LLM utilities
│   │   ├── extraction/         # Document extraction pipeline
│   │   └── storage/            # S3 file handling
│   │
│   ├── server/                 # Server-side code
│   │   ├── routers/            # tRPC routers
│   │   └── services/           # Business logic
│   │
│   └── types/                  # TypeScript types & schemas
│
├── drizzle/                    # Database migrations
├── public/                     # Static assets
└── tests/                      # Test files
```

---

## Contributing

This is an early-stage project. If you're interested in contributing:

1. Check the issues for open tasks
2. Read the technical architecture docs
3. Set up your local environment
4. Pick an issue and submit a PR

---

## License

Proprietary. All rights reserved.

---

## Contact

**Open Insurance, Inc.**

- Website: [openinsurance.com](https://openinsurance.com)
- Email: hello@openinsurance.com
- Founder: Zach Schofel (zach@openinsurance.com)
