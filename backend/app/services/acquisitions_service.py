"""Acquisitions Service - Orchestrates acquisition premium calculation.

This module provides the main service layer for the acquisition calculator,
combining LLM analysis with property data to generate premium estimates.
"""

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.acquisitions import (
    AcquisitionCalculateRequest,
    AcquisitionCalculateResponse,
    ComparableProperty,
    PremiumRange,
    RiskFactor,
)
from app.services.acquisitions_llm_service import get_acquisitions_llm_service

logger = logging.getLogger(__name__)

# Mock properties data for initial development
# This matches the structure from frontend/src/lib/mock-data.ts
MOCK_PROPERTIES = [
    {
        "id": "prop-1",
        "name": "Shoaff Park Apartments",
        "address": {
            "street": "2500 Shoaff Park Dr",
            "city": "Fort Wayne",
            "state": "IN",
            "zip": "46825",
        },
        "latitude": 41.1178,
        "longitude": -85.1047,
        "property_type": "Multi-Family",
        "total_units": 156,
        "total_buildings": 8,
        "year_built": 1998,
        "total_insured_value": 32500000,
        "total_premium": 285000,
    },
    {
        "id": "prop-2",
        "name": "Buffalo Run Estates",
        "address": {
            "street": "1200 Buffalo Run Blvd",
            "city": "Fort Wayne",
            "state": "IN",
            "zip": "46804",
        },
        "latitude": 41.0534,
        "longitude": -85.2012,
        "property_type": "Multi-Family",
        "total_units": 220,
        "total_buildings": 12,
        "year_built": 2005,
        "total_insured_value": 45000000,
        "total_premium": 412000,
    },
    {
        "id": "prop-3",
        "name": "Lake Sheri Villas",
        "address": {
            "street": "800 Lake Sheri Dr",
            "city": "Fort Wayne",
            "state": "IN",
            "zip": "46815",
        },
        "latitude": 41.0891,
        "longitude": -85.0523,
        "property_type": "Multi-Family",
        "total_units": 88,
        "total_buildings": 4,
        "year_built": 2012,
        "total_insured_value": 22000000,
        "total_premium": 178000,
    },
    {
        "id": "prop-4",
        "name": "Riverside Commons",
        "address": {
            "street": "450 Riverside Dr",
            "city": "Indianapolis",
            "state": "IN",
            "zip": "46202",
        },
        "latitude": 39.7784,
        "longitude": -86.1621,
        "property_type": "Mixed-Use",
        "total_units": 180,
        "total_buildings": 6,
        "year_built": 2018,
        "total_insured_value": 55000000,
        "total_premium": 485000,
    },
    {
        "id": "prop-5",
        "name": "Maple Grove Apartments",
        "address": {
            "street": "3200 Maple Grove Ln",
            "city": "Carmel",
            "state": "IN",
            "zip": "46032",
        },
        "latitude": 39.9784,
        "longitude": -86.1180,
        "property_type": "Multi-Family",
        "total_units": 144,
        "total_buildings": 6,
        "year_built": 2015,
        "total_insured_value": 38000000,
        "total_premium": 325000,
    },
    {
        "id": "prop-6",
        "name": "Downtown Lofts",
        "address": {
            "street": "100 Main St",
            "city": "Fort Wayne",
            "state": "IN",
            "zip": "46802",
        },
        "latitude": 41.0793,
        "longitude": -85.1394,
        "property_type": "Multi-Family",
        "total_units": 64,
        "total_buildings": 1,
        "year_built": 1920,
        "total_insured_value": 18000000,
        "total_premium": 195000,
    },
    {
        "id": "prop-7",
        "name": "Eastwood Manor",
        "address": {
            "street": "5500 Eastwood Rd",
            "city": "Fort Wayne",
            "state": "IN",
            "zip": "46816",
        },
        "latitude": 41.0456,
        "longitude": -85.0678,
        "property_type": "Multi-Family",
        "total_units": 200,
        "total_buildings": 10,
        "year_built": 2008,
        "total_insured_value": 42000000,
        "total_premium": 375000,
    },
]


class AcquisitionsService:
    """Orchestrates acquisition calculation using LLM and data services.

    This service coordinates:
    1. Fetching candidate properties (mock or database)
    2. LLM-based comparable matching
    3. LLM-based risk analysis
    4. Premium range calculation
    5. Response assembly
    """

    def __init__(self, session: AsyncSession | None = None):
        """Initialize the acquisitions service.

        Args:
            session: Optional database session. If None, uses mock data.
        """
        self.session = session
        self.llm_service = get_acquisitions_llm_service()

    async def calculate_acquisition(
        self,
        request: AcquisitionCalculateRequest,
    ) -> AcquisitionCalculateResponse:
        """Calculate acquisition premium estimate.

        Flow:
        1. Get candidate properties (mock or DB)
        2. LLM scores comparables
        3. LLM analyzes risk factors
        4. Assess uniqueness
        5. Calculate premium ranges
        6. Build response

        Args:
            request: The acquisition calculation request

        Returns:
            Complete acquisition calculation response
        """
        logger.info(f"Calculating acquisition for: {request.address}")

        # 1. Get candidate properties
        candidates = await self._get_candidate_properties()
        logger.info(f"Found {len(candidates)} candidate properties")

        # 2. LLM scores and ranks comparables
        comparables_result = await self.llm_service.find_comparable_properties(
            target=request,
            candidates=candidates,
        )
        logger.info(
            f"LLM scored {len(comparables_result.get('comparables', []))} comparables"
        )

        # 3. LLM identifies risk factors
        risks_result = await self.llm_service.analyze_risk_factors(target=request)
        logger.info(
            f"LLM identified {len(risks_result.get('risk_factors', []))} risk factors"
        )

        # 4. Assess uniqueness (deterministic based on LLM scores)
        uniqueness = self.llm_service.assess_uniqueness(comparables_result)
        logger.info(
            f"Uniqueness assessment: is_unique={uniqueness['is_unique']}, "
            f"confidence={uniqueness['confidence']}"
        )

        # 5. Calculate premium ranges
        premium_range = None
        preliminary_estimate = None
        premium_range_label = None
        message = None

        if uniqueness["is_unique"]:
            # Unique property - provide preliminary estimate + consultant message
            preliminary_estimate = self._calculate_preliminary_estimate(candidates)
            message = (
                "This property is a bit unique. We need our insurance consultants "
                "to put their eyes on it and will circulate an email with estimates "
                "in the next 24 hours. Thanks for being a valued partner of Open Insurance."
            )
        else:
            # Normal property - calculate from comparables
            premium_range = self._calculate_premium_range(
                comparables_result, candidates
            )
            premium_range_label = self._get_premium_range_label(premium_range)
            message = f"This property is likely to be within the {premium_range_label}."

        # 6. Build comparable property list
        comparable_list = self._build_comparable_list(comparables_result, candidates)

        # 7. Build risk factor list
        risk_list = self._build_risk_list(risks_result)

        return AcquisitionCalculateResponse(
            is_unique=uniqueness["is_unique"],
            uniqueness_reason=uniqueness.get("reason"),
            confidence=uniqueness["confidence"],
            premium_range=premium_range,
            premium_range_label=premium_range_label,
            preliminary_estimate=preliminary_estimate,
            message=message,
            comparables=comparable_list,
            risk_factors=risk_list,
            llm_explanation=comparables_result.get("overall_assessment"),
        )

    async def _get_candidate_properties(self) -> list[dict]:
        """Get candidate properties for comparison.

        For MVP, uses mock data. Later will query database.

        Returns:
            List of property dictionaries with calculated premium_per_unit
        """
        # TODO: Replace with actual database query when ready
        # if self.session:
        #     properties = await self.property_repo.list_with_summary(limit=100)
        #     return self._convert_properties_to_dict(properties)

        # For now, use mock data with calculated premium_per_unit
        candidates = []
        for prop in MOCK_PROPERTIES:
            total_units = prop.get("total_units", 0)
            total_premium = prop.get("total_premium", 0)

            candidate = {
                **prop,
                "premium_per_unit": (
                    total_premium / total_units if total_units > 0 else 0
                ),
            }
            candidates.append(candidate)

        return candidates

    def _calculate_premium_range(
        self,
        comparables_result: dict,
        candidates: list[dict],
    ) -> PremiumRange:
        """Calculate premium range from top comparables using weighted averaging.

        Uses similarity scores as weights - higher scoring comparables have
        more influence on the premium estimate.

        Args:
            comparables_result: LLM scoring results with similarity scores
            candidates: All candidate properties

        Returns:
            PremiumRange with low/mid/high estimates
        """
        scored = comparables_result.get("comparables", [])

        # Create a lookup map for candidates by ID
        candidates_map = {c["id"]: c for c in candidates}

        # Get premium/unit and scores for top comparables
        weighted_data = []
        for comp in scored[:10]:  # Top 10
            prop_id = comp.get("property_id")
            score = comp.get("score", 50)

            if prop_id in candidates_map:
                premium = candidates_map[prop_id].get("premium_per_unit", 0)
                if premium > 0 and score > 0:
                    weighted_data.append({
                        "premium": premium,
                        "score": score,
                        "weight": score / 100,  # Normalize to 0-1
                    })

        if not weighted_data:
            # Fallback to all candidates (unweighted)
            premiums = [
                c.get("premium_per_unit", 0)
                for c in candidates
                if c.get("premium_per_unit", 0) > 0
            ]
            if not premiums:
                return PremiumRange(low=Decimal(0), mid=Decimal(0), high=Decimal(0))

            sorted_premiums = sorted(premiums)
            return PremiumRange(
                low=Decimal(str(round(sorted_premiums[0], 2))),
                mid=Decimal(str(round(sum(premiums) / len(premiums), 2))),
                high=Decimal(str(round(sorted_premiums[-1], 2))),
            )

        # Calculate weighted average for mid-point
        total_weight = sum(d["weight"] for d in weighted_data)
        if total_weight > 0:
            weighted_mid = sum(
                d["premium"] * d["weight"] for d in weighted_data
            ) / total_weight
        else:
            weighted_mid = sum(d["premium"] for d in weighted_data) / len(weighted_data)

        # Calculate low/high from premium distribution
        premiums = [d["premium"] for d in weighted_data]
        sorted_premiums = sorted(premiums)

        # Use percentiles for more robust low/high estimates
        n = len(sorted_premiums)
        if n >= 5:
            # 20th and 80th percentile for tighter range
            low_idx = max(0, int(n * 0.2))
            high_idx = min(n - 1, int(n * 0.8))
            low = sorted_premiums[low_idx]
            high = sorted_premiums[high_idx]
        else:
            # For small samples, use min/max
            low = sorted_premiums[0]
            high = sorted_premiums[-1]

        # Ensure mid is within range
        mid = max(low, min(high, weighted_mid))

        logger.info(
            f"Premium calculation: {len(weighted_data)} comparables, "
            f"weighted_mid=${weighted_mid:.0f}, range=${low:.0f}-${high:.0f}"
        )

        return PremiumRange(
            low=Decimal(str(round(low, 2))),
            mid=Decimal(str(round(mid, 2))),
            high=Decimal(str(round(high, 2))),
        )

    def _calculate_preliminary_estimate(
        self,
        candidates: list[dict],
    ) -> PremiumRange:
        """Calculate preliminary estimate for unique properties.

        Uses wider percentile ranges to reflect uncertainty.

        Args:
            candidates: All candidate properties

        Returns:
            PremiumRange with wider low/high bounds
        """
        premiums = [
            c.get("premium_per_unit", 0)
            for c in candidates
            if c.get("premium_per_unit", 0) > 0
        ]

        if not premiums:
            return PremiumRange(low=Decimal(0), mid=Decimal(0), high=Decimal(0))

        # Use wider range for uncertainty
        sorted_premiums = sorted(premiums)
        n = len(sorted_premiums)

        # 10th and 90th percentile for wider range
        low_idx = max(0, int(n * 0.1))
        high_idx = min(n - 1, int(n * 0.9))

        low = sorted_premiums[low_idx]
        high = sorted_premiums[high_idx]
        mid = sum(premiums) / len(premiums)

        return PremiumRange(
            low=Decimal(str(round(low, 2))),
            mid=Decimal(str(round(mid, 2))),
            high=Decimal(str(round(high, 2))),
        )

    def _get_premium_range_label(self, premium_range: PremiumRange) -> str:
        """Generate human-readable premium range label.

        Args:
            premium_range: The calculated premium range

        Returns:
            Human-readable description like "medium range ($1,500-$2,500)"
        """
        return f"medium range (${premium_range.low:,.0f}-${premium_range.high:,.0f})"

    def _build_comparable_list(
        self,
        comparables_result: dict,
        candidates: list[dict],
    ) -> list[ComparableProperty]:
        """Build list of comparable properties for response.

        Args:
            comparables_result: LLM scoring results
            candidates: All candidate properties

        Returns:
            List of ComparableProperty objects
        """
        result = []
        scored = comparables_result.get("comparables", [])

        # Create a lookup map for candidates by ID
        candidates_map = {c["id"]: c for c in candidates}

        for comp in scored[:10]:  # Top 10
            prop_id = comp.get("property_id")

            if prop_id not in candidates_map:
                continue

            c = candidates_map[prop_id]
            address = c.get("address", {})

            if isinstance(address, dict):
                address_str = f"{address.get('city', '')}, {address.get('state', '')}"
            else:
                address_str = str(address)

            result.append(
                ComparableProperty(
                    property_id=prop_id,
                    name=c.get("name", "Unknown"),
                    address=address_str,
                    premium_per_unit=Decimal(str(c.get("premium_per_unit", 0))),
                    premium_date=date.today(),  # TODO: Use actual date from data
                    similarity_score=comp.get("score", 0),
                    similarity_reason=comp.get("reasoning"),
                )
            )

        return result

    def _build_risk_list(self, risks_result: dict) -> list[RiskFactor]:
        """Build list of risk factors for response.

        Args:
            risks_result: LLM risk analysis results

        Returns:
            List of RiskFactor objects
        """
        result = []
        risks = risks_result.get("risk_factors", [])

        for risk in risks:
            # Validate severity
            severity = risk.get("severity", "info")
            if severity not in ("info", "warning", "critical"):
                severity = "info"

            result.append(
                RiskFactor(
                    name=risk.get("name", "Unknown"),
                    severity=severity,
                    reason=risk.get("reason"),
                )
            )

        return result
