"""Policy API endpoints.

Provides policy listing, detail views, and coverage information.
"""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.repositories.policy_repository import CoverageRepository, PolicyRepository
from app.schemas.policy import (
    CarrierSchema,
    CoverageSchema,
    EndorsementSchema,
    InsuredEntitySchema,
    PolicyCoveragesResponse,
    PolicyDatesSchema,
    PolicyDetail,
    PolicyFinancialsSchema,
    PolicyListItem,
    PolicyListResponse,
    SourceDocumentSchema,
)

router = APIRouter()


def _build_policy_list_item(policy, property_name: str | None = None) -> PolicyListItem:
    """Convert a Policy model to PolicyListItem schema."""
    today = date.today()
    days_until = None
    policy_status = "active"

    if policy.expiration_date:
        days_until = (policy.expiration_date - today).days
        if days_until < 0:
            policy_status = "expired"

    # Get property info from program
    prop_name = property_name
    prop_id = None
    if policy.program and policy.program.property:
        prop_name = policy.program.property.name
        prop_id = policy.program.property.id

    return PolicyListItem(
        id=policy.id,
        policy_number=policy.policy_number,
        policy_type=policy.policy_type,
        carrier_name=policy.carrier_name,
        effective_date=policy.effective_date,
        expiration_date=policy.expiration_date,
        days_until_expiration=days_until,
        status=policy_status,
        annual_premium=policy.premium,
        coverage_count=len(policy.coverages) if policy.coverages else 0,
        property_name=prop_name,
        property_id=prop_id,
    )


def _build_policy_detail(policy) -> PolicyDetail:
    """Convert a Policy model to PolicyDetail schema."""
    today = date.today()

    # Calculate days until expiration
    days_until = None
    term_months = None
    if policy.expiration_date:
        days_until = (policy.expiration_date - today).days
        if policy.effective_date:
            delta = policy.expiration_date - policy.effective_date
            term_months = round(delta.days / 30)

    # Build dates schema
    dates = PolicyDatesSchema(
        effective_date=policy.effective_date,
        expiration_date=policy.expiration_date,
        days_until_expiration=days_until,
        policy_term_months=term_months,
    )

    # Build financials schema
    financials = PolicyFinancialsSchema(
        annual_premium=policy.premium,
        taxes=policy.taxes,
        fees=policy.fees,
        total_cost=policy.total_cost,
    )

    # Build carrier schema
    carrier = None
    if policy.carrier:
        carrier = CarrierSchema(
            id=policy.carrier.id,
            name=policy.carrier.name,
            am_best_rating=policy.carrier.am_best_rating,
            naic_number=policy.carrier.naic_number,
        )
    elif policy.carrier_name:
        carrier = CarrierSchema(name=policy.carrier_name)

    # Build insured entity schema
    insured = None
    if policy.named_insured:
        insured = InsuredEntitySchema(
            id=policy.named_insured.id,
            name=policy.named_insured.name,
            entity_type=policy.named_insured.entity_type,
        )

    # Build coverages list
    coverages = [
        CoverageSchema(
            id=c.id,
            coverage_name=c.coverage_name,
            coverage_category=c.coverage_category,
            limit_amount=c.limit_amount,
            limit_type=c.limit_type,
            deductible_amount=c.deductible_amount,
            deductible_type=c.deductible_type,
            deductible_pct=c.deductible_pct,
            coinsurance_pct=c.coinsurance_pct,
            valuation_type=c.valuation_type,
            waiting_period_hours=c.waiting_period_hours,
        )
        for c in (policy.coverages or [])
    ]

    # Build endorsements list
    endorsements = [
        EndorsementSchema(
            id=e.id,
            endorsement_number=e.endorsement_number,
            title=e.title,
            effective_date=e.effective_date,
            premium_change=e.premium_change,
        )
        for e in (policy.endorsements or [])
    ]

    # Build source documents list
    source_documents = []
    if policy.document:
        source_documents.append(
            SourceDocumentSchema(
                id=policy.document.id,
                filename=policy.document.file_name or "Unknown",
                document_type=policy.document.document_type,
                uploaded_at=policy.document.created_at,
            )
        )

    # Get property info
    prop_id = None
    prop_name = None
    if policy.program and policy.program.property:
        prop_id = policy.program.property.id
        prop_name = policy.program.property.name

    return PolicyDetail(
        id=policy.id,
        policy_number=policy.policy_number,
        policy_type=policy.policy_type,
        carrier=carrier,
        insured_entity=insured,
        dates=dates,
        financials=financials,
        admitted=policy.admitted,
        form_type=policy.form_type,
        policy_form=policy.policy_form,
        coverages=coverages,
        endorsements=endorsements,
        additional_insureds=[],  # Placeholder - would need to parse from policy
        source_documents=source_documents,
        property_id=prop_id,
        property_name=prop_name,
        extraction_confidence=policy.extraction_confidence,
        needs_review=policy.needs_review,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    db: AsyncSessionDep,
    organization_id: str | None = Query(
        default=None, description="Filter by organization ID"
    ),
    policy_type: str | None = Query(
        default=None, description="Filter by policy type"
    ),
    sort_by: str = Query(
        default="expiration_date",
        description="Sort field: expiration_date, policy_type, premium",
    ),
    sort_order: str = Query(default="asc", description="Sort order: asc, desc"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum results"),
) -> PolicyListResponse:
    """List all policies.

    Returns policies with summary information including:
    - Policy identification
    - Carrier and dates
    - Premium and coverage count
    - Associated property
    """
    repo = PolicyRepository(db)
    policies = await repo.list_all_with_property(
        organization_id=organization_id,
        policy_type=policy_type,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
    )

    items = [_build_policy_list_item(policy) for policy in policies]

    return PolicyListResponse(
        policies=items,
        total_count=len(items),
    )


@router.get("/{policy_id}", response_model=PolicyDetail)
async def get_policy(
    policy_id: str,
    db: AsyncSessionDep,
) -> PolicyDetail:
    """Get detailed policy information.

    Returns complete policy data including:
    - Policy identification and dates
    - Carrier and insured information
    - Financial details (premium, taxes, fees)
    - All coverages with limits and deductibles
    - Endorsements
    - Source documents
    """
    repo = PolicyRepository(db)
    policy = await repo.get_with_details(policy_id)

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found",
        )

    return _build_policy_detail(policy)


@router.get("/{policy_id}/coverages", response_model=PolicyCoveragesResponse)
async def get_policy_coverages(
    policy_id: str,
    db: AsyncSessionDep,
) -> PolicyCoveragesResponse:
    """Get all coverages for a policy.

    Returns detailed coverage information including:
    - Coverage limits and types
    - Deductibles
    - Coinsurance
    - Valuation types
    """
    # Verify policy exists
    policy_repo = PolicyRepository(db)
    policy = await policy_repo.get_by_id(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found",
        )

    # Get coverages
    coverage_repo = CoverageRepository(db)
    coverages = await coverage_repo.get_by_policy(policy_id)

    items = [
        CoverageSchema(
            id=c.id,
            coverage_name=c.coverage_name,
            coverage_category=c.coverage_category,
            limit_amount=c.limit_amount,
            limit_type=c.limit_type,
            deductible_amount=c.deductible_amount,
            deductible_type=c.deductible_type,
            deductible_pct=c.deductible_pct,
            coinsurance_pct=c.coinsurance_pct,
            valuation_type=c.valuation_type,
            waiting_period_hours=c.waiting_period_hours,
        )
        for c in coverages
    ]

    return PolicyCoveragesResponse(
        coverages=items,
        total_count=len(items),
    )
