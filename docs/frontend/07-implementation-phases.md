# Implementation Phases

A structured 7-phase rollout plan to build the Open Insurance frontend with Steve Jobs-level attention to detail. Each phase builds on the previous, delivering usable value incrementally.

---

## Phase Overview

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| **Phase 1** | Foundation | Project setup, design system, layouts |
| **Phase 2** | Dashboard | Dashboard page, stats, timelines, alerts |
| **Phase 3** | Properties | Property list, detail, health score feature |
| **Phase 4** | Gaps | Gap detection UI, compliance checking |
| **Phase 5** | Documents & Chat | Upload wizard, AI chat interface |
| **Phase 6** | Renewals | Renewal intelligence, market data |
| **Phase 7** | Polish | Micro-interactions, performance, testing |

---

## Phase 1: Foundation

**Goal:** Establish the technical foundation and design system that everything else builds upon.

### 1.1 Project Setup

```bash
# Create Next.js 14 project
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir

# Install core dependencies
cd frontend
npm install @tanstack/react-query @tanstack/react-query-devtools
npm install framer-motion
npm install three @react-three/fiber @react-three/drei @react-three/postprocessing
npm install lucide-react
npm install class-variance-authority clsx tailwind-merge
npm install sonner  # Toast notifications
npm install recharts  # Charts

# Development dependencies
npm install -D @types/three
```

### 1.2 shadcn/ui Setup

```bash
npx shadcn-ui@latest init
# Choose: New York style, Slate color, CSS variables

# Install components
npx shadcn-ui@latest add button card badge dialog input select
npx shadcn-ui@latest add dropdown-menu popover tooltip skeleton
npx shadcn-ui@latest add tabs separator progress avatar
```

### 1.3 Files to Create

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Dashboard (placeholder)
│   ├── loading.tsx          # Global loading
│   ├── error.tsx            # Error boundary
│   └── globals.css          # Extended with design tokens
│
├── components/
│   ├── Providers.tsx        # Query + other providers
│   ├── primitives/
│   │   ├── Button.tsx       # Extended with gradients
│   │   ├── Card.tsx         # Glass variants
│   │   ├── Badge.tsx        # Status variants
│   │   └── index.ts
│   ├── patterns/
│   │   ├── GlassCard.tsx
│   │   ├── DataCard.tsx
│   │   ├── ScoreRing.tsx
│   │   ├── StatusBadge.tsx
│   │   └── index.ts
│   ├── layouts/
│   │   ├── AppShell/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── index.ts
│   │   └── PageContainer.tsx
│   └── three/
│       ├── shared/
│       │   └── Scene.tsx
│       ├── GradientMeshBg.tsx
│       └── index.ts
│
├── lib/
│   ├── utils.ts             # cn() helper
│   ├── api/
│   │   └── client.ts        # API client
│   └── motion/
│       └── variants.ts      # Animation variants
│
├── hooks/
│   ├── useMediaQuery.ts
│   └── index.ts
│
├── types/
│   └── api.ts               # API types
│
└── tailwind.config.ts       # Extended with design tokens
```

### 1.4 Deliverables

- [ ] Next.js 14 project initialized
- [ ] Tailwind configured with full design tokens
- [ ] shadcn/ui installed and themed
- [ ] AppShell layout with sidebar and header
- [ ] 3D gradient mesh background
- [ ] API client with error handling
- [ ] React Query provider
- [ ] All primitive components styled
- [ ] Pattern components created

### 1.5 Success Criteria

- `npm run dev` starts the app
- AppShell renders with navigation
- 3D background animates smoothly
- All buttons, cards, badges match design system

---

## Phase 2: Dashboard Experience

**Goal:** Create a compelling first impression that communicates portfolio health at a glance.

### 2.1 Components to Build

**Dashboard-specific:**
- `PortfolioStats` - Four stat cards with count-up
- `ExpirationTimeline` - Horizontal timeline with dots
- `AlertsPanel` - Filterable alert list
- `HealthScoreWidget` - Score ring + component bars
- `QuickActions` - Action button grid

**Three.js:**
- `HealthScoreGlobe` - 3D hero visualization
- `PropertyCity` - Optional 3D property overview

### 2.2 Files to Create

```
app/
└── page.tsx                  # Dashboard page

components/
├── features/
│   └── dashboard/
│       ├── PortfolioStats.tsx
│       ├── ExpirationTimeline.tsx
│       ├── AlertsPanel.tsx
│       ├── HealthScoreWidget.tsx
│       ├── QuickActions.tsx
│       └── index.ts
├── patterns/
│   ├── CountUp.tsx
│   ├── GradientProgress.tsx
│   ├── TrendIndicator.tsx
│   └── TimelineItem.tsx
└── three/
    └── HealthScoreGlobe/
        └── HealthScoreGlobe.tsx

hooks/
└── queries/
    └── useDashboard.ts       # Dashboard API hooks
```

### 2.3 API Integration

```typescript
// Endpoints used:
GET /v1/dashboard/summary
GET /v1/dashboard/expirations
GET /v1/dashboard/alerts
```

### 2.4 Deliverables

- [ ] Dashboard page with all sections
- [ ] Stat cards with animated count-up
- [ ] Expiration timeline visualization
- [ ] Alerts panel with severity filtering
- [ ] Health score widget (2D ring)
- [ ] 3D Health Score Globe
- [ ] All data fetching with React Query
- [ ] Loading skeletons
- [ ] Empty states

### 2.5 Success Criteria

- Dashboard loads in < 2 seconds
- All stats animate on scroll into view
- Alerts are filterable by severity
- Health score updates when clicking "recalculate"

---

## Phase 3: Property Intelligence

**Goal:** Enable deep dives into individual properties with the flagship Health Score feature.

### 3.1 Components to Build

**Properties List:**
- `PropertyGrid` - Responsive card grid
- `PropertyCard` - Card with key metrics
- `PropertyFilters` - Search + filter bar

**Property Detail:**
- `PropertyHeader` - Glass hero with stats
- `PropertyTabs` - Tab navigation
- `InsuranceSummary` - Policy cards
- `BuildingsList` - Expandable building cards

**Health Score (THE showpiece):**
- `HealthScoreHero` - Full 3D globe experience
- `ComponentBreakdown` - Animated progress bars
- `RecommendationList` - Prioritized actions
- `ScoreHistory` - Trend chart

### 3.2 Files to Create

```
app/
└── properties/
    ├── page.tsx              # Properties list
    ├── loading.tsx
    └── [id]/
        ├── page.tsx          # Property overview
        ├── layout.tsx        # Tab navigation
        ├── loading.tsx
        ├── health-score/
        │   └── page.tsx
        └── policies/
            └── page.tsx

components/
└── features/
    ├── properties/
    │   ├── PropertyGrid.tsx
    │   ├── PropertyCard.tsx
    │   ├── PropertyFilters.tsx
    │   ├── PropertyHeader.tsx
    │   ├── PropertyTabs.tsx
    │   ├── InsuranceSummary.tsx
    │   ├── BuildingsList.tsx
    │   └── index.ts
    ├── health-score/
    │   ├── HealthScoreHero.tsx
    │   ├── ComponentBreakdown.tsx
    │   ├── RecommendationList.tsx
    │   ├── ScoreHistory.tsx
    │   └── index.ts
    └── policies/
        ├── PolicyCard.tsx
        ├── CoverageTable.tsx
        └── index.ts

hooks/
└── queries/
    ├── useProperties.ts
    └── useHealthScore.ts
```

### 3.3 API Integration

```typescript
// Endpoints used:
GET /v1/properties
GET /v1/properties/{id}
GET /v1/properties/{id}/policies
GET /v1/health-score/properties/{id}
GET /v1/health-score/properties/{id}/history
POST /v1/health-score/properties/{id}/recalculate
```

### 3.4 Deliverables

- [ ] Properties list with search/filter
- [ ] Property detail with all sections
- [ ] Health Score page with 3D globe
- [ ] Component breakdown with animations
- [ ] Recommendation list with point values
- [ ] Score history chart
- [ ] Policy cards and coverage tables
- [ ] Buildings accordion

### 3.5 Success Criteria

- Properties list loads and filters quickly
- Health Score globe renders smoothly
- Score recalculation works and updates UI
- Navigation between tabs is seamless

---

## Phase 4: Gap Intelligence

**Goal:** Help users identify, understand, and resolve coverage gaps.

### 4.1 Components to Build

**Gaps Overview:**
- `GapsList` - Animated list with filters
- `GapCard` - Severity-styled card
- `GapFilters` - Filter controls
- `GapStats` - Summary counts

**Gap Detail:**
- `GapDetail` - Full gap information
- `GapAnalysis` - LLM-powered insights
- `AcknowledgeDialog` - Acknowledge modal
- `ResolveDialog` - Resolution modal

**Compliance:**
- `ComplianceStatus` - Pass/fail checklist
- `RequirementCheck` - Individual check row
- `LenderCard` - Lender information

**Three.js:**
- `CoverageShield` - 3D shield with holes

### 4.2 Files to Create

```
app/
├── gaps/
│   ├── page.tsx              # Portfolio gaps
│   └── [id]/
│       └── page.tsx          # Gap detail
└── properties/
    └── [id]/
        ├── gaps/
        │   └── page.tsx
        └── compliance/
            └── page.tsx

components/
└── features/
    ├── gaps/
    │   ├── GapsList.tsx
    │   ├── GapCard.tsx
    │   ├── GapDetail.tsx
    │   ├── GapAnalysis.tsx
    │   ├── GapFilters.tsx
    │   ├── AcknowledgeDialog.tsx
    │   ├── ResolveDialog.tsx
    │   └── index.ts
    └── compliance/
        ├── ComplianceStatus.tsx
        ├── RequirementCheck.tsx
        ├── LenderCard.tsx
        └── index.ts

hooks/
└── queries/
    ├── useGaps.ts
    └── useCompliance.ts
```

### 4.3 API Integration

```typescript
// Endpoints used:
GET /v1/gaps
GET /v1/gaps/{id}
POST /v1/gaps/{id}/analyze
POST /v1/gaps/{id}/acknowledge
POST /v1/gaps/{id}/resolve
POST /v1/gaps/detect
GET /v1/compliance/properties/{id}
```

### 4.4 Deliverables

- [ ] Portfolio-wide gaps list
- [ ] Property-specific gaps view
- [ ] Gap detail with LLM analysis
- [ ] Acknowledge and resolve workflows
- [ ] 3D Coverage Shield visualization
- [ ] Compliance status display
- [ ] Lender requirements comparison

### 4.5 Success Criteria

- Gaps filter by severity and status
- Gap analysis loads with skeleton
- Acknowledge/resolve updates optimistically
- Compliance checks show pass/fail clearly

---

## Phase 5: Documents & AI Chat

**Goal:** Enable document ingestion and conversational intelligence.

### 5.1 Components to Build

**Documents:**
- `DocumentGrid` - Document card grid
- `DocumentCard` - Status-aware card
- `UploadWizard` - Multi-step upload
- `ProcessingStatus` - Real-time status
- `DocumentViewer` - PDF viewer (optional)

**Chat:**
- `ChatInterface` - Main chat container
- `MessageBubble` - User/AI messages
- `StreamingText` - Typewriter effect
- `SourceCitation` - Reference display
- `SuggestedQuestions` - Quick prompts
- `PropertySelector` - Context filter

**Three.js:**
- `DocumentPipeline` - 3D processing viz

### 5.2 Files to Create

```
app/
├── documents/
│   ├── page.tsx              # Document list
│   ├── upload/
│   │   └── page.tsx          # Upload wizard
│   └── [id]/
│       └── page.tsx          # Document detail
├── chat/
│   └── page.tsx              # AI Chat
└── properties/
    └── [id]/
        └── documents/
            └── page.tsx

components/
└── features/
    ├── documents/
    │   ├── DocumentGrid.tsx
    │   ├── DocumentCard.tsx
    │   ├── UploadWizard.tsx
    │   ├── ProcessingStatus.tsx
    │   └── index.ts
    └── chat/
        ├── ChatInterface.tsx
        ├── MessageBubble.tsx
        ├── StreamingText.tsx
        ├── SourceCitation.tsx
        ├── SuggestedQuestions.tsx
        ├── PropertySelector.tsx
        └── index.ts

hooks/
├── queries/
│   └── useDocuments.ts
└── useChat.ts                # SSE streaming hook
```

### 5.3 API Integration

```typescript
// Endpoints used:
GET /v1/documents
POST /v1/documents/initiate-upload
PUT [presigned URL]
POST /v1/documents/{id}/complete-upload
GET /v1/documents/{id}
POST /v1/chat (SSE streaming)
```

### 5.4 Deliverables

- [ ] Document list with status indicators
- [ ] Drag-and-drop upload wizard
- [ ] Real-time processing status
- [ ] 3D document pipeline visualization
- [ ] Chat interface with streaming
- [ ] Source citations with links
- [ ] Suggested questions
- [ ] Property context filtering

### 5.5 Success Criteria

- File uploads show real-time progress
- Processing status updates automatically
- Chat responses stream smoothly
- Sources link to document pages

---

## Phase 6: Renewal Intelligence

**Goal:** Provide proactive renewal support with market insights.

### 6.1 Components to Build

**Renewals:**
- `RenewalTimeline` - 3D timeline path
- `ForecastChart` - Low/mid/high range
- `MarketContext` - Rate trends display
- `ReadinessScore` - Document checklist
- `NegotiationInsights` - Leverage points
- `BrokerPackage` - Download generator

**Three.js:**
- `RenewalPath` - 3D milestone journey

### 6.2 Files to Create

```
app/
├── renewals/
│   └── page.tsx              # Portfolio renewals
└── properties/
    └── [id]/
        └── renewals/
            └── page.tsx

components/
└── features/
    └── renewals/
        ├── RenewalTimeline.tsx
        ├── ForecastChart.tsx
        ├── MarketContext.tsx
        ├── ReadinessScore.tsx
        ├── NegotiationInsights.tsx
        ├── BrokerPackage.tsx
        └── index.ts

hooks/
└── queries/
    └── useRenewals.ts
```

### 6.3 API Integration

```typescript
// Endpoints used:
GET /v1/renewals/forecast/{property_id}
GET /v1/renewals/timeline/{property_id}
GET /v1/renewals/readiness/{property_id}
GET /v1/enrichment/market-intelligence/{property_id}
POST /v1/renewals/{property_id}/package
```

### 6.4 Deliverables

- [ ] Portfolio renewal overview
- [ ] 3D renewal timeline path
- [ ] Premium forecast with range chart
- [ ] Market intelligence panel
- [ ] Readiness score with checklist
- [ ] Negotiation insights
- [ ] Broker package generation/download

### 6.5 Success Criteria

- Timeline shows current milestone
- Forecast updates when data changes
- Market intelligence refreshes on demand
- Package downloads as ZIP

---

## Phase 7: Polish & Delight

**Goal:** Elevate from functional to exceptional with micro-interactions and performance.

### 7.1 Micro-Interactions

- Button press effects
- Card hover animations
- Page transition refinements
- Loading state enhancements
- Success celebration animations
- Error shake effects

### 7.2 Performance Optimization

- Lighthouse audit (target: 90+ all categories)
- Bundle analysis and code splitting
- Image optimization
- Three.js lazy loading and LOD
- React Query cache optimization
- Prefetching on hover

### 7.3 Additional Features

- Command palette (Cmd+K)
- Keyboard shortcuts
- Notification center
- Real-time updates (optional WebSocket)

### 7.4 Files to Create/Update

```
components/
├── shared/
│   ├── CommandPalette.tsx
│   ├── NotificationCenter.tsx
│   └── KeyboardShortcuts.tsx
├── patterns/
│   ├── ConfettiBurst.tsx
│   ├── SuccessCheckmark.tsx
│   └── ErrorShake.tsx
└── (update existing components with final polish)
```

### 7.5 Deliverables

- [ ] All micro-interactions implemented
- [ ] Command palette working
- [ ] Keyboard shortcuts documented
- [ ] Lighthouse score > 90
- [ ] Bundle size < 300KB initial
- [ ] All 3D scenes performant on mobile
- [ ] Reduced motion preferences honored

### 7.6 Success Criteria

- Users describe the app as "delightful"
- Performance metrics all green
- Accessibility audit passes
- Zero console errors/warnings

---

## Dependencies Between Phases

```
Phase 1 (Foundation)
    ↓
Phase 2 (Dashboard) ←───────────────────┐
    ↓                                   │
Phase 3 (Properties) ←──── Phase 4 (Gaps)
    ↓                                   │
Phase 5 (Documents & Chat) ─────────────┘
    ↓
Phase 6 (Renewals)
    ↓
Phase 7 (Polish)
```

- **Phases 4-6** can be parallelized after Phase 3
- **Phase 7** requires all others complete

---

## Definition of Done (Per Phase)

- [ ] All components render correctly
- [ ] All API integrations work
- [ ] Loading and error states handled
- [ ] Responsive on desktop/tablet/mobile
- [ ] Animations smooth (60fps)
- [ ] Accessibility basics met
- [ ] Code reviewed
- [ ] No TypeScript errors
- [ ] No console errors

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| 3D performance issues | Use mobile fallbacks, lazy loading |
| API latency | Optimistic updates, skeletons |
| Large bundle size | Code splitting, tree shaking |
| Complexity creep | Strict phase boundaries |
| Design inconsistency | Design system enforcement |

---

## Getting Started

1. Review all documentation files in `/docs/frontend/`
2. Start with Phase 1 setup
3. Build components incrementally
4. Test each component in isolation
5. Integrate into pages
6. Gather feedback and iterate

---

## Quick Reference: Key Files

| Purpose | Path |
|---------|------|
| Design tokens | `tailwind.config.ts` |
| Animation variants | `lib/motion/variants.ts` |
| API client | `lib/api/client.ts` |
| Query hooks | `hooks/queries/*.ts` |
| 3D components | `components/three/*.tsx` |
| Layout shell | `components/layouts/AppShell/` |

---

This plan provides a clear path from zero to a production-ready, Steve Jobs-level frontend experience. Execute each phase completely before moving to the next, and don't compromise on quality.
