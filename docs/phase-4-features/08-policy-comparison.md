# Policy Comparison (Year-over-Year)

## Overview

The Policy Comparison feature automatically detects changes between policy periods. It identifies coverage changes, limit adjustments, new exclusions, and premium changes - catching "silent" coverage reductions that might otherwise go unnoticed.

**This is an innovation that doesn't exist in the market today.**

---

## Why This Matters

### Current State (What Exists)
- Manual PDF comparison (time-consuming, error-prone)
- Broker summaries at renewal (often incomplete)
- No historical tracking of coverage evolution

### The Gap
Property owners currently:
- Don't notice subtle coverage reductions
- Can't track how their coverage has changed over time
- Miss new exclusions added at renewal
- Don't understand if premium increases are justified by coverage changes

### Our Innovation
Automatic detection of:
1. **Coverage Changes** - Limits increased/decreased
2. **New Exclusions** - What's no longer covered
3. **Term Changes** - Deductibles, waiting periods, etc.
4. **Premium Analysis** - Cost vs coverage change correlation
5. **Silent Reductions** - Premium up but coverage down

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      POLICY COMPARISON ENGINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     POLICY VERSIONS                                  │   │
│  │  ┌──────────────┐          ┌──────────────┐                         │   │
│  │  │   Previous   │   vs     │   Current    │                         │   │
│  │  │   Period     │  ────>   │   Period     │                         │   │
│  │  │  2023-2024   │          │  2024-2025   │                         │   │
│  │  └──────────────┘          └──────────────┘                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    COMPARISON ENGINE                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Limit      │  │  Exclusion   │  │    Term      │              │   │
│  │  │  Comparison  │  │  Detection   │  │  Comparison  │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Premium    │  │  Coverage    │  │   Entity     │              │   │
│  │  │   Analysis   │  │  Type Diff   │  │   Changes    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    COMPARISON REPORT                                 │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  Coverage Changes | New Exclusions | Premium Analysis        │   │   │
│  │  │  Alerts for silent reductions | Historical trends            │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Comparison Categories

### 1. Limit Changes

```json
{
  "category": "limit_changes",
  "changes": [
    {
      "coverage_type": "building",
      "previous_limit": 35000000,
      "current_limit": 38500000,
      "change_amount": 3500000,
      "change_pct": 10.0,
      "direction": "increased",
      "severity": "info",
      "note": "Building limit increased, likely inflation adjustment"
    },
    {
      "coverage_type": "flood_sublimit",
      "previous_limit": 500000,
      "current_limit": 0,
      "change_amount": -500000,
      "change_pct": -100.0,
      "direction": "removed",
      "severity": "critical",
      "note": "Flood sublimit was REMOVED entirely"
    },
    {
      "coverage_type": "business_income",
      "previous_limit": 2000000,
      "current_limit": 1000000,
      "change_amount": -1000000,
      "change_pct": -50.0,
      "direction": "decreased",
      "severity": "warning",
      "note": "Business income limit reduced by 50%"
    }
  ]
}
```

### 2. Deductible Changes

```json
{
  "category": "deductible_changes",
  "changes": [
    {
      "coverage_type": "property",
      "previous_deductible": 10000,
      "current_deductible": 25000,
      "change_amount": 15000,
      "change_pct": 150.0,
      "direction": "increased",
      "severity": "warning",
      "note": "Property deductible increased significantly"
    },
    {
      "coverage_type": "wind_hail",
      "previous_deductible": "2%",
      "current_deductible": "5%",
      "change_amount": "3%",
      "direction": "increased",
      "severity": "critical",
      "note": "Wind deductible now 5% - may exceed lender limits"
    }
  ]
}
```

### 3. New Exclusions

```json
{
  "category": "exclusions_added",
  "changes": [
    {
      "exclusion_name": "Communicable Disease Exclusion",
      "description": "Excludes losses arising from communicable diseases including pandemics",
      "severity": "warning",
      "common_since": "2020",
      "note": "Standard post-COVID exclusion, most policies now include this"
    },
    {
      "exclusion_name": "Cyber Event Exclusion",
      "description": "Excludes physical damage arising from cyber attacks",
      "severity": "warning",
      "note": "Consider standalone cyber policy if not already in place"
    },
    {
      "exclusion_name": "PFAS/Forever Chemicals Exclusion",
      "description": "Excludes claims related to PFAS contamination",
      "severity": "info",
      "note": "Increasingly common in commercial property policies"
    }
  ]
}
```

### 4. Coverage Terms Changed

```json
{
  "category": "term_changes",
  "changes": [
    {
      "term_name": "business_income_period",
      "previous_value": "12 months",
      "current_value": "6 months",
      "severity": "warning",
      "note": "Business income period reduced by half"
    },
    {
      "term_name": "extended_period_of_indemnity",
      "previous_value": "180 days",
      "current_value": "90 days",
      "severity": "info",
      "note": "Extended period reduced"
    },
    {
      "term_name": "ordinance_law",
      "previous_value": "Not included",
      "current_value": "25% of building limit",
      "severity": "positive",
      "note": "Ordinance/law coverage ADDED - this is an improvement"
    }
  ]
}
```

### 5. Premium Analysis

```json
{
  "category": "premium_analysis",
  "previous_premium": 142500,
  "current_premium": 168900,
  "change_amount": 26400,
  "change_pct": 18.5,
  "analysis": {
    "justified_by_coverage": false,
    "coverage_value_change": 10.0,
    "premium_vs_coverage_ratio": 1.85,
    "alert": "Premium increased 18.5% but coverage value only increased 10%"
  },
  "breakdown": [
    {
      "factor": "Building limit increase",
      "estimated_impact": "+$9,500 (10%)"
    },
    {
      "factor": "Market rate increases",
      "estimated_impact": "+$14,250 (10%)"
    },
    {
      "factor": "Loss experience",
      "estimated_impact": "-$2,850 (favorable)"
    }
  ],
  "silent_reduction_alert": {
    "detected": true,
    "message": "Your premium increased 18.5% but flood sublimit was REMOVED. This represents a significant coverage reduction despite higher cost.",
    "severity": "critical"
  }
}
```

---

## Detection Logic

### Limit Comparison

```python
def compare_limits(
    previous_policy: Policy,
    current_policy: Policy
) -> List[LimitChange]:
    """Compare coverage limits between policy periods."""

    changes = []

    # Map coverages by type for comparison
    prev_coverages = {c.coverage_type: c for c in previous_policy.coverages}
    curr_coverages = {c.coverage_type: c for c in current_policy.coverages}

    # Check for changed/removed coverages
    for coverage_type, prev in prev_coverages.items():
        if coverage_type in curr_coverages:
            curr = curr_coverages[coverage_type]
            if prev.limit != curr.limit:
                change_pct = ((curr.limit - prev.limit) / prev.limit * 100) if prev.limit else 0

                changes.append(LimitChange(
                    coverage_type=coverage_type,
                    previous_limit=prev.limit,
                    current_limit=curr.limit,
                    change_amount=curr.limit - prev.limit,
                    change_pct=change_pct,
                    direction="increased" if change_pct > 0 else "decreased",
                    severity=categorize_limit_change_severity(coverage_type, change_pct)
                ))
        else:
            # Coverage removed entirely
            changes.append(LimitChange(
                coverage_type=coverage_type,
                previous_limit=prev.limit,
                current_limit=0,
                change_amount=-prev.limit,
                change_pct=-100,
                direction="removed",
                severity="critical"
            ))

    # Check for new coverages
    for coverage_type, curr in curr_coverages.items():
        if coverage_type not in prev_coverages:
            changes.append(LimitChange(
                coverage_type=coverage_type,
                previous_limit=0,
                current_limit=curr.limit,
                change_amount=curr.limit,
                change_pct=100,
                direction="added",
                severity="positive"
            ))

    return changes


def categorize_limit_change_severity(
    coverage_type: str,
    change_pct: float
) -> str:
    """Determine severity of a limit change."""

    critical_coverages = ["building", "flood", "business_income", "liability"]

    if change_pct <= -50:
        return "critical"
    elif change_pct <= -25:
        return "warning" if coverage_type in critical_coverages else "info"
    elif change_pct < 0:
        return "info"
    else:
        return "positive" if change_pct > 0 else "none"
```

### Exclusion Detection (AI-Powered)

```python
async def detect_new_exclusions(
    previous_policy: Policy,
    current_policy: Policy,
    rag_service: RAGQueryService
) -> List[ExclusionChange]:
    """Use AI to detect new exclusions."""

    # Query RAG for exclusions from each policy
    prev_exclusions = await rag_service.query(
        f"List all exclusions from policy {previous_policy.policy_number}",
        filter_document_id=previous_policy.source_document_id
    )

    curr_exclusions = await rag_service.query(
        f"List all exclusions from policy {current_policy.policy_number}",
        filter_document_id=current_policy.source_document_id
    )

    # Use LLM to compare and identify new exclusions
    prompt = f"""
    Compare these two lists of policy exclusions and identify:
    1. Exclusions that are NEW in the current policy
    2. Exclusions that were REMOVED from the previous policy
    3. Exclusions that were MODIFIED

    PREVIOUS POLICY EXCLUSIONS:
    {prev_exclusions.answer}

    CURRENT POLICY EXCLUSIONS:
    {curr_exclusions.answer}

    For each new or modified exclusion, explain:
    - What it means for the policyholder
    - How common this exclusion is in the industry
    - Severity (critical, warning, info)

    Return as JSON array.
    """

    response = await llm_client.generate(
        prompt=prompt,
        model="gemini-2.5-flash",
        response_format="json"
    )

    return [ExclusionChange(**e) for e in response.exclusions]
```

### Silent Reduction Detection

```python
def detect_silent_reductions(
    comparison: PolicyComparison
) -> Optional[SilentReductionAlert]:
    """Detect when premium increases despite coverage reductions."""

    premium_change_pct = comparison.premium_analysis.change_pct

    # Calculate effective coverage change
    coverage_reductions = [
        c for c in comparison.limit_changes
        if c.direction in ["decreased", "removed"]
    ]

    coverage_increases = [
        c for c in comparison.limit_changes
        if c.direction in ["increased", "added"]
    ]

    # Calculate net coverage change
    total_reduction = sum(abs(c.change_amount) for c in coverage_reductions)
    total_increase = sum(c.change_amount for c in coverage_increases)
    net_change = total_increase - total_reduction

    # Check for silent reduction
    if premium_change_pct > 0 and net_change < 0:
        # Premium went up but coverage went down
        return SilentReductionAlert(
            detected=True,
            premium_change_pct=premium_change_pct,
            coverage_change_amount=net_change,
            message=f"Premium increased {premium_change_pct:.1f}% but net coverage "
                   f"DECREASED by ${abs(net_change):,.0f}. Review changes carefully.",
            severity="critical",
            key_reductions=[c.coverage_type for c in coverage_reductions]
        )

    # Check for exclusions added with premium increase
    if premium_change_pct > 5 and len(comparison.exclusions_added) > 0:
        return SilentReductionAlert(
            detected=True,
            premium_change_pct=premium_change_pct,
            message=f"Premium increased {premium_change_pct:.1f}% but "
                   f"{len(comparison.exclusions_added)} new exclusions were added.",
            severity="warning",
            key_reductions=[e.exclusion_name for e in comparison.exclusions_added]
        )

    return None
```

---

## API Endpoints

### Get Policy Comparison

#### `GET /v1/policies/{id}/comparison`

Compare current policy to previous period.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `compare_to` | UUID | - | Specific previous policy ID |
| `periods_back` | integer | 1 | How many periods to compare |

**Response:**
```json
{
  "current_policy": {
    "id": "uuid",
    "policy_number": "PRO-2024-001234",
    "effective_date": "2024-04-15",
    "expiration_date": "2025-04-15",
    "annual_premium": 168900
  },
  "previous_policy": {
    "id": "uuid",
    "policy_number": "PRO-2023-001234",
    "effective_date": "2023-04-15",
    "expiration_date": "2024-04-15",
    "annual_premium": 142500
  },
  "summary": {
    "total_changes": 8,
    "critical_changes": 2,
    "warning_changes": 3,
    "positive_changes": 1,
    "premium_change_pct": 18.5,
    "silent_reduction_detected": true
  },
  "limit_changes": [ ... ],
  "deductible_changes": [ ... ],
  "exclusions_added": [ ... ],
  "exclusions_removed": [ ... ],
  "term_changes": [ ... ],
  "premium_analysis": { ... },
  "silent_reduction_alert": {
    "detected": true,
    "severity": "critical",
    "message": "Premium increased 18.5% but flood sublimit was REMOVED..."
  },
  "comparison_date": "2025-01-15T10:00:00Z"
}
```

---

### Get Historical Comparison

#### `GET /v1/properties/{id}/policy-history`

Get historical policy comparison across multiple years.

**Response:**
```json
{
  "property_id": "uuid",
  "property_name": "Buffalo Run",
  "policy_type": "property",
  "history": [
    {
      "period": "2024-2025",
      "policy_id": "uuid",
      "premium": 168900,
      "building_limit": 38500000,
      "deductible": 25000,
      "key_changes": ["Flood sublimit removed", "Premium +18.5%"]
    },
    {
      "period": "2023-2024",
      "policy_id": "uuid",
      "premium": 142500,
      "building_limit": 35000000,
      "deductible": 10000,
      "key_changes": ["Building limit +5%", "Deductible increased"]
    },
    {
      "period": "2022-2023",
      "policy_id": "uuid",
      "premium": 128000,
      "building_limit": 33333333,
      "deductible": 10000,
      "key_changes": ["New policy"]
    }
  ],
  "trends": {
    "3_year_premium_change": 31.9,
    "3_year_limit_change": 15.5,
    "avg_annual_premium_increase": 10.6,
    "coverage_trend": "decreasing",
    "premium_trend": "increasing"
  }
}
```

---

### Compare Any Two Policies

#### `POST /v1/policies/compare`

Compare any two policies (not just sequential).

**Request Body:**
```json
{
  "policy_a_id": "uuid",
  "policy_b_id": "uuid"
}
```

**Response:** Same as single comparison

---

## Auto-Comparison Triggers

### On New Policy Ingestion

```python
@on_event("policy.created")
async def compare_on_new_policy(event):
    """Auto-compare when a new policy is ingested."""

    new_policy = await policy_repo.get(event.policy_id)

    # Find previous policy of same type
    previous = await policy_repo.find_previous(
        property_id=new_policy.property_id,
        policy_type=new_policy.policy_type,
        before_date=new_policy.effective_date
    )

    if previous:
        comparison = await comparison_service.compare_policies(
            previous_policy_id=previous.id,
            current_policy_id=new_policy.id
        )

        # Alert if critical changes detected
        if comparison.summary.critical_changes > 0:
            await notify_user(
                property_id=new_policy.property_id,
                title="Critical policy changes detected",
                message=f"Your new {new_policy.policy_type} policy has "
                       f"{comparison.summary.critical_changes} critical changes "
                       f"from the previous period.",
                severity="critical"
            )
```

---

## Storage

### Policy Version Tracking

```sql
CREATE TABLE policy_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    current_policy_id UUID NOT NULL REFERENCES policies(id),
    previous_policy_id UUID NOT NULL REFERENCES policies(id),
    comparison_data JSONB NOT NULL,
    summary JSONB NOT NULL,
    silent_reduction_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_policy_comparisons_current
ON policy_comparisons(current_policy_id);

CREATE INDEX idx_policy_comparisons_silent_reduction
ON policy_comparisons(silent_reduction_detected) WHERE silent_reduction_detected = TRUE;
```

---

## Related Documents

- [07-coverage-conflicts.md](./07-coverage-conflicts.md) - Cross-policy conflicts
- [06-renewal-intelligence.md](./06-renewal-intelligence.md) - Uses comparison for renewal prep
- [02-gap-detection.md](./02-gap-detection.md) - Gap detection for current policy
