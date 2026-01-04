"""Renewal Readiness Service - Document readiness tracking for renewals.

This service provides:
1. Document readiness assessment for renewal
2. LLM-powered document content verification
3. Data extraction from documents for renewal preparation
4. Readiness scoring and grading

Uses Gemini 2.5 Flash via OpenRouter for LLM verification.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.document import Document
from app.models.insurance_program import InsuranceProgram
from app.models.policy import Policy
from app.models.property import Property
from app.models.renewal_readiness import RenewalReadiness

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"

# Document requirements for renewal
REQUIRED_DOCUMENTS = [
    {"type": "policy", "label": "Current Policy", "max_age_days": 365},
    {"type": "loss_run", "label": "Loss Runs (3-year)", "max_age_days": 90},
    {"type": "sov", "label": "Statement of Values", "max_age_days": 365},
]

RECOMMENDED_DOCUMENTS = [
    {"type": "coi", "label": "Certificate of Insurance", "max_age_days": 365},
    {"type": "proposal", "label": "Insurance Proposal", "max_age_days": 365},
    {"type": "invoice", "label": "Premium Invoice", "max_age_days": 365},
    {"type": "endorsement", "label": "Policy Endorsements", "max_age_days": 365},
]

# Document staleness thresholds (days)
STALENESS_THRESHOLDS = {
    "policy": 365,
    "loss_run": 90,
    "sov": 365,
    "coi": 365,
    "proposal": 365,
    "invoice": 365,
    "endorsement": 365,
    "valuation": 730,  # 2 years
}


class RenewalReadinessError(Exception):
    """Base exception for renewal readiness errors."""
    pass


class RenewalReadinessAPIError(RenewalReadinessError):
    """Raised when LLM API returns an error."""
    pass


@dataclass
class DocumentStatus:
    """Status of a single document."""

    type: str
    label: str
    status: str  # found, missing, stale, not_applicable
    document_id: str | None = None
    filename: str | None = None
    age_days: int | None = None
    verified: bool = False
    extracted_data: dict | None = None
    issues: list[str] = field(default_factory=list)


@dataclass
class ReadinessIssue:
    """Issue identified in readiness assessment."""

    severity: str  # critical, warning, info
    issue: str
    impact: str


@dataclass
class ReadinessRecommendation:
    """Recommendation for improving readiness."""

    priority: str  # high, medium, low
    action: str
    deadline: str | None = None


@dataclass
class TimelineMilestone:
    """Milestone in renewal timeline."""

    days_before_renewal: int
    action: str
    status: str  # completed, missed, upcoming


@dataclass
class ReadinessResult:
    """Result of readiness assessment."""

    property_id: str
    property_name: str
    target_renewal_date: datetime
    days_until_renewal: int

    # Scores
    readiness_score: int
    readiness_grade: str

    # Document status
    required_documents: list[DocumentStatus]
    recommended_documents: list[DocumentStatus]

    # LLM verification
    verification_summary: str | None
    data_consistency_issues: list[str]

    # Issues and recommendations
    issues: list[ReadinessIssue]
    recommendations: list[ReadinessRecommendation]

    # Timeline
    milestones: list[TimelineMilestone]

    # Metadata
    assessment_date: datetime
    status: str
    model_used: str | None
    latency_ms: int


# LLM Prompts
VERIFICATION_SYSTEM_PROMPT = """You are an insurance document verification specialist. Analyze the provided document information and verify its contents.

For each document, confirm:
1. The document type matches what it claims to be
2. Key data points are present and valid
3. Any inconsistencies with other documents

Respond in JSON format:
{
    "verified_documents": [
        {
            "document_id": "...",
            "type": "...",
            "verified": true/false,
            "extracted_data": {
                // Key data points from document
            },
            "issues": ["Any issues found"]
        }
    ],
    "data_consistency_issues": ["Cross-document inconsistencies"],
    "verification_summary": "Overall assessment of document quality"
}"""

VERIFICATION_USER_PROMPT = """Verify these documents for renewal readiness:

PROPERTY: {property_name}
RENEWAL DATE: {renewal_date}

DOCUMENTS:
{documents_context}

Verify each document and check for cross-document consistency (e.g., matching entity names, policy numbers, dates)."""


class RenewalReadinessService:
    """Service for assessing renewal readiness."""

    def __init__(self, session: AsyncSession, api_key: str | None = None):
        """Initialize renewal readiness service.

        Args:
            session: Database session.
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.session = session
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL

        if not self.api_key:
            logger.warning("OpenRouter API key not configured for renewal readiness")

    async def assess_readiness(
        self,
        property_id: str,
        force: bool = False,
        verify_contents: bool = True,
    ) -> ReadinessResult:
        """Assess renewal readiness for a property.

        Args:
            property_id: Property ID.
            force: Force reassessment.
            verify_contents: Use LLM to verify document contents.

        Returns:
            ReadinessResult with assessment.
        """
        # Load property with documents and programs
        prop = await self._load_property_with_context(property_id)
        if not prop:
            raise RenewalReadinessError(f"Property {property_id} not found")

        # Get renewal date from active program
        renewal_date = self._get_renewal_date(prop)
        if not renewal_date:
            raise RenewalReadinessError(
                f"No active insurance program found for property {property_id}"
            )

        days_until = (renewal_date.date() - date.today()).days

        # Check for recent assessment
        if not force:
            existing = await self._get_recent_assessment(property_id)
            if existing and existing.assessment_date > datetime.now(timezone.utc) - timedelta(days=1):
                logger.info(f"Using existing readiness assessment for property {property_id}")
                return self._assessment_model_to_result(existing, prop)

        # Assess required documents
        required_docs = await self._assess_documents(
            prop, REQUIRED_DOCUMENTS
        )

        # Assess recommended documents
        recommended_docs = await self._assess_documents(
            prop, RECOMMENDED_DOCUMENTS
        )

        # Calculate readiness score
        readiness_score, readiness_grade = self._calculate_readiness_score(
            required_docs, recommended_docs
        )

        # LLM verification if enabled
        verification_summary = None
        data_consistency_issues = []
        latency_ms = 0

        if verify_contents and self.api_key:
            all_docs = [d for d in required_docs + recommended_docs if d.document_id]
            if all_docs:
                start_time = time.time()
                verification = await self._verify_documents_with_llm(
                    prop, renewal_date, all_docs
                )
                latency_ms = int((time.time() - start_time) * 1000)

                verification_summary = verification.get("verification_summary")
                data_consistency_issues = verification.get("data_consistency_issues", [])

                # Update document status with verification results
                self._apply_verification_results(
                    required_docs + recommended_docs,
                    verification.get("verified_documents", []),
                )

        # Build issues and recommendations
        issues = self._build_issues(required_docs, recommended_docs, days_until)
        recommendations = self._build_recommendations(
            required_docs, recommended_docs, days_until
        )

        # Build milestones
        milestones = self._build_milestones(days_until)

        result = ReadinessResult(
            property_id=property_id,
            property_name=prop.name,
            target_renewal_date=renewal_date,
            days_until_renewal=days_until,
            readiness_score=readiness_score,
            readiness_grade=readiness_grade,
            required_documents=required_docs,
            recommended_documents=recommended_docs,
            verification_summary=verification_summary,
            data_consistency_issues=data_consistency_issues,
            issues=issues,
            recommendations=recommendations,
            milestones=milestones,
            assessment_date=datetime.now(timezone.utc),
            status="current",
            model_used=self.model if verify_contents else None,
            latency_ms=latency_ms,
        )

        # Save to database
        await self._save_assessment(result)

        return result

    async def get_portfolio_readiness(
        self,
        organization_id: str,
    ) -> dict:
        """Get readiness summary for entire portfolio.

        Args:
            organization_id: Organization ID.

        Returns:
            Portfolio readiness summary.
        """
        stmt = (
            select(Property)
            .options(
                selectinload(Property.insurance_programs),
                selectinload(Property.documents),
                selectinload(Property.renewal_readiness),
            )
            .where(
                Property.organization_id == organization_id,
                Property.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        properties = list(result.scalars().all())

        property_summaries = []
        total_score = 0
        grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        common_missing = {}

        for prop in properties:
            # Get latest readiness assessment
            latest = self._get_latest_readiness(prop.renewal_readiness)

            if latest:
                score = latest.readiness_score
                grade = latest.readiness_grade
                days = latest.target_renewal_date
                days_until = (days.date() - date.today()).days if days else 0

                # Count missing documents
                doc_status = latest.document_status or {}
                missing_required = len([
                    d for d in doc_status.get("required", [])
                    if d.get("status") == "missing"
                ])
                missing_recommended = len([
                    d for d in doc_status.get("recommended", [])
                    if d.get("status") == "missing"
                ])

                for doc in doc_status.get("required", []):
                    if doc.get("status") == "missing":
                        doc_type = doc.get("type", "unknown")
                        common_missing[doc_type] = common_missing.get(doc_type, 0) + 1
            else:
                score = 0
                grade = "F"
                days_until = 0
                missing_required = len(REQUIRED_DOCUMENTS)
                missing_recommended = len(RECOMMENDED_DOCUMENTS)

            property_summaries.append({
                "id": prop.id,
                "name": prop.name,
                "readiness_score": score,
                "readiness_grade": grade,
                "days_until_renewal": days_until,
                "missing_required": missing_required,
                "missing_recommended": missing_recommended,
            })

            total_score += score
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

        avg_score = total_score // len(properties) if properties else 0
        avg_grade = self._score_to_grade(avg_score)

        # Sort common missing by frequency
        common_missing_sorted = sorted(
            common_missing.keys(),
            key=lambda k: common_missing[k],
            reverse=True,
        )[:5]

        return {
            "average_readiness": avg_score,
            "average_grade": avg_grade,
            "property_count": len(properties),
            "distribution": grade_distribution,
            "common_missing_docs": common_missing_sorted,
            "properties": property_summaries,
        }

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    async def _load_property_with_context(self, property_id: str) -> Property | None:
        """Load property with documents and programs."""
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

    def _get_renewal_date(self, prop: Property) -> datetime | None:
        """Get renewal date from active program or latest program with expiration.

        Falls back to policy expiration dates if program expiration is not set.
        """
        # First try active programs
        active_programs = [
            p for p in prop.insurance_programs if p.status == "active"
        ]

        # If no active programs, use all programs
        programs_to_check = active_programs if active_programs else prop.insurance_programs

        if not programs_to_check:
            return None

        # Get earliest future expiration date from programs
        today = date.today()
        exp_dates = [
            p.expiration_date for p in programs_to_check
            if p.expiration_date and p.expiration_date >= today
        ]

        if not exp_dates:
            # Fallback: check policy expiration dates within programs
            for program in programs_to_check:
                for policy in program.policies:
                    if policy.expiration_date and policy.expiration_date >= today:
                        exp_dates.append(policy.expiration_date)

        if not exp_dates:
            # Last fallback: get any expiration date even if in past
            exp_dates = [
                p.expiration_date for p in programs_to_check if p.expiration_date
            ]
            # Also check policies
            if not exp_dates:
                for program in programs_to_check:
                    for policy in program.policies:
                        if policy.expiration_date:
                            exp_dates.append(policy.expiration_date)

        if not exp_dates:
            return None

        earliest = min(exp_dates)
        return datetime.combine(earliest, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )

    async def _get_recent_assessment(
        self, property_id: str
    ) -> RenewalReadiness | None:
        """Get most recent assessment."""
        stmt = (
            select(RenewalReadiness)
            .where(
                RenewalReadiness.property_id == property_id,
                RenewalReadiness.status == "current",
                RenewalReadiness.deleted_at.is_(None),
            )
            .order_by(RenewalReadiness.assessment_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _assess_documents(
        self,
        prop: Property,
        requirements: list[dict],
    ) -> list[DocumentStatus]:
        """Assess document status against requirements."""
        results = []
        today = date.today()

        for req in requirements:
            doc_type = req["type"]
            label = req["label"]
            max_age = req.get("max_age_days", 365)

            # Find matching document
            matching_docs = [
                d for d in prop.documents
                if d.document_type == doc_type and d.deleted_at is None
            ]

            if not matching_docs:
                results.append(DocumentStatus(
                    type=doc_type,
                    label=label,
                    status="missing",
                ))
                continue

            # Get most recent document
            latest = max(matching_docs, key=lambda d: d.created_at)
            age_days = (today - latest.created_at.date()).days

            # Check staleness
            staleness_threshold = STALENESS_THRESHOLDS.get(doc_type, 365)
            is_stale = age_days > staleness_threshold

            results.append(DocumentStatus(
                type=doc_type,
                label=label,
                status="stale" if is_stale else "found",
                document_id=latest.id,
                filename=latest.file_name,
                age_days=age_days,
                verified=False,
            ))

        return results

    def _calculate_readiness_score(
        self,
        required: list[DocumentStatus],
        recommended: list[DocumentStatus],
    ) -> tuple[int, str]:
        """Calculate readiness score and grade.

        Required documents: 60% weight
        Recommended documents: 40% weight
        """
        required_weight = 60
        recommended_weight = 40

        # Score required documents
        required_score = 0
        if required:
            for doc in required:
                if doc.status == "found":
                    required_score += 1.0
                elif doc.status == "stale":
                    required_score += 0.5
            required_score = (required_score / len(required)) * required_weight

        # Score recommended documents
        recommended_score = 0
        if recommended:
            for doc in recommended:
                if doc.status == "found":
                    recommended_score += 1.0
                elif doc.status == "stale":
                    recommended_score += 0.5
            recommended_score = (recommended_score / len(recommended)) * recommended_weight

        total_score = int(required_score + recommended_score)
        grade = self._score_to_grade(total_score)

        return total_score, grade

    def _score_to_grade(self, score: int) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    async def _verify_documents_with_llm(
        self,
        prop: Property,
        renewal_date: datetime,
        documents: list[DocumentStatus],
    ) -> dict:
        """Verify documents using LLM."""
        # Build documents context
        docs_context = []
        for doc in documents:
            if doc.document_id:
                # Get document from database
                doc_record = next(
                    (d for d in prop.documents if d.id == doc.document_id),
                    None,
                )
                if doc_record:
                    docs_context.append(
                        f"Document ID: {doc.document_id}\n"
                        f"Type: {doc.type}\n"
                        f"Filename: {doc.filename}\n"
                        f"Age: {doc.age_days} days\n"
                        f"Extraction Status: {doc_record.extraction_status}\n"
                        f"Extraction Data: {json.dumps(doc_record.extraction_json or {}, indent=2)[:2000]}"
                    )

        user_prompt = VERIFICATION_USER_PROMPT.format(
            property_name=prop.name,
            renewal_date=renewal_date.strftime("%Y-%m-%d"),
            documents_context="\n\n---\n\n".join(docs_context),
        )

        response = await self._call_llm(VERIFICATION_SYSTEM_PROMPT, user_prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return self._extract_json_from_response(response)

    def _apply_verification_results(
        self,
        documents: list[DocumentStatus],
        verification_results: list[dict],
    ) -> None:
        """Apply LLM verification results to document status."""
        for doc in documents:
            matching = next(
                (v for v in verification_results if v.get("document_id") == doc.document_id),
                None,
            )
            if matching:
                doc.verified = matching.get("verified", False)
                doc.extracted_data = matching.get("extracted_data")
                doc.issues = matching.get("issues", [])

    def _build_issues(
        self,
        required: list[DocumentStatus],
        recommended: list[DocumentStatus],
        days_until: int,
    ) -> list[ReadinessIssue]:
        """Build list of issues."""
        issues = []

        # Critical: Missing required documents
        for doc in required:
            if doc.status == "missing":
                issues.append(ReadinessIssue(
                    severity="critical",
                    issue=f"{doc.label} is missing",
                    impact="Cannot complete renewal without this document",
                ))
            elif doc.status == "stale":
                issues.append(ReadinessIssue(
                    severity="warning",
                    issue=f"{doc.label} is outdated ({doc.age_days} days old)",
                    impact="May not reflect current coverage or values",
                ))

        # Warning: Missing recommended documents
        for doc in recommended:
            if doc.status == "missing":
                issues.append(ReadinessIssue(
                    severity="info",
                    issue=f"{doc.label} is missing",
                    impact="May slow down renewal process",
                ))

        # Timeline-based issues
        if days_until <= 30:
            missing_required = len([d for d in required if d.status == "missing"])
            if missing_required > 0:
                issues.append(ReadinessIssue(
                    severity="critical",
                    issue=f"Renewal in {days_until} days with {missing_required} missing required documents",
                    impact="Urgent action needed to avoid coverage gap",
                ))

        return issues

    def _build_recommendations(
        self,
        required: list[DocumentStatus],
        recommended: list[DocumentStatus],
        days_until: int,
    ) -> list[ReadinessRecommendation]:
        """Build recommendations."""
        recommendations = []

        # Prioritize by timeline
        for doc in required:
            if doc.status == "missing":
                if days_until <= 30:
                    priority = "high"
                    deadline = "Immediately"
                elif days_until <= 60:
                    priority = "high"
                    deadline = "Within 2 weeks"
                else:
                    priority = "medium"
                    deadline = "60 days before renewal"

                recommendations.append(ReadinessRecommendation(
                    priority=priority,
                    action=f"Upload {doc.label}",
                    deadline=deadline,
                ))
            elif doc.status == "stale":
                recommendations.append(ReadinessRecommendation(
                    priority="medium",
                    action=f"Request updated {doc.label}",
                    deadline="Before renewal quotes",
                ))

        for doc in recommended:
            if doc.status == "missing":
                recommendations.append(ReadinessRecommendation(
                    priority="low",
                    action=f"Upload {doc.label} if available",
                    deadline=None,
                ))

        return recommendations

    def _build_milestones(self, days_until: int) -> list[TimelineMilestone]:
        """Build renewal timeline milestones."""
        milestones = [
            TimelineMilestone(
                days_before_renewal=90,
                action="Complete document collection",
                status="completed" if days_until <= 90 else "upcoming",
            ),
            TimelineMilestone(
                days_before_renewal=60,
                action="Request renewal quotes from carriers",
                status="completed" if days_until <= 60 else ("missed" if days_until <= 60 else "upcoming"),
            ),
            TimelineMilestone(
                days_before_renewal=30,
                action="Finalize carrier selection",
                status="completed" if days_until <= 30 else ("missed" if days_until <= 30 else "upcoming"),
            ),
            TimelineMilestone(
                days_before_renewal=14,
                action="Bind coverage",
                status="completed" if days_until <= 14 else "upcoming",
            ),
        ]

        return milestones

    async def _save_assessment(self, result: ReadinessResult) -> RenewalReadiness:
        """Save assessment to database."""
        # Mark existing assessments as superseded
        stmt = (
            select(RenewalReadiness)
            .where(
                RenewalReadiness.property_id == result.property_id,
                RenewalReadiness.status == "current",
                RenewalReadiness.deleted_at.is_(None),
            )
        )
        existing = await self.session.execute(stmt)
        for assessment in existing.scalars().all():
            assessment.status = "superseded"

        # Create new assessment
        assessment = RenewalReadiness(
            property_id=result.property_id,
            target_renewal_date=result.target_renewal_date,
            assessment_date=result.assessment_date,
            readiness_score=result.readiness_score,
            readiness_grade=result.readiness_grade,
            document_status={
                "required": [
                    {
                        "type": d.type,
                        "label": d.label,
                        "status": d.status,
                        "document_id": d.document_id,
                        "filename": d.filename,
                        "age_days": d.age_days,
                        "verified": d.verified,
                    }
                    for d in result.required_documents
                ],
                "recommended": [
                    {
                        "type": d.type,
                        "label": d.label,
                        "status": d.status,
                        "document_id": d.document_id,
                        "filename": d.filename,
                        "age_days": d.age_days,
                        "verified": d.verified,
                    }
                    for d in result.recommended_documents
                ],
            },
            llm_verification={
                "verified_documents": [
                    {
                        "document_id": d.document_id,
                        "type": d.type,
                        "verified": d.verified,
                        "extracted_data": d.extracted_data,
                        "issues": d.issues,
                    }
                    for d in result.required_documents + result.recommended_documents
                    if d.document_id
                ],
                "data_consistency_issues": result.data_consistency_issues,
                "verification_summary": result.verification_summary,
            } if result.verification_summary else None,
            issues=[
                {"severity": i.severity, "issue": i.issue, "impact": i.impact}
                for i in result.issues
            ],
            recommendations=[
                {"priority": r.priority, "action": r.action, "deadline": r.deadline}
                for r in result.recommendations
            ],
            renewal_timeline={
                "days_until_renewal": result.days_until_renewal,
                "milestones": [
                    {"day": m.days_before_renewal, "action": m.action, "status": m.status}
                    for m in result.milestones
                ],
            },
            status="current",
            llm_model_used=result.model_used,
            llm_latency_ms=result.latency_ms,
        )

        self.session.add(assessment)
        await self.session.flush()

        logger.info(f"Saved renewal readiness assessment for property {result.property_id}")
        return assessment

    def _assessment_model_to_result(
        self, assessment: RenewalReadiness, prop: Property
    ) -> ReadinessResult:
        """Convert database model to result dataclass."""
        doc_status = assessment.document_status or {}

        required_docs = [
            DocumentStatus(
                type=d.get("type", ""),
                label=d.get("label", ""),
                status=d.get("status", "missing"),
                document_id=d.get("document_id"),
                filename=d.get("filename"),
                age_days=d.get("age_days"),
                verified=d.get("verified", False),
            )
            for d in doc_status.get("required", [])
        ]

        recommended_docs = [
            DocumentStatus(
                type=d.get("type", ""),
                label=d.get("label", ""),
                status=d.get("status", "missing"),
                document_id=d.get("document_id"),
                filename=d.get("filename"),
                age_days=d.get("age_days"),
                verified=d.get("verified", False),
            )
            for d in doc_status.get("recommended", [])
        ]

        verification = assessment.llm_verification or {}
        timeline = assessment.renewal_timeline or {}

        return ReadinessResult(
            property_id=assessment.property_id,
            property_name=prop.name,
            target_renewal_date=assessment.target_renewal_date,
            days_until_renewal=timeline.get("days_until_renewal", 0),
            readiness_score=assessment.readiness_score,
            readiness_grade=assessment.readiness_grade,
            required_documents=required_docs,
            recommended_documents=recommended_docs,
            verification_summary=verification.get("verification_summary"),
            data_consistency_issues=verification.get("data_consistency_issues", []),
            issues=[
                ReadinessIssue(
                    severity=i.get("severity", "info"),
                    issue=i.get("issue", ""),
                    impact=i.get("impact", ""),
                )
                for i in (assessment.issues or [])
            ],
            recommendations=[
                ReadinessRecommendation(
                    priority=r.get("priority", "medium"),
                    action=r.get("action", ""),
                    deadline=r.get("deadline"),
                )
                for r in (assessment.recommendations or [])
            ],
            milestones=[
                TimelineMilestone(
                    days_before_renewal=m.get("day", 0),
                    action=m.get("action", ""),
                    status=m.get("status", "upcoming"),
                )
                for m in timeline.get("milestones", [])
            ],
            assessment_date=assessment.assessment_date,
            status=assessment.status,
            model_used=assessment.llm_model_used,
            latency_ms=assessment.llm_latency_ms or 0,
        )

    def _get_latest_readiness(
        self, readiness_list: list[RenewalReadiness]
    ) -> RenewalReadiness | None:
        """Get the latest readiness assessment."""
        current = [r for r in readiness_list if r.status == "current"]
        if current:
            return max(current, key=lambda r: r.assessment_date)
        return None

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call the LLM API."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Renewal Readiness",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3,
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenRouter API error: {response.status_code} - {error_detail}")
                raise RenewalReadinessAPIError(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                raise RenewalReadinessError("No response from LLM")

            return choices[0].get("message", {}).get("content", "")

    def _extract_json_from_response(self, response: str) -> dict:
        """Extract JSON from a response that may contain extra text."""
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "verified_documents": [],
            "data_consistency_issues": [],
            "verification_summary": response[:500] if response else "",
        }


def get_renewal_readiness_service(session: AsyncSession) -> RenewalReadinessService:
    """Factory function to create RenewalReadinessService.

    Args:
        session: Database session.

    Returns:
        RenewalReadinessService instance.
    """
    return RenewalReadinessService(session)
