# Lender Compliance Checking

## Overview

The Lender Compliance system verifies that insurance coverage meets lender requirements for each property. It compares actual coverage against lender-specific requirements and identifies non-compliance issues.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LENDER COMPLIANCE SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     REQUIREMENT TEMPLATES                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Standard   │  │  Fannie Mae  │  │ Conservative │              │   │
│  │  │   Template   │  │   Template   │  │   Template   │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                         │                                           │   │
│  │                         ▼                                           │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              PROPERTY LENDER REQUIREMENTS                    │   │   │
│  │  │  (Customizable per property based on loan agreement)        │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      COMPLIANCE CHECKS                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Property   │  │      GL      │  │   Umbrella   │              │   │
│  │  │    Limit     │  │    Limit     │  │    Limit     │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  Deductible  │  │    Flood     │  │  Mortgagee   │              │   │
│  │  │    Maximum   │  │   Required   │  │    Listed    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    COMPLIANCE REPORT                                 │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  Status: COMPLIANT / NON-COMPLIANT / NO REQUIREMENTS         │   │   │
│  │  │  Issues: List of specific non-compliance items               │   │   │
│  │  │  Recommendations: How to resolve issues                      │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Requirement Templates

Based on industry standards from [Fannie Mae Multifamily Guide](https://mfguide.fanniemae.com/node/4226) and common lender practices.

### Standard Template

Default requirements for most commercial loans.

```yaml
name: Standard
description: Common requirements for commercial real estate loans

property_coverage:
  type: replacement_cost
  min_percentage: 100  # 100% of replacement cost

general_liability:
  min_per_occurrence: 1000000      # $1,000,000
  min_aggregate: 2000000           # $2,000,000

umbrella:
  required: false
  min_limit: 5000000               # $5,000,000 if required

deductible:
  max_percentage: 5.0              # 5% of TIV max
  max_flat: null                   # No flat max

flood:
  required_zones:
    - A
    - AE
    - AH
    - AO
    - V
    - VE

earthquake:
  required: false

terrorism:
  required: false

additional_requirements:
  mortgagee_listed: true
  policy_current: true
  notice_days: 30                  # 30-day cancellation notice
```

### Fannie Mae Template

Requirements based on [Fannie Mae Multifamily Guide](https://mfguide.fanniemae.com/).

```yaml
name: Fannie Mae
description: Fannie Mae multifamily loan requirements

property_coverage:
  type: replacement_cost
  min_percentage: 100
  settlement_basis: replacement_cost  # ACV not acceptable

general_liability:
  min_per_occurrence: 1000000
  min_aggregate: 2000000
  per_location_aggregate: true

umbrella:
  required: true
  min_limit_by_units:
    - units: 50
      limit: 1000000
    - units: 100
      limit: 2000000
    - units: 200
      limit: 5000000
    - units: 500
      limit: 10000000
    - units: 1000
      limit: 15000000

deductible:
  max_percentage: 5.0
  applies_per_occurrence: true

flood:
  required_zones:
    - A
    - AE
    - AH
    - AO
    - AR
    - V
    - VE
  min_coverage: loan_amount        # At least loan amount

business_income:
  required: true
  min_period_months: 12
  extended_period_days: 90

equipment_breakdown:
  required: true

builders_risk:
  required_for_construction: true

additional_requirements:
  mortgagee_listed: true
  policy_current: true
  replacement_cost_settlement: true
  ordinance_law: true
```

### Conservative Template

Stricter requirements for risk-averse lenders.

```yaml
name: Conservative
description: Stricter requirements for conservative lenders

property_coverage:
  type: replacement_cost
  min_percentage: 100

general_liability:
  min_per_occurrence: 1000000
  min_aggregate: 2000000

umbrella:
  required: true
  min_limit: 10000000              # $10M minimum

deductible:
  max_percentage: 2.0              # Stricter 2% max
  max_flat: 100000                 # $100K max flat

flood:
  required: true                   # Always required
  min_coverage: replacement_cost

earthquake:
  required_regions:
    - CA
    - WA
    - OR
    - AK
    - HI

terrorism:
  required: true
```

---

## Compliance Checks

### 1. Property Coverage Check

```python
def check_property_coverage(
    requirement: LenderRequirement,
    policies: List[Policy],
    property: Property
) -> Optional[ComplianceIssue]:
    property_policy = next(
        (p for p in policies if p.policy_type == "property" and p.status == "active"),
        None
    )

    if not property_policy:
        return ComplianceIssue(
            check_type="property_coverage",
            status="fail",
            message="No active property insurance policy found",
            current_value=None,
            required_value=f"100% of replacement cost"
        )

    replacement_cost = sum(b.replacement_cost for b in property.buildings)
    coverage_limit = property_policy.building_limit or 0

    if requirement.min_property_limit:
        min_required = requirement.min_property_limit
    else:
        min_required = replacement_cost  # 100% of replacement cost

    if coverage_limit < min_required:
        return ComplianceIssue(
            check_type="property_coverage",
            status="fail",
            message=f"Property coverage below required minimum",
            current_value=f"${coverage_limit:,.0f}",
            required_value=f"${min_required:,.0f}",
            gap_amount=min_required - coverage_limit
        )

    return ComplianceIssue(
        check_type="property_coverage",
        status="pass",
        current_value=f"${coverage_limit:,.0f}",
        required_value=f"${min_required:,.0f}"
    )
```

### 2. General Liability Check

```python
def check_gl_coverage(
    requirement: LenderRequirement,
    policies: List[Policy]
) -> Optional[ComplianceIssue]:
    gl_policy = next(
        (p for p in policies if p.policy_type == "general_liability" and p.status == "active"),
        None
    )

    if not gl_policy:
        return ComplianceIssue(
            check_type="general_liability",
            status="fail",
            message="No active general liability policy found",
            required_value=f"${requirement.min_gl_limit:,.0f} per occurrence"
        )

    per_occurrence = gl_policy.per_occurrence_limit or 0
    required = requirement.min_gl_limit or 1_000_000

    if per_occurrence < required:
        return ComplianceIssue(
            check_type="general_liability",
            status="fail",
            message=f"GL coverage below required minimum",
            current_value=f"${per_occurrence:,.0f}",
            required_value=f"${required:,.0f}",
            gap_amount=required - per_occurrence
        )

    return ComplianceIssue(
        check_type="general_liability",
        status="pass",
        current_value=f"${per_occurrence:,.0f}",
        required_value=f"${required:,.0f}"
    )
```

### 3. Umbrella Check

```python
def check_umbrella_coverage(
    requirement: LenderRequirement,
    policies: List[Policy],
    property: Property
) -> Optional[ComplianceIssue]:
    if not requirement.min_umbrella_limit:
        return ComplianceIssue(
            check_type="umbrella",
            status="not_required",
            message="Umbrella coverage not required by lender"
        )

    umbrella_policy = next(
        (p for p in policies if p.policy_type == "umbrella" and p.status == "active"),
        None
    )

    required = requirement.min_umbrella_limit

    if not umbrella_policy:
        return ComplianceIssue(
            check_type="umbrella",
            status="fail",
            message="No active umbrella policy found",
            required_value=f"${required:,.0f}"
        )

    current = umbrella_policy.total_limit or 0

    if current < required:
        return ComplianceIssue(
            check_type="umbrella",
            status="fail",
            message=f"Umbrella coverage below required minimum",
            current_value=f"${current:,.0f}",
            required_value=f"${required:,.0f}",
            gap_amount=required - current
        )

    return ComplianceIssue(
        check_type="umbrella",
        status="pass",
        current_value=f"${current:,.0f}",
        required_value=f"${required:,.0f}"
    )
```

### 4. Deductible Check

```python
def check_deductible(
    requirement: LenderRequirement,
    policies: List[Policy],
    property: Property
) -> Optional[ComplianceIssue]:
    property_policy = next(
        (p for p in policies if p.policy_type == "property" and p.status == "active"),
        None
    )

    if not property_policy:
        return None  # Covered by property coverage check

    tiv = sum(b.replacement_cost for b in property.buildings)

    # Check percentage deductible
    if property_policy.deductible_pct and requirement.max_deductible_pct:
        if property_policy.deductible_pct > requirement.max_deductible_pct:
            deductible_amount = tiv * property_policy.deductible_pct
            max_amount = tiv * requirement.max_deductible_pct
            return ComplianceIssue(
                check_type="deductible",
                status="fail",
                message=f"Deductible exceeds lender maximum",
                current_value=f"{property_policy.deductible_pct:.0%} (${deductible_amount:,.0f})",
                required_value=f"≤ {requirement.max_deductible_pct:.0%} (${max_amount:,.0f})"
            )

    # Check flat deductible
    if property_policy.deductible and requirement.max_deductible_amount:
        if property_policy.deductible > requirement.max_deductible_amount:
            return ComplianceIssue(
                check_type="deductible",
                status="fail",
                message=f"Deductible exceeds lender maximum",
                current_value=f"${property_policy.deductible:,.0f}",
                required_value=f"≤ ${requirement.max_deductible_amount:,.0f}"
            )

    return ComplianceIssue(
        check_type="deductible",
        status="pass",
        message="Deductible within limits"
    )
```

### 5. Flood Coverage Check

```python
HIGH_RISK_ZONES = ["A", "AE", "AH", "AO", "AR", "V", "VE"]

def check_flood_coverage(
    requirement: LenderRequirement,
    policies: List[Policy],
    property: Property
) -> Optional[ComplianceIssue]:
    in_flood_zone = property.flood_zone in HIGH_RISK_ZONES

    if not requirement.requires_flood and not in_flood_zone:
        return ComplianceIssue(
            check_type="flood",
            status="not_required",
            message=f"Flood coverage not required (Zone {property.flood_zone or 'X'})"
        )

    if not requirement.requires_flood and not in_flood_zone:
        return None

    # Check for flood coverage
    has_flood = any(
        p.policy_type == "flood" or
        any(c.coverage_type == "flood" for c in p.coverages)
        for p in policies if p.status == "active"
    )

    if not has_flood and (requirement.requires_flood or in_flood_zone):
        return ComplianceIssue(
            check_type="flood",
            status="fail",
            message=f"Flood coverage required but not found (Zone {property.flood_zone})",
            current_value="None",
            required_value="Flood insurance policy"
        )

    return ComplianceIssue(
        check_type="flood",
        status="pass",
        message="Flood coverage in place"
    )
```

### 6. Mortgagee Listed Check

```python
def check_mortgagee_listed(
    requirement: LenderRequirement,
    policies: List[Policy],
    lender: Lender
) -> Optional[ComplianceIssue]:
    if not lender:
        return ComplianceIssue(
            check_type="mortgagee",
            status="not_required",
            message="No lender associated with property"
        )

    property_policy = next(
        (p for p in policies if p.policy_type == "property" and p.status == "active"),
        None
    )

    if not property_policy:
        return None  # Covered by property coverage check

    # Check if lender is listed as additional insured / mortgagee
    mortgagees = property_policy.additional_insureds or []
    lender_listed = any(
        lender.name.lower() in m.get("name", "").lower()
        for m in mortgagees
    )

    if not lender_listed:
        return ComplianceIssue(
            check_type="mortgagee",
            status="fail",
            message=f"Lender not listed as mortgagee on policy",
            current_value="Not listed",
            required_value=f"{lender.name} listed as mortgagee"
        )

    return ComplianceIssue(
        check_type="mortgagee",
        status="pass",
        message=f"{lender.name} listed as mortgagee"
    )
```

### 7. Policy Currency Check

```python
def check_policy_current(policies: List[Policy]) -> Optional[ComplianceIssue]:
    today = date.today()

    for policy in policies:
        if policy.status == "active" and policy.expiration_date:
            if policy.expiration_date < today:
                return ComplianceIssue(
                    check_type="policy_current",
                    status="fail",
                    message=f"{policy.policy_type} policy has expired",
                    current_value=f"Expired {policy.expiration_date}",
                    required_value="Active, unexpired policy"
                )

    return ComplianceIssue(
        check_type="policy_current",
        status="pass",
        message="All policies are current"
    )
```

---

## API Endpoints

### Get Compliance Status

#### `GET /v1/properties/{id}/compliance`

Returns compliance status for a property.

**Response:**
```json
{
  "property_id": "uuid",
  "property_name": "Buffalo Run",
  "lender": {
    "id": "uuid",
    "name": "Wells Fargo",
    "loan_number": "123456789"
  },
  "overall_status": "non_compliant",
  "checks": [
    {
      "check_type": "property_coverage",
      "status": "pass",
      "message": null,
      "current_value": "$35,989,980",
      "required_value": "$35,989,980"
    },
    {
      "check_type": "general_liability",
      "status": "pass",
      "current_value": "$1,000,000",
      "required_value": "$1,000,000"
    },
    {
      "check_type": "umbrella",
      "status": "pass",
      "current_value": "$10,000,000",
      "required_value": "$5,000,000"
    },
    {
      "check_type": "deductible",
      "status": "fail",
      "message": "Deductible exceeds lender maximum",
      "current_value": "5% ($1,799,499)",
      "required_value": "≤ 2% ($719,800)"
    },
    {
      "check_type": "flood",
      "status": "not_required",
      "message": "Flood coverage not required (Zone X)"
    },
    {
      "check_type": "mortgagee",
      "status": "pass",
      "message": "Wells Fargo listed as mortgagee"
    },
    {
      "check_type": "policy_current",
      "status": "pass",
      "message": "All policies are current"
    }
  ],
  "issues_count": 1,
  "last_checked_at": "2025-01-15T10:00:00Z"
}
```

**Status Values:**
| Status | Description |
|--------|-------------|
| `compliant` | All checks pass |
| `non_compliant` | One or more checks fail |
| `no_requirements` | No lender requirements configured |

---

### List Lender Requirements

#### `GET /v1/properties/{id}/lender-requirements`

Returns lender requirements for a property.

**Response:**
```json
{
  "property_id": "uuid",
  "lender": {
    "id": "uuid",
    "name": "Wells Fargo"
  },
  "loan_number": "123456789",
  "loan_amount": 25000000.00,
  "maturity_date": "2030-06-15",
  "requirements": {
    "min_property_limit": 35989980.00,
    "min_gl_limit": 1000000.00,
    "min_umbrella_limit": 5000000.00,
    "max_deductible_pct": 0.02,
    "max_deductible_amount": null,
    "requires_flood": false,
    "requires_earthquake": false,
    "requires_terrorism": false,
    "additional_requirements": "30-day notice of cancellation required"
  },
  "template_used": "Fannie Mae",
  "created_at": "2024-06-15T10:00:00Z",
  "updated_at": "2024-06-15T10:00:00Z"
}
```

---

### Create/Update Lender Requirements

#### `PUT /v1/properties/{id}/lender-requirements`

Create or update lender requirements.

**Request Body:**
```json
{
  "lender_id": "uuid",
  "loan_number": "123456789",
  "loan_amount": 25000000.00,
  "maturity_date": "2030-06-15",
  "template": "fannie_mae",
  "overrides": {
    "max_deductible_pct": 0.02
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "property_id": "uuid",
  "message": "Lender requirements updated successfully"
}
```

---

### List Requirement Templates

#### `GET /v1/compliance/templates`

Returns available requirement templates.

**Response:**
```json
{
  "templates": [
    {
      "id": "standard",
      "name": "Standard",
      "description": "Common requirements for commercial real estate loans",
      "requirements": {
        "min_property_limit": null,
        "min_gl_limit": 1000000,
        "min_umbrella_limit": null,
        "max_deductible_pct": 0.05,
        "requires_flood_in_zones": ["A", "AE", "V", "VE"]
      }
    },
    {
      "id": "fannie_mae",
      "name": "Fannie Mae",
      "description": "Fannie Mae multifamily loan requirements",
      "requirements": {
        "min_property_limit": null,
        "min_gl_limit": 1000000,
        "min_umbrella_limit": 5000000,
        "max_deductible_pct": 0.05,
        "requires_business_income": true,
        "business_income_months": 12
      }
    },
    {
      "id": "conservative",
      "name": "Conservative",
      "description": "Stricter requirements for conservative lenders",
      "requirements": {
        "min_property_limit": null,
        "min_gl_limit": 1000000,
        "min_umbrella_limit": 10000000,
        "max_deductible_pct": 0.02,
        "requires_flood": true,
        "requires_terrorism": true
      }
    }
  ]
}
```

---

### Run Compliance Check

#### `POST /v1/properties/{id}/compliance/check`

Manually trigger compliance check.

**Response:**
```json
{
  "property_id": "uuid",
  "overall_status": "non_compliant",
  "issues_count": 1,
  "checked_at": "2025-01-15T10:00:00Z"
}
```

---

## Implementation

### Compliance Service

```python
# app/services/compliance/service.py

class ComplianceService:
    def __init__(
        self,
        property_repo: PropertyRepository,
        policy_repo: PolicyRepository,
        requirement_repo: LenderRequirementRepository,
        lender_repo: LenderRepository
    ):
        self.property_repo = property_repo
        self.policy_repo = policy_repo
        self.requirement_repo = requirement_repo
        self.lender_repo = lender_repo

        self.checks = [
            PropertyCoverageCheck(),
            GeneralLiabilityCheck(),
            UmbrellaCheck(),
            DeductibleCheck(),
            FloodCheck(),
            MortgageeCheck(),
            PolicyCurrentCheck(),
        ]

    async def check_compliance(
        self,
        property_id: UUID
    ) -> ComplianceResult:
        """Run all compliance checks for a property."""

        property = await self.property_repo.get(property_id)
        requirement = await self.requirement_repo.get_by_property(property_id)

        if not requirement:
            return ComplianceResult(
                property_id=property_id,
                overall_status="no_requirements",
                checks=[],
                issues_count=0
            )

        policies = await self.policy_repo.get_by_property(property_id)
        lender = await self.lender_repo.get(requirement.lender_id) if requirement.lender_id else None

        results = []
        for check in self.checks:
            result = check.evaluate(
                requirement=requirement,
                policies=policies,
                property=property,
                lender=lender
            )
            if result:
                results.append(result)

        failed_count = sum(1 for r in results if r.status == "fail")
        overall_status = "compliant" if failed_count == 0 else "non_compliant"

        # Update stored compliance status
        await self.requirement_repo.update_compliance_status(
            property_id=property_id,
            status=overall_status,
            issues=[r.to_dict() for r in results if r.status == "fail"]
        )

        return ComplianceResult(
            property_id=property_id,
            overall_status=overall_status,
            checks=results,
            issues_count=failed_count
        )
```

---

## Integration with Gap Detection

Compliance failures also create coverage gaps:

```python
async def on_compliance_check_complete(result: ComplianceResult):
    """Create coverage gaps for compliance failures."""

    if result.overall_status == "non_compliant":
        for check in result.checks:
            if check.status == "fail":
                await gap_service.create_gap(
                    property_id=result.property_id,
                    gap_type="non_compliant",
                    severity="critical",
                    title=f"Lender Compliance: {check.check_type}",
                    description=check.message,
                    current_value=check.current_value,
                    recommended_value=check.required_value
                )
```

---

## Related Documents

- [02-gap-detection.md](./02-gap-detection.md) - Gap detection (creates gaps for non-compliance)
- [05-insurance-health-score.md](./05-insurance-health-score.md) - Compliance affects health score
- [01-dashboard-api.md](./01-dashboard-api.md) - Compliance summary in dashboard
