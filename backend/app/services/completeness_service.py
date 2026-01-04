"""Document Completeness Service with LLM Enhancement.

Tracks what insurance documents are present vs expected for each property.
Uses LLM to provide impact analysis and recommendations for missing documents.
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.document import Document
from app.models.policy import Policy
from app.models.property import Property
from app.models.insurance_program import InsuranceProgram

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"


class CompletenessError(Exception):
    """Base exception for completeness service errors."""
    pass


@dataclass
class DocumentStatus:
    """Status of a single document type."""
    type: str
    label: str
    status: str  # present, missing, not_applicable
    document_id: str | None
    filename: str | None
    importance: str | None
    uploaded_at: datetime | None = None


@dataclass
class MissingDocumentImpact:
    """LLM-generated impact analysis for a missing document."""
    document: str
    impact: str
    priority: str  # high, medium, low
    reason: str


@dataclass
class CompletenessResult:
    """Result of document completeness calculation."""
    property_id: str
    property_name: str
    percentage: float
    grade: str
    required_present: int
    required_total: int
    optional_present: int
    optional_total: int
    required_documents: list[DocumentStatus]
    optional_documents: list[DocumentStatus]
    # LLM-enhanced fields
    missing_document_impacts: list[MissingDocumentImpact] | None = None
    overall_risk_summary: str | None = None
    recommended_actions: list[str] | None = None
    llm_analyzed: bool = False


@dataclass
class PortfolioCompletenessResult:
    """Portfolio-wide completeness summary."""
    average_completeness: float
    fully_complete_count: int
    missing_required_count: int
    total_properties: int
    distribution: dict[str, int]
    most_common_missing: list[dict]
    properties: list[dict]


# Document type definitions
REQUIRED_DOCUMENTS = [
    ("property_policy", "Property Policy", "Required for complete coverage verification"),
    ("gl_policy", "General Liability Policy", "Required for complete coverage verification"),
    ("coi", "Certificate of Insurance", "Required for lender and vendor verification"),
]

OPTIONAL_DOCUMENTS = [
    ("umbrella_policy", "Umbrella Policy", "Provides additional liability protection"),
    ("sov", "Statement of Values", "Ensures accurate property valuations"),
    ("loss_run", "Loss Runs", "Needed for renewals and risk assessment"),
    ("invoice", "Premium Invoice", "Verifies premium amounts and payment status"),
    ("proposal", "Insurance Proposal", "Useful for comparing coverage options"),
    ("endorsement", "Endorsements", "Documents coverage modifications"),
]


# LLM Prompt for completeness analysis
COMPLETENESS_ANALYSIS_PROMPT = """You are an expert commercial real estate insurance analyst. Analyze the document completeness status for this property and provide insights.

PROPERTY INFORMATION:
{property_context}

DOCUMENTS PRESENT:
{present_documents}

DOCUMENTS MISSING:
{missing_documents}

EXISTING POLICIES:
{policies_context}

Analyze the missing documents and provide:
1. Impact of each missing document on the property's insurance posture
2. Priority ranking for which documents to obtain first
3. Overall risk assessment due to documentation gaps
4. Recommended actions

Respond in JSON format:
{{
    "missing_document_impacts": [
        {{
            "document": "<document type>",
            "impact": "<specific impact of this missing document>",
            "priority": "high|medium|low",
            "reason": "<why this priority level>"
        }}
    ],
    "overall_risk_summary": "<2-3 sentence summary of documentation risk>",
    "recommended_actions": ["action 1", "action 2", ...]
}}"""


class CompletenessService:
    """Service for calculating document completeness with LLM enhancement."""

    def __init__(self, session: AsyncSession, api_key: str | None = None):
        """Initialize completeness service.

        Args:
            session: Database session.
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.session = session
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL

    async def get_completeness(
        self,
        property_id: str,
        include_llm_analysis: bool = True,
    ) -> CompletenessResult:
        """Calculate document completeness for a property.

        Args:
            property_id: Property ID.
            include_llm_analysis: Whether to include LLM impact analysis.

        Returns:
            CompletenessResult with completeness data and optional LLM insights.
        """
        # Load property with documents
        prop = await self._load_property_with_documents(property_id)
        if not prop:
            raise CompletenessError(f"Property {property_id} not found")

        # Get documents and map to types
        documents = prop.documents or []
        doc_map = self._map_documents_to_types(documents)

        # Build required documents status
        required_docs: list[DocumentStatus] = []
        required_present = 0
        for doc_type, label, importance in REQUIRED_DOCUMENTS:
            doc = doc_map.get(doc_type)
            if doc:
                required_docs.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="present",
                    document_id=doc.id,
                    filename=doc.file_name,
                    importance=None,
                    uploaded_at=doc.created_at,
                ))
                required_present += 1
            else:
                required_docs.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="missing",
                    document_id=None,
                    filename=None,
                    importance=importance,
                ))

        # Build optional documents status
        optional_docs: list[DocumentStatus] = []
        optional_present = 0
        for doc_type, label, importance in OPTIONAL_DOCUMENTS:
            doc = doc_map.get(doc_type)
            if doc:
                optional_docs.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="present",
                    document_id=doc.id,
                    filename=doc.file_name,
                    importance=None,
                    uploaded_at=doc.created_at,
                ))
                optional_present += 1
            else:
                optional_docs.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="missing",
                    document_id=None,
                    filename=None,
                    importance=importance,
                ))

        # Calculate percentage
        required_total = len(REQUIRED_DOCUMENTS)
        optional_total = len(OPTIONAL_DOCUMENTS)

        required_score = (required_present / required_total * 100) if required_total > 0 else 100
        optional_score = (optional_present / optional_total * 100) if optional_total > 0 else 100

        percentage = (required_score * 0.6) + (optional_score * 0.4)
        grade = self._calculate_grade(percentage)

        result = CompletenessResult(
            property_id=property_id,
            property_name=prop.name,
            percentage=round(percentage, 1),
            grade=grade,
            required_present=required_present,
            required_total=required_total,
            optional_present=optional_present,
            optional_total=optional_total,
            required_documents=required_docs,
            optional_documents=optional_docs,
        )

        # Add LLM analysis if requested and there are missing documents
        missing_docs = [d for d in required_docs + optional_docs if d.status == "missing"]
        if include_llm_analysis and missing_docs and self.api_key:
            try:
                llm_result = await self._get_llm_analysis(prop, required_docs, optional_docs)
                result.missing_document_impacts = llm_result.get("missing_document_impacts", [])
                result.overall_risk_summary = llm_result.get("overall_risk_summary")
                result.recommended_actions = llm_result.get("recommended_actions", [])
                result.llm_analyzed = True
            except Exception as e:
                logger.warning(f"LLM analysis failed for property {property_id}: {e}")

        return result

    async def get_portfolio_completeness(
        self,
        organization_id: str | None = None,
    ) -> PortfolioCompletenessResult:
        """Get completeness summary across all properties.

        Args:
            organization_id: Optional organization filter.

        Returns:
            PortfolioCompletenessResult with aggregated data.
        """
        # Get all properties
        stmt = (
            select(Property)
            .options(selectinload(Property.documents))
            .where(Property.deleted_at.is_(None))
        )
        if organization_id:
            stmt = stmt.where(Property.organization_id == organization_id)

        result = await self.session.execute(stmt)
        properties = list(result.scalars().all())

        if not properties:
            return PortfolioCompletenessResult(
                average_completeness=0.0,
                fully_complete_count=0,
                missing_required_count=0,
                total_properties=0,
                distribution={"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
                most_common_missing=[],
                properties=[],
            )

        # Calculate completeness for each property
        property_results = []
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        missing_counts: dict[str, int] = {}
        fully_complete = 0
        missing_required = 0
        total_percentage = 0.0

        for prop in properties:
            # Quick calculation without LLM
            completeness = await self.get_completeness(prop.id, include_llm_analysis=False)
            total_percentage += completeness.percentage
            grade_counts[completeness.grade] = grade_counts.get(completeness.grade, 0) + 1

            if completeness.percentage >= 100:
                fully_complete += 1
            if completeness.required_present < completeness.required_total:
                missing_required += 1

            # Track missing documents
            for doc in completeness.required_documents + completeness.optional_documents:
                if doc.status == "missing":
                    missing_counts[doc.type] = missing_counts.get(doc.type, 0) + 1

            property_results.append({
                "id": prop.id,
                "name": prop.name,
                "completeness": completeness.percentage,
                "grade": completeness.grade,
                "missing_required": completeness.required_total - completeness.required_present,
                "missing_optional": completeness.optional_total - completeness.optional_present,
            })

        # Build most common missing list
        most_common_missing = sorted(
            [
                {
                    "type": doc_type,
                    "label": self._get_document_label(doc_type),
                    "missing_count": count,
                    "percentage_missing": round(count / len(properties) * 100, 1),
                }
                for doc_type, count in missing_counts.items()
            ],
            key=lambda x: x["missing_count"],
            reverse=True,
        )[:5]

        return PortfolioCompletenessResult(
            average_completeness=round(total_percentage / len(properties), 1),
            fully_complete_count=fully_complete,
            missing_required_count=missing_required,
            total_properties=len(properties),
            distribution=grade_counts,
            most_common_missing=most_common_missing,
            properties=property_results,
        )

    async def _load_property_with_documents(self, property_id: str) -> Property | None:
        """Load property with documents and policies."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.documents),
                selectinload(Property.insurance_programs).selectinload(
                    InsuranceProgram.policies
                ),
            )
            .where(
                Property.id == property_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _map_documents_to_types(self, documents: list[Document]) -> dict[str, Document]:
        """Map documents to expected document types."""
        doc_map: dict[str, Document] = {}

        for doc in documents:
            if doc.deleted_at is not None:
                continue

            doc_type = doc.document_type
            doc_subtype = doc.document_subtype

            # Map based on document type and subtype
            if doc_type == "policy":
                if doc_subtype == "property":
                    doc_map["property_policy"] = doc
                elif doc_subtype in ("general_liability", "gl"):
                    doc_map["gl_policy"] = doc
                elif doc_subtype in ("umbrella", "excess"):
                    doc_map["umbrella_policy"] = doc
            elif doc_type == "coi":
                doc_map["coi"] = doc
            elif doc_type == "sov":
                doc_map["sov"] = doc
            elif doc_type == "loss_run":
                doc_map["loss_run"] = doc
            elif doc_type == "invoice":
                doc_map["invoice"] = doc
            elif doc_type == "proposal":
                doc_map["proposal"] = doc
            elif doc_type == "endorsement":
                doc_map["endorsement"] = doc

        return doc_map

    def _calculate_grade(self, percentage: float) -> str:
        """Calculate letter grade from percentage."""
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"

    def _get_document_label(self, doc_type: str) -> str:
        """Get human-readable label for document type."""
        all_docs = REQUIRED_DOCUMENTS + OPTIONAL_DOCUMENTS
        for dtype, label, _ in all_docs:
            if dtype == doc_type:
                return label
        return doc_type

    async def _get_llm_analysis(
        self,
        prop: Property,
        required_docs: list[DocumentStatus],
        optional_docs: list[DocumentStatus],
    ) -> dict[str, Any]:
        """Get LLM analysis for missing documents."""
        # Build property context
        property_context = self._build_property_context(prop)

        # Build document lists
        present_docs = [
            f"- {d.label}: {d.filename}"
            for d in required_docs + optional_docs
            if d.status == "present"
        ]
        missing_docs = [
            f"- {d.label} ({d.importance})"
            for d in required_docs + optional_docs
            if d.status == "missing"
        ]

        # Build policies context
        policies_context = self._build_policies_context(prop)

        # Format prompt
        prompt = COMPLETENESS_ANALYSIS_PROMPT.format(
            property_context=property_context,
            present_documents="\n".join(present_docs) if present_docs else "None",
            missing_documents="\n".join(missing_docs) if missing_docs else "None",
            policies_context=policies_context,
        )

        # Call LLM
        response = await self._call_llm(prompt)

        # Parse response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = self._extract_json_from_response(response)

        # Convert to proper types
        if "missing_document_impacts" in result:
            result["missing_document_impacts"] = [
                MissingDocumentImpact(
                    document=item.get("document", ""),
                    impact=item.get("impact", ""),
                    priority=item.get("priority", "medium"),
                    reason=item.get("reason", ""),
                )
                for item in result.get("missing_document_impacts", [])
            ]

        return result

    def _build_property_context(self, prop: Property) -> str:
        """Build property context string for LLM."""
        lines = [
            f"Name: {prop.name}",
            f"Type: {prop.property_type or 'N/A'}",
            f"Address: {prop.address}, {prop.city}, {prop.state}",
            f"Units: {prop.units or 'N/A'}",
            f"Square Feet: {prop.sq_ft or 'N/A'}",
            f"Flood Zone: {prop.flood_zone or 'N/A'}",
        ]
        return "\n".join(lines)

    def _build_policies_context(self, prop: Property) -> str:
        """Build policies context string for LLM."""
        lines = []
        for program in prop.insurance_programs:
            if program.status == "active":
                for policy in program.policies:
                    lines.append(
                        f"- {policy.policy_type}: {policy.carrier_name or 'Unknown carrier'}"
                    )
        return "\n".join(lines) if lines else "No active policies found"

    async def _call_llm(self, user_message: str) -> str:
        """Call the LLM API."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Completeness Analysis",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.3,
                },
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                raise CompletenessError(f"LLM API error: {response.status_code}")

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                raise CompletenessError("No response from LLM")

            return choices[0].get("message", {}).get("content", "")

    def _extract_json_from_response(self, response: str) -> dict:
        """Extract JSON from a response that may contain extra text."""
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Return default structure
        return {
            "missing_document_impacts": [],
            "overall_risk_summary": "Unable to analyze document completeness.",
            "recommended_actions": [],
        }


def get_completeness_service(session: AsyncSession) -> CompletenessService:
    """Factory function to create CompletenessService.

    Args:
        session: Database session.

    Returns:
        CompletenessService instance.
    """
    return CompletenessService(session)
