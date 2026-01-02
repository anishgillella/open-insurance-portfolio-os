"""Pydantic schemas for document ingestion and extraction."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Types of insurance documents."""

    POLICY = "policy"
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
    deductible_percentage: float | None = None
    coinsurance_percentage: float | None = None
    waiting_period_hours: int | None = None
    valuation_type: str | None = None  # e.g., "RCV", "ACV"
    exclusions: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    source_page: int | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Policy Extraction
# ---------------------------------------------------------------------------


class PolicyExtraction(BaseModel):
    """Extracted policy information."""

    # Policy Identity
    policy_type: PolicyType
    policy_number: str | None = None
    carrier_name: str | None = None

    # Dates
    effective_date: date | None = None
    expiration_date: date | None = None

    # Named Insured
    named_insured: str | None = None
    insured_address: str | None = None

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
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Certificate of Insurance Extraction
# ---------------------------------------------------------------------------


class COIPolicyReference(BaseModel):
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


class COIExtraction(BaseModel):
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


class ProposalExtraction(BaseModel):
    """Extracted insurance proposal/quote comparison."""

    # Proposal Identity
    proposal_title: str | None = None
    proposal_type: str | None = None  # "renewal", "new business", "remarket"

    # Named Insured
    named_insured: str | None = None
    insured_address: str | None = None

    # Term
    effective_date: date | None = None
    expiration_date: date | None = None

    # Properties/Locations
    properties: list[ProposalPropertyQuote] = Field(default_factory=list)

    # Portfolio-level summary
    portfolio_expiring_premium: float | None = None
    portfolio_renewal_premium: float | None = None
    portfolio_premium_change: float | None = None
    portfolio_premium_change_pct: float | None = None

    # Carriers involved
    carriers: list[str] = Field(default_factory=list)

    # Extraction metadata
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Unified Extraction Result
# ---------------------------------------------------------------------------


class ExtractionResult(BaseModel):
    """Unified extraction result containing all extracted data."""

    classification: DocumentClassification
    policy: PolicyExtraction | None = None
    coi: COIExtraction | None = None
    invoice: InvoiceExtraction | None = None
    sov: SOVExtraction | None = None
    proposal: ProposalExtraction | None = None

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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IngestRequest(BaseModel):
    """Request to ingest a document."""

    file_path: str
    organization_id: str
    property_id: str | None = None


class IngestResponse(BaseModel):
    """Response from document ingestion."""

    document_id: str
    file_name: str
    status: str
    classification: DocumentClassification | None = None
    extraction_summary: dict | None = None
    errors: list[str] = Field(default_factory=list)
