# Coverage Conflict Detection

## Overview

The Coverage Conflict Detection system uses AI to identify conflicts, overlaps, and gaps **between** policies. Unlike gap detection (which checks if coverage exists), conflict detection analyzes how multiple policies interact with each other.

**This is an innovation that doesn't exist in the market today.**

---

## Why This Matters

### Current State (What Exists)
- Manual policy review by brokers/risk managers
- Conflicts often discovered only at claim time
- No automated cross-policy analysis

### The Gap
Property owners currently:
- Don't know if their policies have conflicting terms
- Can't identify coverage overlaps (double-paying for same coverage)
- Miss gaps that appear when policies don't align
- Only discover issues when filing claims

### Our Innovation
AI-powered detection of:
1. **Conflicts** - Policies that contradict each other
2. **Gaps** - Coverage that falls between policies
3. **Overlaps** - Duplicate coverage (wasting premium)
4. **Inconsistencies** - Mismatched terms, entities, or values

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COVERAGE CONFLICT DETECTION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     DATA EXTRACTION LAYER                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Policy     │  │   Coverage   │  │  Exclusion   │              │   │
│  │  │   Terms      │  │    Limits    │  │    Terms     │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  Additional  │  │  Valuation   │  │   Entity     │              │   │
│  │  │  Insureds    │  │   Methods    │  │    Names     │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CONFLICT DETECTION ENGINE                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  Rule-Based  │  │  AI-Powered  │  │  Semantic    │              │   │
│  │  │   Checks     │  │   Analysis   │  │  Similarity  │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CONFLICT TYPES                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  Coverage    │  │  Excess/     │  │   Entity     │              │   │
│  │  │  Conflicts   │  │  Primary Gap │  │  Mismatch    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  Valuation   │  │  Exclusion   │  │   Limit      │              │   │
│  │  │  Conflicts   │  │  Conflicts   │  │  Overlaps    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Conflict Types

### 1. Excess/Primary Gap

**Description:** The umbrella policy doesn't properly attach to underlying coverage.

**Example:**
```
⚠️ EXCESS/PRIMARY GAP DETECTED

Property Policy GL Limit: $1,000,000 per occurrence
Umbrella Policy Underlying Requirement: $2,000,000 per occurrence

ISSUE: Your umbrella requires $2M underlying GL, but you only have $1M.
Claims between $1M and $2M would NOT be covered by either policy.

RECOMMENDATION: Either increase GL to $2M or get umbrella endorsement
to accept $1M underlying.
```

**Detection Logic:**
```python
def check_excess_primary_gap(
    gl_policy: Policy,
    umbrella_policy: Policy
) -> Optional[Conflict]:
    if not umbrella_policy.underlying_requirements:
        return None

    required_gl = umbrella_policy.underlying_requirements.get("general_liability")
    actual_gl = gl_policy.per_occurrence_limit

    if required_gl and actual_gl and actual_gl < required_gl:
        return Conflict(
            conflict_type="excess_primary_gap",
            severity="critical",
            title="Gap between GL and Umbrella coverage",
            description=f"Umbrella requires ${required_gl:,.0f} underlying GL, "
                       f"but you only have ${actual_gl:,.0f}",
            affected_policies=[gl_policy.id, umbrella_policy.id],
            gap_amount=required_gl - actual_gl,
            recommendation="Increase GL limit or modify umbrella requirements"
        )
```

### 2. Entity Name Mismatch

**Description:** Different policies list different named insureds or mortgagees.

**Example:**
```
⚠️ ENTITY NAME MISMATCH

Property Policy Named Insured: "ABC Management LLC"
GL Policy Named Insured: "ABC Management Inc"
Umbrella Policy Named Insured: "ABC Properties LLC"

ISSUE: Entity names don't match across policies.
This could cause claim denials or lender compliance issues.

RECOMMENDATION: Ensure all policies list the same legal entity name.
```

**Detection Logic:**
```python
def check_entity_mismatch(policies: List[Policy]) -> List[Conflict]:
    conflicts = []

    # Group insured names
    insured_names = {}
    for policy in policies:
        if policy.insured_entity:
            name = normalize_entity_name(policy.insured_entity.name)
            if name not in insured_names:
                insured_names[name] = []
            insured_names[name].append(policy)

    if len(insured_names) > 1:
        conflicts.append(Conflict(
            conflict_type="entity_mismatch",
            severity="warning",
            title="Named insured differs across policies",
            description=f"Found {len(insured_names)} different entity names: "
                       f"{', '.join(insured_names.keys())}",
            affected_policies=[p.id for p in policies],
            recommendation="Ensure all policies list the same legal entity"
        ))

    # Check mortgagee names
    mortgagees = {}
    for policy in policies:
        for ai in policy.additional_insureds or []:
            if ai.get("type") == "mortgagee":
                name = normalize_entity_name(ai.get("name", ""))
                if name not in mortgagees:
                    mortgagees[name] = []
                mortgagees[name].append(policy)

    if len(mortgagees) > 1:
        conflicts.append(Conflict(
            conflict_type="mortgagee_mismatch",
            severity="warning",
            title="Mortgagee name differs across policies",
            description=f"Found different mortgagee names: {', '.join(mortgagees.keys())}",
            recommendation="Ensure lender name is consistent across all policies"
        ))

    return conflicts
```

### 3. Valuation Method Conflict

**Description:** Different policies use different valuation methods for the same property.

**Example:**
```
⚠️ VALUATION METHOD CONFLICT

Property Policy (Building A-D): Replacement Cost
Property Policy (Building E): Actual Cash Value

ISSUE: Building E uses ACV, meaning claims will be depreciated.
All other buildings use Replacement Cost.

RECOMMENDATION: Ensure all buildings use Replacement Cost valuation.
```

**Detection Logic:**
```python
def check_valuation_conflicts(
    property: Property,
    policies: List[Policy]
) -> Optional[Conflict]:
    valuation_methods = {}

    for policy in policies:
        if policy.policy_type == "property":
            for coverage in policy.coverages:
                if coverage.coverage_type == "building":
                    method = coverage.valuation_type or policy.valuation_type
                    if method not in valuation_methods:
                        valuation_methods[method] = []
                    valuation_methods[method].append(coverage.description)

    if len(valuation_methods) > 1:
        return Conflict(
            conflict_type="valuation_conflict",
            severity="warning",
            title="Mixed valuation methods",
            description=f"Buildings use different valuation: {valuation_methods}",
            recommendation="Use Replacement Cost for all buildings"
        )
```

### 4. Coverage Overlap (Duplicate Coverage)

**Description:** Same coverage exists on multiple policies (wasting premium).

**Example:**
```
⚠️ COVERAGE OVERLAP DETECTED

Equipment Breakdown coverage found on:
- Property Policy: $1,000,000 limit, $10,000 premium
- Standalone Equipment Breakdown Policy: $500,000 limit, $5,000 premium

ISSUE: You're paying for equipment breakdown coverage twice.
The policies may have different terms about which is primary.

RECOMMENDATION: Remove duplicate coverage from one policy to save ~$5,000.
```

**Detection Logic:**
```python
def check_coverage_overlap(policies: List[Policy]) -> List[Conflict]:
    conflicts = []
    coverage_map = {}

    for policy in policies:
        for coverage in policy.coverages:
            coverage_type = normalize_coverage_type(coverage.coverage_type)
            if coverage_type not in coverage_map:
                coverage_map[coverage_type] = []
            coverage_map[coverage_type].append({
                "policy_id": policy.id,
                "policy_type": policy.policy_type,
                "limit": coverage.limit,
                "premium": coverage.premium
            })

    for coverage_type, occurrences in coverage_map.items():
        if len(occurrences) > 1:
            total_premium = sum(o.get("premium", 0) or 0 for o in occurrences)
            conflicts.append(Conflict(
                conflict_type="coverage_overlap",
                severity="info",
                title=f"Duplicate {coverage_type} coverage",
                description=f"Found {coverage_type} on {len(occurrences)} policies",
                affected_policies=[o["policy_id"] for o in occurrences],
                potential_savings=min(o.get("premium", 0) or 0 for o in occurrences),
                recommendation=f"Consider removing duplicate coverage to save premium"
            ))

    return conflicts
```

### 5. Exclusion Conflict

**Description:** One policy covers what another policy excludes, creating confusion.

**Example:**
```
⚠️ EXCLUSION CONFLICT

Property Policy: Covers water damage from burst pipes up to $50,000
Umbrella Policy: EXCLUDES all water damage

ISSUE: If a pipe bursts and causes $100,000 damage:
- Property pays first $50,000
- Umbrella does NOT cover excess due to water exclusion
- You're uninsured for $50,000

RECOMMENDATION: Get water damage coverage added to umbrella,
or increase property sublimit.
```

**Detection Logic:**
```python
async def check_exclusion_conflicts(
    policies: List[Policy],
    rag_service: RAGQueryService
) -> List[Conflict]:
    """Use AI to detect exclusion conflicts."""

    conflicts = []

    # For each coverage type, check if it's excluded elsewhere
    coverages = []
    exclusions = []

    for policy in policies:
        # Extract coverages
        for coverage in policy.coverages:
            coverages.append({
                "policy_id": policy.id,
                "policy_type": policy.policy_type,
                "coverage": coverage.coverage_type,
                "description": coverage.description
            })

        # Extract exclusions (from policy text via RAG)
        policy_exclusions = await rag_service.query(
            f"What are the exclusions in policy {policy.policy_number}?",
            property_id=policy.property_id
        )
        exclusions.append({
            "policy_id": policy.id,
            "exclusions": policy_exclusions
        })

    # Use AI to find conflicts
    prompt = f"""
    Analyze these coverages and exclusions for conflicts:

    COVERAGES:
    {json.dumps(coverages, indent=2)}

    EXCLUSIONS:
    {json.dumps(exclusions, indent=2)}

    Identify cases where:
    1. One policy covers something another policy excludes
    2. The primary policy has a sublimit, and excess excludes that coverage
    3. Exclusions create gaps in the coverage tower

    Return conflicts in JSON format.
    """

    # Call LLM for analysis
    analysis = await llm_service.analyze(prompt)

    for conflict in analysis.conflicts:
        conflicts.append(Conflict(**conflict))

    return conflicts
```

### 6. Limit Tower Gaps

**Description:** The coverage limits don't stack properly.

**Example:**
```
⚠️ LIMIT TOWER GAP

Property Limit: $35,000,000
Umbrella Limit: $10,000,000
Umbrella Attachment: $50,000,000

ISSUE: Umbrella attaches at $50M but property only provides $35M.
There's a $15M gap where you have no coverage.

RECOMMENDATION: Lower umbrella attachment point or increase property limit.
```

---

## AI-Powered Analysis

### Using RAG for Deep Conflict Detection

```python
class ConflictDetectionService:
    def __init__(
        self,
        rag_service: RAGQueryService,
        policy_repo: PolicyRepository,
        llm_client: LLMClient
    ):
        self.rag_service = rag_service
        self.policy_repo = policy_repo
        self.llm_client = llm_client

    async def detect_conflicts(
        self,
        property_id: UUID
    ) -> List[Conflict]:
        """Detect all conflicts for a property."""

        policies = await self.policy_repo.get_by_property(property_id)

        # Run rule-based checks
        conflicts = []
        conflicts.extend(self._check_excess_primary_gaps(policies))
        conflicts.extend(self._check_entity_mismatches(policies))
        conflicts.extend(self._check_valuation_conflicts(policies))
        conflicts.extend(self._check_coverage_overlaps(policies))

        # Run AI-powered analysis
        ai_conflicts = await self._ai_conflict_analysis(property_id, policies)
        conflicts.extend(ai_conflicts)

        # Deduplicate and rank
        conflicts = self._deduplicate_conflicts(conflicts)
        conflicts = self._rank_conflicts(conflicts)

        return conflicts

    async def _ai_conflict_analysis(
        self,
        property_id: UUID,
        policies: List[Policy]
    ) -> List[Conflict]:
        """Use AI to find subtle conflicts."""

        # Build context from policy documents
        context = []
        for policy in policies:
            # Get key sections from each policy
            exclusions = await self.rag_service.query(
                f"List all exclusions from policy {policy.policy_number}",
                property_id=property_id,
                filter_document_type="policy"
            )
            context.append({
                "policy_number": policy.policy_number,
                "policy_type": policy.policy_type,
                "carrier": policy.carrier.name if policy.carrier else "Unknown",
                "key_exclusions": exclusions.answer
            })

        # Ask LLM to identify conflicts
        prompt = f"""
        Analyze these insurance policies for potential conflicts:

        {json.dumps(context, indent=2)}

        Look for:
        1. Coverage that one policy provides but another excludes
        2. Gaps where excess coverage won't attach to primary
        3. Conflicting definitions or terms
        4. Situations where claims might be denied due to policy conflicts

        For each conflict found, provide:
        - conflict_type
        - severity (critical/warning/info)
        - title
        - description
        - affected_policies
        - recommendation

        Return as JSON array.
        """

        response = await self.llm_client.generate(
            prompt=prompt,
            model="gemini-2.5-flash",
            response_format="json"
        )

        return [Conflict(**c) for c in response.conflicts]
```

---

## API Endpoints

### Get Coverage Conflicts

#### `GET /v1/properties/{id}/conflicts`

Returns detected coverage conflicts for a property.

**Response:**
```json
{
  "property_id": "uuid",
  "property_name": "Buffalo Run",
  "analysis_date": "2025-01-15T10:00:00Z",
  "summary": {
    "total_conflicts": 3,
    "critical": 1,
    "warning": 1,
    "info": 1
  },
  "conflicts": [
    {
      "id": "uuid",
      "conflict_type": "excess_primary_gap",
      "severity": "critical",
      "title": "Gap between GL and Umbrella coverage",
      "description": "Umbrella requires $2M underlying GL, but you only have $1M. Claims between $1M and $2M would not be covered.",
      "affected_policies": [
        {
          "id": "uuid",
          "policy_number": "GL-2024-001",
          "policy_type": "general_liability"
        },
        {
          "id": "uuid",
          "policy_number": "UMB-2024-001",
          "policy_type": "umbrella"
        }
      ],
      "gap_amount": 1000000,
      "recommendation": "Increase GL to $2M per occurrence or get umbrella endorsement to accept $1M underlying",
      "detected_at": "2025-01-15T10:00:00Z"
    },
    {
      "id": "uuid",
      "conflict_type": "entity_mismatch",
      "severity": "warning",
      "title": "Named insured differs across policies",
      "description": "Property policy lists 'ABC Management LLC' but GL lists 'ABC Management Inc'",
      "affected_policies": ["uuid", "uuid"],
      "recommendation": "Update all policies to list the same legal entity name"
    },
    {
      "id": "uuid",
      "conflict_type": "coverage_overlap",
      "severity": "info",
      "title": "Duplicate equipment breakdown coverage",
      "description": "Equipment breakdown found on both property policy and standalone policy",
      "potential_savings": 5000,
      "recommendation": "Consider removing duplicate coverage to save approximately $5,000"
    }
  ]
}
```

---

### Run Conflict Analysis

#### `POST /v1/properties/{id}/conflicts/analyze`

Trigger a fresh conflict analysis.

**Request Body:**
```json
{
  "include_ai_analysis": true,
  "force_refresh": false
}
```

**Response:**
```json
{
  "property_id": "uuid",
  "analysis_id": "uuid",
  "status": "completed",
  "conflicts_found": 3,
  "duration_ms": 4500
}
```

---

### Acknowledge Conflict

#### `POST /v1/conflicts/{id}/acknowledge`

Mark a conflict as reviewed.

**Request Body:**
```json
{
  "notes": "Discussed with broker, will address at renewal"
}
```

---

## Triggers

### When to Run Conflict Detection

1. **On Document Ingestion** - New policy uploaded
2. **On Policy Update** - Policy terms changed
3. **Manual Request** - User triggers analysis
4. **Periodic** - Weekly scan for all properties

```python
@on_event("document.ingested")
async def check_conflicts_on_ingestion(event):
    if event.document_type == "policy":
        await conflict_service.detect_conflicts(event.property_id)

@scheduled("0 2 * * 0")  # Weekly on Sunday 2 AM
async def weekly_conflict_scan():
    properties = await property_repo.list_all()
    for prop in properties:
        await conflict_service.detect_conflicts(prop.id)
```

---

## Related Documents

- [02-gap-detection.md](./02-gap-detection.md) - Single-policy gap detection
- [05-insurance-health-score.md](./05-insurance-health-score.md) - Conflicts affect health score
- [08-policy-comparison.md](./08-policy-comparison.md) - Detecting changes over time
