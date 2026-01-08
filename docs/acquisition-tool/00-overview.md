# Acquisition Calculator Tool

## Overview

The Acquisition Calculator is an **AI-powered insurance premium estimation tool** for properties being considered for acquisition. It helps CRE investors and insurance professionals understand expected insurance costs before purchasing a property.

**This is a new innovation that brings proactive pricing intelligence to the acquisition process.**

---

## Why This Matters

### Current State (What Exists)
- Buyers have no idea what insurance will cost until after acquisition
- Brokers provide quotes reactively, often delaying deals
- No visibility into comparable property premiums
- Risk factors are discovered too late

### The Gap
Property acquirers currently:
- Make investment decisions without insurance cost data
- Get surprised by high premiums after purchase
- Can't compare potential acquisitions on insurance basis
- Have no visibility into risk factors affecting premiums

### Our Innovation
The Acquisition Calculator provides:
1. **AI-Powered Comparables** - LLM identifies similar properties for premium estimation
2. **Premium Range Estimates** - Low/Medium/High premium predictions
3. **Risk Factor Analysis** - AI identifies risks from property characteristics and notes
4. **Unique Property Detection** - Routes unusual properties to human consultants

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ACQUISITION CALCULATOR ENGINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     USER INPUT LAYER                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Property   │  │   Building   │  │   Financial  │              │   │
│  │  │   Address    │  │   Details    │  │    Data      │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AI ANALYSIS ENGINE                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  Comparable  │  │    Risk      │  │  Uniqueness  │              │   │
│  │  │   Finder     │  │   Analyzer   │  │   Detector   │              │   │
│  │  │    (LLM)     │  │    (LLM)     │  │    (LLM)     │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    OUTPUT GENERATION                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Premium    │  │  Comparables │  │     Risk     │              │   │
│  │  │   Ranges     │  │    Chart     │  │   Factors    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## User Interface

### Input Form (Left Panel)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Address | Text + Search | Yes | Property street address |
| Link | URL | No | Optional listing URL |
| Unit Count | Number | Yes | Total number of units |
| Vintage | Number | Yes | Year built |
| Stories | Number | Yes | Number of floors |
| Total Buildings | Number | Yes | Number of buildings |
| Total SF | Number | Yes | Gross square footage |
| Current Occupancy | Percentage | Yes | Current occupancy rate |
| Estimated Annual Income | Currency | Yes | Gross annual income |
| Notes | Textarea | No | Additional property details |

### Results Panel (Right Panel)
1. **Premium Range Bar** - Visual indicator showing Low/Medium/High ranges
2. **Premium Message** - "This property is likely to be within the medium range ($200-$800)"
3. **Comparables Chart** - Scatter plot showing premium/unit over time
4. **Risk Factors Grid** - 6 risk factor badges with severity indicators
5. **Unique Property Modal** - Shown when property can't be reliably estimated

---

## Features

### 1. AI-Powered Comparable Matching

The LLM analyzes all candidate properties and scores similarity based on:
- Geographic proximity and market similarity
- Building vintage and construction era
- Size (units, square footage, buildings)
- Property type and use
- Risk characteristics from notes

**Unlike fixed criteria, the LLM can:**
- Weigh multiple factors intelligently
- Understand context ("next to a lakefront" → flood risk)
- Explain WHY properties are comparable
- Handle edge cases gracefully

### 2. Premium Range Estimation

Based on comparable properties, calculate:
```json
{
  "premium_range": {
    "low": 100,
    "mid": 200,
    "high": 800
  },
  "premium_range_label": "medium range ($200-$800)",
  "confidence": "high"
}
```

### 3. Risk Factor Analysis

The LLM identifies applicable risks:
| Risk Factor | Detection Method |
|-------------|------------------|
| Flood Zone | Address analysis, notes mentioning water |
| Wind Exposure | Coastal proximity, hurricane zones |
| Fire Exposure | Wildfire areas, fire station distance |
| Vintage Wiring | Buildings pre-1970 |
| Vintage Plumbing | Buildings pre-1970 |
| Tort Environment | Litigation-heavy states (FL, CA, NY) |

### 4. Unique Property Detection

When the LLM determines insufficient comparable data:
- Average similarity score < 50, OR
- Fewer than 3 properties with score > 60

**Response:**
```json
{
  "is_unique": true,
  "uniqueness_reason": "This lakefront property with 1920s vintage wiring is unlike any in our portfolio.",
  "preliminary_estimate": { "low": 180, "high": 450, "confidence": "low" },
  "message": "We need our insurance consultants to put their eyes on it and will circulate an email with estimates in the next 24 hours."
}
```

---

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 00 | [Overview](./00-overview.md) | This document |
| 01 | [Data Model](./01-data-model.md) | Schemas and database design |
| 02 | [LLM Service](./02-llm-service.md) | AI integration patterns |
| 03 | [API Design](./03-api-design.md) | Endpoint specifications |
| 04 | [Frontend Components](./04-frontend-components.md) | UI implementation |
| 05 | [Implementation Phases](./05-implementation-phases.md) | Step-by-step build plan |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Calculation response time | < 5 seconds | API response time |
| Comparable accuracy | > 80% | User feedback on relevance |
| Premium estimate accuracy | Within 30% | Compare to actual quotes |
| Unique property detection | > 90% | False positive/negative rate |
| User satisfaction | > 4/5 stars | Post-calculation survey |

---

## Dependencies

### Internal
- Property data with premium information (from existing portfolio)
- OpenRouter API key (for LLM calls)
- Mock data for initial development

### External Services
- **OpenRouter + Gemini 2.5 Flash** - LLM for analysis
- **Google Places API** (future) - Address geocoding

---

## Next Steps

1. Review [01-data-model.md](./01-data-model.md) for schema definitions
2. Review [02-llm-service.md](./02-llm-service.md) for AI integration
3. Review [05-implementation-phases.md](./05-implementation-phases.md) for build plan
