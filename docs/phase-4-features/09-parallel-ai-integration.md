# Parallel AI Integration

## Overview

[Parallel AI](https://parallel.ai/) provides web research APIs built specifically for AI agents. This integration enables Open Insurance to access real-time market intelligence, regulatory updates, and property risk data from the web.

---

## Why Parallel AI

### Capabilities

| API | Use Case | Benefit |
|-----|----------|---------|
| **Task API** | Deep research on market conditions | Structured, cited answers |
| **Search API** | Quick lookups for specific data | Fast, relevant results |
| **Extract API** | Pull data from web pages | Clean, LLM-ready content |
| **Monitor API** | Track changes over time | Proactive alerts |
| **FindAll API** | Entity discovery | Market comparisons |

### Performance

- Task API achieves 48% accuracy on BrowseComp/WISER benchmarks
- Outperforms GPT-4 browsing (1%), Claude (6%), Perplexity (8%)
- SOC-II Type II certified for enterprise security

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PARALLEL AI INTEGRATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     OPEN INSURANCE SERVICES                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Renewal    │  │    Risk      │  │   Market     │              │   │
│  │  │ Intelligence │  │ Enrichment   │  │  Monitoring  │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     PARALLEL CLIENT WRAPPER                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │    Task      │  │   Search     │  │   Extract    │              │   │
│  │  │   Client     │  │   Client     │  │   Client     │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │  ┌──────────────┐  ┌──────────────┐                                │   │
│  │  │   Monitor    │  │   FindAll    │                                │   │
│  │  │   Client     │  │   Client     │                                │   │
│  │  └──────────────┘  └──────────────┘                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     PARALLEL AI PLATFORM                             │   │
│  │                     https://parallel.ai                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Use Cases

### 1. Market Intelligence for Renewals

**Purpose:** Research current market conditions for renewal negotiations.

**API:** Task API (processor: `pro` or `ultra`)

```python
async def get_market_intelligence(
    property_type: str,
    state: str,
    tiv: float
) -> MarketIntelligence:
    """Research market conditions for a property type/location."""

    result = await parallel_client.task.create(
        objective=f"""
        Research current commercial property insurance market conditions for:
        - Property type: {property_type}
        - Location: {state}
        - Total Insured Value: ${tiv:,.0f}

        Provide:
        1. Current rate trends (% change YoY) for this property type in this state
        2. Key factors driving rate changes (CAT losses, reinsurance, etc.)
        3. Major carrier appetite for this segment
        4. Predicted rate changes for next 6 months
        5. Any regulatory changes affecting coverage requirements

        Focus on Q4 2024 / Q1 2025 data.
        """,
        processor="pro",
        output_schema={
            "type": "object",
            "properties": {
                "rate_trend_pct": {"type": "number"},
                "rate_trend_range": {"type": "string"},
                "key_factors": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "carrier_appetite": {
                    "type": "object",
                    "properties": {
                        "increasing": {"type": "array", "items": {"type": "string"}},
                        "stable": {"type": "array", "items": {"type": "string"}},
                        "decreasing": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "forecast_6mo": {"type": "string"},
                "regulatory_changes": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    )

    return MarketIntelligence(
        rate_trend_pct=result.output.get("rate_trend_pct"),
        rate_trend_range=result.output.get("rate_trend_range"),
        key_factors=result.output.get("key_factors", []),
        carrier_appetite=result.output.get("carrier_appetite", {}),
        forecast_6mo=result.output.get("forecast_6mo"),
        regulatory_changes=result.output.get("regulatory_changes", []),
        sources=result.output.get("sources", []),
        researched_at=datetime.utcnow()
    )
```

**Example Output:**
```json
{
  "rate_trend_pct": 12,
  "rate_trend_range": "10-15%",
  "key_factors": [
    "Hurricane losses in Gulf region driving reinsurance costs",
    "Construction cost inflation (8% YoY) affecting replacement values",
    "Carrier capacity reduction in coastal Texas markets",
    "Social inflation impacting liability claims"
  ],
  "carrier_appetite": {
    "increasing": ["Nationwide", "Liberty Mutual"],
    "stable": ["Zurich", "Travelers", "Hartford"],
    "decreasing": ["AIG", "Chubb (coastal)"]
  },
  "forecast_6mo": "Rates expected to moderate in Q2 2025 after Jan 1 reinsurance renewals settle. Inland Texas more competitive than coastal.",
  "regulatory_changes": [
    "Texas DOI increased minimum flood coverage requirements in Zone A areas",
    "New building code requirements for wind mitigation in coastal counties"
  ],
  "sources": [
    "Insurance Journal - Texas Commercial Property Report Q4 2024",
    "CIAB Commercial Property/Casualty Market Report",
    "AM Best - Market Segment Outlook 2025"
  ]
}
```

---

### 2. Property Risk Enrichment

**Purpose:** Get external risk data for a property address.

**API:** Task API (processor: `core`)

```python
async def get_property_risk_data(
    address: str,
    city: str,
    state: str,
    zip_code: str
) -> PropertyRiskData:
    """Get risk data for a property from public sources."""

    full_address = f"{address}, {city}, {state} {zip_code}"

    result = await parallel_client.task.create(
        objective=f"""
        Research property risk data for: {full_address}

        Find:
        1. FEMA flood zone designation
        2. Distance to nearest fire station
        3. Fire protection class (if available)
        4. Recent building permits or violations
        5. Historical weather events in the area (hurricanes, tornadoes, hail)
        6. Crime statistics for the area
        7. Any environmental hazards nearby

        Use official government sources where possible.
        """,
        processor="core",
        output_schema={
            "type": "object",
            "properties": {
                "flood_zone": {"type": "string"},
                "flood_zone_source": {"type": "string"},
                "fire_station_distance_miles": {"type": "number"},
                "fire_protection_class": {"type": "string"},
                "recent_permits": {"type": "array", "items": {"type": "string"}},
                "violations": {"type": "array", "items": {"type": "string"}},
                "weather_risks": {
                    "type": "object",
                    "properties": {
                        "hurricane_risk": {"type": "string"},
                        "tornado_risk": {"type": "string"},
                        "hail_risk": {"type": "string"}
                    }
                },
                "crime_index": {"type": "number"},
                "environmental_hazards": {"type": "array", "items": {"type": "string"}}
            }
        }
    )

    return PropertyRiskData(**result.output)
```

---

### 3. Carrier Research

**Purpose:** Research carrier financial strength and specialties.

**API:** Task API + FindAll API

```python
async def research_carrier(carrier_name: str) -> CarrierIntelligence:
    """Research a carrier's financial strength and market position."""

    result = await parallel_client.task.create(
        objective=f"""
        Research the insurance carrier: {carrier_name}

        Find:
        1. Current A.M. Best rating and outlook
        2. S&P and Moody's ratings if available
        3. Recent financial performance
        4. Market specialty areas
        5. Recent news (claims issues, leadership changes, market exits)
        6. Customer satisfaction ratings if available
        """,
        processor="core"
    )

    return CarrierIntelligence(**result.output)


async def find_alternative_carriers(
    property_type: str,
    state: str,
    min_rating: str = "A-"
) -> List[Carrier]:
    """Find carriers that write this type of business."""

    result = await parallel_client.findall.create(
        objective=f"""
        Find insurance carriers that:
        - Write commercial {property_type} insurance in {state}
        - Have A.M. Best rating of {min_rating} or better
        - Are actively writing new business

        For each carrier, provide:
        - Company name
        - A.M. Best rating
        - Specialty focus
        - Contact or quote process
        """,
        processor="pro",
        max_entities=10
    )

    return [Carrier(**c) for c in result.entities]
```

---

### 4. Regulatory Monitoring

**Purpose:** Track changes to insurance regulations.

**API:** Monitor API

```python
async def setup_regulatory_monitoring(states: List[str]) -> str:
    """Set up monitoring for regulatory changes."""

    monitor = await parallel_client.monitor.create(
        objective=f"""
        Monitor for insurance regulatory changes in: {', '.join(states)}

        Watch for:
        1. Changes to minimum coverage requirements
        2. New filing requirements
        3. Rate filing approvals/denials
        4. Building code changes affecting insurance
        5. Flood zone remapping
        6. New disclosure requirements

        Alert on significant changes.
        """,
        frequency="daily",
        webhook_url=f"{settings.BASE_URL}/webhooks/parallel/regulatory"
    )

    return monitor.id


@webhook("/webhooks/parallel/regulatory")
async def handle_regulatory_update(payload: dict):
    """Handle incoming regulatory updates."""

    change = RegulatoryChange(
        state=payload.get("state"),
        change_type=payload.get("change_type"),
        summary=payload.get("summary"),
        effective_date=payload.get("effective_date"),
        source_url=payload.get("source_url")
    )

    # Notify affected users
    affected_properties = await property_repo.get_by_state(change.state)
    for prop in affected_properties:
        await notify_user(
            property_id=prop.id,
            title=f"Regulatory Change in {change.state}",
            message=change.summary,
            severity="info"
        )
```

---

### 5. Lender Requirement Lookup

**Purpose:** Research lender-specific insurance requirements.

**API:** Task API

```python
async def get_lender_requirements(lender_name: str) -> LenderRequirements:
    """Research a lender's insurance requirements."""

    result = await parallel_client.task.create(
        objective=f"""
        Research the insurance requirements for loans from: {lender_name}

        Find their requirements for:
        1. Minimum property coverage (replacement cost %)
        2. Minimum general liability limits
        3. Umbrella/excess requirements
        4. Maximum deductible allowed
        5. Flood insurance requirements
        6. Required endorsements (mortgagee clause, etc.)
        7. Notice requirements for policy changes

        Look for official lender guidelines or seller/servicer guides.
        """,
        processor="pro"
    )

    return LenderRequirements(**result.output)
```

---

## Implementation

### Client Configuration

```python
# app/services/parallel/client.py

from parallel import Parallel
from app.core.config import settings


class ParallelClient:
    def __init__(self):
        self.client = Parallel(api_key=settings.PARALLEL_API_KEY)

    @property
    def task(self):
        return self.client.task

    @property
    def search(self):
        return self.client.search

    @property
    def extract(self):
        return self.client.extract

    @property
    def monitor(self):
        return self.client.monitor

    @property
    def findall(self):
        return self.client.findall


# Dependency injection
def get_parallel_client() -> ParallelClient:
    return ParallelClient()
```

### Caching Strategy

```python
# app/services/parallel/cache.py

from datetime import timedelta

CACHE_TTL = {
    "market_intelligence": timedelta(hours=48),
    "property_risk": timedelta(days=7),
    "carrier_info": timedelta(days=30),
    "lender_requirements": timedelta(days=90),
}


class ParallelCache:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def get_cached(
        self,
        cache_type: str,
        key: str
    ) -> Optional[dict]:
        cache_key = f"parallel:{cache_type}:{key}"
        data = await self.redis.get(cache_key)
        if data:
            return json.loads(data)
        return None

    async def set_cached(
        self,
        cache_type: str,
        key: str,
        data: dict
    ) -> None:
        cache_key = f"parallel:{cache_type}:{key}"
        ttl = CACHE_TTL.get(cache_type, timedelta(hours=24))
        await self.redis.setex(
            cache_key,
            int(ttl.total_seconds()),
            json.dumps(data)
        )
```

### Rate Limiting

```python
# app/services/parallel/rate_limiter.py

from asyncio import Semaphore

class ParallelRateLimiter:
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = Semaphore(max_concurrent)

    async def acquire(self):
        await self.semaphore.acquire()

    def release(self):
        self.semaphore.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        self.release()
```

---

## API Endpoints

### Get Market Intelligence

#### `GET /v1/market-intelligence`

Get market intelligence for a property type/location.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `property_type` | string | Yes | multifamily, office, retail, etc. |
| `state` | string | Yes | State code (TX, CA, etc.) |
| `refresh` | boolean | No | Force refresh from Parallel |

**Response:**
```json
{
  "rate_trend_pct": 12,
  "rate_trend_range": "10-15%",
  "key_factors": [...],
  "carrier_appetite": {...},
  "forecast_6mo": "...",
  "sources": [...],
  "cached": true,
  "cache_age_hours": 12,
  "next_refresh": "2025-01-17T10:00:00Z"
}
```

---

### Enrich Property Risk

#### `POST /v1/properties/{id}/enrich-risk`

Enrich property with external risk data.

**Response:**
```json
{
  "property_id": "uuid",
  "risk_data": {
    "flood_zone": "X",
    "fire_protection_class": "3",
    "crime_index": 45,
    "weather_risks": {...}
  },
  "sources": [...],
  "enriched_at": "2025-01-15T10:00:00Z"
}
```

---

### Research Carrier

#### `GET /v1/carriers/{name}/research`

Research a carrier's financial strength and market position.

**Response:**
```json
{
  "carrier_name": "Zurich",
  "ratings": {
    "am_best": "A+",
    "am_best_outlook": "Stable",
    "sp": "AA-"
  },
  "specialty_areas": [
    "Commercial Property",
    "Multifamily",
    "Large Accounts"
  ],
  "recent_news": [...],
  "sources": [...]
}
```

---

## Cost Management

### Processor Selection

| Processor | Cost | Use For |
|-----------|------|---------|
| `lite` | Lowest | Simple lookups, basic facts |
| `base` | Low | Standard research queries |
| `core` | Medium | Property risk, carrier research |
| `pro` | Higher | Market intelligence, complex analysis |
| `ultra` | Highest | Critical decisions, comprehensive research |

### Cost Optimization

```python
class ParallelCostOptimizer:
    def select_processor(
        self,
        query_type: str,
        importance: str
    ) -> str:
        """Select appropriate processor based on query type."""

        processor_map = {
            ("property_risk", "normal"): "core",
            ("property_risk", "high"): "pro",
            ("market_intelligence", "normal"): "pro",
            ("market_intelligence", "high"): "ultra",
            ("carrier_research", "normal"): "core",
            ("lender_requirements", "normal"): "core",
            ("regulatory_update", "normal"): "base",
        }

        return processor_map.get((query_type, importance), "core")
```

---

## Environment Configuration

```python
# .env

# Parallel AI Configuration
PARALLEL_API_KEY=your_api_key_here
PARALLEL_BASE_URL=https://api.parallel.ai/v1

# Rate Limiting
PARALLEL_MAX_CONCURRENT=5
PARALLEL_DAILY_LIMIT=1000

# Caching
PARALLEL_CACHE_ENABLED=true
PARALLEL_CACHE_TTL_HOURS=48
```

```python
# app/core/config.py

class Settings(BaseSettings):
    # Parallel AI
    PARALLEL_API_KEY: str
    PARALLEL_BASE_URL: str = "https://api.parallel.ai/v1"
    PARALLEL_MAX_CONCURRENT: int = 5
    PARALLEL_DAILY_LIMIT: int = 1000
    PARALLEL_CACHE_ENABLED: bool = True
    PARALLEL_CACHE_TTL_HOURS: int = 48
```

---

## Error Handling

```python
class ParallelService:
    async def safe_task(
        self,
        objective: str,
        processor: str = "core",
        **kwargs
    ) -> Optional[TaskResult]:
        """Execute task with error handling and fallback."""

        try:
            async with self.rate_limiter:
                result = await self.client.task.create(
                    objective=objective,
                    processor=processor,
                    **kwargs
                )
                return result

        except parallel.RateLimitError:
            logger.warning("Parallel rate limit hit, queuing for retry")
            await self.queue_for_retry(objective, processor, kwargs)
            return None

        except parallel.APIError as e:
            logger.error(f"Parallel API error: {e}")
            # Return cached data if available
            cached = await self.cache.get_fallback(objective)
            if cached:
                return cached
            raise

        except Exception as e:
            logger.error(f"Unexpected error in Parallel call: {e}")
            raise
```

---

## Related Documents

- [06-renewal-intelligence.md](./06-renewal-intelligence.md) - Uses Parallel for market research
- [05-insurance-health-score.md](./05-insurance-health-score.md) - Risk enrichment for scoring
- [00-overview.md](./00-overview.md) - Phase 4 overview
