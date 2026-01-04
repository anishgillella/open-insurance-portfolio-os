"""Document Completeness API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AsyncSessionDep
from app.schemas.completeness import (
    CompletenessResponse,
    CompletenessDataSchema,
    PortfolioCompletenessResponse,
    PortfolioCompletenessPropertySchema,
    MissingDocumentSummarySchema,
    MissingDocumentImpactSchema,
    MarkNotApplicableRequest,
    MarkNotApplicableResponse,
)
from app.services.completeness_service import CompletenessService

router = APIRouter()


@router.get("/properties/{property_id}", response_model=CompletenessResponse)
async def get_property_completeness(
    property_id: str,
    db: AsyncSessionDep,
    include_llm_analysis: bool = Query(True, description="Include LLM impact analysis"),
) -> CompletenessResponse:
    """Get document completeness for a property.

    Calculates what documents are present vs expected and provides
    LLM-generated impact analysis for missing documents.

    Args:
        property_id: Property ID.
        include_llm_analysis: Whether to include LLM analysis.

    Returns:
        CompletenessResponse with completeness data and optional LLM insights.
    """
    service = CompletenessService(db)

    try:
        result = await service.get_completeness(property_id, include_llm_analysis)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {property_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # Convert to response schema
    return CompletenessResponse(
        property_id=result.property_id,
        property_name=result.property_name,
        completeness=CompletenessDataSchema(
            percentage=result.percentage,
            grade=result.grade,
            required_present=result.required_present,
            required_total=result.required_total,
            optional_present=result.optional_present,
            optional_total=result.optional_total,
        ),
        documents={
            "required": [
                {
                    "type": d.type,
                    "label": d.label,
                    "status": d.status,
                    "document_id": d.document_id,
                    "filename": d.filename,
                    "importance": d.importance,
                    "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
                }
                for d in result.required_documents
            ],
            "optional": [
                {
                    "type": d.type,
                    "label": d.label,
                    "status": d.status,
                    "document_id": d.document_id,
                    "filename": d.filename,
                    "importance": d.importance,
                    "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
                }
                for d in result.optional_documents
            ],
        },
        missing_document_impacts=[
            MissingDocumentImpactSchema(
                document=impact.document,
                impact=impact.impact,
                priority=impact.priority,
                reason=impact.reason,
            )
            for impact in (result.missing_document_impacts or [])
        ] if result.missing_document_impacts else None,
        overall_risk_summary=result.overall_risk_summary,
        recommended_actions=result.recommended_actions,
        llm_analyzed=result.llm_analyzed,
        calculated_at=datetime.now(timezone.utc),
    )


@router.get("/summary", response_model=PortfolioCompletenessResponse)
async def get_portfolio_completeness(
    db: AsyncSessionDep,
    organization_id: str | None = Query(None, description="Filter by organization"),
) -> PortfolioCompletenessResponse:
    """Get document completeness summary across all properties.

    Aggregates completeness data for the entire portfolio.

    Args:
        organization_id: Optional organization filter.

    Returns:
        PortfolioCompletenessResponse with aggregated data.
    """
    service = CompletenessService(db)
    result = await service.get_portfolio_completeness(organization_id)

    return PortfolioCompletenessResponse(
        summary={
            "average_completeness": result.average_completeness,
            "fully_complete_count": result.fully_complete_count,
            "missing_required_count": result.missing_required_count,
            "total_properties": result.total_properties,
        },
        distribution=result.distribution,
        most_common_missing=[
            MissingDocumentSummarySchema(
                type=item["type"],
                label=item["label"],
                missing_count=item["missing_count"],
                percentage_missing=item["percentage_missing"],
            )
            for item in result.most_common_missing
        ],
        properties=[
            PortfolioCompletenessPropertySchema(
                id=prop["id"],
                name=prop["name"],
                completeness=prop["completeness"],
                grade=prop["grade"],
                missing_required=prop["missing_required"],
                missing_optional=prop["missing_optional"],
            )
            for prop in result.properties
        ],
    )


@router.post("/properties/{property_id}/not-applicable", response_model=MarkNotApplicableResponse)
async def mark_not_applicable(
    property_id: str,
    request: MarkNotApplicableRequest,
    db: AsyncSessionDep,
) -> MarkNotApplicableResponse:
    """Mark a document type as not applicable for a property.

    This excludes the document from completeness calculations.

    Args:
        property_id: Property ID.
        request: Document type and reason.

    Returns:
        MarkNotApplicableResponse confirming the action.
    """
    # TODO: Implement N/A tracking in a separate table or Property JSONB field
    # For now, return a placeholder response
    return MarkNotApplicableResponse(
        property_id=property_id,
        document_type=request.document_type,
        status="not_applicable",
        reason=request.reason,
        marked_at=datetime.now(timezone.utc),
    )
