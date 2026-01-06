"""Document ingestion API endpoints."""

import asyncio
import logging
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    DocumentClassification,
    DocumentResponse,
    ExtractionResult,
    IngestDirectoryRequest,
    IngestDirectoryResponse,
    IngestRequest,
    IngestResponse,
)
from app.services.classification_service import get_classification_service
from app.services.extraction_service import get_extraction_service
from app.services.ingestion_service import IngestionService
from app.services.ocr_service import get_ocr_service

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentListResponse(BaseModel):
    """Response for document list."""

    documents: list[DocumentResponse]
    total: int


class AsyncUploadResponse(BaseModel):
    """Response from async document upload."""

    document_id: str
    file_name: str
    status: str  # "pending", "processing", "completed", "failed"
    message: str


# Background processing tasks storage (in production, use Redis or similar)
_background_tasks: dict[str, asyncio.Task] = {}


async def process_document_background(
    document_id: str,
    file_path: str,
    organization_id: str,
    property_name: str,
    property_id: str | None,
    program_id: str | None,
) -> None:
    """Process a document in the background.

    Creates its own database session since this runs outside the request context.
    """
    from app.core.database import async_session_maker

    logger.info(f"[BACKGROUND] Starting processing for document {document_id}")

    async with async_session_maker() as db:
        try:
            # Get the document record
            repo = DocumentRepository(db)
            document = await repo.get_by_id(document_id)

            if not document:
                logger.error(f"[BACKGROUND] Document {document_id} not found")
                return

            # Update status to processing
            document.upload_status = "processing"
            await db.commit()

            # Process using ingestion service
            service = IngestionService(db)
            result = await service.ingest_file(
                file_path=file_path,
                organization_id=organization_id,
                property_name=property_name,
                property_id=property_id,
                program_id=program_id,
                existing_document_id=document_id,
            )

            # Update upload_status to completed after successful processing
            document = await repo.get_by_id(document_id)
            if document:
                document.upload_status = "completed"

            await db.commit()
            logger.info(f"[BACKGROUND] Completed processing for document {document_id}: {result.status}")

        except Exception as e:
            logger.error(f"[BACKGROUND] Failed processing document {document_id}: {e}")
            try:
                # Update status to failed
                document = await repo.get_by_id(document_id)
                if document:
                    document.upload_status = "failed"
                    document.extraction_status = "failed"
                    await db.commit()
            except Exception as commit_err:
                logger.error(f"[BACKGROUND] Failed to update status: {commit_err}")
        finally:
            # Clean up task reference
            if document_id in _background_tasks:
                del _background_tasks[document_id]


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    organization_id: str | None = None,
    property_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List all documents.

    Args:
        organization_id: Optional filter by organization.
        property_id: Optional filter by property.
        db: Database session.

    Returns:
        List of documents.
    """
    repo = DocumentRepository(db)
    documents_with_names = await repo.list_all_with_property_names(
        organization_id=organization_id,
        property_id=property_id,
    )

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                file_name=doc.file_name,
                file_url=doc.file_url,
                document_type=doc.document_type,
                document_subtype=doc.document_subtype,
                carrier=doc.carrier,
                policy_number=doc.policy_number,
                effective_date=doc.effective_date,
                expiration_date=doc.expiration_date,
                upload_status=doc.upload_status,
                ocr_status=doc.ocr_status,
                extraction_status=doc.extraction_status,
                extraction_confidence=doc.extraction_confidence,
                needs_human_review=doc.needs_human_review,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                property_id=doc.property_id,
                property_name=prop_name,
            )
            for doc, prop_name in documents_with_names
        ],
        total=len(documents_with_names),
    )


class ProcessRequest(BaseModel):
    """Request to process a document from a file path."""

    file_path: str


class ProcessResponse(BaseModel):
    """Response from document processing (without database)."""

    file_name: str
    page_count: int
    classification: DocumentClassification
    extraction: dict[str, Any] | None = None
    ocr_text: str | None = None
    errors: list[str] = []


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
            property_name=request.property_name,
            property_id=request.property_id,
        )
        await db.commit()
        return result

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-directory", response_model=IngestDirectoryResponse)
async def ingest_directory(
    request: IngestDirectoryRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestDirectoryResponse:
    """Ingest all documents in a directory.

    This endpoint processes all PDF/image files in a directory through the
    full ingestion pipeline: OCR → Classification → Extraction → Storage.

    Args:
        request: Directory ingest request with path and organization ID.
        db: Database session.

    Returns:
        IngestDirectoryResponse with results for each file.
    """
    # Validate directory exists
    directory_path = Path(request.directory_path)
    if not directory_path.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory_path}")

    if not directory_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.directory_path}")

    # Process directory
    service = IngestionService(db)

    try:
        results = await service.ingest_directory(
            directory_path=request.directory_path,
            organization_id=request.organization_id,
            property_name=request.property_name,
            property_id=request.property_id,
            program_id=request.program_id,
            force_reprocess=request.force_reprocess,
        )
        await db.commit()

        # Calculate summary
        successful = sum(1 for r in results if r.status == "completed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")

        return IngestDirectoryResponse(
            directory_path=request.directory_path,
            total_files=len(results),
            successful=successful,
            failed=failed,
            skipped=skipped,
            results=results,
        )

    except Exception as e:
        logger.error(f"Directory ingestion failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/async", response_model=AsyncUploadResponse)
async def upload_document_async(
    file: UploadFile = File(...),
    organization_id: str = Form(...),
    property_name: str = Form(...),
    property_id: str | None = Form(None),
    program_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> AsyncUploadResponse:
    """Upload a document and process it asynchronously.

    This endpoint saves the file and returns immediately with a document ID.
    Processing (OCR, classification, extraction, embeddings) happens in the background.
    Use GET /documents/{document_id} to check processing status.

    Args:
        file: Uploaded file.
        organization_id: Organization ID.
        property_name: Property name.
        property_id: Optional property ID.
        program_id: Optional insurance program ID.
        db: Database session.

    Returns:
        AsyncUploadResponse with document ID and status.
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

    # Create document record with pending status
    document_id = str(uuid.uuid4())
    document = Document(
        id=document_id,
        file_name=file.filename or "unknown",
        file_url=str(final_path),  # Local path for now, updated after S3 upload
        organization_id=organization_id,
        property_id=property_id,
        upload_status="pending",
        ocr_status="pending",
        extraction_status="pending",
    )
    db.add(document)
    await db.commit()

    logger.info(f"Created document record {document_id} with pending status")

    # Start background processing
    logger.info(f"Starting background task for document {document_id}")
    try:
        task = asyncio.create_task(
            process_document_background(
                document_id=document_id,
                file_path=str(final_path),
                organization_id=organization_id,
                property_name=property_name,
                property_id=property_id,
                program_id=program_id,
            )
        )
        _background_tasks[document_id] = task

        # Add callback to log any exceptions from the task
        def task_done_callback(t: asyncio.Task) -> None:
            if t.exception():
                logger.error(f"Background task for {document_id} failed with exception: {t.exception()}")

        task.add_done_callback(task_done_callback)
        logger.info(f"Background task created for document {document_id}")
    except Exception as e:
        logger.error(f"Failed to create background task for {document_id}: {e}")

    return AsyncUploadResponse(
        document_id=document_id,
        file_name=file.filename or "unknown",
        status="pending",
        message="Document uploaded successfully. Processing started in background.",
    )


@router.post("/upload", response_model=IngestResponse)
async def upload_and_ingest_document(
    file: UploadFile = File(...),
    organization_id: str = Form(...),
    property_name: str = Form(...),
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
        property_name: Property name (used for folder organization in storage).
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
            property_name=property_name,
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


@router.post("/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest) -> ProcessResponse:
    """Process a document without storing to database.

    This endpoint runs the full OCR → Classification → Extraction pipeline
    without any database operations. Useful for testing and quick analysis.

    Args:
        request: ProcessRequest with file path.

    Returns:
        ProcessResponse with classification and extraction results.
    """
    file_path = Path(request.file_path)
    errors: list[str] = []

    # Validate file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail=f"Path is not a file: {request.file_path}")

    # Step 1: OCR
    logger.info(f"Processing document: {file_path.name}")
    ocr_service = get_ocr_service()

    try:
        ocr_result = await ocr_service.process_file_with_metadata(str(file_path))
        markdown = ocr_result.get("markdown", "")
        page_count = ocr_result.get("page_count", 1)
        logger.info(f"OCR completed: {page_count} pages, {len(markdown)} chars")
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    # Step 2: Classification
    classification_service = get_classification_service()

    try:
        classification = await classification_service.classify(markdown)
        logger.info(
            f"Classification: {classification.document_type.value} "
            f"(confidence: {classification.confidence})"
        )
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        errors.append(f"Classification failed: {e}")
        # Return partial result with unknown classification
        from app.schemas.document import DocumentType

        classification = DocumentClassification(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
        )
        return ProcessResponse(
            file_name=file_path.name,
            page_count=page_count,
            classification=classification,
            ocr_text=markdown,
            errors=errors,
        )

    # Step 3: Extraction
    extraction_service = get_extraction_service()
    extraction_dict: dict[str, Any] | None = None

    try:
        extraction_result = await extraction_service.extract(markdown, classification)
        extraction_dict = extraction_result.model_dump(mode="json")
        logger.info(f"Extraction completed (confidence: {extraction_result.overall_confidence})")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        errors.append(f"Extraction failed: {e}")

    return ProcessResponse(
        file_name=file_path.name,
        page_count=page_count,
        classification=classification,
        extraction=extraction_dict,
        ocr_text=markdown,
        errors=errors,
    )


@router.post("/process/upload", response_model=ProcessResponse)
async def process_uploaded_document(
    file: UploadFile = File(...),
    include_ocr_text: bool = Form(False),
) -> ProcessResponse:
    """Upload and process a document without storing to database.

    This endpoint accepts a file upload and runs the full pipeline
    without any database operations.

    Args:
        file: Uploaded file.
        include_ocr_text: Whether to include raw OCR text in response.

    Returns:
        ProcessResponse with classification and extraction results.
    """
    errors: list[str] = []

    # Validate file type
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}",
        )

    # Save to temp file
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_ext,
        ) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = Path(tmp_file.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    try:
        # Step 1: OCR
        logger.info(f"Processing uploaded document: {file.filename}")
        ocr_service = get_ocr_service()

        try:
            ocr_result = await ocr_service.process_file_with_metadata(str(temp_path))
            markdown = ocr_result.get("markdown", "")
            page_count = ocr_result.get("page_count", 1)
            logger.info(f"OCR completed: {page_count} pages, {len(markdown)} chars")
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

        # Step 2: Classification
        classification_service = get_classification_service()

        try:
            classification = await classification_service.classify(markdown)
            logger.info(
                f"Classification: {classification.document_type.value} "
                f"(confidence: {classification.confidence})"
            )
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            errors.append(f"Classification failed: {e}")
            from app.schemas.document import DocumentType

            classification = DocumentClassification(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
            )
            return ProcessResponse(
                file_name=file.filename or "unknown",
                page_count=page_count,
                classification=classification,
                ocr_text=markdown if include_ocr_text else None,
                errors=errors,
            )

        # Step 3: Extraction
        extraction_service = get_extraction_service()
        extraction_dict: dict[str, Any] | None = None

        try:
            extraction_result = await extraction_service.extract(markdown, classification)
            extraction_dict = extraction_result.model_dump(mode="json")
            logger.info(f"Extraction completed (confidence: {extraction_result.overall_confidence})")
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            errors.append(f"Extraction failed: {e}")

        return ProcessResponse(
            file_name=file.filename or "unknown",
            page_count=page_count,
            classification=classification,
            extraction=extraction_dict,
            ocr_text=markdown if include_ocr_text else None,
            errors=errors,
        )

    finally:
        # Clean up temp file
        try:
            temp_path.unlink()
        except Exception:
            pass
