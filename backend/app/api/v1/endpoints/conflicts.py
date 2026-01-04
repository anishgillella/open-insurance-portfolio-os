"""Coverage Conflict API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.repositories.conflict_repository import ConflictRepository
from app.repositories.property_repository import PropertyRepository
from app.schemas.conflict import (
    ConflictListResponse,
    ConflictDetail,
    ConflictListItem,
    ConflictSummarySchema,
    AnalyzeConflictsRequest,
    AnalyzeConflictsResponse,
    AcknowledgeRequest,
    ResolveRequest,
    ConflictActionResponse,
)
from app.services.conflict_detection_service import (
    ConflictDetectionService,
    ConflictDetectionError,
)

router = APIRouter()


@router.get("/properties/{property_id}", response_model=ConflictListResponse)
async def get_property_conflicts(
    property_id: str,
    db: AsyncSessionDep,
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    severity: str | None = Query(None, description="Filter by severity"),
) -> ConflictListResponse:
    """Get coverage conflicts for a property.

    Returns all detected conflicts with optional filtering.

    Args:
        property_id: Property ID.
        status_filter: Optional status filter (open, acknowledged, resolved).
        severity: Optional severity filter (critical, warning, info).

    Returns:
        ConflictListResponse with conflicts and summary.
    """
    # Verify property exists
    property_repo = PropertyRepository(db)
    prop = await property_repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    # Get conflicts
    conflict_repo = ConflictRepository(db)
    conflicts = await conflict_repo.get_by_property(
        property_id,
        status=status_filter,
        severity=severity,
    )

    # Build summary
    summary = ConflictSummarySchema(
        total_conflicts=len(conflicts),
        critical=sum(1 for c in conflicts if c.severity == "critical"),
        warning=sum(1 for c in conflicts if c.severity == "warning"),
        info=sum(1 for c in conflicts if c.severity == "info"),
    )

    return ConflictListResponse(
        property_id=property_id,
        property_name=prop.name,
        analysis_date=conflicts[0].detected_at if conflicts else datetime.now(timezone.utc),
        summary=summary,
        conflicts=[
            ConflictListItem(
                id=c.id,
                conflict_type=c.conflict_type,
                severity=c.severity,
                title=c.title,
                description=c.description,
                affected_policy_ids=c.affected_policy_ids or [],
                gap_amount=c.gap_amount,
                potential_savings=c.potential_savings,
                recommendation=c.recommendation,
                status=c.status,
                detected_at=c.detected_at,
            )
            for c in conflicts
        ],
        cross_policy_analysis=None,  # Not stored per-conflict
        portfolio_recommendations=[],
    )


@router.post("/properties/{property_id}/analyze", response_model=AnalyzeConflictsResponse)
async def analyze_conflicts(
    property_id: str,
    db: AsyncSessionDep,
    request: AnalyzeConflictsRequest | None = None,
) -> AnalyzeConflictsResponse:
    """Trigger fresh conflict analysis for a property.

    Uses LLM to analyze policies and detect conflicts.

    Args:
        property_id: Property ID.
        request: Optional analysis options.

    Returns:
        AnalyzeConflictsResponse with detection results.
    """
    service = ConflictDetectionService(db)

    clear_existing = request.force_refresh if request else True

    try:
        result = await service.detect_conflicts(
            property_id,
            clear_existing=clear_existing,
        )
    except ConflictDetectionError as e:
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

    return AnalyzeConflictsResponse(
        property_id=result.property_id,
        analysis_id=None,  # Could generate a unique analysis ID
        status="completed",
        conflicts_found=len(result.conflicts),
        summary=ConflictSummarySchema(
            total_conflicts=result.summary.get("total_conflicts", 0),
            critical=result.summary.get("critical", 0),
            warning=result.summary.get("warning", 0),
            info=result.summary.get("info", 0),
        ),
        cross_policy_analysis=result.cross_policy_analysis,
        portfolio_recommendations=result.portfolio_recommendations,
        duration_ms=result.latency_ms,
    )


@router.get("/{conflict_id}", response_model=ConflictDetail)
async def get_conflict(
    conflict_id: str,
    db: AsyncSessionDep,
) -> ConflictDetail:
    """Get detailed conflict information.

    Returns full conflict details including LLM analysis.

    Args:
        conflict_id: Conflict ID.

    Returns:
        ConflictDetail with all conflict information.
    """
    repo = ConflictRepository(db)
    conflict = await repo.get_with_property(conflict_id)

    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
        )

    return ConflictDetail(
        id=conflict.id,
        property_id=conflict.property_id,
        conflict_type=conflict.conflict_type,
        severity=conflict.severity,
        title=conflict.title,
        description=conflict.description,
        affected_policy_ids=conflict.affected_policy_ids or [],
        gap_amount=conflict.gap_amount,
        potential_savings=conflict.potential_savings,
        recommendation=conflict.recommendation,
        status=conflict.status,
        detected_at=conflict.detected_at,
        detection_method=conflict.detection_method,
        llm_reasoning=conflict.llm_reasoning,
        llm_analysis=conflict.llm_analysis,
        llm_analyzed_at=conflict.llm_analyzed_at,
        llm_model_used=conflict.llm_model_used,
        acknowledged_at=conflict.acknowledged_at,
        acknowledged_by=conflict.acknowledged_by,
        acknowledged_notes=conflict.acknowledged_notes,
        resolved_at=conflict.resolved_at,
        resolved_by=conflict.resolved_by,
        resolution_notes=conflict.resolution_notes,
        created_at=conflict.created_at,
        updated_at=conflict.updated_at,
    )


@router.post("/{conflict_id}/acknowledge", response_model=ConflictActionResponse)
async def acknowledge_conflict(
    conflict_id: str,
    request: AcknowledgeRequest,
    db: AsyncSessionDep,
) -> ConflictActionResponse:
    """Mark a conflict as acknowledged.

    Indicates the conflict has been reviewed.

    Args:
        conflict_id: Conflict ID.
        request: Acknowledgment notes.

    Returns:
        ConflictActionResponse confirming the action.
    """
    repo = ConflictRepository(db)
    conflict = await repo.acknowledge_conflict(
        conflict_id,
        notes=request.notes,
    )

    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
        )

    await db.commit()

    return ConflictActionResponse(
        id=conflict.id,
        status=conflict.status,
        message="Conflict acknowledged successfully",
        updated_at=conflict.acknowledged_at or datetime.now(timezone.utc),
    )


@router.post("/{conflict_id}/resolve", response_model=ConflictActionResponse)
async def resolve_conflict(
    conflict_id: str,
    request: ResolveRequest,
    db: AsyncSessionDep,
) -> ConflictActionResponse:
    """Mark a conflict as resolved.

    Indicates the conflict has been addressed.

    Args:
        conflict_id: Conflict ID.
        request: Resolution notes.

    Returns:
        ConflictActionResponse confirming the action.
    """
    repo = ConflictRepository(db)
    conflict = await repo.resolve_conflict(
        conflict_id,
        notes=request.notes,
    )

    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
        )

    await db.commit()

    return ConflictActionResponse(
        id=conflict.id,
        status=conflict.status,
        message="Conflict resolved successfully",
        updated_at=conflict.resolved_at or datetime.now(timezone.utc),
    )
