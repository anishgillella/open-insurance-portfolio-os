"""Document Ingestion Service.

This service orchestrates the complete document ingestion pipeline:
1. File validation and document record creation
2. OCR processing (Mistral)
3. Classification (Gemini)
4. Extraction (Gemini)
5. Auto-create property and program if needed
6. Database record creation (policies, certificates, financials, etc.)
7. File storage (local + S3)

Features:
- Parallel processing of multiple files in a directory
- Each file processed in its own async task for maximum throughput
- Auto-creates property and insurance program from property_name
- Populates all relational tables based on document type
"""

import asyncio
import logging
from datetime import date
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_maker
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.financial_repository import FinancialRepository
from app.repositories.policy_repository import CoverageRepository, PolicyRepository
from app.repositories.program_repository import ProgramRepository
from app.repositories.property_repository import PropertyRepository
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
from app.services.storage_service import StorageService, get_storage_service

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
        storage_service: StorageService | None = None,
    ):
        """Initialize ingestion service.

        Args:
            session: Database session.
            ocr_service: OCR service instance.
            classification_service: Classification service instance.
            extraction_service: Extraction service instance.
            storage_service: Storage service instance.
        """
        self.session = session
        self.ocr_service = ocr_service or get_ocr_service()
        self.classification_service = classification_service or get_classification_service()
        self.extraction_service = extraction_service or get_extraction_service()
        self.storage_service = storage_service or get_storage_service()

        # Repositories
        self.document_repo = DocumentRepository(session)
        self.property_repo = PropertyRepository(session)
        self.program_repo = ProgramRepository(session)
        self.policy_repo = PolicyRepository(session)
        self.coverage_repo = CoverageRepository(session)
        self.certificate_repo = CertificateRepository(session)
        self.financial_repo = FinancialRepository(session)
        self.claim_repo = ClaimRepository(session)

    async def ingest_file(
        self,
        file_path: str,
        organization_id: str,
        property_name: str,
        property_id: str | None = None,
        program_id: str | None = None,
        force_reprocess: bool = True,
        auto_create_entities: bool = True,
    ) -> IngestResponse:
        """Ingest a single document file.

        If a document with the same filename already exists for this organization,
        it will be reprocessed (updated) instead of creating a duplicate.

        When auto_create_entities=True (default), automatically creates:
        - Property record (if not provided)
        - InsuranceProgram record (if not provided)

        Args:
            file_path: Path to the document file.
            organization_id: Organization ID.
            property_name: Property name (used for folder organization and auto-creation).
            property_id: Optional property ID (auto-created if not provided).
            program_id: Optional insurance program ID (auto-created if not provided).
            force_reprocess: If True, reprocess existing documents. If False, skip them.
            auto_create_entities: If True, auto-create property and program.

        Returns:
            IngestResponse with results and any errors.
        """
        path = Path(file_path)
        errors: list[str] = []

        logger.info(f"Starting ingestion for: {path.name}")

        # Auto-create property and program if needed
        if auto_create_entities and not property_id:
            try:
                property_obj, prop_is_new = await self.property_repo.get_or_create(
                    name=property_name,
                    organization_id=organization_id,
                )
                property_id = property_obj.id
                if prop_is_new:
                    logger.info(f"Auto-created property: {property_name} (id: {property_id})")
            except Exception as e:
                error_msg = f"Failed to auto-create property: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        if auto_create_entities and property_id and not program_id:
            try:
                # Determine program year from current date
                current_year = date.today().year
                program_obj, prog_is_new = await self.program_repo.get_or_create(
                    property_id=property_id,
                    program_year=current_year,
                )
                program_id = program_obj.id
                if prog_is_new:
                    logger.info(f"Auto-created program: {current_year} (id: {program_id})")
            except Exception as e:
                error_msg = f"Failed to auto-create program: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

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

        # Use atomic upsert to handle race conditions in parallel processing
        # This will either create a new document or update an existing one
        document, is_new = await self.document_repo.upsert_from_file(
            file_name=path.name,
            file_url=str(path.absolute()),
            organization_id=organization_id,
            property_id=property_id,
            file_size_bytes=file_size,
            file_type=file_type,
            mime_type=mime_type,
        )

        if not is_new and not force_reprocess:
            logger.info(f"Document already exists, skipping: {path.name} (id: {document.id})")
            return IngestResponse(
                document_id=document.id,
                file_name=path.name,
                status="skipped",
                errors=["Document already exists. Use force_reprocess=True to reprocess."],
            )

        logger.info(f"{'Created new' if is_new else 'Reprocessing'} document: {document.id}")

        # Variables to store for later file storage
        ocr_markdown: str | None = None
        extraction_json: dict | None = None

        # Step 1: OCR
        markdown_text: str = ""
        try:
            await self.document_repo.update_ocr_status(
                document.id, ProcessingStatus.PROCESSING
            )

            ocr_result = await self.ocr_service.process_file_with_metadata(path)
            markdown_text = ocr_result["markdown"]
            page_count = ocr_result["page_count"]

            # Store for file storage later
            ocr_markdown = markdown_text

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

            # Store for file storage later
            extraction_json = extraction_result.model_dump(mode="json")

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

        # Step 3.5: Generate embeddings for RAG/Chat
        embedding_stats: dict | None = None
        try:
            embedding_stats = await self._run_embedding_pipeline(document.id)
            logger.info(
                f"Embedding completed: {embedding_stats.get('chunks_created', 0)} chunks, "
                f"{embedding_stats.get('vectors_upserted', 0)} vectors"
            )
        except Exception as e:
            # Embedding errors are non-fatal - document is still usable
            logger.warning(f"Embedding failed: {e}")
            errors.append(f"Embedding failed: {e}")

        # Step 4: Create database records from extraction
        # Now always runs since we auto-create property and program
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

            # Step 4.5: Auto-run gap detection and compliance checking
            if property_id:
                try:
                    await self._run_gap_detection(property_id)
                except Exception as e:
                    # Gap detection errors are non-fatal
                    logger.warning(f"Gap detection failed for property {property_id}: {e}")
        elif extraction_result and not program_id:
            logger.warning(
                f"Skipping record creation for {path.name}: no program_id available. "
                "Set auto_create_entities=True to auto-create."
            )

        # Step 5: Store files (local + S3)
        storage_urls: dict[str, str] = {}
        try:
            storage_urls = await self.storage_service.store_document(
                file_path=path,
                organization_id=organization_id,
                property_name=property_name,
                ocr_markdown=ocr_markdown,
                extraction_json=extraction_json,
            )
            logger.info(f"Files stored: {list(storage_urls.keys())}")

            # Update document with S3 URL if available
            if "original_s3" in storage_urls:
                await self.document_repo.update(
                    document.id, file_url=storage_urls["original_s3"]
                )

        except Exception as e:
            error_msg = f"Storage failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Build summary
        extraction_summary = None
        if extraction_result:
            extraction_summary = self._build_extraction_summary(extraction_result)

        # Add storage URLs to summary
        if storage_urls:
            extraction_summary = extraction_summary or {}
            extraction_summary["storage"] = storage_urls

        # Add embedding stats to summary
        if embedding_stats:
            extraction_summary = extraction_summary or {}
            extraction_summary["embedding"] = {
                "chunks": embedding_stats.get("chunks_created", 0),
                "vectors": embedding_stats.get("vectors_upserted", 0),
                "tokens": embedding_stats.get("tokens_used", 0),
            }

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
        property_name: str | None = None,
        property_id: str | None = None,
        program_id: str | None = None,
        extensions: set[str] | None = None,
        max_concurrent: int | None = None,
        force_reprocess: bool = True,
        auto_create_entities: bool = True,
    ) -> list[IngestResponse]:
        """Ingest all documents in a directory in PARALLEL.

        Each file is processed in its own async task for maximum throughput.
        Uses semaphore to limit concurrent API calls.

        When auto_create_entities=True (default):
        - Creates a single Property for the directory (uses directory name)
        - Creates a single InsuranceProgram for the current year
        - All documents in the directory share the same property and program

        Args:
            directory_path: Path to directory.
            organization_id: Organization ID.
            property_name: Property name for storage (defaults to directory name).
            property_id: Optional property ID (auto-created if not provided).
            program_id: Optional insurance program ID (auto-created if not provided).
            extensions: File extensions to process (default: pdf, png, jpg, jpeg).
            max_concurrent: Maximum number of files to process concurrently (default: 5).
            force_reprocess: If True, reprocess existing documents. If False, skip them.
            auto_create_entities: If True, auto-create property and program once for all files.

        Returns:
            List of IngestResponse for each file.
        """
        # Use config value if not specified
        if max_concurrent is None:
            max_concurrent = settings.max_concurrent_files

        if extensions is None:
            extensions = {".pdf", ".png", ".jpg", ".jpeg"}

        directory = Path(directory_path)
        if not directory.is_dir():
            raise IngestionError(f"Not a directory: {directory_path}")

        # Use directory name as property name if not provided
        if property_name is None:
            property_name = directory.name

        files = [f for f in directory.iterdir() if f.suffix.lower() in extensions]

        logger.info(
            f"Found {len(files)} files to ingest in {directory_path} "
            f"(property: {property_name}, parallel: {max_concurrent}, force_reprocess: {force_reprocess})"
        )

        # Auto-create property and program ONCE for the entire directory
        # This ensures all documents share the same property and program
        if auto_create_entities and not property_id:
            property_obj, prop_is_new = await self.property_repo.get_or_create(
                name=property_name,
                organization_id=organization_id,
            )
            property_id = property_obj.id
            if prop_is_new:
                logger.info(f"Auto-created property for directory: {property_name} (id: {property_id})")

        if auto_create_entities and property_id and not program_id:
            current_year = date.today().year
            program_obj, prog_is_new = await self.program_repo.get_or_create(
                property_id=property_id,
                program_year=current_year,
            )
            program_id = program_obj.id
            if prog_is_new:
                logger.info(f"Auto-created program for directory: {current_year} (id: {program_id})")

        # IMPORTANT: Commit property and program so parallel tasks can see them
        # Each parallel task uses its own session, so we need to commit here
        if auto_create_entities:
            await self.session.commit()
            logger.info("Committed property and program before parallel processing")

        # Semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_file(file_path: Path) -> IngestResponse:
            """Process a single file with its own database session.

            Each parallel task gets its own session to avoid SQLAlchemy
            concurrent session access errors.
            """
            async with semaphore:
                # Create a new session for this task
                async with async_session_maker() as task_session:
                    try:
                        logger.info(f"[PARALLEL] Starting ingestion: {file_path.name}")

                        # Create a new IngestionService with the task-specific session
                        task_service = IngestionService(
                            session=task_session,
                            ocr_service=self.ocr_service,
                            classification_service=self.classification_service,
                            extraction_service=self.extraction_service,
                            storage_service=self.storage_service,
                        )

                        # Pass the shared property_id and program_id
                        # Disable auto_create_entities since we already created them
                        result = await task_service.ingest_file(
                            str(file_path),
                            organization_id=organization_id,
                            property_name=property_name,
                            property_id=property_id,
                            program_id=program_id,
                            force_reprocess=force_reprocess,
                            auto_create_entities=False,  # Already created above
                        )

                        # Commit the task's session
                        await task_session.commit()

                        logger.info(f"[PARALLEL] Completed: {file_path.name} - {result.status}")
                        return result
                    except Exception as e:
                        await task_session.rollback()
                        logger.error(f"[PARALLEL] Failed: {file_path.name} - {e}")
                        return IngestResponse(
                            document_id="",
                            file_name=file_path.name,
                            status="failed",
                            errors=[str(e)],
                        )

        # Process all files in parallel using asyncio.gather
        tasks = [process_file(file_path) for file_path in files]
        results = await asyncio.gather(*tasks)

        # Log summary
        successful = sum(1 for r in results if r.status == "completed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        partial = sum(1 for r in results if r.status == "completed_with_errors")
        logger.info(
            f"[PARALLEL] Directory ingestion complete: "
            f"{successful} successful, {partial} partial, {failed} failed, {skipped} skipped"
        )

        return list(results)

    async def _create_records_from_extraction(
        self,
        extraction: ExtractionResult,
        program_id: str,
        document_id: str,
        property_id: str | None = None,
    ) -> dict:
        """Create database records from extraction result.

        Based on document type, creates appropriate records:
        - Policy documents → policies + coverages tables
        - COI/EOP documents → certificates + policies tables
        - Invoice documents → financials table
        - Loss Run documents → claims table
        - SOV documents → valuations table (TODO)

        Args:
            extraction: Extraction result.
            program_id: Insurance program ID.
            document_id: Source document ID.
            property_id: Property ID for claims.

        Returns:
            Dictionary with created record IDs by type.
        """
        created_records: dict = {}

        # Create policy and coverages if we extracted policy data
        if extraction.policy:
            policy = await self.policy_repo.create_from_extraction(
                extraction.policy,
                program_id=program_id,
                document_id=document_id,
            )
            logger.info(f"Created policy: {policy.id}")
            created_records["policy_id"] = policy.id

            # Create coverages
            if extraction.policy.coverages:
                coverages = await self.coverage_repo.create_many_from_extraction(
                    extraction.policy.coverages,
                    policy_id=policy.id,
                    document_id=document_id,
                )
                logger.info(f"Created {len(coverages)} coverages")
                created_records["coverage_ids"] = [c.id for c in coverages]

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
            created_records["certificate_id"] = certificate.id

            # Also create stub policies from COI references if they don't exist
            if extraction.coi.policies:
                policy_ids = []
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
                            policy_ids.append(policy.id)
                if policy_ids:
                    created_records["policy_ids_from_coi"] = policy_ids

        # Create financial record from invoice extraction
        if extraction.invoice:
            financial = await self.financial_repo.create_from_extraction(
                extraction.invoice,
                program_id=program_id,
                document_id=document_id,
            )
            logger.info(f"Created financial record: {financial.id}")
            created_records["financial_id"] = financial.id

        # Create claims from loss run extraction
        if extraction.loss_run and extraction.loss_run.claims and property_id:
            claims = await self.claim_repo.create_many_from_extraction(
                extraction.loss_run.claims,
                property_id=property_id,
                document_id=document_id,
            )
            logger.info(f"Created {len(claims)} claims from loss run")
            created_records["claim_ids"] = [c.id for c in claims]

        # TODO: Create valuations from SOV extraction
        # if extraction.sov and extraction.sov.properties:
        #     for sov_property in extraction.sov.properties:
        #         valuation = await self.valuation_repo.create_from_extraction(...)

        return created_records

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

    async def _run_gap_detection(self, property_id: str) -> None:
        """Run gap detection, compliance checking, and LLM analysis for a property.

        This is called automatically after document extraction to:
        1. Detect coverage gaps using rule-based thresholds
        2. Check compliance against lender requirements
        3. Enrich gaps with LLM-powered analysis

        Args:
            property_id: Property ID to check.
        """
        from app.services.compliance_service import ComplianceService
        from app.services.gap_detection_service import GapDetectionService

        logger.info(f"Running auto gap detection for property {property_id}")

        # Step 1: Run rule-based gap detection
        gap_service = GapDetectionService(self.session)
        gaps = await gap_service.detect_gaps_for_property(
            property_id, clear_existing=True
        )
        logger.info(f"Auto gap detection found {len(gaps)} gaps for property {property_id}")

        # Step 2: Run compliance checking (only if lender requirements exist)
        compliance_service = ComplianceService(self.session)
        results = await compliance_service.check_compliance_for_property(
            property_id, create_gaps=True
        )
        if results:
            total_issues = sum(len(r.issues) for r in results)
            logger.info(
                f"Auto compliance check found {total_issues} issues "
                f"across {len(results)} requirements for property {property_id}"
            )

        # Step 3: Run LLM-enhanced analysis on detected gaps
        if gaps:
            await self._run_llm_gap_analysis(property_id, gaps)

    async def _run_llm_gap_analysis(self, property_id: str, gaps: list) -> None:
        """Run LLM-enhanced analysis on detected gaps.

        This enriches rule-based gaps with AI-powered insights including:
        - Enhanced descriptions
        - Risk assessments and scores
        - Actionable recommendations
        - Industry context

        Args:
            property_id: Property ID.
            gaps: List of detected gaps.
        """
        from app.services.gap_analysis_service import GapAnalysisService, GapAnalysisError

        try:
            logger.info(f"Running LLM gap analysis for property {property_id} ({len(gaps)} gaps)")

            analysis_service = GapAnalysisService(self.session)

            # Analyze each gap individually
            analyzed_count = 0
            for gap in gaps:
                try:
                    analysis = await analysis_service.analyze_gap(gap.id)
                    analyzed_count += 1
                    logger.debug(
                        f"Gap {gap.id} analyzed: risk_score={analysis.risk_score}, "
                        f"priority={analysis.action_priority}"
                    )
                except GapAnalysisError as e:
                    logger.warning(f"Failed to analyze gap {gap.id}: {e}")
                    continue

            logger.info(
                f"LLM gap analysis complete for property {property_id}: "
                f"{analyzed_count}/{len(gaps)} gaps analyzed"
            )

            # Step 4: Calculate/update health score after gap detection
            await self._update_health_score(property_id, trigger="ingestion")

            # Step 5: Detect coverage conflicts
            await self._detect_conflicts(property_id)

        except Exception as e:
            # LLM analysis errors are non-fatal - gaps are still detected
            logger.warning(f"LLM gap analysis failed for property {property_id}: {e}")

    async def _update_health_score(self, property_id: str, trigger: str) -> None:
        """Update health score after changes.

        Calculates a new health score for the property using LLM analysis.
        Non-fatal if it fails.

        Args:
            property_id: Property ID.
            trigger: What triggered the recalculation.
        """
        from app.services.health_score_service import HealthScoreService, HealthScoreError

        try:
            logger.info(f"Updating health score for property {property_id} (trigger: {trigger})")
            health_service = HealthScoreService(self.session)
            result = await health_service.calculate_health_score(property_id, trigger=trigger)
            logger.info(f"Health score updated for property {property_id}: {result.score} ({result.grade})")
        except HealthScoreError as e:
            logger.warning(f"Health score update failed for property {property_id}: {e}")
        except Exception as e:
            logger.warning(f"Health score update failed for property {property_id}: {e}")

    async def _detect_conflicts(self, property_id: str) -> None:
        """Detect coverage conflicts between policies.

        Uses LLM to analyze policies for conflicts and overlaps.
        Non-fatal if it fails.

        Args:
            property_id: Property ID.
        """
        from app.services.conflict_detection_service import ConflictDetectionService, ConflictDetectionError

        try:
            logger.info(f"Detecting conflicts for property {property_id}")
            conflict_service = ConflictDetectionService(self.session)
            result = await conflict_service.detect_conflicts(property_id, clear_existing=True)
            logger.info(
                f"Conflict detection complete for property {property_id}: "
                f"{len(result.conflicts)} conflicts found"
            )
        except ConflictDetectionError as e:
            logger.warning(f"Conflict detection failed for property {property_id}: {e}")
        except Exception as e:
            logger.warning(f"Conflict detection failed for property {property_id}: {e}")

    async def _run_embedding_pipeline(self, document_id: str) -> dict:
        """Run the embedding pipeline for a document.

        This chunks the document's OCR text, generates embeddings, and stores them
        in Pinecone for RAG/Chat functionality.

        Args:
            document_id: Document ID to process.

        Returns:
            Dictionary with embedding statistics.
        """
        from app.services.embedding_pipeline_service import (
            EmbeddingPipelineService,
            EmbeddingPipelineError,
        )

        logger.info(f"Running embedding pipeline for document {document_id}")

        pipeline_service = EmbeddingPipelineService(self.session)
        result = await pipeline_service.process_document(document_id, force_reprocess=False)

        return result
