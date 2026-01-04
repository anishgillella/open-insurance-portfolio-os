"""Renewal Intelligence Engine API endpoints (Phase 4.4).

Provides endpoints for:
- Premium forecasting
- Renewal timeline and alerts
- Document readiness assessment
- Market context analysis
- Policy and program comparison
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.schemas.renewal import (
    # Forecast schemas
    RenewalForecastResponse,
    ForecastListItem,
    ForecastListResponse,
    ForecastRangeSchema,
    FactorBreakdownSchema,
    GenerateForecastRequest,
    GenerateForecastResponse,
    # Alert schemas
    RenewalAlertResponse,
    AlertListResponse,
    AlertSummarySchema,
    AcknowledgeAlertRequest,
    ResolveAlertRequest,
    AlertActionResponse,
    AlertConfigSchema,
    UpdateAlertConfigRequest,
    AlertConfigResponse,
    # Timeline schemas
    RenewalTimelineResponse,
    TimelineItemSchema,
    TimelineSummarySchema,
    # Readiness schemas
    RenewalReadinessResponse,
    DocumentStatusSchema,
    ReadinessIssueSchema,
    ReadinessRecommendationSchema,
    TimelineMilestoneSchema,
    AssessReadinessRequest,
    PortfolioReadinessResponse,
    PortfolioReadinessPropertySchema,
    # Market context schemas
    MarketContextResponse,
    PolicyAnalysisSchema,
    YoYChangeSchema,
    NegotiationRecommendationSchema,
    AnalyzeMarketContextRequest,
    # Summary schemas
    RenewalSummaryResponse,
    # Policy comparison schemas
    PolicyComparisonResponse,
    ProgramComparisonResponse,
    ComparePoliciesRequest,
    CompareProgramsRequest,
    PolicySummarySchema,
    CoverageComparisonSchema,
)
from app.services.renewal_forecast_service import (
    RenewalForecastService,
    RenewalForecastError,
)
from app.services.renewal_timeline_service import (
    RenewalTimelineService,
    RenewalTimelineError,
)
from app.services.renewal_readiness_service import (
    RenewalReadinessService,
    RenewalReadinessError,
)
from app.services.market_context_service import (
    MarketContextService,
    MarketContextError,
)
from app.services.policy_comparison_service import (
    PolicyComparisonService,
    PolicyComparisonError,
)

router = APIRouter()


# =============================================================================
# Forecast Endpoints
# =============================================================================


@router.get("/forecast/{property_id}", response_model=RenewalForecastResponse)
async def get_renewal_forecast(
    property_id: str,
    db: AsyncSessionDep,
) -> RenewalForecastResponse:
    """Get renewal forecast for a property.

    Returns the most recent premium forecast with rule-based and LLM predictions.

    Args:
        property_id: Property ID.

    Returns:
        RenewalForecastResponse with forecast details.
    """
    service = RenewalForecastService(db)

    result = await service.get_forecast(property_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No forecast found for property {property_id}. Use POST to generate.",
        )

    return _forecast_result_to_response(result)


@router.post("/forecast/{property_id}", response_model=GenerateForecastResponse)
async def generate_renewal_forecast(
    property_id: str,
    db: AsyncSessionDep,
    request: GenerateForecastRequest | None = None,
) -> GenerateForecastResponse:
    """Generate a new renewal forecast for a property.

    Triggers premium forecasting with rule-based calculations and LLM analysis.

    Args:
        property_id: Property ID.
        request: Optional forecast options.

    Returns:
        GenerateForecastResponse with new forecast.
    """
    service = RenewalForecastService(db)
    force = request.force if request else False
    include_market = request.include_market_context if request else True

    try:
        result = await service.generate_forecast(
            property_id,
            force=force,
            include_market_context=include_market,
        )
    except RenewalForecastError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    await db.commit()

    return GenerateForecastResponse(
        id=result.property_id,  # Using property_id as forecast was just created
        property_id=result.property_id,
        status="generated",
        message="Renewal forecast generated successfully",
        forecast=_forecast_result_to_response(result),
    )


@router.get("/forecasts", response_model=ForecastListResponse)
async def list_forecasts(
    db: AsyncSessionDep,
    organization_id: str | None = Query(None, description="Filter by organization"),
    status_filter: str = Query("active", description="Filter by status"),
) -> ForecastListResponse:
    """List all renewal forecasts.

    Args:
        organization_id: Optional organization filter.
        status_filter: Filter by status (active, superseded, expired).

    Returns:
        ForecastListResponse with forecast list.
    """
    service = RenewalForecastService(db)
    forecasts = await service.list_forecasts(
        organization_id=organization_id,
        status=status_filter,
    )

    items = []
    for f in forecasts:
        days = (f.current_expiration_date - date.today()).days if f.current_expiration_date else 0
        items.append(ForecastListItem(
            id=f.id,
            property_id=f.property_id,
            property_name=f.property.name if f.property else "Unknown",
            renewal_year=f.renewal_year,
            current_expiration_date=f.current_expiration_date,
            days_until_expiration=days,
            current_premium=f.current_premium,
            llm_predicted_mid=f.llm_predicted_mid,
            llm_confidence_score=f.llm_confidence_score,
            status=f.status,
            forecast_date=f.forecast_date,
        ))

    return ForecastListResponse(
        forecasts=items,
        total_count=len(items),
    )


# =============================================================================
# Timeline Endpoints
# =============================================================================


@router.get("/timeline", response_model=RenewalTimelineResponse)
async def get_renewal_timeline(
    db: AsyncSessionDep,
    organization_id: str | None = Query(None, description="Filter by organization"),
    days_ahead: int = Query(120, ge=30, le=365, description="Days ahead to look"),
) -> RenewalTimelineResponse:
    """Get renewal timeline for upcoming expirations.

    Returns all policies expiring within the specified time window.

    Args:
        organization_id: Optional organization filter.
        days_ahead: How many days ahead to look (30-365).

    Returns:
        RenewalTimelineResponse with timeline and summary.
    """
    service = RenewalTimelineService(db)
    timeline, summary = await service.get_timeline(
        organization_id=organization_id,
        days_ahead=days_ahead,
    )

    return RenewalTimelineResponse(
        timeline=[
            TimelineItemSchema(
                property_id=item.property_id,
                property_name=item.property_name,
                policy_id=item.policy_id,
                policy_number=item.policy_number,
                policy_type=item.policy_type,
                carrier_name=item.carrier_name,
                expiration_date=item.expiration_date,
                days_until_expiration=item.days_until_expiration,
                severity=item.severity,
                current_premium=item.current_premium,
                predicted_premium=item.predicted_premium,
                has_forecast=item.has_forecast,
                has_active_alerts=item.has_active_alerts,
                alert_count=item.alert_count,
            )
            for item in timeline
        ],
        summary=TimelineSummarySchema(
            total_renewals=summary.total_renewals,
            expiring_30_days=summary.expiring_30_days,
            expiring_60_days=summary.expiring_60_days,
            expiring_90_days=summary.expiring_90_days,
            total_premium_at_risk=summary.total_premium_at_risk,
        ),
    )


# =============================================================================
# Alert Endpoints
# =============================================================================


@router.post("/alerts/generate")
async def generate_alerts(
    db: AsyncSessionDep,
    organization_id: str | None = Query(None, description="Filter by organization"),
    include_llm: bool = Query(True, description="Include LLM enhancement"),
) -> dict:
    """Generate renewal alerts based on configured thresholds.

    Scans all policies and creates alerts for those approaching expiration.

    Args:
        organization_id: Optional organization filter.
        include_llm: Include LLM enhancement for priority scoring.

    Returns:
        Count of new alerts generated.
    """
    service = RenewalTimelineService(db)
    count = await service.generate_alerts(
        organization_id=organization_id,
        include_llm_enhancement=include_llm,
    )

    await db.commit()

    return {
        "status": "success",
        "alerts_generated": count,
        "message": f"Generated {count} new renewal alerts",
    }


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    db: AsyncSessionDep,
    organization_id: str | None = Query(None, description="Filter by organization"),
    status_filter: str | None = Query(None, description="Filter by status"),
    severity_filter: str | None = Query(None, description="Filter by severity"),
) -> AlertListResponse:
    """List renewal alerts.

    Args:
        organization_id: Optional organization filter.
        status_filter: Filter by status (pending, acknowledged, resolved).
        severity_filter: Filter by severity (info, warning, critical).

    Returns:
        AlertListResponse with alerts and summary.
    """
    service = RenewalTimelineService(db)
    alerts, summary = await service.list_alerts(
        organization_id=organization_id,
        status=status_filter,
        severity=severity_filter,
    )

    return AlertListResponse(
        alerts=[
            RenewalAlertResponse(
                id=a.id,
                property_id=a.property_id,
                property_name=a.property.name if a.property else "Unknown",
                policy_id=a.policy_id,
                policy_number=a.policy.policy_number if a.policy else None,
                policy_type=a.policy.policy_type if a.policy else None,
                carrier_name=a.policy.carrier_name if a.policy else None,
                threshold_days=a.threshold_days,
                days_until_expiration=a.days_until_expiration,
                expiration_date=a.expiration_date,
                severity=a.severity,
                title=a.title,
                message=a.message,
                status=a.status,
                triggered_at=a.triggered_at,
                acknowledged_at=a.acknowledged_at,
                acknowledged_by=a.acknowledged_by,
                resolved_at=a.resolved_at,
                llm_priority_score=a.llm_priority_score,
                llm_renewal_strategy=a.llm_renewal_strategy,
                llm_key_actions=a.llm_key_actions or [],
                created_at=a.created_at,
            )
            for a in alerts
        ],
        total_count=len(alerts),
        summary=AlertSummarySchema(
            total=summary.total,
            critical=summary.critical,
            warning=summary.warning,
            info=summary.info,
            pending=summary.pending,
        ),
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertActionResponse)
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSessionDep,
    request: AcknowledgeAlertRequest | None = None,
) -> AlertActionResponse:
    """Acknowledge a renewal alert.

    Args:
        alert_id: Alert ID.
        request: Optional acknowledgement notes.

    Returns:
        AlertActionResponse with updated status.
    """
    service = RenewalTimelineService(db)

    try:
        alert = await service.acknowledge_alert(
            alert_id,
            notes=request.notes if request else None,
        )
    except RenewalTimelineError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    await db.commit()

    return AlertActionResponse(
        id=alert.id,
        status=alert.status,
        message="Alert acknowledged successfully",
        updated_at=alert.acknowledged_at or datetime.now(timezone.utc),
    )


@router.post("/alerts/{alert_id}/resolve", response_model=AlertActionResponse)
async def resolve_alert(
    alert_id: str,
    db: AsyncSessionDep,
    request: ResolveAlertRequest | None = None,
) -> AlertActionResponse:
    """Resolve a renewal alert.

    Args:
        alert_id: Alert ID.
        request: Optional resolution notes.

    Returns:
        AlertActionResponse with updated status.
    """
    service = RenewalTimelineService(db)

    try:
        alert = await service.resolve_alert(
            alert_id,
            notes=request.notes if request else None,
        )
    except RenewalTimelineError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    await db.commit()

    return AlertActionResponse(
        id=alert.id,
        status=alert.status,
        message="Alert resolved successfully",
        updated_at=alert.resolved_at or datetime.now(timezone.utc),
    )


@router.get("/alerts/config/{property_id}", response_model=AlertConfigResponse)
async def get_alert_config(
    property_id: str,
    db: AsyncSessionDep,
) -> AlertConfigResponse:
    """Get alert configuration for a property.

    Args:
        property_id: Property ID.

    Returns:
        AlertConfigResponse with current configuration.
    """
    service = RenewalTimelineService(db)
    config = await service.get_alert_config(property_id)

    if config:
        return AlertConfigResponse(
            property_id=config.property_id,
            thresholds=config.thresholds,
            enabled=config.enabled,
            severity_mapping=config.severity_mapping,
        )

    # Return defaults if no custom config
    return AlertConfigResponse(
        property_id=property_id,
        thresholds=[90, 60, 30],
        enabled=True,
        severity_mapping=None,
        message="Using default configuration",
    )


@router.put("/alerts/config/{property_id}", response_model=AlertConfigResponse)
async def update_alert_config(
    property_id: str,
    db: AsyncSessionDep,
    request: UpdateAlertConfigRequest,
) -> AlertConfigResponse:
    """Update alert configuration for a property.

    Args:
        property_id: Property ID.
        request: New configuration values.

    Returns:
        AlertConfigResponse with updated configuration.
    """
    service = RenewalTimelineService(db)
    config = await service.update_alert_config(
        property_id,
        thresholds=request.thresholds,
        enabled=request.enabled,
        severity_mapping=request.severity_mapping,
    )

    await db.commit()

    return AlertConfigResponse(
        property_id=config.property_id,
        thresholds=config.thresholds,
        enabled=config.enabled,
        severity_mapping=config.severity_mapping,
        message="Configuration updated successfully",
    )


# =============================================================================
# Readiness Endpoints
# =============================================================================


@router.get("/readiness/{property_id}", response_model=RenewalReadinessResponse)
async def get_renewal_readiness(
    property_id: str,
    db: AsyncSessionDep,
) -> RenewalReadinessResponse:
    """Get document readiness assessment for a property.

    Returns current readiness status or triggers new assessment.

    Args:
        property_id: Property ID.

    Returns:
        RenewalReadinessResponse with readiness details.
    """
    service = RenewalReadinessService(db)

    try:
        result = await service.assess_readiness(property_id, force=False)
    except RenewalReadinessError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    await db.commit()

    return _readiness_result_to_response(result)


@router.post("/readiness/{property_id}", response_model=RenewalReadinessResponse)
async def assess_renewal_readiness(
    property_id: str,
    db: AsyncSessionDep,
    request: AssessReadinessRequest | None = None,
) -> RenewalReadinessResponse:
    """Trigger new readiness assessment for a property.

    Args:
        property_id: Property ID.
        request: Optional assessment options.

    Returns:
        RenewalReadinessResponse with new assessment.
    """
    service = RenewalReadinessService(db)
    force = request.force if request else True
    verify = request.verify_contents if request else True

    try:
        result = await service.assess_readiness(
            property_id,
            force=force,
            verify_contents=verify,
        )
    except RenewalReadinessError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    await db.commit()

    return _readiness_result_to_response(result)


@router.get("/readiness/portfolio", response_model=PortfolioReadinessResponse)
async def get_portfolio_readiness(
    db: AsyncSessionDep,
    organization_id: str = Query(..., description="Organization ID"),
) -> PortfolioReadinessResponse:
    """Get readiness summary for entire portfolio.

    Args:
        organization_id: Organization ID (required).

    Returns:
        PortfolioReadinessResponse with portfolio summary.
    """
    service = RenewalReadinessService(db)
    result = await service.get_portfolio_readiness(organization_id)

    return PortfolioReadinessResponse(
        average_readiness=result["average_readiness"],
        average_grade=result["average_grade"],
        property_count=result["property_count"],
        distribution=result["distribution"],
        common_missing_docs=result["common_missing_docs"],
        properties=[
            PortfolioReadinessPropertySchema(
                id=p["id"],
                name=p["name"],
                readiness_score=p["readiness_score"],
                readiness_grade=p["readiness_grade"],
                days_until_renewal=p["days_until_renewal"],
                missing_required=p["missing_required"],
                missing_recommended=p["missing_recommended"],
            )
            for p in result["properties"]
        ],
    )


# =============================================================================
# Market Context Endpoints
# =============================================================================


@router.get("/market-context/{property_id}", response_model=MarketContextResponse)
async def get_market_context(
    property_id: str,
    db: AsyncSessionDep,
) -> MarketContextResponse:
    """Get market context analysis for a property.

    Returns cached analysis if still valid, or None if not available.

    Args:
        property_id: Property ID.

    Returns:
        MarketContextResponse with market analysis.
    """
    service = MarketContextService(db)
    result = await service.get_market_context(property_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No market context found for property {property_id}. Use POST to analyze.",
        )

    return _market_context_result_to_response(result)


@router.post("/market-context/{property_id}", response_model=MarketContextResponse)
async def analyze_market_context(
    property_id: str,
    db: AsyncSessionDep,
    request: AnalyzeMarketContextRequest | None = None,
) -> MarketContextResponse:
    """Analyze market context for a property.

    Triggers comprehensive market analysis with LLM.

    Args:
        property_id: Property ID.
        request: Optional analysis options.

    Returns:
        MarketContextResponse with new analysis.
    """
    service = MarketContextService(db)
    force = request.force if request else False
    include_yoy = request.include_yoy if request else True
    include_negotiation = request.include_negotiation if request else True

    try:
        result = await service.analyze_market_context(
            property_id,
            force=force,
            include_yoy=include_yoy,
            include_negotiation=include_negotiation,
        )
    except MarketContextError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    await db.commit()

    return _market_context_result_to_response(result)


# =============================================================================
# Comprehensive Summary Endpoint
# =============================================================================


@router.get("/summary/{property_id}", response_model=RenewalSummaryResponse)
async def get_renewal_summary(
    property_id: str,
    db: AsyncSessionDep,
) -> RenewalSummaryResponse:
    """Get comprehensive renewal summary for a property.

    Combines forecast, readiness, market context, and alerts into a single view.

    Args:
        property_id: Property ID.

    Returns:
        RenewalSummaryResponse with comprehensive summary.
    """
    forecast_service = RenewalForecastService(db)
    readiness_service = RenewalReadinessService(db)
    market_service = MarketContextService(db)
    timeline_service = RenewalTimelineService(db)

    # Get forecast
    forecast = await forecast_service.get_forecast(property_id)
    forecast_response = _forecast_result_to_response(forecast) if forecast else None

    # Get readiness (without triggering new assessment)
    try:
        readiness = await readiness_service.assess_readiness(
            property_id, force=False, verify_contents=False
        )
    except RenewalReadinessError:
        readiness = None

    # Get market context
    market = await market_service.get_market_context(property_id)

    # Get alerts count
    alerts, alert_summary = await timeline_service.list_alerts(status="pending")
    property_alerts = [a for a in alerts if a.property_id == property_id]

    # Determine overall status
    status_val = "on_track"
    priority_actions = []

    if readiness:
        if readiness.readiness_grade in ["D", "F"]:
            status_val = "at_risk"
            priority_actions.extend([r.action for r in readiness.recommendations[:3]])
        elif readiness.readiness_grade == "C":
            status_val = "needs_attention"

    critical_count = len([a for a in property_alerts if a.severity == "critical"])
    if critical_count > 0:
        status_val = "at_risk"

    return RenewalSummaryResponse(
        property_id=property_id,
        property_name=forecast.property_name if forecast else (readiness.property_name if readiness else "Unknown"),
        next_expiration_date=forecast.current_expiration_date if forecast else None,
        days_until_expiration=(
            (forecast.current_expiration_date - date.today()).days
            if forecast and forecast.current_expiration_date
            else None
        ),
        forecast=forecast_response,
        readiness_score=readiness.readiness_score if readiness else None,
        readiness_grade=readiness.readiness_grade if readiness else None,
        missing_documents=len([
            d for d in (readiness.required_documents if readiness else [])
            if d.status == "missing"
        ]),
        market_condition=market.market_condition if market else None,
        negotiation_points=market.negotiation_leverage[:3] if market else [],
        active_alerts=len(property_alerts),
        critical_alerts=critical_count,
        renewal_status=status_val,
        priority_actions=priority_actions,
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _forecast_result_to_response(result) -> RenewalForecastResponse:
    """Convert ForecastResult to response schema."""
    days = (result.current_expiration_date - date.today()).days if result.current_expiration_date else 0

    return RenewalForecastResponse(
        id=result.property_id,  # Using property_id since we don't have forecast ID in result
        property_id=result.property_id,
        property_name=result.property_name,
        program_id=result.program_id,
        policy_id=result.policy_id,
        renewal_year=result.renewal_year,
        current_expiration_date=result.current_expiration_date,
        days_until_expiration=days,
        current_premium=result.current_premium,
        rule_based_estimate=result.rule_based_estimate,
        rule_based_change_pct=result.rule_based_change_pct,
        llm_prediction=ForecastRangeSchema(
            low=result.llm_predicted_low or Decimal("0"),
            mid=result.llm_predicted_mid or Decimal("0"),
            high=result.llm_predicted_high or Decimal("0"),
        ) if result.llm_predicted_mid else None,
        llm_confidence_score=result.llm_confidence_score,
        factor_breakdown={
            name: FactorBreakdownSchema(
                weight=factor.weight,
                impact=factor.impact,
                reasoning=factor.reasoning,
            )
            for name, factor in result.factor_breakdown.items()
        } if result.factor_breakdown else None,
        reasoning=result.reasoning,
        market_context=result.market_context,
        negotiation_points=result.negotiation_points,
        status="active",
        forecast_date=result.forecast_date,
        model_used=result.model_used,
        latency_ms=result.latency_ms,
    )


def _readiness_result_to_response(result) -> RenewalReadinessResponse:
    """Convert ReadinessResult to response schema."""
    return RenewalReadinessResponse(
        property_id=result.property_id,
        property_name=result.property_name,
        target_renewal_date=result.target_renewal_date,
        days_until_renewal=result.days_until_renewal,
        readiness_score=result.readiness_score,
        readiness_grade=result.readiness_grade,
        required_documents=[
            DocumentStatusSchema(
                type=d.type,
                label=d.label,
                status=d.status,
                document_id=d.document_id,
                filename=d.filename,
                age_days=d.age_days,
                verified=d.verified,
                extracted_data=d.extracted_data,
                issues=d.issues,
            )
            for d in result.required_documents
        ],
        recommended_documents=[
            DocumentStatusSchema(
                type=d.type,
                label=d.label,
                status=d.status,
                document_id=d.document_id,
                filename=d.filename,
                age_days=d.age_days,
                verified=d.verified,
                extracted_data=d.extracted_data,
                issues=d.issues,
            )
            for d in result.recommended_documents
        ],
        verification_summary=result.verification_summary,
        data_consistency_issues=result.data_consistency_issues,
        issues=[
            ReadinessIssueSchema(
                severity=i.severity,
                issue=i.issue,
                impact=i.impact,
            )
            for i in result.issues
        ],
        recommendations=[
            ReadinessRecommendationSchema(
                priority=r.priority,
                action=r.action,
                deadline=r.deadline,
            )
            for r in result.recommendations
        ],
        milestones=[
            TimelineMilestoneSchema(
                days_before_renewal=m.days_before_renewal,
                action=m.action,
                status=m.status,
            )
            for m in result.milestones
        ],
        assessment_date=result.assessment_date,
        status=result.status,
        model_used=result.model_used,
        latency_ms=result.latency_ms,
    )


def _market_context_result_to_response(result) -> MarketContextResponse:
    """Convert MarketContextResult to response schema."""
    return MarketContextResponse(
        property_id=result.property_id,
        property_name=result.property_name,
        analysis_date=result.analysis_date,
        valid_until=result.valid_until,
        market_condition=result.market_condition,
        market_condition_reasoning=result.market_condition_reasoning,
        property_risk_profile=result.property_risk_profile,
        carrier_relationship_assessment=result.carrier_relationship_assessment,
        policy_analysis=PolicyAnalysisSchema(
            key_exclusions=result.policy_analysis.key_exclusions,
            notable_sublimits=result.policy_analysis.notable_sublimits,
            unusual_terms=result.policy_analysis.unusual_terms,
            coverage_strengths=result.policy_analysis.coverage_strengths,
            coverage_weaknesses=result.policy_analysis.coverage_weaknesses,
        ) if result.policy_analysis else None,
        yoy_changes=YoYChangeSchema(
            premium_change_pct=result.yoy_changes.premium_change_pct,
            limit_changes=result.yoy_changes.limit_changes,
            deductible_changes=result.yoy_changes.deductible_changes,
            new_exclusions=result.yoy_changes.new_exclusions,
            removed_coverages=result.yoy_changes.removed_coverages,
        ) if result.yoy_changes else None,
        negotiation_leverage=result.negotiation_leverage,
        negotiation_recommendations=[
            NegotiationRecommendationSchema(
                action=r.action,
                priority=r.priority,
                rationale=r.rationale,
            )
            for r in result.negotiation_recommendations
        ],
        risk_insights=result.risk_insights,
        executive_summary=result.executive_summary,
        status=result.status,
        model_used=result.model_used,
        latency_ms=result.latency_ms,
    )


# =============================================================================
# Policy Comparison Endpoints (Phase 4.4.2)
# =============================================================================


@router.post("/compare/policies", response_model=PolicyComparisonResponse)
async def compare_policies(
    request: ComparePoliciesRequest,
    db: AsyncSessionDep,
) -> PolicyComparisonResponse:
    """Compare two policies.

    Compare any two policies with optional LLM-powered analysis.
    By default, only policies of the same type can be compared.

    Args:
        request: Comparison request with policy IDs and options.

    Returns:
        PolicyComparisonResponse with detailed comparison.
    """
    service = PolicyComparisonService(db)

    try:
        result = await service.compare_policies(
            policy_a_id=request.policy_a_id,
            policy_b_id=request.policy_b_id,
            allow_cross_type=request.allow_cross_type,
            include_llm_analysis=request.include_llm_analysis,
            comparison_type="arbitrary",
        )
    except PolicyComparisonError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        if "types don't match" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return _policy_comparison_result_to_response(result)


@router.post("/compare/programs", response_model=ProgramComparisonResponse)
async def compare_programs(
    request: CompareProgramsRequest,
    db: AsyncSessionDep,
) -> ProgramComparisonResponse:
    """Compare two insurance programs (year-over-year).

    Compare insurance programs across years for a property.
    Includes aggregate premium/TIV comparison and individual policy comparisons.

    Args:
        request: Comparison request with property ID and years.

    Returns:
        ProgramComparisonResponse with detailed comparison.
    """
    service = PolicyComparisonService(db)

    try:
        result = await service.compare_programs(
            property_id=request.property_id,
            program_a_year=request.program_a_year,
            program_b_year=request.program_b_year,
            include_policy_details=request.include_policy_details,
            include_llm_analysis=request.include_llm_analysis,
        )
    except PolicyComparisonError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return _program_comparison_result_to_response(result)


def _policy_comparison_result_to_response(result) -> PolicyComparisonResponse:
    """Convert PolicyComparisonResult to response schema."""
    return PolicyComparisonResponse(
        comparison_id=result.comparison_id,
        comparison_type=result.comparison_type,
        comparison_date=result.comparison_date,
        policy_a=PolicySummarySchema(
            id=result.policy_a.id,
            policy_number=result.policy_a.policy_number,
            policy_type=result.policy_a.policy_type,
            carrier_name=result.policy_a.carrier_name,
            effective_date=result.policy_a.effective_date,
            expiration_date=result.policy_a.expiration_date,
            premium=result.policy_a.premium,
            total_limit=result.policy_a.total_limit,
            coverage_count=result.policy_a.coverage_count,
        ),
        policy_b=PolicySummarySchema(
            id=result.policy_b.id,
            policy_number=result.policy_b.policy_number,
            policy_type=result.policy_b.policy_type,
            carrier_name=result.policy_b.carrier_name,
            effective_date=result.policy_b.effective_date,
            expiration_date=result.policy_b.expiration_date,
            premium=result.policy_b.premium,
            total_limit=result.policy_b.total_limit,
            coverage_count=result.policy_b.coverage_count,
        ),
        premium_change=result.premium_change,
        premium_change_pct=result.premium_change_pct,
        coverages_added=result.coverages_added,
        coverages_removed=result.coverages_removed,
        coverages_changed=[
            CoverageComparisonSchema(
                coverage_name=c.coverage_name,
                status=c.status,
                policy_a_limit=c.policy_a_limit,
                policy_a_deductible=c.policy_a_deductible,
                policy_a_sublimit=c.policy_a_sublimit,
                policy_b_limit=c.policy_b_limit,
                policy_b_deductible=c.policy_b_deductible,
                policy_b_sublimit=c.policy_b_sublimit,
                limit_change=c.limit_change,
                limit_change_pct=c.limit_change_pct,
                deductible_change=c.deductible_change,
                deductible_change_pct=c.deductible_change_pct,
                impact_assessment=c.impact_assessment,
            )
            for c in result.coverages_changed
        ],
        coverages_unchanged=result.coverages_unchanged,
        total_limit_change=result.total_limit_change,
        total_limit_change_pct=result.total_limit_change_pct,
        avg_deductible_change_pct=result.avg_deductible_change_pct,
        executive_summary=result.executive_summary,
        key_changes=result.key_changes,
        risk_implications=result.risk_implications,
        recommendations=result.recommendations,
        model_used=result.model_used,
        latency_ms=result.latency_ms,
    )


def _program_comparison_result_to_response(result) -> ProgramComparisonResponse:
    """Convert ProgramComparisonResult to response schema."""
    return ProgramComparisonResponse(
        comparison_id=result.comparison_id,
        property_id=result.property_id,
        property_name=result.property_name,
        comparison_date=result.comparison_date,
        program_a_year=result.program_a_year,
        program_b_year=result.program_b_year,
        program_a_id=result.program_a_id,
        program_b_id=result.program_b_id,
        total_premium_a=result.total_premium_a,
        total_premium_b=result.total_premium_b,
        premium_change=result.premium_change,
        premium_change_pct=result.premium_change_pct,
        total_insured_value_a=result.total_insured_value_a,
        total_insured_value_b=result.total_insured_value_b,
        tiv_change=result.tiv_change,
        tiv_change_pct=result.tiv_change_pct,
        policy_comparisons=[
            _policy_comparison_result_to_response(pc)
            for pc in result.policy_comparisons
        ],
        policies_added=[
            PolicySummarySchema(
                id=p.id,
                policy_number=p.policy_number,
                policy_type=p.policy_type,
                carrier_name=p.carrier_name,
                effective_date=p.effective_date,
                expiration_date=p.expiration_date,
                premium=p.premium,
                total_limit=p.total_limit,
                coverage_count=p.coverage_count,
            )
            for p in result.policies_added
        ],
        policies_removed=[
            PolicySummarySchema(
                id=p.id,
                policy_number=p.policy_number,
                policy_type=p.policy_type,
                carrier_name=p.carrier_name,
                effective_date=p.effective_date,
                expiration_date=p.expiration_date,
                premium=p.premium,
                total_limit=p.total_limit,
                coverage_count=p.coverage_count,
            )
            for p in result.policies_removed
        ],
        executive_summary=result.executive_summary,
        key_changes=result.key_changes,
        coverage_gaps_identified=result.coverage_gaps_identified,
        recommendations=result.recommendations,
        model_used=result.model_used,
        latency_ms=result.latency_ms,
    )
