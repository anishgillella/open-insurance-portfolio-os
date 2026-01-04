"""Policy API schemas.

Schemas for policy listing, detail views, coverages, and related data.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Carrier Schema
# ---------------------------------------------------------------------------


class CarrierSchema(BaseModel):
    """Insurance carrier information."""

    id: str | None = Field(default=None, description="Carrier ID")
    name: str = Field(..., description="Carrier name")
    am_best_rating: str | None = Field(default=None, description="A.M. Best rating")
    naic_number: str | None = Field(default=None, description="NAIC number")


# ---------------------------------------------------------------------------
# Insured Entity Schema
# ---------------------------------------------------------------------------


class InsuredEntitySchema(BaseModel):
    """Named insured entity information."""

    id: str | None = Field(default=None, description="Entity ID")
    name: str = Field(..., description="Entity name")
    entity_type: str | None = Field(default=None, description="Entity type (LLC, etc)")


# ---------------------------------------------------------------------------
# Coverage Schema
# ---------------------------------------------------------------------------


class CoverageSchema(BaseModel):
    """Policy coverage information."""

    id: str = Field(..., description="Coverage ID")
    coverage_name: str | None = Field(default=None, description="Coverage name")
    coverage_category: str | None = Field(
        default=None, description="Coverage category"
    )
    limit_amount: Decimal | None = Field(default=None, description="Coverage limit")
    limit_type: str | None = Field(default=None, description="Limit type")
    deductible_amount: Decimal | None = Field(
        default=None, description="Deductible amount"
    )
    deductible_type: str | None = Field(default=None, description="Deductible type")
    deductible_pct: float | None = Field(
        default=None, description="Deductible percentage"
    )
    coinsurance_pct: float | None = Field(
        default=None, description="Coinsurance percentage"
    )
    valuation_type: str | None = Field(default=None, description="Valuation type")
    waiting_period_hours: int | None = Field(
        default=None, description="Waiting period in hours"
    )


# ---------------------------------------------------------------------------
# Endorsement Schema
# ---------------------------------------------------------------------------


class EndorsementSchema(BaseModel):
    """Policy endorsement information."""

    id: str = Field(..., description="Endorsement ID")
    endorsement_number: str | None = Field(
        default=None, description="Endorsement number"
    )
    title: str | None = Field(default=None, description="Endorsement title")
    effective_date: date | None = Field(default=None, description="Effective date")
    premium_change: Decimal | None = Field(
        default=None, description="Premium change amount"
    )


# ---------------------------------------------------------------------------
# Additional Insured Schema
# ---------------------------------------------------------------------------


class AdditionalInsuredSchema(BaseModel):
    """Additional insured/mortgagee information."""

    name: str = Field(..., description="Name")
    type: str | None = Field(
        default=None, description="Type: mortgagee, additional_insured"
    )
    address: str | None = Field(default=None, description="Address")


# ---------------------------------------------------------------------------
# Source Document Schema
# ---------------------------------------------------------------------------


class SourceDocumentSchema(BaseModel):
    """Source document reference."""

    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Filename")
    document_type: str | None = Field(default=None, description="Document type")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


# ---------------------------------------------------------------------------
# Policy Dates Schema
# ---------------------------------------------------------------------------


class PolicyDatesSchema(BaseModel):
    """Policy date information."""

    effective_date: date | None = Field(default=None, description="Effective date")
    expiration_date: date | None = Field(default=None, description="Expiration date")
    days_until_expiration: int | None = Field(
        default=None, description="Days until expiration"
    )
    policy_term_months: int | None = Field(
        default=None, description="Policy term in months"
    )


# ---------------------------------------------------------------------------
# Policy Financials Schema
# ---------------------------------------------------------------------------


class PolicyFinancialsSchema(BaseModel):
    """Policy financial information."""

    annual_premium: Decimal | None = Field(default=None, description="Annual premium")
    taxes: Decimal | None = Field(default=None, description="Taxes")
    fees: Decimal | None = Field(default=None, description="Fees")
    total_cost: Decimal | None = Field(default=None, description="Total cost")


# ---------------------------------------------------------------------------
# Policy List Item
# ---------------------------------------------------------------------------


class PolicyListItem(BaseModel):
    """Policy summary for list view."""

    id: str = Field(..., description="Policy ID")
    policy_number: str | None = Field(default=None, description="Policy number")
    policy_type: str = Field(..., description="Policy type")
    carrier_name: str | None = Field(default=None, description="Carrier name")
    effective_date: date | None = Field(default=None, description="Effective date")
    expiration_date: date | None = Field(default=None, description="Expiration date")
    days_until_expiration: int | None = Field(
        default=None, description="Days until expiration"
    )
    status: str = Field(default="active", description="Policy status")
    annual_premium: Decimal | None = Field(default=None, description="Annual premium")
    coverage_count: int = Field(default=0, description="Number of coverages")
    property_name: str | None = Field(
        default=None, description="Associated property name"
    )
    property_id: str | None = Field(
        default=None, description="Associated property ID"
    )


# ---------------------------------------------------------------------------
# Policy List Response
# ---------------------------------------------------------------------------


class PolicyListResponse(BaseModel):
    """Response for policy list endpoint."""

    policies: list[PolicyListItem] = Field(
        default_factory=list, description="List of policies"
    )
    total_count: int = Field(default=0, description="Total number of policies")


# ---------------------------------------------------------------------------
# Property Policies Response
# ---------------------------------------------------------------------------


class PropertyPolicySummary(BaseModel):
    """Summary of policies for a property."""

    total_policies: int = Field(default=0, description="Total policies")
    total_premium: Decimal = Field(
        default=Decimal("0"), description="Total premium"
    )
    active_policies: int = Field(default=0, description="Active policies")
    expired_policies: int = Field(default=0, description="Expired policies")


class PropertyPoliciesResponse(BaseModel):
    """Response for property policies endpoint."""

    policies: list[PolicyListItem] = Field(
        default_factory=list, description="List of policies"
    )
    summary: PropertyPolicySummary = Field(
        default_factory=PropertyPolicySummary, description="Policy summary"
    )


# ---------------------------------------------------------------------------
# Policy Detail Response
# ---------------------------------------------------------------------------


class PolicyDetail(BaseModel):
    """Detailed policy information."""

    id: str = Field(..., description="Policy ID")
    policy_number: str | None = Field(default=None, description="Policy number")
    policy_type: str = Field(..., description="Policy type")

    # Related entities
    carrier: CarrierSchema | None = Field(default=None, description="Carrier info")
    insured_entity: InsuredEntitySchema | None = Field(
        default=None, description="Named insured"
    )

    # Dates
    dates: PolicyDatesSchema = Field(
        default_factory=PolicyDatesSchema, description="Policy dates"
    )

    # Financials
    financials: PolicyFinancialsSchema = Field(
        default_factory=PolicyFinancialsSchema, description="Financial info"
    )

    # Policy characteristics
    admitted: bool | None = Field(default=None, description="Admitted policy")
    form_type: str | None = Field(default=None, description="Form type")
    policy_form: str | None = Field(default=None, description="Policy form")

    # Coverages and endorsements
    coverages: list[CoverageSchema] = Field(
        default_factory=list, description="Coverages"
    )
    endorsements: list[EndorsementSchema] = Field(
        default_factory=list, description="Endorsements"
    )

    # Additional insureds
    additional_insureds: list[AdditionalInsuredSchema] = Field(
        default_factory=list, description="Additional insureds/mortgagees"
    )

    # Source documents
    source_documents: list[SourceDocumentSchema] = Field(
        default_factory=list, description="Source documents"
    )

    # Property info
    property_id: str | None = Field(default=None, description="Property ID")
    property_name: str | None = Field(default=None, description="Property name")

    # Quality
    extraction_confidence: float | None = Field(
        default=None, description="Extraction confidence"
    )
    needs_review: bool = Field(default=False, description="Needs manual review")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Policy Coverages Response
# ---------------------------------------------------------------------------


class PolicyCoveragesResponse(BaseModel):
    """Response for policy coverages endpoint."""

    coverages: list[CoverageSchema] = Field(
        default_factory=list, description="List of coverages"
    )
    total_count: int = Field(default=0, description="Total number of coverages")
