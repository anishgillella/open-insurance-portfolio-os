# Dashboard & Portfolio API

## Overview

The Dashboard API provides endpoints for viewing portfolio summary statistics, managing properties, and accessing policy information. This forms the foundation for all user-facing features in Phase 4.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DASHBOARD API LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  /v1/dashboard                                                              │
│  ├── GET /summary              → Portfolio-wide statistics                  │
│  ├── GET /expirations          → Upcoming policy expirations                │
│  └── GET /alerts               → Active alerts and notifications           │
│                                                                             │
│  /v1/properties                                                             │
│  ├── GET /                     → List all properties                        │
│  ├── POST /                    → Create new property                        │
│  ├── GET /{id}                 → Property detail with related data          │
│  ├── PUT /{id}                 → Update property                            │
│  ├── DELETE /{id}              → Delete property                            │
│  ├── GET /{id}/policies        → Policies for property                      │
│  ├── GET /{id}/documents       → Documents for property                     │
│  ├── GET /{id}/gaps            → Coverage gaps for property                 │
│  └── GET /{id}/health-score    → Insurance health score                     │
│                                                                             │
│  /v1/policies                                                               │
│  ├── GET /                     → List all policies                          │
│  ├── GET /{id}                 → Policy detail with coverages               │
│  ├── GET /{id}/coverages       → Coverages for policy                       │
│  └── GET /{id}/documents       → Source documents for policy                │
│                                                                             │
│  /v1/programs                                                               │
│  ├── GET /                     → List insurance programs                    │
│  ├── GET /{id}                 → Program detail                             │
│  └── GET /{id}/policies        → Policies in program                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Endpoints Specification

### Dashboard Summary

#### `GET /v1/dashboard/summary`

Returns portfolio-wide statistics for the dashboard overview.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organization_id` | UUID | No | Filter by organization (future multi-tenant) |

**Response Schema:**
```json
{
  "portfolio_stats": {
    "total_properties": 7,
    "total_buildings": 23,
    "total_units": 1450,
    "total_insured_value": 125000000.00,
    "total_annual_premium": 650000.00
  },
  "expiration_stats": {
    "expiring_30_days": 2,
    "expiring_60_days": 1,
    "expiring_90_days": 3,
    "next_expiration": {
      "property_name": "Buffalo Run",
      "policy_type": "property",
      "expiration_date": "2025-02-15",
      "days_until_expiration": 28
    }
  },
  "gap_stats": {
    "total_open_gaps": 5,
    "critical_gaps": 2,
    "warning_gaps": 2,
    "info_gaps": 1,
    "properties_with_gaps": 3
  },
  "compliance_stats": {
    "compliant_properties": 5,
    "non_compliant_properties": 2,
    "properties_without_requirements": 0
  },
  "completeness_stats": {
    "average_completeness": 78.5,
    "fully_complete_properties": 3,
    "properties_missing_required_docs": 2
  },
  "health_score": {
    "portfolio_average": 72,
    "trend": "improving",
    "trend_delta": 3
  },
  "generated_at": "2025-01-15T10:30:00Z"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `portfolio_stats.total_properties` | integer | Count of all properties |
| `portfolio_stats.total_buildings` | integer | Count of all buildings |
| `portfolio_stats.total_units` | integer | Sum of all units across properties |
| `portfolio_stats.total_insured_value` | decimal | Sum of all TIV (Total Insured Value) |
| `portfolio_stats.total_annual_premium` | decimal | Sum of all annual premiums |
| `expiration_stats.expiring_30_days` | integer | Policies expiring in ≤30 days |
| `expiration_stats.expiring_60_days` | integer | Policies expiring in 31-60 days |
| `expiration_stats.expiring_90_days` | integer | Policies expiring in 61-90 days |
| `gap_stats.total_open_gaps` | integer | Count of all open coverage gaps |
| `gap_stats.critical_gaps` | integer | Count of critical severity gaps |
| `health_score.portfolio_average` | integer | Average Insurance Health Score (0-100) |
| `health_score.trend` | string | "improving", "stable", or "declining" |

---

### Expiration Timeline

#### `GET /v1/dashboard/expirations`

Returns upcoming policy expirations for timeline visualization.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days_ahead` | integer | No | 90 | How many days to look ahead |
| `limit` | integer | No | 20 | Max results to return |

**Response Schema:**
```json
{
  "expirations": [
    {
      "id": "uuid",
      "property_id": "uuid",
      "property_name": "Buffalo Run",
      "policy_id": "uuid",
      "policy_number": "PRO-2024-001234",
      "policy_type": "property",
      "carrier_name": "Zurich",
      "expiration_date": "2025-02-15",
      "days_until_expiration": 28,
      "severity": "critical",
      "annual_premium": 145000.00,
      "coverage_limit": 35989980.00
    }
  ],
  "summary": {
    "total_expiring": 6,
    "total_premium_at_risk": 425000.00
  }
}
```

**Severity Levels:**
| Days Until Expiration | Severity |
|----------------------|----------|
| ≤ 30 days | `critical` |
| 31-60 days | `warning` |
| 61-90 days | `info` |

---

### Dashboard Alerts

#### `GET /v1/dashboard/alerts`

Returns active alerts requiring attention.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `severity` | string | No | all | Filter: critical, warning, info |
| `type` | string | No | all | Filter: gap, expiration, compliance |
| `limit` | integer | No | 10 | Max results |

**Response Schema:**
```json
{
  "alerts": [
    {
      "id": "uuid",
      "type": "gap",
      "severity": "critical",
      "title": "Underinsured Property",
      "message": "Buffalo Run property coverage is only 75% of building value",
      "property_id": "uuid",
      "property_name": "Buffalo Run",
      "created_at": "2025-01-10T14:30:00Z",
      "action_url": "/properties/{id}/gaps"
    }
  ],
  "counts": {
    "critical": 2,
    "warning": 3,
    "info": 5
  }
}
```

---

## Property Endpoints

### List Properties

#### `GET /v1/properties`

Returns all properties with summary information. For typical portfolios (< 100 properties), returns complete list without pagination.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `organization_id` | UUID | No | - | Filter by organization |
| `sort_by` | string | No | name | Sort field: name, premium, expiration, health_score |
| `sort_order` | string | No | asc | Sort order: asc, desc |
| `search` | string | No | - | Search by name or address |
| `state` | string | No | - | Filter by state code |
| `has_gaps` | boolean | No | - | Filter properties with open gaps |
| `expiring_within` | integer | No | - | Filter by days until next expiration |
| `limit` | integer | No | 100 | Max results to return |

**Response Schema:**
```json
{
  "properties": [
    {
      "id": "uuid",
      "name": "Buffalo Run",
      "address": {
        "street": "123 Buffalo Way",
        "city": "Houston",
        "state": "TX",
        "zip": "77001"
      },
      "property_type": "multifamily",
      "total_units": 200,
      "total_buildings": 5,
      "total_insured_value": 35989980.00,
      "annual_premium": 145000.00,
      "next_expiration": "2025-02-15",
      "days_until_expiration": 28,
      "open_gaps_count": 2,
      "compliance_status": "compliant",
      "health_score": 72,
      "completeness_pct": 85,
      "coverage_types": ["property", "general_liability", "umbrella"]
    }
  ],
  "total_count": 7
}
```

---

### Property Detail

#### `GET /v1/properties/{id}`

Returns detailed property information including related entities.

**Response Schema:**
```json
{
  "id": "uuid",
  "name": "Buffalo Run",
  "address": {
    "street": "123 Buffalo Way",
    "city": "Houston",
    "state": "TX",
    "zip": "77001",
    "county": "Harris"
  },
  "property_type": "multifamily",
  "year_built": 1995,
  "construction_type": "frame",
  "total_units": 200,
  "total_sqft": 180000,
  "occupancy_rate": 94.5,

  "buildings": [
    {
      "id": "uuid",
      "name": "Building A",
      "units": 40,
      "stories": 3,
      "sqft": 36000,
      "year_built": 1995,
      "replacement_cost": 7200000.00
    }
  ],

  "insurance_summary": {
    "total_insured_value": 35989980.00,
    "total_annual_premium": 145000.00,
    "policy_count": 3,
    "next_expiration": "2025-02-15",
    "coverage_types": ["property", "general_liability", "umbrella"]
  },

  "health_score": {
    "score": 72,
    "grade": "C",
    "components": {
      "coverage_adequacy": 18,
      "policy_currency": 20,
      "deductible_risk": 12,
      "coverage_breadth": 12,
      "lender_compliance": 15,
      "documentation_quality": 8
    },
    "trend": "improving",
    "calculated_at": "2025-01-15T10:00:00Z"
  },

  "gaps_summary": {
    "total_open": 2,
    "critical": 1,
    "warning": 1,
    "info": 0
  },

  "compliance_summary": {
    "status": "compliant",
    "lender_name": "Wells Fargo",
    "issues_count": 0
  },

  "completeness": {
    "percentage": 85,
    "required_present": 3,
    "required_total": 3,
    "optional_present": 4,
    "optional_total": 6
  },

  "created_at": "2024-06-15T10:00:00Z",
  "updated_at": "2025-01-10T14:30:00Z"
}
```

---

### Property Policies

#### `GET /v1/properties/{id}/policies`

Returns all policies associated with a property.

**Response Schema:**
```json
{
  "policies": [
    {
      "id": "uuid",
      "policy_number": "PRO-2024-001234",
      "policy_type": "property",
      "carrier": {
        "id": "uuid",
        "name": "Zurich",
        "am_best_rating": "A+"
      },
      "effective_date": "2024-02-15",
      "expiration_date": "2025-02-15",
      "days_until_expiration": 28,
      "status": "active",
      "annual_premium": 95000.00,
      "total_limit": 35989980.00,
      "deductible": 25000.00,
      "coverage_count": 5,
      "source_document_id": "uuid"
    }
  ],
  "summary": {
    "total_policies": 3,
    "total_premium": 145000.00,
    "active_policies": 3,
    "expired_policies": 0
  }
}
```

---

## Policy Endpoints

### Policy Detail

#### `GET /v1/policies/{id}`

Returns detailed policy information including all coverages.

**Response Schema:**
```json
{
  "id": "uuid",
  "policy_number": "PRO-2024-001234",
  "policy_type": "property",

  "carrier": {
    "id": "uuid",
    "name": "Zurich",
    "am_best_rating": "A+",
    "naic_number": "16535"
  },

  "insured_entity": {
    "id": "uuid",
    "name": "ABC Properties LLC",
    "entity_type": "llc"
  },

  "dates": {
    "effective_date": "2024-02-15",
    "expiration_date": "2025-02-15",
    "days_until_expiration": 28,
    "policy_term_months": 12
  },

  "financials": {
    "annual_premium": 95000.00,
    "total_limit": 35989980.00,
    "aggregate_limit": 35989980.00,
    "deductible": 25000.00,
    "deductible_type": "flat",
    "coinsurance_pct": 90
  },

  "coverages": [
    {
      "id": "uuid",
      "coverage_type": "building",
      "description": "Building Coverage - Replacement Cost",
      "limit": 35989980.00,
      "deductible": 25000.00,
      "valuation_type": "replacement_cost",
      "coinsurance_pct": 90
    },
    {
      "id": "uuid",
      "coverage_type": "business_income",
      "description": "Business Income with Extra Expense",
      "limit": 2000000.00,
      "waiting_period_days": 72,
      "period_of_indemnity_months": 12
    }
  ],

  "endorsements": [
    {
      "id": "uuid",
      "endorsement_number": "END-001",
      "title": "Ordinance or Law Coverage",
      "effective_date": "2024-02-15",
      "premium_change": 1500.00
    }
  ],

  "additional_insureds": [
    {
      "name": "Wells Fargo Bank NA",
      "type": "mortgagee",
      "address": "123 Bank St, Charlotte NC"
    }
  ],

  "source_documents": [
    {
      "id": "uuid",
      "filename": "buffalo_run_property_policy_2024.pdf",
      "document_type": "policy",
      "uploaded_at": "2024-02-20T10:00:00Z"
    }
  ],

  "extraction_confidence": 0.92,
  "created_at": "2024-02-20T10:30:00Z",
  "updated_at": "2024-02-20T10:30:00Z"
}
```

---

## Program Endpoints

### List Programs

#### `GET /v1/programs`

Returns insurance programs (multi-carrier programs).

**Response Schema:**
```json
{
  "programs": [
    {
      "id": "uuid",
      "program_name": "2024 Property Program",
      "program_type": "property",
      "effective_date": "2024-02-15",
      "expiration_date": "2025-02-15",
      "total_insured_value": 125000000.00,
      "total_premium": 450000.00,
      "carrier_count": 3,
      "property_count": 7,
      "policy_count": 7
    }
  ]
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Property not found",
    "details": {
      "property_id": "uuid"
    }
  }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Implementation Notes

### Database Queries

For dashboard summary, use aggregation queries:

```python
# Example: Get portfolio stats
async def get_portfolio_stats(db: AsyncSession) -> PortfolioStats:
    result = await db.execute(
        select(
            func.count(Property.id).label("total_properties"),
            func.sum(Property.total_units).label("total_units"),
            func.sum(Policy.annual_premium).label("total_premium"),
        )
        .select_from(Property)
        .outerjoin(Policy, Property.id == Policy.property_id)
        .where(Policy.status == "active")
    )
    return result.one()
```

### Caching Strategy

- Dashboard summary: Cache for 5 minutes
- Property list: Cache for 1 minute
- Property detail: No cache (always fresh)

### No Pagination for MVP

For typical commercial real estate portfolios (< 100 properties, < 500 policies), pagination is not needed:

- All list endpoints return complete results
- Optional `limit` parameter provides control if needed
- Simplifies frontend implementation
- Can add pagination later for enterprise scale

---

## Related Documents

- [02-gap-detection.md](./02-gap-detection.md) - Gap endpoints
- [03-compliance-checking.md](./03-compliance-checking.md) - Compliance endpoints
- [05-insurance-health-score.md](./05-insurance-health-score.md) - Health score calculation
