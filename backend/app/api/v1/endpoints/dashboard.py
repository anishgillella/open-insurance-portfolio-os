"""Dashboard API endpoints.

Provides portfolio-level statistics, expiration tracking, and alerts.
"""

from fastapi import APIRouter, Query

from app.core.dependencies import AsyncSessionDep
from app.schemas.dashboard import (
    AlertsResponse,
    DashboardSummary,
    ExpirationTimelineResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSessionDep,
    organization_id: str | None = Query(
        default=None, description="Filter by organization ID"
    ),
) -> DashboardSummary:
    """Get portfolio dashboard summary.

    Returns aggregated statistics including:
    - Portfolio stats (properties, buildings, units, TIV, premium)
    - Expiration stats (policies expiring in 30/60/90 days)
    - Gap stats (open coverage gaps by severity)
    - Compliance stats (lender compliance status)
    - Completeness stats (document completeness)
    - Health score (portfolio average)
    """
    service = DashboardService(db)
    return await service.get_dashboard_summary(organization_id)


@router.get("/expirations", response_model=ExpirationTimelineResponse)
async def get_expiration_timeline(
    db: AsyncSessionDep,
    days_ahead: int = Query(
        default=90, ge=1, le=365, description="Days to look ahead"
    ),
    organization_id: str | None = Query(
        default=None, description="Filter by organization ID"
    ),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum results"),
) -> ExpirationTimelineResponse:
    """Get upcoming policy expirations.

    Returns a timeline of policies expiring within the specified window,
    ordered by expiration date. Each policy includes severity based on
    days until expiration:
    - critical: ≤ 30 days
    - warning: 31-60 days
    - info: 61-90 days
    """
    service = DashboardService(db)
    return await service.get_expiration_timeline(
        days_ahead=days_ahead,
        organization_id=organization_id,
        limit=limit,
    )


@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(
    db: AsyncSessionDep,
    severity: str | None = Query(
        default=None, description="Filter by severity: critical, warning, info"
    ),
    type: str | None = Query(
        default=None,
        alias="alert_type",
        description="Filter by type: gap, expiration, compliance",
    ),
    organization_id: str | None = Query(
        default=None, description="Filter by organization ID"
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
) -> AlertsResponse:
    """Get active alerts requiring attention.

    Returns alerts sorted by severity (critical first), including:
    - Expiration alerts for policies expiring soon
    - Gap alerts for coverage gaps
    - Compliance alerts for lender requirement issues
    """
    service = DashboardService(db)
    return await service.get_alerts(
        severity=severity,
        alert_type=type,
        organization_id=organization_id,
        limit=limit,
    )
