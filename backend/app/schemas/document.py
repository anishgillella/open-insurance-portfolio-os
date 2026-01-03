"""Pydantic schemas for document ingestion and extraction."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


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
# Program Extraction (Multi-Carrier Insurance Program)
# ---------------------------------------------------------------------------


class CarrierInfo(BaseModel):
    """Information about a carrier in the program."""

    carrier_name: str
    carrier_code: str | None = None  # Short code like "NFM", "QBE", "Lloyds"
    policy_number: str | None = None
    naic_number: str | None = None
    address: str | None = None
    am_best_rating: str | None = None
    admitted: bool | None = None  # Admitted vs surplus lines


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


class SublimitEntry(BaseModel):
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


class SublimitsSchedule(BaseModel):
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


class EquipmentBreakdownCoverage(BaseModel):
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


class TerrorismCoverage(BaseModel):
    """Terrorism coverage details."""

    terrorism_form: str | None = None  # e.g., "AR TERR 07 20"
    terrorism_limit: float | None = None
    terrorism_limit_basis: str | None = None  # "per_occurrence", "as_per_schedule"
    terrorism_deductible: float | None = None
    certified_terrorism_covered: bool | None = None  # TRIA coverage
    non_certified_terrorism_covered: bool | None = None
    tria_exclusion_form: str | None = None


class SinkholeCoverage(BaseModel):
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

    property_type: str  # e.g., "Real & Personal Property", "Roof Coverings"
    valuation_type: str  # "RCV", "ACV", "Agreed Value"
    conditions: list[str] = Field(default_factory=list)  # e.g., "pre-2011 roofs"


class PolicyRestriction(BaseModel):
    """Policy restriction or warranty."""

    restriction_type: str  # "exclusion", "warranty", "condition"
    description: str
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


class ProgramExtraction(BaseModel):
    """Extracted multi-carrier insurance program information."""

    # Program Identity
    account_number: str | None = None
    program_name: str | None = None

    # Named Insured
    named_insured: str | None = None
    insured_address: str | None = None
    additional_named_insureds: list[str] = Field(default_factory=list)

    # Term
    effective_date: date | None = None
    expiration_date: date | None = None

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
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


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
