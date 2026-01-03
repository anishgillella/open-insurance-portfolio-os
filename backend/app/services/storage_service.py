"""Storage Service for S3 and local file storage.

This service handles uploading and storing:
- Original document files (PDF, images)
- OCR markdown output
- Extraction JSON results

Files are stored both locally and in S3 with the structure:
- s3://bucket/{organization_id}/{property_name}/{filename}
- local: ./storage/{organization_id}/{property_name}/{filename}
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any

import aioboto3
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class StorageService:
    """Service for storing files locally and in S3."""

    def __init__(
        self,
        bucket_name: str | None = None,
        local_storage_path: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_region: str | None = None,
    ):
        """Initialize storage service.

        Args:
            bucket_name: S3 bucket name.
            local_storage_path: Local storage directory path.
            aws_access_key_id: AWS access key.
            aws_secret_access_key: AWS secret key.
            aws_region: AWS region.
        """
        self.bucket_name = bucket_name or settings.aws_s3_bucket
        self.local_storage_path = Path(local_storage_path or "./storage")
        self.aws_access_key_id = aws_access_key_id or settings.aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key or settings.aws_secret_access_key
        self.aws_region = aws_region or settings.aws_region

        # Ensure local storage directory exists
        self.local_storage_path.mkdir(parents=True, exist_ok=True)

        # S3 session
        self._session = aioboto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region,
        )

        # Boto config for retries
        self._boto_config = Config(
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=10,
            read_timeout=30,
        )

    def _get_storage_key(
        self,
        organization_id: str,
        property_name: str,
        filename: str,
    ) -> str:
        """Build storage key/path for a file.

        Args:
            organization_id: Organization ID.
            property_name: Property name (folder).
            filename: File name.

        Returns:
            Storage key like "org123/Shoaff Park/document.pdf"
        """
        # Sanitize property name for use as folder name
        safe_property_name = self._sanitize_folder_name(property_name)
        return f"{organization_id}/{safe_property_name}/{filename}"

    def _sanitize_folder_name(self, name: str) -> str:
        """Sanitize a string for use as a folder name.

        Args:
            name: Raw folder name.

        Returns:
            Sanitized folder name.
        """
        # Replace problematic characters but keep spaces
        return name.replace("/", "-").replace("\\", "-").replace(":", "-").strip()

    def _get_base_filename(self, filepath: Path) -> str:
        """Get base filename without extension.

        Args:
            filepath: Path to file.

        Returns:
            Base filename without extension.
        """
        return filepath.stem

    async def store_document(
        self,
        file_path: str | Path,
        organization_id: str,
        property_name: str,
        ocr_markdown: str | None = None,
        extraction_json: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Store a document and its processed outputs.

        Stores:
        - Original file (copied to local, uploaded to S3)
        - OCR markdown (if provided)
        - Extraction JSON (if provided)

        Args:
            file_path: Path to the original document file.
            organization_id: Organization ID.
            property_name: Property name for folder organization.
            ocr_markdown: OCR markdown text to store.
            extraction_json: Extraction result dict to store.

        Returns:
            Dict with URLs/paths for each stored file:
            {
                "original_local": "/path/to/local/file.pdf",
                "original_s3": "s3://bucket/org/prop/file.pdf",
                "markdown_local": "/path/to/local/file.md",
                "markdown_s3": "s3://bucket/org/prop/file.md",
                "json_local": "/path/to/local/file.json",
                "json_s3": "s3://bucket/org/prop/file.json",
            }
        """
        source_path = Path(file_path)
        if not source_path.exists():
            raise StorageError(f"Source file not found: {file_path}")

        base_filename = self._get_base_filename(source_path)
        original_filename = source_path.name
        markdown_filename = f"{base_filename}.md"
        json_filename = f"{base_filename}.json"

        results: dict[str, str] = {}

        # Build local directory path
        local_dir = (
            self.local_storage_path
            / organization_id
            / self._sanitize_folder_name(property_name)
        )
        local_dir.mkdir(parents=True, exist_ok=True)

        # Store original file
        local_original_path = local_dir / original_filename
        s3_original_key = self._get_storage_key(
            organization_id, property_name, original_filename
        )

        # Copy original to local
        shutil.copy2(source_path, local_original_path)
        results["original_local"] = str(local_original_path.absolute())
        logger.info(f"Stored original locally: {local_original_path}")

        # Upload original to S3
        try:
            await self._upload_file_to_s3(source_path, s3_original_key)
            results["original_s3"] = f"s3://{self.bucket_name}/{s3_original_key}"
            logger.info(f"Uploaded original to S3: {results['original_s3']}")
        except Exception as e:
            logger.error(f"Failed to upload original to S3: {e}")
            results["original_s3_error"] = str(e)

        # Store OCR markdown
        if ocr_markdown:
            local_md_path = local_dir / markdown_filename
            s3_md_key = self._get_storage_key(
                organization_id, property_name, markdown_filename
            )

            # Write markdown locally
            local_md_path.write_text(ocr_markdown, encoding="utf-8")
            results["markdown_local"] = str(local_md_path.absolute())
            logger.info(f"Stored markdown locally: {local_md_path}")

            # Upload markdown to S3
            try:
                await self._upload_text_to_s3(
                    ocr_markdown, s3_md_key, content_type="text/markdown"
                )
                results["markdown_s3"] = f"s3://{self.bucket_name}/{s3_md_key}"
                logger.info(f"Uploaded markdown to S3: {results['markdown_s3']}")
            except Exception as e:
                logger.error(f"Failed to upload markdown to S3: {e}")
                results["markdown_s3_error"] = str(e)

        # Store extraction JSON
        if extraction_json:
            local_json_path = local_dir / json_filename
            s3_json_key = self._get_storage_key(
                organization_id, property_name, json_filename
            )

            # Write JSON locally
            json_content = json.dumps(extraction_json, indent=2, default=str)
            local_json_path.write_text(json_content, encoding="utf-8")
            results["json_local"] = str(local_json_path.absolute())
            logger.info(f"Stored JSON locally: {local_json_path}")

            # Upload JSON to S3
            try:
                await self._upload_text_to_s3(
                    json_content, s3_json_key, content_type="application/json"
                )
                results["json_s3"] = f"s3://{self.bucket_name}/{s3_json_key}"
                logger.info(f"Uploaded JSON to S3: {results['json_s3']}")
            except Exception as e:
                logger.error(f"Failed to upload JSON to S3: {e}")
                results["json_s3_error"] = str(e)

        return results

    async def _upload_file_to_s3(self, file_path: Path, s3_key: str) -> None:
        """Upload a file to S3.

        Args:
            file_path: Local file path.
            s3_key: S3 object key.
        """
        content_type = self._get_content_type(file_path)

        async with self._session.client(
            "s3", config=self._boto_config
        ) as s3_client:
            with open(file_path, "rb") as f:
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=f.read(),
                    ContentType=content_type,
                )

    async def _upload_text_to_s3(
        self, content: str, s3_key: str, content_type: str = "text/plain"
    ) -> None:
        """Upload text content to S3.

        Args:
            content: Text content to upload.
            s3_key: S3 object key.
            content_type: MIME type.
        """
        async with self._session.client(
            "s3", config=self._boto_config
        ) as s3_client:
            await s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content.encode("utf-8"),
                ContentType=content_type,
            )

    async def download_from_s3(self, s3_key: str, local_path: Path) -> None:
        """Download a file from S3.

        Args:
            s3_key: S3 object key.
            local_path: Local destination path.
        """
        async with self._session.client(
            "s3", config=self._boto_config
        ) as s3_client:
            response = await s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            content = await response["Body"].read()
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(content)

    async def get_text_from_s3(self, s3_key: str) -> str:
        """Get text content from S3.

        Args:
            s3_key: S3 object key.

        Returns:
            Text content.
        """
        async with self._session.client(
            "s3", config=self._boto_config
        ) as s3_client:
            response = await s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            content = await response["Body"].read()
            return content.decode("utf-8")

    async def list_property_files(
        self, organization_id: str, property_name: str
    ) -> list[dict[str, str]]:
        """List all files for a property in S3.

        Args:
            organization_id: Organization ID.
            property_name: Property name.

        Returns:
            List of file info dicts with key and size.
        """
        prefix = self._get_storage_key(organization_id, property_name, "")

        async with self._session.client(
            "s3", config=self._boto_config
        ) as s3_client:
            response = await s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
            )

            files = []
            for obj in response.get("Contents", []):
                files.append(
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                    }
                )
            return files

    async def file_exists_in_s3(self, s3_key: str) -> bool:
        """Check if a file exists in S3.

        Args:
            s3_key: S3 object key.

        Returns:
            True if file exists.
        """
        try:
            async with self._session.client(
                "s3", config=self._boto_config
            ) as s3_client:
                await s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                )
                return True
        except Exception:
            return False

    def _get_content_type(self, file_path: Path) -> str:
        """Get MIME type for a file.

        Args:
            file_path: Path to file.

        Returns:
            MIME type string.
        """
        ext = file_path.suffix.lower()
        content_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".md": "text/markdown",
            ".json": "application/json",
            ".txt": "text/plain",
        }
        return content_types.get(ext, "application/octet-stream")


# Singleton instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Get or create storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
