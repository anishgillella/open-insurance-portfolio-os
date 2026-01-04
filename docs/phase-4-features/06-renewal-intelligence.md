# Renewal Intelligence Engine

## Overview

The Renewal Intelligence Engine provides **AI-powered insights for policy renewals**. It transforms the renewal process from reactive ("policy is expiring!") to proactive ("here's your renewal strategy with market context").

**This is an innovation that doesn't exist in the market today.**

---

## Why This Matters

### Current State (What Exists)
- Calendar reminders for expiration dates
- Manual broker conversations
- No visibility into market conditions
- No automated document preparation

### The Gap
Property owners currently:
- Don't know what premium changes to expect
- Can't compare their situation to market trends
- Spend hours gathering documents for brokers
- Have no negotiation leverage from their own data

### Our Innovation
The Renewal Intelligence Engine provides:
1. **Premium Forecasts** - Predict likely premium changes
2. **Market Context** - Current trends in the insurance market
3. **Renewal Readiness** - Automated document preparation
4. **Negotiation Insights** - Data-driven leverage points

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RENEWAL INTELLIGENCE ENGINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     DATA COLLECTION LAYER                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Internal   │  │  Parallel AI │  │   Historical │              │   │
│  │  │  Portfolio   │  │  Market Data │  │    Trends    │              │   │
│  │  │    Data      │  │   Research   │  │              │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ANALYSIS ENGINE                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Premium    │  │    Loss      │  │   Market     │              │   │
│  │  │  Forecaster  │  │   Analysis   │  │   Analyzer   │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    OUTPUT GENERATION                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Renewal    │  │   Broker     │  │  Negotiation │              │   │
│  │  │   Timeline   │  │  Prep Pack   │  │   Insights   │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### 1. Premium Forecast

Predict likely premium changes based on multiple factors.

**Factors Considered:**
| Factor | Weight | Description |
|--------|--------|-------------|
| Loss History | 30% | Claims in past 3-5 years |
| Market Trends | 25% | Industry-wide rate changes |
| Property Changes | 15% | TIV changes, renovations |
| Coverage Changes | 15% | Limit/deductible adjustments |
| Carrier Appetite | 15% | Carrier's current market position |

**Output:**
```json
{
  "property_id": "uuid",
  "current_premium": 145000,
  "forecast": {
    "low_estimate": 152250,
    "mid_estimate": 162350,
    "high_estimate": 174000,
    "percentage_change": {
      "low": 5,
      "mid": 12,
      "high": 20
    }
  },
  "confidence": 0.75,
  "factors": [
    {
      "factor": "market_trends",
      "impact": "+8-12%",
      "description": "Commercial property rates in Texas rising due to CAT losses"
    },
    {
      "factor": "loss_history",
      "impact": "+2-3%",
      "description": "One water damage claim ($45K) in past 3 years"
    },
    {
      "factor": "tiv_change",
      "impact": "+5%",
      "description": "Building values increased 5% for inflation adjustment"
    }
  ],
  "comparison": {
    "last_renewal_change": 8.5,
    "3_year_average_change": 6.2
  }
}
```

### 2. Market Intelligence

AI-researched market conditions for the specific property type and location.

**Using Parallel AI Task API:**
```python
async def get_market_intelligence(
    property: Property,
    carrier: Carrier
) -> MarketIntelligence:
    """Research current market conditions."""

    result = await parallel_client.task.create(
        objective=f"""
        Research current commercial property insurance market conditions for:
        - Property type: {property.property_type} (multifamily apartments)
        - Location: {property.state}
        - Size: {property.total_units} units, ${property.tiv:,.0f} TIV
        - Current carrier: {carrier.name if carrier else 'Unknown'}

        Provide:
        1. Current rate trends (% change YoY) for this property type
        2. Key factors driving rate changes in this market
        3. Carrier appetite and capacity for this segment
        4. Predicted rate changes for next 6 months
        5. Any regulatory or market changes affecting coverage

        Focus on 2025 data and trends.
        """,
        processor="pro",
        output_schema={
            "type": "object",
            "properties": {
                "rate_trend_pct": {"type": "number"},
                "rate_trend_range": {"type": "string"},
                "key_factors": {"type": "array", "items": {"type": "string"}},
                "carrier_appetite": {"type": "string"},
                "forecast_next_6mo": {"type": "string"},
                "regulatory_changes": {"type": "array", "items": {"type": "string"}},
                "sources": {"type": "array", "items": {"type": "string"}}
            }
        }
    )

    return MarketIntelligence(**result.output)
```

**Output Example:**
```json
{
  "market_intelligence": {
    "rate_trend": "+10-15%",
    "rate_trend_description": "Commercial property rates in Texas continue upward trend",
    "key_factors": [
      "Hurricane losses in Gulf region driving reinsurance costs up",
      "Construction cost inflation affecting replacement values",
      "Carrier capacity reduction in coastal markets"
    ],
    "carrier_appetite": {
      "current_carrier": "Zurich - Stable appetite, looking to retain quality accounts",
      "market_overview": "Major carriers cautious on Texas coastal, competitive inland"
    },
    "forecast_6mo": "Rates expected to stabilize Q2 2025 after reinsurance renewals",
    "opportunities": [
      "Early renewal (60+ days) may lock in lower rates before Q1 increases",
      "Higher deductibles can offset premium increases by 5-8%"
    ],
    "sources": [
      "Insurance Journal - Texas Commercial Property Report Q4 2024",
      "AM Best - Market Segment Outlook: Multifamily",
      "CIAB Commercial Property/Casualty Market Report"
    ]
  }
}
```

### 3. Renewal Timeline

Automated timeline with action items.

```json
{
  "property_id": "uuid",
  "policy_expiration": "2025-04-15",
  "renewal_timeline": [
    {
      "date": "2024-12-15",
      "days_before": 120,
      "milestone": "Begin Renewal Process",
      "status": "completed",
      "actions": [
        "Review current coverage with broker",
        "Identify any coverage changes needed"
      ]
    },
    {
      "date": "2025-01-15",
      "days_before": 90,
      "milestone": "Gather Renewal Documents",
      "status": "in_progress",
      "actions": [
        "Request loss runs from carriers",
        "Update property valuations",
        "Prepare SOV"
      ],
      "documents_ready": {
        "loss_runs": true,
        "sov": false,
        "property_schedule": true
      }
    },
    {
      "date": "2025-02-15",
      "days_before": 60,
      "milestone": "Submit to Market",
      "status": "upcoming",
      "actions": [
        "Broker submits to carriers",
        "Review initial indications"
      ]
    },
    {
      "date": "2025-03-15",
      "days_before": 30,
      "milestone": "Finalize Renewal",
      "status": "upcoming",
      "actions": [
        "Compare quotes",
        "Negotiate final terms",
        "Bind coverage"
      ]
    },
    {
      "date": "2025-04-15",
      "days_before": 0,
      "milestone": "Policy Effective",
      "status": "upcoming",
      "actions": [
        "Confirm new policy received",
        "Verify coverage matches quote"
      ]
    }
  ]
}
```

### 4. Broker Prep Package

Auto-generated document package for the broker.

**Contents:**
```json
{
  "property_id": "uuid",
  "generated_at": "2025-01-15T10:00:00Z",
  "package": {
    "property_summary": {
      "name": "Buffalo Run Apartments",
      "address": "123 Buffalo Way, Houston TX 77001",
      "property_type": "Multifamily - Garden Style",
      "year_built": 1995,
      "total_units": 200,
      "total_sqft": 180000,
      "construction": "Frame"
    },
    "current_coverage": {
      "property": {
        "carrier": "Zurich",
        "policy_number": "PRO-2024-001234",
        "effective": "2024-04-15",
        "expiration": "2025-04-15",
        "building_limit": 35989980,
        "deductible": 25000,
        "premium": 95000
      },
      "general_liability": {
        "carrier": "Zurich",
        "per_occurrence": 1000000,
        "aggregate": 2000000,
        "premium": 35000
      },
      "umbrella": {
        "carrier": "Zurich",
        "limit": 10000000,
        "premium": 15000
      }
    },
    "property_schedule": {
      "buildings": [
        {
          "name": "Building A",
          "address": "123 Buffalo Way, Bldg A",
          "sqft": 36000,
          "units": 40,
          "stories": 3,
          "year_built": 1995,
          "construction": "Frame",
          "replacement_cost": 7200000
        }
      ],
      "total_replacement_cost": 35989980
    },
    "loss_history": {
      "summary": {
        "total_claims_5yr": 2,
        "total_incurred": 67500,
        "loss_ratio": 4.6
      },
      "claims": [
        {
          "date": "2023-06-15",
          "type": "Water Damage",
          "incurred": 45000,
          "status": "Closed"
        },
        {
          "date": "2022-01-20",
          "type": "Slip and Fall",
          "incurred": 22500,
          "status": "Closed"
        }
      ]
    },
    "changes_since_last_renewal": [
      "Building values increased 5% per inflation adjustment",
      "No major renovations or changes",
      "One water damage claim settled"
    ],
    "coverage_requests": [
      "Maintain current coverage structure",
      "Explore options to reduce wind deductible"
    ],
    "documents_attached": [
      "Current declarations pages",
      "Loss runs (5 year)",
      "Statement of Values",
      "Certificate of Insurance"
    ]
  },
  "download_url": "/v1/properties/{id}/renewal/package/download"
}
```

### 5. Negotiation Insights

Data-driven leverage points for renewal negotiations.

```json
{
  "property_id": "uuid",
  "negotiation_insights": {
    "strengths": [
      {
        "point": "Excellent Loss Ratio",
        "details": "Your 4.6% loss ratio is significantly below the industry average of 55-65%",
        "leverage": "Request premium credit or rate hold based on loss experience"
      },
      {
        "point": "Long-Term Customer",
        "details": "8 years with current carrier without major claims",
        "leverage": "Emphasize loyalty and request retention pricing"
      },
      {
        "point": "Professional Management",
        "details": "Property managed by professional management company with good track record",
        "leverage": "Highlight risk management practices"
      }
    ],
    "weaknesses": [
      {
        "point": "Recent Claim",
        "details": "Water damage claim ($45K) in 2023 may impact renewal",
        "mitigation": "Emphasize remediation steps taken to prevent recurrence"
      },
      {
        "point": "Building Age",
        "details": "30-year-old property may face age-related scrutiny",
        "mitigation": "Provide documentation of recent upgrades and maintenance"
      }
    ],
    "negotiation_strategies": [
      {
        "strategy": "Request Rate Hold",
        "rationale": "Based on loss history, you should not be subject to full market increases",
        "expected_outcome": "5-8% increase vs market 12-15%"
      },
      {
        "strategy": "Increase Deductible",
        "rationale": "Raising property deductible from $25K to $50K",
        "expected_outcome": "3-5% premium reduction"
      },
      {
        "strategy": "Multi-Year Policy",
        "rationale": "Lock in rates for 2-3 years if market is rising",
        "expected_outcome": "Rate certainty, avoid next year's increases"
      }
    ],
    "market_comparison": {
      "your_rate_per_sqft": 0.53,
      "market_average": 0.58,
      "percentile": 35,
      "note": "Your rate is below average - good negotiating position"
    }
  }
}
```

---

## API Endpoints

### Get Renewal Intelligence

#### `GET /v1/properties/{id}/renewal`

Returns comprehensive renewal intelligence for a property.

**Response:**
```json
{
  "property_id": "uuid",
  "property_name": "Buffalo Run",
  "renewal_status": {
    "policy_expiration": "2025-04-15",
    "days_until_expiration": 90,
    "renewal_phase": "preparation",
    "readiness_score": 75
  },
  "premium_forecast": { ... },
  "market_intelligence": { ... },
  "timeline": { ... },
  "negotiation_insights": { ... },
  "broker_package_ready": true,
  "generated_at": "2025-01-15T10:00:00Z"
}
```

---

### Get Premium Forecast

#### `GET /v1/properties/{id}/renewal/forecast`

Returns premium forecast only.

**Response:**
```json
{
  "property_id": "uuid",
  "current_premium": 145000,
  "forecast": {
    "low": 152250,
    "mid": 162350,
    "high": 174000
  },
  "factors": [ ... ],
  "confidence": 0.75
}
```

---

### Get Market Intelligence

#### `GET /v1/properties/{id}/renewal/market`

Returns market intelligence (triggers Parallel AI research if stale).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `refresh` | boolean | false | Force refresh from Parallel AI |

**Response:**
```json
{
  "property_id": "uuid",
  "market_intelligence": { ... },
  "data_freshness": "2_days",
  "next_refresh": "2025-01-18T10:00:00Z"
}
```

---

### Generate Broker Package

#### `POST /v1/properties/{id}/renewal/package`

Generate broker preparation package.

**Request Body:**
```json
{
  "include_loss_runs": true,
  "include_sov": true,
  "include_current_policies": true,
  "custom_notes": "Please explore options for lower wind deductible"
}
```

**Response:**
```json
{
  "property_id": "uuid",
  "package_id": "uuid",
  "download_url": "/v1/properties/{id}/renewal/package/{package_id}/download",
  "expires_at": "2025-01-22T10:00:00Z",
  "contents": [
    "property_summary.pdf",
    "coverage_summary.pdf",
    "loss_runs.pdf",
    "sov.xlsx",
    "declarations.pdf"
  ]
}
```

---

### Download Broker Package

#### `GET /v1/properties/{id}/renewal/package/{package_id}/download`

Downloads the broker package as a ZIP file.

**Response:** ZIP file containing all documents

---

## Implementation

### Renewal Intelligence Service

```python
class RenewalIntelligenceService:
    def __init__(
        self,
        property_repo: PropertyRepository,
        policy_repo: PolicyRepository,
        claim_repo: ClaimRepository,
        parallel_client: ParallelClient,
        document_service: DocumentService
    ):
        self.property_repo = property_repo
        self.policy_repo = policy_repo
        self.claim_repo = claim_repo
        self.parallel_client = parallel_client
        self.document_service = document_service

    async def get_renewal_intelligence(
        self,
        property_id: UUID
    ) -> RenewalIntelligence:
        """Get comprehensive renewal intelligence."""

        property = await self.property_repo.get(property_id)
        policies = await self.policy_repo.get_by_property(property_id)
        claims = await self.claim_repo.get_by_property(property_id, years=5)

        # Calculate premium forecast
        forecast = await self._calculate_premium_forecast(property, policies, claims)

        # Get market intelligence (may use cached)
        market = await self._get_market_intelligence(property, policies)

        # Generate timeline
        timeline = self._generate_timeline(policies)

        # Generate negotiation insights
        insights = self._generate_negotiation_insights(property, policies, claims, market)

        return RenewalIntelligence(
            property_id=property_id,
            premium_forecast=forecast,
            market_intelligence=market,
            timeline=timeline,
            negotiation_insights=insights
        )

    async def _calculate_premium_forecast(
        self,
        property: Property,
        policies: List[Policy],
        claims: List[Claim]
    ) -> PremiumForecast:
        """Calculate expected premium changes."""

        current_premium = sum(p.annual_premium or 0 for p in policies if p.status == "active")

        # Factor 1: Loss history impact
        total_incurred = sum(c.incurred_amount or 0 for c in claims)
        loss_ratio = total_incurred / (current_premium * 5) if current_premium > 0 else 0

        if loss_ratio < 0.3:
            loss_impact = (-0.02, 0.02)  # Good loss history
        elif loss_ratio < 0.5:
            loss_impact = (0.02, 0.05)   # Average
        else:
            loss_impact = (0.05, 0.15)   # Poor

        # Factor 2: Market trend (from cached or default)
        market_impact = (0.08, 0.12)  # Default assumption

        # Factor 3: TIV changes
        tiv_change = 0.05  # Assume 5% inflation adjustment

        # Calculate ranges
        low_pct = loss_impact[0] + market_impact[0] + tiv_change
        high_pct = loss_impact[1] + market_impact[1] + tiv_change
        mid_pct = (low_pct + high_pct) / 2

        return PremiumForecast(
            current_premium=current_premium,
            low_estimate=current_premium * (1 + low_pct),
            mid_estimate=current_premium * (1 + mid_pct),
            high_estimate=current_premium * (1 + high_pct),
            confidence=0.75
        )

    async def _get_market_intelligence(
        self,
        property: Property,
        policies: List[Policy]
    ) -> MarketIntelligence:
        """Get market intelligence, using Parallel AI if needed."""

        # Check cache first
        cached = await self._get_cached_market_data(property.id)
        if cached and cached.age_hours < 48:
            return cached.data

        # Research with Parallel AI
        carrier = await self._get_primary_carrier(policies)

        result = await self.parallel_client.task.create(
            objective=f"""
            Research current commercial property insurance market conditions for:
            - Property type: {property.property_type}
            - Location: {property.state}
            - Size: {property.total_units} units
            - TIV: ${sum(b.replacement_cost or 0 for b in property.buildings):,.0f}

            Provide:
            1. Current rate trends (% YoY) for multifamily in {property.state}
            2. Key factors driving premium changes
            3. Carrier appetite for this segment
            4. 6-month outlook
            """,
            processor="pro"
        )

        market = MarketIntelligence(**result.output)
        await self._cache_market_data(property.id, market)
        return market
```

---

## Triggers

### When to Generate Renewal Intelligence

1. **90 Days Before Expiration** - Auto-generate initial analysis
2. **60 Days Before Expiration** - Refresh with latest market data
3. **On Request** - User manually requests analysis
4. **Market Changes** - If monitoring detects significant changes

```python
@scheduled("0 8 * * *")  # Daily at 8 AM
async def check_upcoming_renewals():
    """Generate renewal intelligence for upcoming renewals."""

    # Find policies expiring in 90-120 days
    upcoming = await policy_repo.get_expiring_between(days_min=90, days_max=120)

    for policy in upcoming:
        existing = await renewal_cache.get(policy.property_id)
        if not existing:
            await renewal_service.get_renewal_intelligence(policy.property_id)
            await notify_user(policy.property_id, "Renewal analysis ready")
```

---

## Related Documents

- [09-parallel-ai-integration.md](./09-parallel-ai-integration.md) - Parallel AI for market research
- [02-gap-detection.md](./02-gap-detection.md) - Expiration detection
- [01-dashboard-api.md](./01-dashboard-api.md) - Expiration timeline display
