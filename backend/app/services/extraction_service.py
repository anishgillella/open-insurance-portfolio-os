"""Document Extraction Service using Gemini via OpenRouter.

This service extracts structured data from insurance documents based on their
document type. It uses type-specific prompts and Pydantic schemas for validation.

For large documents, it uses chunked extraction:
1. Split document into chunks (~50K chars each)
2. Extract from each chunk in parallel
3. Merge extractions, deduplicating and taking highest confidence values
"""

import asyncio
import json
import logging
import re
from datetime import date

import httpx

from app.core.config import settings
from app.schemas.document import (
    COIExtraction,
    COIPolicyReference,
    CoverageExtraction,
    DocumentClassification,
    DocumentType,
    ExtractionResult,
    InvoiceExtraction,
    InvoiceLineItem,
    PolicyExtraction,
    PolicyType,
    ProposalCoverageQuote,
    ProposalExtraction,
    ProposalPropertyQuote,
    SOVExtraction,
    SOVPropertyExtraction,
)

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Base exception for extraction errors."""

    pass


class ExtractionAPIError(ExtractionError):
    """Raised when LLM API returns an error."""

    pass


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
            "deductible_percentage": <number 0-100 or null>,
            "coinsurance_percentage": <number 0-100 or null>,
            "waiting_period_hours": <number or null>,
            "valuation_type": "<RCV|ACV|agreed value|null>",
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


class ExtractionService:
    """Service for extracting structured data from insurance documents."""

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "google/gemini-2.5-flash"

    # Chunking configuration
    MAX_CHARS_PER_CHUNK = 50000  # ~50K chars per chunk
    CHUNK_OVERLAP = 2000  # Overlap between chunks to avoid splitting mid-sentence
    MAX_SINGLE_PASS_CHARS = 60000  # Documents under this size use single-pass extraction

    def __init__(self, api_key: str | None = None):
        """Initialize extraction service.

        Args:
            api_key: OpenRouter API key.
        """
        self.api_key = api_key or settings.openrouter_api_key
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")

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

    async def _call_llm(self, prompt: str) -> dict:
        """Call the LLM and return parsed JSON response."""
        if not self.api_key:
            raise ExtractionError("OpenRouter API key not configured")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.dev",
                    "X-Title": "Open Insurance Platform",
                },
                json={
                    "model": self.MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 8000,
                },
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
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            return json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse extraction response: {e}")
            raise ExtractionError(f"Failed to parse LLM response: {e}")

    async def extract_policy(self, document_text: str) -> PolicyExtraction:
        """Extract policy information from document text."""
        logger.info("Extracting policy information...")

        prompt = POLICY_EXTRACTION_PROMPT.format(document_text=document_text)
        data = await self._call_llm(prompt)

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
                    deductible_percentage=cov_data.get("deductible_percentage"),
                    coinsurance_percentage=cov_data.get("coinsurance_percentage"),
                    waiting_period_hours=cov_data.get("waiting_period_hours"),
                    valuation_type=cov_data.get("valuation_type"),
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
        data = await self._call_llm(prompt)

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
        data = await self._call_llm(prompt)

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
        data = await self._call_llm(prompt)

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
        data = await self._call_llm(prompt)

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
        and result merging.

        Args:
            document_text: OCR-extracted text from the document.
            classification: Document classification result.

        Returns:
            ExtractionResult with type-specific extracted data.
        """
        result = ExtractionResult(
            classification=classification,
            raw_text=document_text[:10000] if len(document_text) > 10000 else document_text,
        )

        doc_type = classification.document_type
        is_large_doc = len(document_text) > self.MAX_SINGLE_PASS_CHARS

        if is_large_doc:
            logger.info(f"Large document detected ({len(document_text)} chars), using chunked extraction")

        try:
            if doc_type in (DocumentType.POLICY, DocumentType.DECLARATION, DocumentType.ENDORSEMENT):
                if is_large_doc:
                    result.policy = await self.extract_policy_chunked(document_text)
                else:
                    result.policy = await self.extract_policy(document_text)
                result.overall_confidence = result.policy.confidence

            elif doc_type in (DocumentType.COI, DocumentType.EOP):
                if is_large_doc:
                    result.coi = await self.extract_coi_chunked(document_text)
                else:
                    result.coi = await self.extract_coi(document_text)
                result.overall_confidence = result.coi.confidence

            elif doc_type == DocumentType.INVOICE:
                result.invoice = await self.extract_invoice(document_text)
                result.overall_confidence = result.invoice.confidence

            elif doc_type == DocumentType.SOV:
                result.sov = await self.extract_sov(document_text)
                result.overall_confidence = result.sov.confidence

            elif doc_type == DocumentType.PROPOSAL:
                result.proposal = await self.extract_proposal(document_text)
                result.overall_confidence = result.proposal.confidence

            else:
                # For unknown types, try policy extraction as default
                logger.warning(f"Unknown document type: {doc_type}, attempting policy extraction")
                if is_large_doc:
                    result.policy = await self.extract_policy_chunked(document_text)
                else:
                    result.policy = await self.extract_policy(document_text)
                result.overall_confidence = result.policy.confidence * 0.5  # Lower confidence

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
