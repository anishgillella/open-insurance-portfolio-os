"""Gap Detection API endpoints.

Provides coverage gap detection, listing, management, and LLM-enhanced analysis.
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.repositories.gap_repository import GapRepository
from app.schemas.gap import (
    CrossPolicyConflict,
    GapAcknowledgeRequest,
    GapActionResponse,
    GapAnalysisRequest,
    GapAnalysisResult,
    GapDetail,
    GapDetectRequest,
    GapDetectResponse,
    GapListItem,
    GapListResponse,
    GapResolveRequest,
    GapSummary,
    PriorityAction,
    PropertyAnalysisRequest,
    PropertyAnalysisResult,
)
from app.services.gap_detection_service import GapDetectionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/detect", response_model=GapDetectResponse)
async def detect_gaps(
    request: GapDetectRequest,
    db: AsyncSessionDep,
) -> GapDetectResponse:
    """Trigger gap detection.

    Can detect gaps for:
    - A specific property (property_id)
    - All properties in an organization (organization_id)
    - All properties (no filters)

    When clear_existing=True (default), existing open gaps are cleared
    before running detection. Acknowledged and resolved gaps are preserved.
    """
    service = GapDetectionService(db)

    gaps_by_type: dict[str, int] = {}
    gaps_by_severity: dict[str, int] = {"critical": 0, "warning": 0, "info": 0}
    properties_checked = 0
    total_gaps = 0

    if request.property_id:
        # Single property
        gaps = await service.detect_gaps_for_property(
            request.property_id,
            clear_existing=request.clear_existing,
        )
        properties_checked = 1
        total_gaps = len(gaps)

        for gap in gaps:
            gaps_by_type[gap.gap_type] = gaps_by_type.get(gap.gap_type, 0) + 1
            gaps_by_severity[gap.severity] = gaps_by_severity.get(gap.severity, 0) + 1

    elif request.organization_id:
        # All properties in organization
        results = await service.detect_gaps_for_organization(
            request.organization_id,
            clear_existing=request.clear_existing,
        )
        properties_checked = len(results)

        for property_gaps in results.values():
            total_gaps += len(property_gaps)
            for gap in property_gaps:
                gaps_by_type[gap.gap_type] = gaps_by_type.get(gap.gap_type, 0) + 1
                gaps_by_severity[gap.severity] = gaps_by_severity.get(gap.severity, 0) + 1

    else:
        # All properties - get all organizations and run
        from sqlalchemy import select

        from app.models.organization import Organization

        stmt = select(Organization).where(Organization.deleted_at.is_(None))
        result = await db.execute(stmt)
        organizations = result.scalars().all()

        for org in organizations:
            results = await service.detect_gaps_for_organization(
                org.id,
                clear_existing=request.clear_existing,
            )
            properties_checked += len(results)

            for property_gaps in results.values():
                total_gaps += len(property_gaps)
                for gap in property_gaps:
                    gaps_by_type[gap.gap_type] = gaps_by_type.get(gap.gap_type, 0) + 1
                    gaps_by_severity[gap.severity] = gaps_by_severity.get(gap.severity, 0) + 1

    await db.commit()

    return GapDetectResponse(
        properties_checked=properties_checked,
        gaps_detected=total_gaps,
        gaps_by_type=gaps_by_type,
        gaps_by_severity=gaps_by_severity,
    )


@router.get("", response_model=GapListResponse)
async def list_gaps(
    db: AsyncSessionDep,
    property_id: str | None = Query(None, description="Filter by property ID"),
    organization_id: str | None = Query(None, description="Filter by organization ID"),
    status: str | None = Query(None, description="Filter by status: open, acknowledged, resolved"),
    severity: str | None = Query(None, description="Filter by severity: critical, warning, info"),
    gap_type: str | None = Query(None, description="Filter by gap type"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
) -> GapListResponse:
    """List coverage gaps with optional filters.

    Returns gaps sorted by severity (critical first), then by detection date.
    """
    repo = GapRepository(db)

    if property_id:
        gaps = await repo.get_by_property(
            property_id=property_id,
            status=status,
            severity=severity,
            gap_type=gap_type,
            limit=limit,
        )
    else:
        gaps = await repo.get_open_gaps(
            property_id=property_id,
            organization_id=organization_id,
            severity=severity,
            gap_type=gap_type,
            limit=limit,
        )

    # Build list items with property names
    items = []
    for gap in gaps:
        property_name = None
        if hasattr(gap, "property") and gap.property:
            property_name = gap.property.name

        items.append(
            GapListItem(
                id=gap.id,
                property_id=gap.property_id,
                property_name=property_name,
                policy_id=gap.policy_id,
                gap_type=gap.gap_type,
                severity=gap.severity,
                title=gap.title,
                description=gap.description,
                coverage_name=gap.coverage_name,
                current_value=gap.current_value,
                recommended_value=gap.recommended_value,
                status=gap.status,
                detected_at=gap.detected_at,
                gap_amount=gap.gap_amount,
            )
        )

    # Calculate summary
    summary = GapSummary(
        total=len(items),
        critical=sum(1 for g in items if g.severity == "critical"),
        warning=sum(1 for g in items if g.severity == "warning"),
        info=sum(1 for g in items if g.severity == "info"),
    )

    return GapListResponse(
        gaps=items,
        total_count=len(items),
        summary=summary,
    )


@router.get("/{gap_id}", response_model=GapDetail)
async def get_gap(
    gap_id: str,
    db: AsyncSessionDep,
) -> GapDetail:
    """Get detailed information about a specific gap.

    Returns the gap with both rule-based detection data and LLM analysis
    (if available). LLM analysis is auto-populated after document ingestion.
    """
    repo = GapRepository(db)
    gap = await repo.get_with_property(gap_id)

    if not gap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gap {gap_id} not found",
        )

    property_name = None
    if gap.property:
        property_name = gap.property.name

    return GapDetail(
        id=gap.id,
        property_id=gap.property_id,
        property_name=property_name,
        policy_id=gap.policy_id,
        program_id=gap.program_id,
        gap_type=gap.gap_type,
        severity=gap.severity,
        title=gap.title,
        description=gap.description,
        coverage_name=gap.coverage_name,
        current_value=gap.current_value,
        recommended_value=gap.recommended_value,
        status=gap.status,
        detected_at=gap.detected_at,
        gap_amount=gap.gap_amount,
        resolution_notes=gap.resolution_notes,
        resolved_at=gap.resolved_at,
        resolved_by=gap.resolved_by,
        detection_method=gap.detection_method,
        created_at=gap.created_at,
        updated_at=gap.updated_at,
        # LLM Analysis fields
        llm_enhanced_description=gap.llm_enhanced_description,
        llm_risk_assessment=gap.llm_risk_assessment,
        llm_risk_score=gap.llm_risk_score,
        llm_recommendations=gap.llm_recommendations,
        llm_potential_consequences=gap.llm_potential_consequences,
        llm_industry_context=gap.llm_industry_context,
        llm_action_priority=gap.llm_action_priority,
        llm_estimated_impact=gap.llm_estimated_impact,
        llm_analyzed_at=gap.llm_analyzed_at,
        llm_model_used=gap.llm_model_used,
    )


@router.post("/{gap_id}/acknowledge", response_model=GapActionResponse)
async def acknowledge_gap(
    gap_id: str,
    request: GapAcknowledgeRequest,
    db: AsyncSessionDep,
) -> GapActionResponse:
    """Mark a gap as acknowledged (reviewed but not resolved).

    Acknowledged gaps are preserved during gap detection reruns.
    """
    repo = GapRepository(db)
    gap = await repo.acknowledge_gap(gap_id, notes=request.notes)

    if not gap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gap {gap_id} not found",
        )

    await db.commit()

    return GapActionResponse(
        id=gap.id,
        status=gap.status,
        message="Gap acknowledged successfully",
    )


@router.post("/{gap_id}/resolve", response_model=GapActionResponse)
async def resolve_gap(
    gap_id: str,
    request: GapResolveRequest,
    db: AsyncSessionDep,
) -> GapActionResponse:
    """Mark a gap as resolved.

    Resolved gaps are preserved during gap detection reruns.
    This also triggers a health score recalculation for the property.
    """
    repo = GapRepository(db)
    gap = await repo.resolve_gap(gap_id, notes=request.notes)

    if not gap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gap {gap_id} not found",
        )

    await db.commit()

    # Trigger health score recalculation after gap resolution
    try:
        from app.services.health_score_service import HealthScoreService

        health_service = HealthScoreService(db)
        await health_service.calculate_health_score(gap.property_id, trigger="gap_resolved")
        await db.commit()
        logger.info(f"Health score recalculated after gap {gap_id} resolution")
    except Exception as e:
        logger.warning(f"Failed to recalculate health score after gap resolution: {e}")

    return GapActionResponse(
        id=gap.id,
        status=gap.status,
        message="Gap resolved successfully",
    )


# ============================================================================
# LLM-Enhanced Analysis Endpoints
# ============================================================================


@router.post("/{gap_id}/analyze", response_model=GapAnalysisResult)
async def analyze_gap(
    gap_id: str,
    db: AsyncSessionDep,
    request: GapAnalysisRequest | None = None,
) -> GapAnalysisResult:
    """Get LLM-enhanced analysis for a specific gap.

    This endpoint combines rule-based gap detection with AI-powered insights:
    - Enhanced description explaining the gap's implications
    - Risk assessment with quantified risk score (1-10)
    - Actionable recommendations
    - Potential consequences if not addressed
    - Industry context and benchmarks
    - Priority classification (immediate, short_term, medium_term)

    Note: This endpoint makes an LLM API call and may take 2-5 seconds.
    """
    from app.services.gap_analysis_service import GapAnalysisError, GapAnalysisService

    # Verify gap exists
    repo = GapRepository(db)
    gap = await repo.get_by_id(gap_id)
    if not gap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gap {gap_id} not found",
        )

    try:
        service = GapAnalysisService(db)
        result = await service.analyze_gap(gap_id)

        return GapAnalysisResult(
            gap_id=result.gap_id,
            enhanced_description=result.enhanced_description,
            risk_assessment=result.risk_assessment,
            risk_score=result.risk_score,
            recommendations=result.recommendations,
            potential_consequences=result.potential_consequences,
            industry_context=result.industry_context,
            action_priority=result.action_priority,
            estimated_impact=result.estimated_impact,
            related_gaps=result.related_gaps,
            analysis_timestamp=result.analysis_timestamp,
            model_used=result.model_used,
            latency_ms=result.latency_ms,
        )

    except GapAnalysisError as e:
        logger.error(f"Gap analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gap analysis service error: {str(e)}",
        )


@router.post("/properties/{property_id}/analyze", response_model=PropertyAnalysisResult)
async def analyze_property_gaps(
    property_id: str,
    db: AsyncSessionDep,
    request: PropertyAnalysisRequest | None = None,
) -> PropertyAnalysisResult:
    """Get comprehensive LLM-enhanced analysis for all gaps on a property.

    This endpoint provides a holistic view of a property's coverage status:
    - Overall risk score and letter grade (A-F)
    - Executive summary for stakeholders
    - Individual analysis of each gap
    - Cross-policy conflict detection
    - Coverage recommendations
    - Prioritized action items
    - Portfolio-level insights and patterns

    The analysis first runs rule-based gap detection, then enhances each
    gap with LLM insights, and finally provides property-level synthesis.

    Note: This endpoint makes multiple LLM API calls and may take 10-30 seconds
    depending on the number of gaps.
    """
    from app.services.gap_analysis_service import GapAnalysisError, GapAnalysisService
    from app.repositories.property_repository import PropertyRepository

    # Verify property exists
    prop_repo = PropertyRepository(db)
    prop = await prop_repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    try:
        service = GapAnalysisService(db)
        result = await service.analyze_property_gaps(property_id)

        # Convert dataclass results to schema models
        gap_analyses = [
            GapAnalysisResult(
                gap_id=ga.gap_id,
                enhanced_description=ga.enhanced_description,
                risk_assessment=ga.risk_assessment,
                risk_score=ga.risk_score,
                recommendations=ga.recommendations,
                potential_consequences=ga.potential_consequences,
                industry_context=ga.industry_context,
                action_priority=ga.action_priority,
                estimated_impact=ga.estimated_impact,
                related_gaps=ga.related_gaps,
                analysis_timestamp=ga.analysis_timestamp,
                model_used=ga.model_used,
                latency_ms=ga.latency_ms,
            )
            for ga in result.gap_analyses
        ]

        cross_policy_conflicts = [
            CrossPolicyConflict(
                conflict_type=c.get("conflict_type", "unknown"),
                description=c.get("description", ""),
                policies_involved=c.get("policies_involved", []),
                severity=c.get("severity", "warning"),
            )
            for c in result.cross_policy_conflicts
        ]

        priority_actions = [
            PriorityAction(
                action=a.get("action", ""),
                priority=a.get("priority", "medium_term"),
                estimated_effort=a.get("estimated_effort"),
                expected_benefit=a.get("expected_benefit"),
            )
            for a in result.priority_actions
        ]

        return PropertyAnalysisResult(
            property_id=result.property_id,
            property_name=result.property_name,
            overall_risk_score=result.overall_risk_score,
            risk_grade=result.risk_grade,
            executive_summary=result.executive_summary,
            gap_analyses=gap_analyses,
            cross_policy_conflicts=cross_policy_conflicts,
            coverage_recommendations=result.coverage_recommendations,
            priority_actions=priority_actions,
            portfolio_insights=result.portfolio_insights,
            analysis_timestamp=result.analysis_timestamp,
            model_used=result.model_used,
            total_latency_ms=result.total_latency_ms,
        )

    except GapAnalysisError as e:
        logger.error(f"Property gap analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gap analysis service error: {str(e)}",
        )
