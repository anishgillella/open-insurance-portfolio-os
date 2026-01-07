"""Claims API endpoints.

Provides claims listing, detail view, and management for the Kanban board UI.
"""

import logging
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.dependencies import AsyncSessionDep
from app.models.claim import Claim
from app.models.property import Property
from app.repositories.claim_repository import ClaimRepository
from app.schemas.claim import (
    ClaimContact,
    ClaimAttachmentGroup,
    ClaimCreateRequest,
    ClaimDetail,
    ClaimKanbanResponse,
    ClaimListItem,
    ClaimListResponse,
    ClaimSummary,
    ClaimTimelineStep,
    ClaimUpdateRequest,
    ClaimStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_timeline(claim: Claim) -> list[ClaimTimelineStep]:
    """Build timeline steps for a claim."""
    status_order = [
        (ClaimStatus.OPEN, "Open"),
        (ClaimStatus.IN_REVIEW, "In Review"),
        (ClaimStatus.PROCESSING, "Processing"),
        (ClaimStatus.CLOSED, "Closed"),
    ]

    current_status = claim.status.lower() if claim.status else "open"
    timeline = []

    # Map status to index for comparison
    status_map = {s.value: i for i, (s, _) in enumerate(status_order)}
    current_index = status_map.get(current_status, 0)

    for i, (status_enum, label) in enumerate(status_order):
        step_date = None
        if status_enum == ClaimStatus.OPEN and claim.date_reported:
            step_date = claim.date_reported
        elif status_enum == ClaimStatus.CLOSED and claim.date_closed:
            step_date = claim.date_closed

        timeline.append(
            ClaimTimelineStep(
                status=status_enum,
                label=label,
                step_date=step_date,
                is_current=(i == current_index),
                is_completed=(i < current_index),
            )
        )

    return timeline


def _build_mock_contacts() -> list[ClaimContact]:
    """Build mock contacts for demo purposes."""
    return [
        ClaimContact(
            role="Internal Lead",
            name="John Walker",
            email="johnwalker.com",
            phone="345-434-3625%",
        ),
        ClaimContact(
            role="Roofer",
            name="Brad Roofer",
            email="brad@roofer.com",
            phone="334-343-66%",
        ),
        ClaimContact(
            role="Insurer",
            name="Sarah Jones",
            email="sarah@jones.com",
            phone="334-343-66%",
        ),
        ClaimContact(
            role="Contact 4",
            name="Phil Eric",
            email="phil@eric.com",
            phone="334-343-66%",
        ),
        ClaimContact(
            role="Contact 5",
            name="Tom Sly",
            email="tom@sly.com",
            phone="334-343-66%",
        ),
        ClaimContact(
            role="Contact 6",
            name="Harry Sends",
            email="harry@sends.com",
            phone="334-343-66%",
        ),
        ClaimContact(
            role="Contact 7",
            name="Sam Serif",
            email="sam@serif.com",
            phone="334-343-66%",
        ),
        ClaimContact(
            role="Contact",
            name="Ciera Long",
            email="ciera@long.com",
            phone="334-343-66%",
        ),
    ]


def _build_mock_attachments() -> list[ClaimAttachmentGroup]:
    """Build mock attachment groups for demo purposes."""
    return [
        ClaimAttachmentGroup(
            category="evidence_photos",
            display_name="Evidence Photos",
            count=3,
            attachments=[],
        ),
        ClaimAttachmentGroup(
            category="policy_documents",
            display_name="Policy Documents",
            count=3,
            attachments=[],
        ),
        ClaimAttachmentGroup(
            category="payments",
            display_name="Payments",
            count=5,
            attachments=[],
        ),
    ]


def _claim_to_list_item(claim: Claim, property_name: str | None = None) -> ClaimListItem:
    """Convert a Claim model to ClaimListItem."""
    days_open = None
    if claim.date_reported and not claim.date_closed:
        days_open = (date.today() - claim.date_reported).days
    elif claim.date_reported and claim.date_closed:
        days_open = (claim.date_closed - claim.date_reported).days

    return ClaimListItem(
        id=str(claim.id),
        claim_number=claim.claim_number,
        property_id=str(claim.property_id),
        property_name=property_name or (claim.property.name if claim.property else None),
        status=claim.status,
        claim_type=claim.claim_type,
        date_of_loss=claim.date_of_loss,
        date_reported=claim.date_reported,
        total_incurred=claim.total_incurred,
        attachment_count=3,  # Mock for now
        days_open=days_open,
        has_alert=claim.litigation_status is not None,
        created_at=claim.created_at,
    )


@router.get("/", response_model=ClaimListResponse)
async def list_claims(
    db: AsyncSessionDep,
    property_id: str | None = Query(None, description="Filter by property ID"),
    status: str | None = Query(None, description="Filter by status"),
    year: int | None = Query(None, description="Filter by year of loss"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ClaimListResponse:
    """List all claims with optional filters."""
    stmt = (
        select(Claim)
        .options(selectinload(Claim.property))
        .where(Claim.deleted_at.is_(None))
    )

    if property_id:
        stmt = stmt.where(Claim.property_id == property_id)
    if status:
        stmt = stmt.where(Claim.status == status)
    if year:
        stmt = stmt.where(func.extract("year", Claim.date_of_loss) == year)

    stmt = stmt.order_by(Claim.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    claims = result.scalars().all()

    # Get counts by status
    count_stmt = (
        select(Claim.status, func.count(Claim.id))
        .where(Claim.deleted_at.is_(None))
        .group_by(Claim.status)
    )
    if property_id:
        count_stmt = count_stmt.where(Claim.property_id == property_id)

    count_result = await db.execute(count_stmt)
    by_status = {row[0] or "unknown": row[1] for row in count_result.all()}

    # Get total count
    total_stmt = select(func.count(Claim.id)).where(Claim.deleted_at.is_(None))
    if property_id:
        total_stmt = total_stmt.where(Claim.property_id == property_id)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    return ClaimListResponse(
        claims=[_claim_to_list_item(c) for c in claims],
        total=total,
        by_status=by_status,
    )


@router.get("/kanban", response_model=ClaimKanbanResponse)
async def get_claims_kanban(
    db: AsyncSessionDep,
    property_id: str | None = Query(None, description="Filter by property ID"),
    year: int | None = Query(None, description="Filter by year"),
) -> ClaimKanbanResponse:
    """Get claims organized for Kanban board view."""
    stmt = (
        select(Claim)
        .options(selectinload(Claim.property))
        .where(Claim.deleted_at.is_(None))
    )

    if property_id:
        stmt = stmt.where(Claim.property_id == property_id)
    if year:
        stmt = stmt.where(func.extract("year", Claim.date_of_loss) == year)

    stmt = stmt.order_by(Claim.created_at.desc())
    result = await db.execute(stmt)
    claims = result.scalars().all()

    # Organize by status
    kanban: dict[str, list[ClaimListItem]] = {
        "open": [],
        "in_review": [],
        "processing": [],
        "closed": [],
    }

    for claim in claims:
        item = _claim_to_list_item(claim)
        status = (claim.status or "open").lower()

        # Map statuses to kanban columns
        if status in ("open", "pending", "reopened"):
            kanban["open"].append(item)
        elif status == "in_review":
            kanban["in_review"].append(item)
        elif status == "processing":
            kanban["processing"].append(item)
        elif status in ("closed", "denied"):
            kanban["closed"].append(item)
        else:
            kanban["open"].append(item)

    return ClaimKanbanResponse(
        open=kanban["open"],
        in_review=kanban["in_review"],
        processing=kanban["processing"],
        closed=kanban["closed"],
        total=len(claims),
    )


@router.get("/summary", response_model=ClaimSummary)
async def get_claims_summary(
    db: AsyncSessionDep,
    property_id: str | None = Query(None, description="Filter by property ID"),
) -> ClaimSummary:
    """Get summary statistics for claims."""
    base_filter = Claim.deleted_at.is_(None)

    # Total claims
    total_stmt = select(func.count(Claim.id)).where(base_filter)
    if property_id:
        total_stmt = total_stmt.where(Claim.property_id == property_id)
    total = (await db.execute(total_stmt)).scalar() or 0

    # Open claims
    open_stmt = select(func.count(Claim.id)).where(
        base_filter, Claim.status.in_(["open", "pending", "in_review", "processing"])
    )
    if property_id:
        open_stmt = open_stmt.where(Claim.property_id == property_id)
    open_claims = (await db.execute(open_stmt)).scalar() or 0

    # Closed claims
    closed_claims = total - open_claims

    # Financial totals
    financial_stmt = select(
        func.coalesce(func.sum(Claim.total_incurred), 0),
        func.coalesce(func.sum(Claim.total_paid), 0),
        func.coalesce(func.sum(Claim.total_reserve), 0),
    ).where(base_filter)
    if property_id:
        financial_stmt = financial_stmt.where(Claim.property_id == property_id)

    financial_result = await db.execute(financial_stmt)
    row = financial_result.one()

    return ClaimSummary(
        total_claims=total,
        open_claims=open_claims,
        closed_claims=closed_claims,
        total_incurred=row[0],
        total_paid=row[1],
        total_reserved=row[2],
    )


@router.get("/{claim_id}", response_model=ClaimDetail)
async def get_claim(
    claim_id: str,
    db: AsyncSessionDep,
) -> ClaimDetail:
    """Get detailed claim information."""
    stmt = (
        select(Claim)
        .options(selectinload(Claim.property))
        .where(Claim.id == claim_id, Claim.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )

    return ClaimDetail(
        id=str(claim.id),
        claim_number=claim.claim_number,
        property_id=str(claim.property_id),
        property_name=claim.property.name if claim.property else None,
        policy_id=str(claim.policy_id) if claim.policy_id else None,
        status=claim.status,
        litigation_status=claim.litigation_status,
        date_of_loss=claim.date_of_loss,
        date_reported=claim.date_reported,
        date_closed=claim.date_closed,
        claim_type=claim.claim_type,
        description=claim.description,
        cause_of_loss=claim.cause_of_loss,
        location_description=claim.location_description,
        location_address=claim.location_address,
        location_name=claim.location_name,
        carrier_name=claim.carrier_name,
        paid_loss=claim.paid_loss,
        paid_expense=claim.paid_expense,
        paid_medical=claim.paid_medical,
        paid_indemnity=claim.paid_indemnity,
        total_paid=claim.total_paid,
        reserve_loss=claim.reserve_loss,
        reserve_expense=claim.reserve_expense,
        reserve_medical=claim.reserve_medical,
        reserve_indemnity=claim.reserve_indemnity,
        total_reserve=claim.total_reserve,
        incurred_loss=claim.incurred_loss,
        incurred_expense=claim.incurred_expense,
        total_incurred=claim.total_incurred,
        deductible_applied=claim.deductible_applied,
        deductible_recovered=claim.deductible_recovered,
        salvage_amount=claim.salvage_amount,
        subrogation_amount=claim.subrogation_amount,
        net_incurred=claim.net_incurred,
        claimant_name=claim.claimant_name,
        claimant_type=claim.claimant_type,
        injury_description=claim.injury_description,
        notes=claim.notes,
        timeline=_build_timeline(claim),
        contacts=_build_mock_contacts(),
        attachment_groups=_build_mock_attachments(),
        created_at=claim.created_at,
        updated_at=claim.updated_at,
    )


@router.post("/", response_model=ClaimDetail, status_code=status.HTTP_201_CREATED)
async def create_claim(
    request: ClaimCreateRequest,
    db: AsyncSessionDep,
) -> ClaimDetail:
    """Create a new claim."""
    # Verify property exists
    prop_stmt = select(Property).where(
        Property.id == request.property_id,
        Property.deleted_at.is_(None),
    )
    prop_result = await db.execute(prop_stmt)
    property = prop_result.scalar_one_or_none()

    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {request.property_id} not found",
        )

    repo = ClaimRepository(db)
    claim = await repo.create(
        property_id=request.property_id,
        claim_number=request.claim_number,
        claim_type=request.claim_type.value if request.claim_type else None,
        status=request.status.value,
        date_of_loss=request.date_of_loss,
        date_reported=request.date_reported or date.today(),
        description=request.description,
        cause_of_loss=request.cause_of_loss,
        carrier_name=request.carrier_name,
        location_address=request.location_address,
        claimant_name=request.claimant_name,
        notes=request.notes,
    )

    return await get_claim(str(claim.id), db)


@router.patch("/{claim_id}", response_model=ClaimDetail)
async def update_claim(
    claim_id: str,
    request: ClaimUpdateRequest,
    db: AsyncSessionDep,
) -> ClaimDetail:
    """Update a claim (e.g., change status for Kanban drag-drop)."""
    repo = ClaimRepository(db)
    claim = await repo.get(claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )

    update_data = {}
    if request.status:
        update_data["status"] = request.status.value
        # Set date_closed if moving to closed
        if request.status == ClaimStatus.CLOSED and not claim.date_closed:
            update_data["date_closed"] = date.today()
    if request.notes is not None:
        update_data["notes"] = request.notes
    if request.description is not None:
        update_data["description"] = request.description

    if update_data:
        await repo.update(claim_id, **update_data)

    return await get_claim(claim_id, db)


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(
    claim_id: str,
    db: AsyncSessionDep,
) -> None:
    """Soft delete a claim."""
    repo = ClaimRepository(db)
    claim = await repo.get(claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )

    await repo.soft_delete(claim_id)
