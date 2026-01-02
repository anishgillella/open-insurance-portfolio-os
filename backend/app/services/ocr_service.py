"""OCR Service using Mistral OCR API.

This service converts PDF documents and images to markdown text using
the Mistral OCR API, which handles:
- Standard PDFs with text
- Scanned documents
- Images (PNG, JPG, TIFF)
- Handwritten content
- Tables and structured data
"""

import base64
import logging
import mimetypes
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Supported file types for OCR
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp"}


class OCRServiceError(Exception):
    """Base exception for OCR service errors."""

    pass


class UnsupportedFileTypeError(OCRServiceError):
    """Raised when file type is not supported for OCR."""

    pass


class OCRAPIError(OCRServiceError):
    """Raised when Mistral OCR API returns an error."""

    pass


class OCRService:
    """Service for converting documents to text using Mistral OCR."""

    MISTRAL_FILES_URL = "https://api.mistral.ai/v1/files"
    MISTRAL_OCR_URL = "https://api.mistral.ai/v1/ocr"

    def __init__(self, api_key: str | None = None):
        """Initialize OCR service.

        Args:
            api_key: Mistral API key. Defaults to settings.mistral_api_key.
        """
        self.api_key = api_key or settings.mistral_api_key
        if not self.api_key:
            logger.warning("Mistral API key not configured")

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for a file based on extension."""
        ext = file_path.suffix.lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".webp": "image/webp",
        }
        return mime_types.get(ext, "application/octet-stream")

    def _validate_file(self, file_path: Path) -> None:
        """Validate that file exists and is supported."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file type: {file_path.suffix}. "
                f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

    def _is_image(self, file_path: Path) -> bool:
        """Check if file is an image (not PDF)."""
        return file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp"}

    async def _upload_file(self, file_path: Path) -> str:
        """Upload a file to Mistral and return the file ID.

        Args:
            file_path: Path to file to upload.

        Returns:
            Uploaded file ID.
        """
        logger.info(f"Uploading file to Mistral: {file_path.name}")

        with open(file_path, "rb") as f:
            file_content = f.read()

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                self.MISTRAL_FILES_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                },
                files={
                    "file": (file_path.name, file_content, self._get_mime_type(file_path)),
                },
                data={
                    "purpose": "ocr",
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Mistral file upload error: {response.status_code} - {error_detail}")
                raise OCRAPIError(f"File upload failed: {response.status_code} - {error_detail}")

            result = response.json()
            file_id = result.get("id")
            logger.info(f"File uploaded successfully: {file_id}")
            return file_id

    async def _get_signed_url(self, file_id: str) -> str:
        """Get a signed URL for an uploaded file.

        Args:
            file_id: Mistral file ID.

        Returns:
            Signed URL for the file.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.MISTRAL_FILES_URL}/{file_id}/url",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                },
                params={"expiry": 60},  # URL valid for 60 seconds
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Get signed URL error: {response.status_code} - {error_detail}")
                raise OCRAPIError(f"Get signed URL failed: {response.status_code}")

            result = response.json()
            return result.get("url")

    async def process_file(self, file_path: str | Path) -> str:
        """Process a document file and return extracted markdown text.

        Args:
            file_path: Path to the document file (PDF or image).

        Returns:
            Extracted text in markdown format.

        Raises:
            FileNotFoundError: If file doesn't exist.
            UnsupportedFileTypeError: If file type not supported.
            OCRAPIError: If Mistral API returns an error.
        """
        file_path = Path(file_path)
        self._validate_file(file_path)

        if not self.api_key:
            raise OCRServiceError("Mistral API key not configured")

        mime_type = self._get_mime_type(file_path)
        logger.info(f"Processing file: {file_path.name} ({mime_type})")

        # For images, use base64 data URL approach
        # For PDFs, upload to Mistral first then use signed URL
        if self._is_image(file_path):
            # Use base64 data URL for images
            with open(file_path, "rb") as f:
                file_content = f.read()
            file_base64 = base64.standard_b64encode(file_content).decode("utf-8")
            data_url = f"data:{mime_type};base64,{file_base64}"

            document = {
                "type": "image_url",
                "image_url": data_url,
            }
        else:
            # Upload PDF and get signed URL
            file_id = await self._upload_file(file_path)
            signed_url = await self._get_signed_url(file_id)

            document = {
                "type": "document_url",
                "document_url": signed_url,
            }

        # Call Mistral OCR API
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                self.MISTRAL_OCR_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mistral-ocr-latest",
                    "document": document,
                    "include_image_base64": False,
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Mistral OCR API error: {response.status_code} - {error_detail}")
                raise OCRAPIError(f"Mistral OCR API error: {response.status_code} - {error_detail}")

            result = response.json()

        # Extract markdown from response
        # Mistral OCR returns pages with markdown content
        pages = result.get("pages", [])
        if not pages:
            logger.warning(f"No pages extracted from {file_path.name}")
            return ""

        # Combine all pages into single markdown document
        markdown_parts = []
        for i, page in enumerate(pages, 1):
            page_markdown = page.get("markdown", "")
            if page_markdown:
                markdown_parts.append(f"<!-- Page {i} -->\n{page_markdown}")

        full_markdown = "\n\n---\n\n".join(markdown_parts)

        logger.info(
            f"OCR completed for {file_path.name}: "
            f"{len(pages)} pages, {len(full_markdown)} characters"
        )

        return full_markdown

    async def process_file_with_metadata(
        self, file_path: str | Path
    ) -> dict:
        """Process a document and return both text and metadata.

        Args:
            file_path: Path to the document file.

        Returns:
            Dictionary with 'markdown', 'page_count', and 'file_info'.
        """
        file_path = Path(file_path)
        self._validate_file(file_path)

        markdown = await self.process_file(file_path)

        # Count pages from markdown (each page is marked with <!-- Page N -->)
        page_count = markdown.count("<!-- Page")

        return {
            "markdown": markdown,
            "page_count": page_count if page_count > 0 else 1,
            "file_info": {
                "name": file_path.name,
                "size_bytes": file_path.stat().st_size,
                "mime_type": self._get_mime_type(file_path),
            },
        }


# Singleton instance
_ocr_service: OCRService | None = None


def get_ocr_service() -> OCRService:
    """Get or create OCR service instance."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
