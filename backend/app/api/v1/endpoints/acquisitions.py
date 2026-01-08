"""Acquisitions API endpoints.

Provides acquisition premium estimation for properties being considered
for purchase. Uses AI-powered comparable matching and risk analysis.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import AsyncSessionDep
from app.schemas.acquisitions import (
    AcquisitionCalculateRequest,
    AcquisitionCalculateResponse,
)
from app.services.acquisitions_service import AcquisitionsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/calculate",
    response_model=AcquisitionCalculateResponse,
    summary="Calculate acquisition premium estimate",
    description="""
Calculates estimated insurance premium for a property being considered for acquisition.

The calculation uses AI to:
1. Find comparable properties from the existing portfolio
2. Score similarity based on location, vintage, size, and characteristics
3. Identify risk factors from property details and notes
4. Generate premium range estimates

If the property is too unique to estimate reliably, it will be flagged for
human consultant review.
""",
    responses={
        200: {
            "description": "Successful calculation",
            "content": {
                "application/json": {
                    "examples": {
                        "normal": {
                            "summary": "Normal property with comparables",
                            "value": {
                                "is_unique": False,
                                "uniqueness_reason": None,
                                "confidence": "high",
                                "premium_range": {
                                    "low": 1500,
                                    "mid": 2000,
                                    "high": 2700,
                                },
                                "premium_range_label": "medium range ($1,500-$2,700)",
                                "message": "This property is likely to be within the medium range ($1,500-$2,700).",
                                "comparables": [
                                    {
                                        "property_id": "prop-1",
                                        "name": "Shoaff Park Apartments",
                                        "address": "Fort Wayne, IN",
                                        "premium_per_unit": 1827,
                                        "premium_date": "2025-01-07",
                                        "similarity_score": 85,
                                        "similarity_reason": "Same state, similar vintage and unit count",
                                    }
                                ],
                                "risk_factors": [
                                    {
                                        "name": "Flood Zone",
                                        "severity": "warning",
                                        "reason": "Notes mention lakefront proximity",
                                    }
                                ],
                                "llm_explanation": "Found 5 comparable properties in Indiana.",
                            },
                        },
                        "unique": {
                            "summary": "Unique property requiring consultant review",
                            "value": {
                                "is_unique": True,
                                "uniqueness_reason": "Property characteristics are unusual. Best comparables have low similarity.",
                                "confidence": "low",
                                "premium_range": None,
                                "preliminary_estimate": {
                                    "low": 1800,
                                    "mid": 2500,
                                    "high": 3500,
                                },
                                "message": "This property is a bit unique. We need our insurance consultants to review.",
                                "comparables": [],
                                "risk_factors": [
                                    {
                                        "name": "Vintage Wiring",
                                        "severity": "critical",
                                        "reason": "1920 construction",
                                    }
                                ],
                            },
                        },
                    }
                }
            },
        },
        400: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
async def calculate_acquisition(
    request: AcquisitionCalculateRequest,
    db: AsyncSessionDep,
) -> AcquisitionCalculateResponse:
    """Calculate acquisition premium estimate.

    Args:
        request: Property details for the acquisition
        db: Database session

    Returns:
        Premium estimate with comparables and risk factors
    """
    try:
        logger.info(f"Calculating acquisition for address: {request.address}")

        service = AcquisitionsService(session=db)
        result = await service.calculate_acquisition(request)

        logger.info(
            f"Calculation complete: is_unique={result.is_unique}, "
            f"confidence={result.confidence}, "
            f"comparables={len(result.comparables)}"
        )

        return result

    except Exception as e:
        logger.exception(f"Failed to calculate acquisition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate acquisition premium. Please try again later.",
        )
