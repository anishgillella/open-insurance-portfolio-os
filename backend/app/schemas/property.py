"""Property API schemas.

Schemas for property listing, detail views, and related data.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import AddressSchema


# ---------------------------------------------------------------------------
# Policy Summary Schema (for embedding in PropertyDetail)
# ---------------------------------------------------------------------------


class PolicySummaryItem(BaseModel):
    """Policy summary for property detail view."""

    id: str = Field(..., description="Policy ID")
    policy_number: str | None = Field(default=None, description="Policy number")
    policy_type: str = Field(..., description="Policy type")
    carrier: str | None = Field(default=None, description="Carrier name")
    effective_date: date | None = Field(default=None, description="Effective date")
    expiration_date: date | None = Field(default=None, description="Expiration date")
    premium: Decimal | None = Field(default=None, description="Premium amount")
    limit: Decimal | None = Field(default=None, description="Coverage limit")
    deductible: Decimal | None = Field(default=None, description="Deductible")
    status: Literal["active", "expired", "pending"] = Field(
        default="active", description="Policy status"
    )


# ---------------------------------------------------------------------------
# Building Schema
# ---------------------------------------------------------------------------


class BuildingSchema(BaseModel):
    """Building information within a property."""

    id: str = Field(..., description="Building ID")
    name: str | None = Field(default=None, description="Building name/identifier")
    units: int | None = Field(default=None, description="Number of units")
    stories: int | None = Field(default=None, description="Number of stories")
    sqft: int | None = Field(default=None, description="Square footage")
    year_built: int | None = Field(default=None, description="Year built")
    construction_type: str | None = Field(
        default=None, description="Construction type"
    )
    replacement_cost: Decimal | None = Field(
        default=None, description="Replacement cost"
    )


# ---------------------------------------------------------------------------
# Insurance Summary
# ---------------------------------------------------------------------------


class InsuranceSummarySchema(BaseModel):
    """Summary of insurance for a property."""

    total_insured_value: Decimal = Field(
        default=Decimal("0"), description="Total insured value"
    )
    total_annual_premium: Decimal = Field(
        default=Decimal("0"), description="Total annual premium"
    )
    policy_count: int = Field(default=0, description="Number of policies")
    next_expiration: date | None = Field(
        default=None, description="Next policy expiration date"
    )
    days_until_expiration: int | None = Field(
        default=None, description="Days until next expiration"
    )
    coverage_types: list[str] = Field(
        default_factory=list, description="List of coverage types"
    )


# ---------------------------------------------------------------------------
# Health Score Schema
# ---------------------------------------------------------------------------


class HealthScoreComponentsSchema(BaseModel):
    """Health score component breakdown."""

    coverage_adequacy: float = Field(default=0, description="Coverage adequacy score")
    policy_currency: float = Field(default=0, description="Policy currency score")
    deductible_risk: float = Field(default=0, description="Deductible risk score")
    coverage_breadth: float = Field(default=0, description="Coverage breadth score")
    lender_compliance: float = Field(default=0, description="Lender compliance score")
    documentation_quality: float = Field(
        default=0, description="Documentation quality score"
    )


class HealthScoreSchema(BaseModel):
    """Property health score information."""

    score: int = Field(default=0, description="Overall health score (0-100)")
    grade: str = Field(default="F", description="Letter grade (A-F)")
    components: HealthScoreComponentsSchema = Field(
        default_factory=HealthScoreComponentsSchema, description="Component scores"
    )
    trend: str = Field(default="stable", description="Trend direction")
    calculated_at: datetime | None = Field(
        default=None, description="Calculation timestamp"
    )


# ---------------------------------------------------------------------------
# Gaps Summary
# ---------------------------------------------------------------------------


class GapsSummarySchema(BaseModel):
    """Summary of coverage gaps for a property."""

    total_open: int = Field(default=0, description="Total open gaps")
    critical: int = Field(default=0, description="Critical gaps")
    warning: int = Field(default=0, description="Warning gaps")
    info: int = Field(default=0, description="Info gaps")


# ---------------------------------------------------------------------------
# Compliance Summary
# ---------------------------------------------------------------------------


class ComplianceSummarySchema(BaseModel):
    """Compliance summary for a property."""

    status: str = Field(
        default="no_requirements",
        description="Status: compliant, non_compliant, no_requirements",
    )
    lender_name: str | None = Field(default=None, description="Lender name")
    issues_count: int = Field(default=0, description="Number of compliance issues")


# ---------------------------------------------------------------------------
# Document Checklist Item
# ---------------------------------------------------------------------------


class DocumentChecklistItem(BaseModel):
    """Individual document type in the completeness checklist."""

    document_type: str = Field(..., description="Document type code")
    display_name: str = Field(..., description="Human-readable document name")
    description: str = Field(..., description="What this document contains")
    is_required: bool = Field(default=True, description="Whether this document is required")
    is_present: bool = Field(default=False, description="Whether this document has been uploaded")
    fields_provided: list[str] = Field(
        default_factory=list, description="Data fields this document provides when uploaded"
    )
    uploaded_file: str | None = Field(default=None, description="Name of uploaded file if present")


# ---------------------------------------------------------------------------
# Completeness Summary
# ---------------------------------------------------------------------------


class CompletenessSummarySchema(BaseModel):
    """Document completeness summary for a property."""

    percentage: float = Field(default=0, description="Completeness percentage")
    required_present: int = Field(
        default=0, description="Required documents present"
    )
    required_total: int = Field(default=0, description="Total required documents")
    optional_present: int = Field(
        default=0, description="Optional documents present"
    )
    optional_total: int = Field(default=0, description="Total optional documents")
    checklist: list[DocumentChecklistItem] = Field(
        default_factory=list, description="Document checklist with status"
    )


# ---------------------------------------------------------------------------
# Property List Item
# ---------------------------------------------------------------------------


class GapsCountSchema(BaseModel):
    """Gap counts by severity."""

    critical: int = Field(default=0, description="Critical gaps")
    warning: int = Field(default=0, description="Warning gaps")
    info: int = Field(default=0, description="Info gaps")


class PropertyListItem(BaseModel):
    """Property summary for list view."""

    id: str = Field(..., description="Property ID")
    name: str = Field(..., description="Property name")
    address: AddressSchema = Field(
        default_factory=AddressSchema, description="Property address"
    )
    property_type: str | None = Field(default=None, description="Property type")
    total_units: int | None = Field(default=None, description="Total units")
    total_buildings: int = Field(default=0, description="Number of buildings")
    year_built: int | None = Field(default=None, description="Year built")
    total_insured_value: Decimal = Field(
        default=Decimal("0"), description="Total insured value"
    )
    total_premium: Decimal = Field(
        default=Decimal("0"), description="Total annual premium"
    )
    health_score: int = Field(default=0, description="Health score (0-100)")
    health_grade: str = Field(default="F", description="Letter grade (A-F)")
    gaps_count: GapsCountSchema = Field(
        default_factory=GapsCountSchema, description="Gap counts by severity"
    )
    next_expiration: date | None = Field(
        default=None, description="Next policy expiration"
    )
    days_until_expiration: int | None = Field(
        default=None, description="Days until next expiration"
    )
    compliance_status: str = Field(
        default="no_requirements", description="Compliance status"
    )
    completeness_percentage: float = Field(default=0, description="Completeness percentage")
    coverage_types: list[str] = Field(
        default_factory=list, description="Types of coverage"
    )
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


# ---------------------------------------------------------------------------
# Property List Response
# ---------------------------------------------------------------------------


class PropertyListResponse(BaseModel):
    """Response for property list endpoint."""

    properties: list[PropertyListItem] = Field(
        default_factory=list, description="List of properties"
    )
    total_count: int = Field(default=0, description="Total number of properties")


# ---------------------------------------------------------------------------
# Property Detail Response
# ---------------------------------------------------------------------------


class PropertyDetail(BaseModel):
    """Detailed property information."""

    id: str = Field(..., description="Property ID")
    name: str = Field(..., description="Property name")
    external_id: str | None = Field(default=None, description="External ID")
    address: AddressSchema = Field(
        default_factory=AddressSchema, description="Property address"
    )
    property_type: str | None = Field(default=None, description="Property type")
    year_built: int | None = Field(default=None, description="Year built")
    construction_type: str | None = Field(
        default=None, description="Construction type"
    )
    total_units: int | None = Field(default=None, description="Total units")
    total_buildings: int = Field(default=0, description="Number of buildings")
    total_sqft: int | None = Field(default=None, description="Total square footage")

    # Protection
    has_sprinklers: bool | None = Field(default=None, description="Has sprinklers")
    protection_class: str | None = Field(
        default=None, description="Fire protection class"
    )

    # Risk factors
    flood_zone: str | None = Field(default=None, description="FEMA flood zone")
    earthquake_zone: str | None = Field(default=None, description="Earthquake zone")
    wind_zone: str | None = Field(default=None, description="Wind zone")

    # Related data
    buildings: list[BuildingSchema] = Field(
        default_factory=list, description="Buildings"
    )
    insurance_summary: InsuranceSummarySchema = Field(
        default_factory=InsuranceSummarySchema, description="Insurance summary"
    )
    health_score: HealthScoreSchema = Field(
        default_factory=HealthScoreSchema, description="Health score"
    )
    gaps_summary: GapsSummarySchema = Field(
        default_factory=GapsSummarySchema, description="Gaps summary"
    )
    compliance_summary: ComplianceSummarySchema = Field(
        default_factory=ComplianceSummarySchema, description="Compliance summary"
    )
    completeness: CompletenessSummarySchema = Field(
        default_factory=CompletenessSummarySchema, description="Completeness"
    )

    # Policies
    policies: list[PolicySummaryItem] = Field(
        default_factory=list, description="Policies associated with property"
    )

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Property Documents Response
# ---------------------------------------------------------------------------


class PropertyDocumentItem(BaseModel):
    """Document associated with a property."""

    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Filename")
    document_type: str | None = Field(default=None, description="Document type")
    classification: str | None = Field(
        default=None, description="Document classification"
    )
    status: str = Field(default="pending", description="Processing status")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    extraction_confidence: float | None = Field(
        default=None, description="Extraction confidence"
    )


class PropertyDocumentsResponse(BaseModel):
    """Response for property documents endpoint."""

    documents: list[PropertyDocumentItem] = Field(
        default_factory=list, description="List of documents"
    )
    total_count: int = Field(default=0, description="Total number of documents")
