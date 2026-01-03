"""Document Ingestion Service.

This service orchestrates the complete document ingestion pipeline:
1. File validation and document record creation
2. OCR processing (Mistral)
3. Classification (Gemini)
4. Extraction (Gemini)
5. Database record creation
"""

import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.certificate_repository import CertificateRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.policy_repository import CoverageRepository, PolicyRepository
from app.schemas.document import (
    DocumentClassification,
    DocumentType,
    ExtractionResult,
    IngestResponse,
    ProcessingStatus,
)
from app.services.classification_service import ClassificationService, get_classification_service
from app.services.extraction_service import ExtractionService, get_extraction_service
from app.services.ocr_service import OCRService, get_ocr_service

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Base exception for ingestion errors."""

    pass


class IngestionService:
    """Service for orchestrating document ingestion."""

    def __init__(
        self,
        session: AsyncSession,
        ocr_service: OCRService | None = None,
        classification_service: ClassificationService | None = None,
        extraction_service: ExtractionService | None = None,
    ):
        """Initialize ingestion service.

        Args:
            session: Database session.
            ocr_service: OCR service instance.
            classification_service: Classification service instance.
            extraction_service: Extraction service instance.
        """
        self.session = session
        self.ocr_service = ocr_service or get_ocr_service()
        self.classification_service = classification_service or get_classification_service()
        self.extraction_service = extraction_service or get_extraction_service()

        # Repositories
        self.document_repo = DocumentRepository(session)
        self.policy_repo = PolicyRepository(session)
        self.coverage_repo = CoverageRepository(session)
        self.certificate_repo = CertificateRepository(session)
        self.claim_repo = ClaimRepository(session)

    async def ingest_file(
        self,
        file_path: str,
        organization_id: str,
        property_id: str | None = None,
        program_id: str | None = None,
    ) -> IngestResponse:
        """Ingest a single document file.

        Args:
            file_path: Path to the document file.
            organization_id: Organization ID.
            property_id: Optional property ID.
            program_id: Optional insurance program ID (for creating policies).

        Returns:
            IngestResponse with results and any errors.
        """
        path = Path(file_path)
        errors: list[str] = []

        logger.info(f"Starting ingestion for: {path.name}")

        # Validate file exists
        if not path.exists():
            return IngestResponse(
                document_id="",
                file_name=path.name,
                status="failed",
                errors=[f"File not found: {file_path}"],
            )

        # Get file metadata
        file_size = path.stat().st_size
        file_type = path.suffix.lower().lstrip(".")
        mime_type = self._get_mime_type(path)

        # Create document record
        document = await self.document_repo.create_from_file(
            file_name=path.name,
            file_url=str(path.absolute()),
            organization_id=organization_id,
            property_id=property_id,
            file_size_bytes=file_size,
            file_type=file_type,
            mime_type=mime_type,
        )

        logger.info(f"Created document record: {document.id}")

        # Step 1: OCR
        try:
            await self.document_repo.update_ocr_status(
                document.id, ProcessingStatus.PROCESSING
            )

            ocr_result = await self.ocr_service.process_file_with_metadata(path)
            markdown_text = ocr_result["markdown"]
            page_count = ocr_result["page_count"]

            await self.document_repo.update_ocr_status(
                document.id,
                ProcessingStatus.COMPLETED,
                ocr_markdown=markdown_text,
                page_count=page_count,
            )

            logger.info(f"OCR completed: {page_count} pages, {len(markdown_text)} chars")

        except Exception as e:
            error_msg = f"OCR failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

            await self.document_repo.update_ocr_status(
                document.id, ProcessingStatus.FAILED, error=str(e)
            )

            return IngestResponse(
                document_id=document.id,
                file_name=path.name,
                status="failed",
                errors=errors,
            )

        # Step 2: Classification
        classification: DocumentClassification | None = None
        try:
            classification = await self.classification_service.classify(markdown_text)

            await self.document_repo.update_classification(document.id, classification)

            logger.info(
                f"Classification: {classification.document_type.value} "
                f"(confidence: {classification.confidence:.2f})"
            )

        except Exception as e:
            error_msg = f"Classification failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            # Continue with unknown classification
            classification = DocumentClassification(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
            )

        # Step 3: Extraction
        extraction_result: ExtractionResult | None = None
        try:
            await self.document_repo.update_extraction_status(
                document.id, ProcessingStatus.PROCESSING
            )

            extraction_result = await self.extraction_service.extract(
                markdown_text, classification
            )

            await self.document_repo.update_extraction_status(
                document.id,
                ProcessingStatus.COMPLETED,
                extraction_result=extraction_result,
            )

            logger.info(
                f"Extraction completed (confidence: {extraction_result.overall_confidence:.2f})"
            )

        except Exception as e:
            error_msg = f"Extraction failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

            await self.document_repo.update_extraction_status(
                document.id, ProcessingStatus.FAILED, error=str(e)
            )

        # Step 4: Create database records from extraction (if we have a program)
        if extraction_result and program_id:
            try:
                await self._create_records_from_extraction(
                    extraction_result,
                    program_id=program_id,
                    document_id=document.id,
                    property_id=property_id,
                )
            except Exception as e:
                error_msg = f"Record creation failed: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Build summary
        extraction_summary = None
        if extraction_result:
            extraction_summary = self._build_extraction_summary(extraction_result)

        status = "completed" if not errors else "completed_with_errors"

        return IngestResponse(
            document_id=document.id,
            file_name=path.name,
            status=status,
            classification=classification,
            extraction_summary=extraction_summary,
            errors=errors,
        )

    async def ingest_directory(
        self,
        directory_path: str,
        organization_id: str,
        property_id: str | None = None,
        program_id: str | None = None,
        extensions: set[str] | None = None,
    ) -> list[IngestResponse]:
        """Ingest all documents in a directory.

        Args:
            directory_path: Path to directory.
            organization_id: Organization ID.
            property_id: Optional property ID.
            program_id: Optional insurance program ID.
            extensions: File extensions to process (default: pdf, png, jpg, jpeg).

        Returns:
            List of IngestResponse for each file.
        """
        if extensions is None:
            extensions = {".pdf", ".png", ".jpg", ".jpeg"}

        directory = Path(directory_path)
        if not directory.is_dir():
            raise IngestionError(f"Not a directory: {directory_path}")

        results = []
        files = [f for f in directory.iterdir() if f.suffix.lower() in extensions]

        logger.info(f"Found {len(files)} files to ingest in {directory_path}")

        for file_path in files:
            try:
                result = await self.ingest_file(
                    str(file_path),
                    organization_id=organization_id,
                    property_id=property_id,
                    program_id=program_id,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to ingest {file_path.name}: {e}")
                results.append(
                    IngestResponse(
                        document_id="",
                        file_name=file_path.name,
                        status="failed",
                        errors=[str(e)],
                    )
                )

        return results

    async def _create_records_from_extraction(
        self,
        extraction: ExtractionResult,
        program_id: str,
        document_id: str,
        property_id: str | None = None,
    ) -> None:
        """Create database records from extraction result.

        Args:
            extraction: Extraction result.
            program_id: Insurance program ID.
            document_id: Source document ID.
            property_id: Property ID for claims.
        """
        # Create policy and coverages if we extracted policy data
        if extraction.policy:
            policy = await self.policy_repo.create_from_extraction(
                extraction.policy,
                program_id=program_id,
                document_id=document_id,
            )
            logger.info(f"Created policy: {policy.id}")

            # Create coverages
            if extraction.policy.coverages:
                coverages = await self.coverage_repo.create_many_from_extraction(
                    extraction.policy.coverages,
                    policy_id=policy.id,
                    document_id=document_id,
                )
                logger.info(f"Created {len(coverages)} coverages")

        # Create certificate from COI/EOP extraction
        if extraction.coi:
            # Determine certificate type
            cert_type = "coi"
            if extraction.classification.document_type == DocumentType.EOP:
                cert_type = "eop"

            certificate = await self.certificate_repo.create_from_extraction(
                extraction.coi,
                program_id=program_id,
                document_id=document_id,
                certificate_type=cert_type,
            )
            logger.info(f"Created certificate: {certificate.id}")

            # Also create stub policies from COI references if they don't exist
            if extraction.coi.policies:
                for pol_extraction in extraction.coi.policies:
                    if pol_extraction.policy_number:
                        existing = await self.policy_repo.get_by_policy_number(
                            pol_extraction.policy_number
                        )
                        if not existing:
                            policy = await self.policy_repo.create_from_extraction(
                                pol_extraction,
                                program_id=program_id,
                                document_id=document_id,
                            )
                            logger.info(f"Created policy from COI: {policy.id}")

        # Create claims from loss run extraction
        if extraction.loss_run and extraction.loss_run.claims and property_id:
            claims = await self.claim_repo.create_many_from_extraction(
                extraction.loss_run.claims,
                property_id=property_id,
                document_id=document_id,
            )
            logger.info(f"Created {len(claims)} claims from loss run")

    def _build_extraction_summary(self, extraction: ExtractionResult) -> dict:
        """Build a summary of extraction results.

        Args:
            extraction: Extraction result.

        Returns:
            Summary dictionary.
        """
        summary: dict = {
            "document_type": extraction.classification.document_type.value,
            "confidence": extraction.overall_confidence,
        }

        if extraction.policy:
            summary["policy"] = {
                "type": extraction.policy.policy_type.value,
                "number": extraction.policy.policy_number,
                "carrier": extraction.policy.carrier_name,
                "effective_date": (
                    extraction.policy.effective_date.isoformat()
                    if extraction.policy.effective_date
                    else None
                ),
                "expiration_date": (
                    extraction.policy.expiration_date.isoformat()
                    if extraction.policy.expiration_date
                    else None
                ),
                "premium": extraction.policy.premium,
                "coverages_count": len(extraction.policy.coverages),
            }

        if extraction.coi:
            summary["coi"] = {
                "insured": extraction.coi.insured_name,
                "holder": extraction.coi.holder_name,
                "policies_count": len(extraction.coi.policies),
            }

        if extraction.invoice:
            summary["invoice"] = {
                "number": extraction.invoice.invoice_number,
                "total": extraction.invoice.total_amount,
                "vendor": extraction.invoice.vendor_name,
            }

        if extraction.sov:
            summary["sov"] = {
                "properties_count": len(extraction.sov.properties),
                "total_tiv": extraction.sov.total_insured_value,
            }

        if extraction.loss_run:
            summary["loss_run"] = {
                "claims_count": len(extraction.loss_run.claims),
                "experience_period_start": (
                    extraction.loss_run.experience_period_start.isoformat()
                    if extraction.loss_run.experience_period_start
                    else None
                ),
                "experience_period_end": (
                    extraction.loss_run.experience_period_end.isoformat()
                    if extraction.loss_run.experience_period_end
                    else None
                ),
            }
            if extraction.loss_run.summary:
                summary["loss_run"]["total_incurred"] = extraction.loss_run.summary.total_incurred
                summary["loss_run"]["open_claims"] = extraction.loss_run.summary.open_claims
                summary["loss_run"]["closed_claims"] = extraction.loss_run.summary.closed_claims

        return summary

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for a file."""
        ext = file_path.suffix.lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
        }
        return mime_types.get(ext, "application/octet-stream")
