"""Document ingestion API endpoints."""

import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentResponse, IngestRequest, IngestResponse
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    request: IngestRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Ingest a document from a local file path.

    This endpoint processes a document through the ingestion pipeline:
    1. OCR (Mistral) - Extract text from PDF/image
    2. Classification - Determine document type
    3. Extraction - Extract structured data

    Args:
        request: Ingest request with file path and organization ID.
        db: Database session.

    Returns:
        IngestResponse with document ID and extraction results.
    """
    # Validate file exists
    file_path = Path(request.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail=f"Path is not a file: {request.file_path}")

    # Process document
    service = IngestionService(db)

    try:
        result = await service.ingest_file(
            file_path=request.file_path,
            organization_id=request.organization_id,
            property_id=request.property_id,
        )
        await db.commit()
        return result

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=IngestResponse)
async def upload_and_ingest_document(
    file: UploadFile = File(...),
    organization_id: str = Form(...),
    property_id: str | None = Form(None),
    program_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Upload and ingest a document.

    This endpoint accepts a file upload, saves it locally, and processes it
    through the ingestion pipeline.

    Args:
        file: Uploaded file.
        organization_id: Organization ID.
        property_id: Optional property ID.
        program_id: Optional insurance program ID.
        db: Database session.

    Returns:
        IngestResponse with document ID and extraction results.
    """
    # Validate file type
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}",
        )

    # Create upload directory if needed
    upload_dir = Path(settings.local_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    try:
        # Create a temp file, then move to final location
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_ext,
            dir=upload_dir,
        ) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = Path(tmp_file.name)

        # Rename to include original filename
        final_path = upload_dir / f"{temp_path.stem}_{file.filename}"
        temp_path.rename(final_path)

        logger.info(f"Saved uploaded file to: {final_path}")

    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Process document
    service = IngestionService(db)

    try:
        result = await service.ingest_file(
            file_path=str(final_path),
            organization_id=organization_id,
            property_id=property_id,
            program_id=program_id,
        )
        await db.commit()
        return result

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get a document by ID.

    Args:
        document_id: Document ID.
        db: Database session.

    Returns:
        Document details.
    """
    repo = DocumentRepository(db)
    document = await repo.get_by_id(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(
        id=document.id,
        file_name=document.file_name,
        file_url=document.file_url,
        document_type=document.document_type,
        document_subtype=document.document_subtype,
        carrier=document.carrier,
        policy_number=document.policy_number,
        effective_date=document.effective_date,
        expiration_date=document.expiration_date,
        upload_status=document.upload_status,
        ocr_status=document.ocr_status,
        extraction_status=document.extraction_status,
        extraction_confidence=document.extraction_confidence,
        needs_human_review=document.needs_human_review,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get("/{document_id}/extraction")
async def get_document_extraction(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get extraction results for a document.

    Args:
        document_id: Document ID.
        db: Database session.

    Returns:
        Extracted data as JSON.
    """
    repo = DocumentRepository(db)
    document = await repo.get_by_id(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.extraction_json is None:
        raise HTTPException(status_code=404, detail="No extraction data available")

    return document.extraction_json


@router.get("/{document_id}/text")
async def get_document_text(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get OCR text for a document.

    Args:
        document_id: Document ID.
        db: Database session.

    Returns:
        OCR markdown text.
    """
    repo = DocumentRepository(db)
    document = await repo.get_by_id(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.ocr_markdown is None:
        raise HTTPException(status_code=404, detail="No OCR text available")

    return {
        "document_id": document.id,
        "file_name": document.file_name,
        "page_count": document.page_count,
        "text": document.ocr_markdown,
    }
