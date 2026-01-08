# Implementation Phases

## Overview

This document outlines the step-by-step implementation plan for the Acquisition Calculator. Each phase builds on the previous one, allowing for incremental testing and validation.

---

## Phase Summary

| Phase | Focus | Duration | Deliverable |
|-------|-------|----------|-------------|
| 1 | Backend Schemas | ~1 hour | Pydantic models defined |
| 2 | LLM Service | ~2 hours | AI integration working |
| 3 | Backend Service | ~1 hour | Business logic complete |
| 4 | API Endpoint | ~30 min | Endpoint testable |
| 5 | Frontend Types | ~30 min | TypeScript types ready |
| 6 | Frontend Page | ~2 hours | UI functional |
| 7 | Navigation | ~15 min | Page accessible |
| 8 | Testing | ~1 hour | End-to-end verified |

---

## Phase 1: Backend Schemas

**Goal:** Define all data structures for the feature.

### File: `backend/app/schemas/acquisitions.py`

**Tasks:**
- [ ] Create `AcquisitionCalculateRequest` model
- [ ] Create `PremiumRange` model
- [ ] Create `ComparableProperty` model
- [ ] Create `RiskFactor` model
- [ ] Create `AcquisitionCalculateResponse` model
- [ ] Add field validation (min/max values, required fields)

**Validation:**
```bash
# Verify imports work
python -c "from app.schemas.acquisitions import AcquisitionCalculateRequest"
```

---

## Phase 2: LLM Service

**Goal:** Implement AI-powered analysis using existing patterns.

### File: `backend/app/services/acquisitions_llm_service.py`

**Tasks:**
- [ ] Create `AcquisitionsLLMService` class
- [ ] Implement `_call_llm()` with retry logic
- [ ] Implement `_format_candidates()` helper
- [ ] Implement `find_comparable_properties()` method
- [ ] Implement `analyze_risk_factors()` method
- [ ] Implement `assess_uniqueness()` method (deterministic)
- [ ] Add singleton factory function `get_acquisitions_llm_service()`

**Testing:**
```python
# Quick test of LLM service
from app.services.acquisitions_llm_service import get_acquisitions_llm_service

service = get_acquisitions_llm_service()

# Test risk analysis (doesn't need candidates)
import asyncio
from app.schemas.acquisitions import AcquisitionCalculateRequest

request = AcquisitionCalculateRequest(
    address="123 Lakefront Dr, Miami, FL",
    unit_count=100,
    vintage=1965,
    stories=2,
    total_buildings=2,
    total_sf=30000,
    current_occupancy_pct=80,
    estimated_annual_income=800000,
    notes="Next to a lake",
)

result = asyncio.run(service.analyze_risk_factors(request))
print(result)
```

---

## Phase 3: Backend Service

**Goal:** Create orchestration layer that combines LLM with data.

### File: `backend/app/services/acquisitions_service.py`

**Tasks:**
- [ ] Create `AcquisitionsService` class
- [ ] Implement `calculate_acquisition()` main method
- [ ] Implement `_get_candidate_properties()` (mock data initially)
- [ ] Implement `_calculate_premium_range()`
- [ ] Implement `_calculate_preliminary_estimate()`
- [ ] Implement `_get_premium_range_label()`
- [ ] Implement `_build_comparable_list()`
- [ ] Implement `_build_risk_list()`

### File: `backend/app/lib/mock_data.py` (if needed)

**Tasks:**
- [ ] Create mock properties constant from frontend mock data
- [ ] Include all fields needed for comparison

**Testing:**
```python
# Test service with mock session
from app.services.acquisitions_service import AcquisitionsService
from app.schemas.acquisitions import AcquisitionCalculateRequest

# Create mock session (or None for mock data mode)
service = AcquisitionsService(session=None)

request = AcquisitionCalculateRequest(
    address="123 Test St, Fort Wayne, IN",
    unit_count=150,
    vintage=2002,
    stories=3,
    total_buildings=3,
    total_sf=40000,
    current_occupancy_pct=80,
    estimated_annual_income=1000000,
)

import asyncio
result = asyncio.run(service.calculate_acquisition(request))
print(result)
```

---

## Phase 4: API Endpoint

**Goal:** Expose the service via REST API.

### File: `backend/app/api/v1/endpoints/acquisitions.py`

**Tasks:**
- [ ] Create router with `APIRouter()`
- [ ] Implement `POST /calculate` endpoint
- [ ] Add proper error handling
- [ ] Add OpenAPI documentation (summary, description, examples)

### File: `backend/app/api/v1/router.py`

**Tasks:**
- [ ] Import acquisitions router
- [ ] Register router with prefix `/acquisitions`

**Testing:**
```bash
# Start backend server
cd backend
uvicorn app.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/v1/acquisitions/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 East Street, Fort Wayne, IN",
    "unit_count": 150,
    "vintage": 2002,
    "stories": 3,
    "total_buildings": 3,
    "total_sf": 40000,
    "current_occupancy_pct": 80,
    "estimated_annual_income": 1000000,
    "notes": "Next to a lakefront"
  }'
```

**Verify in Swagger:**
- Open http://localhost:8000/docs
- Find `/acquisitions/calculate` endpoint
- Test with example request

---

## Phase 5: Frontend Types & API

**Goal:** Add TypeScript types and API client.

### File: `frontend/src/types/api.ts`

**Tasks:**
- [ ] Add `AcquisitionRequest` interface
- [ ] Add `PremiumRange` interface
- [ ] Add `ComparableProperty` interface
- [ ] Add `RiskFactor` interface
- [ ] Add `AcquisitionResult` interface

### File: `frontend/src/lib/api/index.ts`

**Tasks:**
- [ ] Add `acquisitionsApi` object
- [ ] Implement `calculate()` method using `apiPost`

**Testing:**
```typescript
// In browser console or test file
import { acquisitionsApi } from '@/lib/api';

const result = await acquisitionsApi.calculate({
  address: '123 Test St',
  unit_count: 100,
  vintage: 2000,
  stories: 2,
  total_buildings: 2,
  total_sf: 30000,
  current_occupancy_pct: 80,
  estimated_annual_income: 500000,
});

console.log(result);
```

---

## Phase 6: Frontend Page & Components

**Goal:** Build the complete UI.

### Step 6.1: Create Page Skeleton

**File:** `frontend/src/app/acquisitions/page.tsx`

**Tasks:**
- [ ] Create basic page structure
- [ ] Add header with title and buttons
- [ ] Add two-column grid layout
- [ ] Add state for result, loading, error

### Step 6.2: Create Form Component

**File:** `frontend/src/components/features/acquisitions/AcquisitionForm.tsx`

**Tasks:**
- [ ] Create form with all fields
- [ ] Add validation
- [ ] Add Calculate button with loading state
- [ ] Add Reset button
- [ ] Wire up to page callbacks

### Step 6.3: Create Results Components

**Files:**
- `frontend/src/components/features/acquisitions/AcquisitionResults.tsx`
- `frontend/src/components/features/acquisitions/PremiumRangeBar.tsx`
- `frontend/src/components/features/acquisitions/ComparablesChart.tsx`
- `frontend/src/components/features/acquisitions/RiskFactorsList.tsx`
- `frontend/src/components/features/acquisitions/UniquePropertyModal.tsx`

**Tasks:**
- [ ] Create `AcquisitionResults` wrapper with conditional rendering
- [ ] Create `PremiumRangeBar` with Low/Medium/High visualization
- [ ] Create `ComparablesChart` using Recharts ScatterChart
- [ ] Create `RiskFactorsList` with 6 risk factor badges
- [ ] Create `UniquePropertyModal` for unique property edge case

### Step 6.4: Create Index Export

**File:** `frontend/src/components/features/acquisitions/index.ts`

```typescript
export { AcquisitionForm } from './AcquisitionForm';
export { AcquisitionResults } from './AcquisitionResults';
export { PremiumRangeBar } from './PremiumRangeBar';
export { ComparablesChart } from './ComparablesChart';
export { RiskFactorsList } from './RiskFactorsList';
export { UniquePropertyModal } from './UniquePropertyModal';
```

**Testing:**
```bash
# Start frontend
cd frontend
npm run dev

# Open http://localhost:3000/acquisitions
# Fill form and test Calculate button
```

---

## Phase 7: Navigation

**Goal:** Make the page accessible from sidebar.

### File: `frontend/src/components/layouts/AppShell/Sidebar.tsx`

**Tasks:**
- [ ] Import `Calculator` icon from lucide-react
- [ ] Add navigation item for Acquisitions
- [ ] Position appropriately in nav order

**Verification:**
- Navigate to dashboard
- Click on Acquisitions in sidebar
- Verify page loads correctly

---

## Phase 8: Testing & Polish

**Goal:** Verify end-to-end functionality and fix issues.

### Test Cases

| Test Case | Expected Result |
|-----------|-----------------|
| Empty form submit | Validation errors shown |
| Valid form submit | Loading state, then results |
| Normal property | Premium range, chart, risk factors |
| Unique property | Modal with consultant message |
| API error | Error message displayed |
| Reset button | Form cleared, results hidden |

### Manual Testing Checklist

- [ ] All form fields accept input correctly
- [ ] Form validation prevents invalid submissions
- [ ] Calculate button shows loading state
- [ ] Results panel updates with data
- [ ] Premium range bar displays correctly
- [ ] Comparables chart renders with tooltips
- [ ] Risk factors show correct severity colors
- [ ] Unique property modal displays correctly
- [ ] Reset clears form and results
- [ ] Page is accessible from sidebar
- [ ] Page is responsive on mobile

### Edge Cases

- [ ] Property with no notes
- [ ] Property with very old vintage (1900)
- [ ] Property with very new vintage (2025)
- [ ] Very high occupancy (100%)
- [ ] Very low occupancy (0%)
- [ ] Large property (1000+ units)
- [ ] Small property (1 unit)

---

## File Checklist

### Backend Files

| File | Status |
|------|--------|
| `backend/app/schemas/acquisitions.py` | [ ] Created |
| `backend/app/services/acquisitions_llm_service.py` | [ ] Created |
| `backend/app/services/acquisitions_service.py` | [ ] Created |
| `backend/app/api/v1/endpoints/acquisitions.py` | [ ] Created |
| `backend/app/api/v1/router.py` | [ ] Modified |
| `backend/app/lib/mock_data.py` | [ ] Created (if needed) |

### Frontend Files

| File | Status |
|------|--------|
| `frontend/src/types/api.ts` | [ ] Modified |
| `frontend/src/lib/api/index.ts` | [ ] Modified |
| `frontend/src/app/acquisitions/page.tsx` | [ ] Created |
| `frontend/src/components/features/acquisitions/AcquisitionForm.tsx` | [ ] Created |
| `frontend/src/components/features/acquisitions/AcquisitionResults.tsx` | [ ] Created |
| `frontend/src/components/features/acquisitions/PremiumRangeBar.tsx` | [ ] Created |
| `frontend/src/components/features/acquisitions/ComparablesChart.tsx` | [ ] Created |
| `frontend/src/components/features/acquisitions/RiskFactorsList.tsx` | [ ] Created |
| `frontend/src/components/features/acquisitions/UniquePropertyModal.tsx` | [ ] Created |
| `frontend/src/components/features/acquisitions/index.ts` | [ ] Created |
| `frontend/src/components/layouts/AppShell/Sidebar.tsx` | [ ] Modified |

---

## Post-Implementation

### Future Enhancements

1. **Database Integration**
   - Replace mock data with actual property queries
   - Add geocoding for distance-based comparables

2. **PDF Export**
   - Generate downloadable PDF report
   - Include all calculation details

3. **Email Functionality**
   - Send results via email
   - Queue unique properties for consultant review

4. **Address Autocomplete**
   - Integrate Google Places API
   - Auto-fill city/state from address

5. **Historical Tracking**
   - Save calculation history
   - Compare multiple properties

---

## Related Documents

- [00-overview.md](./00-overview.md) - Feature overview
- [01-data-model.md](./01-data-model.md) - Schema definitions
- [02-llm-service.md](./02-llm-service.md) - LLM integration
- [03-api-design.md](./03-api-design.md) - API specification
- [04-frontend-components.md](./04-frontend-components.md) - UI components
