"""Document Classification Service using Gemini via OpenRouter.

This service classifies insurance documents into types (policy, COI, invoice, etc.)
and extracts quick metadata for routing to the appropriate extraction pipeline.

Features:
- Smart document sampling for large documents
- JSON mode for reliable parsing
- Pattern-based pre-classification hints
- Retry logic with exponential backoff
"""

import asyncio
import json
import logging
import re
from datetime import date

import httpx

from app.core.config import settings
from app.schemas.document import DocumentClassification, DocumentType, PolicyType

logger = logging.getLogger(__name__)


# Patterns that strongly indicate document type (used for pre-classification hints)
PROGRAM_INDICATORS = [
    r"CONTRACT\s+ALLOCATION",
    r"LAYER\s+OF\s+PARTICIPATION",
    r"PARTICIPATION\s*%",
    r"Lloyd['']?s\s+Syndicate",
    r"CERTAIN\s+UNDERWRITERS?\s+AT\s+LLOYD['']?S",
    r"multiple\s+insurers?\s+sharing",
    r"AR\s+CA\s+\d{2}\s+\d{2}",  # Contract Allocation form number
    r"peril\s+codes?\s*[:\s]*(NW|Q|AR|EBD|CYB)",
]

COI_INDICATORS = [
    r"CERTIFICATE\s+OF\s+(LIABILITY\s+)?INSURANCE",
    r"ACORD\s+25",
    r"ACORD\s+28",
    r"THIS\s+CERTIFICATE\s+IS\s+ISSUED\s+AS\s+A\s+MATTER\s+OF\s+INFORMATION",
    r"CERTIFICATE\s+HOLDER",
]

EOP_INDICATORS = [
    r"EVIDENCE\s+OF\s+PROPERTY",
    r"EVIDENCE\s+OF\s+INSURANCE",
    r"MORTGAGEE\s+CLAUSE",
    r"LENDER['']?S\s+LOSS\s+PAYABLE",
]

INVOICE_INDICATORS = [
    r"INVOICE\s+(NUMBER|NO|#)",
    r"AMOUNT\s+DUE",
    r"PREMIUM\s+INVOICE",
    r"BILLING\s+STATEMENT",
    r"PAYMENT\s+DUE",
]

SOV_INDICATORS = [
    r"STATEMENT\s+OF\s+VALUES",
    r"SCHEDULE\s+OF\s+(LOCATIONS|VALUES|PROPERTY)",
    r"PROPERTY\s+SCHEDULE",
    r"TIV\s+BY\s+LOCATION",
]

PROPOSAL_INDICATORS = [
    r"PROPOSAL",
    r"QUOTE\s+COMPARISON",
    r"PREMIUM\s+COMPARISON",
    r"EXPIRING\s+.*\s+RENEWAL",
    r"OPTION\s+[123ABC]",
]

LOSS_RUN_INDICATORS = [
    r"LOSS\s+(RUN|HISTORY|REPORT|EXPERIENCE)",
    r"CLAIMS?\s+(HISTORY|REPORT|SUMMARY)",
    r"EXPERIENCE\s+(REPORT|SUMMARY|HISTORY)",
    r"(PAID|INCURRED|RESERVED)\s+(LOSS|CLAIMS?)",
    r"DATE\s+OF\s+LOSS",
    r"CLAIM\s+(NUMBER|#|NO\.?)",
    r"VALUATION\s+DATE",
]


class ClassificationError(Exception):
    """Base exception for classification errors."""

    pass


class ClassificationAPIError(ClassificationError):
    """Raised when LLM API returns an error."""

    pass


CLASSIFICATION_PROMPT = """You are an expert insurance document classifier. Analyze the document text carefully and classify it accurately.

DOCUMENT TEXT:
{document_text}

{pre_classification_hint}

---

Classify this document and extract key metadata. Return a JSON object:

{{
    "document_type": "<one of: program, policy, coi, eop, invoice, sov, loss_run, endorsement, declaration, proposal, unknown>",
    "document_subtype": "<optional specific subtype>",
    "policy_type": "<if applicable: property, general_liability, umbrella, excess, flood, earthquake, terrorism, crime, cyber, epl, dno, auto, workers_comp, boiler_machinery, unknown>",
    "confidence": <float 0.0-1.0>,
    "carrier_name": "<primary insurance company name>",
    "policy_number": "<primary policy number>",
    "effective_date": "<YYYY-MM-DD>",
    "expiration_date": "<YYYY-MM-DD>",
    "insured_name": "<named insured>",
    "classification_reasoning": "<brief explanation of why you chose this type>"
}}

CLASSIFICATION RULES (in order of priority):

1. **"program"** - MUST classify as program if ANY of these are present:
   - Multiple carriers listed with separate policy numbers (e.g., Lloyd's AMR-81904, QBE MSP-41783, Steadfast CPP-xxx)
   - "Contract Allocation" section or form AR CA
   - Participation percentages (e.g., "33.0000%", "9.0000%")
   - Layer structure showing excess amounts (e.g., "$24,808,864 excess of $15,000")
   - Lloyd's syndicates listed (e.g., "510 KLN", "2987 BRT")
   - Peril codes (NW, Q, AR, EBD, CYB)
   - Declaration page showing multiple insurers with individual premiums

   NOTE: A "program" may contain endorsements, but if multiple carriers share risk, it's a PROGRAM not an endorsement.

2. **"coi"** - Certificate of Insurance:
   - ACORD 25 or ACORD 28 forms
   - "CERTIFICATE OF INSURANCE" header
   - Certificate holder section
   - "This certificate is issued as a matter of information"

3. **"eop"** - Evidence of Property:
   - "Evidence of Property Insurance"
   - For mortgage/lender requirements
   - Mortgagee clause prominent

4. **"policy"** - Single-carrier policy:
   - Full policy with ONE carrier only
   - Contains terms, conditions, exclusions
   - NOT a program (no shared risk)

5. **"endorsement"** - Policy amendment:
   - Modifies existing policy
   - Single carrier
   - "This endorsement changes the policy"
   - NOT part of a multi-carrier program

6. **"invoice"** - Billing document:
   - Premium invoice, billing statement
   - Payment due amounts

7. **"sov"** - Statement of Values:
   - Property schedules with values
   - Location listings with TIV

8. **"proposal"** - Quote/comparison:
   - Premium comparisons
   - Expiring vs Renewal columns
   - Multiple options

9. **"declaration"** - Dec page only:
   - Just the declarations page
   - Single carrier summary

10. **"loss_run"** - Claims history

Return ONLY valid JSON."""


class ClassificationService:
    """Service for classifying insurance documents.

    Features:
    - Smart document sampling for large documents
    - Pattern-based pre-classification hints
    - JSON mode for reliable parsing
    - Retry logic with exponential backoff
    """

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "google/gemini-2.5-flash"

    # Configuration
    MAX_RETRIES = 3
    INITIAL_DELAY = 1.0
    BACKOFF_MULTIPLIER = 2.0

    def __init__(self, api_key: str | None = None):
        """Initialize classification service.

        Args:
            api_key: OpenRouter API key. Uses OPENROUTER_API_KEY env var if not provided.
        """
        self.api_key = api_key or settings.openrouter_api_key
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")

    def _detect_patterns(self, text: str) -> dict[str, list[str]]:
        """Detect document type indicators in text.

        Args:
            text: Document text to analyze.

        Returns:
            Dict mapping document types to list of matched patterns.
        """
        detected = {}

        pattern_groups = {
            "program": PROGRAM_INDICATORS,
            "coi": COI_INDICATORS,
            "eop": EOP_INDICATORS,
            "invoice": INVOICE_INDICATORS,
            "sov": SOV_INDICATORS,
            "proposal": PROPOSAL_INDICATORS,
            "loss_run": LOSS_RUN_INDICATORS,
        }

        for doc_type, patterns in pattern_groups.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(pattern)
            if matches:
                detected[doc_type] = matches

        return detected

    def _count_carriers(self, text: str) -> int:
        """Count distinct insurance carriers mentioned in text.

        Args:
            text: Document text to analyze.

        Returns:
            Number of distinct carriers found.
        """
        carrier_patterns = [
            r"Lloyd['']?s",
            r"QBE\s+(Specialty|Insurance)",
            r"Steadfast\s+Insurance",
            r"National\s+Fire\s+(&|and)\s+Marine",
            r"GeoVera",
            r"Transverse",
            r"Old\s+Republic",
            r"Spinnaker",
            r"Zurich",
            r"AIG",
            r"Chubb",
            r"Liberty\s+Mutual",
            r"Travelers",
            r"Hartford",
            r"CNA",
            r"Allianz",
        ]

        carriers_found = set()
        for pattern in carrier_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                carriers_found.add(pattern)

        return len(carriers_found)

    def _extract_first_n_pages(self, text: str, n_pages: int = 10) -> str:
        """Extract the first N pages from document text.

        For classification, the first 10 pages almost always contain all
        the information needed:
        - Declaration page (pages 1-2)
        - Schedule of forms (page 3)
        - Contract Allocation for programs (pages 4-8)
        - Key endorsement references

        Args:
            text: Full document text with page markers (<!-- Page N -->).
            n_pages: Number of pages to extract (default 10).

        Returns:
            Text from the first N pages.
        """
        # Look for page markers from OCR (<!-- Page N -->)
        page_pattern = re.compile(r"<!--\s*Page\s+(\d+)\s*-->", re.IGNORECASE)

        # Find all page markers
        page_matches = list(page_pattern.finditer(text))

        if not page_matches:
            # No page markers found - fall back to character limit
            # Assume ~4000 chars per page average
            char_limit = n_pages * 4000
            return text[:char_limit] if len(text) > char_limit else text

        # Find the position where page N+1 starts (or end of document)
        cutoff_position = len(text)

        for match in page_matches:
            page_num = int(match.group(1))
            if page_num > n_pages:
                cutoff_position = match.start()
                break

        extracted = text[:cutoff_position]

        logger.debug(
            f"Extracted first {n_pages} pages: {len(extracted):,} chars "
            f"(from {len(text):,} total)"
        )

        return extracted

    def _build_pre_classification_hint(self, detected_patterns: dict, carrier_count: int) -> str:
        """Build a hint for the LLM based on detected patterns.

        Args:
            detected_patterns: Dict of detected patterns by type.
            carrier_count: Number of carriers detected.

        Returns:
            Hint string to include in prompt.
        """
        hints = []

        if "program" in detected_patterns or carrier_count >= 3:
            hints.append(
                f"STRONG INDICATOR: This document appears to be a PROGRAM (multi-carrier). "
                f"Found {carrier_count} carriers and these program indicators: {detected_patterns.get('program', [])}"
            )

        if "coi" in detected_patterns:
            hints.append(f"COI indicators found: {detected_patterns['coi']}")

        if "eop" in detected_patterns:
            hints.append(f"EOP indicators found: {detected_patterns['eop']}")

        if "invoice" in detected_patterns:
            hints.append(f"Invoice indicators found: {detected_patterns['invoice']}")

        if "sov" in detected_patterns:
            hints.append(f"SOV indicators found: {detected_patterns['sov']}")

        if "proposal" in detected_patterns:
            hints.append(f"Proposal indicators found: {detected_patterns['proposal']}")

        if "loss_run" in detected_patterns:
            hints.append(f"Loss Run indicators found: {detected_patterns['loss_run']}")

        if hints:
            return "PRE-CLASSIFICATION HINTS (based on pattern detection):\n" + "\n".join(hints)
        return ""

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return None

    def _parse_document_type(self, type_str: str) -> DocumentType:
        """Parse document type string to enum."""
        type_map = {
            "program": DocumentType.PROGRAM,
            "policy": DocumentType.POLICY,
            "coi": DocumentType.COI,
            "eop": DocumentType.EOP,
            "invoice": DocumentType.INVOICE,
            "sov": DocumentType.SOV,
            "loss_run": DocumentType.LOSS_RUN,
            "endorsement": DocumentType.ENDORSEMENT,
            "declaration": DocumentType.DECLARATION,
            "proposal": DocumentType.PROPOSAL,
            "unknown": DocumentType.UNKNOWN,
        }
        return type_map.get(type_str.lower(), DocumentType.UNKNOWN)

    def _parse_policy_type(self, type_str: str | None) -> PolicyType | None:
        """Parse policy type string to enum."""
        if not type_str:
            return None
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
            "unknown": PolicyType.UNKNOWN,
        }
        return type_map.get(type_str.lower(), PolicyType.UNKNOWN)

    async def classify(self, document_text: str) -> DocumentClassification:
        """Classify a document based on its text content.

        Uses smart sampling for large documents, pattern detection for hints,
        and JSON mode for reliable parsing.

        Args:
            document_text: The OCR-extracted text from the document.

        Returns:
            DocumentClassification with type, subtype, and metadata.

        Raises:
            ClassificationAPIError: If the LLM API call fails after retries.
        """
        if not self.api_key:
            raise ClassificationError("OpenRouter API key not configured")

        logger.info(f"Classifying document ({len(document_text)} chars)...")

        # Step 1: Detect patterns in full document (fast regex scan)
        detected_patterns = self._detect_patterns(document_text)
        carrier_count = self._count_carriers(document_text)

        logger.info(
            f"Pattern detection: {len(detected_patterns)} types detected, "
            f"{carrier_count} carriers found"
        )

        # Step 2: Extract first 10 pages for LLM (contains all classification info)
        sampled_text = self._extract_first_n_pages(document_text, n_pages=10)

        # Step 3: Build pre-classification hint
        pre_hint = self._build_pre_classification_hint(detected_patterns, carrier_count)

        # Step 4: Build prompt
        prompt = CLASSIFICATION_PROMPT.format(
            document_text=sampled_text,
            pre_classification_hint=pre_hint
        )

        # Step 5: Call LLM with retry
        data = await self._call_llm_with_retry(prompt)

        if data is None:
            # All retries failed, use pattern-based fallback
            logger.warning("LLM classification failed, using pattern-based fallback")
            return self._pattern_based_fallback(detected_patterns, carrier_count)

        # Step 6: Build classification result
        classification = DocumentClassification(
            document_type=self._parse_document_type(data.get("document_type", "unknown")),
            document_subtype=data.get("document_subtype"),
            policy_type=self._parse_policy_type(data.get("policy_type")),
            confidence=float(data.get("confidence", 0.5)),
            carrier_name=data.get("carrier_name"),
            policy_number=data.get("policy_number"),
            effective_date=self._parse_date(data.get("effective_date")),
            expiration_date=self._parse_date(data.get("expiration_date")),
            insured_name=data.get("insured_name"),
        )

        # Step 7: Override if pattern detection strongly disagrees
        classification = self._validate_and_override(
            classification, detected_patterns, carrier_count
        )

        logger.info(
            f"Classification complete: {classification.document_type.value} "
            f"(confidence: {classification.confidence:.2f})"
        )
        if data.get("classification_reasoning"):
            logger.debug(f"Reasoning: {data.get('classification_reasoning')}")

        return classification

    async def _call_llm_with_retry(self, prompt: str) -> dict | None:
        """Call LLM with retry logic and JSON mode.

        Args:
            prompt: The classification prompt.

        Returns:
            Parsed JSON response or None if all retries fail.
        """
        delay = self.INITIAL_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
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
                            "max_tokens": 1500,
                            "response_format": {"type": "json_object"},  # JSON mode
                        },
                    )

                    if response.status_code != 200:
                        raise ClassificationAPIError(
                            f"API error: {response.status_code} - {response.text}"
                        )

                    result = response.json()
                    content = result["choices"][0]["message"]["content"]

                    # Clean up if needed (shouldn't be necessary with JSON mode)
                    content = content.strip()
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]

                    return json.loads(content)

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"Classification attempt {attempt + 1} parse error: {e}")
            except Exception as e:
                logger.warning(f"Classification attempt {attempt + 1} failed: {e}")

            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(delay)
                delay *= self.BACKOFF_MULTIPLIER

        return None

    def _pattern_based_fallback(
        self, detected_patterns: dict, carrier_count: int
    ) -> DocumentClassification:
        """Fallback classification based on detected patterns.

        Used when LLM classification fails.

        Args:
            detected_patterns: Dict of detected patterns.
            carrier_count: Number of carriers detected.

        Returns:
            Best-guess classification based on patterns.
        """
        # Priority order for pattern-based classification
        if "program" in detected_patterns or carrier_count >= 3:
            return DocumentClassification(
                document_type=DocumentType.PROGRAM,
                policy_type=PolicyType.PROPERTY,
                confidence=0.7,
            )

        if "coi" in detected_patterns:
            return DocumentClassification(
                document_type=DocumentType.COI,
                confidence=0.7,
            )

        if "eop" in detected_patterns:
            return DocumentClassification(
                document_type=DocumentType.EOP,
                confidence=0.7,
            )

        if "invoice" in detected_patterns:
            return DocumentClassification(
                document_type=DocumentType.INVOICE,
                confidence=0.7,
            )

        if "sov" in detected_patterns:
            return DocumentClassification(
                document_type=DocumentType.SOV,
                confidence=0.7,
            )

        if "proposal" in detected_patterns:
            return DocumentClassification(
                document_type=DocumentType.PROPOSAL,
                confidence=0.7,
            )

        if "loss_run" in detected_patterns:
            return DocumentClassification(
                document_type=DocumentType.LOSS_RUN,
                confidence=0.7,
            )

        return DocumentClassification(
            document_type=DocumentType.UNKNOWN,
            confidence=0.3,
        )

    def _validate_and_override(
        self,
        classification: DocumentClassification,
        detected_patterns: dict,
        carrier_count: int,
    ) -> DocumentClassification:
        """Validate LLM classification and override if patterns strongly disagree.

        This catches cases where the LLM misclassifies a program as an endorsement
        or policy.

        Args:
            classification: LLM classification result.
            detected_patterns: Detected patterns in document.
            carrier_count: Number of carriers detected.

        Returns:
            Validated (potentially overridden) classification.
        """
        # Strong program indicators should override endorsement/policy classification
        program_indicators = detected_patterns.get("program", [])
        is_likely_program = (
            len(program_indicators) >= 2 or
            carrier_count >= 4 or
            (len(program_indicators) >= 1 and carrier_count >= 3)
        )

        if is_likely_program and classification.document_type in (
            DocumentType.ENDORSEMENT,
            DocumentType.POLICY,
            DocumentType.DECLARATION,
        ):
            logger.info(
                f"Overriding {classification.document_type.value} -> program "
                f"(found {len(program_indicators)} program indicators, {carrier_count} carriers)"
            )
            classification.document_type = DocumentType.PROGRAM
            # Adjust confidence based on pattern strength
            classification.confidence = min(0.95, classification.confidence + 0.1)

        return classification


# Singleton instance
_classification_service: ClassificationService | None = None


def get_classification_service() -> ClassificationService:
    """Get or create classification service instance."""
    global _classification_service
    if _classification_service is None:
        _classification_service = ClassificationService()
    return _classification_service
