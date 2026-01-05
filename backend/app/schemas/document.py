"""Pydantic schemas for document ingestion and extraction.

This module defines comprehensive Pydantic schemas for insurance document
processing, including classification, extraction, and validation.

Key Features:
- NullSafeModel: Handles LLM null responses for boolean fields
- FlexibleNumericModel: Parses percentage strings, currency, and other LLM formats
- Field validators: Policy numbers, dates, amounts
- Shared mixins: Consistent patterns across extraction types
"""

from datetime import date, datetime
from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Numeric Parsing Utilities
# ---------------------------------------------------------------------------


def parse_flexible_numeric(value: Any) -> float | None:
    """Parse various numeric formats from LLM output.

    Handles:
    - Percentages: "2%", "5.5%" -> 0.02, 0.055 (as decimal)
    - Currency: "$1,000", "$1M", "$2.5B" -> 1000, 1000000, 2500000000
    - Plain numbers: "1000", 1000, 1000.50
    - Strings with commas: "1,234,567" -> 1234567
    - Words: "null", "N/A", "" -> None

    Args:
        value: The value to parse (string, int, float, or None)

    Returns:
        Parsed float value or None if unparseable
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        return None

    # Clean the string
    value = value.strip()

    # Handle empty or null-like values
    if not value or value.lower() in ("null", "n/a", "none", "-", ""):
        return None

    # Check if it's a percentage
    is_percentage = value.endswith("%")
    if is_percentage:
        value = value[:-1].strip()

    # Remove currency symbols and commas
    value = value.replace("$", "").replace(",", "").strip()

    # Handle shorthand (M for million, B for billion, K for thousand)
    multiplier = 1.0
    if value.upper().endswith("M"):
        multiplier = 1_000_000
        value = value[:-1].strip()
    elif value.upper().endswith("B"):
        multiplier = 1_000_000_000
        value = value[:-1].strip()
    elif value.upper().endswith("K"):
        multiplier = 1_000
        value = value[:-1].strip()

    try:
        result = float(value) * multiplier
        # If it was a percentage, convert to decimal (e.g., 2% -> 0.02)
        if is_percentage:
            result = result / 100.0
        return result
    except ValueError:
        return None


def parse_flexible_numeric_dict(d: dict[str, Any]) -> dict[str, float | None]:
    """Parse all values in a dictionary using flexible numeric parsing.

    Args:
        d: Dictionary with string keys and various value types

    Returns:
        Dictionary with parsed float values (or None for unparseable)
    """
    return {k: parse_flexible_numeric(v) for k, v in d.items()}


# ---------------------------------------------------------------------------
# Base Models and Mixins
# ---------------------------------------------------------------------------


def _is_bool_type(annotation: Any) -> bool:
    """Check if an annotation is a boolean type (bool, bool | None, Optional[bool])."""
    import types

    if annotation is bool:
        return True

    # Python 3.10+ uses types.UnionType for `X | Y` syntax
    if isinstance(annotation, types.UnionType):
        return bool in annotation.__args__

    # Handle typing.Union (e.g., Optional[bool], Union[bool, None])
    origin = getattr(annotation, "__origin__", None)
    if origin is not None:
        args = getattr(annotation, "__args__", ())
        return bool in args

    return False


class NullSafeModel(BaseModel):
    """Base model that converts None to default values for boolean fields.

    This handles LLM responses that return null for boolean fields,
    converting them to False (the typical default).

    For fields declared as `bool | None` or `Optional[bool]`, if the input
    value is None, it will be converted to the field's default (or False).
    """

    @model_validator(mode="before")
    @classmethod
    def convert_none_booleans(cls, data: Any) -> Any:
        """Convert None values to False for boolean fields."""
        if not isinstance(data, dict):
            return data

        # Get field info to identify boolean fields
        for field_name, field_info in cls.model_fields.items():
            annotation = field_info.annotation
            # Check if it's a boolean type (bool, bool | None, Optional[bool])
            if _is_bool_type(annotation):
                if field_name in data and data[field_name] is None:
                    # Use field default if available, otherwise False
                    default_val = field_info.default
                    if default_val is None or (hasattr(default_val, "__class__") and default_val.__class__.__name__ == "PydanticUndefinedType"):
                        default_val = False
                    data[field_name] = default_val

        return data


class ConfidenceMixin(BaseModel):
    """Mixin for models that include extraction confidence scores."""

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DateRangeMixin(BaseModel):
    """Mixin for models with effective/expiration date ranges."""

    effective_date: date | None = None
    expiration_date: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "DateRangeMixin":
        """Validate that effective_date is before expiration_date."""
        if self.effective_date and self.expiration_date:
            if self.effective_date > self.expiration_date:
                # Log warning but don't fail - LLM may have swapped dates
                pass  # Could swap dates or raise warning
        return self


class InsuredInfoMixin(BaseModel):
    """Mixin for models with named insured information."""

    named_insured: str | None = None
    insured_address: str | None = None


class PolicyIdentityMixin(BaseModel):
    """Mixin for models with policy identification fields."""

    policy_number: str | None = None
    carrier_name: str | None = None

    @field_validator("policy_number", mode="before")
    @classmethod
    def clean_policy_number(cls, v: Any) -> str | None:
        """Clean and validate policy number format."""
        if v is None:
            return None
        # Convert to string and strip whitespace
        v = str(v).strip()
        if not v:
            return None
        # Remove common artifacts from OCR
        v = re.sub(r"\s+", " ", v)  # Normalize whitespace
        return v


class AmountMixin(BaseModel):
    """Mixin providing amount validation."""

    @field_validator("*", mode="before")
    @classmethod
    def validate_amounts(cls, v: Any, info) -> Any:
        """Ensure amount fields are non-negative."""
        field_name = info.field_name
        # Check if this looks like an amount field
        amount_keywords = ["amount", "limit", "premium", "deductible", "value", "cost", "fee", "tax"]
        is_amount_field = any(kw in field_name.lower() for kw in amount_keywords)

        if is_amount_field and v is not None:
            try:
                num_val = float(v)
                if num_val < 0:
                    return abs(num_val)  # Convert negative to positive
            except (ValueError, TypeError):
                pass
        return v


class DocumentType(str, Enum):
    """Types of insurance documents."""

    POLICY = "policy"
    PROGRAM = "program"  # Multi-carrier insurance program with contract allocation
    COI = "coi"  # Certificate of Insurance
    EOP = "eop"  # Evidence of Property
    INVOICE = "invoice"
    SOV = "sov"  # Statement of Values
    LOSS_RUN = "loss_run"
    ENDORSEMENT = "endorsement"
    DECLARATION = "declaration"
    PROPOSAL = "proposal"  # Insurance proposal/quote comparison
    UNKNOWN = "unknown"


class PolicyType(str, Enum):
    """Types of insurance policies."""

    PROPERTY = "property"
    GENERAL_LIABILITY = "general_liability"
    UMBRELLA = "umbrella"
    EXCESS = "excess"
    FLOOD = "flood"
    EARTHQUAKE = "earthquake"
    TERRORISM = "terrorism"
    CRIME = "crime"
    CYBER = "cyber"
    EPL = "epl"  # Employment Practices Liability
    DNO = "dno"  # Directors & Officers
    AUTO = "auto"
    WORKERS_COMP = "workers_comp"
    BOILER_MACHINERY = "boiler_machinery"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Status of document processing stages."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Document Classification
# ---------------------------------------------------------------------------


class DocumentClassification(BaseModel):
    """Result of document classification."""

    document_type: DocumentType
    document_subtype: str | None = None
    policy_type: PolicyType | None = None
    confidence: float = Field(ge=0.0, le=1.0)

    # Quick metadata extracted during classification
    carrier_name: str | None = None
    policy_number: str | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    insured_name: str | None = None


# ---------------------------------------------------------------------------
# Coverage Extraction
# ---------------------------------------------------------------------------


class CoverageExtraction(BaseModel):
    """Extracted coverage details."""

    coverage_name: str
    coverage_category: str | None = None
    limit_amount: float | None = None
    limit_type: str | None = None  # e.g., "per occurrence", "aggregate"
    sublimit: float | None = None
    sublimit_applies_to: str | None = None
    deductible_amount: float | None = None
    deductible_type: str | None = None  # e.g., "per occurrence", "percentage"
    deductible_pct: float | None = None  # Matches DB column name (percentage 0-100)
    deductible_minimum: float | None = None
    deductible_maximum: float | None = None
    coinsurance_pct: float | None = None  # Matches DB column name
    waiting_period_hours: int | None = None
    valuation_type: str | None = None  # e.g., "RCV", "ACV"
    margin_clause_pct: float | None = None  # Matches DB column name
    exclusions: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    source_page: int | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Policy Extraction
# ---------------------------------------------------------------------------


class PolicyExtraction(NullSafeModel, DateRangeMixin, InsuredInfoMixin, PolicyIdentityMixin, ConfidenceMixin):
    """Extracted policy information.

    Inherits from:
    - NullSafeModel: Handles null boolean values from LLM
    - DateRangeMixin: Provides effective_date/expiration_date with validation
    - InsuredInfoMixin: Provides named_insured/insured_address
    - PolicyIdentityMixin: Provides policy_number/carrier_name with cleaning
    - ConfidenceMixin: Provides confidence score field
    """

    # Policy Identity
    policy_type: PolicyType

    # Premium
    premium: float | None = None
    taxes: float | None = None
    fees: float | None = None
    total_cost: float | None = None

    # Policy Characteristics
    admitted: bool | None = None
    form_type: str | None = None  # e.g., "special", "basic", "broad"
    policy_form: str | None = None  # e.g., "CP 00 10"

    # Coverages
    coverages: list[CoverageExtraction] = Field(default_factory=list)

    # Mortgagee/Loss Payee
    mortgagee_name: str | None = None
    mortgagee_clause: str | None = None
    loss_payee: str | None = None

    # Additional Information
    additional_insureds: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    special_conditions: list[str] = Field(default_factory=list)

    # Extraction metadata
    source_pages: list[int] = Field(default_factory=list)

    @field_validator("premium", "taxes", "fees", "total_cost", mode="before")
    @classmethod
    def validate_positive_amounts(cls, v: Any) -> float | None:
        """Ensure monetary amounts are non-negative."""
        if v is None:
            return None
        try:
            num_val = float(v)
            return abs(num_val) if num_val < 0 else num_val
        except (ValueError, TypeError):
            return None


# ---------------------------------------------------------------------------
# Certificate of Insurance Extraction
# ---------------------------------------------------------------------------


class COIPolicyReference(NullSafeModel):
    """Policy referenced on a COI."""

    insurer_letter: str | None = None  # A, B, C, etc.
    policy_type: PolicyType
    policy_number: str | None = None
    carrier_name: str | None = None
    naic_number: str | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    coverage_form: str | None = None  # "claims-made" or "occurrence"
    is_additional_insured: bool = False
    is_subrogation_waived: bool = False
    aggregate_limit_applies_per: str | None = None  # "policy", "project", "location"
    limits: dict[str, float | None] = Field(default_factory=dict)  # Flexible limit storage
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("limits", mode="before")
    @classmethod
    def parse_limits(cls, v: Any) -> dict[str, float | None]:
        """Parse limits dict, handling percentage strings like '2%'."""
        if not isinstance(v, dict):
            return {}
        return parse_flexible_numeric_dict(v)


class COIExtraction(NullSafeModel):
    """Extracted Certificate of Insurance information."""

    # Certificate Identity
    certificate_number: str | None = None
    revision_number: str | None = None
    issue_date: date | None = None

    # Producer/Broker Information
    producer_name: str | None = None
    producer_address: str | None = None
    producer_phone: str | None = None
    producer_email: str | None = None
    producer_reference: str | None = None  # Internal reference number

    # Insured
    insured_name: str | None = None
    insured_address: str | None = None

    # Certificate Holder
    holder_name: str | None = None
    holder_address: str | None = None

    # Insurers (A, B, C, D, E, F)
    insurers: dict[str, dict] = Field(default_factory=dict)  # {"A": {"name": "...", "naic": "..."}}

    @field_validator("insurers", mode="before")
    @classmethod
    def filter_null_insurers(cls, v: Any) -> dict[str, dict]:
        """Filter out null values from insurers dict.

        LLM often returns null for unused insurer slots (B-F).
        """
        if not isinstance(v, dict):
            return {}
        return {k: val for k, val in v.items() if val is not None and isinstance(val, dict)}

    # Policy References (detailed)
    policies: list[COIPolicyReference] = Field(default_factory=list)

    # General Liability Limits
    gl_each_occurrence: float | None = None
    gl_damage_to_rented: float | None = None
    gl_medical_expense: float | None = None
    gl_personal_advertising: float | None = None
    gl_general_aggregate: float | None = None
    gl_products_completed: float | None = None
    gl_coverage_form: str | None = None  # "claims-made" or "occurrence"
    gl_aggregate_limit_applies_per: str | None = None  # "policy", "project", "location"

    # Auto Liability Limits
    auto_combined_single: float | None = None
    auto_bodily_injury_per_person: float | None = None
    auto_bodily_injury_per_accident: float | None = None
    auto_property_damage: float | None = None
    auto_types: list[str] = Field(default_factory=list)  # ["any auto", "owned", "hired", "non-owned"]

    # Umbrella/Excess Liability
    umbrella_limit: float | None = None
    umbrella_aggregate: float | None = None
    umbrella_deductible: float | None = None
    umbrella_retention: float | None = None
    umbrella_coverage_form: str | None = None  # "claims-made" or "occurrence"

    # Workers Compensation
    workers_comp_per_statute: bool | None = None
    workers_comp_other: bool | None = None
    workers_comp_each_accident: float | None = None
    workers_comp_disease_ea_employee: float | None = None
    workers_comp_disease_policy_limit: float | None = None
    workers_comp_excluded_partners: bool | None = None

    # Property Coverage
    property_limit: float | None = None

    # Description of Operations
    description_of_operations: str | None = None

    # Additional Insureds & Waivers
    additional_insureds: list[str] = Field(default_factory=list)
    subrogation_waiver_applies: bool = False

    # Cancellation Terms
    cancellation_notice_days: int | None = None
    cancellation_terms: str | None = None

    # Authorized Representative
    authorized_representative: str | None = None

    # Lender-Specific (for Evidence of Property)
    loan_number: str | None = None
    mortgagee_clause: str | None = None
    loss_payee_clause: str | None = None

    # Extraction metadata
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Invoice Extraction
# ---------------------------------------------------------------------------


class InvoiceLineItem(BaseModel):
    """Line item from an invoice."""

    description: str
    amount: float
    policy_number: str | None = None


class InvoiceExtraction(BaseModel):
    """Extracted invoice information."""

    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None

    # Vendor
    vendor_name: str | None = None
    vendor_address: str | None = None

    # Amounts
    subtotal: float | None = None
    taxes: float | None = None
    fees: float | None = None
    total_amount: float | None = None

    # Line Items
    line_items: list[InvoiceLineItem] = Field(default_factory=list)

    # References
    policy_numbers: list[str] = Field(default_factory=list)

    # Extraction metadata
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Statement of Values Extraction
# ---------------------------------------------------------------------------


class SOVPropertyExtraction(BaseModel):
    """Property from Statement of Values."""

    property_name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None

    # Values
    building_value: float | None = None
    contents_value: float | None = None
    business_income_value: float | None = None
    total_insured_value: float | None = None

    # Building Details
    construction_type: str | None = None
    year_built: int | None = None
    square_footage: int | None = None
    stories: int | None = None
    occupancy: str | None = None


class SOVExtraction(BaseModel):
    """Extracted Statement of Values information."""

    as_of_date: date | None = None
    total_insured_value: float | None = None

    properties: list[SOVPropertyExtraction] = Field(default_factory=list)

    # Extraction metadata
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Proposal/Quote Extraction
# ---------------------------------------------------------------------------


class ProposalCoverageQuote(BaseModel):
    """A coverage quote within a proposal."""

    coverage_type: str  # "property", "general_liability", "umbrella", etc.
    carrier_name: str | None = None
    limit_amount: float | None = None
    deductible_amount: float | None = None
    expiring_premium: float | None = None
    renewal_premium: float | None = None
    premium_change: float | None = None  # Absolute change
    premium_change_pct: float | None = None  # Percentage change


class ProposalPropertyQuote(BaseModel):
    """Quote for a specific property in a proposal."""

    property_name: str | None = None
    property_address: str | None = None
    unit_count: int | None = None
    total_insured_value: float | None = None
    expiring_tiv: float | None = None
    renewal_tiv: float | None = None

    # Coverages for this property
    coverages: list[ProposalCoverageQuote] = Field(default_factory=list)

    # Premium summary for this property
    expiring_total_premium: float | None = None
    renewal_total_premium: float | None = None
    price_per_door_expiring: float | None = None
    price_per_door_renewal: float | None = None


class ProposalExtraction(DateRangeMixin, InsuredInfoMixin, ConfidenceMixin):
    """Extracted insurance proposal/quote comparison.

    Inherits from:
    - DateRangeMixin: Provides effective_date/expiration_date with validation
    - InsuredInfoMixin: Provides named_insured/insured_address
    - ConfidenceMixin: Provides confidence score field
    """

    # Proposal Identity
    proposal_title: str | None = None
    proposal_type: str | None = None  # "renewal", "new business", "remarket"

    # Properties/Locations
    properties: list[ProposalPropertyQuote] = Field(default_factory=list)

    # Portfolio-level summary
    portfolio_expiring_premium: float | None = None
    portfolio_renewal_premium: float | None = None
    portfolio_premium_change: float | None = None
    portfolio_premium_change_pct: float | None = None

    # Carriers involved
    carriers: list[str] = Field(default_factory=list)
    # Note: confidence is inherited from ConfidenceMixin


# ---------------------------------------------------------------------------
# Program Extraction (Multi-Carrier Insurance Program)
# ---------------------------------------------------------------------------


class CarrierInfo(NullSafeModel):
    """Information about a carrier in the program."""

    carrier_name: str
    carrier_code: str | None = None  # Short code like "NFM", "QBE", "Lloyds"
    policy_number: str | None = None
    naic_number: str | None = None
    address: str | None = None
    am_best_rating: str | None = None
    admitted: bool | None = None  # Admitted vs surplus lines

    @field_validator("policy_number", mode="before")
    @classmethod
    def clean_policy_number(cls, v: Any) -> str | None:
        """Clean and validate policy number format."""
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None


class LloydsSyndicate(BaseModel):
    """Lloyd's syndicate information."""

    syndicate_number: str
    syndicate_abbreviation: str | None = None
    participation_percentage: float | None = None


class ContractAllocationLayer(BaseModel):
    """A layer in the contract allocation table."""

    layer_description: str  # e.g., "$24,808,864 excess of $15,000"
    attachment_point: float | None = None  # e.g., 15000
    layer_limit: float | None = None  # e.g., 24808864
    perils_covered: list[str] = Field(default_factory=list)  # e.g., ["AR EXCL NW", "NW,Q"]
    peril_codes: list[str] = Field(default_factory=list)  # e.g., ["NW", "Q", "AR"]
    carrier_code: str | None = None
    carrier_name: str | None = None
    policy_number: str | None = None
    participation_amount: float | None = None
    participation_percentage: float | None = None
    rate_per_hundred: float | None = None


class ContractAllocation(BaseModel):
    """Contract allocation table for multi-carrier programs."""

    account_number: str | None = None
    layers: list[ContractAllocationLayer] = Field(default_factory=list)

    # Peril symbol definitions
    peril_symbols: dict[str, str] = Field(default_factory=dict)  # e.g., {"NW": "Named Windstorm"}

    # Maximum risk definition
    max_risk_basis: str | None = None  # e.g., "Any One Occurrence"
    max_limit: float | None = None


class SublimitEntry(NullSafeModel):
    """A sublimit from the supplemental declarations."""

    sublimit_name: str
    limit_amount: float | None = None
    limit_type: str | None = None  # "per_occurrence", "annual_aggregate", "per_location"
    duration_days: int | None = None  # For time-based sublimits like Civil Authority
    duration_type: str | None = None  # "days", "months"
    is_included: bool = False  # True if "INCLUDED" rather than a specific amount
    is_not_covered: bool = False  # True if "NOT COVERED"
    percentage_of: str | None = None  # e.g., "TIV", "building_value"
    percentage_value: float | None = None
    minimum_amount: float | None = None
    maximum_amount: float | None = None
    applies_to: str | None = None  # What the sublimit applies to
    conditions: list[str] = Field(default_factory=list)


class SublimitsSchedule(NullSafeModel):
    """Complete sublimits schedule from supplemental declarations."""

    # Maximum policy limit
    maximum_limit_of_liability: float | None = None
    limit_basis: str | None = None  # e.g., "per_occurrence", "blanket"

    # Named peril sublimits (Priority 1)
    earth_movement_aggregate: float | None = None
    earth_movement_california_aggregate: float | None = None
    earth_movement_pacific_nw_aggregate: float | None = None
    earth_movement_new_madrid_aggregate: float | None = None
    flood_aggregate: float | None = None
    flood_sfha_aggregate: float | None = None  # Special Flood Hazard Areas
    named_storm_limit: float | None = None
    named_storm_is_included: bool = False

    # Common sublimits (typed fields for frequent ones)
    accounts_receivable: float | None = None
    civil_authority_days: int | None = None
    civil_authority_limit: float | None = None
    contingent_time_element_days: int | None = None
    contingent_time_element_limit: float | None = None
    debris_removal_percentage: float | None = None
    debris_removal_limit: float | None = None
    electronic_data_media: float | None = None
    errors_omissions: float | None = None
    extended_period_of_indemnity_days: int | None = None
    extra_expense: float | None = None
    fine_arts: float | None = None
    fire_brigade_charges: float | None = None
    fungus_mold_aggregate: float | None = None
    ingress_egress_days: int | None = None
    ingress_egress_limit: float | None = None
    leasehold_interest: float | None = None
    pollution_aggregate: float | None = None
    newly_acquired_property_days: int | None = None
    newly_acquired_property_limit: float | None = None
    ordinance_law_coverage_a: str | None = None  # Often "Included in Building Limit"
    ordinance_law_coverage_b: float | None = None
    ordinance_law_coverage_b_percentage: float | None = None
    ordinance_law_coverage_c: str | None = None
    ordinance_law_coverage_d: str | None = None
    ordinance_law_coverage_e: str | None = None
    ordinary_payroll_days: int | None = None
    service_interruption_limit: float | None = None
    service_interruption_waiting_hours: int | None = None
    spoilage: float | None = None
    transit: float | None = None
    valuable_papers_records: float | None = None

    # Flexible storage for additional sublimits
    additional_sublimits: list[SublimitEntry] = Field(default_factory=list)


class DeductibleEntry(BaseModel):
    """A deductible from the deductible schedule."""

    deductible_name: str
    deductible_type: str | None = None  # "flat", "percentage", "waiting_period"
    flat_amount: float | None = None
    percentage_of_tiv: float | None = None
    percentage_basis: str | None = None  # "per_location", "per_building"
    minimum_amount: float | None = None
    maximum_amount: float | None = None
    waiting_period_hours: int | None = None
    applies_to_perils: list[str] = Field(default_factory=list)
    applies_to_locations: str | None = None  # e.g., "All Locations", "California only"
    conditions: list[str] = Field(default_factory=list)


class DeductibleSchedule(BaseModel):
    """Complete deductible schedule."""

    # Base deductible
    base_property_deductible: float | None = None
    base_time_element_deductible: float | None = None
    base_combined_deductible: float | None = None

    # Catastrophe deductibles (Priority 1 - Critical for claims)
    earth_movement_percentage: float | None = None
    earth_movement_minimum: float | None = None
    earth_movement_california_percentage: float | None = None
    earth_movement_california_minimum: float | None = None

    windstorm_hail_percentage: float | None = None
    windstorm_hail_minimum: float | None = None

    named_storm_percentage: float | None = None
    named_storm_minimum: float | None = None  # CRITICAL - often $1M+

    hurricane_percentage: float | None = None
    hurricane_minimum: float | None = None

    flood_deductible: float | None = None
    flood_sfha_deductible: float | None = None

    # Equipment breakdown
    equipment_breakdown_deductible: float | None = None

    # Cyber
    cyber_deductible: float | None = None

    # Terrorism
    terrorism_deductible: float | None = None

    # Rules for applying deductibles
    deductible_application_rules: list[str] = Field(default_factory=list)

    # Additional/specific deductibles
    additional_deductibles: list[DeductibleEntry] = Field(default_factory=list)


class CyberCoverage(BaseModel):
    """Cyber suite coverage details."""

    # Aggregate limits
    cyber_aggregate_limit: float | None = None
    cyber_deductible: float | None = None

    # Identity recovery
    identity_recovery_limit: float | None = None

    # Data compromise response
    forensic_it_review_limit: float | None = None
    legal_review_limit: float | None = None
    notification_limit: float | None = None
    public_relations_limit: float | None = None
    regulatory_fines_limit: float | None = None
    pci_fines_limit: float | None = None
    first_party_malware_limit: float | None = None

    # Computer attack
    loss_of_business_limit: float | None = None
    data_restoration_limit: float | None = None
    system_restoration_limit: float | None = None
    cyber_extortion_limit: float | None = None

    # Liability
    data_compromise_liability_limit: float | None = None
    network_security_liability_limit: float | None = None
    electronic_media_liability_limit: float | None = None

    # Identity recovery sublimits
    lost_wages_limit: float | None = None
    mental_health_counseling_limit: float | None = None
    miscellaneous_costs_limit: float | None = None


class EquipmentBreakdownCoverage(NullSafeModel):
    """Equipment breakdown coverage details."""

    equipment_breakdown_limit: str | None = None  # Often "Per SOV"
    equipment_breakdown_deductible: float | None = None
    time_element_coverage: str | None = None
    extra_expense_limit: float | None = None
    data_restoration_limit: float | None = None
    expediting_expenses_limit: float | None = None
    green_upgrades_limit: float | None = None
    hazardous_substances_limit: float | None = None
    off_premises_limit: float | None = None
    service_interruption_included: bool = False
    spoilage_limit: float | None = None
    spoilage_coinsurance: float | None = None
    public_relations_included: bool = False


class TerrorismCoverage(NullSafeModel):
    """Terrorism coverage details."""

    terrorism_form: str | None = None  # e.g., "AR TERR 07 20"
    terrorism_limit: float | None = None
    terrorism_limit_basis: str | None = None  # "per_occurrence", "as_per_schedule"
    terrorism_deductible: float | None = None
    certified_terrorism_covered: bool | None = None  # TRIA coverage
    non_certified_terrorism_covered: bool | None = None
    tria_exclusion_form: str | None = None


class SinkholeCoverage(NullSafeModel):
    """Sinkhole coverage details (state-specific)."""

    sinkhole_covered: bool = False
    catastrophic_ground_cover_collapse_covered: bool = False
    florida_specific: bool = False
    valuation_type: str | None = None  # "ACV" until stabilization in FL
    neutral_evaluation_available: bool = False
    stabilization_requirements: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)


class CATCoveredProperty(BaseModel):
    """CAT Covered Property endorsement details."""

    cat_property_limit: float | None = None  # Often $100,000 max
    cat_property_deductible_percentage: float | None = None
    cat_property_minimum_deductible: float | None = None

    # Property exclusions (not covered for CAT perils)
    excluded_property_types: list[str] = Field(default_factory=list)

    # Property that requires scheduling
    requires_scheduling: list[str] = Field(default_factory=list)

    # Covered if scheduled
    covered_if_scheduled: list[str] = Field(default_factory=list)


class ValuationBasis(BaseModel):
    """Valuation basis for different property types."""

    property_type: str | None = None  # e.g., "Real & Personal Property", "Roof Coverings"
    valuation_type: str | None = None  # "RCV", "ACV", "Agreed Value"
    conditions: list[str] = Field(default_factory=list)  # e.g., "pre-2011 roofs"


class PolicyRestriction(BaseModel):
    """Policy restriction or warranty."""

    restriction_type: str | None = None  # "exclusion", "warranty", "condition"
    description: str | None = None
    applies_to: str | None = None  # What it applies to
    source_endorsement: str | None = None


class ServiceOfSuit(BaseModel):
    """Service of suit clause for a carrier."""

    carrier_name: str
    service_address: str | None = None
    contact_name: str | None = None
    lma_form: str | None = None  # e.g., "LMA5020"


class FormsEndorsementsSchedule(BaseModel):
    """Schedule of forms and endorsements."""

    form_number: str
    form_title: str | None = None
    form_description: str | None = None


class ProgramExtraction(DateRangeMixin, InsuredInfoMixin, ConfidenceMixin):
    """Extracted multi-carrier insurance program information.

    Inherits from:
    - DateRangeMixin: Provides effective_date/expiration_date with validation
    - InsuredInfoMixin: Provides named_insured/insured_address
    - ConfidenceMixin: Provides confidence score field
    """

    # Program Identity
    account_number: str | None = None
    program_name: str | None = None

    # Additional named insureds (beyond the mixin)
    additional_named_insureds: list[str] = Field(default_factory=list)

    # Producer/Broker
    producer_name: str | None = None
    producer_address: str | None = None

    # Program Manager/Correspondent
    program_manager: str | None = None
    program_manager_address: str | None = None
    correspondent: str | None = None

    # Premium Summary
    total_premium: float | None = None
    premium_by_state: dict[str, float] = Field(default_factory=dict)
    taxes: float | None = None
    fees: float | None = None
    surplus_lines_tax: float | None = None
    inspection_fee: float | None = None
    program_fee: float | None = None
    total_cost: float | None = None
    minimum_earned_premium: float | None = None

    # Carriers (all carriers in the program)
    carriers: list[CarrierInfo] = Field(default_factory=list)

    # Lloyd's syndicates (if applicable)
    lloyds_syndicates: list[LloydsSyndicate] = Field(default_factory=list)

    # Contract Allocation
    contract_allocation: ContractAllocation | None = None

    # Premium by Carrier
    carrier_premiums: dict[str, dict[str, float]] = Field(
        default_factory=dict
    )  # {"AMR-81904": {"property": 10543, "tria": 0}}

    # Sublimits Schedule
    sublimits: SublimitsSchedule | None = None

    # Deductible Schedule
    deductibles: DeductibleSchedule | None = None

    # Specialty Coverages
    cyber_coverage: CyberCoverage | None = None
    equipment_breakdown: EquipmentBreakdownCoverage | None = None
    terrorism_coverage: TerrorismCoverage | None = None
    sinkhole_coverage: SinkholeCoverage | None = None

    # CAT Property Endorsement
    cat_covered_property: CATCoveredProperty | None = None

    # Valuation
    valuation_bases: list[ValuationBasis] = Field(default_factory=list)

    # Policy Restrictions and Warranties
    restrictions: list[PolicyRestriction] = Field(default_factory=list)

    # Policy Exclusions (major exclusions)
    major_exclusions: list[str] = Field(default_factory=list)  # e.g., "Flood", "Named Storm in existence"

    # Coverage Territory
    coverage_territory: str | None = None

    # Service of Suit
    service_of_suit: list[ServiceOfSuit] = Field(default_factory=list)

    # Forms and Endorsements Schedule
    forms_schedule: list[FormsEndorsementsSchedule] = Field(default_factory=list)

    # State-specific notices
    state_notices: dict[str, str] = Field(default_factory=dict)  # {"SC": "Hurricane deductible notice"}

    # Individual policy/coverage details (from the existing schema)
    coverages: list[CoverageExtraction] = Field(default_factory=list)

    # Extraction metadata
    source_pages: list[int] = Field(default_factory=list)
    # Note: confidence is inherited from ConfidenceMixin


# ---------------------------------------------------------------------------
# Loss Run Extraction
# ---------------------------------------------------------------------------


class ClaimStatus(str, Enum):
    """Status of an insurance claim."""

    OPEN = "open"
    CLOSED = "closed"
    REOPENED = "reopened"
    PENDING = "pending"
    DENIED = "denied"
    SUBROGATION = "subrogation"
    LITIGATION = "litigation"
    UNKNOWN = "unknown"


class ClaimType(str, Enum):
    """Type of insurance claim."""

    PROPERTY_DAMAGE = "property_damage"
    BODILY_INJURY = "bodily_injury"
    LIABILITY = "liability"
    WATER_DAMAGE = "water_damage"
    FIRE = "fire"
    WIND_HAIL = "wind_hail"
    THEFT = "theft"
    VANDALISM = "vandalism"
    SLIP_FALL = "slip_fall"
    AUTO = "auto"
    WORKERS_COMP = "workers_comp"
    EQUIPMENT_BREAKDOWN = "equipment_breakdown"
    OTHER = "other"
    UNKNOWN = "unknown"


class ClaimEntry(BaseModel):
    """Individual claim from a loss run report."""

    # Claim Identity
    claim_number: str | None = None
    policy_number: str | None = None
    carrier_name: str | None = None

    # Dates
    date_of_loss: date | None = None
    date_reported: date | None = None
    date_closed: date | None = None

    # Claim Details
    claim_type: ClaimType | None = None
    claim_status: ClaimStatus | None = None
    claimant_name: str | None = None
    description: str | None = None
    cause_of_loss: str | None = None

    # Location
    location_address: str | None = None
    location_name: str | None = None

    # Financials - Paid
    paid_loss: float | None = None  # Total paid for loss/damages
    paid_expense: float | None = None  # Paid allocated loss adjustment expense (ALAE)
    paid_medical: float | None = None  # For workers comp / bodily injury
    paid_indemnity: float | None = None  # For workers comp
    total_paid: float | None = None  # Total paid (loss + expense)

    # Financials - Reserves
    reserve_loss: float | None = None  # Outstanding reserve for loss
    reserve_expense: float | None = None  # Outstanding reserve for expense
    reserve_medical: float | None = None
    reserve_indemnity: float | None = None
    total_reserve: float | None = None

    # Financials - Incurred (Paid + Reserve)
    incurred_loss: float | None = None
    incurred_expense: float | None = None
    total_incurred: float | None = None  # Total incurred = paid + reserve

    # Recovery
    subrogation_amount: float | None = None
    deductible_recovered: float | None = None
    salvage_amount: float | None = None
    net_incurred: float | None = None  # Incurred minus recoveries

    # Additional Info
    litigation_status: str | None = None
    injury_description: str | None = None
    notes: str | None = None


class LossRunSummary(BaseModel):
    """Summary statistics for loss run."""

    # Claim Counts
    total_claims: int = 0
    open_claims: int = 0
    closed_claims: int = 0

    # Claims by Type
    claims_by_type: dict[str, int] = Field(default_factory=dict)
    claims_by_year: dict[str, int] = Field(default_factory=dict)

    # Financial Summary
    total_paid: float = 0.0
    total_reserved: float = 0.0
    total_incurred: float = 0.0
    total_recovered: float = 0.0
    net_incurred: float = 0.0

    # Largest Claims
    largest_claim_amount: float | None = None
    largest_claim_number: str | None = None

    # Loss Ratios (if premium available)
    premium_for_period: float | None = None
    loss_ratio: float | None = None  # Incurred / Premium


class LossRunExtraction(InsuredInfoMixin, PolicyIdentityMixin, ConfidenceMixin):
    """Extracted loss run / claims history information.

    Inherits from:
    - InsuredInfoMixin: Provides named_insured/insured_address
    - PolicyIdentityMixin: Provides policy_number/carrier_name with cleaning
    - ConfidenceMixin: Provides confidence score field
    """

    # Report Identity
    report_title: str | None = None
    report_date: date | None = None  # As-of date for the report
    report_run_date: date | None = None  # When the report was generated

    # Additional policy/carrier info beyond mixins
    policy_numbers: list[str] = Field(default_factory=list)  # Multiple policies
    carriers: list[str] = Field(default_factory=list)  # Multiple carriers

    # Report Period
    experience_period_start: date | None = None
    experience_period_end: date | None = None
    valuation_date: date | None = None

    # Line of Business
    line_of_business: PolicyType | None = None
    lines_of_business: list[PolicyType] = Field(default_factory=list)

    # Claims
    claims: list[ClaimEntry] = Field(default_factory=list)

    # Summary
    summary: LossRunSummary | None = None

    # Large Loss Threshold (if specified)
    large_loss_threshold: float | None = None

    # Notes
    report_notes: list[str] = Field(default_factory=list)

    # Extraction metadata
    source_pages: list[int] = Field(default_factory=list)
    # Note: confidence is inherited from ConfidenceMixin


# ---------------------------------------------------------------------------
# Unified Extraction Result
# ---------------------------------------------------------------------------


class ExtractionResult(BaseModel):
    """Unified extraction result containing all extracted data."""

    classification: DocumentClassification
    policy: PolicyExtraction | None = None
    program: ProgramExtraction | None = None  # Multi-carrier insurance program
    coi: COIExtraction | None = None
    invoice: InvoiceExtraction | None = None
    sov: SOVExtraction | None = None
    proposal: ProposalExtraction | None = None
    loss_run: LossRunExtraction | None = None  # Loss run / claims history

    # Raw text from OCR
    raw_text: str | None = None

    # Overall confidence
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# API Schemas
# ---------------------------------------------------------------------------


class DocumentCreate(BaseModel):
    """Schema for creating a document record."""

    file_name: str
    file_path: str  # Local file path
    organization_id: str
    property_id: str | None = None


class DocumentResponse(BaseModel):
    """Schema for document API response."""

    id: str
    file_name: str
    file_url: str
    document_type: str | None
    document_subtype: str | None
    carrier: str | None
    policy_number: str | None
    effective_date: date | None
    expiration_date: date | None
    upload_status: str
    ocr_status: str
    extraction_status: str
    extraction_confidence: float | None
    needs_human_review: bool
    property_id: str | None = None
    property_name: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IngestRequest(BaseModel):
    """Request to ingest a document."""

    file_path: str
    organization_id: str
    property_name: str
    property_id: str | None = None


class IngestResponse(BaseModel):
    """Response from document ingestion."""

    document_id: str
    file_name: str
    status: str
    classification: DocumentClassification | None = None
    extraction_summary: dict | None = None
    errors: list[str] = Field(default_factory=list)


class IngestDirectoryRequest(BaseModel):
    """Request to ingest all documents in a directory."""

    directory_path: str
    organization_id: str
    property_name: str | None = None  # Defaults to directory name if not provided
    property_id: str | None = None
    program_id: str | None = None
    force_reprocess: bool = True  # If True, reprocess existing docs. If False, skip them.


class IngestDirectoryResponse(BaseModel):
    """Response from directory ingestion."""

    directory_path: str
    total_files: int
    successful: int
    failed: int
    skipped: int = 0  # Documents that already existed and were skipped
    results: list[IngestResponse]
