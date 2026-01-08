# LLM Service Integration

## Overview

The Acquisition Calculator uses an **AI-first approach** where the LLM handles the core intelligence:
1. **Comparable Matching** - Score and rank similar properties
2. **Risk Analysis** - Identify risks from property characteristics and notes
3. **Uniqueness Detection** - Determine when to route to human consultants

This follows the same patterns used in existing services (`classification_service.py`, `renewal_forecast_service.py`).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  AcquisitionsLLMService                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  _call_llm()    │    │   OpenRouter    │                    │
│  │  Retry Logic    │───▶│  Gemini 2.5     │                    │
│  │  JSON Parsing   │    │    Flash        │                    │
│  └─────────────────┘    └─────────────────┘                    │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    PUBLIC METHODS                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │    find_     │  │   analyze_   │  │   assess_    │  │   │
│  │  │ comparable_  │  │    risk_     │  │  uniqueness  │  │   │
│  │  │ properties() │  │  factors()   │  │     ()       │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Service Implementation

### File: `backend/app/services/acquisitions_llm_service.py`

```python
import httpx
import json
import asyncio
import logging
from typing import Any

from app.core.config import settings
from app.schemas.acquisitions import (
    AcquisitionCalculateRequest,
    RiskFactor,
    ScoredComparable,
)

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


class AcquisitionsLLMService:
    """AI-powered acquisition analysis using LLM.

    Follows existing patterns from classification_service.py
    and renewal_forecast_service.py.
    """

    MAX_RETRIES = 3
    INITIAL_DELAY = 1.0
    BACKOFF_MULTIPLIER = 2.0

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.openrouter_api_key

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Make LLM call with retry logic and JSON parsing.

        Args:
            system_prompt: System role instructions
            user_prompt: User message with task details
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (lower = more deterministic)

        Returns:
            Parsed JSON response from LLM

        Raises:
            Exception: After all retries exhausted
        """
        delay = self.INITIAL_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        OPENROUTER_URL,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://open-insurance.app",
                            "X-Title": "Open Insurance",
                        },
                        json={
                            "model": MODEL,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "response_format": {"type": "json_object"},
                        },
                    )

                    if response.status_code != 200:
                        logger.warning(
                            f"LLM API error: {response.status_code} - {response.text}"
                        )
                        raise Exception(f"API error: {response.status_code}")

                    content = response.json()["choices"][0]["message"]["content"]
                    return json.loads(content)

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    delay *= self.BACKOFF_MULTIPLIER
                else:
                    raise

            except Exception as e:
                logger.warning(f"LLM call failed on attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    delay *= self.BACKOFF_MULTIPLIER
                else:
                    raise

    def _format_candidates(self, candidates: list[dict]) -> str:
        """Format candidate properties for LLM prompt."""
        lines = []
        for i, prop in enumerate(candidates, 1):
            lines.append(f"""
Property {i}:
- ID: {prop.get('id', 'unknown')}
- Name: {prop.get('name', 'Unknown')}
- Address: {prop.get('address', {}).get('street', '')}, {prop.get('address', {}).get('city', '')}, {prop.get('address', {}).get('state', '')}
- Year Built: {prop.get('year_built', 'Unknown')}
- Units: {prop.get('total_units', 0)}
- Buildings: {prop.get('total_buildings', 1)}
- Premium: ${prop.get('total_premium', 0):,.0f}
- Premium/Unit: ${prop.get('premium_per_unit', 0):,.0f}
""")
        return "\n".join(lines)

    async def find_comparable_properties(
        self,
        target: AcquisitionCalculateRequest,
        candidates: list[dict],
    ) -> dict[str, Any]:
        """Score and rank comparable properties using LLM.

        The LLM evaluates each candidate property against the target
        and assigns a similarity score (0-100) with reasoning.

        Args:
            target: The property being evaluated for acquisition
            candidates: List of existing properties to compare against

        Returns:
            {
                "comparables": [{"property_id": ..., "score": 85, "reasoning": ...}],
                "overall_assessment": "..."
            }
        """
        system_prompt = """You are an expert commercial real estate insurance analyst.
Your task is to identify comparable properties for insurance premium estimation.

When scoring similarity, consider:
1. Geographic proximity and market similarity (same state/region)
2. Building vintage/age (similar construction era)
3. Size (units, square footage, number of buildings)
4. Property type and use characteristics
5. Risk characteristics mentioned in notes

Score each property 0-100 where:
- 90-100: Excellent match (nearly identical characteristics)
- 70-89: Good match (most characteristics align)
- 50-69: Fair match (some characteristics align)
- Below 50: Poor match (significant differences)

Always return valid JSON."""

        user_prompt = f"""Score each candidate property on similarity to this target property for insurance premium estimation.

TARGET PROPERTY:
- Address: {target.address}
- Year Built: {target.vintage}
- Units: {target.unit_count}
- Square Feet: {target.total_sf:,}
- Buildings: {target.total_buildings}
- Stories: {target.stories}
- Occupancy: {target.current_occupancy_pct}%
- Estimated Annual Income: ${target.estimated_annual_income:,.0f}
- Notes: {target.notes or 'None provided'}

CANDIDATE PROPERTIES:
{self._format_candidates(candidates)}

Return JSON in this exact format:
{{
  "comparables": [
    {{
      "property_id": "prop-1",
      "score": 85,
      "reasoning": "Similar vintage (2005 vs 2002), same state (IN), comparable unit count"
    }}
  ],
  "overall_assessment": "Found 5 strong comparable properties in the Indiana market with similar vintage and size characteristics."
}}

Sort comparables by score descending. Include all candidates with score >= 40."""

        return await self._call_llm(system_prompt, user_prompt)

    async def analyze_risk_factors(
        self,
        target: AcquisitionCalculateRequest,
    ) -> dict[str, Any]:
        """Identify risk factors from property characteristics using LLM.

        The LLM analyzes the property details and notes to identify
        insurance risk factors that would affect premiums.

        Args:
            target: The property being evaluated

        Returns:
            {
                "risk_factors": [
                    {"name": "Flood Zone", "severity": "warning", "reason": "..."}
                ]
            }
        """
        system_prompt = """You are an insurance underwriter analyzing property risk factors.
Identify risks that would affect commercial property insurance premiums.

Risk categories to consider:
1. Flood Zone - Proximity to water bodies, flood plains, mentions of lakefront/riverfront
2. Wind Exposure - Coastal areas, hurricane zones, high-wind regions
3. Fire Exposure - Wildfire areas, distance to fire stations, fire-prone regions
4. Vintage Wiring - Buildings pre-1970 often have outdated/dangerous electrical systems
5. Vintage Plumbing - Buildings pre-1970 may have galvanized/lead pipes
6. Tort Environment - Litigation-heavy states (FL, CA, NY, TX) increase liability costs

Severity levels:
- "critical": Major risk requiring immediate attention
- "warning": Moderate risk that affects premium
- "info": Minor consideration

Only include risk factors that actually apply based on the evidence provided.
Always return valid JSON."""

        user_prompt = f"""Analyze this property for insurance risk factors:

PROPERTY DETAILS:
- Address: {target.address}
- Year Built: {target.vintage}
- Stories: {target.stories}
- Buildings: {target.total_buildings}
- Notes: {target.notes or 'None provided'}

Based on these details, identify applicable risk factors.

Return JSON in this exact format:
{{
  "risk_factors": [
    {{
      "name": "Flood Zone",
      "severity": "warning",
      "reason": "Address mentions lakefront location, indicating proximity to water"
    }},
    {{
      "name": "Vintage Wiring",
      "severity": "warning",
      "reason": "Building constructed in 1965, before modern electrical codes"
    }}
  ]
}}

Only include risks that have clear evidence from the provided details. If no significant risks are identified, return an empty array."""

        return await self._call_llm(
            system_prompt,
            user_prompt,
            max_tokens=1000,
            temperature=0.2,
        )

    def assess_uniqueness(
        self,
        comparables_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Determine if property is too unique for automated pricing.

        This is a deterministic function (no LLM call) that evaluates
        the quality of comparable properties found.

        Criteria for "unique":
        - Average similarity score < 50, OR
        - Fewer than 3 properties with score > 60

        Args:
            comparables_result: Output from find_comparable_properties()

        Returns:
            {
                "is_unique": bool,
                "reason": str | None,
                "confidence": "high" | "medium" | "low"
            }
        """
        comparables = comparables_result.get("comparables", [])

        if not comparables:
            return {
                "is_unique": True,
                "reason": "No comparable properties found in the portfolio.",
                "confidence": "low",
            }

        # Calculate metrics
        scores = [c.get("score", 0) for c in comparables]
        top_scores = scores[:5]  # Consider top 5
        avg_score = sum(top_scores) / len(top_scores) if top_scores else 0
        good_matches = len([s for s in top_scores if s > 60])

        # Determine uniqueness
        if avg_score < 50 or good_matches < 3:
            return {
                "is_unique": True,
                "reason": f"Property characteristics are unusual. Best comparables have low similarity (avg: {avg_score:.0f}/100, only {good_matches} good matches).",
                "confidence": "low",
            }

        # Determine confidence based on match quality
        if avg_score >= 75 and good_matches >= 4:
            confidence = "high"
        elif avg_score >= 60 and good_matches >= 3:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "is_unique": False,
            "reason": None,
            "confidence": confidence,
        }


# Singleton pattern (following existing service patterns)
_acquisitions_llm_service: AcquisitionsLLMService | None = None


def get_acquisitions_llm_service() -> AcquisitionsLLMService:
    """Get or create the AcquisitionsLLMService singleton."""
    global _acquisitions_llm_service
    if _acquisitions_llm_service is None:
        _acquisitions_llm_service = AcquisitionsLLMService()
    return _acquisitions_llm_service
```

---

## Prompt Engineering

### Comparable Matching Prompt

**Goal:** Get accurate similarity scores with reasoning.

**Key Elements:**
1. Clear scoring rubric (0-100 scale with definitions)
2. Explicit factors to consider
3. Structured JSON output format
4. Request for reasoning (enables debugging)

**Example Input:**
```
TARGET PROPERTY:
- Address: 123 East Street, Fort Wayne, IN 46802
- Year Built: 2002
- Units: 150
- ...

CANDIDATE PROPERTIES:
Property 1:
- ID: prop-1
- Name: Shoaff Park Apartments
- Address: Fort Wayne, IN
- Year Built: 1998
- Units: 156
- ...
```

**Example Output:**
```json
{
  "comparables": [
    {
      "property_id": "prop-1",
      "score": 88,
      "reasoning": "Same city (Fort Wayne), similar vintage (1998 vs 2002), nearly identical unit count (156 vs 150)"
    }
  ],
  "overall_assessment": "Found excellent comparable in same market with matching characteristics."
}
```

### Risk Analysis Prompt

**Goal:** Extract relevant risks with evidence-based reasoning.

**Key Elements:**
1. Defined risk categories
2. Severity level definitions
3. Requirement for evidence/reasoning
4. Instruction to omit non-applicable risks

**Example Input:**
```
PROPERTY DETAILS:
- Address: 123 Lakefront Dr, Miami, FL
- Year Built: 1965
- Notes: Next to a lakefront, original plumbing
```

**Example Output:**
```json
{
  "risk_factors": [
    {
      "name": "Flood Zone",
      "severity": "critical",
      "reason": "Lakefront location in Miami indicates high flood exposure"
    },
    {
      "name": "Vintage Wiring",
      "severity": "warning",
      "reason": "1965 construction predates modern electrical codes"
    },
    {
      "name": "Vintage Plumbing",
      "severity": "warning",
      "reason": "Notes mention 'original plumbing' from 1965"
    },
    {
      "name": "Tort Environment",
      "severity": "warning",
      "reason": "Florida is a high-litigation state for property claims"
    }
  ]
}
```

---

## Error Handling

### Retry Strategy

```
Attempt 1: Try immediately
  ↓ (fail)
Wait 1.0 seconds
  ↓
Attempt 2: Retry
  ↓ (fail)
Wait 2.0 seconds
  ↓
Attempt 3: Final attempt
  ↓ (fail)
Raise exception
```

### JSON Parsing Fallback

If JSON parsing fails, attempt to extract JSON from response:

```python
try:
    return json.loads(content)
except json.JSONDecodeError:
    # Try to extract JSON from markdown code blocks
    import re
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    if json_match:
        return json.loads(json_match.group(1))
    # Try to find raw JSON object
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        return json.loads(json_match.group())
    raise
```

### Default Responses

If LLM fails completely, return safe defaults:

```python
# For comparables
default_comparables = {
    "comparables": [],
    "overall_assessment": "Unable to analyze comparables at this time."
}

# For risk factors
default_risks = {
    "risk_factors": []
}
```

---

## Testing

### Unit Tests

```python
import pytest
from app.services.acquisitions_llm_service import AcquisitionsLLMService

@pytest.fixture
def service():
    return AcquisitionsLLMService(api_key="test-key")

def test_format_candidates(service):
    candidates = [
        {"id": "1", "name": "Test Property", "year_built": 2000, "total_units": 100}
    ]
    result = service._format_candidates(candidates)
    assert "Test Property" in result
    assert "2000" in result

def test_assess_uniqueness_with_good_matches(service):
    comparables = {
        "comparables": [
            {"property_id": "1", "score": 85},
            {"property_id": "2", "score": 78},
            {"property_id": "3", "score": 72},
            {"property_id": "4", "score": 65},
        ]
    }
    result = service.assess_uniqueness(comparables)
    assert result["is_unique"] is False
    assert result["confidence"] in ["high", "medium"]

def test_assess_uniqueness_with_poor_matches(service):
    comparables = {
        "comparables": [
            {"property_id": "1", "score": 45},
            {"property_id": "2", "score": 38},
        ]
    }
    result = service.assess_uniqueness(comparables)
    assert result["is_unique"] is True
    assert result["confidence"] == "low"
```

### Integration Tests

```python
@pytest.mark.integration
async def test_find_comparable_properties():
    service = get_acquisitions_llm_service()

    request = AcquisitionCalculateRequest(
        address="123 Test St, Fort Wayne, IN",
        unit_count=150,
        vintage=2000,
        stories=3,
        total_buildings=3,
        total_sf=40000,
        current_occupancy_pct=80,
        estimated_annual_income=1000000,
    )

    candidates = [...]  # Mock properties

    result = await service.find_comparable_properties(request, candidates)

    assert "comparables" in result
    assert "overall_assessment" in result
```

---

## Related Documents

- [01-data-model.md](./01-data-model.md) - Schema definitions
- [03-api-design.md](./03-api-design.md) - API endpoint using this service
- [05-implementation-phases.md](./05-implementation-phases.md) - Build order
