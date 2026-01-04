# Insurance Health Score™

## Overview

The Insurance Health Score is a **novel, proprietary metric** that provides a single score (0-100) measuring how well-protected a property or portfolio is. Unlike external risk scores that focus on perils (flood, fire, earthquake), the Health Score measures the **quality of your actual insurance coverage**.

**This is an innovation that doesn't exist in the market today.**

---

## Why This Matters

### Current State (What Exists)
- **External Risk Scores:** HazardHub, Zesty.ai, etc. measure property-level *peril exposure* (flood risk, wildfire risk)
- **Credit-Based Insurance Scores:** Used by insurers for pricing, not visible to property owners
- **No Coverage Quality Score:** No tool tells property owners "How well am I actually protected?"

### The Gap
Property owners currently have no way to answer:
- "Is my portfolio adequately insured?"
- "Am I improving or declining over time?"
- "How do I compare to similar properties?"

### Our Innovation
The Insurance Health Score answers: **"How well-protected is this property/portfolio based on coverage quality, not just risk exposure?"**

---

## Score Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     INSURANCE HEALTH SCORE (0-100)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  COVERAGE ADEQUACY (25%)                                            │   │
│  │  Are coverage limits sufficient for property values?                │   │
│  │  ├── Building coverage vs replacement cost                          │   │
│  │  ├── Business income coverage adequacy                              │   │
│  │  └── Liability limits appropriateness                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  POLICY CURRENCY (20%)                                              │   │
│  │  Are policies current and not near expiration?                      │   │
│  │  ├── No expired policies                                            │   │
│  │  ├── No policies expiring within 30 days                           │   │
│  │  └── Renewal process started for policies expiring 60-90 days      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DEDUCTIBLE RISK (15%)                                              │   │
│  │  Are deductibles at manageable levels?                              │   │
│  │  ├── Percentage deductibles within limits (≤5% of TIV)             │   │
│  │  ├── Flat deductibles reasonable                                    │   │
│  │  └── No excessive out-of-pocket exposure                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  COVERAGE BREADTH (15%)                                             │   │
│  │  Does coverage include all recommended types?                       │   │
│  │  ├── Required coverages present (Property, GL)                      │   │
│  │  ├── Recommended coverages present (Umbrella if TIV > $5M)         │   │
│  │  ├── Special coverages for location (Flood, Earthquake)            │   │
│  │  └── Business income, equipment breakdown, etc.                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LENDER COMPLIANCE (15%)                                            │   │
│  │  Does coverage meet lender requirements?                            │   │
│  │  ├── All lender requirements satisfied                              │   │
│  │  ├── Mortgagee properly listed                                      │   │
│  │  └── Required endorsements in place                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DOCUMENTATION QUALITY (10%)                                        │   │
│  │  Is insurance documentation complete?                               │   │
│  │  ├── All required documents uploaded                                │   │
│  │  ├── Optional documents present                                     │   │
│  │  └── Documents are current (not outdated)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Scoring Algorithm

### Component Weights

| Component | Weight | Max Points |
|-----------|--------|------------|
| Coverage Adequacy | 25% | 25 |
| Policy Currency | 20% | 20 |
| Deductible Risk | 15% | 15 |
| Coverage Breadth | 15% | 15 |
| Lender Compliance | 15% | 15 |
| Documentation Quality | 10% | 10 |
| **Total** | **100%** | **100** |

### Score Grades

| Score Range | Grade | Description |
|-------------|-------|-------------|
| 90-100 | A | Excellent - Well protected |
| 80-89 | B | Good - Minor improvements possible |
| 70-79 | C | Fair - Several issues to address |
| 60-69 | D | Poor - Significant gaps |
| 0-59 | F | Critical - Immediate action required |

---

## Component Calculations

### 1. Coverage Adequacy (25 points max)

```python
def calculate_coverage_adequacy(
    property: Property,
    policies: List[Policy]
) -> float:
    """Calculate coverage adequacy score (0-25 points)."""

    scores = []

    # Building coverage ratio (0-10 points)
    building_value = sum(b.replacement_cost for b in property.buildings)
    property_policy = get_active_policy(policies, "property")

    if property_policy and building_value > 0:
        coverage_ratio = property_policy.building_limit / building_value
        if coverage_ratio >= 1.0:
            building_score = 10
        elif coverage_ratio >= 0.90:
            building_score = 8
        elif coverage_ratio >= 0.80:
            building_score = 5
        else:
            building_score = coverage_ratio * 5  # Linear 0-5 for < 80%
        scores.append(building_score)
    else:
        scores.append(0)

    # Business income coverage (0-8 points)
    if property_policy:
        has_bi = any(c.coverage_type == "business_income" for c in property_policy.coverages)
        bi_months = get_bi_period_months(property_policy)

        if has_bi and bi_months >= 12:
            bi_score = 8
        elif has_bi and bi_months >= 6:
            bi_score = 5
        elif has_bi:
            bi_score = 3
        else:
            bi_score = 0
        scores.append(bi_score)
    else:
        scores.append(0)

    # Liability adequacy (0-7 points)
    gl_policy = get_active_policy(policies, "general_liability")
    if gl_policy:
        per_occurrence = gl_policy.per_occurrence_limit or 0
        if per_occurrence >= 2_000_000:
            liability_score = 7
        elif per_occurrence >= 1_000_000:
            liability_score = 5
        elif per_occurrence >= 500_000:
            liability_score = 3
        else:
            liability_score = 1
        scores.append(liability_score)
    else:
        scores.append(0)

    return sum(scores)  # Max 25
```

### 2. Policy Currency (20 points max)

```python
def calculate_policy_currency(policies: List[Policy]) -> float:
    """Calculate policy currency score (0-20 points)."""

    if not policies:
        return 0

    today = date.today()
    active_policies = [p for p in policies if p.status == "active"]

    if not active_policies:
        return 0

    # Check for expired policies (-10 points each, min 0)
    expired_count = sum(1 for p in policies if p.expiration_date and p.expiration_date < today)
    if expired_count > 0:
        return 0  # Any expired policy = 0 score

    # Calculate based on time until expiration
    min_days_until_expiration = min(
        (p.expiration_date - today).days
        for p in active_policies
        if p.expiration_date
    )

    if min_days_until_expiration > 90:
        return 20  # All policies > 90 days out
    elif min_days_until_expiration > 60:
        return 15  # Closest policy 60-90 days
    elif min_days_until_expiration > 30:
        return 10  # Closest policy 30-60 days
    elif min_days_until_expiration > 0:
        return 5   # Closest policy < 30 days
    else:
        return 0   # Expired
```

### 3. Deductible Risk (15 points max)

```python
def calculate_deductible_risk(
    property: Property,
    policies: List[Policy]
) -> float:
    """Calculate deductible risk score (0-15 points)."""

    property_policy = get_active_policy(policies, "property")
    if not property_policy:
        return 0

    tiv = sum(b.replacement_cost for b in property.buildings)
    score = 15  # Start with max, deduct for issues

    # Check percentage deductible
    if property_policy.deductible_pct:
        pct = property_policy.deductible_pct
        if pct > 0.05:
            score -= 10  # Critical: > 5%
        elif pct > 0.03:
            score -= 5   # Warning: 3-5%
        elif pct > 0.02:
            score -= 2   # Minor: 2-3%

    # Check flat deductible
    if property_policy.deductible:
        deductible = property_policy.deductible
        if deductible > 500_000:
            score -= 8
        elif deductible > 250_000:
            score -= 5
        elif deductible > 100_000:
            score -= 2

    return max(0, score)
```

### 4. Coverage Breadth (15 points max)

```python
def calculate_coverage_breadth(
    property: Property,
    policies: List[Policy]
) -> float:
    """Calculate coverage breadth score (0-15 points)."""

    coverage_types = {p.policy_type for p in policies if p.status == "active"}
    tiv = sum(b.replacement_cost for b in property.buildings)
    score = 0

    # Required coverages (0-8 points)
    if "property" in coverage_types:
        score += 4
    if "general_liability" in coverage_types:
        score += 4

    # Recommended coverages (0-4 points)
    if tiv > 5_000_000 and "umbrella" in coverage_types:
        score += 4
    elif tiv <= 5_000_000:
        score += 4  # Umbrella not required for smaller properties

    # Special coverages (0-3 points)
    if property.flood_zone in ["A", "AE", "V", "VE"]:
        if "flood" in coverage_types or has_flood_coverage(policies):
            score += 3
    else:
        score += 3  # Flood not required

    return min(15, score)
```

### 5. Lender Compliance (15 points max)

```python
def calculate_lender_compliance(
    property_id: UUID,
    compliance_result: Optional[ComplianceResult]
) -> float:
    """Calculate lender compliance score (0-15 points)."""

    if not compliance_result:
        return 15  # No lender requirements = full score

    if compliance_result.overall_status == "no_requirements":
        return 15

    if compliance_result.overall_status == "compliant":
        return 15

    # Calculate based on number of issues
    total_checks = len(compliance_result.checks)
    passed_checks = sum(1 for c in compliance_result.checks if c.status == "pass")

    if total_checks == 0:
        return 15

    compliance_ratio = passed_checks / total_checks
    return round(compliance_ratio * 15)
```

### 6. Documentation Quality (10 points max)

```python
def calculate_documentation_quality(
    completeness_result: CompletenessResult
) -> float:
    """Calculate documentation quality score (0-10 points)."""

    # Direct mapping from completeness percentage
    return completeness_result.percentage / 10
```

---

## Full Calculation

```python
class HealthScoreService:
    def __init__(
        self,
        property_repo: PropertyRepository,
        policy_repo: PolicyRepository,
        compliance_service: ComplianceService,
        completeness_service: CompletenessService,
        gap_repo: GapRepository
    ):
        self.property_repo = property_repo
        self.policy_repo = policy_repo
        self.compliance_service = compliance_service
        self.completeness_service = completeness_service
        self.gap_repo = gap_repo

    async def calculate_health_score(
        self,
        property_id: UUID
    ) -> HealthScoreResult:
        """Calculate comprehensive health score for a property."""

        property = await self.property_repo.get(property_id)
        policies = await self.policy_repo.get_by_property(property_id)
        compliance = await self.compliance_service.check_compliance(property_id)
        completeness = await self.completeness_service.get_completeness(property_id)

        # Calculate each component
        coverage_adequacy = calculate_coverage_adequacy(property, policies)
        policy_currency = calculate_policy_currency(policies)
        deductible_risk = calculate_deductible_risk(property, policies)
        coverage_breadth = calculate_coverage_breadth(property, policies)
        lender_compliance = calculate_lender_compliance(property_id, compliance)
        documentation_quality = calculate_documentation_quality(completeness)

        # Sum components
        total_score = (
            coverage_adequacy +
            policy_currency +
            deductible_risk +
            coverage_breadth +
            lender_compliance +
            documentation_quality
        )

        # Determine grade
        grade = self._get_grade(total_score)

        # Calculate trend (compare to previous)
        previous = await self._get_previous_score(property_id)
        if previous:
            trend = "improving" if total_score > previous else "declining" if total_score < previous else "stable"
            trend_delta = total_score - previous
        else:
            trend = "new"
            trend_delta = 0

        # Store result
        result = HealthScoreResult(
            property_id=property_id,
            score=round(total_score),
            grade=grade,
            components={
                "coverage_adequacy": round(coverage_adequacy, 1),
                "policy_currency": round(policy_currency, 1),
                "deductible_risk": round(deductible_risk, 1),
                "coverage_breadth": round(coverage_breadth, 1),
                "lender_compliance": round(lender_compliance, 1),
                "documentation_quality": round(documentation_quality, 1)
            },
            trend=trend,
            trend_delta=trend_delta,
            calculated_at=datetime.utcnow()
        )

        await self._store_score(result)
        return result

    def _get_grade(self, score: float) -> str:
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
```

---

## API Endpoints

### Get Property Health Score

#### `GET /v1/properties/{id}/health-score`

Returns the Insurance Health Score for a property.

**Response:**
```json
{
  "property_id": "uuid",
  "property_name": "Buffalo Run",
  "score": 72,
  "grade": "C",
  "components": {
    "coverage_adequacy": {
      "score": 18,
      "max": 25,
      "percentage": 72,
      "details": {
        "building_coverage": "95% of replacement cost",
        "business_income": "12 months coverage",
        "liability": "$1M per occurrence"
      }
    },
    "policy_currency": {
      "score": 20,
      "max": 20,
      "percentage": 100,
      "details": {
        "nearest_expiration": "45 days",
        "expired_policies": 0
      }
    },
    "deductible_risk": {
      "score": 10,
      "max": 15,
      "percentage": 67,
      "details": {
        "property_deductible": "3% of TIV",
        "issue": "Above recommended 2% threshold"
      }
    },
    "coverage_breadth": {
      "score": 12,
      "max": 15,
      "percentage": 80,
      "details": {
        "present": ["property", "general_liability", "umbrella"],
        "missing": [],
        "note": "All recommended coverages in place"
      }
    },
    "lender_compliance": {
      "score": 10,
      "max": 15,
      "percentage": 67,
      "details": {
        "status": "non_compliant",
        "issues": ["Deductible exceeds lender maximum"]
      }
    },
    "documentation_quality": {
      "score": 8.5,
      "max": 10,
      "percentage": 85,
      "details": {
        "completeness": "85%",
        "missing": ["proposal", "endorsements"]
      }
    }
  },
  "trend": {
    "direction": "improving",
    "delta": 3,
    "previous_score": 69,
    "previous_date": "2024-12-15T10:00:00Z"
  },
  "recommendations": [
    {
      "priority": "high",
      "component": "lender_compliance",
      "action": "Reduce deductible to 2% or less at renewal",
      "potential_improvement": 5
    },
    {
      "priority": "medium",
      "component": "coverage_adequacy",
      "action": "Increase building coverage to 100% of replacement cost",
      "potential_improvement": 4
    }
  ],
  "calculated_at": "2025-01-15T10:00:00Z"
}
```

---

### Get Portfolio Health Score

#### `GET /v1/health-score/portfolio`

Returns aggregate health score for the entire portfolio.

**Response:**
```json
{
  "portfolio_score": 75,
  "portfolio_grade": "C",
  "property_count": 7,
  "distribution": {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 1,
    "F": 0
  },
  "component_averages": {
    "coverage_adequacy": 18.5,
    "policy_currency": 17.2,
    "deductible_risk": 12.1,
    "coverage_breadth": 13.8,
    "lender_compliance": 12.4,
    "documentation_quality": 7.8
  },
  "trend": {
    "direction": "improving",
    "delta": 2,
    "period": "30_days"
  },
  "properties": [
    {
      "id": "uuid",
      "name": "Buffalo Run",
      "score": 72,
      "grade": "C",
      "trend": "improving"
    },
    {
      "id": "uuid",
      "name": "Lake Sheri",
      "score": 91,
      "grade": "A",
      "trend": "stable"
    }
  ],
  "calculated_at": "2025-01-15T10:00:00Z"
}
```

---

### Get Health Score History

#### `GET /v1/properties/{id}/health-score/history`

Returns historical health scores for trend analysis.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | integer | 90 | Number of days of history |

**Response:**
```json
{
  "property_id": "uuid",
  "current_score": 72,
  "history": [
    {
      "date": "2025-01-15",
      "score": 72,
      "grade": "C"
    },
    {
      "date": "2025-01-01",
      "score": 70,
      "grade": "C"
    },
    {
      "date": "2024-12-15",
      "score": 69,
      "grade": "D"
    },
    {
      "date": "2024-12-01",
      "score": 65,
      "grade": "D"
    }
  ],
  "trend_analysis": {
    "30_day_change": 2,
    "90_day_change": 7,
    "direction": "improving",
    "projected_30_day": 75
  }
}
```

---

## Benchmarking (Future Enhancement)

### Comparison Data
```json
{
  "property_id": "uuid",
  "score": 72,
  "benchmarks": {
    "portfolio_average": 75,
    "portfolio_percentile": 42,
    "similar_properties": {
      "criteria": "Multifamily, Texas, 100-300 units",
      "average": 68,
      "percentile": 65,
      "sample_size": 150
    }
  }
}
```

---

## Storage Schema

```sql
CREATE TABLE health_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id),
    score INTEGER NOT NULL,
    grade VARCHAR(1) NOT NULL,
    components JSONB NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_health_scores_property_date
ON health_scores(property_id, calculated_at DESC);
```

---

## Recalculation Triggers

The health score should be recalculated when:

1. **Document Ingested** - New policy or document affects scores
2. **Gap Detected/Resolved** - Coverage issues change
3. **Compliance Changed** - Lender requirements updated
4. **Manual Request** - User triggers recalculation
5. **Daily Job** - Catch expiration changes (policy currency)

```python
# Event handlers
@on_event("document.ingested")
async def recalc_on_ingestion(event):
    if event.property_id:
        await health_score_service.calculate_health_score(event.property_id)

@on_event("gap.created")
@on_event("gap.resolved")
async def recalc_on_gap_change(event):
    await health_score_service.calculate_health_score(event.property_id)

@scheduled("0 6 * * *")  # Daily at 6 AM
async def daily_recalculation():
    properties = await property_repo.list_all()
    for prop in properties:
        await health_score_service.calculate_health_score(prop.id)
```

---

## Related Documents

- [02-gap-detection.md](./02-gap-detection.md) - Gaps affect coverage adequacy score
- [03-compliance-checking.md](./03-compliance-checking.md) - Compliance component
- [04-document-completeness.md](./04-document-completeness.md) - Documentation quality component
- [01-dashboard-api.md](./01-dashboard-api.md) - Health score in dashboard
