"""Document Classification Service using Gemini via OpenRouter.

This service classifies insurance documents into types (policy, COI, invoice, etc.)
and extracts quick metadata for routing to the appropriate extraction pipeline.
"""

import json
import logging
from datetime import date

import httpx

from app.core.config import settings
from app.schemas.document import DocumentClassification, DocumentType, PolicyType

logger = logging.getLogger(__name__)


class ClassificationError(Exception):
    """Base exception for classification errors."""

    pass


class ClassificationAPIError(ClassificationError):
    """Raised when LLM API returns an error."""

    pass


CLASSIFICATION_PROMPT = """You are an insurance document classifier. Analyze the following document text and classify it.

DOCUMENT TEXT:
{document_text}

---

Classify this document and extract key metadata. Respond with a JSON object containing:

{{
    "document_type": "<one of: program, policy, coi, eop, invoice, sov, loss_run, endorsement, declaration, proposal, unknown>",
    "document_subtype": "<optional specific subtype, e.g., 'ACORD 25' for COI, 'renewal' for policy, 'comparison' for proposal>",
    "policy_type": "<if document_type is policy/endorsement/program, one of: property, general_liability, umbrella, excess, flood, earthquake, terrorism, crime, cyber, epl, dno, auto, workers_comp, boiler_machinery, unknown>",
    "confidence": <float between 0.0 and 1.0>,
    "carrier_name": "<insurance company name if found>",
    "policy_number": "<policy number if found>",
    "effective_date": "<YYYY-MM-DD format if found>",
    "expiration_date": "<YYYY-MM-DD format if found>",
    "insured_name": "<named insured if found>"
}}

CLASSIFICATION GUIDE:
- "program": Multi-carrier insurance program with CONTRACT ALLOCATION table showing multiple insurers (Lloyd's, QBE, Steadfast, etc.) sharing risk with participation percentages. Look for: Contract Allocation Endorsement, multiple policy numbers for different carriers, peril codes (NW, Q, AR), layer structures, Lloyd's syndicates. This is different from a simple policy - it's a shared/layered program.
- "policy": Full insurance policy document with declarations, terms, conditions (single carrier)
- "coi": Certificate of Insurance (ACORD 25, ACORD 28, etc.)
- "eop": Evidence of Property Insurance (for lenders)
- "invoice": Premium invoice or billing statement
- "sov": Statement of Values / Schedule of Locations
- "loss_run": Claims history / loss run report
- "endorsement": Policy endorsement/amendment
- "declaration": Declarations page only
- "proposal": Insurance proposal, quote, or premium comparison document (often shows "Expiring" vs "Renewal" columns, multiple carriers, or premium comparisons)
- "unknown": Cannot determine document type

IMPORTANT: If you see multiple carriers with policy numbers listed together, a "Contract Allocation" table, participation percentages, or Lloyd's syndicates, classify as "program" NOT "policy" or "endorsement".

Return ONLY the JSON object, no additional text."""


class ClassificationService:
    """Service for classifying insurance documents."""

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "google/gemini-2.5-flash"

    def __init__(self, api_key: str | None = None):
        """Initialize classification service.

        Args:
            api_key: OpenRouter API key. Uses OPENROUTER_API_KEY env var if not provided.
        """
        self.api_key = api_key or settings.openrouter_api_key
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")

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

        Args:
            document_text: The OCR-extracted text from the document.

        Returns:
            DocumentClassification with type, subtype, and metadata.

        Raises:
            ClassificationAPIError: If the LLM API call fails.
        """
        if not self.api_key:
            raise ClassificationError("OpenRouter API key not configured")

        # Truncate very long documents to first ~50k characters for classification
        # (classification doesn't need the full document)
        max_chars = 50000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "\n\n[Document truncated for classification...]"

        prompt = CLASSIFICATION_PROMPT.format(document_text=document_text)

        logger.info("Classifying document...")

        async with httpx.AsyncClient(timeout=60.0) as client:
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
                    "temperature": 0.1,  # Low temperature for consistent classification
                    "max_tokens": 1000,
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenRouter API error: {response.status_code} - {error_detail}")
                raise ClassificationAPIError(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )

            result = response.json()

        # Extract content from response
        try:
            content = result["choices"][0]["message"]["content"]
            # Clean up markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse classification response: {e}")
            logger.debug(f"Raw response: {result}")
            # Return unknown classification on parse failure
            return DocumentClassification(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
            )

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

        logger.info(
            f"Classification complete: {classification.document_type.value} "
            f"(confidence: {classification.confidence:.2f})"
        )

        return classification


# Singleton instance
_classification_service: ClassificationService | None = None


def get_classification_service() -> ClassificationService:
    """Get or create classification service instance."""
    global _classification_service
    if _classification_service is None:
        _classification_service = ClassificationService()
    return _classification_service
