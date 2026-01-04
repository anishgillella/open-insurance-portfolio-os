"""Parallel AI Client Service.

Provides a wrapper around Parallel AI's Task API for web research.
Uses a two-step approach:
1. Parallel AI performs web research and returns rich text
2. Gemini structures the output into typed schemas

Reference: https://docs.parallel.ai
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Parallel AI API endpoints
PARALLEL_TASK_URL = "https://api.parallel.ai/v1/tasks/runs"
PARALLEL_POLL_INTERVAL = 2  # seconds between polling


class ParallelClientError(Exception):
    """Base exception for Parallel AI client errors."""
    pass


class ParallelAPIError(ParallelClientError):
    """Raised when Parallel API returns an error."""
    pass


class ParallelRateLimitError(ParallelClientError):
    """Raised when rate limit is hit."""
    pass


@dataclass
class ParallelTaskResult:
    """Result from a Parallel AI Task API call."""

    task_id: str
    status: str
    output: str  # Raw text output from research
    sources: list[dict] | None
    processor: str
    latency_ms: int
    metadata: dict | None = None


class ParallelClient:
    """Client for Parallel AI Task API.

    This client focuses on the Task API for web research.
    It returns raw text which can then be structured using an LLM.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize Parallel AI client.

        Args:
            api_key: Parallel API key. Defaults to settings.
        """
        self.api_key = api_key or settings.parallel_api_key
        self.base_url = settings.parallel_base_url
        self.default_processor = settings.parallel_default_processor

        if not self.api_key:
            logger.warning("Parallel API key not configured")

    async def research(
        self,
        objective: str,
        processor: str | None = None,
        max_wait_seconds: int = 300,
    ) -> ParallelTaskResult:
        """Execute a research task using Parallel AI.

        This method sends a research objective to Parallel AI and waits
        for the result. The output is raw text that can be structured
        by an LLM.

        Args:
            objective: The research objective/question.
            processor: Processor to use (lite, base, core, core-fast, pro, ultra).
                      Defaults to core-fast.
            max_wait_seconds: Maximum time to wait for result.

        Returns:
            ParallelTaskResult with raw text output.

        Raises:
            ParallelAPIError: If the API returns an error.
            ParallelRateLimitError: If rate limit is exceeded.
        """
        if not self.api_key:
            raise ParallelClientError("Parallel API key not configured")

        processor = processor or self.default_processor
        start_time = time.time()

        async with httpx.AsyncClient(timeout=max_wait_seconds + 30) as client:
            # Create task run
            # Parallel AI uses x-api-key header and task_spec/input format
            try:
                response = await client.post(
                    PARALLEL_TASK_URL,
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "task_spec": {
                            "output_schema": "Comprehensive research report as detailed text"
                        },
                        "input": objective,
                        "processor": processor,
                    },
                )
            except httpx.TimeoutException:
                raise ParallelAPIError("Request timed out waiting for Parallel AI")

            if response.status_code == 429:
                raise ParallelRateLimitError("Parallel AI rate limit exceeded")

            # Parallel API returns 200, 201, or 202 for success
            # 202 means task is queued and we need to poll for results
            if response.status_code not in (200, 201, 202):
                error_detail = response.text
                logger.error(f"Parallel API error: {response.status_code} - {error_detail}")
                raise ParallelAPIError(
                    f"Parallel API error: {response.status_code} - {error_detail}"
                )

            result = response.json()
            run_id = result.get("run_id") or result.get("id")
            status = result.get("status", "")

            # If status is queued or running, poll for completion
            if status in ("queued", "running", "pending") and run_id:
                logger.info(f"Task {run_id} is {status}, polling for completion...")
                result = await self._poll_for_result(client, run_id, max_wait_seconds)

            latency_ms = int((time.time() - start_time) * 1000)

            # Log the result for debugging
            logger.info(f"Parallel AI result keys: {list(result.keys())}")
            logger.debug(f"Parallel AI full result: {result}")

            # Extract output - handle different response formats
            output = ""
            sources = []

            # Try multiple possible output field names
            # Parallel AI returns output.content for the actual data
            output_data = result.get("output", {})
            if isinstance(output_data, dict):
                # Check for content field (standard Parallel AI format)
                if "content" in output_data:
                    content = output_data["content"]
                    if isinstance(content, str):
                        output = content
                    elif isinstance(content, dict):
                        # Convert dict to readable text
                        output = str(content)
                elif "text" in output_data:
                    output = output_data["text"]
                else:
                    output = str(output_data)
            elif isinstance(output_data, str):
                output = output_data
            elif result.get("result"):
                if isinstance(result["result"], str):
                    output = result["result"]
                elif isinstance(result["result"], dict):
                    output = result["result"].get("text", result["result"].get("content", str(result["result"])))
            elif result.get("response"):
                output = result["response"]
            elif result.get("text"):
                output = result["text"]
            elif result.get("content"):
                output = result["content"]

            logger.info(f"Extracted output length: {len(output)} chars")

            # Extract sources if available
            if result.get("sources"):
                sources = result["sources"]
            elif result.get("citations"):
                sources = result["citations"]

            return ParallelTaskResult(
                task_id=run_id or "",
                status=result.get("status", "completed"),
                output=output,
                sources=sources if sources else None,
                processor=processor,
                latency_ms=latency_ms,
                metadata={
                    "model": result.get("model"),
                    "tokens": result.get("tokens"),
                },
            )

    async def _poll_for_result(
        self,
        client: httpx.AsyncClient,
        run_id: str,
        max_wait_seconds: int,
    ) -> dict[str, Any]:
        """Poll for task completion and get result.

        Uses the /result endpoint which blocks until completion.

        Args:
            client: HTTP client.
            run_id: Task run ID.
            max_wait_seconds: Maximum time to wait.

        Returns:
            Completed task result with output.
        """
        # Use the /result endpoint which blocks and returns full output
        result_url = f"{PARALLEL_TASK_URL}/{run_id}/result"

        try:
            response = await client.get(
                result_url,
                headers={"x-api-key": self.api_key},
                timeout=max_wait_seconds,
            )
        except httpx.TimeoutException:
            raise ParallelAPIError(f"Task {run_id} timed out waiting for result")

        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"Result fetch error: {response.status_code} - {error_detail}")
            raise ParallelAPIError(f"Failed to get result: {response.status_code}")

        result = response.json()
        status = result.get("run", {}).get("status", result.get("status", ""))

        if status in ("failed", "error", "cancelled"):
            error_msg = result.get("error", result.get("message", "Task failed"))
            raise ParallelAPIError(f"Task failed: {error_msg}")

        return result

    async def research_market_conditions(
        self,
        property_type: str,
        state: str,
        tiv: float | None = None,
        carrier: str | None = None,
    ) -> ParallelTaskResult:
        """Research current insurance market conditions.

        Args:
            property_type: Type of property (multifamily, office, retail, etc.)
            state: State code (TX, CA, etc.)
            tiv: Total insured value (optional)
            carrier: Current carrier name (optional)

        Returns:
            ParallelTaskResult with market research.
        """
        tiv_str = f"${tiv:,.0f}" if tiv else "not specified"
        carrier_str = carrier if carrier else "not specified"

        objective = f"""Research current commercial property insurance market conditions for:
- Property type: {property_type}
- Location: {state}
- Total Insured Value: {tiv_str}
- Current carrier: {carrier_str}

Provide comprehensive information on:
1. Current rate trends (percentage change year-over-year) for this property type in this state
2. Key factors driving rate changes (CAT losses, reinsurance costs, inflation, etc.)
3. Major carrier appetite for this segment (which carriers are expanding, stable, or contracting)
4. Predicted rate changes for the next 6-12 months
5. Any regulatory changes or market developments affecting coverage requirements
6. Premium benchmarks or rate per square foot if available
7. Recent catastrophe losses or claims trends affecting this market

Focus on the most recent data available (2024-2025). Include specific numbers and cite sources."""

        return await self.research(objective, processor="core-fast")

    async def research_property_risk(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
    ) -> ParallelTaskResult:
        """Research property risk data from public sources.

        Args:
            address: Street address
            city: City name
            state: State code
            zip_code: ZIP code

        Returns:
            ParallelTaskResult with property risk data.
        """
        full_address = f"{address}, {city}, {state} {zip_code}"

        objective = f"""Research property risk data for: {full_address}

Find the following information from public sources:
1. FEMA flood zone designation and flood risk
2. Distance to nearest fire station
3. Fire protection class (ISO PPC rating) if available
4. Recent building permits or violations from local records
5. Historical weather events in the area (hurricanes, tornadoes, hail, wildfires)
6. Crime statistics and safety index for the area
7. Environmental hazards nearby (Superfund sites, industrial facilities)
8. Earthquake risk zone if applicable
9. Any notable infrastructure issues (aging utilities, drainage problems)

Use official government sources (FEMA, local municipalities, EPA) where possible.
Include specific data points and source citations."""

        return await self.research(objective, processor="core-fast")

    async def research_carrier(
        self,
        carrier_name: str,
        property_type: str | None = None,
    ) -> ParallelTaskResult:
        """Research carrier financial strength and market position.

        Args:
            carrier_name: Name of the insurance carrier
            property_type: Optional property type for specialty focus

        Returns:
            ParallelTaskResult with carrier research.
        """
        property_context = f" for {property_type} insurance" if property_type else ""

        objective = f"""Research the insurance carrier: {carrier_name}

Find comprehensive information on:
1. Current A.M. Best rating and outlook
2. S&P and Moody's ratings if available
3. Recent financial performance and stability
4. Market specialty areas and lines of business
5. Commercial property insurance appetite{property_context}
6. Recent news including:
   - Claims handling reputation
   - Leadership changes
   - Market expansions or exits
   - Mergers/acquisitions
7. Customer satisfaction ratings or reviews
8. Geographic focus and state licenses
9. Any regulatory actions or concerns

Provide specific ratings, dates, and source citations."""

        return await self.research(objective, processor="core-fast")

    async def research_lender_requirements(
        self,
        lender_name: str,
        loan_type: str | None = None,
    ) -> ParallelTaskResult:
        """Research lender-specific insurance requirements.

        Args:
            lender_name: Name of the lender
            loan_type: Optional loan type (conventional, FHA, Fannie Mae, etc.)

        Returns:
            ParallelTaskResult with lender requirements.
        """
        loan_context = f" for {loan_type} loans" if loan_type else ""

        objective = f"""Research the insurance requirements for {lender_name}{loan_context}.

Find their requirements for:
1. Minimum property coverage (replacement cost percentage, typically 100%)
2. Minimum general liability limits (per occurrence and aggregate)
3. Umbrella/excess liability requirements
4. Maximum deductible allowed (as percentage of TIV or flat dollar)
5. Flood insurance requirements (when required, minimum coverage)
6. Wind/named storm requirements for coastal properties
7. Required endorsements:
   - Mortgagee/loss payee clause requirements
   - Waiver of subrogation
   - Notice of cancellation requirements (typically 30 days)
8. Acceptable carrier ratings (A.M. Best minimum)
9. Certificate of insurance requirements
10. Special requirements for earthquake zones

Look for official lender guidelines, seller/servicer guides, or underwriting requirements.
Include specific numbers, thresholds, and source citations."""

        return await self.research(objective, processor="core-fast")


def get_parallel_client() -> ParallelClient:
    """Factory function to create ParallelClient.

    Returns:
        ParallelClient instance.
    """
    return ParallelClient()
