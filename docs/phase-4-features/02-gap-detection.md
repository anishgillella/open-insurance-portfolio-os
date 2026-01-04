# Coverage Gap Detection

## Overview

The Gap Detection system automatically identifies potential coverage problems across the portfolio. It uses a rules engine to evaluate properties, policies, and coverages against industry standards and configurable thresholds.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GAP DETECTION ENGINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          TRIGGER LAYER                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Document   │  │    Manual    │  │   Scheduled  │              │   │
│  │  │  Ingestion   │  │   Trigger    │  │     Job      │              │   │
│  │  │   Complete   │  │   Endpoint   │  │   (Future)   │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         RULES ENGINE                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Underinsur-  │  │    High      │  │  Expiration  │              │   │
│  │  │    ance      │  │  Deductible  │  │    Check     │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Missing    │  │   Missing    │  │   Outdated   │              │   │
│  │  │   Coverage   │  │    Flood     │  │  Valuation   │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         GAP MANAGEMENT                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │    Create    │  │ Deduplicate  │  │   Notify     │              │   │
│  │  │     Gap      │  │   Existing   │  │    User      │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Gap Types

### 1. Underinsurance Gap

**Description:** Coverage limit is less than property/building value, risking coinsurance penalties.

**Industry Standard:**
- Most policies have 80-90% coinsurance clause ([NAIOP](https://www.naiop.org/))
- Below 80% triggers claim penalties
- Best practice is 100% coverage

**Detection Logic:**
```python
def check_underinsurance(property: Property, policy: Policy) -> Optional[Gap]:
    building_value = sum(b.replacement_cost for b in property.buildings)
    coverage_limit = policy.building_limit

    coverage_ratio = coverage_limit / building_value if building_value > 0 else 1.0

    if coverage_ratio < 0.80:
        return Gap(
            gap_type="underinsurance",
            severity="critical",
            title=f"Underinsured - Coverage at {coverage_ratio:.0%}",
            description=f"Building coverage is only {coverage_ratio:.0%} of replacement cost. "
                       f"This may trigger coinsurance penalties on claims.",
            current_value=f"${coverage_limit:,.0f}",
            recommended_value=f"${building_value:,.0f}",
            gap_amount=building_value - coverage_limit
        )
    elif coverage_ratio < 0.90:
        return Gap(
            gap_type="underinsurance",
            severity="warning",
            title=f"Below recommended coverage - {coverage_ratio:.0%}",
            description=f"Coverage is {coverage_ratio:.0%} of value. "
                       f"Consider increasing to 100% for full protection.",
            current_value=f"${coverage_limit:,.0f}",
            recommended_value=f"${building_value:,.0f}",
            gap_amount=building_value - coverage_limit
        )
    return None
```

**Thresholds:**
| Coverage Ratio | Severity | Action |
|----------------|----------|--------|
| < 80% | Critical | Immediate action required |
| 80-90% | Warning | Recommend increase at renewal |
| ≥ 90% | OK | No gap |

---

### 2. High Deductible Gap

**Description:** Deductible is higher than recommended, increasing out-of-pocket exposure.

**Industry Standard:**
- [Fannie Mae](https://mfguide.fanniemae.com/) max is 5% of TIV
- Industry best practice is 2-3% for wind/hail
- Flat deductibles over $250K are notable

**Detection Logic:**
```python
def check_high_deductible(property: Property, policy: Policy) -> Optional[Gap]:
    tiv = sum(b.replacement_cost for b in property.buildings)

    # Check percentage deductibles
    if policy.deductible_pct:
        if policy.deductible_pct > 0.05:
            return Gap(
                gap_type="high_deductible",
                severity="critical",
                title=f"Deductible exceeds 5% ({policy.deductible_pct:.0%})",
                description=f"Your {policy.deductible_pct:.0%} deductible "
                           f"(${tiv * policy.deductible_pct:,.0f}) exceeds the "
                           f"maximum 5% allowed by most lenders.",
                current_value=f"{policy.deductible_pct:.0%} (${tiv * policy.deductible_pct:,.0f})",
                recommended_value="≤ 5%"
            )
        elif policy.deductible_pct > 0.03:
            return Gap(
                gap_type="high_deductible",
                severity="warning",
                title=f"Elevated deductible ({policy.deductible_pct:.0%})",
                description=f"Your deductible is above the recommended 2-3% range."
            )

    # Check flat deductibles
    if policy.deductible and policy.deductible > 250000:
        return Gap(
            gap_type="high_deductible",
            severity="warning",
            title=f"High flat deductible (${policy.deductible:,.0f})",
            description=f"Consider the out-of-pocket exposure from this deductible."
        )

    return None
```

**Thresholds:**
| Deductible | Severity | Rationale |
|------------|----------|-----------|
| > 5% of TIV | Critical | Exceeds Fannie Mae maximum |
| 3-5% of TIV | Warning | Above best practice range |
| > $250,000 flat | Warning | Large out-of-pocket exposure |
| ≤ 3% of TIV | OK | Within normal range |

---

### 3. Expiration Gap

**Description:** Policy is expiring soon and renewal should be in progress.

**Industry Standard:**
- [Insurance brokers](https://www.useindio.com/) recommend starting 120-160 days before
- 60-90 days is minimum recommended
- 30 days or less is critical

**Detection Logic:**
```python
from datetime import date, timedelta

def check_expiration(policy: Policy) -> Optional[Gap]:
    days_until = (policy.expiration_date - date.today()).days

    if days_until <= 0:
        return Gap(
            gap_type="expired",
            severity="critical",
            title="Policy has expired",
            description=f"This policy expired on {policy.expiration_date}. "
                       f"You may have a coverage gap."
        )
    elif days_until <= 30:
        return Gap(
            gap_type="expiring",
            severity="critical",
            title=f"Policy expires in {days_until} days",
            description=f"Renewal must be completed immediately to avoid coverage gap."
        )
    elif days_until <= 60:
        return Gap(
            gap_type="expiring",
            severity="warning",
            title=f"Policy expires in {days_until} days",
            description=f"Renewal process should be in progress. "
                       f"Contact your broker if not already started."
        )
    elif days_until <= 90:
        return Gap(
            gap_type="expiring",
            severity="info",
            title=f"Policy expires in {days_until} days",
            description=f"Plan to begin renewal process soon."
        )

    return None
```

**Thresholds:**
| Days Until Expiration | Severity | Action |
|----------------------|----------|--------|
| ≤ 0 (expired) | Critical | Immediate action - potential gap! |
| 1-30 days | Critical | Complete renewal immediately |
| 31-60 days | Warning | Ensure renewal in progress |
| 61-90 days | Info | Plan for renewal |
| > 90 days | OK | No gap |

---

### 4. Missing Coverage Gap

**Description:** Expected coverage type is not present for the property.

**Industry Standard:**
- Property + GL are required for all commercial real estate
- Umbrella recommended for properties > $5M TIV
- Flood required in FEMA zones A, V, AE, VE

**Detection Logic:**
```python
REQUIRED_COVERAGES = ["property", "general_liability"]
RECOMMENDED_COVERAGES_TIV_THRESHOLD = 5_000_000

def check_missing_coverage(property: Property, policies: List[Policy]) -> List[Gap]:
    gaps = []
    tiv = sum(b.replacement_cost for b in property.buildings)
    coverage_types = {p.policy_type for p in policies if p.status == "active"}

    # Check required coverages
    for required in REQUIRED_COVERAGES:
        if required not in coverage_types:
            gaps.append(Gap(
                gap_type="missing_coverage",
                severity="critical",
                title=f"Missing {required.replace('_', ' ').title()} coverage",
                description=f"All commercial properties should have {required} coverage.",
                coverage_name=required
            ))

    # Check umbrella for large properties
    if tiv > RECOMMENDED_COVERAGES_TIV_THRESHOLD:
        if "umbrella" not in coverage_types:
            gaps.append(Gap(
                gap_type="missing_coverage",
                severity="warning",
                title="Missing umbrella coverage",
                description=f"Properties with TIV over $5M typically have umbrella coverage "
                           f"for additional liability protection.",
                coverage_name="umbrella"
            ))

    return gaps
```

---

### 5. Missing Flood Coverage Gap

**Description:** Property is in a flood zone but lacks flood coverage.

**Industry Standard:**
- Required in FEMA zones A, V, AE, VE by most lenders
- NFIP or private flood policies accepted

**Detection Logic:**
```python
HIGH_RISK_FLOOD_ZONES = ["A", "AE", "AH", "AO", "AR", "V", "VE"]

def check_missing_flood(property: Property, policies: List[Policy]) -> Optional[Gap]:
    if property.flood_zone not in HIGH_RISK_FLOOD_ZONES:
        return None

    has_flood = any(
        p.policy_type == "flood" or
        any(c.coverage_type == "flood" for c in p.coverages)
        for p in policies if p.status == "active"
    )

    if not has_flood:
        return Gap(
            gap_type="missing_flood",
            severity="critical",
            title=f"No flood coverage in Zone {property.flood_zone}",
            description=f"Property is in FEMA flood zone {property.flood_zone} but has no "
                       f"flood insurance. This is typically required by lenders.",
            coverage_name="flood"
        )

    return None
```

---

### 6. Outdated Valuation Gap

**Description:** Building valuation is stale and may not reflect current replacement costs.

**Industry Standard:**
- Valuations should be updated every 2-3 years
- Construction costs have risen significantly

**Detection Logic:**
```python
from datetime import date
from dateutil.relativedelta import relativedelta

def check_outdated_valuation(property: Property) -> Optional[Gap]:
    if not property.last_valuation_date:
        return Gap(
            gap_type="outdated_valuation",
            severity="info",
            title="No recorded valuation date",
            description="Consider getting a property valuation to ensure adequate coverage."
        )

    years_since = relativedelta(date.today(), property.last_valuation_date).years

    if years_since >= 3:
        return Gap(
            gap_type="outdated_valuation",
            severity="warning",
            title=f"Valuation is {years_since} years old",
            description=f"Last valuation was {property.last_valuation_date}. "
                       f"Consider updating to ensure adequate coverage."
        )
    elif years_since >= 2:
        return Gap(
            gap_type="outdated_valuation",
            severity="info",
            title=f"Valuation is {years_since} years old",
            description="Plan to update valuation within the next year."
        )

    return None
```

---

## API Endpoints

### Trigger Gap Detection

#### `POST /v1/gaps/detect`

Manually trigger gap detection for one or all properties.

**Request Body:**
```json
{
  "property_id": "uuid",  // Optional - null for all properties
  "force_refresh": false  // Re-run even if recently run
}
```

**Response:**
```json
{
  "detection_run_id": "uuid",
  "properties_analyzed": 7,
  "gaps_found": 5,
  "gaps_created": 3,
  "gaps_resolved": 2,
  "duration_ms": 1250
}
```

---

### List Gaps

#### `GET /v1/gaps`

Returns paginated list of coverage gaps.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | open | Filter: open, acknowledged, resolved, all |
| `severity` | string | No | all | Filter: critical, warning, info |
| `gap_type` | string | No | all | Filter by gap type |
| `property_id` | UUID | No | - | Filter by property |
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 20 | Items per page |

**Response:**
```json
{
  "gaps": [
    {
      "id": "uuid",
      "property_id": "uuid",
      "property_name": "Buffalo Run",
      "policy_id": "uuid",
      "policy_number": "PRO-2024-001234",
      "gap_type": "underinsurance",
      "severity": "critical",
      "title": "Underinsured - Coverage at 75%",
      "description": "Building coverage is only 75% of replacement cost...",
      "coverage_name": null,
      "current_value": "$27,000,000",
      "recommended_value": "$36,000,000",
      "gap_amount": 9000000.00,
      "status": "open",
      "detected_at": "2025-01-10T14:30:00Z",
      "detection_method": "automatic"
    }
  ],
  "summary": {
    "total_open": 5,
    "critical": 2,
    "warning": 2,
    "info": 1
  },
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 5,
    "total_pages": 1
  }
}
```

---

### Get Gap Detail

#### `GET /v1/gaps/{id}`

Returns detailed gap information.

**Response:**
```json
{
  "id": "uuid",
  "property": {
    "id": "uuid",
    "name": "Buffalo Run",
    "address": "123 Buffalo Way, Houston TX"
  },
  "policy": {
    "id": "uuid",
    "policy_number": "PRO-2024-001234",
    "policy_type": "property",
    "carrier_name": "Zurich"
  },
  "gap_type": "underinsurance",
  "severity": "critical",
  "title": "Underinsured - Coverage at 75%",
  "description": "Building coverage is only 75% of replacement cost. This may trigger coinsurance penalties on claims.",
  "current_value": "$27,000,000",
  "recommended_value": "$36,000,000",
  "gap_amount": 9000000.00,
  "status": "open",
  "detected_at": "2025-01-10T14:30:00Z",
  "detection_method": "automatic",
  "resolved_at": null,
  "resolved_by": null,
  "resolution_notes": null,
  "recommendation": "Contact your broker to increase building coverage to at least 80% of replacement cost before your next renewal.",
  "related_gaps": []
}
```

---

### Acknowledge Gap

#### `POST /v1/gaps/{id}/acknowledge`

Mark a gap as acknowledged (reviewed but not resolved).

**Request Body:**
```json
{
  "notes": "Discussed with broker, will address at renewal"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "acknowledged",
  "acknowledged_at": "2025-01-15T10:00:00Z",
  "acknowledged_by": "user-uuid"
}
```

---

### Resolve Gap

#### `POST /v1/gaps/{id}/resolve`

Mark a gap as resolved.

**Request Body:**
```json
{
  "resolution_notes": "Increased coverage to $36M effective 2025-02-01"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "resolved",
  "resolved_at": "2025-01-15T10:00:00Z",
  "resolved_by": "user-uuid"
}
```

---

## Rules Configuration

Rules can be configured via environment variables or a config file:

```yaml
# gap_detection_config.yaml

underinsurance:
  critical_threshold: 0.80  # < 80% = critical
  warning_threshold: 0.90   # 80-90% = warning
  enabled: true

high_deductible:
  critical_pct: 0.05        # > 5% = critical
  warning_pct: 0.03         # 3-5% = warning
  warning_flat: 250000      # > $250K flat = warning
  enabled: true

expiration:
  critical_days: 30
  warning_days: 60
  info_days: 90
  enabled: true

missing_coverage:
  required:
    - property
    - general_liability
  recommended_tiv_threshold: 5000000
  recommended:
    - umbrella
  enabled: true

missing_flood:
  high_risk_zones:
    - A
    - AE
    - AH
    - AO
    - AR
    - V
    - VE
  enabled: true

outdated_valuation:
  warning_years: 3
  info_years: 2
  enabled: true
```

---

## Implementation

### Service Structure

```python
# app/services/gap_detection/service.py

class GapDetectionService:
    def __init__(
        self,
        property_repo: PropertyRepository,
        policy_repo: PolicyRepository,
        gap_repo: GapRepository,
        config: GapDetectionConfig
    ):
        self.property_repo = property_repo
        self.policy_repo = policy_repo
        self.gap_repo = gap_repo
        self.config = config

        # Initialize rules
        self.rules = [
            UnderinsuranceRule(config.underinsurance),
            HighDeductibleRule(config.high_deductible),
            ExpirationRule(config.expiration),
            MissingCoverageRule(config.missing_coverage),
            MissingFloodRule(config.missing_flood),
            OutdatedValuationRule(config.outdated_valuation),
        ]

    async def detect_gaps(
        self,
        property_id: Optional[UUID] = None,
        force_refresh: bool = False
    ) -> GapDetectionResult:
        """Run gap detection for one or all properties."""

        if property_id:
            properties = [await self.property_repo.get(property_id)]
        else:
            properties = await self.property_repo.list_all()

        gaps_found = []
        gaps_created = 0
        gaps_resolved = 0

        for property in properties:
            policies = await self.policy_repo.get_by_property(property.id)

            # Run each rule
            for rule in self.rules:
                if not rule.enabled:
                    continue

                new_gaps = rule.evaluate(property, policies)
                gaps_found.extend(new_gaps)

            # Deduplicate and persist
            for gap in new_gaps:
                existing = await self.gap_repo.find_matching(gap)
                if not existing:
                    await self.gap_repo.create(gap)
                    gaps_created += 1

            # Auto-resolve gaps that no longer apply
            resolved = await self._resolve_stale_gaps(property.id, gaps_found)
            gaps_resolved += resolved

        return GapDetectionResult(
            properties_analyzed=len(properties),
            gaps_found=len(gaps_found),
            gaps_created=gaps_created,
            gaps_resolved=gaps_resolved
        )
```

### Rule Base Class

```python
# app/services/gap_detection/rules/base.py

from abc import ABC, abstractmethod

class GapDetectionRule(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def evaluate(
        self,
        property: Property,
        policies: List[Policy]
    ) -> List[CoverageGap]:
        """Evaluate the rule and return any gaps found."""
        pass

    def create_gap(
        self,
        property_id: UUID,
        gap_type: str,
        severity: str,
        title: str,
        description: str,
        **kwargs
    ) -> CoverageGap:
        return CoverageGap(
            property_id=property_id,
            gap_type=gap_type,
            severity=severity,
            title=title,
            description=description,
            status="open",
            detection_method="automatic",
            detected_at=datetime.utcnow(),
            **kwargs
        )
```

---

## Auto-Detection Triggers

### On Document Ingestion

```python
# In ingestion pipeline
async def on_ingestion_complete(document_id: UUID):
    document = await document_repo.get(document_id)

    if document.property_id:
        # Trigger gap detection for this property
        await gap_detection_service.detect_gaps(
            property_id=document.property_id
        )
```

### On Policy Update

```python
# In policy update endpoint
async def update_policy(policy_id: UUID, updates: PolicyUpdate):
    policy = await policy_repo.update(policy_id, updates)

    # Re-run gap detection
    await gap_detection_service.detect_gaps(
        property_id=policy.property_id
    )
```

---

## Related Documents

- [03-compliance-checking.md](./03-compliance-checking.md) - Lender compliance (uses gap detection)
- [05-insurance-health-score.md](./05-insurance-health-score.md) - Uses gap data in scoring
- [01-dashboard-api.md](./01-dashboard-api.md) - Gap display in dashboard
