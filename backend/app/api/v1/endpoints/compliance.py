"""Compliance API endpoints.

Provides lender compliance checking, requirement management, and templates.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.models.lender_requirement import LenderRequirement
from app.repositories.property_repository import PropertyRepository
from pydantic import BaseModel
from app.schemas.gap import (
    BatchComplianceItem,
    BatchComplianceRequest,
    BatchComplianceResponse,
    ComplianceCheckRequest,
    ComplianceCheckResult,
    ComplianceIssueSchema,
    ComplianceTemplateInfo,
    ComplianceTemplatesResponse,
    LenderRequirementCreate,
    LenderRequirementResponse,
    LenderRequirementUpdate,
    PropertyComplianceResponse,
)
from app.services.compliance_service import ComplianceService


class LiveComplianceCheckRequest(BaseModel):
    """Request for live compliance check using Parallel AI."""
    lender_name: str
    loan_type: str | None = None
    create_gaps: bool = True

router = APIRouter()


@router.post("/batch", response_model=BatchComplianceResponse)
async def batch_check_compliance(
    request: BatchComplianceRequest,
    db: AsyncSessionDep,
) -> BatchComplianceResponse:
    """Check compliance for multiple properties in a single request.

    This is much more efficient than calling get_property_compliance
    for each property individually. Use this for portfolio-wide compliance views.

    Args:
        request: List of property IDs to check.
        db: Database session.

    Returns:
        BatchComplianceResponse with compliance status for all properties.
    """
    service = ComplianceService(db)
    prop_repo = PropertyRepository(db)

    results: list[BatchComplianceItem] = []
    compliant_count = 0
    non_compliant_count = 0
    no_requirements_count = 0

    # Process all properties
    for property_id in request.property_ids:
        prop = await prop_repo.get_by_id(property_id)
        if not prop:
            continue

        # Run compliance checks for this property
        check_results = await service.check_compliance_for_property(
            property_id, create_gaps=request.create_gaps
        )

        # Build response item
        compliance_checks = []
        total_issues = 0
        overall_status = "compliant"

        for result in check_results:
            issues = [
                ComplianceIssueSchema(
                    check_name=i.check_name,
                    severity=i.severity,
                    message=i.message,
                    current_value=i.current_value,
                    required_value=i.required_value,
                )
                for i in result.issues
            ]
            total_issues += len(issues)

            # Track worst status
            if result.status == "non_compliant":
                overall_status = "non_compliant"
            elif result.status == "partial" and overall_status != "non_compliant":
                overall_status = "partial"

            compliance_checks.append(
                ComplianceCheckResult(
                    property_id=result.property_id,
                    lender_requirement_id=result.lender_requirement_id,
                    template_name=result.template_name,
                    status=result.status,
                    is_compliant=result.is_compliant,
                    issues=issues,
                    checked_at=datetime.now(timezone.utc),
                )
            )

        if not compliance_checks:
            overall_status = "no_requirements"
            no_requirements_count += 1
        elif overall_status == "compliant":
            compliant_count += 1
        else:
            non_compliant_count += 1

        results.append(
            BatchComplianceItem(
                property_id=property_id,
                property_name=prop.name,
                overall_status=overall_status,
                total_issues=total_issues,
                compliance_checks=compliance_checks,
            )
        )

    return BatchComplianceResponse(
        results=results,
        total_properties=len(results),
        compliant_count=compliant_count,
        non_compliant_count=non_compliant_count,
        no_requirements_count=no_requirements_count,
    )


@router.get("/templates", response_model=ComplianceTemplatesResponse)
async def get_compliance_templates(
    db: AsyncSessionDep,
) -> ComplianceTemplatesResponse:
    """Get list of available compliance templates.

    Templates can be used for quick compliance checks without
    setting up specific lender requirements.
    """
    service = ComplianceService(db)
    templates_info = service.get_available_templates()

    templates = [
        ComplianceTemplateInfo(
            name=t["name"],
            display_name=t["display_name"],
            description=t["description"],
        )
        for t in templates_info
    ]

    return ComplianceTemplatesResponse(templates=templates)


@router.get("/properties/{property_id}", response_model=PropertyComplianceResponse)
async def get_property_compliance(
    property_id: str,
    db: AsyncSessionDep,
) -> PropertyComplianceResponse:
    """Get compliance status for a property.

    Returns compliance check results against all lender requirements
    associated with this property.
    """
    # Verify property exists
    prop_repo = PropertyRepository(db)
    prop = await prop_repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    # Run compliance checks
    service = ComplianceService(db)
    results = await service.check_compliance_for_property(
        property_id, create_gaps=False  # Don't create gaps on read
    )

    # Build response
    compliance_checks = []
    total_issues = 0
    overall_status = "compliant"

    for result in results:
        issues = [
            ComplianceIssueSchema(
                check_name=i.check_name,
                severity=i.severity,
                message=i.message,
                current_value=i.current_value,
                required_value=i.required_value,
            )
            for i in result.issues
        ]
        total_issues += len(issues)

        # Track worst status
        if result.status == "non_compliant":
            overall_status = "non_compliant"
        elif result.status == "partial" and overall_status != "non_compliant":
            overall_status = "partial"

        compliance_checks.append(
            ComplianceCheckResult(
                property_id=result.property_id,
                lender_requirement_id=result.lender_requirement_id,
                template_name=result.template_name,
                status=result.status,
                is_compliant=result.is_compliant,
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )
        )

    if not compliance_checks:
        overall_status = "no_requirements"

    return PropertyComplianceResponse(
        property_id=property_id,
        property_name=prop.name,
        compliance_checks=compliance_checks,
        overall_status=overall_status,
        total_issues=total_issues,
    )


@router.post("/properties/{property_id}/check", response_model=PropertyComplianceResponse)
async def check_property_compliance(
    property_id: str,
    request: ComplianceCheckRequest,
    db: AsyncSessionDep,
) -> PropertyComplianceResponse:
    """Manually trigger compliance check for a property.

    Can check against:
    - All lender requirements (default)
    - A specific template (template_name parameter)

    When create_gaps=True (default), creates CoverageGap records for issues.
    """
    # Verify property exists
    prop_repo = PropertyRepository(db)
    prop = await prop_repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    service = ComplianceService(db)
    compliance_checks = []
    total_issues = 0
    overall_status = "compliant"

    if request.template_name:
        # Check against specific template
        try:
            result = await service.check_against_template(
                property_id, request.template_name
            )
            issues = [
                ComplianceIssueSchema(
                    check_name=i.check_name,
                    severity=i.severity,
                    message=i.message,
                    current_value=i.current_value,
                    required_value=i.required_value,
                )
                for i in result.issues
            ]
            total_issues = len(issues)
            overall_status = result.status

            compliance_checks.append(
                ComplianceCheckResult(
                    property_id=result.property_id,
                    lender_requirement_id=None,
                    template_name=result.template_name,
                    status=result.status,
                    is_compliant=result.is_compliant,
                    issues=issues,
                    checked_at=datetime.now(timezone.utc),
                )
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    else:
        # Check against all lender requirements
        results = await service.check_compliance_for_property(
            property_id, create_gaps=request.create_gaps
        )

        for result in results:
            issues = [
                ComplianceIssueSchema(
                    check_name=i.check_name,
                    severity=i.severity,
                    message=i.message,
                    current_value=i.current_value,
                    required_value=i.required_value,
                )
                for i in result.issues
            ]
            total_issues += len(issues)

            if result.status == "non_compliant":
                overall_status = "non_compliant"
            elif result.status == "partial" and overall_status != "non_compliant":
                overall_status = "partial"

            compliance_checks.append(
                ComplianceCheckResult(
                    property_id=result.property_id,
                    lender_requirement_id=result.lender_requirement_id,
                    template_name=result.template_name,
                    status=result.status,
                    is_compliant=result.is_compliant,
                    issues=issues,
                    checked_at=datetime.now(timezone.utc),
                )
            )

    if not compliance_checks:
        overall_status = "no_requirements"

    await db.commit()

    return PropertyComplianceResponse(
        property_id=property_id,
        property_name=prop.name,
        compliance_checks=compliance_checks,
        overall_status=overall_status,
        total_issues=total_issues,
    )


@router.post("/properties/{property_id}/check-live", response_model=ComplianceCheckResult)
async def check_compliance_with_live_requirements(
    property_id: str,
    request: LiveComplianceCheckRequest,
    db: AsyncSessionDep,
) -> ComplianceCheckResult:
    """Check compliance using LIVE lender requirements from Parallel AI.

    This endpoint:
    1. Fetches real-time lender requirements via Parallel AI web research
    2. Checks property insurance against those live requirements
    3. Optionally creates CoverageGap records for any issues found

    This is useful for checking compliance against lenders not in the database,
    or to get the most up-to-date requirements for known lenders.

    Note: This operation may take 30-120 seconds due to web research.
    """
    # Verify property exists
    prop_repo = PropertyRepository(db)
    prop = await prop_repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    service = ComplianceService(db)

    try:
        result = await service.check_compliance_with_live_requirements(
            property_id=property_id,
            lender_name=request.lender_name,
            loan_type=request.loan_type,
            create_gaps=request.create_gaps,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Build response
    issues = [
        ComplianceIssueSchema(
            check_name=i.check_name,
            severity=i.severity,
            message=i.message,
            current_value=i.current_value,
            required_value=i.required_value,
        )
        for i in result.issues
    ]

    await db.commit()

    return ComplianceCheckResult(
        property_id=result.property_id,
        lender_requirement_id=None,  # Live check, no DB requirement
        template_name=result.template_name,
        status=result.status,
        is_compliant=result.is_compliant,
        issues=issues,
        checked_at=datetime.now(timezone.utc),
    )


@router.get("/properties/{property_id}/requirements", response_model=list[LenderRequirementResponse])
async def get_lender_requirements(
    property_id: str,
    db: AsyncSessionDep,
) -> list[LenderRequirementResponse]:
    """Get all lender requirements for a property."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Verify property exists
    prop_repo = PropertyRepository(db)
    prop = await prop_repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    stmt = (
        select(LenderRequirement)
        .options(selectinload(LenderRequirement.lender))
        .where(
            LenderRequirement.property_id == property_id,
            LenderRequirement.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    requirements = result.scalars().all()

    return [
        LenderRequirementResponse(
            id=req.id,
            property_id=req.property_id,
            lender_id=req.lender_id,
            lender_name=req.lender.name if req.lender else None,
            loan_number=req.loan_number,
            loan_amount=req.loan_amount,
            min_property_limit=req.min_property_limit,
            min_gl_limit=req.min_gl_limit,
            min_umbrella_limit=req.min_umbrella_limit,
            max_deductible_amount=req.max_deductible_amount,
            max_deductible_pct=req.max_deductible_pct,
            requires_flood=req.requires_flood,
            requires_earthquake=req.requires_earthquake,
            requires_terrorism=req.requires_terrorism,
            compliance_status=req.compliance_status,
            compliance_checked_at=req.compliance_checked_at,
            created_at=req.created_at,
            updated_at=req.updated_at,
        )
        for req in requirements
    ]


@router.post("/properties/{property_id}/requirements", response_model=LenderRequirementResponse)
async def create_lender_requirement(
    property_id: str,
    request: LenderRequirementCreate,
    db: AsyncSessionDep,
) -> LenderRequirementResponse:
    """Create a new lender requirement for a property."""
    from uuid import uuid4

    # Verify property exists
    prop_repo = PropertyRepository(db)
    prop = await prop_repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_id} not found",
        )

    # Create requirement
    requirement = LenderRequirement(
        id=str(uuid4()),
        property_id=property_id,
        lender_id=request.lender_id,
        loan_number=request.loan_number,
        loan_amount=request.loan_amount,
        min_property_limit=request.min_property_limit,
        min_gl_limit=request.min_gl_limit,
        min_umbrella_limit=request.min_umbrella_limit,
        max_deductible_amount=request.max_deductible_amount,
        max_deductible_pct=request.max_deductible_pct,
        requires_flood=request.requires_flood,
        requires_earthquake=request.requires_earthquake,
        requires_terrorism=request.requires_terrorism,
    )
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)

    return LenderRequirementResponse(
        id=requirement.id,
        property_id=requirement.property_id,
        lender_id=requirement.lender_id,
        lender_name=None,
        loan_number=requirement.loan_number,
        loan_amount=requirement.loan_amount,
        min_property_limit=requirement.min_property_limit,
        min_gl_limit=requirement.min_gl_limit,
        min_umbrella_limit=requirement.min_umbrella_limit,
        max_deductible_amount=requirement.max_deductible_amount,
        max_deductible_pct=requirement.max_deductible_pct,
        requires_flood=requirement.requires_flood,
        requires_earthquake=requirement.requires_earthquake,
        requires_terrorism=requirement.requires_terrorism,
        compliance_status=requirement.compliance_status,
        compliance_checked_at=requirement.compliance_checked_at,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


@router.put("/properties/{property_id}/requirements/{requirement_id}", response_model=LenderRequirementResponse)
async def update_lender_requirement(
    property_id: str,
    requirement_id: str,
    request: LenderRequirementUpdate,
    db: AsyncSessionDep,
) -> LenderRequirementResponse:
    """Update a lender requirement."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    stmt = (
        select(LenderRequirement)
        .options(selectinload(LenderRequirement.lender))
        .where(
            LenderRequirement.id == requirement_id,
            LenderRequirement.property_id == property_id,
            LenderRequirement.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender requirement {requirement_id} not found",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(requirement, field, value)

    # Clear compliance status since requirements changed
    requirement.compliance_status = None
    requirement.compliance_checked_at = None

    await db.commit()
    await db.refresh(requirement)

    return LenderRequirementResponse(
        id=requirement.id,
        property_id=requirement.property_id,
        lender_id=requirement.lender_id,
        lender_name=requirement.lender.name if requirement.lender else None,
        loan_number=requirement.loan_number,
        loan_amount=requirement.loan_amount,
        min_property_limit=requirement.min_property_limit,
        min_gl_limit=requirement.min_gl_limit,
        min_umbrella_limit=requirement.min_umbrella_limit,
        max_deductible_amount=requirement.max_deductible_amount,
        max_deductible_pct=requirement.max_deductible_pct,
        requires_flood=requirement.requires_flood,
        requires_earthquake=requirement.requires_earthquake,
        requires_terrorism=requirement.requires_terrorism,
        compliance_status=requirement.compliance_status,
        compliance_checked_at=requirement.compliance_checked_at,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )


@router.delete("/properties/{property_id}/requirements/{requirement_id}")
async def delete_lender_requirement(
    property_id: str,
    requirement_id: str,
    db: AsyncSessionDep,
) -> dict:
    """Delete a lender requirement."""
    from sqlalchemy import select

    stmt = select(LenderRequirement).where(
        LenderRequirement.id == requirement_id,
        LenderRequirement.property_id == property_id,
        LenderRequirement.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender requirement {requirement_id} not found",
        )

    # Soft delete
    requirement.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Lender requirement deleted successfully"}
