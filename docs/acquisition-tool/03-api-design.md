# API Design

## Overview

The Acquisition Calculator exposes a single POST endpoint that accepts property details and returns premium estimates with comparable properties and risk factors.

---

## Endpoint

### Calculate Acquisition Premium

```
POST /v1/acquisitions/calculate
```

Calculates estimated insurance premium for a property being considered for acquisition.

---

## Request

### Headers

| Header | Required | Value |
|--------|----------|-------|
| Content-Type | Yes | application/json |
| Authorization | No | Bearer token (if auth enabled) |

### Body

```json
{
  "address": "123 East Street, Fort Wayne, IN 46802",
  "link": "https://example.com/listing/123",
  "unit_count": 150,
  "vintage": 2002,
  "stories": 3,
  "total_buildings": 3,
  "total_sf": 40000,
  "current_occupancy_pct": 80,
  "estimated_annual_income": 1000000,
  "notes": "Next to a lakefront, recently renovated lobby"
}
```

### Field Validation

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| address | string | Yes | Non-empty |
| link | string | No | Valid URL format |
| unit_count | integer | Yes | >= 1 |
| vintage | integer | Yes | 1800-2030 |
| stories | integer | Yes | 1-100 |
| total_buildings | integer | Yes | >= 1 |
| total_sf | integer | Yes | >= 100 |
| current_occupancy_pct | float | Yes | 0-100 |
| estimated_annual_income | decimal | Yes | >= 0 |
| notes | string | No | max 2000 chars |

---

## Response

### Success (200 OK)

#### Normal Property Response

```json
{
  "is_unique": false,
  "uniqueness_reason": null,
  "confidence": "high",
  "premium_range": {
    "low": 100,
    "mid": 200,
    "high": 800
  },
  "premium_range_label": "medium range ($200-$800)",
  "preliminary_estimate": null,
  "message": "This property is likely to be within the medium range ($200-$800).",
  "comparables": [
    {
      "property_id": "prop-1",
      "name": "Shoaff Park Apartments",
      "address": "Fort Wayne, IN",
      "premium_per_unit": 1827,
      "premium_date": "2025-06-15",
      "similarity_score": 85,
      "similarity_reason": "Similar vintage, same state, comparable size"
    },
    {
      "property_id": "prop-2",
      "name": "Buffalo Run Estates",
      "address": "Fort Wayne, IN",
      "premium_per_unit": 1872,
      "premium_date": "2025-02-18",
      "similarity_score": 78,
      "similarity_reason": "Same market, similar unit count"
    }
  ],
  "risk_factors": [
    {
      "name": "Flood Zone",
      "severity": "warning",
      "reason": "Address mentions lakefront proximity"
    },
    {
      "name": "Vintage Wiring",
      "severity": "info",
      "reason": null
    }
  ],
  "llm_explanation": "Found 5 comparable properties in Indiana with similar characteristics. Premium estimates based on weighted average of top comparables."
}
```

#### Unique Property Response

```json
{
  "is_unique": true,
  "uniqueness_reason": "This lakefront property with 1920s vintage wiring is unlike any in our portfolio. Best comparables have low similarity (avg: 42/100).",
  "confidence": "low",
  "premium_range": null,
  "premium_range_label": null,
  "preliminary_estimate": {
    "low": 180,
    "mid": 315,
    "high": 450
  },
  "message": "This property is a bit unique. We need our insurance consultants to put their eyes on it and will circulate an email with estimates in the next 24 hours. Thanks for being a valued partner of Open Insurance.",
  "comparables": [],
  "risk_factors": [
    {
      "name": "Flood Zone",
      "severity": "critical",
      "reason": "Lakefront location indicates high flood risk"
    },
    {
      "name": "Vintage Wiring",
      "severity": "critical",
      "reason": "1920 construction has severely outdated electrical systems"
    }
  ],
  "llm_explanation": null
}
```

### Error Responses

#### 400 Bad Request - Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "unit_count"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

#### 500 Internal Server Error - LLM Failure

```json
{
  "detail": "Failed to calculate acquisition premium. Please try again later."
}
```

---

## Implementation

### File: `backend/app/api/v1/endpoints/acquisitions.py`

```python
from fastapi import APIRouter, HTTPException, status
import logging

from app.core.dependencies import AsyncSessionDep
from app.services.acquisitions_service import AcquisitionsService
from app.schemas.acquisitions import (
    AcquisitionCalculateRequest,
    AcquisitionCalculateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/calculate",
    response_model=AcquisitionCalculateResponse,
    summary="Calculate acquisition premium estimate",
    description="""
    Calculates estimated insurance premium for a property being considered for acquisition.

    The calculation uses AI to:
    1. Find comparable properties from the existing portfolio
    2. Score similarity based on location, vintage, size, and characteristics
    3. Identify risk factors from property details and notes
    4. Generate premium range estimates

    If the property is too unique to estimate reliably, it will be flagged for
    human consultant review.
    """,
    responses={
        200: {
            "description": "Successful calculation",
            "content": {
                "application/json": {
                    "examples": {
                        "normal": {
                            "summary": "Normal property with comparables",
                            "value": {
                                "is_unique": False,
                                "confidence": "high",
                                "premium_range": {"low": 100, "mid": 200, "high": 800},
                                "comparables": [{"property_id": "prop-1", "...": "..."}],
                                "risk_factors": [{"name": "Flood Zone", "severity": "warning"}],
                            },
                        },
                        "unique": {
                            "summary": "Unique property requiring consultant review",
                            "value": {
                                "is_unique": True,
                                "uniqueness_reason": "Property characteristics are unusual...",
                                "confidence": "low",
                                "preliminary_estimate": {"low": 180, "mid": 315, "high": 450},
                            },
                        },
                    }
                }
            },
        },
        400: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
async def calculate_acquisition(
    request: AcquisitionCalculateRequest,
    db: AsyncSessionDep,
) -> AcquisitionCalculateResponse:
    """Calculate acquisition premium estimate."""
    try:
        service = AcquisitionsService(db)
        result = await service.calculate_acquisition(request)
        return result

    except Exception as e:
        logger.exception(f"Failed to calculate acquisition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate acquisition premium. Please try again later.",
        )
```

### Router Registration

**File: `backend/app/api/v1/router.py`**

Add to imports:
```python
from app.api.v1.endpoints import acquisitions
```

Add to router registration:
```python
api_router.include_router(
    acquisitions.router,
    prefix="/acquisitions",
    tags=["acquisitions"]
)
```

---

## Service Layer

### File: `backend/app/services/acquisitions_service.py`

```python
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.property_repository import PropertyRepository
from app.services.acquisitions_llm_service import get_acquisitions_llm_service
from app.schemas.acquisitions import (
    AcquisitionCalculateRequest,
    AcquisitionCalculateResponse,
    PremiumRange,
    ComparableProperty,
    RiskFactor,
)
from app.lib.mock_data import MOCK_PROPERTIES  # For initial development


class AcquisitionsService:
    """Orchestrates acquisition calculation using LLM and data services."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.property_repo = PropertyRepository(session)
        self.llm_service = get_acquisitions_llm_service()

    async def calculate_acquisition(
        self,
        request: AcquisitionCalculateRequest,
    ) -> AcquisitionCalculateResponse:
        """Calculate acquisition premium estimate.

        Flow:
        1. Get candidate properties (mock or DB)
        2. LLM scores comparables
        3. LLM analyzes risk factors
        4. Assess uniqueness
        5. Calculate premium ranges
        6. Build response
        """
        # 1. Get candidate properties
        candidates = await self._get_candidate_properties()

        # 2. LLM scores and ranks comparables
        comparables_result = await self.llm_service.find_comparable_properties(
            target=request,
            candidates=candidates,
        )

        # 3. LLM identifies risk factors
        risks_result = await self.llm_service.analyze_risk_factors(target=request)

        # 4. Assess uniqueness (deterministic based on LLM scores)
        uniqueness = self.llm_service.assess_uniqueness(comparables_result)

        # 5. Calculate premium ranges
        premium_range = None
        preliminary_estimate = None
        premium_range_label = None
        message = None

        if uniqueness["is_unique"]:
            # Unique property - provide preliminary estimate + consultant message
            preliminary_estimate = self._calculate_preliminary_estimate(candidates)
            message = (
                "This property is a bit unique. We need our insurance consultants "
                "to put their eyes on it and will circulate an email with estimates "
                "in the next 24 hours. Thanks for being a valued partner of Open Insurance."
            )
        else:
            # Normal property - calculate from comparables
            premium_range = self._calculate_premium_range(
                comparables_result, candidates
            )
            premium_range_label = self._get_premium_range_label(premium_range)
            message = f"This property is likely to be within the {premium_range_label}."

        # 6. Build comparable property list
        comparable_list = self._build_comparable_list(
            comparables_result, candidates
        )

        # 7. Build risk factor list
        risk_list = self._build_risk_list(risks_result)

        return AcquisitionCalculateResponse(
            is_unique=uniqueness["is_unique"],
            uniqueness_reason=uniqueness.get("reason"),
            confidence=uniqueness["confidence"],
            premium_range=premium_range,
            premium_range_label=premium_range_label,
            preliminary_estimate=preliminary_estimate,
            message=message,
            comparables=comparable_list,
            risk_factors=risk_list,
            llm_explanation=comparables_result.get("overall_assessment"),
        )

    async def _get_candidate_properties(self) -> list[dict]:
        """Get candidate properties for comparison.

        For MVP, uses mock data. Later will query database.
        """
        # TODO: Replace with actual database query
        # properties = await self.property_repo.list_with_summary(limit=100)

        # For now, use mock data with calculated premium_per_unit
        candidates = []
        for prop in MOCK_PROPERTIES:
            candidate = {
                **prop,
                "premium_per_unit": (
                    prop["total_premium"] / prop["total_units"]
                    if prop.get("total_units", 0) > 0
                    else 0
                ),
            }
            candidates.append(candidate)

        return candidates

    def _calculate_premium_range(
        self,
        comparables_result: dict,
        candidates: list[dict],
    ) -> PremiumRange:
        """Calculate premium range from top comparables."""
        scored = comparables_result.get("comparables", [])

        # Get premium/unit for top comparables
        premiums = []
        for comp in scored[:10]:  # Top 10
            prop_id = comp.get("property_id")
            # Find matching candidate
            for c in candidates:
                if c.get("id") == prop_id:
                    premiums.append(c.get("premium_per_unit", 0))
                    break

        if not premiums:
            # Fallback to all candidates
            premiums = [c.get("premium_per_unit", 0) for c in candidates if c.get("premium_per_unit", 0) > 0]

        if not premiums:
            return PremiumRange(low=Decimal(0), mid=Decimal(0), high=Decimal(0))

        # Calculate ranges
        sorted_premiums = sorted(premiums)
        low = sorted_premiums[0] if sorted_premiums else 0
        high = sorted_premiums[-1] if sorted_premiums else 0
        mid = sum(premiums) / len(premiums) if premiums else 0

        return PremiumRange(
            low=Decimal(str(round(low, 2))),
            mid=Decimal(str(round(mid, 2))),
            high=Decimal(str(round(high, 2))),
        )

    def _calculate_preliminary_estimate(
        self,
        candidates: list[dict],
    ) -> PremiumRange:
        """Calculate preliminary estimate for unique properties."""
        premiums = [
            c.get("premium_per_unit", 0)
            for c in candidates
            if c.get("premium_per_unit", 0) > 0
        ]

        if not premiums:
            return PremiumRange(low=Decimal(0), mid=Decimal(0), high=Decimal(0))

        # Use wider range for uncertainty
        sorted_premiums = sorted(premiums)
        low = sorted_premiums[int(len(sorted_premiums) * 0.1)]  # 10th percentile
        high = sorted_premiums[int(len(sorted_premiums) * 0.9)]  # 90th percentile
        mid = sum(premiums) / len(premiums)

        return PremiumRange(
            low=Decimal(str(round(low, 2))),
            mid=Decimal(str(round(mid, 2))),
            high=Decimal(str(round(high, 2))),
        )

    def _get_premium_range_label(self, premium_range: PremiumRange) -> str:
        """Generate human-readable premium range label."""
        return f"medium range (${premium_range.low:,.0f}-${premium_range.high:,.0f})"

    def _build_comparable_list(
        self,
        comparables_result: dict,
        candidates: list[dict],
    ) -> list[ComparableProperty]:
        """Build list of comparable properties for response."""
        result = []
        scored = comparables_result.get("comparables", [])

        for comp in scored[:10]:  # Top 10
            prop_id = comp.get("property_id")

            # Find matching candidate
            for c in candidates:
                if c.get("id") == prop_id:
                    address = c.get("address", {})
                    address_str = f"{address.get('city', '')}, {address.get('state', '')}"

                    result.append(
                        ComparableProperty(
                            property_id=prop_id,
                            name=c.get("name", "Unknown"),
                            address=address_str,
                            premium_per_unit=Decimal(str(c.get("premium_per_unit", 0))),
                            premium_date=date.today(),  # TODO: Use actual date
                            similarity_score=comp.get("score", 0),
                            similarity_reason=comp.get("reasoning"),
                        )
                    )
                    break

        return result

    def _build_risk_list(self, risks_result: dict) -> list[RiskFactor]:
        """Build list of risk factors for response."""
        result = []
        risks = risks_result.get("risk_factors", [])

        for risk in risks:
            result.append(
                RiskFactor(
                    name=risk.get("name", "Unknown"),
                    severity=risk.get("severity", "info"),
                    reason=risk.get("reason"),
                )
            )

        return result
```

---

## Testing

### Manual Testing with cURL

```bash
# Test successful calculation
curl -X POST http://localhost:8000/v1/acquisitions/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 East Street, Fort Wayne, IN 46802",
    "unit_count": 150,
    "vintage": 2002,
    "stories": 3,
    "total_buildings": 3,
    "total_sf": 40000,
    "current_occupancy_pct": 80,
    "estimated_annual_income": 1000000,
    "notes": "Next to a lakefront"
  }'

# Test with minimal required fields
curl -X POST http://localhost:8000/v1/acquisitions/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "address": "456 Test Ave, Indianapolis, IN",
    "unit_count": 50,
    "vintage": 1965,
    "stories": 2,
    "total_buildings": 1,
    "total_sf": 20000,
    "current_occupancy_pct": 75,
    "estimated_annual_income": 500000
  }'
```

### OpenAPI Documentation

Available at: `http://localhost:8000/docs#/acquisitions`

---

## Related Documents

- [01-data-model.md](./01-data-model.md) - Schema definitions
- [02-llm-service.md](./02-llm-service.md) - LLM integration
- [04-frontend-components.md](./04-frontend-components.md) - Frontend consuming this API
