# Frontend Pages Guide

A comprehensive reference for all web pages in Open Insurance, detailing data sources, conditional logic, and UI configurations.

---

## Table of Contents

1. [Dashboard (/)](#1-dashboard-)
2. [Properties (/properties)](#2-properties-properties)
3. [Property Detail (/properties/[id])](#3-property-detail-propertiesid)
4. [Property Health Score (/properties/[id]/health-score)](#4-property-health-score-propertiesidhealthscore)
5. [Property Renewals (/properties/[id]/renewals)](#5-property-renewals-propertiesidrenewals)
6. [Property Extracted Data (/properties/[id]/extracted-data)](#6-property-extracted-data-propertiesidextracteddata)
7. [Coverage Gaps (/gaps)](#7-coverage-gaps-gaps)
8. [Compliance (/compliance)](#8-compliance-compliance)
9. [Documents (/documents)](#9-documents-documents)
10. [Chat (/chat)](#10-chat-chat)
11. [Renewals Portfolio (/renewals)](#11-renewals-portfolio-renewals)

---

## 1. Dashboard (/)

**File:** `frontend/src/app/page.tsx`

### Purpose
Main landing page showing portfolio overview with key metrics, alerts, and visualizations.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `dashboardApi.getSummary()` | `GET /v1/dashboard/summary` | Portfolio stats, health score, gap stats |
| `dashboardApi.getExpirations()` | `GET /v1/dashboard/expirations` | Upcoming policy expirations |
| `dashboardApi.getAlerts()` | `GET /v1/dashboard/alerts` | Active alerts (gaps, compliance, expirations) |
| `propertiesApi.list()` | `GET /v1/properties` | All properties for visualization |

### Data Displayed

**Stats Grid (4 cards):**
- Total Properties: `summary.portfolio_stats.total_properties`
- Total Insured Value: `summary.portfolio_stats.total_insured_value`
- Annual Premium: `summary.portfolio_stats.total_annual_premium`
- Health Score: `summary.health_score.portfolio_average`

**Expiration Timeline:**
- Shows first 4 upcoming expirations
- Links to property detail page

**Alerts Panel:**
- Shows first 3 active alerts
- Links to property or gaps page

**Portfolio Health Widget:**
- ScoreRing showing portfolio average health
- Properties with gaps count
- Critical gaps count

**Portfolio Visualization:**
- Treemap or Bubble chart (toggleable)
- Shows all properties sized by TIV

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `isLoading === true` | Show loading spinner |
| `error !== null` | Show error state with retry button |
| `expirations.length === 0` | Show "No upcoming expirations" message |
| `alerts.length === 0` | Show green checkmark "No active alerts" |
| `properties.length === 0` | Show empty state with upload CTA |
| `properties.length > 0` | Show portfolio visualization |
| `days_until_expiration <= 14` | Expiration severity = `critical` (red) |
| `days_until_expiration <= 30` | Expiration severity = `warning` (yellow) |
| `days_until_expiration > 30` | Expiration severity = `info` (blue) |

### Greeting Logic
```javascript
const hour = new Date().getHours();
if (hour < 12) return 'Good morning';
if (hour < 18) return 'Good afternoon';
return 'Good evening';
```

---

## 2. Properties (/properties)

**File:** `frontend/src/app/properties/page.tsx`

### Purpose
Property portfolio listing with search, filtering, sorting, and management actions.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `propertiesApi.list()` | `GET /v1/properties` | All properties |
| `dashboardApi.getSummary()` | `GET /v1/dashboard/summary` | Portfolio summary stats |
| `propertiesApi.delete(id)` | `DELETE /v1/properties/{id}` | Soft delete property |
| `adminApi.resetAllData()` | `POST /v1/admin/reset` | Reset all data |

### Data Displayed

**Summary Cards (4):**
- Total Properties: `summary.portfolio_stats.total_properties`
- With Gaps: `summary.gap_stats.properties_with_gaps`
- Expiring in 30d: `summary.expiration_stats.expiring_30_days`
- Total Gaps: `summary.gap_stats.total_open_gaps`

**Property Cards/List:**
- Property name, address
- Health score with grade
- TIV, Premium
- Days until expiration
- Gap count

### Filter Options

| Filter | Options | Default |
|--------|---------|---------|
| Search | Free text (name, street, city) | Empty |
| Health Grade | All, A, B, C, D, F | All |
| Expiration | All, 30 days, 60 days, 90 days | All |
| Sort By | Name, Health, TIV, Premium, Expiration | Name |
| Sort Direction | Ascending, Descending | Ascending |
| View Mode | Grid, List | Grid |

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `isLoading === true` | Show loading spinner |
| `error !== null` | Show error state with retry |
| `filteredAndSortedProperties.length === 0` | Show empty state |
| `properties.length === 0` | Empty state: "Upload documents to create properties" |
| `hasActiveFilters` | Show active filter count, clear button |
| `viewMode === 'grid'` | 3-column grid layout |
| `viewMode === 'list'` | Single column list layout |

### Modals

1. **Delete Property Modal**
   - Shows property name
   - Lists what will be deleted (documents, gaps, policies, compliance)
   - Confirm/Cancel buttons

2. **Reset All Data Modal**
   - Warning about irreversible action
   - Lists all data types being deleted
   - Shows result after reset

---

## 3. Property Detail (/properties/[id])

**File:** `frontend/src/app/properties/[id]/page.tsx`

### Purpose
Comprehensive view of a single property with health score, coverage, gaps, and actions.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `propertiesApi.get(id)` | `GET /v1/properties/{id}` | Full property detail with policies, buildings, completeness |
| `healthScoreApi.get(id)` | `GET /v1/health-score/properties/{id}` | Health score with components |
| `gapsApi.list(property_id)` | `GET /v1/gaps?property_id={id}` | Property gaps |

### Data Displayed

**Hero Header:**
- Property name
- Address (street, city, state, zip)
- Property type badge
- Building/unit counts
- Year built
- Health score (large)
- TIV
- Days until expiration

**Health Score Card:**
- ScoreRing visualization (180px)
- Component breakdown (if available):
  - Component name
  - Percentage score
  - Progress bar
  - Issues list (up to 2 per component)

**Key Metrics Card:**
- Total Insured Value
- Annual Premium
- Total Units
- Year Built

**Coverage Card:**
- First 3 policies with:
  - Policy type
  - Carrier
  - Status indicator (green=active, yellow=other)
- Coverage gaps alert (if any)

**Gaps Card (or Coverage Status):**
- If gaps exist: First 3 gaps with severity and description
- If no gaps: Green "All coverage requirements met" message

**Quick Actions:**
- View Health Score Details
- Address Gaps / View Gap Analysis
- Renewal Planning
- View Documents (with count)
- View Extracted Data

**Renewal Status:**
- Days until expiration
- Progress bar
- Urgency coloring
- Start Renewal Process button

**Document Completeness:**
- Percentage badge
- Required/Optional document counts
- Progress bar
- Checklist items with status
- Upload Missing Documents button

**Property Risk Card:**
- External component for risk enrichment

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `isLoading` | Show loading spinner |
| `error \|\| !property` | Show "Property not found" with back link |
| `healthScore?.components?.length > 0` | Show component breakdown |
| `healthScore?.components?.length === 0` | Show generic score explanation |
| `daysUntilExpiration <= 14` | Critical (red) styling |
| `daysUntilExpiration <= 30` | Warning (yellow) styling |
| `gaps.length > 0` | Show gaps card with gap list |
| `gaps.length === 0` | Show "No Gaps" success card |
| `property.policies?.length === 0` | Show "No policies found" |
| `completeness.percentage >= 75` | Success badge |
| `completeness.percentage >= 50` | Warning badge |
| `completeness.percentage < 50` | Critical badge |

---

## 4. Property Health Score (/properties/[id]/health-score)

**File:** `frontend/src/app/properties/[id]/health-score/page.tsx`

### Purpose
Detailed health score analysis with 3D visualization, component breakdown, and recommendations.

### Data Sources

Currently uses **mock data** for:
- `mockProperties` - Property lookup
- `mockHealthComponents` - Component scores
- `mockRecommendations` - Improvement recommendations
- `mockScoreHistory` - Historical trend

### Data Displayed

**Hero Section:**
- 3D HealthScoreGlobe or 2D ScoreRing (toggleable)
- Current score (large)
- Grade with color
- Trend indicator (+5 pts from last month)
- Potential improvement points

**Component Breakdown:**
- Each health component with:
  - Name
  - Score
  - Max score
  - Issues/details

**Recommendations:**
- Priority-ordered list
- Each recommendation shows:
  - Title
  - Description
  - Potential point improvement
  - Implementation steps

**Score History:**
- Line chart showing trend over time

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `!property` | Show "Property not found" |
| `use3D === true` | Show HealthScoreGlobe |
| `use3D === false` | Show ScoreRing |
| `isRecalculating` | Disable button, show spinner |

---

## 5. Property Renewals (/properties/[id]/renewals)

**File:** `frontend/src/app/properties/[id]/renewals/page.tsx`

### Purpose
Property-specific renewal planning with forecasting, document readiness, market context, and YoY comparison.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `propertiesApi.get(id)` | `GET /v1/properties/{id}` | Property details |
| `renewalsApi.getForecast(id)` | `GET /v1/renewals/forecast/{id}` | Premium forecast |
| `renewalsApi.getAlerts(id)` | `GET /v1/renewals/alerts?property_id={id}` | Property alerts |
| `renewalsApi.getReadiness(id)` | `GET /v1/renewals/readiness/{id}` | Document readiness |
| `renewalsApi.getMarketContext(id)` | `GET /v1/renewals/market-context/{id}` | Market analysis |

**Mock Data Used:**
- `mockRenewalTimelines` - Milestone timeline
- `mockPolicyComparisons` - YoY comparison
- `mockAlertConfigs` - Alert configuration

### Tabs

| Tab | Content |
|-----|---------|
| Overview | Milestones timeline + Alerts sidebar |
| Forecast Details | RenewalForecastCard component |
| Document Readiness | ReadinessChecklist component |
| Market Intelligence | MarketIntelligenceCard + MarketContextPanel |
| YoY Comparison | PolicyComparison component |

### Data Displayed

**Hero Header:**
- Days until expiration (large badge)
- Property name
- Expiration date
- Current premium
- Forecast (mid)
- Estimated change %

**Overview Tab:**
- Milestone progress bar
- Milestone cards with:
  - Status icon (completed, in_progress, upcoming, overdue)
  - Target date
  - Action items checklist
  - Documents ready status
- Alerts list

**Forecast Tab:**
- Low/Mid/High premium range
- Change percentages
- Factor analysis
- Negotiation points

**Documents Tab:**
- Readiness score and grade
- Document checklist (found/missing/stale)
- Upload buttons

**Market Tab:**
- Live market intelligence (Parallel AI)
- Rate trends
- Carrier appetite
- Market factors

**Comparison Tab:**
- Previous vs Current policy
- Coverage changes
- Premium change

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `isLoading` | Show loading spinner |
| `error \|\| !property` | Show error with back button |
| `!forecast` | Show "Generate Forecast" CTA |
| `!readiness` | Show "Upload documents" message |
| `!marketContext` | Only show MarketIntelligenceCard |
| `!comparison` | Show "Requires multiple years" message |
| `severity === 'critical'` | Red badge, pulse animation |
| `severity === 'warning'` | Yellow badge |

---

## 6. Property Extracted Data (/properties/[id]/extracted-data)

**File:** `frontend/src/app/properties/[id]/extracted-data/page.tsx`

### Purpose
View all data extracted from documents for a property, organized by field or document.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `propertiesApi.getExtractedData(id)` | `GET /v1/properties/{id}/extracted-data` | Aggregated extracted fields |

### Data Displayed

**Header Stats:**
- Total documents
- Documents with extractions
- Total fields extracted

**Two View Modes:**

1. **By Field:**
   - Grouped by category (property, valuation, coverage, policy)
   - Each category expandable
   - Field display name + consolidated value
   - Source document chips with confidence

2. **By Document:**
   - Each document expandable
   - Document name, type, upload date
   - Extraction confidence badge
   - Grid of extracted key-value pairs

**Structured Data Sections (Fields view only):**
- Valuations: TIV, building value, contents, business income
- Policies: Type, carrier, policy number, premium, dates, coverage count
- Certificates: Type, number, insured, holder, limits
- Financials: Record type, invoice date, due date, total, taxes, fees

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `isLoading` | Show loading spinner |
| `error \|\| !data` | Show error with retry |
| `categories.length === 0` | Show "No Extracted Data" |
| `document_extractions.length === 0` | Show "No Documents" |
| `activeTab === 'fields'` | Show category-grouped view |
| `activeTab === 'documents'` | Show document-based view |
| `extraction_confidence >= 0.8` | Green confidence badge |
| `extraction_confidence >= 0.6` | Yellow confidence badge |
| `extraction_confidence < 0.6` | Red confidence badge |

### Category Icons & Colors

| Category | Icon | Color |
|----------|------|-------|
| property | Building2 | Blue |
| valuation | DollarSign | Green |
| coverage | Shield | Purple |
| policy | FileText | Orange |

---

## 7. Coverage Gaps (/gaps)

**File:** `frontend/src/app/gaps/page.tsx`

### Purpose
Portfolio-wide coverage gap detection and management.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `gapsApi.list()` | `GET /v1/gaps` | All gaps |
| `propertiesApi.list()` | `GET /v1/properties` | Properties for filtering |
| `gapsApi.detect(property_id)` | `POST /v1/gaps/detect` | Run gap detection |
| `gapsApi.acknowledge(id, notes)` | `POST /v1/gaps/{id}/acknowledge` | Mark acknowledged |
| `gapsApi.resolve(id, notes)` | `POST /v1/gaps/{id}/resolve` | Mark resolved |

### URL Parameters

| Parameter | Purpose |
|-----------|---------|
| `property_id` | Filter to single property |
| `property` | Alias for property_id |

### Data Displayed

**GapStats Component:**
- Total gaps
- By severity (critical, warning, info)
- By status (open, acknowledged, resolved)

**GapList Component:**
- Filterable, searchable list
- Each gap shows:
  - Gap type
  - Severity badge
  - Property name
  - Description
  - Created date

**GapDetailModal:**
- Full gap details
- LLM-generated analysis
- Recommendations
- Acknowledge/Resolve actions

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `isLoading` | Show loading spinner |
| `error` | Show error with retry |
| `propertyFilter` | Show property name badge in header |
| `propertyFilter` | Show "Run Detection" button |
| `isDetecting` | Disable button, show spinner |
| `selectedGap !== null` | Show GapDetailModal |

---

## 8. Compliance (/compliance)

**File:** `frontend/src/app/compliance/page.tsx`

### Purpose
Lender compliance monitoring across all properties.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `propertiesApi.list()` | `GET /v1/properties` | All properties |
| `complianceApi.batchCheckCompliance(ids)` | `POST /v1/compliance/batch` | Compliance results for all |
| `complianceApi.getPropertyCompliance(id)` | `GET /v1/compliance/properties/{id}` | Single property compliance |

### URL Parameters

| Parameter | Purpose |
|-----------|---------|
| `property_id` | Filter to single property |
| `property` | Alias for property_id |

### Data Displayed

**Stats Row (4 cards):**
- Compliant count
- Non-Compliant count
- Total Issues count
- Properties Checked count

**Coverage Overview:**
- Shield visualization
- Coverage types with adequacy percentages

**Property Compliance List:**
- Each property shows:
  - Compliance status icon (check/X)
  - Property name
  - Compliant/Non-Compliant badge
  - Lender name
  - Template name
  - Passed checks ratio
  - Issue count (if non-compliant)

**Compliance Detail Modal:**
- Property name with status badge
- Lender and template info
- List of all checks:
  - Pass/Fail/N/A status
  - Requirement name
  - Current value
  - Required value

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `isLoading` | Show loading spinner |
| `error` | Show error with retry |
| `isLoadingCompliance` | Show spinner in list area |
| `filteredStatuses.length === 0` | Show empty state |
| `properties.length === 0` | Show "Upload documents first" |
| `status.is_compliant` | Green check icon |
| `!status.is_compliant` | Red X icon, issue count badge |
| `isModalOpen` | Show compliance detail modal |

---

## 9. Documents (/documents)

**File:** `frontend/src/app/documents/page.tsx`

### Purpose
Document management with upload, viewing, and filtering.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `documentsApi.list()` | `GET /v1/documents` | All documents |
| `propertiesApi.list()` | `GET /v1/properties` | Properties for filtering |
| `documentsApi.uploadAsync(file, ...)` | `POST /v1/documents/upload/async` | Upload document |

### URL Parameters

| Parameter | Purpose |
|-----------|---------|
| `property_id` | Filter to single property |
| `property` | Alias for property_id |

### Data Displayed

**Stats Row:**
- Total documents
- Completed
- Processing
- Failed
- Needs Review

**Filter Options:**
- Search (filename, carrier, policy number)
- Property dropdown
- Document type dropdown
- Status dropdown (completed, processing, failed, pending)
- View mode toggle (grid/table)

**Document Cards (Grid View):**
- Document type icon
- Filename
- Status icon
- Property name
- Carrier
- Policy number
- Upload date
- Review badge (if needs review)
- Confidence badge

**Document Table (Table View):**
- All above plus columns for actions

**Upload Modal:**
- Property selection (existing or new name)
- File drop zone (PDF only)
- Selected files list with remove option
- Progress bar during upload
- Results summary

**Document Detail Modal:**
- Full document metadata
- View Property / View Extraction / Download actions

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `isLoading` | Show loading spinner |
| `error` | Show error with retry |
| `hasProcessingDocs` | Auto-refresh every 5 seconds |
| `filteredDocuments.length === 0` | Show empty state |
| `viewMode === 'grid'` | 4-column card grid |
| `viewMode === 'table'` | Full-width table |
| `isUploadModalOpen` | Show upload modal |
| `selectedDocument !== null` | Show detail modal |
| `upload_status === 'completed'` | Green check icon |
| `upload_status === 'processing'` | Spinning loader |
| `upload_status === 'pending'` | Pulsing clock |
| `upload_status === 'failed'` | Red X icon |
| `extraction_confidence >= 0.8` | Green confidence badge |
| `extraction_confidence >= 0.6` | Yellow confidence badge |
| `extraction_confidence < 0.6` | Red confidence badge |

---

## 10. Chat (/chat)

**File:** `frontend/src/app/chat/page.tsx`

### Purpose
RAG-powered conversational interface for querying insurance documents.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `propertiesApi.list()` | `GET /v1/properties` | Properties for filtering |
| `streamChat(message, callbacks, conversationId, propertyId)` | `POST /v1/chat` (SSE) | Streaming response with sources |

### Data Displayed

**Empty State:**
- Welcome message
- 4 suggested questions:
  - "What policies are expiring soon?"
  - "Show me coverage gaps"
  - "What is my total insured value?"
  - "Which properties have compliance issues?"

**Messages:**
- User messages (right-aligned, blue)
- Assistant messages (left-aligned, gray)
  - Markdown rendered content
  - Streaming cursor during generation
  - Source citations

**Source Chips:**
- Document name
- Page number (if available)
- Tooltip with:
  - Relevant excerpt
  - Relevance score

**Property Filter:**
- Dropdown to filter responses to specific property
- Clear button

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `messages.length === 0` | Show empty state with suggestions |
| `isLoading` | Disable send button, show spinner |
| `message.isStreaming` | Show blinking cursor |
| `message.error` | Show error message in red |
| `message.sources?.length > 0` | Show source chips below message |
| `selectedPropertyId` | Show filter indicator |
| `showFilters` | Expand filter panel |

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Enter | Send message |
| Shift+Enter | New line |

---

## 11. Renewals Portfolio (/renewals)

**File:** `frontend/src/app/renewals/page.tsx`

### Purpose
Portfolio-wide renewal tracking, timeline, forecasting, and alert management.

### Data Sources

| API Call | Endpoint | Returns |
|----------|----------|---------|
| `propertiesApi.list()` | `GET /v1/properties` | All properties |
| `renewalsApi.getTimeline(undefined, 365)` | `GET /v1/renewals/timeline` | Renewal timeline items + summary |
| `renewalsApi.getAlerts()` | `GET /v1/renewals/alerts` | All renewal alerts |
| `renewalsApi.batchGetForecasts(ids)` | `POST /v1/renewals/forecasts/batch` | Batch forecasts |
| `renewalsApi.acknowledgeAlert(id)` | `POST /v1/renewals/alerts/{id}/acknowledge` | Acknowledge alert |
| `renewalsApi.resolveAlert(id)` | `POST /v1/renewals/alerts/{id}/resolve` | Resolve alert |

### Data Displayed

**Summary Stats (4 cards):**
- Upcoming Renewals: `summary.total_upcoming_renewals`
- Premium at Risk: `summary.total_premium_at_risk`
- Avg Forecast Change: `summary.avg_forecast_change_pct`
- Projected Premium: `summary.projected_total_premium`

**Status Overview (GlassCard):**

*By Urgency:*
- Critical (<30d): Count + red indicator
- Warning (30-60d): Count + yellow indicator
- Early (>60d): Count + blue indicator

*By Status:*
- On Track: No active alerts
- Needs Attention: Has alerts, >30d
- Overdue: Has alerts, <=30d

*Quick Actions:*
- Configure Alert Defaults button
- Generate Renewal Report button

**Renewal Timeline:**
- Sorted by days until expiration (most urgent first)
- Each item shows:
  - Days badge with urgency color
  - Property name
  - Severity badge
  - Expiration date
  - Forecast (mid) value
  - Change percentage
  - Policy type, carrier, current premium
  - "Forecast Ready" / "X Alerts" badges

**Alerts Panel:**
- RenewalAlertsList component
- Acknowledge/Resolve actions

**Forecasts Table:**
- Property name
- Days remaining
- Expiration date with severity badge
- Current premium
- Forecast range (low-high)
- Mid forecast
- Change percentage
- Confidence badge
- View Details link

### Conditional Logic

| Condition | UI Behavior |
|-----------|-------------|
| `isLoading` | Show loading spinner |
| `error` | Show error with retry |
| `sortedTimelines.length === 0` | Show empty state |
| `properties.length === 0` | "Upload documents to create properties" |
| `forecasts.size > 0` | Show forecasts table |
| `days_until_expiration <= 30` | Severity = critical (red) |
| `days_until_expiration <= 60` | Severity = warning (yellow) |
| `days_until_expiration > 60` | Severity = info (blue) |
| `selectedPropertyId` | Highlight selected in timeline |
| `forecast_change_percent >= 0` | Red (increase) |
| `forecast_change_percent < 0` | Green (decrease) |

---

## Common Patterns

### Loading States
All pages use the same loading pattern:
```jsx
if (isLoading) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin" />
    </div>
  );
}
```

### Error States
All pages use the same error pattern:
```jsx
if (error) {
  return (
    <div className="text-center py-16">
      <AlertTriangle className="h-12 w-12 text-[var(--color-critical-500)] mx-auto mb-4" />
      <h3>Failed to load...</h3>
      <p>{error}</p>
      <Button onClick={fetchData}>Try Again</Button>
    </div>
  );
}
```

### API Response Normalization
All pages handle various API response formats:
```javascript
setData(
  Array.isArray(response) ? response :
  response?.items || response?.properties || response?.gaps || []
);
```

### Severity Color Mapping

| Severity | Background | Text |
|----------|------------|------|
| critical | `--color-critical-50/500` | Red |
| warning | `--color-warning-50/500` | Yellow/Orange |
| info | `--color-info-50/500` | Blue |
| success | `--color-success-50/500` | Green |

### Grade Calculation
```javascript
function getGrade(score: number): string {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
}
```

---

## API Endpoints Summary

| Page | Primary Endpoints |
|------|-------------------|
| Dashboard | `/dashboard/summary`, `/dashboard/expirations`, `/dashboard/alerts` |
| Properties | `/properties` |
| Property Detail | `/properties/{id}`, `/health-score/properties/{id}`, `/gaps` |
| Health Score | (Mock data - to be wired) |
| Property Renewals | `/renewals/forecast/{id}`, `/renewals/readiness/{id}`, `/renewals/market-context/{id}` |
| Extracted Data | `/properties/{id}/extracted-data` |
| Gaps | `/gaps`, `/gaps/detect` |
| Compliance | `/compliance/batch`, `/compliance/properties/{id}` |
| Documents | `/documents`, `/documents/upload/async` |
| Chat | `/chat` (SSE streaming) |
| Renewals | `/renewals/timeline`, `/renewals/alerts`, `/renewals/forecasts/batch` |

---

## Health Score Calculation System

The Insurance Health Score (0-100) is calculated by an **LLM (Gemini 2.5 Flash)** using property data as context. The score is composed of 6 weighted components.

**File:** `backend/app/services/health_score_service.py`

### Component Breakdown

| Component | Max Points | What It Measures |
|-----------|------------|------------------|
| **Coverage Adequacy** | 25 | Building coverage vs replacement cost, business income, liability limits |
| **Policy Currency** | 20 | Are policies current? How close to expiration? Any lapse risk? |
| **Deductible Risk** | 15 | Are deductibles reasonable relative to TIV? Out-of-pocket exposure? |
| **Coverage Breadth** | 15 | Required coverages (property, GL) + recommended (umbrella, flood, EQ) |
| **Lender Compliance** | 15 | Does coverage meet lender requirements? Mortgagee listed? |
| **Documentation Quality** | 10 | Are required documents present and current? |

**Total: 100 points**

### Grade Thresholds

| Grade | Score Range | Meaning |
|-------|-------------|---------|
| **A** | 90-100 | Excellent coverage, minimal risk |
| **B** | 80-89 | Good coverage, minor improvements possible |
| **C** | 70-79 | Adequate but notable gaps |
| **D** | 60-69 | Significant gaps requiring attention |
| **F** | 0-59 | Critical deficiencies, high risk |

### Why Properties Get Low Scores (F Grade)

A property will score low (F grade) when:

1. **No Active Insurance Programs**
   - No policies loaded = 0 points for coverage adequacy, policy currency, deductible risk, coverage breadth

2. **Missing Required Coverages**
   - No property coverage policy
   - No general liability policy
   - Missing flood coverage in flood zones

3. **Expired or Expiring Policies**
   - Policies already expired = 0 points for policy currency
   - Policies expiring within 30 days = reduced score

4. **Inadequate Coverage Limits**
   - Building coverage < 80% of replacement cost
   - GL limits below industry standards

5. **Missing Documents**
   - No uploaded documents = low documentation quality score
   - Required documents (policy dec pages, COIs) not present

6. **No Lender Requirements on File**
   - Can't assess lender compliance = lower score

7. **Open Coverage Gaps**
   - Existing unresolved gaps negatively impact the score

### Data Sent to LLM for Scoring

The health score service gathers this context before calling the LLM:

```
PROPERTY DATA:
- Name, type, address, units, sq ft, year built
- Construction type, flood zone, earthquake zone
- Sprinkler status

BUILDINGS:
- Building names and values
- Total building value

POLICIES & COVERAGES:
- Active insurance programs
- Each policy: type, number, carrier, expiration, premium
- Each coverage: name, limit, deductible

LENDER REQUIREMENTS:
- Lender name, loan number, loan amount
- Min property limit, max deductible %
- Requires flood/earthquake
- Current compliance status

DOCUMENTS:
- Document completeness percentage and grade
- Required vs optional documents present
- Missing documents list

EXISTING GAPS:
- Open coverage gaps (up to 10)
- Gap type, severity, amounts

EXTERNAL RISK DATA (from Parallel AI):
- Flood zone and risk level
- Fire protection class and distances
- Weather/CAT exposure (hurricane, tornado, hail, wildfire, earthquake)
- Crime risk index and grade
- Environmental hazards
- Overall risk score and implications
```

### How to Improve a Low Score

| Issue | Action | Points Impact |
|-------|--------|---------------|
| No policies | Upload policy documents | +40-60 points |
| Expired policies | Renew or upload current policies | +15-20 points |
| Missing GL | Add general liability policy | +10-15 points |
| Missing flood (in flood zone) | Add flood coverage | +5-10 points |
| High deductibles | Lower deductibles or document justification | +5-10 points |
| Missing documents | Upload dec pages, COIs, loss runs | +5-10 points |
| No lender requirements | Add lender requirement records | +5-10 points |

---

## Compliance Checking System

The compliance system checks property insurance against lender requirements. It supports both **template-based** and **live** (Parallel AI) compliance checks.

**File:** `backend/app/services/compliance_service.py`

### Compliance Templates

**File:** `backend/app/core/gap_thresholds.py`

#### 1. Standard Commercial
```
min_property_coverage: 100% of building value
min_gl_limit: $1,000,000
min_umbrella_limit: Not required
max_deductible: 5% of TIV
requires_flood: Only if in flood zone
requires_earthquake: No
requires_business_income: No
```

#### 2. Fannie Mae Multifamily
```
min_property_coverage: 100% replacement cost
min_gl_limit: $1,000,000
min_umbrella_limit: Varies by unit count:
  - 1-50 units: $1M
  - 51-100 units: $2M
  - 101-200 units: $5M
  - 200+ units: $10M
max_deductible: 5% of TIV OR $100,000 (whichever is greater)
requires_flood: Yes (if in flood zone)
requires_earthquake: Market dependent
requires_business_income: Yes (12 months)
```

#### 3. Conservative
```
min_property_coverage: 100% of building value
min_gl_limit: $2,000,000
min_umbrella_limit: $5,000,000 (always required)
max_deductible: 2% of TIV OR $50,000
requires_flood: Yes (always)
requires_earthquake: Yes (always)
requires_terrorism: Yes
requires_business_income: Yes
```

### Compliance Checks Performed

| Check | What It Validates | Severity if Failed |
|-------|-------------------|-------------------|
| **Property Coverage** | Coverage >= min required (% of TIV or flat amount) | Critical |
| **General Liability** | GL limit >= minimum required | Critical |
| **Umbrella/Excess** | Umbrella limit >= minimum (if required) | Critical |
| **Deductible (%)** | Deductible % <= max allowed | Warning |
| **Deductible (Flat)** | Deductible $ <= max allowed | Warning |
| **Deductible (% of TIV)** | Flat deductible as % of TIV <= max | Warning |
| **Flood Coverage** | Has flood coverage if required (based on flood zone) | Critical |
| **Earthquake Coverage** | Has earthquake coverage if required | Critical |

### How Compliance Status is Determined

```
if (no issues):
    status = "compliant"
elif (has critical issues):
    status = "non_compliant"
else:
    status = "partial"
```

### Compliance Data Flow

1. **Property loads** with insurance programs, policies, and coverages
2. **Lender requirements** fetched for the property (or template applied)
3. **Coverage data gathered**:
   - Total property limit (sum of property coverages)
   - Total GL limit (sum of liability coverages)
   - Total umbrella limit
   - Total TIV
   - Max deductible % and amount
   - Has flood/earthquake/business income (boolean)
4. **Each check runs** comparing actual vs required
5. **Issues created** for each failed check
6. **Gaps created** if `create_gaps=True` (persisted to database)

### Why Properties Fail Compliance

| Failure Reason | Example |
|----------------|---------|
| **No property coverage** | Total property limit = $0 vs required $1M |
| **Insufficient GL** | GL = $500K vs required $1M |
| **Missing umbrella** | No umbrella policy vs required $5M |
| **High deductibles** | 7% deductible vs max 5% allowed |
| **No flood coverage** | Property in Zone AE with no flood policy |
| **No earthquake coverage** | Required by lender but not present |

### Live Compliance Check (Parallel AI)

The system can fetch **real-time lender requirements** via Parallel AI web research:

```python
# Example: Check against live Wells Fargo requirements
result = await compliance_service.check_compliance_with_live_requirements(
    property_id="...",
    lender_name="Wells Fargo",
    loan_type="Commercial Real Estate"
)
```

This:
1. Calls Parallel AI to research current lender requirements
2. Extracts structured requirements (limits, deductibles, required coverages)
3. Builds a temporary LenderRequirement object
4. Runs the same compliance checks
5. Returns results with "Wells Fargo (Live Research)" as template name

---

## Coverage Gap Detection Thresholds

**File:** `backend/app/core/gap_thresholds.py`

These rule-based thresholds determine when gaps are detected:

### Underinsurance
| Severity | Condition |
|----------|-----------|
| **Critical** | Coverage < 80% of building value |
| **Warning** | Coverage 80-90% of building value |
| **OK** | Coverage >= 90% of building value |

### High Deductible
| Severity | Condition |
|----------|-----------|
| **Critical** | Deductible > 5% of TIV OR > $500K flat |
| **Warning** | Deductible 3-5% of TIV OR > $250K flat |
| **OK** | Deductible <= 3% of TIV AND <= $250K |

### Policy Expiration
| Severity | Days Until Expiration |
|----------|----------------------|
| **Critical** | <= 30 days |
| **Warning** | 31-60 days |
| **Info** | 61-90 days |

### Missing Coverage
| Gap Type | When Detected |
|----------|--------------|
| **Missing Property** | No property coverage policy found |
| **Missing GL** | No general liability policy found |
| **Missing Flood** | Property in flood zone (A, AE, AH, AO, AR, A99, V, VE) without flood coverage |
| **Missing Umbrella** | TIV > $5M without umbrella/excess policy (recommendation) |

### Outdated Valuation
| Severity | Last Appraisal Age |
|----------|-------------------|
| **Critical** | > 3 years old |
| **Warning** | > 2 years old |
| **OK** | <= 2 years old |

### High-Risk Flood Zones

Properties in these FEMA flood zones trigger flood coverage requirements:
- **A** - 100-year flood zone
- **AE** - 100-year flood zone with base flood elevations
- **AH** - 100-year flood zone with 1-3 foot depths
- **AO** - 100-year flood zone with sheet flow
- **AR** - 100-year flood zone, temporary
- **A99** - 100-year flood zone, federal protection
- **V** - Coastal high hazard area
- **VE** - Coastal high hazard area with velocity
