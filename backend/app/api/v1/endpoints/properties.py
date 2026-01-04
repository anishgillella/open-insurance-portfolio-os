"""Property API endpoints.

Provides property listing, detail views, and related data access.
"""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.repositories.policy_repository import PolicyRepository
from app.repositories.property_repository import PropertyRepository
from app.schemas.common import AddressSchema
from app.schemas.policy import PolicyListItem, PropertyPoliciesResponse, PropertyPolicySummary
from app.schemas.property import (
    BuildingSchema,
    ComplianceSummarySchema,
    CompletenessSummarySchema,
    GapsSummarySchema,
    HealthScoreSchema,
    InsuranceSummarySchema,
    PropertyDetail,
    PropertyDocumentItem,
    PropertyDocumentsResponse,
    PropertyListItem,
    PropertyListResponse,
)

router = APIRouter()


def _build_property_list_item(prop) -> PropertyListItem:
    """Convert a Property model to PropertyListItem schema."""
    # Calculate insurance summary from programs
    total_premium = Decimal("0")
    total_tiv = Decimal("0")
    coverage_types = set()
    next_expiration = None
    days_until = None

    for program in prop.insurance_programs:
        if program.status == "active":
            if program.total_premium:
                total_premium += program.total_premium
            if program.total_insured_value:
                total_tiv += program.total_insured_value

            for policy in program.policies:
                if policy.policy_type:
                    coverage_types.add(policy.policy_type)
                if policy.expiration_date:
                    if next_expiration is None or policy.expiration_date < next_expiration:
                        next_expiration = policy.expiration_date

    if next_expiration:
        days_until = (next_expiration - date.today()).days

    # Count open gaps
    open_gaps = sum(
        1 for g in prop.coverage_gaps
        if g.status == "open" and g.deleted_at is None
    )

    return PropertyListItem(
        id=prop.id,
        name=prop.name,
        address=AddressSchema(
            street=prop.address,
            city=prop.city,
            state=prop.state,
            zip=prop.zip,
            county=prop.county,
            country=prop.country,
        ),
        property_type=prop.property_type,
        total_units=prop.units,
        total_buildings=len(prop.buildings),
        total_insured_value=total_tiv,
        annual_premium=total_premium,
        next_expiration=next_expiration,
        days_until_expiration=days_until,
        open_gaps_count=open_gaps,
        compliance_status="no_requirements",  # Placeholder
        health_score=None,  # Placeholder - will be calculated in Phase 4.3
        completeness_pct=prop.completeness_pct,
        coverage_types=sorted(list(coverage_types)),
    )


def _build_property_detail(prop) -> PropertyDetail:
    """Convert a Property model to PropertyDetail schema."""
    # Build buildings list
    buildings = [
        BuildingSchema(
            id=b.id,
            name=b.name,
            units=b.units,
            stories=b.stories,
            sqft=b.sq_ft,
            year_built=b.year_built,
            construction_type=b.construction_type,
            replacement_cost=b.replacement_cost,
        )
        for b in prop.buildings
    ]

    # Calculate insurance summary
    total_premium = Decimal("0")
    total_tiv = Decimal("0")
    coverage_types = set()
    next_expiration = None
    policy_count = 0

    for program in prop.insurance_programs:
        if program.status == "active":
            if program.total_premium:
                total_premium += program.total_premium
            if program.total_insured_value:
                total_tiv += program.total_insured_value
            policy_count += len(program.policies)

            for policy in program.policies:
                if policy.policy_type:
                    coverage_types.add(policy.policy_type)
                if policy.expiration_date:
                    if next_expiration is None or policy.expiration_date < next_expiration:
                        next_expiration = policy.expiration_date

    days_until = None
    if next_expiration:
        days_until = (next_expiration - date.today()).days

    insurance_summary = InsuranceSummarySchema(
        total_insured_value=total_tiv,
        total_annual_premium=total_premium,
        policy_count=policy_count,
        next_expiration=next_expiration,
        days_until_expiration=days_until,
        coverage_types=sorted(list(coverage_types)),
    )

    # Calculate gap summary
    critical = 0
    warning = 0
    info = 0
    for gap in prop.coverage_gaps:
        if gap.status == "open" and gap.deleted_at is None:
            if gap.severity == "critical":
                critical += 1
            elif gap.severity == "warning":
                warning += 1
            else:
                info += 1

    gaps_summary = GapsSummarySchema(
        total_open=critical + warning + info,
        critical=critical,
        warning=warning,
        info=info,
    )

    # Placeholder summaries (will be implemented in later phases)
    health_score = HealthScoreSchema()
    compliance_summary = ComplianceSummarySchema()
    completeness = CompletenessSummarySchema(percentage=prop.completeness_pct)

    return PropertyDetail(
        id=prop.id,
        name=prop.name,
        external_id=prop.external_id,
        address=AddressSchema(
            street=prop.address,
            city=prop.city,
            state=prop.state,
            zip=prop.zip,
            county=prop.county,
            country=prop.country,
        ),
        property_type=prop.property_type,
        year_built=prop.year_built,
        construction_type=prop.construction_type,
        total_units=prop.units,
        total_sqft=prop.sq_ft,
        has_sprinklers=prop.has_sprinklers,
        protection_class=prop.protection_class,
        flood_zone=prop.flood_zone,
        earthquake_zone=prop.earthquake_zone,
        wind_zone=prop.wind_zone,
        buildings=buildings,
        insurance_summary=insurance_summary,
        health_score=health_score,
        gaps_summary=gaps_summary,
        compliance_summary=compliance_summary,
        completeness=completeness,
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


@router.get("", response_model=PropertyListResponse)
async def list_properties(
    db: AsyncSessionDep,
    organization_id: str | None = Query(
        default=None, description="Filter by organization ID"
    ),
    state: str | None = Query(default=None, description="Filter by state code"),
    search: str | None = Query(
        default=None, description="Search by name or address"
    ),
    sort_by: str = Query(
        default="name",
        description="Sort field: name, premium, expiration, health_score",
    ),
    sort_order: str = Query(default="asc", description="Sort order: asc, desc"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum results"),
) -> PropertyListResponse:
    """List all properties with summary information.

    Returns properties with aggregated data including:
    - Address and characteristics
    - Insurance summary (TIV, premium, coverage types)
    - Next expiration date
    - Open gaps count
    - Compliance status
    """
    repo = PropertyRepository(db)
    properties = await repo.list_with_summary(
        organization_id=organization_id,
        state=state,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
    )

    items = [_build_property_list_item(prop) for prop in properties]

    return PropertyListResponse(
        properties=items,
        total_count=len(items),
    )


@router.get("/{property_id}", response_model=PropertyDetail)
async def get_property(
    property_id: str,
    db: AsyncSessionDep,
) -> PropertyDetail:
    """Get detailed property information.

    Returns complete property data including:
    - Property characteristics
    - All buildings
    - Insurance summary
    - Health score
    - Gap summary
    - Compliance status
    - Document completeness
    """
    repo = PropertyRepository(db)
    prop = await repo.get_with_details(property_id)

    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    return _build_property_detail(prop)


@router.get("/{property_id}/policies", response_model=PropertyPoliciesResponse)
async def get_property_policies(
    property_id: str,
    db: AsyncSessionDep,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum results"),
) -> PropertyPoliciesResponse:
    """Get all policies for a property.

    Returns policies from all insurance programs for this property,
    including coverage counts and status information.
    """
    # Verify property exists
    prop_repo = PropertyRepository(db)
    prop = await prop_repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    # Get policies
    policy_repo = PolicyRepository(db)
    policies = await policy_repo.get_by_property(property_id, limit=limit)

    today = date.today()
    items = []
    total_premium = Decimal("0")
    active_count = 0
    expired_count = 0

    for policy in policies:
        days_until = None
        policy_status = "active"

        if policy.expiration_date:
            days_until = (policy.expiration_date - today).days
            if days_until < 0:
                policy_status = "expired"
                expired_count += 1
            else:
                active_count += 1
        else:
            active_count += 1

        if policy.premium:
            total_premium += policy.premium

        items.append(
            PolicyListItem(
                id=policy.id,
                policy_number=policy.policy_number,
                policy_type=policy.policy_type,
                carrier_name=policy.carrier_name,
                effective_date=policy.effective_date,
                expiration_date=policy.expiration_date,
                days_until_expiration=days_until,
                status=policy_status,
                annual_premium=policy.premium,
                coverage_count=len(policy.coverages),
                property_name=prop.name,
                property_id=prop.id,
            )
        )

    return PropertyPoliciesResponse(
        policies=items,
        summary=PropertyPolicySummary(
            total_policies=len(items),
            total_premium=total_premium,
            active_policies=active_count,
            expired_policies=expired_count,
        ),
    )


@router.get("/{property_id}/documents", response_model=PropertyDocumentsResponse)
async def get_property_documents(
    property_id: str,
    db: AsyncSessionDep,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum results"),
) -> PropertyDocumentsResponse:
    """Get all documents for a property.

    Returns documents associated with this property,
    including processing status and extraction confidence.
    """
    repo = PropertyRepository(db)

    # Verify property exists
    prop = await repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    # Get documents
    documents = await repo.get_documents_by_property(property_id, limit=limit)

    items = [
        PropertyDocumentItem(
            id=doc.id,
            filename=doc.file_name or "Unknown",
            document_type=doc.document_type,
            classification=doc.document_subtype,
            status=doc.extraction_status or "pending",
            uploaded_at=doc.created_at,
            extraction_confidence=doc.extraction_confidence,
        )
        for doc in documents
    ]

    return PropertyDocumentsResponse(
        documents=items,
        total_count=len(items),
    )
