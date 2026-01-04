"""Tests for Phase 4.3 features: Document Completeness, Health Score, and Coverage Conflicts.

These tests cover:
1. Document Completeness Service
2. Health Score Service (with LLM mocking)
3. Coverage Conflict Detection Service (with LLM mocking)
4. API Endpoints for all features
5. Recalculation triggers
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.building import Building
from app.models.coverage import Coverage
from app.models.coverage_conflict import CoverageConflict
from app.models.coverage_gap import CoverageGap
from app.models.document import Document
from app.models.health_score import HealthScore
from app.models.insurance_program import InsuranceProgram
from app.models.lender_requirement import LenderRequirement
from app.models.organization import Organization
from app.models.policy import Policy
from app.models.property import Property
from app.repositories.conflict_repository import ConflictRepository
from app.repositories.health_score_repository import HealthScoreRepository
from app.services.completeness_service import CompletenessService
from app.services.conflict_detection_service import ConflictDetectionService
from app.services.health_score_service import HealthScoreService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    org_id = str(uuid4())
    org = Organization(
        id=org_id,
        name="Test Organization",
        slug=f"test-org-{org_id[:8]}",
    )
    db_session.add(org)
    await db_session.flush()
    return org


@pytest.fixture
async def test_property(db_session: AsyncSession, test_organization: Organization) -> Property:
    """Create a test property."""
    prop = Property(
        id=str(uuid4()),
        organization_id=test_organization.id,
        name="Test Property",
        address="123 Test Street",
        city="Test City",
        state="CA",
        zip="90210",
        property_type="multifamily",
        units=100,
        flood_zone="X",
    )
    db_session.add(prop)
    await db_session.flush()
    return prop


@pytest.fixture
async def test_building(db_session: AsyncSession, test_property: Property) -> Building:
    """Create a test building."""
    building = Building(
        id=str(uuid4()),
        property_id=test_property.id,
        building_name="Main Building",
        building_value=Decimal("10000000"),
    )
    db_session.add(building)
    await db_session.flush()
    return building


@pytest.fixture
async def test_program(db_session: AsyncSession, test_property: Property) -> InsuranceProgram:
    """Create a test insurance program."""
    program = InsuranceProgram(
        id=str(uuid4()),
        property_id=test_property.id,
        program_year=date.today().year,
        status="active",
        total_insured_value=Decimal("10000000"),
    )
    db_session.add(program)
    await db_session.flush()
    return program


@pytest.fixture
async def test_policy(
    db_session: AsyncSession,
    test_program: InsuranceProgram,
) -> Policy:
    """Create a test property policy."""
    policy = Policy(
        id=str(uuid4()),
        program_id=test_program.id,
        policy_type="property",
        policy_number="PROP-2024-001",
        carrier_name="Test Insurance Co",
        effective_date=date.today(),
        expiration_date=date.today().replace(year=date.today().year + 1),
        premium=Decimal("50000"),
    )
    db_session.add(policy)
    await db_session.flush()
    return policy


@pytest.fixture
async def test_documents(
    db_session: AsyncSession,
    test_property: Property,
    test_organization: Organization,
) -> list[Document]:
    """Create test documents of various types."""
    docs = []

    # Property policy document
    doc1 = Document(
        id=str(uuid4()),
        property_id=test_property.id,
        organization_id=test_organization.id,
        file_name="property_policy.pdf",
        file_url="/uploads/property_policy.pdf",
        document_type="policy",
        document_subtype="property",
        upload_status="completed",
    )
    docs.append(doc1)

    # GL policy document
    doc2 = Document(
        id=str(uuid4()),
        property_id=test_property.id,
        organization_id=test_organization.id,
        file_name="gl_policy.pdf",
        file_url="/uploads/gl_policy.pdf",
        document_type="policy",
        document_subtype="general_liability",
        upload_status="completed",
    )
    docs.append(doc2)

    # COI document
    doc3 = Document(
        id=str(uuid4()),
        property_id=test_property.id,
        organization_id=test_organization.id,
        file_name="coi.pdf",
        file_url="/uploads/coi.pdf",
        document_type="coi",
        upload_status="completed",
    )
    docs.append(doc3)

    for doc in docs:
        db_session.add(doc)

    await db_session.flush()
    return docs


# ============================================================================
# Document Completeness Tests
# ============================================================================


class TestCompletenessService:
    """Tests for CompletenessService."""

    async def test_get_completeness_with_all_required(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_documents: list[Document],
    ):
        """Test completeness when all required documents are present."""
        service = CompletenessService(db_session, api_key=None)
        result = await service.get_completeness(test_property.id, include_llm_analysis=False)

        assert result.property_id == test_property.id
        assert result.required_present == 3  # property, GL, COI
        assert result.required_total == 3
        assert result.percentage >= 60  # At least required docs = 60%
        assert result.grade in ["A", "B", "C", "D", "F"]

    async def test_get_completeness_missing_required(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test completeness when no documents are present."""
        service = CompletenessService(db_session, api_key=None)
        result = await service.get_completeness(test_property.id, include_llm_analysis=False)

        assert result.required_present == 0
        assert result.percentage == 0
        assert result.grade == "F"

    async def test_completeness_grade_calculation(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_documents: list[Document],
    ):
        """Test that grades are calculated correctly."""
        service = CompletenessService(db_session, api_key=None)
        result = await service.get_completeness(test_property.id, include_llm_analysis=False)

        # With 3 required docs (60%) and 0 optional (0%), score should be 60%
        expected_score = (100 * 0.6) + (0 * 0.4)  # 60
        assert result.percentage == expected_score
        assert result.grade == "D"  # 60-69 = D


# ============================================================================
# Health Score Repository Tests
# ============================================================================


class TestHealthScoreRepository:
    """Tests for HealthScoreRepository."""

    async def test_create_score(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test creating a health score."""
        repo = HealthScoreRepository(db_session)

        score = await repo.create_score(
            property_id=test_property.id,
            score=75,
            grade="C",
            components={
                "coverage_adequacy": {"score": 20, "max": 25, "reasoning": "Good coverage"},
                "policy_currency": {"score": 18, "max": 20, "reasoning": "Current policies"},
            },
            calculated_at=datetime.now(timezone.utc),
            trigger="test",
            executive_summary="Test summary",
            recommendations=[],
        )

        assert score.id is not None
        assert score.score == 75
        assert score.grade == "C"
        assert score.trend_direction == "new"  # First score

    async def test_get_latest_for_property(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test getting the latest score for a property."""
        repo = HealthScoreRepository(db_session)

        # Create two scores
        await repo.create_score(
            property_id=test_property.id,
            score=70,
            grade="C",
            components={},
            calculated_at=datetime.now(timezone.utc),
            trigger="test",
        )

        await repo.create_score(
            property_id=test_property.id,
            score=80,
            grade="B",
            components={},
            calculated_at=datetime.now(timezone.utc),
            trigger="test",
        )

        latest = await repo.get_latest_for_property(test_property.id)

        assert latest is not None
        assert latest.score == 80
        assert latest.grade == "B"
        assert latest.trend_direction == "improving"
        assert latest.trend_delta == 10


# ============================================================================
# Conflict Repository Tests
# ============================================================================


class TestConflictRepository:
    """Tests for ConflictRepository."""

    async def test_create_conflict(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test creating a conflict."""
        repo = ConflictRepository(db_session)

        conflict = await repo.create_conflict(
            property_id=test_property.id,
            conflict_type="entity_mismatch",
            severity="warning",
            title="Entity name mismatch",
            description="Named insureds differ across policies",
            affected_policy_ids=["policy1", "policy2"],
            recommendation="Update policies to use same entity name",
            detection_method="llm",
        )

        assert conflict.id is not None
        assert conflict.conflict_type == "entity_mismatch"
        assert conflict.severity == "warning"
        assert conflict.status == "open"

    async def test_acknowledge_conflict(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test acknowledging a conflict."""
        repo = ConflictRepository(db_session)

        conflict = await repo.create_conflict(
            property_id=test_property.id,
            conflict_type="coverage_overlap",
            severity="info",
            title="Duplicate coverage",
        )

        acknowledged = await repo.acknowledge_conflict(
            conflict.id,
            notes="Reviewed and acceptable",
        )

        assert acknowledged is not None
        assert acknowledged.status == "acknowledged"
        assert acknowledged.acknowledged_notes == "Reviewed and acceptable"

    async def test_resolve_conflict(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test resolving a conflict."""
        repo = ConflictRepository(db_session)

        conflict = await repo.create_conflict(
            property_id=test_property.id,
            conflict_type="limit_tower_gap",
            severity="critical",
            title="Coverage gap in tower",
        )

        resolved = await repo.resolve_conflict(
            conflict.id,
            notes="Increased coverage to fill gap",
        )

        assert resolved is not None
        assert resolved.status == "resolved"
        assert resolved.resolution_notes == "Increased coverage to fill gap"

    async def test_clear_open_conflicts(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test clearing open conflicts."""
        repo = ConflictRepository(db_session)

        # Create open conflicts
        await repo.create_conflict(
            property_id=test_property.id,
            conflict_type="entity_mismatch",
            severity="warning",
            title="Conflict 1",
        )
        await repo.create_conflict(
            property_id=test_property.id,
            conflict_type="coverage_overlap",
            severity="info",
            title="Conflict 2",
        )

        # Acknowledge one
        conflicts = await repo.get_by_property(test_property.id)
        await repo.acknowledge_conflict(conflicts[0].id)

        # Clear open conflicts
        cleared = await repo.clear_open_conflicts(test_property.id)

        # Only one should be cleared (the open one)
        assert cleared == 1

        # Check remaining
        remaining = await repo.get_by_property(test_property.id)
        assert len(remaining) == 1
        assert remaining[0].status == "acknowledged"


# ============================================================================
# Health Score Service Tests (with LLM mocking)
# ============================================================================


class TestHealthScoreService:
    """Tests for HealthScoreService with mocked LLM."""

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for health score calculation."""
        return {
            "total_score": 78,
            "grade": "C",
            "components": {
                "coverage_adequacy": {
                    "score": 20,
                    "reasoning": "Building coverage is adequate",
                    "key_findings": ["Good replacement cost coverage"],
                    "concerns": [],
                },
                "policy_currency": {
                    "score": 18,
                    "reasoning": "Policies are current",
                    "key_findings": ["No expired policies"],
                    "concerns": [],
                },
                "deductible_risk": {
                    "score": 12,
                    "reasoning": "Deductibles are reasonable",
                    "key_findings": [],
                    "concerns": ["Slightly high wind deductible"],
                },
                "coverage_breadth": {
                    "score": 12,
                    "reasoning": "Core coverages present",
                    "key_findings": ["Property and GL in place"],
                    "concerns": ["Missing umbrella"],
                },
                "lender_compliance": {
                    "score": 10,
                    "reasoning": "Meets most requirements",
                    "key_findings": [],
                    "concerns": ["Deductible slightly high for lender"],
                },
                "documentation_quality": {
                    "score": 6,
                    "reasoning": "Key documents present",
                    "key_findings": ["Required docs uploaded"],
                    "concerns": ["Missing loss runs"],
                },
            },
            "executive_summary": "Property has adequate coverage with some room for improvement.",
            "recommendations": [
                {"priority": "medium", "action": "Add umbrella policy", "impact": "+3 points", "component": "coverage_breadth"},
            ],
            "risk_factors": ["Missing umbrella coverage"],
            "strengths": ["Current policies", "Adequate limits"],
        }

    async def test_calculate_health_score(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
        test_policy: Policy,
        test_documents: list[Document],
        mock_llm_response: dict,
    ):
        """Test health score calculation with mocked LLM."""
        import json

        with patch.object(
            HealthScoreService,
            "_call_llm",
            new_callable=AsyncMock,
            return_value=json.dumps(mock_llm_response),
        ):
            service = HealthScoreService(db_session, api_key="test-key")
            result = await service.calculate_health_score(test_property.id, trigger="test")

            assert result.score == 78
            assert result.grade == "C"
            assert "coverage_adequacy" in result.components
            assert result.executive_summary == mock_llm_response["executive_summary"]


# ============================================================================
# Conflict Detection Service Tests (with LLM mocking)
# ============================================================================


class TestConflictDetectionService:
    """Tests for ConflictDetectionService with mocked LLM."""

    @pytest.fixture
    def mock_llm_conflicts_response(self):
        """Mock LLM response for conflict detection."""
        return {
            "conflicts": [
                {
                    "conflict_type": "entity_mismatch",
                    "severity": "warning",
                    "title": "Named insured differs across policies",
                    "description": "Property policy lists 'ABC LLC' but GL lists 'ABC Inc'",
                    "affected_policies": ["PROP-2024-001", "GL-2024-001"],
                    "gap_amount": None,
                    "potential_savings": None,
                    "recommendation": "Update all policies to use same entity name",
                    "reasoning": "Detected different entity names in policy data",
                },
            ],
            "summary": {
                "total_conflicts": 1,
                "critical": 0,
                "warning": 1,
                "info": 0,
            },
            "cross_policy_analysis": "Policies generally align well with minor entity naming issue.",
            "portfolio_recommendations": ["Standardize entity names across all policies"],
        }

    async def test_detect_conflicts_no_policies(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test conflict detection with no policies returns empty."""
        service = ConflictDetectionService(db_session, api_key="test-key")
        result = await service.detect_conflicts(test_property.id)

        assert len(result.conflicts) == 0
        assert "No active policies" in result.cross_policy_analysis

    async def test_detect_conflicts_single_policy(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
        test_policy: Policy,
    ):
        """Test conflict detection with single policy returns empty."""
        service = ConflictDetectionService(db_session, api_key="test-key")
        result = await service.detect_conflicts(test_property.id)

        assert len(result.conflicts) == 0
        assert "one active policy" in result.cross_policy_analysis.lower()


# ============================================================================
# API Endpoint Tests
# ============================================================================


class TestCompletenessEndpoints:
    """Tests for completeness API endpoints."""

    async def test_get_property_completeness(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
        test_documents: list[Document],
    ):
        """Test GET /v1/completeness/properties/{id}."""
        response = await client.get(
            f"/v1/completeness/properties/{test_property.id}",
            params={"include_llm_analysis": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["property_id"] == test_property.id
        assert "completeness" in data
        assert "documents" in data

    async def test_get_property_completeness_not_found(self, client):
        """Test GET /v1/completeness/properties/{id} with invalid ID."""
        fake_id = str(uuid4())
        response = await client.get(
            f"/v1/completeness/properties/{fake_id}",
            params={"include_llm_analysis": False},
        )

        assert response.status_code == 404


class TestHealthScoreEndpoints:
    """Tests for health score API endpoints."""

    async def test_get_portfolio_health_score(
        self,
        client,
        db_session: AsyncSession,
    ):
        """Test GET /v1/health-score/portfolio."""
        response = await client.get("/v1/health-score/portfolio")

        assert response.status_code == 200
        data = response.json()
        assert "portfolio_score" in data
        assert "distribution" in data


class TestConflictEndpoints:
    """Tests for conflict API endpoints."""

    async def test_get_property_conflicts(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test GET /v1/conflicts/properties/{id}."""
        response = await client.get(f"/v1/conflicts/properties/{test_property.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["property_id"] == test_property.id
        assert "conflicts" in data
        assert "summary" in data

    async def test_acknowledge_conflict(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test POST /v1/conflicts/{id}/acknowledge."""
        # Create a conflict first
        repo = ConflictRepository(db_session)
        conflict = await repo.create_conflict(
            property_id=test_property.id,
            conflict_type="test",
            severity="info",
            title="Test conflict",
        )
        await db_session.commit()

        response = await client.post(
            f"/v1/conflicts/{conflict.id}/acknowledge",
            json={"notes": "Reviewed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "acknowledged"
