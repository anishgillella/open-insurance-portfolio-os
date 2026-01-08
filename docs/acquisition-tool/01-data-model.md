# Data Model & Schemas

## Overview

This document defines the data structures for the Acquisition Calculator, including request/response schemas, intermediate data types, and database considerations.

---

## Request Schema

### AcquisitionCalculateRequest

The input from the user's form submission.

```python
from pydantic import BaseModel, Field
from decimal import Decimal

class AcquisitionCalculateRequest(BaseModel):
    """Request schema for acquisition calculation."""

    # Property Identification
    address: str = Field(
        ...,
        description="Full street address of the property",
        example="123 East Street, Fort Wayne, IN 46802"
    )
    link: str | None = Field(
        default=None,
        description="Optional URL to property listing"
    )

    # Building Characteristics
    unit_count: int = Field(
        ...,
        ge=1,
        description="Total number of units",
        example=150
    )
    vintage: int = Field(
        ...,
        ge=1800,
        le=2030,
        description="Year the property was built",
        example=2002
    )
    stories: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of stories/floors",
        example=3
    )
    total_buildings: int = Field(
        ...,
        ge=1,
        description="Total number of buildings on property",
        example=3
    )
    total_sf: int = Field(
        ...,
        ge=100,
        description="Total gross square footage",
        example=40000
    )

    # Financial & Occupancy
    current_occupancy_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Current occupancy percentage (0-100)",
        example=80.0
    )
    estimated_annual_income: Decimal = Field(
        ...,
        ge=0,
        description="Estimated gross annual income",
        example=1000000
    )

    # Additional Context
    notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional notes about the property",
        example="Next to a lakefront, recently renovated lobby"
    )
```

---

## Response Schemas

### PremiumRange

Represents a range of premium estimates.

```python
class PremiumRange(BaseModel):
    """Premium range with low/mid/high estimates."""

    low: Decimal = Field(
        ...,
        description="Lower bound premium estimate ($/unit)",
        example=100
    )
    mid: Decimal = Field(
        ...,
        description="Mid-point premium estimate ($/unit)",
        example=200
    )
    high: Decimal = Field(
        ...,
        description="Upper bound premium estimate ($/unit)",
        example=800
    )
```

### ComparableProperty

A property used for comparison.

```python
from datetime import date

class ComparableProperty(BaseModel):
    """A comparable property with premium data."""

    property_id: str = Field(
        ...,
        description="Unique identifier of the comparable property"
    )
    name: str = Field(
        ...,
        description="Property name",
        example="Shoaff Park Apartments"
    )
    address: str = Field(
        ...,
        description="Property address",
        example="Fort Wayne, IN"
    )
    premium_per_unit: Decimal = Field(
        ...,
        description="Premium per unit ($/unit)",
        example=1827
    )
    premium_date: date = Field(
        ...,
        description="Date of the premium data",
        example="2025-06-15"
    )
    similarity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="LLM-assigned similarity score (0-100)",
        example=85
    )
    similarity_reason: str | None = Field(
        default=None,
        description="LLM explanation of why this property is comparable"
    )
```

### RiskFactor

An identified risk that affects premium.

```python
from typing import Literal

class RiskFactor(BaseModel):
    """An insurance risk factor identified by LLM."""

    name: str = Field(
        ...,
        description="Risk factor name",
        example="Flood Zone"
    )
    severity: Literal["info", "warning", "critical"] = Field(
        ...,
        description="Severity level of the risk"
    )
    reason: str | None = Field(
        default=None,
        description="LLM explanation of why this risk applies",
        example="Address mentions lakefront proximity"
    )
```

### AcquisitionCalculateResponse

The complete response from the calculation.

```python
class AcquisitionCalculateResponse(BaseModel):
    """Complete response from acquisition calculation."""

    # Uniqueness Detection
    is_unique: bool = Field(
        ...,
        description="True if property is too unique for automated pricing"
    )
    uniqueness_reason: str | None = Field(
        default=None,
        description="LLM explanation of why property is unique"
    )

    # Confidence
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="Confidence level in the estimate"
    )

    # Premium Estimates
    premium_range: PremiumRange | None = Field(
        default=None,
        description="Premium range estimates ($/unit)"
    )
    premium_range_label: str | None = Field(
        default=None,
        description="Human-readable premium range description",
        example="medium range ($200-$800)"
    )

    # For unique properties
    preliminary_estimate: PremiumRange | None = Field(
        default=None,
        description="Best-guess estimate for unique properties"
    )

    # User Message
    message: str | None = Field(
        default=None,
        description="User-friendly summary or action message"
    )

    # Comparable Properties
    comparables: list[ComparableProperty] = Field(
        default_factory=list,
        description="List of comparable properties used in calculation"
    )

    # Risk Factors
    risk_factors: list[RiskFactor] = Field(
        default_factory=list,
        description="Identified risk factors affecting premium"
    )

    # LLM Explanation
    llm_explanation: str | None = Field(
        default=None,
        description="LLM's overall explanation of the analysis"
    )
```

---

## Internal Schemas

### ScoredComparable

Internal representation of a scored comparable from LLM.

```python
class ScoredComparable(BaseModel):
    """LLM-scored comparable property (internal use)."""

    property_id: str
    score: int  # 0-100
    reasoning: str
```

### LLMComparablesResponse

Expected JSON structure from LLM comparables call.

```python
class LLMComparablesResponse(BaseModel):
    """Expected response structure from LLM comparables analysis."""

    comparables: list[ScoredComparable]
    overall_assessment: str
```

### LLMRiskFactorsResponse

Expected JSON structure from LLM risk analysis.

```python
class LLMRiskFactorsResponse(BaseModel):
    """Expected response structure from LLM risk analysis."""

    risk_factors: list[RiskFactor]
```

---

## Database Considerations

### Current Data Available

From existing `properties` table and mock data:

| Field | Available | Source |
|-------|-----------|--------|
| Property ID | Yes | `properties.id` |
| Name | Yes | `properties.name` |
| Address | Yes | `properties.address`, `city`, `state`, `zip` |
| Lat/Lng | Yes (mock) | `mockProperties.latitude`, `longitude` |
| Units | Yes | `properties.units` |
| Year Built | Yes | `properties.year_built` |
| Total Buildings | Partial | Count from `buildings` table |
| Square Footage | Yes | `properties.sq_ft` |
| Premium | Yes | `insurance_programs.total_premium` |
| Premium Date | Yes | `insurance_programs.effective_date` |

### Calculated Fields

| Field | Calculation |
|-------|-------------|
| `premium_per_unit` | `total_premium / units` |
| `age` | `current_year - year_built` |

### Data Gaps (Not Currently Stored)

| Field | Needed For | Workaround |
|-------|------------|------------|
| Occupancy % | Input validation | Not stored, input only |
| Annual Income | Input validation | Not stored, input only |
| Geocoding | Distance calc | Use mock lat/lng for now |

---

## TypeScript Types (Frontend)

```typescript
// Request
export interface AcquisitionRequest {
  address: string;
  link?: string;
  unit_count: number;
  vintage: number;
  stories: number;
  total_buildings: number;
  total_sf: number;
  current_occupancy_pct: number;
  estimated_annual_income: number;
  notes?: string;
}

// Response
export interface PremiumRange {
  low: number;
  mid: number;
  high: number;
}

export interface ComparableProperty {
  property_id: string;
  name: string;
  address: string;
  premium_per_unit: number;
  premium_date: string;
  similarity_score: number;
  similarity_reason?: string;
}

export interface RiskFactor {
  name: string;
  severity: 'info' | 'warning' | 'critical';
  reason?: string;
}

export interface AcquisitionResult {
  is_unique: boolean;
  uniqueness_reason?: string;
  confidence: 'high' | 'medium' | 'low';
  premium_range?: PremiumRange;
  premium_range_label?: string;
  preliminary_estimate?: PremiumRange;
  message?: string;
  comparables: ComparableProperty[];
  risk_factors: RiskFactor[];
  llm_explanation?: string;
}
```

---

## Example Payloads

### Request Example

```json
{
  "address": "123 East Street, Fort Wayne, IN 46802",
  "link": null,
  "unit_count": 150,
  "vintage": 2002,
  "stories": 3,
  "total_buildings": 3,
  "total_sf": 40000,
  "current_occupancy_pct": 80,
  "estimated_annual_income": 1000000,
  "notes": "Next to a lakefront"
}
```

### Response Example (Normal)

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
      "severity": "warning",
      "reason": null
    }
  ],
  "llm_explanation": "Found 5 comparable properties in Indiana with similar characteristics. Premium estimates based on weighted average of comparables."
}
```

### Response Example (Unique Property)

```json
{
  "is_unique": true,
  "uniqueness_reason": "This lakefront property with unusual vintage characteristics is unlike any in our portfolio. Best comparables have low similarity (avg: 42/100).",
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
    }
  ],
  "llm_explanation": null
}
```

---

## Related Documents

- [02-llm-service.md](./02-llm-service.md) - LLM integration that produces these responses
- [03-api-design.md](./03-api-design.md) - API endpoint using these schemas
