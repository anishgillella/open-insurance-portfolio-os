"""Document Extraction Service using Gemini via OpenRouter.

This service extracts structured data from insurance documents based on their
document type. It uses type-specific prompts and Pydantic schemas for validation.

Features:
- JSON mode enforcement via OpenRouter response_format parameter
- Validation retry with error context for failed extractions
- Chunked extraction for large documents with parallel processing
- Intelligent merge strategies for combining chunk extractions

For large documents, it uses chunked extraction:
1. Split document into chunks (~50K chars each)
2. Extract from each chunk in parallel
3. Merge extractions, deduplicating and taking highest confidence values
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.schemas.document import (
    CarrierInfo,
    CATCoveredProperty,
    ClaimEntry,
    ClaimStatus,
    ClaimType,
    COIExtraction,
    COIPolicyReference,
    ContractAllocation,
    ContractAllocationLayer,
    CoverageExtraction,
    CyberCoverage,
    DeductibleEntry,
    DeductibleSchedule,
    DocumentClassification,
    DocumentType,
    EquipmentBreakdownCoverage,
    ExtractionResult,
    FormsEndorsementsSchedule,
    InvoiceExtraction,
    InvoiceLineItem,
    LloydsSyndicate,
    LossRunExtraction,
    LossRunSummary,
    PolicyExtraction,
    PolicyRestriction,
    PolicyType,
    ProgramExtraction,
    ProposalCoverageQuote,
    ProposalExtraction,
    ProposalPropertyQuote,
    ServiceOfSuit,
    SinkholeCoverage,
    SOVExtraction,
    SOVPropertyExtraction,
    SublimitEntry,
    SublimitsSchedule,
    TerrorismCoverage,
    ValuationBasis,
)

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Base exception for extraction errors."""

    pass


class ExtractionAPIError(ExtractionError):
    """Raised when LLM API returns an error."""

    pass


class ExtractionValidationError(ExtractionError):
    """Raised when extracted data fails schema validation."""

    pass


# ---------------------------------------------------------------------------
# Extraction Configuration
# ---------------------------------------------------------------------------

T = TypeVar("T", bound=BaseModel)


@dataclass
class ExtractionConfig:
    """Configuration for extraction with retry and JSON mode."""

    # JSON Mode
    use_json_mode: bool = True

    # Retry settings
    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_multiplier: float = 2.0

    # Chunking settings
    max_chunk_chars: int = 50000
    chunk_overlap_chars: int = 2000
    max_concurrent_chunks: int = 5

    # Validation settings
    fail_on_validation_error: bool = False


# Default configuration
DEFAULT_CONFIG = ExtractionConfig()


# ---------------------------------------------------------------------------
# Extraction Prompts
# ---------------------------------------------------------------------------

POLICY_EXTRACTION_PROMPT = """You are an expert insurance document analyst. Extract detailed policy information from the following document.

DOCUMENT TEXT:
{document_text}

---

Extract all policy information and return as JSON:

{{
    "policy_type": "<property|general_liability|umbrella|excess|flood|earthquake|terrorism|crime|cyber|epl|dno|auto|workers_comp|boiler_machinery|unknown>",
    "policy_number": "<policy number>",
    "carrier_name": "<insurance company name>",
    "effective_date": "<YYYY-MM-DD>",
    "expiration_date": "<YYYY-MM-DD>",
    "named_insured": "<full named insured text>",
    "insured_address": "<insured address>",
    "premium": <number or null>,
    "taxes": <number or null>,
    "fees": <number or null>,
    "total_cost": <number or null>,
    "admitted": <true|false|null>,
    "form_type": "<special|basic|broad|null>",
    "policy_form": "<policy form number like CP 00 10>",
    "coverages": [
        {{
            "coverage_name": "<name>",
            "coverage_category": "<property|liability|auto|workers_comp|other>",
            "limit_amount": <number or null>,
            "limit_type": "<per occurrence|aggregate|combined single|null>",
            "sublimit": <number or null>,
            "sublimit_applies_to": "<what sublimit applies to>",
            "deductible_amount": <number or null>,
            "deductible_type": "<per occurrence|per claim|percentage|null>",
            "deductible_pct": <number 0-100 or null>,
            "deductible_minimum": <number or null>,
            "deductible_maximum": <number or null>,
            "coinsurance_pct": <number 0-100 or null>,
            "waiting_period_hours": <number or null>,
            "valuation_type": "<RCV|ACV|agreed value|null>",
            "margin_clause_pct": <number 0-100 or null>,
            "exclusions": ["list of exclusions"],
            "conditions": ["list of special conditions"],
            "source_page": <page number or null>,
            "confidence": <0.0-1.0>
        }}
    ],
    "mortgagee_name": "<mortgagee/loss payee name>",
    "mortgagee_clause": "<full mortgagee clause text>",
    "loss_payee": "<loss payee name>",
    "additional_insureds": ["list of additional insureds"],
    "exclusions": ["key policy exclusions"],
    "special_conditions": ["special conditions or endorsements"],
    "source_pages": [<page numbers where key info found>],
    "confidence": <overall confidence 0.0-1.0>
}}

Return ONLY the JSON object. Extract as much detail as possible. Use null for missing fields."""


COI_EXTRACTION_PROMPT = """You are an expert insurance document analyst. Extract ALL information from this ACORD Certificate of Insurance (COI).

DOCUMENT TEXT:
{document_text}

---

Extract EVERY field visible on the certificate. Return as JSON:

{{
    "certificate_number": "<certificate number>",
    "revision_number": "<revision number if shown>",
    "issue_date": "<YYYY-MM-DD>",

    "producer_name": "<producer/broker company name>",
    "producer_address": "<full producer address>",
    "producer_phone": "<phone number>",
    "producer_email": "<email address>",
    "producer_reference": "<internal reference number like CN...>",

    "insured_name": "<named insured>",
    "insured_address": "<insured full address>",

    "holder_name": "<certificate holder name>",
    "holder_address": "<certificate holder address>",

    "insurers": {{
        "A": {{"name": "<insurer A name>", "naic": "<NAIC number>"}},
        "B": {{"name": "<insurer B name>", "naic": "<NAIC number>"}},
        "C": {{"name": "<insurer C name>", "naic": "<NAIC number>"}},
        "D": {{"name": "<insurer D name>", "naic": "<NAIC number>"}},
        "E": {{"name": "<insurer E name>", "naic": "<NAIC number>"}},
        "F": {{"name": "<insurer F name>", "naic": "<NAIC number>"}}
    }},

    "policies": [
        {{
            "insurer_letter": "<A, B, C, etc>",
            "policy_type": "<general_liability|auto|umbrella|workers_comp|property|other>",
            "policy_number": "<policy number>",
            "carrier_name": "<carrier name>",
            "naic_number": "<NAIC number>",
            "effective_date": "<YYYY-MM-DD>",
            "expiration_date": "<YYYY-MM-DD>",
            "coverage_form": "<claims-made|occurrence>",
            "is_additional_insured": <true if ADDL INSD box is checked>,
            "is_subrogation_waived": <true if SUBR WVD box is checked>,
            "aggregate_limit_applies_per": "<policy|project|location>",
            "limits": {{
                "<limit name>": <amount>
            }},
            "confidence": <0.0-1.0>
        }}
    ],

    "gl_each_occurrence": <number or null>,
    "gl_damage_to_rented": <number or null>,
    "gl_medical_expense": <number or null>,
    "gl_personal_advertising": <number or null>,
    "gl_general_aggregate": <number or null>,
    "gl_products_completed": <number or null>,
    "gl_coverage_form": "<claims-made|occurrence>",
    "gl_aggregate_limit_applies_per": "<policy|project|location>",

    "auto_combined_single": <number or null>,
    "auto_bodily_injury_per_person": <number or null>,
    "auto_bodily_injury_per_accident": <number or null>,
    "auto_property_damage": <number or null>,
    "auto_types": ["any auto", "owned", "scheduled", "hired", "non-owned"],

    "umbrella_limit": <number or null>,
    "umbrella_aggregate": <number or null>,
    "umbrella_deductible": <number or null>,
    "umbrella_retention": <number or null>,
    "umbrella_coverage_form": "<claims-made|occurrence>",

    "workers_comp_per_statute": <true|false|null>,
    "workers_comp_other": <true|false|null>,
    "workers_comp_each_accident": <number or null>,
    "workers_comp_disease_ea_employee": <number or null>,
    "workers_comp_disease_policy_limit": <number or null>,
    "workers_comp_excluded_partners": <true if partners/officers excluded>,

    "property_limit": <number or null>,

    "description_of_operations": "<full text from DESCRIPTION OF OPERATIONS section>",

    "additional_insureds": ["<names of additional insureds mentioned>"],
    "subrogation_waiver_applies": <true if subrogation is waived>,

    "cancellation_notice_days": <number of days notice>,
    "cancellation_terms": "<cancellation clause text>",

    "authorized_representative": "<name of authorized rep>",

    "loan_number": "<loan number if present>",
    "mortgagee_clause": "<mortgagee clause text>",
    "loss_payee_clause": "<loss payee clause text>",

    "confidence": <overall confidence 0.0-1.0>
}}

IMPORTANT: Extract ALL visible information. Do not skip any fields that have data on the certificate.
Return ONLY the JSON object. Use null for missing fields."""


INVOICE_EXTRACTION_PROMPT = """You are an expert insurance document analyst. Extract invoice/billing information from the following document.

DOCUMENT TEXT:
{document_text}

---

Extract all invoice information and return as JSON:

{{
    "invoice_number": "<invoice number>",
    "invoice_date": "<YYYY-MM-DD>",
    "due_date": "<YYYY-MM-DD>",
    "vendor_name": "<vendor/agency name>",
    "vendor_address": "<vendor address>",
    "subtotal": <number or null>,
    "taxes": <number or null>,
    "fees": <number or null>,
    "total_amount": <number or null>,
    "line_items": [
        {{
            "description": "<line item description>",
            "amount": <number>,
            "policy_number": "<associated policy number or null>"
        }}
    ],
    "policy_numbers": ["list of referenced policy numbers"],
    "confidence": <overall confidence 0.0-1.0>
}}

Return ONLY the JSON object. Use null for missing fields."""


SOV_EXTRACTION_PROMPT = """You are an expert insurance document analyst. Extract Statement of Values (SOV) / Schedule of Locations information from the following document.

DOCUMENT TEXT:
{document_text}

---

Extract all property values and return as JSON:

{{
    "as_of_date": "<YYYY-MM-DD>",
    "total_insured_value": <total TIV number or null>,
    "properties": [
        {{
            "property_name": "<property name>",
            "address": "<street address>",
            "city": "<city>",
            "state": "<state>",
            "zip_code": "<zip>",
            "building_value": <number or null>,
            "contents_value": <number or null>,
            "business_income_value": <number or null>,
            "total_insured_value": <TIV for this property or null>,
            "construction_type": "<frame|masonry|fire resistive|etc>",
            "year_built": <year number or null>,
            "square_footage": <number or null>,
            "stories": <number or null>,
            "occupancy": "<occupancy type>"
        }}
    ],
    "confidence": <overall confidence 0.0-1.0>
}}

Return ONLY the JSON object. Extract ALL properties listed. Use null for missing fields."""


PROPOSAL_EXTRACTION_PROMPT = """You are an expert insurance document analyst. Extract ALL information from this insurance proposal/quote comparison document.

DOCUMENT TEXT:
{document_text}

---

This is a proposal or quote comparison document. It typically shows "Expiring" vs "Renewal" premium comparisons, multiple properties, and multiple carriers.

Extract ALL information and return as JSON:

{{
    "proposal_title": "<document title>",
    "proposal_type": "<renewal|new_business|remarket>",
    "named_insured": "<insured name>",
    "insured_address": "<insured address if shown>",
    "effective_date": "<YYYY-MM-DD>",
    "expiration_date": "<YYYY-MM-DD>",
    "properties": [
        {{
            "property_name": "<property name, e.g., 'The Bend'>",
            "property_address": "<property address>",
            "unit_count": <number of units or null>,
            "total_insured_value": <current/renewal TIV>,
            "expiring_tiv": <expiring TIV>,
            "renewal_tiv": <renewal TIV>,
            "coverages": [
                {{
                    "coverage_type": "<property|general_liability|umbrella|excess|etc>",
                    "carrier_name": "<carrier name>",
                    "limit_amount": <limit if shown>,
                    "deductible_amount": <deductible if shown>,
                    "expiring_premium": <expiring premium>,
                    "renewal_premium": <renewal premium>,
                    "premium_change": <absolute change>,
                    "premium_change_pct": <percentage change as decimal, e.g., -0.24 for -24%>
                }}
            ],
            "expiring_total_premium": <total expiring premium for this property>,
            "renewal_total_premium": <total renewal premium for this property>,
            "price_per_door_expiring": <price per unit expiring>,
            "price_per_door_renewal": <price per unit renewal>
        }}
    ],
    "portfolio_expiring_premium": <total expiring premium across all properties>,
    "portfolio_renewal_premium": <total renewal premium across all properties>,
    "portfolio_premium_change": <absolute change in total premium>,
    "portfolio_premium_change_pct": <percentage change as decimal>,
    "carriers": ["<list of all carriers mentioned>"],
    "confidence": <overall confidence 0.0-1.0>
}}

IMPORTANT:
- Extract BOTH Expiring and Renewal values when shown
- Identify all carriers mentioned for each coverage type
- Calculate or extract premium changes
- Separate data by property/location when multiple are shown

Return ONLY the JSON object. Use null for missing fields."""


LOSS_RUN_EXTRACTION_PROMPT = """You are an expert insurance document analyst. Extract ALL information from this loss run / claims history document.

DOCUMENT TEXT:
{document_text}

---

This is a loss run or claims history report. It shows historical claims data for an insured, including dates, amounts paid, reserves, and claim status.

Extract ALL information and return as JSON:

{{
    "report_title": "<title of the report>",
    "report_date": "<YYYY-MM-DD - as-of date for the data>",
    "report_run_date": "<YYYY-MM-DD - when report was generated>",

    "named_insured": "<insured name>",
    "insured_address": "<insured address if shown>",

    "policy_number": "<primary policy number>",
    "policy_numbers": ["<all policy numbers listed>"],
    "carrier_name": "<primary carrier>",
    "carriers": ["<all carriers if multiple>"],

    "experience_period_start": "<YYYY-MM-DD - start of experience period>",
    "experience_period_end": "<YYYY-MM-DD - end of experience period>",
    "valuation_date": "<YYYY-MM-DD - valuation date>",

    "line_of_business": "<property|general_liability|auto|workers_comp|etc>",
    "lines_of_business": ["<all lines if multiple>"],

    "claims": [
        {{
            "claim_number": "<claim number>",
            "policy_number": "<policy number for this claim>",
            "carrier_name": "<carrier handling claim>",

            "date_of_loss": "<YYYY-MM-DD>",
            "date_reported": "<YYYY-MM-DD>",
            "date_closed": "<YYYY-MM-DD or null if open>",

            "claim_type": "<property_damage|bodily_injury|liability|water_damage|fire|wind_hail|theft|vandalism|slip_fall|auto|workers_comp|equipment_breakdown|other|unknown>",
            "claim_status": "<open|closed|reopened|pending|denied|subrogation|litigation|unknown>",
            "claimant_name": "<claimant name if shown>",
            "description": "<description of loss>",
            "cause_of_loss": "<cause code or description>",

            "location_address": "<location where loss occurred>",
            "location_name": "<location name if shown>",

            "paid_loss": <amount paid for damages>,
            "paid_expense": <amount paid for expenses/ALAE>,
            "paid_medical": <medical payments if applicable>,
            "paid_indemnity": <indemnity payments if workers comp>,
            "total_paid": <total paid amount>,

            "reserve_loss": <outstanding reserve for loss>,
            "reserve_expense": <outstanding reserve for expense>,
            "reserve_medical": <medical reserve>,
            "reserve_indemnity": <indemnity reserve>,
            "total_reserve": <total outstanding reserve>,

            "incurred_loss": <incurred loss = paid + reserve>,
            "incurred_expense": <incurred expense>,
            "total_incurred": <total incurred>,

            "subrogation_amount": <subrogation recovery>,
            "deductible_recovered": <deductible recovered>,
            "salvage_amount": <salvage if any>,
            "net_incurred": <incurred minus recoveries>,

            "litigation_status": "<litigation status if in suit>",
            "injury_description": "<injury description for BI claims>",
            "notes": "<any notes>"
        }}
    ],

    "summary": {{
        "total_claims": <total number of claims>,
        "open_claims": <number of open claims>,
        "closed_claims": <number of closed claims>,

        "claims_by_type": {{"property_damage": 5, "liability": 3}},
        "claims_by_year": {{"2023": 10, "2024": 5}},

        "total_paid": <total paid across all claims>,
        "total_reserved": <total outstanding reserves>,
        "total_incurred": <total incurred>,
        "total_recovered": <total recoveries>,
        "net_incurred": <net incurred after recoveries>,

        "largest_claim_amount": <largest single claim incurred>,
        "largest_claim_number": "<claim number of largest claim>",

        "premium_for_period": <premium if shown>,
        "loss_ratio": <loss ratio if calculable>
    }},

    "large_loss_threshold": <threshold for large loss reporting if specified>,
    "report_notes": ["<any report notes or caveats>"],
    "confidence": <overall confidence 0.0-1.0>
}}

IMPORTANT:
- Extract EVERY claim listed, not just a sample
- Calculate totals if not explicitly shown
- Preserve claim numbers and dates exactly as shown
- Identify claim types from descriptions if not explicitly categorized
- Note any claims in litigation or subrogation

Return ONLY the JSON object. Use null for missing fields."""


PROGRAM_EXTRACTION_PROMPT = """You are an expert insurance document analyst specializing in multi-carrier commercial property programs. This document is a MULTI-CARRIER INSURANCE PROGRAM with multiple insurers sharing risk through a Contract Allocation structure.

DOCUMENT TEXT:
{document_text}

---

Extract ALL program information comprehensively. This is critical insurance data used for claims processing, carrier notification, and coverage determination.

Return as JSON:

{{
    "account_number": "<account number like 1053867>",
    "program_name": "<program name if shown>",

    "named_insured": "<full named insured>",
    "insured_address": "<complete address>",
    "additional_named_insureds": ["<any additional named insureds>"],

    "effective_date": "<YYYY-MM-DD>",
    "expiration_date": "<YYYY-MM-DD>",

    "producer_name": "<broker/producer name>",
    "producer_address": "<broker address>",

    "program_manager": "<program manager like AmRisc, LLC>",
    "program_manager_address": "<program manager address>",
    "correspondent": "<correspondent if different>",

    "total_premium": <total premium number>,
    "premium_by_state": {{"SC": 104482.00}},
    "taxes": <taxes amount>,
    "fees": <fees amount>,
    "surplus_lines_tax": <surplus lines tax>,
    "inspection_fee": <inspection fee>,
    "program_fee": <program fee>,
    "total_cost": <grand total>,
    "minimum_earned_premium": <minimum earned premium>,

    "carriers": [
        {{
            "carrier_name": "<full carrier name>",
            "carrier_code": "<short code like NFM, QBE, Lloyds>",
            "policy_number": "<policy number>",
            "naic_number": "<NAIC number if shown>",
            "address": "<carrier address>",
            "admitted": <true if admitted, false if surplus lines>
        }}
    ],

    "lloyds_syndicates": [
        {{
            "syndicate_number": "<number like 510>",
            "syndicate_abbreviation": "<abbreviation like KLN>"
        }}
    ],

    "contract_allocation": {{
        "account_number": "<account number>",
        "layers": [
            {{
                "layer_description": "<e.g., $24,808,864 excess of $15,000>",
                "attachment_point": <attachment point number>,
                "layer_limit": <layer limit number>,
                "perils_covered": ["<peril codes like AR EXCL NW>"],
                "peril_codes": ["NW", "Q"],
                "carrier_code": "<carrier code>",
                "carrier_name": "<carrier name>",
                "policy_number": "<policy number>",
                "participation_amount": <dollar amount>,
                "participation_percentage": <percentage as decimal, e.g., 0.33 for 33%>,
                "rate_per_hundred": <rate like 0.065>
            }}
        ],
        "peril_symbols": {{
            "NW": "Named Windstorm",
            "Q": "Earthquake",
            "AR": "All Risk",
            "EBD": "Equipment Breakdown",
            "CYB": "Cyber",
            "T": "Terrorism",
            "F": "Flood",
            "WH": "Windstorm and Hail"
        }},
        "max_risk_basis": "<e.g., Any One Occurrence>",
        "max_limit": <maximum limit number>
    }},

    "carrier_premiums": {{
        "<policy_number>": {{
            "property": <property premium>,
            "tria": <TRIA premium>
        }}
    }},

    "sublimits": {{
        "maximum_limit_of_liability": <max limit>,
        "limit_basis": "<per_occurrence or blanket>",

        "earth_movement_aggregate": <amount or null>,
        "earth_movement_california_aggregate": <amount or null if NOT COVERED>,
        "earth_movement_pacific_nw_aggregate": <amount or null>,
        "earth_movement_new_madrid_aggregate": <amount or null>,
        "flood_aggregate": <amount or null if NOT COVERED>,
        "flood_sfha_aggregate": <amount or null>,
        "named_storm_limit": <amount or null>,
        "named_storm_is_included": <true if INCLUDED>,

        "accounts_receivable": <amount>,
        "civil_authority_days": <number of days>,
        "civil_authority_limit": <limit amount>,
        "contingent_time_element_days": <days>,
        "contingent_time_element_limit": <limit>,
        "debris_removal_percentage": <percentage as decimal>,
        "debris_removal_limit": <limit>,
        "electronic_data_media": <limit>,
        "errors_omissions": <limit>,
        "extended_period_of_indemnity_days": <days>,
        "extra_expense": <limit>,
        "fine_arts": <limit>,
        "fire_brigade_charges": <limit>,
        "fungus_mold_aggregate": <annual aggregate>,
        "ingress_egress_days": <days>,
        "ingress_egress_limit": <limit>,
        "leasehold_interest": <limit>,
        "pollution_aggregate": <limit>,
        "newly_acquired_property_days": <days>,
        "newly_acquired_property_limit": <limit>,
        "ordinance_law_coverage_a": "<text like Included in Building Limit>",
        "ordinance_law_coverage_b": <limit or null>,
        "ordinance_law_coverage_b_percentage": <percentage of building value>,
        "ordinance_law_coverage_c": "<text>",
        "ordinance_law_coverage_d": "<text>",
        "ordinance_law_coverage_e": "<text>",
        "ordinary_payroll_days": <days>,
        "service_interruption_limit": <limit>,
        "service_interruption_waiting_hours": <hours>,
        "spoilage": <limit>,
        "transit": <limit>,
        "valuable_papers_records": <limit>,

        "additional_sublimits": [
            {{
                "sublimit_name": "<name>",
                "limit_amount": <amount or null>,
                "limit_type": "<per_occurrence, annual_aggregate, per_location>",
                "duration_days": <days if time-based>,
                "is_included": <true if INCLUDED>,
                "is_not_covered": <true if NOT COVERED>,
                "percentage_of": "<TIV, building_value>",
                "percentage_value": <percentage as decimal>,
                "minimum_amount": <minimum>,
                "maximum_amount": <maximum>,
                "applies_to": "<what it applies to>",
                "conditions": ["<conditions>"]
            }}
        ]
    }},

    "deductibles": {{
        "base_property_deductible": <amount>,
        "base_time_element_deductible": <amount>,
        "base_combined_deductible": <amount if combined>,

        "earth_movement_percentage": <percentage as decimal, e.g., 0.02 for 2%>,
        "earth_movement_minimum": <minimum amount>,
        "earth_movement_california_percentage": <percentage>,
        "earth_movement_california_minimum": <minimum>,

        "windstorm_hail_percentage": <percentage>,
        "windstorm_hail_minimum": <minimum>,

        "named_storm_percentage": <percentage, e.g., 0.05 for 5%>,
        "named_storm_minimum": <CRITICAL - minimum like 1241193>,

        "hurricane_percentage": <percentage>,
        "hurricane_minimum": <minimum>,

        "flood_deductible": <amount>,
        "flood_sfha_deductible": <amount>,

        "equipment_breakdown_deductible": <amount>,
        "cyber_deductible": <amount>,
        "terrorism_deductible": <amount>,

        "deductible_application_rules": ["<rules for applying deductibles>"],

        "additional_deductibles": [
            {{
                "deductible_name": "<name>",
                "deductible_type": "<flat, percentage, waiting_period>",
                "flat_amount": <amount>,
                "percentage_of_tiv": <percentage>,
                "percentage_basis": "<per_location, per_building>",
                "minimum_amount": <minimum>,
                "applies_to_perils": ["<perils>"],
                "applies_to_locations": "<location description>",
                "conditions": ["<conditions>"]
            }}
        ]
    }},

    "cyber_coverage": {{
        "cyber_aggregate_limit": <annual aggregate>,
        "cyber_deductible": <deductible>,
        "identity_recovery_limit": <limit per person>,
        "forensic_it_review_limit": <limit>,
        "legal_review_limit": <limit>,
        "public_relations_limit": <limit>,
        "regulatory_fines_limit": <limit>,
        "pci_fines_limit": <limit>,
        "first_party_malware_limit": <limit>,
        "loss_of_business_limit": <limit>,
        "data_restoration_limit": <limit>,
        "cyber_extortion_limit": <limit>,
        "data_compromise_liability_limit": <limit>,
        "lost_wages_limit": <limit>,
        "mental_health_counseling_limit": <limit>,
        "miscellaneous_costs_limit": <limit>
    }},

    "equipment_breakdown": {{
        "equipment_breakdown_limit": "<Per SOV or amount>",
        "equipment_breakdown_deductible": <deductible>,
        "time_element_coverage": "<Per SOV or description>",
        "extra_expense_limit": <limit>,
        "data_restoration_limit": <limit>,
        "expediting_expenses_limit": <limit>,
        "green_upgrades_limit": <limit>,
        "hazardous_substances_limit": <limit>,
        "off_premises_limit": <limit>,
        "service_interruption_included": <true/false>,
        "spoilage_limit": <limit>,
        "spoilage_coinsurance": <percentage>,
        "public_relations_included": <true/false>
    }},

    "terrorism_coverage": {{
        "terrorism_form": "<form number like AR TERR 07 20>",
        "terrorism_limit": <limit or null if as per schedule>,
        "terrorism_limit_basis": "<per_occurrence, as_per_schedule>",
        "terrorism_deductible": <deductible>,
        "certified_terrorism_covered": <true/false - TRIA coverage>,
        "non_certified_terrorism_covered": <true/false>,
        "tria_exclusion_form": "<form number if TRIA excluded>"
    }},

    "sinkhole_coverage": {{
        "sinkhole_covered": <true/false>,
        "catastrophic_ground_cover_collapse_covered": <true/false>,
        "florida_specific": <true if Florida-specific rules apply>,
        "valuation_type": "<ACV or RCV>",
        "neutral_evaluation_available": <true/false>,
        "stabilization_requirements": ["<requirements>"],
        "exclusions": ["<exclusions>"]
    }},

    "cat_covered_property": {{
        "cat_property_limit": <max limit like 100000>,
        "cat_property_deductible_percentage": <percentage>,
        "cat_property_minimum_deductible": <minimum>,
        "excluded_property_types": ["<list of excluded property types>"],
        "requires_scheduling": ["<property types requiring scheduling>"],
        "covered_if_scheduled": ["<property covered only if scheduled>"]
    }},

    "valuation_bases": [
        {{
            "property_type": "<Real & Personal Property>",
            "valuation_type": "<RCV, ACV, Agreed Value>",
            "conditions": ["<conditions like pre-2011 roofs>"]
        }}
    ],

    "restrictions": [
        {{
            "restriction_type": "<exclusion, warranty, condition>",
            "description": "<description>",
            "applies_to": "<what it applies to>",
            "source_endorsement": "<endorsement number>"
        }}
    ],

    "major_exclusions": ["<major exclusions like Flood, Named Storm in existence>"],

    "coverage_territory": "<coverage territory>",

    "service_of_suit": [
        {{
            "carrier_name": "<carrier>",
            "service_address": "<address for service of process>",
            "contact_name": "<contact name if shown>",
            "lma_form": "<LMA form number>"
        }}
    ],

    "forms_schedule": [
        {{
            "form_number": "<form number>",
            "form_title": "<form title>",
            "form_description": "<description>"
        }}
    ],

    "state_notices": {{
        "<state code>": "<notice description>"
    }},

    "coverages": [
        {{
            "coverage_name": "<name>",
            "coverage_category": "<property, liability, etc>",
            "limit_amount": <limit>,
            "deductible_amount": <deductible>,
            "valuation_type": "<RCV, ACV>",
            "exclusions": ["<exclusions>"],
            "conditions": ["<conditions>"],
            "source_page": <page number>,
            "confidence": <0.0-1.0>
        }}
    ],

    "source_pages": [<page numbers>],
    "confidence": <overall confidence 0.0-1.0>
}}

CRITICAL EXTRACTION PRIORITIES:
1. CONTRACT ALLOCATION TABLE - Extract ALL layers with carriers, participation %, rates
2. DEDUCTIBLES - Especially Named Storm minimum (often $1M+), critical for claims
3. SUBLIMITS - All 36+ sublimits from Supplemental Declarations
4. CARRIERS - All 8+ carriers with policy numbers
5. LLOYD'S SYNDICATES - All syndicate numbers and abbreviations
6. CYBER COVERAGE - Full cyber suite with all sublimits
7. EXCLUSIONS - Major exclusions (Flood status, Named Storm restrictions)
8. PREMIUM BREAKDOWN - By carrier and coverage type

Return ONLY the JSON object. Extract EVERYTHING visible. Use null for truly missing fields."""


class ExtractionService:
    """Service for extracting structured data from insurance documents.

    Features:
    - JSON mode enforcement via OpenRouter API
    - Validation retry with error context
    - Chunked extraction for large documents
    - Parallel processing with intelligent merge
    - Custom validation hooks
    """

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "google/gemini-2.5-flash"

    # Chunking configuration (kept for backward compatibility)
    MAX_CHARS_PER_CHUNK = 50000  # ~50K chars per chunk
    CHUNK_OVERLAP = 2000  # Overlap between chunks to avoid splitting mid-sentence
    MAX_SINGLE_PASS_CHARS = 60000  # Documents under this size use single-pass extraction

    def __init__(
        self,
        api_key: str | None = None,
        config: ExtractionConfig | None = None,
    ):
        """Initialize extraction service.

        Args:
            api_key: OpenRouter API key.
            config: Extraction configuration (uses DEFAULT_CONFIG if not provided).
        """
        self.api_key = api_key or settings.openrouter_api_key
        self.config = config or DEFAULT_CONFIG

        if not self.api_key:
            logger.warning("OpenRouter API key not configured")

        # Lazy-load services to avoid circular imports
        self._chunking_service = None
        self._merge_service = None
        self._validation_service = None

    @property
    def chunking_service(self):
        """Get or create chunking service."""
        if self._chunking_service is None:
            from app.services.chunking_service import ChunkingService

            self._chunking_service = ChunkingService(
                max_chars=self.config.max_chunk_chars,
                overlap_chars=self.config.chunk_overlap_chars,
            )
        return self._chunking_service

    @property
    def merge_service(self):
        """Get or create merge service."""
        if self._merge_service is None:
            from app.services.merge_service import MergeService

            self._merge_service = MergeService()
        return self._merge_service

    @property
    def validation_service(self):
        """Get or create validation service."""
        if self._validation_service is None:
            from app.services.validation_service import ValidationService

            self._validation_service = ValidationService()
        return self._validation_service

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split document text into chunks for parallel processing.

        Splits on page boundaries (<!-- Page N -->) when possible,
        otherwise splits on paragraph boundaries.

        Args:
            text: Full document text.

        Returns:
            List of text chunks.
        """
        if len(text) <= self.MAX_SINGLE_PASS_CHARS:
            return [text]

        # Try to split on page boundaries first
        page_pattern = r"(<!-- Page \d+ -->)"
        pages = re.split(page_pattern, text)

        # Reconstruct pages with their markers
        reconstructed_pages = []
        i = 0
        while i < len(pages):
            if re.match(page_pattern, pages[i]):
                # This is a page marker, combine with next content
                if i + 1 < len(pages):
                    reconstructed_pages.append(pages[i] + pages[i + 1])
                    i += 2
                else:
                    reconstructed_pages.append(pages[i])
                    i += 1
            else:
                if pages[i].strip():
                    reconstructed_pages.append(pages[i])
                i += 1

        # Now group pages into chunks
        chunks = []
        current_chunk = ""

        for page in reconstructed_pages:
            if len(current_chunk) + len(page) <= self.MAX_CHARS_PER_CHUNK:
                current_chunk += page
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = page

        if current_chunk:
            chunks.append(current_chunk)

        logger.info(f"Split document into {len(chunks)} chunks")
        return chunks

    def _merge_policy_extractions(
        self, extractions: list[PolicyExtraction], chunk_indices: list[int] | None = None
    ) -> PolicyExtraction:
        """Merge multiple policy extractions into one.

        Prioritizes early chunks for key metadata (declaration pages are at the start),
        combines lists, and deduplicates coverages.

        Args:
            extractions: List of PolicyExtraction from different chunks.
            chunk_indices: Original chunk indices (to prioritize early chunks for metadata).

        Returns:
            Merged PolicyExtraction.
        """
        if not extractions:
            return PolicyExtraction(policy_type=PolicyType.UNKNOWN)

        if len(extractions) == 1:
            return extractions[0]

        # If we have chunk indices, pair them with extractions
        if chunk_indices:
            indexed_extractions = list(zip(chunk_indices, extractions))
            # Sort by chunk index (early chunks first) for metadata priority
            indexed_extractions.sort(key=lambda x: x[0])
            extractions_ordered = [ext for _, ext in indexed_extractions]
        else:
            extractions_ordered = extractions

        # Start with the first chunk's extraction as base (declaration page is usually first)
        # This ensures we get the correct policy type, carrier, dates from the dec page
        merged = extractions_ordered[0].model_copy()

        # Merge fields from other extractions
        all_coverages = []
        all_additional_insureds = set()
        all_exclusions = set()
        all_special_conditions = set()
        all_source_pages = set()

        for ext in extractions_ordered:
            # Only take values from later chunks if early chunks didn't have them
            if ext.policy_number and not merged.policy_number:
                merged.policy_number = ext.policy_number
            if ext.carrier_name and not merged.carrier_name:
                merged.carrier_name = ext.carrier_name
            if ext.effective_date and not merged.effective_date:
                merged.effective_date = ext.effective_date
            if ext.expiration_date and not merged.expiration_date:
                merged.expiration_date = ext.expiration_date
            if ext.named_insured and not merged.named_insured:
                merged.named_insured = ext.named_insured
            if ext.premium and not merged.premium:
                merged.premium = ext.premium
            if ext.total_cost and not merged.total_cost:
                merged.total_cost = ext.total_cost

            # Collect all coverages
            all_coverages.extend(ext.coverages)
            all_additional_insureds.update(ext.additional_insureds)
            all_exclusions.update(ext.exclusions)
            all_special_conditions.update(ext.special_conditions)
            all_source_pages.update(ext.source_pages)

        # Deduplicate coverages by name
        seen_coverages = {}
        for cov in all_coverages:
            key = cov.coverage_name.lower()
            if key not in seen_coverages or cov.confidence > seen_coverages[key].confidence:
                seen_coverages[key] = cov

        merged.coverages = list(seen_coverages.values())
        merged.additional_insureds = list(all_additional_insureds)
        merged.exclusions = list(all_exclusions)
        merged.special_conditions = list(all_special_conditions)
        merged.source_pages = sorted(all_source_pages)

        # Average confidence
        merged.confidence = sum(e.confidence for e in extractions) / len(extractions)

        return merged

    def _merge_coi_extractions(self, extractions: list[COIExtraction]) -> COIExtraction:
        """Merge multiple COI extractions into one."""
        if not extractions:
            return COIExtraction()

        if len(extractions) == 1:
            return extractions[0]

        # Start with highest confidence
        extractions_sorted = sorted(extractions, key=lambda x: x.confidence, reverse=True)
        merged = extractions_sorted[0].model_copy()

        # Merge policies from all extractions
        all_policies = []
        all_additional_insureds = set()

        for ext in extractions:
            all_policies.extend(ext.policies)
            all_additional_insureds.update(ext.additional_insureds)

            # Fill in missing fields
            if ext.certificate_number and not merged.certificate_number:
                merged.certificate_number = ext.certificate_number
            if ext.producer_name and not merged.producer_name:
                merged.producer_name = ext.producer_name
            if ext.insured_name and not merged.insured_name:
                merged.insured_name = ext.insured_name
            if ext.holder_name and not merged.holder_name:
                merged.holder_name = ext.holder_name

            # Merge insurers dict
            for key, value in ext.insurers.items():
                if key not in merged.insurers or not merged.insurers[key].get("name"):
                    merged.insurers[key] = value

        # Deduplicate policies by policy number
        seen_policies = {}
        for pol in all_policies:
            key = pol.policy_number or f"{pol.policy_type}_{pol.carrier_name}"
            if key not in seen_policies or pol.confidence > seen_policies[key].confidence:
                seen_policies[key] = pol

        merged.policies = list(seen_policies.values())
        merged.additional_insureds = list(all_additional_insureds)
        merged.confidence = sum(e.confidence for e in extractions) / len(extractions)

        return merged

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return None

    def _parse_policy_type(self, type_str: str | None) -> PolicyType:
        """Parse policy type string to enum."""
        if not type_str:
            return PolicyType.UNKNOWN
        type_map = {
            "property": PolicyType.PROPERTY,
            "general_liability": PolicyType.GENERAL_LIABILITY,
            "umbrella": PolicyType.UMBRELLA,
            "excess": PolicyType.EXCESS,
            "flood": PolicyType.FLOOD,
            "earthquake": PolicyType.EARTHQUAKE,
            "terrorism": PolicyType.TERRORISM,
            "crime": PolicyType.CRIME,
            "cyber": PolicyType.CYBER,
            "epl": PolicyType.EPL,
            "dno": PolicyType.DNO,
            "auto": PolicyType.AUTO,
            "workers_comp": PolicyType.WORKERS_COMP,
            "boiler_machinery": PolicyType.BOILER_MACHINERY,
        }
        return type_map.get(type_str.lower(), PolicyType.UNKNOWN)

    def _repair_json(self, content: str) -> str:
        """Attempt to repair malformed JSON.

        Common issues:
        - Trailing commas
        - Missing quotes around keys
        - Truncated JSON (missing closing brackets)
        - Control characters in strings
        """
        # Remove any text before the first { or [
        first_brace = content.find("{")
        first_bracket = content.find("[")
        if first_brace == -1 and first_bracket == -1:
            return content
        if first_brace == -1:
            start = first_bracket
        elif first_bracket == -1:
            start = first_brace
        else:
            start = min(first_brace, first_bracket)
        content = content[start:]

        # Remove trailing commas before } or ]
        content = re.sub(r",\s*}", "}", content)
        content = re.sub(r",\s*]", "]", content)

        # Remove control characters except newlines and tabs
        content = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", content)

        # Try to balance brackets if truncated
        open_braces = content.count("{") - content.count("}")
        open_brackets = content.count("[") - content.count("]")

        # Add missing closing brackets/braces
        content = content + ("]" * open_brackets) + ("}" * open_braces)

        return content

    async def _call_llm_with_retry(
        self,
        prompt: str,
        config: ExtractionConfig | None = None,
    ) -> dict:
        """Call the LLM with retry logic, JSON repair, and validation context.

        Features:
        - Exponential backoff retry
        - JSON mode enforcement
        - Error context added to retry prompts
        - JSON repair for malformed responses

        Args:
            prompt: The prompt to send to the LLM.
            config: Extraction configuration (uses DEFAULT_CONFIG if not provided).

        Returns:
            Parsed JSON response as a dictionary.
        """
        if config is None:
            config = DEFAULT_CONFIG

        last_error = None
        last_raw_response = ""
        delay = config.initial_delay
        current_prompt = prompt

        for attempt in range(config.max_retries):
            try:
                result = await self._call_llm(current_prompt, use_json_mode=config.use_json_mode)
                return result
            except ExtractionError as e:
                last_error = e
                error_str = str(e)

                # Extract raw response if available for error context
                if "First 500 chars:" in error_str:
                    # Parse out the raw response from error message
                    last_raw_response = error_str

                if attempt < config.max_retries - 1:
                    logger.warning(
                        f"Extraction attempt {attempt + 1}/{config.max_retries} failed, "
                        f"retrying in {delay:.1f}s... Error: {e}"
                    )

                    # Add error context to prompt for retry
                    current_prompt = self._add_error_context_to_prompt(
                        prompt, error_str, last_raw_response
                    )

                    # Exponential backoff
                    await asyncio.sleep(delay)
                    delay *= config.backoff_multiplier

        # All retries failed
        raise last_error

    def _add_error_context_to_prompt(
        self, original_prompt: str, error: str, raw_response: str
    ) -> str:
        """Add error context to prompt for retry attempts.

        This helps the LLM understand what went wrong and produce valid output.

        Args:
            original_prompt: The original extraction prompt.
            error: The error message from the failed attempt.
            raw_response: The raw response that failed (if available).

        Returns:
            Updated prompt with error context.
        """
        error_context = """

IMPORTANT - RETRY CONTEXT:
Your previous response could not be parsed as valid JSON.
"""
        if "JSONDecodeError" in error or "parse" in error.lower():
            error_context += """
Error type: Invalid JSON format
Please ensure your response is ONLY valid JSON with no additional text, markdown, or explanation.
Do not wrap the JSON in code blocks (```).
"""
        elif "validation" in error.lower():
            error_context += f"""
Error type: Schema validation failed
Details: {error[:500]}
Please ensure all required fields are present and have the correct data types.
"""
        else:
            error_context += f"""
Error: {error[:300]}
"""

        error_context += """
Respond with ONLY the JSON object. No markdown, no explanation, just valid JSON."""

        return original_prompt + error_context

    async def _call_llm(self, prompt: str, use_json_mode: bool = True) -> dict:
        """Call the LLM and return parsed JSON response.

        Args:
            prompt: The prompt to send to the LLM.
            use_json_mode: Whether to enforce JSON output mode via API parameter.

        Returns:
            Parsed JSON response as a dictionary.
        """
        if not self.api_key:
            raise ExtractionError("OpenRouter API key not configured")

        # Build request body
        request_body = {
            "model": self.MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 16000,  # Increased for complex extractions
        }

        # Add JSON mode if enabled - forces valid JSON output at API level
        if use_json_mode:
            request_body["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                self.OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.dev",
                    "X-Title": "Open Insurance Platform",
                },
                json=request_body,
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenRouter API error: {response.status_code} - {error_detail}")
                raise ExtractionAPIError(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )

            result = response.json()

        # Extract and parse JSON content
        try:
            content = result["choices"][0]["message"]["content"]
            content = content.strip()

            # Strip markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # First try to parse as-is
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to repair the JSON
                logger.warning("Initial JSON parse failed, attempting repair...")
                repaired = self._repair_json(content)
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError as repair_error:
                    # Log the problematic content for debugging
                    logger.error(f"JSON repair failed. First 500 chars: {repaired[:500]}")
                    logger.error(f"Last 500 chars: {repaired[-500:]}")
                    raise ExtractionError(
                        f"Failed to parse LLM response even after repair: {repair_error}"
                    )

        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract content from LLM response: {e}")
            raise ExtractionError(f"Failed to extract content from LLM response: {e}")

    async def extract_policy(self, document_text: str) -> PolicyExtraction:
        """Extract policy information from document text."""
        logger.info("Extracting policy information...")

        prompt = POLICY_EXTRACTION_PROMPT.format(document_text=document_text)
        data = await self._call_llm_with_retry(prompt)

        # Parse coverages
        coverages = []
        for cov_data in data.get("coverages", []):
            coverages.append(
                CoverageExtraction(
                    coverage_name=cov_data.get("coverage_name", "Unknown"),
                    coverage_category=cov_data.get("coverage_category"),
                    limit_amount=cov_data.get("limit_amount"),
                    limit_type=cov_data.get("limit_type"),
                    sublimit=cov_data.get("sublimit"),
                    sublimit_applies_to=cov_data.get("sublimit_applies_to"),
                    deductible_amount=cov_data.get("deductible_amount"),
                    deductible_type=cov_data.get("deductible_type"),
                    deductible_pct=cov_data.get("deductible_pct"),
                    deductible_minimum=cov_data.get("deductible_minimum"),
                    deductible_maximum=cov_data.get("deductible_maximum"),
                    coinsurance_pct=cov_data.get("coinsurance_pct"),
                    waiting_period_hours=cov_data.get("waiting_period_hours"),
                    valuation_type=cov_data.get("valuation_type"),
                    margin_clause_pct=cov_data.get("margin_clause_pct"),
                    exclusions=cov_data.get("exclusions", []),
                    conditions=cov_data.get("conditions", []),
                    source_page=cov_data.get("source_page"),
                    confidence=cov_data.get("confidence", 0.5),
                )
            )

        return PolicyExtraction(
            policy_type=self._parse_policy_type(data.get("policy_type")),
            policy_number=data.get("policy_number"),
            carrier_name=data.get("carrier_name"),
            effective_date=self._parse_date(data.get("effective_date")),
            expiration_date=self._parse_date(data.get("expiration_date")),
            named_insured=data.get("named_insured"),
            insured_address=data.get("insured_address"),
            premium=data.get("premium"),
            taxes=data.get("taxes"),
            fees=data.get("fees"),
            total_cost=data.get("total_cost"),
            admitted=data.get("admitted"),
            form_type=data.get("form_type"),
            policy_form=data.get("policy_form"),
            coverages=coverages,
            mortgagee_name=data.get("mortgagee_name"),
            mortgagee_clause=data.get("mortgagee_clause"),
            loss_payee=data.get("loss_payee"),
            additional_insureds=data.get("additional_insureds", []),
            exclusions=data.get("exclusions", []),
            special_conditions=data.get("special_conditions", []),
            source_pages=data.get("source_pages", []),
            confidence=data.get("confidence", 0.5),
        )

    async def extract_coi(self, document_text: str) -> COIExtraction:
        """Extract Certificate of Insurance information."""
        logger.info("Extracting COI information...")

        prompt = COI_EXTRACTION_PROMPT.format(document_text=document_text)
        data = await self._call_llm_with_retry(prompt)

        # Parse policies referenced in COI
        policies = []
        for pol_data in data.get("policies", []):
            # Filter out None values from limits dict
            raw_limits = pol_data.get("limits", {})
            limits = {k: v for k, v in raw_limits.items() if v is not None} if raw_limits else {}

            policies.append(
                COIPolicyReference(
                    insurer_letter=pol_data.get("insurer_letter"),
                    policy_type=self._parse_policy_type(pol_data.get("policy_type")),
                    policy_number=pol_data.get("policy_number"),
                    carrier_name=pol_data.get("carrier_name"),
                    naic_number=pol_data.get("naic_number"),
                    effective_date=self._parse_date(pol_data.get("effective_date")),
                    expiration_date=self._parse_date(pol_data.get("expiration_date")),
                    coverage_form=pol_data.get("coverage_form"),
                    is_additional_insured=bool(pol_data.get("is_additional_insured")),
                    is_subrogation_waived=bool(pol_data.get("is_subrogation_waived")),
                    aggregate_limit_applies_per=pol_data.get("aggregate_limit_applies_per"),
                    limits=limits,
                    confidence=pol_data.get("confidence", 0.5),
                )
            )

        return COIExtraction(
            # Certificate Identity
            certificate_number=data.get("certificate_number"),
            revision_number=data.get("revision_number"),
            issue_date=self._parse_date(data.get("issue_date")),
            # Producer Info
            producer_name=data.get("producer_name"),
            producer_address=data.get("producer_address"),
            producer_phone=data.get("producer_phone"),
            producer_email=data.get("producer_email"),
            producer_reference=data.get("producer_reference"),
            # Insured & Holder
            insured_name=data.get("insured_name"),
            insured_address=data.get("insured_address"),
            holder_name=data.get("holder_name"),
            holder_address=data.get("holder_address"),
            # Insurers
            insurers=data.get("insurers", {}),
            policies=policies,
            # GL Limits
            gl_each_occurrence=data.get("gl_each_occurrence"),
            gl_damage_to_rented=data.get("gl_damage_to_rented"),
            gl_medical_expense=data.get("gl_medical_expense"),
            gl_personal_advertising=data.get("gl_personal_advertising"),
            gl_general_aggregate=data.get("gl_general_aggregate"),
            gl_products_completed=data.get("gl_products_completed"),
            gl_coverage_form=data.get("gl_coverage_form"),
            gl_aggregate_limit_applies_per=data.get("gl_aggregate_limit_applies_per"),
            # Auto Limits
            auto_combined_single=data.get("auto_combined_single"),
            auto_bodily_injury_per_person=data.get("auto_bodily_injury_per_person"),
            auto_bodily_injury_per_accident=data.get("auto_bodily_injury_per_accident"),
            auto_property_damage=data.get("auto_property_damage"),
            auto_types=data.get("auto_types", []),
            # Umbrella
            umbrella_limit=data.get("umbrella_limit"),
            umbrella_aggregate=data.get("umbrella_aggregate"),
            umbrella_deductible=data.get("umbrella_deductible"),
            umbrella_retention=data.get("umbrella_retention"),
            umbrella_coverage_form=data.get("umbrella_coverage_form"),
            # Workers Comp
            workers_comp_per_statute=data.get("workers_comp_per_statute"),
            workers_comp_other=data.get("workers_comp_other"),
            workers_comp_each_accident=data.get("workers_comp_each_accident"),
            workers_comp_disease_ea_employee=data.get("workers_comp_disease_ea_employee"),
            workers_comp_disease_policy_limit=data.get("workers_comp_disease_policy_limit"),
            workers_comp_excluded_partners=data.get("workers_comp_excluded_partners"),
            # Property
            property_limit=data.get("property_limit"),
            # Description & Additional
            description_of_operations=data.get("description_of_operations"),
            additional_insureds=data.get("additional_insureds", []),
            subrogation_waiver_applies=bool(data.get("subrogation_waiver_applies")),
            # Cancellation
            cancellation_notice_days=data.get("cancellation_notice_days"),
            cancellation_terms=data.get("cancellation_terms"),
            authorized_representative=data.get("authorized_representative"),
            # Lender-Specific
            loan_number=data.get("loan_number"),
            mortgagee_clause=data.get("mortgagee_clause"),
            loss_payee_clause=data.get("loss_payee_clause"),
            confidence=data.get("confidence", 0.5),
        )

    async def extract_invoice(self, document_text: str) -> InvoiceExtraction:
        """Extract invoice information."""
        logger.info("Extracting invoice information...")

        prompt = INVOICE_EXTRACTION_PROMPT.format(document_text=document_text)
        data = await self._call_llm_with_retry(prompt)

        # Parse line items
        line_items = []
        for item_data in data.get("line_items", []):
            line_items.append(
                InvoiceLineItem(
                    description=item_data.get("description", ""),
                    amount=item_data.get("amount", 0),
                    policy_number=item_data.get("policy_number"),
                )
            )

        return InvoiceExtraction(
            invoice_number=data.get("invoice_number"),
            invoice_date=self._parse_date(data.get("invoice_date")),
            due_date=self._parse_date(data.get("due_date")),
            vendor_name=data.get("vendor_name"),
            vendor_address=data.get("vendor_address"),
            subtotal=data.get("subtotal"),
            taxes=data.get("taxes"),
            fees=data.get("fees"),
            total_amount=data.get("total_amount"),
            line_items=line_items,
            policy_numbers=data.get("policy_numbers", []),
            confidence=data.get("confidence", 0.5),
        )

    async def extract_sov(self, document_text: str) -> SOVExtraction:
        """Extract Statement of Values information."""
        logger.info("Extracting SOV information...")

        prompt = SOV_EXTRACTION_PROMPT.format(document_text=document_text)
        data = await self._call_llm_with_retry(prompt)

        # Parse properties
        properties = []
        for prop_data in data.get("properties", []):
            properties.append(
                SOVPropertyExtraction(
                    property_name=prop_data.get("property_name"),
                    address=prop_data.get("address"),
                    city=prop_data.get("city"),
                    state=prop_data.get("state"),
                    zip_code=prop_data.get("zip_code"),
                    building_value=prop_data.get("building_value"),
                    contents_value=prop_data.get("contents_value"),
                    business_income_value=prop_data.get("business_income_value"),
                    total_insured_value=prop_data.get("total_insured_value"),
                    construction_type=prop_data.get("construction_type"),
                    year_built=prop_data.get("year_built"),
                    square_footage=prop_data.get("square_footage"),
                    stories=prop_data.get("stories"),
                    occupancy=prop_data.get("occupancy"),
                )
            )

        return SOVExtraction(
            as_of_date=self._parse_date(data.get("as_of_date")),
            total_insured_value=data.get("total_insured_value"),
            properties=properties,
            confidence=data.get("confidence", 0.5),
        )

    async def extract_proposal(self, document_text: str) -> ProposalExtraction:
        """Extract proposal/quote comparison information."""
        logger.info("Extracting proposal information...")

        prompt = PROPOSAL_EXTRACTION_PROMPT.format(document_text=document_text)
        data = await self._call_llm_with_retry(prompt)

        # Parse properties
        properties = []
        for prop_data in data.get("properties", []):
            # Parse coverages for this property
            coverages = []
            for cov_data in prop_data.get("coverages", []):
                coverages.append(
                    ProposalCoverageQuote(
                        coverage_type=cov_data.get("coverage_type", "unknown"),
                        carrier_name=cov_data.get("carrier_name"),
                        limit_amount=cov_data.get("limit_amount"),
                        deductible_amount=cov_data.get("deductible_amount"),
                        expiring_premium=cov_data.get("expiring_premium"),
                        renewal_premium=cov_data.get("renewal_premium"),
                        premium_change=cov_data.get("premium_change"),
                        premium_change_pct=cov_data.get("premium_change_pct"),
                    )
                )

            properties.append(
                ProposalPropertyQuote(
                    property_name=prop_data.get("property_name"),
                    property_address=prop_data.get("property_address"),
                    unit_count=prop_data.get("unit_count"),
                    total_insured_value=prop_data.get("total_insured_value"),
                    expiring_tiv=prop_data.get("expiring_tiv"),
                    renewal_tiv=prop_data.get("renewal_tiv"),
                    coverages=coverages,
                    expiring_total_premium=prop_data.get("expiring_total_premium"),
                    renewal_total_premium=prop_data.get("renewal_total_premium"),
                    price_per_door_expiring=prop_data.get("price_per_door_expiring"),
                    price_per_door_renewal=prop_data.get("price_per_door_renewal"),
                )
            )

        return ProposalExtraction(
            proposal_title=data.get("proposal_title"),
            proposal_type=data.get("proposal_type"),
            named_insured=data.get("named_insured"),
            insured_address=data.get("insured_address"),
            effective_date=self._parse_date(data.get("effective_date")),
            expiration_date=self._parse_date(data.get("expiration_date")),
            properties=properties,
            portfolio_expiring_premium=data.get("portfolio_expiring_premium"),
            portfolio_renewal_premium=data.get("portfolio_renewal_premium"),
            portfolio_premium_change=data.get("portfolio_premium_change"),
            portfolio_premium_change_pct=data.get("portfolio_premium_change_pct"),
            carriers=data.get("carriers", []),
            confidence=data.get("confidence", 0.5),
        )

    async def extract_loss_run(self, document_text: str) -> LossRunExtraction:
        """Extract loss run / claims history information."""
        logger.info("Extracting loss run information...")

        prompt = LOSS_RUN_EXTRACTION_PROMPT.format(document_text=document_text)
        data = await self._call_llm_with_retry(prompt)

        # Parse claims
        claims = []
        for claim_data in data.get("claims", []):
            # Parse claim type
            claim_type = None
            claim_type_str = claim_data.get("claim_type")
            if claim_type_str:
                try:
                    claim_type = ClaimType(claim_type_str.lower())
                except ValueError:
                    claim_type = ClaimType.UNKNOWN

            # Parse claim status
            claim_status = None
            status_str = claim_data.get("claim_status")
            if status_str:
                try:
                    claim_status = ClaimStatus(status_str.lower())
                except ValueError:
                    claim_status = ClaimStatus.UNKNOWN

            claims.append(
                ClaimEntry(
                    claim_number=claim_data.get("claim_number"),
                    policy_number=claim_data.get("policy_number"),
                    carrier_name=claim_data.get("carrier_name"),
                    date_of_loss=self._parse_date(claim_data.get("date_of_loss")),
                    date_reported=self._parse_date(claim_data.get("date_reported")),
                    date_closed=self._parse_date(claim_data.get("date_closed")),
                    claim_type=claim_type,
                    claim_status=claim_status,
                    claimant_name=claim_data.get("claimant_name"),
                    description=claim_data.get("description"),
                    cause_of_loss=claim_data.get("cause_of_loss"),
                    location_address=claim_data.get("location_address"),
                    location_name=claim_data.get("location_name"),
                    paid_loss=claim_data.get("paid_loss"),
                    paid_expense=claim_data.get("paid_expense"),
                    paid_medical=claim_data.get("paid_medical"),
                    paid_indemnity=claim_data.get("paid_indemnity"),
                    total_paid=claim_data.get("total_paid"),
                    reserve_loss=claim_data.get("reserve_loss"),
                    reserve_expense=claim_data.get("reserve_expense"),
                    reserve_medical=claim_data.get("reserve_medical"),
                    reserve_indemnity=claim_data.get("reserve_indemnity"),
                    total_reserve=claim_data.get("total_reserve"),
                    incurred_loss=claim_data.get("incurred_loss"),
                    incurred_expense=claim_data.get("incurred_expense"),
                    total_incurred=claim_data.get("total_incurred"),
                    subrogation_amount=claim_data.get("subrogation_amount"),
                    deductible_recovered=claim_data.get("deductible_recovered"),
                    salvage_amount=claim_data.get("salvage_amount"),
                    net_incurred=claim_data.get("net_incurred"),
                    litigation_status=claim_data.get("litigation_status"),
                    injury_description=claim_data.get("injury_description"),
                    notes=claim_data.get("notes"),
                )
            )

        # Parse summary
        summary = None
        summary_data = data.get("summary")
        if summary_data:
            summary = LossRunSummary(
                total_claims=summary_data.get("total_claims", 0),
                open_claims=summary_data.get("open_claims", 0),
                closed_claims=summary_data.get("closed_claims", 0),
                claims_by_type=summary_data.get("claims_by_type", {}),
                claims_by_year=summary_data.get("claims_by_year", {}),
                total_paid=summary_data.get("total_paid", 0.0),
                total_reserved=summary_data.get("total_reserved", 0.0),
                total_incurred=summary_data.get("total_incurred", 0.0),
                total_recovered=summary_data.get("total_recovered", 0.0),
                net_incurred=summary_data.get("net_incurred", 0.0),
                largest_claim_amount=summary_data.get("largest_claim_amount"),
                largest_claim_number=summary_data.get("largest_claim_number"),
                premium_for_period=summary_data.get("premium_for_period"),
                loss_ratio=summary_data.get("loss_ratio"),
            )

        # Parse lines of business
        lines_of_business = []
        for lob in data.get("lines_of_business", []):
            try:
                lines_of_business.append(PolicyType(lob.lower()))
            except ValueError:
                lines_of_business.append(PolicyType.UNKNOWN)

        # Parse primary line of business
        line_of_business = None
        lob_str = data.get("line_of_business")
        if lob_str:
            try:
                line_of_business = PolicyType(lob_str.lower())
            except ValueError:
                line_of_business = PolicyType.UNKNOWN

        return LossRunExtraction(
            report_title=data.get("report_title"),
            report_date=self._parse_date(data.get("report_date")),
            report_run_date=self._parse_date(data.get("report_run_date")),
            named_insured=data.get("named_insured"),
            insured_address=data.get("insured_address"),
            policy_number=data.get("policy_number"),
            policy_numbers=data.get("policy_numbers", []),
            carrier_name=data.get("carrier_name"),
            carriers=data.get("carriers", []),
            experience_period_start=self._parse_date(data.get("experience_period_start")),
            experience_period_end=self._parse_date(data.get("experience_period_end")),
            valuation_date=self._parse_date(data.get("valuation_date")),
            line_of_business=line_of_business,
            lines_of_business=lines_of_business,
            claims=claims,
            summary=summary,
            large_loss_threshold=data.get("large_loss_threshold"),
            report_notes=data.get("report_notes", []),
            confidence=data.get("confidence", 0.5),
        )

    async def extract_program(self, document_text: str) -> ProgramExtraction:
        """Extract multi-carrier insurance program information."""
        logger.info("Extracting program information...")

        prompt = PROGRAM_EXTRACTION_PROMPT.format(document_text=document_text)
        data = await self._call_llm_with_retry(prompt)

        # Parse carriers
        carriers = []
        for carrier_data in data.get("carriers", []):
            carriers.append(
                CarrierInfo(
                    carrier_name=carrier_data.get("carrier_name", "Unknown"),
                    carrier_code=carrier_data.get("carrier_code"),
                    policy_number=carrier_data.get("policy_number"),
                    naic_number=carrier_data.get("naic_number"),
                    address=carrier_data.get("address"),
                    am_best_rating=carrier_data.get("am_best_rating"),
                    admitted=carrier_data.get("admitted"),
                )
            )

        # Parse Lloyd's syndicates
        lloyds_syndicates = []
        for synd_data in data.get("lloyds_syndicates", []):
            lloyds_syndicates.append(
                LloydsSyndicate(
                    syndicate_number=synd_data.get("syndicate_number", ""),
                    syndicate_abbreviation=synd_data.get("syndicate_abbreviation"),
                    participation_percentage=synd_data.get("participation_percentage"),
                )
            )

        # Parse contract allocation
        contract_allocation = None
        ca_data = data.get("contract_allocation")
        if ca_data:
            layers = []
            for layer_data in ca_data.get("layers", []):
                layers.append(
                    ContractAllocationLayer(
                        layer_description=layer_data.get("layer_description", ""),
                        attachment_point=layer_data.get("attachment_point"),
                        layer_limit=layer_data.get("layer_limit"),
                        perils_covered=layer_data.get("perils_covered", []),
                        peril_codes=layer_data.get("peril_codes", []),
                        carrier_code=layer_data.get("carrier_code"),
                        carrier_name=layer_data.get("carrier_name"),
                        policy_number=layer_data.get("policy_number"),
                        participation_amount=layer_data.get("participation_amount"),
                        participation_percentage=layer_data.get("participation_percentage"),
                        rate_per_hundred=layer_data.get("rate_per_hundred"),
                    )
                )
            contract_allocation = ContractAllocation(
                account_number=ca_data.get("account_number"),
                layers=layers,
                peril_symbols=ca_data.get("peril_symbols", {}),
                max_risk_basis=ca_data.get("max_risk_basis"),
                max_limit=ca_data.get("max_limit"),
            )

        # Parse sublimits schedule
        sublimits = None
        sub_data = data.get("sublimits")
        if sub_data:
            additional_sublimits = []
            for sub_entry in sub_data.get("additional_sublimits", []):
                additional_sublimits.append(
                    SublimitEntry(
                        sublimit_name=sub_entry.get("sublimit_name", ""),
                        limit_amount=sub_entry.get("limit_amount"),
                        limit_type=sub_entry.get("limit_type"),
                        duration_days=sub_entry.get("duration_days"),
                        duration_type=sub_entry.get("duration_type"),
                        is_included=sub_entry.get("is_included", False),
                        is_not_covered=sub_entry.get("is_not_covered", False),
                        percentage_of=sub_entry.get("percentage_of"),
                        percentage_value=sub_entry.get("percentage_value"),
                        minimum_amount=sub_entry.get("minimum_amount"),
                        maximum_amount=sub_entry.get("maximum_amount"),
                        applies_to=sub_entry.get("applies_to"),
                        conditions=sub_entry.get("conditions", []),
                    )
                )
            sublimits = SublimitsSchedule(
                maximum_limit_of_liability=sub_data.get("maximum_limit_of_liability"),
                limit_basis=sub_data.get("limit_basis"),
                earth_movement_aggregate=sub_data.get("earth_movement_aggregate"),
                earth_movement_california_aggregate=sub_data.get("earth_movement_california_aggregate"),
                earth_movement_pacific_nw_aggregate=sub_data.get("earth_movement_pacific_nw_aggregate"),
                earth_movement_new_madrid_aggregate=sub_data.get("earth_movement_new_madrid_aggregate"),
                flood_aggregate=sub_data.get("flood_aggregate"),
                flood_sfha_aggregate=sub_data.get("flood_sfha_aggregate"),
                named_storm_limit=sub_data.get("named_storm_limit"),
                named_storm_is_included=sub_data.get("named_storm_is_included", False),
                accounts_receivable=sub_data.get("accounts_receivable"),
                civil_authority_days=sub_data.get("civil_authority_days"),
                civil_authority_limit=sub_data.get("civil_authority_limit"),
                contingent_time_element_days=sub_data.get("contingent_time_element_days"),
                contingent_time_element_limit=sub_data.get("contingent_time_element_limit"),
                debris_removal_percentage=sub_data.get("debris_removal_percentage"),
                debris_removal_limit=sub_data.get("debris_removal_limit"),
                electronic_data_media=sub_data.get("electronic_data_media"),
                errors_omissions=sub_data.get("errors_omissions"),
                extended_period_of_indemnity_days=sub_data.get("extended_period_of_indemnity_days"),
                extra_expense=sub_data.get("extra_expense"),
                fine_arts=sub_data.get("fine_arts"),
                fire_brigade_charges=sub_data.get("fire_brigade_charges"),
                fungus_mold_aggregate=sub_data.get("fungus_mold_aggregate"),
                ingress_egress_days=sub_data.get("ingress_egress_days"),
                ingress_egress_limit=sub_data.get("ingress_egress_limit"),
                leasehold_interest=sub_data.get("leasehold_interest"),
                pollution_aggregate=sub_data.get("pollution_aggregate"),
                newly_acquired_property_days=sub_data.get("newly_acquired_property_days"),
                newly_acquired_property_limit=sub_data.get("newly_acquired_property_limit"),
                ordinance_law_coverage_a=sub_data.get("ordinance_law_coverage_a"),
                ordinance_law_coverage_b=sub_data.get("ordinance_law_coverage_b"),
                ordinance_law_coverage_b_percentage=sub_data.get("ordinance_law_coverage_b_percentage"),
                ordinance_law_coverage_c=sub_data.get("ordinance_law_coverage_c"),
                ordinance_law_coverage_d=sub_data.get("ordinance_law_coverage_d"),
                ordinance_law_coverage_e=sub_data.get("ordinance_law_coverage_e"),
                ordinary_payroll_days=sub_data.get("ordinary_payroll_days"),
                service_interruption_limit=sub_data.get("service_interruption_limit"),
                service_interruption_waiting_hours=sub_data.get("service_interruption_waiting_hours"),
                spoilage=sub_data.get("spoilage"),
                transit=sub_data.get("transit"),
                valuable_papers_records=sub_data.get("valuable_papers_records"),
                additional_sublimits=additional_sublimits,
            )

        # Parse deductible schedule
        deductibles = None
        ded_data = data.get("deductibles")
        if ded_data:
            additional_deductibles = []
            for ded_entry in ded_data.get("additional_deductibles", []):
                additional_deductibles.append(
                    DeductibleEntry(
                        deductible_name=ded_entry.get("deductible_name", ""),
                        deductible_type=ded_entry.get("deductible_type"),
                        flat_amount=ded_entry.get("flat_amount"),
                        percentage_of_tiv=ded_entry.get("percentage_of_tiv"),
                        percentage_basis=ded_entry.get("percentage_basis"),
                        minimum_amount=ded_entry.get("minimum_amount"),
                        maximum_amount=ded_entry.get("maximum_amount"),
                        waiting_period_hours=ded_entry.get("waiting_period_hours"),
                        applies_to_perils=ded_entry.get("applies_to_perils", []),
                        applies_to_locations=ded_entry.get("applies_to_locations"),
                        conditions=ded_entry.get("conditions", []),
                    )
                )
            deductibles = DeductibleSchedule(
                base_property_deductible=ded_data.get("base_property_deductible"),
                base_time_element_deductible=ded_data.get("base_time_element_deductible"),
                base_combined_deductible=ded_data.get("base_combined_deductible"),
                earth_movement_percentage=ded_data.get("earth_movement_percentage"),
                earth_movement_minimum=ded_data.get("earth_movement_minimum"),
                earth_movement_california_percentage=ded_data.get("earth_movement_california_percentage"),
                earth_movement_california_minimum=ded_data.get("earth_movement_california_minimum"),
                windstorm_hail_percentage=ded_data.get("windstorm_hail_percentage"),
                windstorm_hail_minimum=ded_data.get("windstorm_hail_minimum"),
                named_storm_percentage=ded_data.get("named_storm_percentage"),
                named_storm_minimum=ded_data.get("named_storm_minimum"),
                hurricane_percentage=ded_data.get("hurricane_percentage"),
                hurricane_minimum=ded_data.get("hurricane_minimum"),
                flood_deductible=ded_data.get("flood_deductible"),
                flood_sfha_deductible=ded_data.get("flood_sfha_deductible"),
                equipment_breakdown_deductible=ded_data.get("equipment_breakdown_deductible"),
                cyber_deductible=ded_data.get("cyber_deductible"),
                terrorism_deductible=ded_data.get("terrorism_deductible"),
                deductible_application_rules=ded_data.get("deductible_application_rules", []),
                additional_deductibles=additional_deductibles,
            )

        # Parse cyber coverage
        cyber_coverage = None
        cyber_data = data.get("cyber_coverage")
        if cyber_data:
            cyber_coverage = CyberCoverage(
                cyber_aggregate_limit=cyber_data.get("cyber_aggregate_limit"),
                cyber_deductible=cyber_data.get("cyber_deductible"),
                identity_recovery_limit=cyber_data.get("identity_recovery_limit"),
                forensic_it_review_limit=cyber_data.get("forensic_it_review_limit"),
                legal_review_limit=cyber_data.get("legal_review_limit"),
                notification_limit=cyber_data.get("notification_limit"),
                public_relations_limit=cyber_data.get("public_relations_limit"),
                regulatory_fines_limit=cyber_data.get("regulatory_fines_limit"),
                pci_fines_limit=cyber_data.get("pci_fines_limit"),
                first_party_malware_limit=cyber_data.get("first_party_malware_limit"),
                loss_of_business_limit=cyber_data.get("loss_of_business_limit"),
                data_restoration_limit=cyber_data.get("data_restoration_limit"),
                system_restoration_limit=cyber_data.get("system_restoration_limit"),
                cyber_extortion_limit=cyber_data.get("cyber_extortion_limit"),
                data_compromise_liability_limit=cyber_data.get("data_compromise_liability_limit"),
                network_security_liability_limit=cyber_data.get("network_security_liability_limit"),
                electronic_media_liability_limit=cyber_data.get("electronic_media_liability_limit"),
                lost_wages_limit=cyber_data.get("lost_wages_limit"),
                mental_health_counseling_limit=cyber_data.get("mental_health_counseling_limit"),
                miscellaneous_costs_limit=cyber_data.get("miscellaneous_costs_limit"),
            )

        # Parse equipment breakdown
        equipment_breakdown = None
        eb_data = data.get("equipment_breakdown")
        if eb_data:
            equipment_breakdown = EquipmentBreakdownCoverage(
                equipment_breakdown_limit=eb_data.get("equipment_breakdown_limit"),
                equipment_breakdown_deductible=eb_data.get("equipment_breakdown_deductible"),
                time_element_coverage=eb_data.get("time_element_coverage"),
                extra_expense_limit=eb_data.get("extra_expense_limit"),
                data_restoration_limit=eb_data.get("data_restoration_limit"),
                expediting_expenses_limit=eb_data.get("expediting_expenses_limit"),
                green_upgrades_limit=eb_data.get("green_upgrades_limit"),
                hazardous_substances_limit=eb_data.get("hazardous_substances_limit"),
                off_premises_limit=eb_data.get("off_premises_limit"),
                service_interruption_included=eb_data.get("service_interruption_included", False),
                spoilage_limit=eb_data.get("spoilage_limit"),
                spoilage_coinsurance=eb_data.get("spoilage_coinsurance"),
                public_relations_included=eb_data.get("public_relations_included", False),
            )

        # Parse terrorism coverage
        terrorism_coverage = None
        terr_data = data.get("terrorism_coverage")
        if terr_data:
            terrorism_coverage = TerrorismCoverage(
                terrorism_form=terr_data.get("terrorism_form"),
                terrorism_limit=terr_data.get("terrorism_limit"),
                terrorism_limit_basis=terr_data.get("terrorism_limit_basis"),
                terrorism_deductible=terr_data.get("terrorism_deductible"),
                certified_terrorism_covered=terr_data.get("certified_terrorism_covered"),
                non_certified_terrorism_covered=terr_data.get("non_certified_terrorism_covered"),
                tria_exclusion_form=terr_data.get("tria_exclusion_form"),
            )

        # Parse sinkhole coverage
        sinkhole_coverage = None
        sink_data = data.get("sinkhole_coverage")
        if sink_data:
            sinkhole_coverage = SinkholeCoverage(
                sinkhole_covered=sink_data.get("sinkhole_covered", False),
                catastrophic_ground_cover_collapse_covered=sink_data.get(
                    "catastrophic_ground_cover_collapse_covered", False
                ),
                florida_specific=sink_data.get("florida_specific", False),
                valuation_type=sink_data.get("valuation_type"),
                neutral_evaluation_available=sink_data.get("neutral_evaluation_available", False),
                stabilization_requirements=sink_data.get("stabilization_requirements", []),
                exclusions=sink_data.get("exclusions", []),
            )

        # Parse CAT covered property
        cat_covered_property = None
        cat_data = data.get("cat_covered_property")
        if cat_data:
            cat_covered_property = CATCoveredProperty(
                cat_property_limit=cat_data.get("cat_property_limit"),
                cat_property_deductible_percentage=cat_data.get("cat_property_deductible_percentage"),
                cat_property_minimum_deductible=cat_data.get("cat_property_minimum_deductible"),
                excluded_property_types=cat_data.get("excluded_property_types", []),
                requires_scheduling=cat_data.get("requires_scheduling", []),
                covered_if_scheduled=cat_data.get("covered_if_scheduled", []),
            )

        # Parse valuation bases
        valuation_bases = []
        for val_data in data.get("valuation_bases", []):
            valuation_bases.append(
                ValuationBasis(
                    property_type=val_data.get("property_type", ""),
                    valuation_type=val_data.get("valuation_type", ""),
                    conditions=val_data.get("conditions", []),
                )
            )

        # Parse restrictions
        restrictions = []
        for restr_data in data.get("restrictions", []):
            restrictions.append(
                PolicyRestriction(
                    restriction_type=restr_data.get("restriction_type", ""),
                    description=restr_data.get("description", ""),
                    applies_to=restr_data.get("applies_to"),
                    source_endorsement=restr_data.get("source_endorsement"),
                )
            )

        # Parse service of suit
        service_of_suit = []
        for sos_data in data.get("service_of_suit", []):
            service_of_suit.append(
                ServiceOfSuit(
                    carrier_name=sos_data.get("carrier_name", ""),
                    service_address=sos_data.get("service_address"),
                    contact_name=sos_data.get("contact_name"),
                    lma_form=sos_data.get("lma_form"),
                )
            )

        # Parse forms schedule
        forms_schedule = []
        for form_data in data.get("forms_schedule", []):
            forms_schedule.append(
                FormsEndorsementsSchedule(
                    form_number=form_data.get("form_number", ""),
                    form_title=form_data.get("form_title"),
                    form_description=form_data.get("form_description"),
                )
            )

        # Parse coverages
        coverages = []
        for cov_data in data.get("coverages", []):
            coverages.append(
                CoverageExtraction(
                    coverage_name=cov_data.get("coverage_name", "Unknown"),
                    coverage_category=cov_data.get("coverage_category"),
                    limit_amount=cov_data.get("limit_amount"),
                    limit_type=cov_data.get("limit_type"),
                    deductible_amount=cov_data.get("deductible_amount"),
                    deductible_type=cov_data.get("deductible_type"),
                    valuation_type=cov_data.get("valuation_type"),
                    exclusions=cov_data.get("exclusions", []),
                    conditions=cov_data.get("conditions", []),
                    source_page=cov_data.get("source_page"),
                    confidence=cov_data.get("confidence", 0.5),
                )
            )

        return ProgramExtraction(
            account_number=data.get("account_number"),
            program_name=data.get("program_name"),
            named_insured=data.get("named_insured"),
            insured_address=data.get("insured_address"),
            additional_named_insureds=data.get("additional_named_insureds", []),
            effective_date=self._parse_date(data.get("effective_date")),
            expiration_date=self._parse_date(data.get("expiration_date")),
            producer_name=data.get("producer_name"),
            producer_address=data.get("producer_address"),
            program_manager=data.get("program_manager"),
            program_manager_address=data.get("program_manager_address"),
            correspondent=data.get("correspondent"),
            total_premium=data.get("total_premium"),
            premium_by_state=data.get("premium_by_state", {}),
            taxes=data.get("taxes"),
            fees=data.get("fees"),
            surplus_lines_tax=data.get("surplus_lines_tax"),
            inspection_fee=data.get("inspection_fee"),
            program_fee=data.get("program_fee"),
            total_cost=data.get("total_cost"),
            minimum_earned_premium=data.get("minimum_earned_premium"),
            carriers=carriers,
            lloyds_syndicates=lloyds_syndicates,
            contract_allocation=contract_allocation,
            carrier_premiums=data.get("carrier_premiums", {}),
            sublimits=sublimits,
            deductibles=deductibles,
            cyber_coverage=cyber_coverage,
            equipment_breakdown=equipment_breakdown,
            terrorism_coverage=terrorism_coverage,
            sinkhole_coverage=sinkhole_coverage,
            cat_covered_property=cat_covered_property,
            valuation_bases=valuation_bases,
            restrictions=restrictions,
            major_exclusions=data.get("major_exclusions", []),
            coverage_territory=data.get("coverage_territory"),
            service_of_suit=service_of_suit,
            forms_schedule=forms_schedule,
            state_notices=data.get("state_notices", {}),
            coverages=coverages,
            source_pages=data.get("source_pages", []),
            confidence=data.get("confidence", 0.5),
        )

    async def _extract_program_from_chunk(
        self, chunk: str, chunk_index: int
    ) -> ProgramExtraction | None:
        """Extract program from a single chunk, handling errors gracefully."""
        try:
            logger.info(f"Extracting program from chunk {chunk_index + 1} ({len(chunk)} chars)")
            return await self.extract_program(chunk)
        except Exception as e:
            logger.warning(f"Chunk {chunk_index + 1} program extraction failed: {e}")
            return None

    def _merge_program_extractions(
        self, extractions: list[ProgramExtraction], chunk_indices: list[int] | None = None
    ) -> ProgramExtraction:
        """Merge multiple program extractions into one.

        Prioritizes early chunks for key metadata (declaration pages are at the start),
        combines lists, and deduplicates.
        """
        if not extractions:
            return ProgramExtraction()

        if len(extractions) == 1:
            return extractions[0]

        # If we have chunk indices, pair them with extractions
        if chunk_indices:
            indexed_extractions = list(zip(chunk_indices, extractions))
            indexed_extractions.sort(key=lambda x: x[0])
            extractions_ordered = [ext for _, ext in indexed_extractions]
        else:
            extractions_ordered = extractions

        # Start with the first chunk's extraction as base
        merged = extractions_ordered[0].model_copy(deep=True)

        # Collect items for merging
        all_carriers = {c.policy_number or c.carrier_name: c for c in merged.carriers}
        all_syndicates = {s.syndicate_number: s for s in merged.lloyds_syndicates}
        all_layers = []
        all_valuation_bases = []
        all_restrictions = []
        all_service_of_suit = {s.carrier_name: s for s in merged.service_of_suit}
        all_forms = {f.form_number: f for f in merged.forms_schedule}
        all_coverages = {c.coverage_name.lower(): c for c in merged.coverages}
        all_major_exclusions = set(merged.major_exclusions)

        if merged.contract_allocation:
            all_layers.extend(merged.contract_allocation.layers)

        for ext in extractions_ordered[1:]:
            # Merge carriers
            for carrier in ext.carriers:
                key = carrier.policy_number or carrier.carrier_name
                if key not in all_carriers:
                    all_carriers[key] = carrier

            # Merge syndicates
            for synd in ext.lloyds_syndicates:
                if synd.syndicate_number not in all_syndicates:
                    all_syndicates[synd.syndicate_number] = synd

            # Merge contract allocation layers
            if ext.contract_allocation:
                all_layers.extend(ext.contract_allocation.layers)
                # Merge peril symbols
                if merged.contract_allocation:
                    merged.contract_allocation.peril_symbols.update(
                        ext.contract_allocation.peril_symbols
                    )

            # Merge valuation bases
            all_valuation_bases.extend(ext.valuation_bases)

            # Merge restrictions
            all_restrictions.extend(ext.restrictions)

            # Merge service of suit
            for sos in ext.service_of_suit:
                if sos.carrier_name not in all_service_of_suit:
                    all_service_of_suit[sos.carrier_name] = sos

            # Merge forms
            for form in ext.forms_schedule:
                if form.form_number not in all_forms:
                    all_forms[form.form_number] = form

            # Merge coverages (take highest confidence)
            for cov in ext.coverages:
                key = cov.coverage_name.lower()
                if key not in all_coverages or cov.confidence > all_coverages[key].confidence:
                    all_coverages[key] = cov

            # Merge major exclusions
            all_major_exclusions.update(ext.major_exclusions)

            # Fill in missing scalar fields from later chunks
            if ext.account_number and not merged.account_number:
                merged.account_number = ext.account_number
            if ext.named_insured and not merged.named_insured:
                merged.named_insured = ext.named_insured
            if ext.total_premium and not merged.total_premium:
                merged.total_premium = ext.total_premium
            if ext.total_cost and not merged.total_cost:
                merged.total_cost = ext.total_cost

            # Merge sublimits (take first non-null)
            if ext.sublimits and not merged.sublimits:
                merged.sublimits = ext.sublimits

            # Merge deductibles (take first non-null)
            if ext.deductibles and not merged.deductibles:
                merged.deductibles = ext.deductibles

            # Merge cyber coverage
            if ext.cyber_coverage and not merged.cyber_coverage:
                merged.cyber_coverage = ext.cyber_coverage

            # Merge equipment breakdown
            if ext.equipment_breakdown and not merged.equipment_breakdown:
                merged.equipment_breakdown = ext.equipment_breakdown

            # Merge terrorism coverage
            if ext.terrorism_coverage and not merged.terrorism_coverage:
                merged.terrorism_coverage = ext.terrorism_coverage

            # Merge sinkhole coverage
            if ext.sinkhole_coverage and not merged.sinkhole_coverage:
                merged.sinkhole_coverage = ext.sinkhole_coverage

            # Merge CAT covered property
            if ext.cat_covered_property and not merged.cat_covered_property:
                merged.cat_covered_property = ext.cat_covered_property

            # Merge state notices
            merged.state_notices.update(ext.state_notices)

            # Merge carrier premiums
            merged.carrier_premiums.update(ext.carrier_premiums)

        # Apply merged collections
        merged.carriers = list(all_carriers.values())
        merged.lloyds_syndicates = list(all_syndicates.values())
        if merged.contract_allocation:
            # Deduplicate layers by description
            seen_layers = {}
            for layer in all_layers:
                key = f"{layer.layer_description}_{layer.carrier_code}_{layer.policy_number}"
                if key not in seen_layers:
                    seen_layers[key] = layer
            merged.contract_allocation.layers = list(seen_layers.values())
        merged.valuation_bases = all_valuation_bases
        merged.restrictions = all_restrictions
        merged.service_of_suit = list(all_service_of_suit.values())
        merged.forms_schedule = list(all_forms.values())
        merged.coverages = list(all_coverages.values())
        merged.major_exclusions = list(all_major_exclusions)

        # Average confidence
        merged.confidence = sum(e.confidence for e in extractions) / len(extractions)

        return merged

    async def extract_program_chunked(self, document_text: str) -> ProgramExtraction:
        """Extract program information using chunked processing for large documents."""
        chunks = self._split_into_chunks(document_text)

        if len(chunks) == 1:
            return await self.extract_program(chunks[0])

        logger.info(f"Processing {len(chunks)} chunks in parallel for program extraction")

        tasks = [self._extract_program_from_chunk(chunk, i) for i, chunk in enumerate(chunks)]
        results = await asyncio.gather(*tasks)

        valid_extractions = []
        valid_indices = []
        for i, result in enumerate(results):
            if result is not None:
                valid_extractions.append(result)
                valid_indices.append(i)

        if not valid_extractions:
            raise ExtractionError("All chunk extractions failed")

        logger.info(f"Merging {len(valid_extractions)} successful program chunk extractions")

        return self._merge_program_extractions(valid_extractions, valid_indices)

    async def _extract_policy_from_chunk(self, chunk: str, chunk_index: int) -> PolicyExtraction | None:
        """Extract policy from a single chunk, handling errors gracefully."""
        try:
            logger.info(f"Extracting from chunk {chunk_index + 1} ({len(chunk)} chars)")
            return await self.extract_policy(chunk)
        except Exception as e:
            logger.warning(f"Chunk {chunk_index + 1} extraction failed: {e}")
            return None

    async def _extract_coi_from_chunk(self, chunk: str, chunk_index: int) -> COIExtraction | None:
        """Extract COI from a single chunk, handling errors gracefully."""
        try:
            logger.info(f"Extracting COI from chunk {chunk_index + 1} ({len(chunk)} chars)")
            return await self.extract_coi(chunk)
        except Exception as e:
            logger.warning(f"Chunk {chunk_index + 1} COI extraction failed: {e}")
            return None

    async def extract_policy_chunked(self, document_text: str) -> PolicyExtraction:
        """Extract policy information using chunked processing for large documents.

        Splits the document into chunks, extracts from each in parallel,
        then merges the results. Prioritizes early chunks for key metadata
        since declaration pages are typically at the beginning.
        """
        chunks = self._split_into_chunks(document_text)

        if len(chunks) == 1:
            # Small document, single pass
            return await self.extract_policy(chunks[0])

        logger.info(f"Processing {len(chunks)} chunks in parallel for policy extraction")

        # Extract from all chunks in parallel
        tasks = [
            self._extract_policy_from_chunk(chunk, i)
            for i, chunk in enumerate(chunks)
        ]
        results = await asyncio.gather(*tasks)

        # Keep track of which chunks succeeded (with their original indices)
        valid_extractions = []
        valid_indices = []
        for i, result in enumerate(results):
            if result is not None:
                valid_extractions.append(result)
                valid_indices.append(i)

        if not valid_extractions:
            raise ExtractionError("All chunk extractions failed")

        logger.info(f"Merging {len(valid_extractions)} successful chunk extractions")

        # Merge all extractions with chunk indices for proper ordering
        return self._merge_policy_extractions(valid_extractions, valid_indices)

    async def extract_coi_chunked(self, document_text: str) -> COIExtraction:
        """Extract COI information using chunked processing for large documents."""
        chunks = self._split_into_chunks(document_text)

        if len(chunks) == 1:
            return await self.extract_coi(chunks[0])

        logger.info(f"Processing {len(chunks)} chunks in parallel for COI extraction")

        tasks = [
            self._extract_coi_from_chunk(chunk, i)
            for i, chunk in enumerate(chunks)
        ]
        results = await asyncio.gather(*tasks)

        valid_extractions = [r for r in results if r is not None]

        if not valid_extractions:
            raise ExtractionError("All chunk extractions failed")

        logger.info(f"Merging {len(valid_extractions)} successful chunk extractions")

        return self._merge_coi_extractions(valid_extractions)

    async def extract(
        self, document_text: str, classification: DocumentClassification
    ) -> ExtractionResult:
        """Extract structured data based on document classification.

        For large documents, uses chunked extraction with parallel processing
        and result merging. Includes validation with warnings/errors.

        Args:
            document_text: OCR-extracted text from the document.
            classification: Document classification result.

        Returns:
            ExtractionResult with type-specific extracted data and validation info.
        """
        result = ExtractionResult(
            classification=classification,
            raw_text=document_text[:10000] if len(document_text) > 10000 else document_text,
        )

        doc_type = classification.document_type
        is_large_doc = len(document_text) > self.MAX_SINGLE_PASS_CHARS

        if is_large_doc:
            logger.info(f"Large document detected ({len(document_text)} chars), using chunked extraction")

        extraction_model = None

        try:
            if doc_type == DocumentType.PROGRAM:
                # Multi-carrier insurance program
                if is_large_doc:
                    result.program = await self.extract_program_chunked(document_text)
                else:
                    result.program = await self.extract_program(document_text)
                result.overall_confidence = result.program.confidence
                extraction_model = result.program

            elif doc_type in (DocumentType.POLICY, DocumentType.DECLARATION, DocumentType.ENDORSEMENT):
                if is_large_doc:
                    result.policy = await self.extract_policy_chunked(document_text)
                else:
                    result.policy = await self.extract_policy(document_text)
                result.overall_confidence = result.policy.confidence
                extraction_model = result.policy

            elif doc_type in (DocumentType.COI, DocumentType.EOP):
                if is_large_doc:
                    result.coi = await self.extract_coi_chunked(document_text)
                else:
                    result.coi = await self.extract_coi(document_text)
                result.overall_confidence = result.coi.confidence
                extraction_model = result.coi

            elif doc_type == DocumentType.INVOICE:
                result.invoice = await self.extract_invoice(document_text)
                result.overall_confidence = result.invoice.confidence
                extraction_model = result.invoice

            elif doc_type == DocumentType.SOV:
                result.sov = await self.extract_sov(document_text)
                result.overall_confidence = result.sov.confidence
                extraction_model = result.sov

            elif doc_type == DocumentType.PROPOSAL:
                result.proposal = await self.extract_proposal(document_text)
                result.overall_confidence = result.proposal.confidence
                extraction_model = result.proposal

            elif doc_type == DocumentType.LOSS_RUN:
                result.loss_run = await self.extract_loss_run(document_text)
                result.overall_confidence = result.loss_run.confidence
                extraction_model = result.loss_run

            else:
                # For unknown types, try policy extraction as default
                logger.warning(f"Unknown document type: {doc_type}, attempting policy extraction")
                if is_large_doc:
                    result.policy = await self.extract_policy_chunked(document_text)
                else:
                    result.policy = await self.extract_policy(document_text)
                result.overall_confidence = result.policy.confidence * 0.5  # Lower confidence
                extraction_model = result.policy

            # Run validation on the extracted data
            if extraction_model is not None:
                try:
                    validation_result = self.validation_service.validate(extraction_model)

                    if validation_result.warnings:
                        logger.info(f"Extraction validation warnings: {validation_result.warnings}")

                    if not validation_result.is_valid:
                        logger.warning(f"Extraction validation errors: {validation_result.errors}")
                        # Store validation info in result (could add to ExtractionResult schema)
                        # For now, just log and optionally reduce confidence
                        if self.config.fail_on_validation_error:
                            raise ExtractionValidationError(
                                f"Validation failed: {validation_result.errors}"
                            )
                        else:
                            # Reduce confidence for validation failures
                            result.overall_confidence *= 0.8
                except Exception as val_error:
                    logger.warning(f"Validation service error: {val_error}")

        except ExtractionError as e:
            logger.error(f"Extraction failed: {e}")
            result.overall_confidence = 0.0

        return result


# Singleton instance
_extraction_service: ExtractionService | None = None


def get_extraction_service() -> ExtractionService:
    """Get or create extraction service instance."""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = ExtractionService()
    return _extraction_service
