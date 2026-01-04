"""Schemas for Parallel AI enrichment features.

Includes schemas for:
- Market Intelligence
- Property Risk Enrichment
- Carrier Research
- Lender Requirements
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# =============================================================================
# Market Intelligence Schemas
# =============================================================================


class MarketTrendSchema(BaseModel):
    """Market trend information."""
    rate_change_pct: float | None = None
    rate_change_range: str | None = None
    direction: str = "stable"
    confidence: str = "medium"


class CarrierAppetiteSchema(BaseModel):
    """Carrier appetite in the market."""
    carrier_name: str
    appetite: str
    notes: str | None = None


class MarketIntelligenceRequest(BaseModel):
    """Request for market intelligence."""
    include_raw_research: bool = Field(False, description="Include raw research text")


class MarketIntelligenceResponse(BaseModel):
    """Response with market intelligence data."""
    property_id: str
    property_type: str
    state: str
    research_date: datetime

    # Rate trends
    rate_trend: MarketTrendSchema
    rate_trend_reasoning: str | None

    # Key factors
    key_factors: list[str]
    factor_details: dict[str, str] | None = None

    # Carrier landscape
    carrier_appetite: list[CarrierAppetiteSchema]
    carrier_summary: str | None

    # Forecasts
    forecast_6mo: str | None
    forecast_12mo: str | None

    # Regulatory
    regulatory_changes: list[str]
    market_developments: list[str]

    # Benchmarks
    premium_benchmark: str | None
    rate_per_sqft: float | None

    # Sources
    sources: list[str]

    # Metadata
    parallel_latency_ms: int
    gemini_latency_ms: int
    total_latency_ms: int
    raw_research: str | None = None


# =============================================================================
# Property Risk Enrichment Schemas
# =============================================================================


class FloodRiskSchema(BaseModel):
    """Flood risk data."""
    zone: str | None = None
    zone_description: str | None = None
    risk_level: str = "unknown"
    source: str | None = None


class FireProtectionSchema(BaseModel):
    """Fire protection data."""
    protection_class: str | None = None
    fire_station_distance_miles: float | None = None
    hydrant_distance_feet: float | None = None
    source: str | None = None


class WeatherRiskSchema(BaseModel):
    """Weather/CAT risk data."""
    hurricane_risk: str = "unknown"
    tornado_risk: str = "unknown"
    hail_risk: str = "unknown"
    wildfire_risk: str = "unknown"
    earthquake_risk: str = "unknown"
    historical_events: list[str] = []


class CrimeRiskSchema(BaseModel):
    """Crime risk data."""
    crime_index: int | None = None
    crime_grade: str | None = None
    risk_level: str = "unknown"
    notes: str | None = None


class EnvironmentalRiskSchema(BaseModel):
    """Environmental hazard data."""
    hazards: list[str] = []
    superfund_nearby: bool = False
    industrial_nearby: bool = False
    risk_level: str = "unknown"


class PropertyRiskEnrichmentRequest(BaseModel):
    """Request for property risk enrichment."""
    include_raw_research: bool = Field(False, description="Include raw research text")
    update_property: bool = Field(False, description="Update property record with enriched data")


class PropertyRiskEnrichmentResponse(BaseModel):
    """Response with property risk enrichment data."""
    property_id: str
    address: str
    enrichment_date: datetime

    # Risk assessments
    flood_risk: FloodRiskSchema
    fire_protection: FireProtectionSchema
    weather_risk: WeatherRiskSchema
    crime_risk: CrimeRiskSchema
    environmental_risk: EnvironmentalRiskSchema

    # Building info
    recent_permits: list[str]
    violations: list[str]
    infrastructure_issues: list[str]

    # Overall assessment
    overall_risk_score: int | None
    risk_summary: str | None
    insurance_implications: list[str]

    # Sources
    sources: list[str]

    # Metadata
    parallel_latency_ms: int
    gemini_latency_ms: int
    total_latency_ms: int
    raw_research: str | None = None

    # Update status
    property_updated: bool = False


# =============================================================================
# Carrier Research Schemas
# =============================================================================


class CarrierRatingsSchema(BaseModel):
    """Carrier financial ratings."""
    am_best_rating: str | None = None
    am_best_outlook: str | None = None
    sp_rating: str | None = None
    moodys_rating: str | None = None
    rating_date: str | None = None


class CarrierSpecialtySchema(BaseModel):
    """Carrier specialty area."""
    line_of_business: str
    expertise_level: str = "moderate"
    notes: str | None = None


class CarrierNewsSchema(BaseModel):
    """Recent carrier news."""
    date: str | None
    headline: str
    summary: str | None
    sentiment: str = "neutral"
    source: str | None = None


class CarrierResearchRequest(BaseModel):
    """Request for carrier research."""
    carrier_name: str = Field(..., description="Name of the carrier to research")
    property_type: str | None = Field(None, description="Property type for context")
    include_raw_research: bool = Field(False, description="Include raw research text")


class CarrierResearchResponse(BaseModel):
    """Response with carrier research data."""
    carrier_name: str
    research_date: datetime

    # Ratings
    ratings: CarrierRatingsSchema

    # Financial health
    financial_strength: str
    financial_summary: str | None

    # Specialties
    specialty_areas: list[CarrierSpecialtySchema]
    primary_lines: list[str]

    # Market position
    market_position: str | None
    geographic_focus: list[str]
    target_segments: list[str]

    # Appetite
    commercial_property_appetite: str
    appetite_notes: str | None

    # News
    recent_news: list[CarrierNewsSchema]
    news_summary: str | None

    # Customer experience
    customer_satisfaction: str | None
    claims_reputation: str | None

    # Concerns
    concerns: list[str]
    regulatory_issues: list[str]

    # Sources
    sources: list[str]

    # Metadata
    parallel_latency_ms: int
    gemini_latency_ms: int
    total_latency_ms: int
    raw_research: str | None = None


# =============================================================================
# Lender Requirements Schemas
# =============================================================================


class CoverageRequirementSchema(BaseModel):
    """Coverage requirement specification."""
    coverage_type: str
    minimum_limit: Decimal | None = None
    limit_description: str | None = None
    required: bool = True
    notes: str | None = None


class DeductibleRequirementSchema(BaseModel):
    """Deductible requirement specification."""
    coverage_type: str
    maximum_amount: Decimal | None = None
    maximum_percentage: float | None = None
    description: str | None = None


class EndorsementRequirementSchema(BaseModel):
    """Required endorsement specification."""
    endorsement_name: str
    description: str | None = None
    required: bool = True


class LenderRequirementsRequest(BaseModel):
    """Request for lender requirements lookup."""
    lender_name: str = Field(..., description="Name of the lender")
    loan_type: str | None = Field(None, description="Type of loan (conventional, FHA, Fannie Mae, etc.)")
    include_raw_research: bool = Field(False, description="Include raw research text")


class LenderRequirementsResponse(BaseModel):
    """Response with lender requirements data."""
    lender_name: str
    loan_type: str | None
    research_date: datetime

    # Coverage requirements
    property_coverage: CoverageRequirementSchema | None
    liability_coverage: CoverageRequirementSchema | None
    umbrella_coverage: CoverageRequirementSchema | None
    flood_coverage: CoverageRequirementSchema | None
    wind_coverage: CoverageRequirementSchema | None
    other_coverages: list[CoverageRequirementSchema]

    # Deductible requirements
    deductible_requirements: list[DeductibleRequirementSchema]
    max_property_deductible_pct: float | None
    max_property_deductible_flat: Decimal | None

    # Endorsements
    required_endorsements: list[EndorsementRequirementSchema]
    mortgagee_clause_required: bool
    notice_of_cancellation_days: int | None
    waiver_of_subrogation_required: bool

    # Carrier requirements
    minimum_carrier_rating: str | None
    acceptable_rating_agencies: list[str]

    # Special requirements
    special_requirements: list[str]
    coastal_requirements: str | None
    earthquake_requirements: str | None

    # Source information
    source_document: str | None
    source_section: str | None
    sources: list[str]

    # Metadata
    parallel_latency_ms: int
    gemini_latency_ms: int
    total_latency_ms: int
    raw_research: str | None = None
