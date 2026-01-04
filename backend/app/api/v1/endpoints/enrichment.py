"""Parallel AI Enrichment API Endpoints (Phase 4.4 External Integrations).

Provides endpoints for:
- Market Intelligence (live research)
- Property Risk Enrichment
- Carrier Research
- Lender Requirements Lookup
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.schemas.enrichment import (
    # Market Intelligence
    MarketIntelligenceRequest,
    MarketIntelligenceResponse,
    MarketTrendSchema,
    CarrierAppetiteSchema,
    # Property Risk
    PropertyRiskEnrichmentRequest,
    PropertyRiskEnrichmentResponse,
    FloodRiskSchema,
    FireProtectionSchema,
    WeatherRiskSchema,
    CrimeRiskSchema,
    EnvironmentalRiskSchema,
    # Carrier Research
    CarrierResearchRequest,
    CarrierResearchResponse,
    CarrierRatingsSchema,
    CarrierSpecialtySchema,
    CarrierNewsSchema,
    # Lender Requirements
    LenderRequirementsRequest,
    LenderRequirementsResponse,
    CoverageRequirementSchema,
    DeductibleRequirementSchema,
    EndorsementRequirementSchema,
)
from app.services.market_intelligence_service import (
    MarketIntelligenceService,
    MarketIntelligenceError,
)
from app.services.property_risk_service import (
    PropertyRiskService,
    PropertyRiskError,
)
from app.services.carrier_research_service import (
    CarrierResearchService,
    CarrierResearchError,
)
from app.services.lender_requirements_service import (
    LenderRequirementsService,
    LenderRequirementsError,
)

router = APIRouter()


# =============================================================================
# Market Intelligence Endpoints
# =============================================================================


@router.get("/market-intelligence/{property_id}", response_model=MarketIntelligenceResponse)
async def get_market_intelligence(
    property_id: str,
    db: AsyncSessionDep,
    include_raw_research: bool = Query(False, description="Include raw Parallel AI research text"),
) -> MarketIntelligenceResponse:
    """Get live market intelligence for a property.

    Uses Parallel AI to research current market conditions including:
    - Rate trends and forecasts
    - Carrier appetite
    - Regulatory changes
    - Market benchmarks

    This endpoint performs real-time web research and may take 30-120 seconds.

    Args:
        property_id: Property ID.
        include_raw_research: Include raw research text in response.

    Returns:
        MarketIntelligenceResponse with current market data.
    """
    service = MarketIntelligenceService(db)

    try:
        result = await service.get_market_intelligence(
            property_id=property_id,
            include_raw_research=include_raw_research,
        )
    except MarketIntelligenceError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        if "not configured" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return MarketIntelligenceResponse(
        property_id=result.property_id,
        property_type=result.property_type,
        state=result.state,
        research_date=result.research_date,
        rate_trend=MarketTrendSchema(
            rate_change_pct=result.rate_trend.rate_change_pct,
            rate_change_range=result.rate_trend.rate_change_range,
            direction=result.rate_trend.direction,
            confidence=result.rate_trend.confidence,
        ),
        rate_trend_reasoning=result.rate_trend_reasoning,
        key_factors=result.key_factors,
        factor_details=result.factor_details,
        carrier_appetite=[
            CarrierAppetiteSchema(
                carrier_name=ca.carrier_name,
                appetite=ca.appetite,
                notes=ca.notes,
            )
            for ca in result.carrier_appetite
        ],
        carrier_summary=result.carrier_summary,
        forecast_6mo=result.forecast_6mo,
        forecast_12mo=result.forecast_12mo,
        regulatory_changes=result.regulatory_changes,
        market_developments=result.market_developments,
        premium_benchmark=result.premium_benchmark,
        rate_per_sqft=result.rate_per_sqft,
        sources=result.sources,
        parallel_latency_ms=result.parallel_latency_ms,
        gemini_latency_ms=result.gemini_latency_ms,
        total_latency_ms=result.total_latency_ms,
        raw_research=result.raw_research,
    )


# =============================================================================
# Property Risk Enrichment Endpoints
# =============================================================================


@router.post("/properties/{property_id}/enrich-risk", response_model=PropertyRiskEnrichmentResponse)
async def enrich_property_risk(
    property_id: str,
    db: AsyncSessionDep,
    request: PropertyRiskEnrichmentRequest | None = None,
) -> PropertyRiskEnrichmentResponse:
    """Enrich property with external risk data.

    Uses Parallel AI to research property risk factors including:
    - FEMA flood zone
    - Fire protection class
    - Weather/CAT exposure
    - Crime statistics
    - Environmental hazards

    This endpoint performs real-time web research and may take 30-120 seconds.

    Args:
        property_id: Property ID.
        request: Optional enrichment options.

    Returns:
        PropertyRiskEnrichmentResponse with risk data.
    """
    service = PropertyRiskService(db)
    include_raw = request.include_raw_research if request else False
    update_prop = request.update_property if request else False

    try:
        if update_prop:
            # Enrich and update property record
            await service.update_property_with_risk_data(property_id)
            await db.commit()

        result = await service.enrich_property_risk(
            property_id=property_id,
            include_raw_research=include_raw,
        )
    except PropertyRiskError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        if "no address" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        if "not configured" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return PropertyRiskEnrichmentResponse(
        property_id=result.property_id,
        address=result.address,
        enrichment_date=result.enrichment_date,
        flood_risk=FloodRiskSchema(
            zone=result.flood_risk.zone,
            zone_description=result.flood_risk.zone_description,
            risk_level=result.flood_risk.risk_level,
            source=result.flood_risk.source,
        ),
        fire_protection=FireProtectionSchema(
            protection_class=result.fire_protection.protection_class,
            fire_station_distance_miles=result.fire_protection.fire_station_distance_miles,
            hydrant_distance_feet=result.fire_protection.hydrant_distance_feet,
            source=result.fire_protection.source,
        ),
        weather_risk=WeatherRiskSchema(
            hurricane_risk=result.weather_risk.hurricane_risk,
            tornado_risk=result.weather_risk.tornado_risk,
            hail_risk=result.weather_risk.hail_risk,
            wildfire_risk=result.weather_risk.wildfire_risk,
            earthquake_risk=result.weather_risk.earthquake_risk,
            historical_events=result.weather_risk.historical_events,
        ),
        crime_risk=CrimeRiskSchema(
            crime_index=result.crime_risk.crime_index,
            crime_grade=result.crime_risk.crime_grade,
            risk_level=result.crime_risk.risk_level,
            notes=result.crime_risk.notes,
        ),
        environmental_risk=EnvironmentalRiskSchema(
            hazards=result.environmental_risk.hazards,
            superfund_nearby=result.environmental_risk.superfund_nearby,
            industrial_nearby=result.environmental_risk.industrial_nearby,
            risk_level=result.environmental_risk.risk_level,
        ),
        recent_permits=result.recent_permits,
        violations=result.violations,
        infrastructure_issues=result.infrastructure_issues,
        overall_risk_score=result.overall_risk_score,
        risk_summary=result.risk_summary,
        insurance_implications=result.insurance_implications,
        sources=result.sources,
        parallel_latency_ms=result.parallel_latency_ms,
        gemini_latency_ms=result.gemini_latency_ms,
        total_latency_ms=result.total_latency_ms,
        raw_research=result.raw_research,
        property_updated=update_prop,
    )


# =============================================================================
# Carrier Research Endpoints
# =============================================================================


@router.post("/carriers/research", response_model=CarrierResearchResponse)
async def research_carrier(
    request: CarrierResearchRequest,
    db: AsyncSessionDep,
) -> CarrierResearchResponse:
    """Research a carrier's financial strength and market position.

    Uses Parallel AI to research carrier information including:
    - A.M. Best and other ratings
    - Financial strength
    - Specialty areas
    - Market appetite
    - Recent news

    This endpoint performs real-time web research and may take 30-120 seconds.

    Args:
        request: Carrier research request with carrier name.

    Returns:
        CarrierResearchResponse with carrier data.
    """
    service = CarrierResearchService(db)

    try:
        result = await service.research_carrier(
            carrier_name=request.carrier_name,
            property_type=request.property_type,
            include_raw_research=request.include_raw_research,
        )
    except CarrierResearchError as e:
        if "not configured" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return CarrierResearchResponse(
        carrier_name=result.carrier_name,
        research_date=result.research_date,
        ratings=CarrierRatingsSchema(
            am_best_rating=result.ratings.am_best_rating,
            am_best_outlook=result.ratings.am_best_outlook,
            sp_rating=result.ratings.sp_rating,
            moodys_rating=result.ratings.moodys_rating,
            rating_date=result.ratings.rating_date,
        ),
        financial_strength=result.financial_strength,
        financial_summary=result.financial_summary,
        specialty_areas=[
            CarrierSpecialtySchema(
                line_of_business=s.line_of_business,
                expertise_level=s.expertise_level,
                notes=s.notes,
            )
            for s in result.specialty_areas
        ],
        primary_lines=result.primary_lines,
        market_position=result.market_position,
        geographic_focus=result.geographic_focus,
        target_segments=result.target_segments,
        commercial_property_appetite=result.commercial_property_appetite,
        appetite_notes=result.appetite_notes,
        recent_news=[
            CarrierNewsSchema(
                date=n.date,
                headline=n.headline,
                summary=n.summary,
                sentiment=n.sentiment,
                source=n.source,
            )
            for n in result.recent_news
        ],
        news_summary=result.news_summary,
        customer_satisfaction=result.customer_satisfaction,
        claims_reputation=result.claims_reputation,
        concerns=result.concerns,
        regulatory_issues=result.regulatory_issues,
        sources=result.sources,
        parallel_latency_ms=result.parallel_latency_ms,
        gemini_latency_ms=result.gemini_latency_ms,
        total_latency_ms=result.total_latency_ms,
        raw_research=result.raw_research,
    )


@router.get("/carriers/{carrier_name}/research", response_model=CarrierResearchResponse)
async def get_carrier_research(
    carrier_name: str,
    db: AsyncSessionDep,
    property_type: str | None = Query(None, description="Property type for context"),
    include_raw_research: bool = Query(False, description="Include raw research text"),
) -> CarrierResearchResponse:
    """Research a carrier by name (GET endpoint).

    Convenience endpoint that takes carrier name as path parameter.

    Args:
        carrier_name: Name of the carrier.
        property_type: Optional property type for context.
        include_raw_research: Include raw research text.

    Returns:
        CarrierResearchResponse with carrier data.
    """
    service = CarrierResearchService(db)

    try:
        result = await service.research_carrier(
            carrier_name=carrier_name,
            property_type=property_type,
            include_raw_research=include_raw_research,
        )
    except CarrierResearchError as e:
        if "not configured" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return CarrierResearchResponse(
        carrier_name=result.carrier_name,
        research_date=result.research_date,
        ratings=CarrierRatingsSchema(
            am_best_rating=result.ratings.am_best_rating,
            am_best_outlook=result.ratings.am_best_outlook,
            sp_rating=result.ratings.sp_rating,
            moodys_rating=result.ratings.moodys_rating,
            rating_date=result.ratings.rating_date,
        ),
        financial_strength=result.financial_strength,
        financial_summary=result.financial_summary,
        specialty_areas=[
            CarrierSpecialtySchema(
                line_of_business=s.line_of_business,
                expertise_level=s.expertise_level,
                notes=s.notes,
            )
            for s in result.specialty_areas
        ],
        primary_lines=result.primary_lines,
        market_position=result.market_position,
        geographic_focus=result.geographic_focus,
        target_segments=result.target_segments,
        commercial_property_appetite=result.commercial_property_appetite,
        appetite_notes=result.appetite_notes,
        recent_news=[
            CarrierNewsSchema(
                date=n.date,
                headline=n.headline,
                summary=n.summary,
                sentiment=n.sentiment,
                source=n.source,
            )
            for n in result.recent_news
        ],
        news_summary=result.news_summary,
        customer_satisfaction=result.customer_satisfaction,
        claims_reputation=result.claims_reputation,
        concerns=result.concerns,
        regulatory_issues=result.regulatory_issues,
        sources=result.sources,
        parallel_latency_ms=result.parallel_latency_ms,
        gemini_latency_ms=result.gemini_latency_ms,
        total_latency_ms=result.total_latency_ms,
        raw_research=result.raw_research,
    )


# =============================================================================
# Lender Requirements Endpoints
# =============================================================================


@router.post("/lenders/requirements", response_model=LenderRequirementsResponse)
async def lookup_lender_requirements(
    request: LenderRequirementsRequest,
    db: AsyncSessionDep,
) -> LenderRequirementsResponse:
    """Lookup lender-specific insurance requirements.

    Uses Parallel AI to research lender requirements including:
    - Coverage minimums
    - Deductible maximums
    - Required endorsements
    - Carrier rating requirements

    This endpoint performs real-time web research and may take 30-120 seconds.

    Args:
        request: Lender requirements request.

    Returns:
        LenderRequirementsResponse with requirements data.
    """
    service = LenderRequirementsService(db)

    try:
        result = await service.lookup_requirements(
            lender_name=request.lender_name,
            loan_type=request.loan_type,
            include_raw_research=request.include_raw_research,
        )
    except LenderRequirementsError as e:
        if "not configured" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return _lender_result_to_response(result)


@router.get("/lenders/{lender_name}/requirements", response_model=LenderRequirementsResponse)
async def get_lender_requirements(
    lender_name: str,
    db: AsyncSessionDep,
    loan_type: str | None = Query(None, description="Type of loan"),
    include_raw_research: bool = Query(False, description="Include raw research text"),
) -> LenderRequirementsResponse:
    """Lookup lender requirements by name (GET endpoint).

    Convenience endpoint that takes lender name as path parameter.

    Args:
        lender_name: Name of the lender.
        loan_type: Optional loan type.
        include_raw_research: Include raw research text.

    Returns:
        LenderRequirementsResponse with requirements data.
    """
    service = LenderRequirementsService(db)

    try:
        result = await service.lookup_requirements(
            lender_name=lender_name,
            loan_type=loan_type,
            include_raw_research=include_raw_research,
        )
    except LenderRequirementsError as e:
        if "not configured" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return _lender_result_to_response(result)


def _lender_result_to_response(result) -> LenderRequirementsResponse:
    """Convert LenderRequirementsResult to response schema."""
    return LenderRequirementsResponse(
        lender_name=result.lender_name,
        loan_type=result.loan_type,
        research_date=result.research_date,
        property_coverage=_coverage_to_schema(result.property_coverage),
        liability_coverage=_coverage_to_schema(result.liability_coverage),
        umbrella_coverage=_coverage_to_schema(result.umbrella_coverage),
        flood_coverage=_coverage_to_schema(result.flood_coverage),
        wind_coverage=_coverage_to_schema(result.wind_coverage),
        other_coverages=[
            _coverage_to_schema(c) for c in result.other_coverages if c
        ],
        deductible_requirements=[
            DeductibleRequirementSchema(
                coverage_type=d.coverage_type,
                maximum_amount=d.maximum_amount,
                maximum_percentage=d.maximum_percentage,
                description=d.description,
            )
            for d in result.deductible_requirements
        ],
        max_property_deductible_pct=result.max_property_deductible_pct,
        max_property_deductible_flat=result.max_property_deductible_flat,
        required_endorsements=[
            EndorsementRequirementSchema(
                endorsement_name=e.endorsement_name,
                description=e.description,
                required=e.required,
            )
            for e in result.required_endorsements
        ],
        mortgagee_clause_required=result.mortgagee_clause_required,
        notice_of_cancellation_days=result.notice_of_cancellation_days,
        waiver_of_subrogation_required=result.waiver_of_subrogation_required,
        minimum_carrier_rating=result.minimum_carrier_rating,
        acceptable_rating_agencies=result.acceptable_rating_agencies,
        special_requirements=result.special_requirements,
        coastal_requirements=result.coastal_requirements,
        earthquake_requirements=result.earthquake_requirements,
        source_document=result.source_document,
        source_section=result.source_section,
        sources=result.sources,
        parallel_latency_ms=result.parallel_latency_ms,
        gemini_latency_ms=result.gemini_latency_ms,
        total_latency_ms=result.total_latency_ms,
        raw_research=result.raw_research,
    )


def _coverage_to_schema(coverage) -> CoverageRequirementSchema | None:
    """Convert CoverageRequirement to schema."""
    if not coverage:
        return None
    return CoverageRequirementSchema(
        coverage_type=coverage.coverage_type,
        minimum_limit=coverage.minimum_limit,
        limit_description=coverage.limit_description,
        required=coverage.required,
        notes=coverage.notes,
    )
