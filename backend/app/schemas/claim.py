"""Schemas for Claims API endpoints."""

import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    """Claim status options."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    PROCESSING = "processing"
    CLOSED = "closed"
    REOPENED = "reopened"
    PENDING = "pending"
    DENIED = "denied"
    SUBROGATION = "subrogation"
    LITIGATION = "litigation"


class ClaimType(str, Enum):
    """Claim type options."""

    PROPERTY_DAMAGE = "property_damage"
    BODILY_INJURY = "bodily_injury"
    LIABILITY = "liability"
    WATER_DAMAGE = "water_damage"
    FIRE = "fire"
    WIND_HAIL = "wind_hail"
    THEFT = "theft"
    VANDALISM = "vandalism"
    SLIP_FALL = "slip_fall"
    AUTO = "auto"
    WORKERS_COMP = "workers_comp"
    EQUIPMENT_BREAKDOWN = "equipment_breakdown"
    OTHER = "other"


# =============================================================================
# Contact Schema
# =============================================================================


class ClaimContact(BaseModel):
    """Contact associated with a claim."""

    role: str = Field(..., description="Contact role (e.g., Internal Lead, Roofer, Insurer)")
    name: str = Field(..., description="Contact name")
    email: str | None = Field(None, description="Contact email")
    phone: str | None = Field(None, description="Contact phone")


# =============================================================================
# Attachment Schema
# =============================================================================


class ClaimAttachment(BaseModel):
    """Attachment associated with a claim."""

    id: str
    category: str = Field(..., description="Category: evidence_photos, policy_documents, payments")
    filename: str
    file_size: int | None = None
    uploaded_at: datetime.datetime | None = None


class ClaimAttachmentGroup(BaseModel):
    """Group of attachments by category."""

    category: str
    display_name: str
    count: int
    attachments: list[ClaimAttachment] = []


# =============================================================================
# Timeline Schema
# =============================================================================


class ClaimTimelineStep(BaseModel):
    """A step in the claim timeline."""

    status: ClaimStatus
    label: str
    step_date: datetime.date | None = None
    is_current: bool = False
    is_completed: bool = False


# =============================================================================
# Response Schemas
# =============================================================================


class ClaimListItem(BaseModel):
    """Claim item for list/kanban view."""

    id: str
    claim_number: str | None = None
    property_id: str
    property_name: str | None = None
    status: str | None = None
    claim_type: str | None = None
    date_of_loss: datetime.date | None = None
    date_reported: datetime.date | None = None
    total_incurred: Decimal | None = None
    attachment_count: int = 0
    days_open: int | None = None
    has_alert: bool = False
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ClaimDetail(BaseModel):
    """Detailed claim information for modal view."""

    id: str
    claim_number: str | None = None
    property_id: str
    property_name: str | None = None
    policy_id: str | None = None

    # Status
    status: str | None = None
    litigation_status: str | None = None

    # Dates
    date_of_loss: datetime.date | None = None
    date_reported: datetime.date | None = None
    date_closed: datetime.date | None = None

    # Description
    claim_type: str | None = None
    description: str | None = None
    cause_of_loss: str | None = None
    location_description: str | None = None
    location_address: str | None = None
    location_name: str | None = None

    # Carrier
    carrier_name: str | None = None

    # Financial - Paid
    paid_loss: Decimal | None = None
    paid_expense: Decimal | None = None
    paid_medical: Decimal | None = None
    paid_indemnity: Decimal | None = None
    total_paid: Decimal | None = None

    # Financial - Reserve
    reserve_loss: Decimal | None = None
    reserve_expense: Decimal | None = None
    reserve_medical: Decimal | None = None
    reserve_indemnity: Decimal | None = None
    total_reserve: Decimal | None = None

    # Financial - Incurred
    incurred_loss: Decimal | None = None
    incurred_expense: Decimal | None = None
    total_incurred: Decimal | None = None

    # Financial - Recovery
    deductible_applied: Decimal | None = None
    deductible_recovered: Decimal | None = None
    salvage_amount: Decimal | None = None
    subrogation_amount: Decimal | None = None
    net_incurred: Decimal | None = None

    # Claimant
    claimant_name: str | None = None
    claimant_type: str | None = None
    injury_description: str | None = None

    # Additional
    notes: str | None = None

    # Timeline
    timeline: list[ClaimTimelineStep] = []

    # Contacts (mock for now, would come from related table)
    contacts: list[ClaimContact] = []

    # Attachments (mock for now, would come from documents)
    attachment_groups: list[ClaimAttachmentGroup] = []

    # Metadata
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None

    class Config:
        from_attributes = True


class ClaimListResponse(BaseModel):
    """Response for listing claims."""

    claims: list[ClaimListItem]
    total: int
    by_status: dict[str, int] = Field(
        default_factory=dict, description="Count of claims by status"
    )


class ClaimKanbanResponse(BaseModel):
    """Response for kanban board view."""

    open: list[ClaimListItem] = []
    in_review: list[ClaimListItem] = []
    processing: list[ClaimListItem] = []
    closed: list[ClaimListItem] = []
    total: int = 0


class ClaimUpdateRequest(BaseModel):
    """Request to update a claim."""

    status: ClaimStatus | None = None
    notes: str | None = None
    description: str | None = None


class ClaimCreateRequest(BaseModel):
    """Request to create a new claim."""

    property_id: str
    claim_number: str | None = None
    claim_type: ClaimType | None = None
    status: ClaimStatus = ClaimStatus.OPEN
    date_of_loss: datetime.date | None = None
    date_reported: datetime.date | None = None
    description: str | None = None
    cause_of_loss: str | None = None
    carrier_name: str | None = None
    location_address: str | None = None
    claimant_name: str | None = None
    notes: str | None = None


class ClaimSummary(BaseModel):
    """Summary statistics for claims."""

    total_claims: int = 0
    open_claims: int = 0
    closed_claims: int = 0
    total_incurred: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    total_reserved: Decimal = Decimal("0")
    avg_days_to_close: float | None = None
