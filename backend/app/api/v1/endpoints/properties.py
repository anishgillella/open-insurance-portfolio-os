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
    DocumentChecklistItem,
    GapsCountSchema,
    GapsSummarySchema,
    HealthScoreSchema,
    InsuranceSummarySchema,
    PolicySummaryItem,
    PropertyDetail,
    PropertyDocumentItem,
    PropertyDocumentsResponse,
    PropertyListItem,
    PropertyListResponse,
)

router = APIRouter()

# Standard insurance document types with metadata
STANDARD_DOCUMENT_TYPES = [
    {
        "document_type": "coi",
        "display_name": "Certificate of Insurance (COI)",
        "description": "Summary of coverage from carrier",
        "is_required": True,
        "fields_provided": [
            "Carrier Name",
            "Policy Number",
            "Coverage Limits",
            "Named Insured",
            "Expiration Date",
        ],
    },
    {
        "document_type": "policy",
        "display_name": "Policy Declaration Page",
        "description": "Official policy terms and premium",
        "is_required": True,
        "fields_provided": [
            "Premium Amount",
            "Deductibles",
            "Coverage Details",
            "Policy Terms",
            "Endorsements",
        ],
    },
    {
        "document_type": "sov",
        "display_name": "Schedule of Values (SOV)",
        "description": "Property values and building details",
        "is_required": True,
        "fields_provided": [
            "Total Insured Value (TIV)",
            "Building Values",
            "Contents Values",
            "Business Income",
            "Building Details",
        ],
    },
    {
        "document_type": "eop",
        "display_name": "Evidence of Property Insurance",
        "description": "Proof of property coverage",
        "is_required": True,
        "fields_provided": [
            "Property Coverage Limits",
            "Deductibles",
            "Covered Perils",
            "Property Address",
        ],
    },
    {
        "document_type": "invoice",
        "display_name": "Premium Invoice/Statement",
        "description": "Payment and premium breakdown",
        "is_required": False,
        "fields_provided": [
            "Total Premium",
            "Premium Breakdown",
            "Payment Terms",
            "Taxes and Fees",
        ],
    },
    {
        "document_type": "loss_run",
        "display_name": "Loss Run Report",
        "description": "Claims history from carrier",
        "is_required": False,
        "fields_provided": [
            "Claims History",
            "Loss Amounts",
            "Claim Dates",
            "Loss Ratio",
        ],
    },
    {
        "document_type": "endorsement",
        "display_name": "Policy Endorsements",
        "description": "Modifications to policy terms",
        "is_required": False,
        "fields_provided": [
            "Coverage Modifications",
            "Additional Insureds",
            "Special Conditions",
        ],
    },
]


def _build_document_completeness(documents) -> CompletenessSummarySchema:
    """Build document completeness checklist from uploaded documents."""
    # Get set of document types that have been uploaded
    uploaded_types = {}
    for doc in documents:
        if doc.document_type and doc.deleted_at is None:
            doc_type = doc.document_type.lower()
            if doc_type not in uploaded_types:
                uploaded_types[doc_type] = doc.file_name

    # Build checklist
    checklist = []
    required_present = 0
    required_total = 0
    optional_present = 0
    optional_total = 0

    for doc_def in STANDARD_DOCUMENT_TYPES:
        doc_type = doc_def["document_type"]
        is_present = doc_type in uploaded_types
        uploaded_file = uploaded_types.get(doc_type)

        checklist.append(
            DocumentChecklistItem(
                document_type=doc_type,
                display_name=doc_def["display_name"],
                description=doc_def["description"],
                is_required=doc_def["is_required"],
                is_present=is_present,
                fields_provided=doc_def["fields_provided"],
                uploaded_file=uploaded_file,
            )
        )

        if doc_def["is_required"]:
            required_total += 1
            if is_present:
                required_present += 1
        else:
            optional_total += 1
            if is_present:
                optional_present += 1

    # Calculate percentage based on required documents
    percentage = (required_present / required_total * 100) if required_total > 0 else 0

    return CompletenessSummarySchema(
        percentage=percentage,
        required_present=required_present,
        required_total=required_total,
        optional_present=optional_present,
        optional_total=optional_total,
        checklist=checklist,
    )


def _extract_financial_data_from_documents(documents) -> tuple[Decimal, Decimal]:
    """Extract total premium and TIV from document extraction data.

    Falls back to extraction_json when program/policy totals are not populated.
    """
    total_premium = Decimal("0")
    total_tiv = Decimal("0")

    for doc in documents:
        if not doc.extraction_json:
            continue

        extraction = doc.extraction_json if isinstance(doc.extraction_json, dict) else {}

        # Try invoice data first (most reliable for premiums)
        invoice = extraction.get("invoice") or {}
        if invoice.get("total_amount"):
            try:
                total_premium += Decimal(str(invoice["total_amount"]))
            except (ValueError, TypeError):
                pass

        # Try SOV data for TIV
        sov = extraction.get("sov") or {}
        if sov.get("total_insured_value"):
            try:
                total_tiv += Decimal(str(sov["total_insured_value"]))
            except (ValueError, TypeError):
                pass

        # Try COI data for TIV (property_limit is commonly used for TIV in certificates)
        coi = extraction.get("coi") or {}
        if total_tiv == 0 and coi.get("property_limit"):
            try:
                total_tiv = Decimal(str(coi["property_limit"]))
            except (ValueError, TypeError):
                pass

        # Try policy data
        policy = extraction.get("policy") or {}
        if policy.get("premium") and not invoice.get("total_amount"):
            try:
                total_premium += Decimal(str(policy["premium"]))
            except (ValueError, TypeError):
                pass
        if total_tiv == 0 and policy.get("total_insured_value"):
            try:
                total_tiv = Decimal(str(policy["total_insured_value"]))
            except (ValueError, TypeError):
                pass

    return total_premium, total_tiv


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

    # If no totals from programs, try to extract from documents
    if total_premium == 0 and total_tiv == 0 and hasattr(prop, 'documents'):
        doc_premium, doc_tiv = _extract_financial_data_from_documents(prop.documents)
        if doc_premium > 0:
            total_premium = doc_premium
        if doc_tiv > 0:
            total_tiv = doc_tiv

    if next_expiration:
        days_until = (next_expiration - date.today()).days

    # Count gaps by severity
    critical_gaps = 0
    warning_gaps = 0
    info_gaps = 0
    for g in prop.coverage_gaps:
        if g.status == "open" and g.deleted_at is None:
            if g.severity == "critical":
                critical_gaps += 1
            elif g.severity == "warning":
                warning_gaps += 1
            else:
                info_gaps += 1

    # Calculate health score (placeholder - simple formula based on gaps)
    health_score = max(0, 100 - (critical_gaps * 20) - (warning_gaps * 10) - (info_gaps * 5))

    # Determine grade from score
    if health_score >= 90:
        health_grade = "A"
    elif health_score >= 80:
        health_grade = "B"
    elif health_score >= 70:
        health_grade = "C"
    elif health_score >= 60:
        health_grade = "D"
    else:
        health_grade = "F"

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
        year_built=prop.year_built,
        total_insured_value=total_tiv,
        total_premium=total_premium,
        health_score=health_score,
        health_grade=health_grade,
        gaps_count=GapsCountSchema(
            critical=critical_gaps,
            warning=warning_gaps,
            info=info_gaps,
        ),
        next_expiration=next_expiration,
        days_until_expiration=days_until,
        compliance_status="no_requirements",  # Placeholder
        completeness_percentage=prop.completeness_pct or 0,
        coverage_types=sorted(list(coverage_types)),
        created_at=prop.created_at,
        updated_at=prop.updated_at,
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

    # If no totals from programs, try to extract from documents
    if total_premium == 0 and total_tiv == 0 and hasattr(prop, 'documents'):
        doc_premium, doc_tiv = _extract_financial_data_from_documents(prop.documents)
        if doc_premium > 0:
            total_premium = doc_premium
        if doc_tiv > 0:
            total_tiv = doc_tiv

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

    # Build document completeness checklist
    completeness = _build_document_completeness(prop.documents) if hasattr(prop, 'documents') else CompletenessSummarySchema()

    # Calculate health score based on gaps and document completeness
    # Simple formula: start at 100, deduct for gaps and missing docs
    base_score = 100
    base_score -= critical * 20  # Critical gaps hurt most
    base_score -= warning * 10   # Warning gaps
    base_score -= info * 5       # Info gaps
    # Deduct for missing required documents (up to 20 points)
    if completeness.required_total > 0:
        doc_penalty = int((1 - completeness.required_present / completeness.required_total) * 20)
        base_score -= doc_penalty
    health_score_value = max(0, min(100, base_score))

    # Determine grade from score
    if health_score_value >= 90:
        health_grade = "A"
    elif health_score_value >= 80:
        health_grade = "B"
    elif health_score_value >= 70:
        health_grade = "C"
    elif health_score_value >= 60:
        health_grade = "D"
    else:
        health_grade = "F"

    health_score = HealthScoreSchema(
        score=health_score_value,
        grade=health_grade,
    )
    compliance_summary = ComplianceSummarySchema()

    # Build policies list
    today = date.today()
    policies_list = []
    for program in prop.insurance_programs:
        if program.status == "active":
            for policy in program.policies:
                # Determine policy status
                if policy.expiration_date:
                    if policy.expiration_date < today:
                        policy_status = "expired"
                    else:
                        policy_status = "active"
                else:
                    policy_status = "pending"

                # Get the largest coverage limit from coverages
                max_limit = None
                if policy.coverages:
                    for cov in policy.coverages:
                        if cov.limit_amount and (max_limit is None or cov.limit_amount > max_limit):
                            max_limit = cov.limit_amount

                # Get first deductible from coverages
                deductible = None
                if policy.coverages:
                    for cov in policy.coverages:
                        if cov.deductible_amount:
                            deductible = cov.deductible_amount
                            break

                policies_list.append(
                    PolicySummaryItem(
                        id=policy.id,
                        policy_number=policy.policy_number,
                        policy_type=policy.policy_type or "unknown",
                        carrier=policy.carrier_name,
                        effective_date=policy.effective_date,
                        expiration_date=policy.expiration_date,
                        premium=policy.premium,
                        limit=max_limit,
                        deductible=deductible,
                        status=policy_status,
                    )
                )

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
        total_buildings=len(prop.buildings) if prop.buildings else 0,
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
        policies=policies_list,
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
