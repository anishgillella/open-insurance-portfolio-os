"""Property API endpoints.

Provides property listing, detail views, and related data access.
"""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.repositories.policy_repository import PolicyRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.valuation_repository import ValuationRepository
from app.schemas.common import AddressSchema
from app.schemas.policy import PolicyListItem, PropertyPoliciesResponse, PropertyPolicySummary
from app.schemas.property import (
    BuildingSchema,
    CertificateExtractionSummary,
    ComplianceSummarySchema,
    CompletenessSummarySchema,
    CoverageExtractionSummary,
    DocumentChecklistItem,
    DocumentExtractionSummary,
    ExtractedFieldValue,
    ExtractedFieldWithSources,
    FinancialExtractionSummary,
    GapsCountSchema,
    GapsSummarySchema,
    HealthScoreSchema,
    InsuranceSummarySchema,
    PolicyExtractionSummary,
    PolicySummaryItem,
    PropertyDetail,
    PropertyDocumentItem,
    PropertyDocumentsResponse,
    PropertyExtractedDataResponse,
    PropertyListItem,
    PropertyListResponse,
    ValuationSummary,
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

    # Count documents
    document_count = len(prop.documents) if hasattr(prop, 'documents') and prop.documents else 0

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
        document_count=document_count,
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


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: str,
    db: AsyncSessionDep,
) -> None:
    """Delete a property and all related data.

    Performs a soft delete (sets deleted_at timestamp) on the property
    and cascades to related documents, gaps, policies, and programs.
    """
    repo = PropertyRepository(db)

    # Verify property exists
    prop = await repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    # Soft delete the property (cascade will handle related records)
    deleted = await repo.delete(property_id, soft=True)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete property",
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


# Field display name mapping for extracted data
FIELD_DISPLAY_NAMES = {
    # Property fields
    "year_built": "Year Built",
    "construction_type": "Construction Type",
    "square_footage": "Square Footage",
    "stories": "Number of Stories",
    "units": "Number of Units",
    "occupancy": "Occupancy Type",
    "address": "Address",
    "city": "City",
    "state": "State",
    "zip_code": "ZIP Code",
    "property_type": "Property Type",
    "roof_type": "Roof Type",
    "roof_year": "Roof Year",
    "sprinkler_type": "Sprinkler Type",
    "has_sprinklers": "Has Sprinklers",
    "protection_class": "Protection Class",
    "flood_zone": "Flood Zone",
    "earthquake_zone": "Earthquake Zone",
    "wind_zone": "Wind Zone",
    # Valuation fields
    "building_value": "Building Value",
    "contents_value": "Contents Value",
    "business_income_value": "Business Income Value",
    "total_insured_value": "Total Insured Value (TIV)",
    "price_per_sqft": "Price per Sq Ft",
    # Policy fields
    "policy_number": "Policy Number",
    "carrier_name": "Carrier",
    "effective_date": "Effective Date",
    "expiration_date": "Expiration Date",
    "premium": "Premium",
    "named_insured": "Named Insured",
    # Coverage fields
    "limit_amount": "Limit Amount",
    "deductible_amount": "Deductible",
    # Certificate fields
    "producer_name": "Producer/Broker",
    "holder_name": "Certificate Holder",
    "gl_each_occurrence": "GL Each Occurrence",
    "gl_general_aggregate": "GL General Aggregate",
    "property_limit": "Property Limit",
    "umbrella_limit": "Umbrella Limit",
}


def _flatten_extraction_json(extraction_json: dict, doc_type: str) -> dict:
    """Flatten nested extraction JSON into a simple key-value dict."""
    result = {}
    if not extraction_json:
        return result

    # Handle different document type structures
    if doc_type and doc_type.lower() == "coi":
        coi_data = extraction_json.get("coi") or extraction_json
        for key in ["producer_name", "insured_name", "holder_name", "effective_date",
                    "expiration_date", "gl_each_occurrence", "gl_general_aggregate",
                    "property_limit", "umbrella_limit", "certificate_number"]:
            if key in coi_data and coi_data[key] is not None:
                result[key] = coi_data[key]

    elif doc_type and doc_type.lower() == "eop":
        eop_data = extraction_json.get("eop") or extraction_json
        for key in ["producer_name", "insured_name", "property_limit",
                    "effective_date", "expiration_date"]:
            if key in eop_data and eop_data[key] is not None:
                result[key] = eop_data[key]

    elif doc_type and doc_type.lower() == "sov":
        sov_data = extraction_json.get("sov") or extraction_json
        if sov_data.get("total_insured_value"):
            result["total_insured_value"] = sov_data["total_insured_value"]
        # Get first property details
        props = sov_data.get("properties", [])
        if props and len(props) > 0:
            prop = props[0]
            for key in ["year_built", "construction_type", "square_footage", "stories",
                        "building_value", "contents_value", "business_income_value"]:
                if key in prop and prop[key] is not None:
                    result[key] = prop[key]

    elif doc_type and doc_type.lower() == "invoice":
        inv_data = extraction_json.get("invoice") or extraction_json
        for key in ["total_amount", "taxes", "fees", "invoice_date", "due_date"]:
            if key in inv_data and inv_data[key] is not None:
                result[key] = inv_data[key]

    elif doc_type and doc_type.lower() == "policy":
        policy_data = extraction_json.get("policy") or extraction_json
        for key in ["policy_number", "carrier_name", "effective_date", "expiration_date",
                    "premium", "named_insured", "policy_type"]:
            if key in policy_data and policy_data[key] is not None:
                result[key] = policy_data[key]

    elif doc_type and doc_type.lower() == "proposal":
        prop_data = extraction_json.get("proposal") or extraction_json
        for key in ["effective_date", "expiration_date", "total_premium",
                    "total_insured_value"]:
            if key in prop_data and prop_data[key] is not None:
                result[key] = prop_data[key]
        # Get properties data
        props = prop_data.get("properties", [])
        if props and len(props) > 0:
            prop = props[0]
            for key in ["unit_count", "total_insured_value", "renewal_tiv"]:
                if key in prop and prop[key] is not None:
                    if key == "unit_count":
                        result["units"] = prop[key]
                    else:
                        result[key] = prop[key]

    # Also try to extract from root level for any document type
    for key in ["year_built", "construction_type", "square_footage", "stories",
                "units", "total_insured_value", "building_value", "contents_value"]:
        if key in extraction_json and extraction_json[key] is not None and key not in result:
            result[key] = extraction_json[key]

    return result


@router.get("/{property_id}/extracted-data", response_model=PropertyExtractedDataResponse)
async def get_property_extracted_data(
    property_id: str,
    db: AsyncSessionDep,
) -> PropertyExtractedDataResponse:
    """Get all extracted data for a property from all documents.

    Returns comprehensive extraction data including:
    - All extracted fields with source document references
    - Valuations from SOV/appraisals
    - Policies with coverages
    - Certificates (COI/EOP)
    - Financial records (invoices)
    - Per-document extraction breakdown
    """
    repo = PropertyRepository(db)
    valuation_repo = ValuationRepository(db)
    policy_repo = PolicyRepository(db)

    # Verify property exists
    prop = await repo.get_with_details(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    # Get all documents for this property
    documents = await repo.get_documents_by_property(property_id, limit=500)

    # Build field aggregation dict: field_name -> list of values with sources
    field_values: dict[str, list[ExtractedFieldValue]] = {}
    document_extractions: list[DocumentExtractionSummary] = []
    last_extraction_at = None
    docs_with_extractions = 0

    for doc in documents:
        if doc.deleted_at is not None:
            continue

        # Track extraction timestamp
        if doc.extraction_completed_at:
            if last_extraction_at is None or doc.extraction_completed_at > last_extraction_at:
                last_extraction_at = doc.extraction_completed_at

        # Flatten extraction JSON
        extracted_fields = {}
        if doc.extraction_json:
            docs_with_extractions += 1
            extracted_fields = _flatten_extraction_json(
                doc.extraction_json, doc.document_type
            )

            # Add each field to aggregation
            for field_name, value in extracted_fields.items():
                if value is None:
                    continue

                field_value = ExtractedFieldValue(
                    value=value,
                    source_document_id=doc.id,
                    source_document_name=doc.file_name or "Unknown",
                    source_document_type=doc.document_type,
                    extraction_confidence=doc.extraction_confidence,
                    extracted_at=doc.extraction_completed_at,
                )

                if field_name not in field_values:
                    field_values[field_name] = []
                field_values[field_name].append(field_value)

        # Build document extraction summary
        document_extractions.append(
            DocumentExtractionSummary(
                document_id=doc.id,
                document_name=doc.file_name or "Unknown",
                document_type=doc.document_type,
                uploaded_at=doc.created_at,
                extraction_confidence=doc.extraction_confidence,
                extracted_fields=extracted_fields,
            )
        )

    # Build extracted fields with sources list
    extracted_fields_list: list[ExtractedFieldWithSources] = []
    for field_name, values in field_values.items():
        # Determine category based on field name
        if field_name in ["building_value", "contents_value", "business_income_value",
                         "total_insured_value", "price_per_sqft"]:
            category = "valuation"
        elif field_name in ["policy_number", "carrier_name", "premium", "named_insured"]:
            category = "policy"
        elif field_name in ["gl_each_occurrence", "gl_general_aggregate", "property_limit",
                           "umbrella_limit", "producer_name", "holder_name"]:
            category = "coverage"
        else:
            category = "property"

        # Consolidated value is the most recent or highest confidence
        consolidated = values[0].value if values else None
        if len(values) > 1:
            # Sort by extraction date (newest first) then confidence
            sorted_values = sorted(
                values,
                key=lambda v: (v.extracted_at or date.min, v.extraction_confidence or 0),
                reverse=True,
            )
            consolidated = sorted_values[0].value

        extracted_fields_list.append(
            ExtractedFieldWithSources(
                field_name=field_name,
                display_name=FIELD_DISPLAY_NAMES.get(field_name, field_name.replace("_", " ").title()),
                category=category,
                values=values,
                consolidated_value=consolidated,
            )
        )

    # Sort by category then field name
    extracted_fields_list.sort(key=lambda f: (f.category, f.field_name))

    # Get valuations
    valuations_db = await valuation_repo.get_by_property(property_id)
    valuations: list[ValuationSummary] = []
    for v in valuations_db:
        # Find source document name
        doc_name = None
        for doc in documents:
            if doc.id == v.document_id:
                doc_name = doc.file_name
                break

        valuations.append(
            ValuationSummary(
                id=v.id,
                valuation_date=v.valuation_date,
                valuation_source=v.valuation_source,
                building_value=v.building_value,
                contents_value=v.contents_value,
                business_income_value=v.business_income_value,
                total_insured_value=v.total_insured_value,
                price_per_sqft=v.price_per_sqft,
                sq_ft_used=v.sq_ft_used,
                source_document_id=v.document_id,
                source_document_name=doc_name,
            )
        )

    # Get policies with coverages
    policies_db = await policy_repo.get_by_property(property_id)
    policies: list[PolicyExtractionSummary] = []
    for p in policies_db:
        # Find source document name
        doc_name = None
        for doc in documents:
            if doc.id == p.document_id:
                doc_name = doc.file_name
                break

        coverages: list[CoverageExtractionSummary] = []
        if p.coverages:
            for c in p.coverages:
                cov_doc_name = None
                for doc in documents:
                    if doc.id == c.source_document_id:
                        cov_doc_name = doc.file_name
                        break

                coverages.append(
                    CoverageExtractionSummary(
                        coverage_name=c.coverage_name or "Unknown",
                        coverage_category=c.coverage_category,
                        limit_amount=c.limit_amount,
                        limit_type=c.limit_type,
                        deductible_amount=c.deductible_amount,
                        deductible_type=c.deductible_type,
                        source_document_id=c.source_document_id,
                        source_document_name=cov_doc_name,
                    )
                )

        policies.append(
            PolicyExtractionSummary(
                id=p.id,
                policy_type=p.policy_type or "unknown",
                policy_number=p.policy_number,
                carrier_name=p.carrier_name,
                effective_date=p.effective_date,
                expiration_date=p.expiration_date,
                premium=p.premium,
                coverages=coverages,
                source_document_id=p.document_id,
                source_document_name=doc_name,
            )
        )

    # Get certificates (from insurance programs)
    certificates: list[CertificateExtractionSummary] = []
    for program in prop.insurance_programs:
        if hasattr(program, "certificates"):
            for cert in program.certificates:
                doc_name = None
                for doc in documents:
                    if doc.id == cert.document_id:
                        doc_name = doc.file_name
                        break

                certificates.append(
                    CertificateExtractionSummary(
                        id=cert.id,
                        certificate_type=cert.certificate_type or "coi",
                        certificate_number=cert.certificate_number,
                        producer_name=cert.producer_name,
                        insured_name=cert.insured_name,
                        holder_name=cert.holder_name,
                        effective_date=cert.effective_date,
                        expiration_date=cert.expiration_date,
                        gl_each_occurrence=cert.gl_each_occurrence,
                        gl_general_aggregate=cert.gl_general_aggregate,
                        property_limit=cert.property_limit,
                        umbrella_limit=cert.umbrella_limit,
                        source_document_id=cert.document_id,
                        source_document_name=doc_name,
                    )
                )

    # Get financials
    financials: list[FinancialExtractionSummary] = []
    for program in prop.insurance_programs:
        if hasattr(program, "financials"):
            for fin in program.financials:
                doc_name = None
                for doc in documents:
                    if doc.id == fin.document_id:
                        doc_name = doc.file_name
                        break

                financials.append(
                    FinancialExtractionSummary(
                        id=fin.id,
                        record_type=fin.record_type or "invoice",
                        total=fin.total,
                        taxes=fin.taxes,
                        fees=fin.fees,
                        invoice_date=fin.invoice_date,
                        due_date=fin.due_date,
                        source_document_id=fin.document_id,
                        source_document_name=doc_name,
                    )
                )

    return PropertyExtractedDataResponse(
        property_id=prop.id,
        property_name=prop.name,
        extracted_fields=extracted_fields_list,
        valuations=valuations,
        policies=policies,
        certificates=certificates,
        financials=financials,
        document_extractions=document_extractions,
        total_documents=len(documents),
        documents_with_extractions=docs_with_extractions,
        last_extraction_at=last_extraction_at,
    )
