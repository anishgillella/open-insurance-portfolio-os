"""Tests for compliance checking service and endpoints."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gap_thresholds import GapType
from app.models.coverage import Coverage
from app.models.insurance_program import InsuranceProgram
from app.models.lender import Lender
from app.models.lender_requirement import LenderRequirement
from app.models.organization import Organization
from app.models.policy import Policy
from app.models.property import Property
from app.services.compliance_service import ComplianceService


@pytest.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    org_id = str(uuid4())
    org = Organization(
        id=org_id,
        name="Test Org",
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
        address="456 Test Ave",
        city="Test City",
        state="CA",
        zip="90210",
        property_type="multifamily",
        units=100,
        flood_zone="AE",  # High-risk flood zone
    )
    db_session.add(prop)
    await db_session.flush()
    return prop


@pytest.fixture
async def test_program(db_session: AsyncSession, test_property: Property) -> InsuranceProgram:
    """Create a test insurance program."""
    program = InsuranceProgram(
        id=str(uuid4()),
        property_id=test_property.id,
        program_year=date.today().year,
        status="active",
        total_insured_value=Decimal("15000000"),
    )
    db_session.add(program)
    await db_session.flush()
    return program


@pytest.fixture
async def test_lender(db_session: AsyncSession) -> Lender:
    """Create a test lender."""
    lender_id = str(uuid4())
    lender = Lender(
        id=lender_id,
        name=f"Test Bank {lender_id[:8]}",  # Unique name for each test
    )
    db_session.add(lender)
    await db_session.flush()
    return lender


@pytest.fixture
async def test_lender_requirement(
    db_session: AsyncSession,
    test_property: Property,
    test_lender: Lender,
) -> LenderRequirement:
    """Create a test lender requirement."""
    req = LenderRequirement(
        id=str(uuid4()),
        property_id=test_property.id,
        lender_id=test_lender.id,
        loan_number="LOAN-001",
        loan_amount=Decimal("10000000"),
        min_property_limit=Decimal("1.0"),  # 100% of TIV
        min_gl_limit=Decimal("1000000"),  # $1M GL
        min_umbrella_limit=Decimal("5000000"),  # $5M umbrella
        max_deductible_pct=0.05,  # 5% max deductible
        requires_flood=True,
        requires_earthquake=False,
    )
    db_session.add(req)
    await db_session.flush()
    return req


@pytest.fixture
async def compliant_policies(
    db_session: AsyncSession,
    test_program: InsuranceProgram,
) -> list[Policy]:
    """Create policies that meet all requirements."""
    policies = []

    # Property policy with 100% coverage
    property_policy = Policy(
        id=str(uuid4()),
        program_id=test_program.id,
        policy_type="property",
        policy_number="PROP-001",
    )
    db_session.add(property_policy)
    await db_session.flush()

    property_coverage = Coverage(
        id=str(uuid4()),
        policy_id=property_policy.id,
        coverage_name="Building Coverage",
        coverage_category="property",
        limit_amount=Decimal("15000000"),  # 100% of TIV
        deductible_pct=2.0,  # 2% - within limit
    )
    db_session.add(property_coverage)
    policies.append(property_policy)

    # GL policy with $2M limit
    gl_policy = Policy(
        id=str(uuid4()),
        program_id=test_program.id,
        policy_type="general_liability",
        policy_number="GL-001",
    )
    db_session.add(gl_policy)
    await db_session.flush()

    gl_coverage = Coverage(
        id=str(uuid4()),
        policy_id=gl_policy.id,
        coverage_name="General Liability",
        coverage_category="liability",
        limit_amount=Decimal("2000000"),
    )
    db_session.add(gl_coverage)
    policies.append(gl_policy)

    # Umbrella policy with $5M limit
    umbrella_policy = Policy(
        id=str(uuid4()),
        program_id=test_program.id,
        policy_type="umbrella",
        policy_number="UMB-001",
    )
    db_session.add(umbrella_policy)
    await db_session.flush()

    umbrella_coverage = Coverage(
        id=str(uuid4()),
        policy_id=umbrella_policy.id,
        coverage_name="Umbrella Liability",
        coverage_category="liability",
        limit_amount=Decimal("5000000"),
    )
    db_session.add(umbrella_coverage)
    policies.append(umbrella_policy)

    # Flood policy
    flood_policy = Policy(
        id=str(uuid4()),
        program_id=test_program.id,
        policy_type="flood",
        policy_number="FLD-001",
    )
    db_session.add(flood_policy)
    policies.append(flood_policy)

    await db_session.commit()
    return policies


class TestComplianceService:
    """Tests for ComplianceService."""

    async def test_compliant_property(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_lender_requirement: LenderRequirement,
        compliant_policies: list[Policy],
    ):
        """Test compliance check for fully compliant property."""
        service = ComplianceService(db_session)
        results = await service.check_compliance_for_property(
            test_property.id, create_gaps=False
        )

        assert len(results) == 1
        result = results[0]
        assert result.is_compliant
        assert result.status == "compliant"
        assert len(result.issues) == 0

    async def test_non_compliant_gl_limit(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
        test_lender_requirement: LenderRequirement,
    ):
        """Test detection of insufficient GL limit."""
        # Create GL policy with insufficient limit
        gl_policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="general_liability",
            policy_number="GL-002",
        )
        db_session.add(gl_policy)
        await db_session.flush()

        gl_coverage = Coverage(
            id=str(uuid4()),
            policy_id=gl_policy.id,
            coverage_name="General Liability",
            coverage_category="liability",
            limit_amount=Decimal("500000"),  # Below $1M requirement
        )
        db_session.add(gl_coverage)
        await db_session.commit()

        service = ComplianceService(db_session)
        results = await service.check_compliance_for_property(
            test_property.id, create_gaps=False
        )

        assert len(results) == 1
        result = results[0]
        assert not result.is_compliant

        gl_issues = [i for i in result.issues if "General Liability" in i.check_name]
        assert len(gl_issues) == 1

    async def test_non_compliant_missing_umbrella(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
        test_lender_requirement: LenderRequirement,
    ):
        """Test detection of missing umbrella coverage."""
        # Create only GL policy, no umbrella
        gl_policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="general_liability",
            policy_number="GL-003",
        )
        db_session.add(gl_policy)
        await db_session.flush()

        gl_coverage = Coverage(
            id=str(uuid4()),
            policy_id=gl_policy.id,
            coverage_name="General Liability",
            coverage_category="liability",
            limit_amount=Decimal("2000000"),
        )
        db_session.add(gl_coverage)
        await db_session.commit()

        service = ComplianceService(db_session)
        results = await service.check_compliance_for_property(
            test_property.id, create_gaps=False
        )

        assert len(results) == 1
        result = results[0]
        assert not result.is_compliant

        umbrella_issues = [i for i in result.issues if "Umbrella" in i.check_name]
        assert len(umbrella_issues) == 1

    async def test_non_compliant_missing_flood(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
        test_lender_requirement: LenderRequirement,
    ):
        """Test detection of missing flood coverage when required."""
        # Create only property policy, no flood
        property_policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="PROP-002",
        )
        db_session.add(property_policy)
        await db_session.flush()

        property_coverage = Coverage(
            id=str(uuid4()),
            policy_id=property_policy.id,
            coverage_name="Building Coverage",
            coverage_category="property",
            limit_amount=Decimal("15000000"),
        )
        db_session.add(property_coverage)
        await db_session.commit()

        service = ComplianceService(db_session)
        results = await service.check_compliance_for_property(
            test_property.id, create_gaps=False
        )

        assert len(results) == 1
        result = results[0]
        assert not result.is_compliant

        flood_issues = [i for i in result.issues if "Flood" in i.check_name]
        assert len(flood_issues) == 1

    async def test_non_compliant_high_deductible(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
        test_lender_requirement: LenderRequirement,
    ):
        """Test detection of deductible exceeding limit."""
        # Create policy with high deductible
        property_policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="property",
            policy_number="PROP-003",
        )
        db_session.add(property_policy)
        await db_session.flush()

        # 8% deductible exceeds 5% limit
        property_coverage = Coverage(
            id=str(uuid4()),
            policy_id=property_policy.id,
            coverage_name="Building Coverage",
            coverage_category="property",
            limit_amount=Decimal("15000000"),
            deductible_pct=8.0,  # 8% exceeds 5% limit
        )
        db_session.add(property_coverage)
        await db_session.commit()

        service = ComplianceService(db_session)
        results = await service.check_compliance_for_property(
            test_property.id, create_gaps=False
        )

        assert len(results) == 1
        result = results[0]

        deductible_issues = [i for i in result.issues if "Deductible" in i.check_name]
        assert len(deductible_issues) >= 1

    async def test_check_against_template(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
    ):
        """Test checking against a compliance template."""
        # Create minimal policies
        gl_policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="general_liability",
            policy_number="GL-004",
        )
        db_session.add(gl_policy)
        await db_session.flush()

        gl_coverage = Coverage(
            id=str(uuid4()),
            policy_id=gl_policy.id,
            coverage_name="General Liability",
            coverage_category="liability",
            limit_amount=Decimal("500000"),  # Below standard $1M
        )
        db_session.add(gl_coverage)
        await db_session.commit()

        service = ComplianceService(db_session)
        result = await service.check_against_template(test_property.id, "standard")

        assert result is not None
        assert result.template_name == "Standard Commercial"
        # Should have GL issue
        gl_issues = [i for i in result.issues if "General Liability" in i.check_name]
        assert len(gl_issues) >= 1

    async def test_get_available_templates(self, db_session: AsyncSession):
        """Test getting list of available templates."""
        service = ComplianceService(db_session)
        templates = service.get_available_templates()

        assert len(templates) == 3

        template_names = [t["name"] for t in templates]
        assert "standard" in template_names
        assert "fannie_mae" in template_names
        assert "conservative" in template_names

    async def test_create_compliance_gaps(
        self,
        db_session: AsyncSession,
        test_property: Property,
        test_program: InsuranceProgram,
        test_lender_requirement: LenderRequirement,
    ):
        """Test that compliance issues create gap records."""
        # Create non-compliant policies
        gl_policy = Policy(
            id=str(uuid4()),
            program_id=test_program.id,
            policy_type="general_liability",
            policy_number="GL-005",
        )
        db_session.add(gl_policy)
        await db_session.flush()

        gl_coverage = Coverage(
            id=str(uuid4()),
            policy_id=gl_policy.id,
            coverage_name="General Liability",
            coverage_category="liability",
            limit_amount=Decimal("500000"),
        )
        db_session.add(gl_coverage)
        await db_session.commit()

        service = ComplianceService(db_session)
        results = await service.check_compliance_for_property(
            test_property.id, create_gaps=True
        )

        # Check gaps were created
        from app.repositories.gap_repository import GapRepository

        gap_repo = GapRepository(db_session)
        gaps = await gap_repo.get_by_property(test_property.id)

        compliance_gaps = [g for g in gaps if g.gap_type == GapType.COMPLIANCE]
        assert len(compliance_gaps) > 0

    async def test_no_requirements_returns_empty(
        self,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test that property with no lender requirements returns empty list."""
        service = ComplianceService(db_session)
        results = await service.check_compliance_for_property(test_property.id)

        assert results == []


class TestComplianceEndpoints:
    """Tests for compliance API endpoints."""

    async def test_get_templates_endpoint(self, client):
        """Test GET /v1/compliance/templates endpoint."""
        response = await client.get("/v1/compliance/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) == 3

    async def test_get_property_compliance_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test GET /v1/compliance/properties/{id} endpoint."""
        response = await client.get(f"/v1/compliance/properties/{test_property.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["property_id"] == test_property.id
        assert "compliance_checks" in data
        assert "overall_status" in data

    async def test_check_compliance_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test POST /v1/compliance/properties/{id}/check endpoint."""
        response = await client.post(
            f"/v1/compliance/properties/{test_property.id}/check",
            json={"template_name": "standard", "create_gaps": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["property_id"] == test_property.id
        assert len(data["compliance_checks"]) == 1

    async def test_get_requirements_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test GET /v1/compliance/properties/{id}/requirements endpoint."""
        response = await client.get(
            f"/v1/compliance/properties/{test_property.id}/requirements"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_requirement_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
    ):
        """Test POST /v1/compliance/properties/{id}/requirements endpoint."""
        response = await client.post(
            f"/v1/compliance/properties/{test_property.id}/requirements",
            json={
                "loan_number": "NEW-LOAN-001",
                "loan_amount": 5000000,
                "min_gl_limit": 1000000,
                "requires_flood": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["loan_number"] == "NEW-LOAN-001"
        assert data["property_id"] == test_property.id

    async def test_update_requirement_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
        test_lender_requirement: LenderRequirement,
    ):
        """Test PUT /v1/compliance/properties/{id}/requirements/{id} endpoint."""
        await db_session.commit()

        response = await client.put(
            f"/v1/compliance/properties/{test_property.id}/requirements/{test_lender_requirement.id}",
            json={
                "min_gl_limit": 2000000,  # Update GL limit
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Decimal serializes with trailing decimals, so check as float
        assert float(data["min_gl_limit"]) == 2000000.0

    async def test_delete_requirement_endpoint(
        self,
        client,
        db_session: AsyncSession,
        test_property: Property,
        test_lender_requirement: LenderRequirement,
    ):
        """Test DELETE /v1/compliance/properties/{id}/requirements/{id} endpoint."""
        await db_session.commit()

        response = await client.delete(
            f"/v1/compliance/properties/{test_property.id}/requirements/{test_lender_requirement.id}"
        )

        assert response.status_code == 200

    async def test_property_not_found(self, client):
        """Test 404 for non-existent property."""
        response = await client.get(f"/v1/compliance/properties/{str(uuid4())}")
        assert response.status_code == 404
