"""Insurance Health Score API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.schemas.health_score import (
    HealthScoreResponse,
    HealthScoreHistoryResponse,
    PortfolioHealthScoreResponse,
    RecalculateRequest,
    RecalculateResponse,
    ComponentScoreSchema,
    RecommendationSchema,
    TrendSchema,
    HistoryEntrySchema,
    TrendAnalysisSchema,
    PortfolioPropertyScoreSchema,
)
from app.services.health_score_service import HealthScoreService, HealthScoreError

router = APIRouter()


@router.get("/properties/{property_id}", response_model=HealthScoreResponse)
async def get_property_health_score(
    property_id: str,
    db: AsyncSessionDep,
) -> HealthScoreResponse:
    """Get Insurance Health Score for a property.

    Returns the most recent health score with full component breakdown
    and LLM-generated insights.

    Args:
        property_id: Property ID.

    Returns:
        HealthScoreResponse with score details.
    """
    service = HealthScoreService(db)

    # Try to get existing score first
    result = await service.get_latest_score(property_id)

    if not result:
        # Calculate new score if none exists
        try:
            result = await service.calculate_health_score(property_id, trigger="manual")
        except HealthScoreError as e:
            if "not found" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Property {property_id} not found",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    # Convert to response schema
    return HealthScoreResponse(
        property_id=result.property_id,
        property_name=result.property_name,
        score=result.score,
        grade=result.grade,
        components={
            name: ComponentScoreSchema(
                score=comp.score,
                max=comp.max_points,
                percentage=comp.percentage,
                reasoning=comp.reasoning,
                key_findings=comp.key_findings,
                concerns=comp.concerns,
            )
            for name, comp in result.components.items()
        },
        executive_summary=result.executive_summary,
        recommendations=[
            RecommendationSchema(
                priority=rec.get("priority", "medium"),
                action=rec.get("action", ""),
                impact=rec.get("impact", ""),
                component=rec.get("component", ""),
            )
            for rec in result.recommendations
        ],
        risk_factors=result.risk_factors,
        strengths=result.strengths,
        trend=TrendSchema(
            direction=result.trend_direction,
            delta=result.trend_delta,
            previous_score=None,  # Would need to query previous
            previous_date=None,
        ),
        calculated_at=result.calculated_at,
        model_used=result.model_used,
        latency_ms=result.latency_ms,
    )


@router.get("/properties/{property_id}/history", response_model=HealthScoreHistoryResponse)
async def get_health_score_history(
    property_id: str,
    db: AsyncSessionDep,
    days: int = Query(90, ge=7, le=365, description="Number of days of history"),
) -> HealthScoreHistoryResponse:
    """Get health score history for trend analysis.

    Returns historical scores to visualize trends over time.

    Args:
        property_id: Property ID.
        days: Number of days of history (7-365).

    Returns:
        HealthScoreHistoryResponse with history and trend analysis.
    """
    service = HealthScoreService(db)
    result = await service.get_score_history(property_id, days)

    if result["current_score"] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No health scores found for property {property_id}",
        )

    trend = result.get("trend_analysis", {})
    return HealthScoreHistoryResponse(
        property_id=result["property_id"],
        current_score=result["current_score"],
        history=[
            HistoryEntrySchema(
                date=entry["date"],
                score=entry["score"],
                grade=entry["grade"],
            )
            for entry in result["history"]
        ],
        trend_analysis=TrendAnalysisSchema(
            direction=trend.get("direction", "new"),
            first_score=trend.get("first_score"),
            last_score=trend.get("last_score"),
            change=trend.get(f"{days}_day_change"),
            note=trend.get("note"),
        ),
    )


@router.get("/portfolio", response_model=PortfolioHealthScoreResponse)
async def get_portfolio_health_score(
    db: AsyncSessionDep,
    organization_id: str | None = Query(None, description="Filter by organization"),
) -> PortfolioHealthScoreResponse:
    """Get aggregate health score for portfolio.

    Calculates average scores across all properties and provides
    grade distribution.

    Args:
        organization_id: Optional organization filter.

    Returns:
        PortfolioHealthScoreResponse with aggregated data.
    """
    service = HealthScoreService(db)
    result = await service.calculate_portfolio_score(organization_id)

    return PortfolioHealthScoreResponse(
        portfolio_score=result.portfolio_score,
        portfolio_grade=result.portfolio_grade,
        property_count=result.property_count,
        distribution=result.distribution,
        component_averages=result.component_averages,
        trend=TrendSchema(
            direction=result.trend_direction,
            delta=result.trend_delta,
            previous_score=None,
            previous_date=None,
        ),
        properties=[
            PortfolioPropertyScoreSchema(
                id=prop["id"],
                name=prop["name"],
                score=prop["score"],
                grade=prop["grade"],
                trend=prop.get("trend"),
            )
            for prop in result.properties
        ],
        calculated_at=result.calculated_at,
    )


@router.post("/properties/{property_id}/recalculate", response_model=RecalculateResponse)
async def recalculate_health_score(
    property_id: str,
    db: AsyncSessionDep,
    request: RecalculateRequest | None = None,
) -> RecalculateResponse:
    """Manually trigger health score recalculation.

    Forces a new health score calculation using current data.

    Args:
        property_id: Property ID.
        request: Optional recalculation options.

    Returns:
        RecalculateResponse with new score and comparison to previous.
    """
    service = HealthScoreService(db)

    # Get previous score for comparison
    previous = await service.get_latest_score(property_id)
    previous_score = previous.score if previous else None

    try:
        result = await service.calculate_health_score(property_id, trigger="manual")
    except HealthScoreError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {property_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    await db.commit()

    return RecalculateResponse(
        property_id=result.property_id,
        score=result.score,
        grade=result.grade,
        previous_score=previous_score,
        change=result.score - previous_score if previous_score else None,
        trend_direction=result.trend_direction,
        calculated_at=result.calculated_at,
        latency_ms=result.latency_ms,
    )
