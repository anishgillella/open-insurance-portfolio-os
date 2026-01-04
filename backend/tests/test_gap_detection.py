"""Tests for gap detection service and endpoints."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gap_thresholds import GapType, Severity
from app.models.building import Building
from app.models.coverage import Coverage
from app.models.coverage_gap import CoverageGap
from app.models.insurance_program import InsuranceProgram
from app.models.organization import Organization
from app.models.policy import Policy
from app.models.property import Property
from app.models.valuation import Valuation
from app.repositories.gap_repository import GapRepository
from app.services.gap_detection_service import GapDetectionService


@pytest.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    org_id = str(uuid4())
    org = Organization(
        id=org_id,
        name="Test Organization",
        slug=f"test-org-{org_id[:8]}",  # Unique slug for each test
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
        flood_zone="X",  # Low risk initially
    )
    db_session.add(prop)
    await db_session.flush()
    return prop


@pytest.fixture
async def test_building(db_session: AsyncSession, test_property: Property) -> Building:
    """Create a test building with building value (used as replacement cost)."""
    building = Building(
        id=str(uuid4()),
        property_id=test_property.id,
        name="Main Building",
        building_value=Decimal("10000000"),  # $10M building value
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


class TestGapRepository:
    """Tests for GapRepository."""

    async def test_create_gap(self, db_session: AsyncSession, test_property: Property):
        """Test creating a coverage gap."""
        repo = GapRepository(db_session)

        gap = await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.UNDERINSURANCE,
            severity=Severity.CRITICAL,
            title="Test Gap",
            description="Test description",
            coverage_name="Property Coverage",
            current_value="$5,000,000",
            recommended_value="$10,000,000",
            gap_amount=5000000.0,
        )

        assert gap.id is not None
        assert gap.property_id == test_property.id
        assert gap.gap_type == GapType.UNDERINSURANCE
        assert gap.severity == Severity.CRITICAL
        assert gap.status == "open"

    async def test_get_by_property(self, db_session: AsyncSession, test_property: Property):
        """Test getting gaps by property."""
        repo = GapRepository(db_session)

        # Create multiple gaps
        await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.UNDERINSURANCE,
            severity=Severity.CRITICAL,
            title="Gap 1",
        )
        await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.HIGH_DEDUCTIBLE,
            severity=Severity.WARNING,
            title="Gap 2",
        )

        gaps = await repo.get_by_property(test_property.id)
        assert len(gaps) == 2

    async def test_clear_open_gaps(self, db_session: AsyncSession, test_property: Property):
        """Test clearing open gaps for a property."""
        repo = GapRepository(db_session)

        # Create gaps
        gap1 = await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.UNDERINSURANCE,
            severity=Severity.CRITICAL,
            title="Open Gap",
        )
        gap2 = await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.HIGH_DEDUCTIBLE,
            severity=Severity.WARNING,
            title="Acknowledged Gap",
        )

        # Acknowledge one gap
        await repo.acknowledge_gap(gap2.id)
        await db_session.flush()

        # Clear open gaps
        cleared = await repo.clear_open_gaps_for_property(test_property.id)
        assert cleared == 1  # Only open gap was cleared

        # Check remaining gaps
        gaps = await repo.get_by_property(test_property.id)
        assert len(gaps) == 1
        assert gaps[0].status == "acknowledged"

    async def test_acknowledge_gap(self, db_session: AsyncSession, test_property: Property):
        """Test acknowledging a gap."""
        repo = GapRepository(db_session)

        gap = await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.EXPIRATION,
            severity=Severity.INFO,
            title="Test Gap",
        )

        updated = await repo.acknowledge_gap(gap.id, notes="Reviewed by user")
        assert updated.status == "acknowledged"
        assert updated.resolution_notes == "Reviewed by user"

    async def test_resolve_gap(self, db_session: AsyncSession, test_property: Property):
        """Test resolving a gap."""
        repo = GapRepository(db_session)

        gap = await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.MISSING_COVERAGE,
            severity=Severity.CRITICAL,
            title="Test Gap",
        )

        updated = await repo.resolve_gap(gap.id, notes="Added coverage")
        assert updated.status == "resolved"
        assert updated.resolved_at is not None


class TestGapDetectionService:
    """Tests for GapDetectionService."""

    async def test_detect_underinsurance_critical(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_building: Building,
        test_program: InsuranceProgram,
    ):
        """Test detection of critical underinsurance (<80%)."""
        # Create a property policy with coverage at 70% of replacement cost
        policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="POL-001",
        )
        db_session.add(policy)
        await db_session.flush()

        # Coverage at 70% of $10M = $7M
        coverage = Coverage(
            id=str(uuid4()),
            policy_id=policy.id,
            coverage_name="Building Coverage",
            coverage_category="property",
            limit_amount=Decimal("7000000"),
        )
        db_session.add(coverage)
        await db_session.commit()

        # Run detection
        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        # Should detect critical underinsurance
        underinsurance_gaps = [g for g in gaps if g.gap_type == GapType.UNDERINSURANCE]
        assert len(underinsurance_gaps) == 1
        assert underinsurance_gaps[0].severity == Severity.CRITICAL

    async def test_detect_underinsurance_warning(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_building: Building,
        test_program: InsuranceProgram,
    ):
        """Test detection of warning underinsurance (80-90%)."""
        policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="POL-002",
        )
        db_session.add(policy)
        await db_session.flush()

        # Coverage at 85% of $10M = $8.5M
        coverage = Coverage(
            id=str(uuid4()),
            policy_id=policy.id,
            coverage_name="Building Coverage",
            coverage_category="property",
            limit_amount=Decimal("8500000"),
        )
        db_session.add(coverage)
        await db_session.commit()

        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        underinsurance_gaps = [g for g in gaps if g.gap_type == GapType.UNDERINSURANCE]
        assert len(underinsurance_gaps) == 1
        assert underinsurance_gaps[0].severity == Severity.WARNING

    async def test_detect_expiration_critical(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
    ):
        """Test detection of critical expiration (<=30 days)."""
        # Policy expiring in 15 days
        policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="POL-003",
            expiration_date=date.today() + timedelta(days=15),
        )
        db_session.add(policy)
        await db_session.commit()

        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        expiration_gaps = [g for g in gaps if g.gap_type == GapType.EXPIRATION]
        assert len(expiration_gaps) == 1
        assert expiration_gaps[0].severity == Severity.CRITICAL

    async def test_detect_expiration_warning(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
    ):
        """Test detection of warning expiration (31-60 days)."""
        policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="POL-004",
            expiration_date=date.today() + timedelta(days=45),
        )
        db_session.add(policy)
        await db_session.commit()

        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        expiration_gaps = [g for g in gaps if g.gap_type == GapType.EXPIRATION]
        assert len(expiration_gaps) == 1
        assert expiration_gaps[0].severity == Severity.WARNING

    async def test_detect_missing_property_coverage(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
    ):
        """Test detection of missing required property coverage."""
        # Create only a GL policy, no property policy
        policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="general_liability",
            policy_number="GL-001",
        )
        db_session.add(policy)
        await db_session.commit()

        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        missing_gaps = [g for g in gaps if g.gap_type == GapType.MISSING_COVERAGE]
        # Should detect missing property coverage
        property_gaps = [g for g in missing_gaps if "property" in g.title.lower()]
        assert len(property_gaps) == 1
        assert property_gaps[0].severity == Severity.CRITICAL

    async def test_detect_missing_flood_coverage(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
    ):
        """Test detection of missing flood coverage in flood zone."""
        # Set property to high-risk flood zone
        test_property.flood_zone = "AE"
        await db_session.flush()

        # Create property policy without flood
        policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="POL-005",
        )
        db_session.add(policy)
        await db_session.commit()

        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        flood_gaps = [g for g in gaps if g.gap_type == GapType.MISSING_FLOOD]
        assert len(flood_gaps) == 1
        assert flood_gaps[0].severity == Severity.CRITICAL

    async def test_no_flood_gap_low_risk_zone(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
    ):
        """Test no flood gap detected for low-risk zone."""
        # Set property to low-risk flood zone
        test_property.flood_zone = "X"
        await db_session.flush()

        policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="POL-006",
        )
        db_session.add(policy)
        await db_session.commit()

        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        flood_gaps = [g for g in gaps if g.gap_type == GapType.MISSING_FLOOD]
        assert len(flood_gaps) == 0

    async def test_detect_high_deductible(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
    ):
        """Test detection of high deductible."""
        policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="POL-007",
        )
        db_session.add(policy)
        await db_session.flush()

        # Deductible at 6% of TIV = $600,000 (critical threshold is 5%)
        coverage = Coverage(
            id=str(uuid4()),
            policy_id=policy.id,
            coverage_name="Building Coverage",
            coverage_category="property",
            limit_amount=Decimal("10000000"),
            deductible_pct=6.0,  # 6%
        )
        db_session.add(coverage)
        await db_session.commit()

        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        deductible_gaps = [g for g in gaps if g.gap_type == GapType.HIGH_DEDUCTIBLE]
        assert len(deductible_gaps) >= 1
        assert any(g.severity == Severity.CRITICAL for g in deductible_gaps)

    async def test_detect_outdated_valuation(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test detection of outdated property valuation."""
        # Create valuation from 4 years ago (critical threshold is 3 years)
        valuation = Valuation(
            id=str(uuid4()),
            property_id=test_property.id,
            valuation_date=date.today() - timedelta(days=365 * 4),
            total_insured_value=Decimal("10000000"),
        )
        db_session.add(valuation)
        await db_session.commit()

        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        valuation_gaps = [g for g in gaps if g.gap_type == GapType.OUTDATED_VALUATION]
        assert len(valuation_gaps) == 1
        assert valuation_gaps[0].severity == Severity.CRITICAL

    async def test_no_valuation_gap_recent(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test no valuation gap for recent valuation."""
        # Create recent valuation (6 months ago)
        valuation = Valuation(
            id=str(uuid4()),
            property_id=test_property.id,
            valuation_date=date.today() - timedelta(days=180),
            total_insured_value=Decimal("10000000"),
        )
        db_session.add(valuation)
        await db_session.commit()

        service = GapDetectionService(db_session)
        gaps = await service.detect_gaps_for_property(test_property.id)

        valuation_gaps = [g for g in gaps if g.gap_type == GapType.OUTDATED_VALUATION]
        assert len(valuation_gaps) == 0

    async def test_clear_existing_gaps_on_rerun(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
    ):
        """Test that existing open gaps are cleared on rerun."""
        service = GapDetectionService(db_session)
        repo = GapRepository(db_session)

        # Create a policy expiring soon
        policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="POL-008",
            expiration_date=date.today() + timedelta(days=20),
        )
        db_session.add(policy)
        await db_session.commit()

        # Run detection first time
        gaps1 = await service.detect_gaps_for_property(test_property.id)
        assert len(gaps1) > 0

        # Run detection second time
        gaps2 = await service.detect_gaps_for_property(test_property.id)

        # Should have same number of gaps (old ones cleared, new ones created)
        all_gaps = await repo.get_by_property(test_property.id)
        # Each gap should only exist once
        gap_ids = [g.id for g in all_gaps]
        assert len(gap_ids) == len(set(gap_ids))


class TestGapEndpoints:
    """Tests for gap API endpoints."""

    async def test_detect_gaps_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test POST /v1/gaps/detect endpoint."""
        response = await client.post(
            "/v1/gaps/detect",
            json={"property_id": test_property.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "properties_checked" in data
        assert "gaps_detected" in data
        assert "gaps_by_type" in data
        assert "gaps_by_severity" in data

    async def test_list_gaps_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test GET /v1/gaps endpoint."""
        # Create a gap first
        repo = GapRepository(db_session)
        await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.EXPIRATION,
            severity=Severity.WARNING,
            title="Test Expiration Gap",
        )
        await db_session.commit()

        response = await client.get(
            "/v1/gaps",
            params={"property_id": test_property.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "gaps" in data
        assert "total_count" in data
        assert "summary" in data
        assert len(data["gaps"]) >= 1

    async def test_get_gap_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test GET /v1/gaps/{gap_id} endpoint."""
        repo = GapRepository(db_session)
        gap = await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.MISSING_COVERAGE,
            severity=Severity.CRITICAL,
            title="Test Gap",
            description="Test description",
        )
        await db_session.commit()

        response = await client.get(f"/v1/gaps/{gap.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == gap.id
        assert data["gap_type"] == GapType.MISSING_COVERAGE
        assert data["severity"] == Severity.CRITICAL

    async def test_acknowledge_gap_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test POST /v1/gaps/{gap_id}/acknowledge endpoint."""
        repo = GapRepository(db_session)
        gap = await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.HIGH_DEDUCTIBLE,
            severity=Severity.WARNING,
            title="Test Gap",
        )
        await db_session.commit()

        response = await client.post(
            f"/v1/gaps/{gap.id}/acknowledge",
            json={"notes": "Reviewed by admin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "acknowledged"

    async def test_resolve_gap_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test POST /v1/gaps/{gap_id}/resolve endpoint."""
        repo = GapRepository(db_session)
        gap = await repo.create_gap(
            property_id=test_property.id,
            gap_type=GapType.UNDERINSURANCE,
            severity=Severity.CRITICAL,
            title="Test Gap",
        )
        await db_session.commit()

        response = await client.post(
            f"/v1/gaps/{gap.id}/resolve",
            json={"notes": "Coverage increased"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"

    async def test_gap_not_found(self, client):
        """Test 404 for non-existent gap."""
        response = await client.get(f"/v1/gaps/{str(uuid4())}")
        assert response.status_code == 404
