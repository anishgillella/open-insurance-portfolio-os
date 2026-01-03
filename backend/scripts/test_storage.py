"""Test script for storage service."""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.storage_service import StorageService


async def test_storage():
    """Test storage service with a sample file."""
    # Initialize storage service using environment variables
    storage = StorageService(
        bucket_name=os.getenv("AWS_S3_BUCKET", "insurance-docs-open"),
        local_storage_path=os.getenv("LOCAL_STORAGE_PATH", "./storage"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_region=os.getenv("AWS_REGION", "us-east-2"),
    )

    # Check if AWS credentials are configured
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        print("Warning: AWS credentials not found in environment variables.")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file.")
        print("Continuing with local storage only...")

    # Test file
    test_file = Path(
        "/Users/anishgillella/conductor/workspaces/open-insurance-portfolio-os/santo-domingo/sample_docs/Shoaff Park/Shoaff Park 2025 Insurance.pdf"
    )

    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return

    print(f"Testing storage with: {test_file.name}")

    # Test storing the document
    try:
        result = await storage.store_document(
            file_path=test_file,
            organization_id="test-org-123",
            property_name="Shoaff Park",
            ocr_markdown="# Test Markdown\n\nThis is a test OCR output.",
            extraction_json={
                "document_type": "policy",
                "policy_number": "TEST-123",
                "carrier": "Test Carrier",
            },
        )

        print("\nStorage Results:")
        for key, value in result.items():
            print(f"  {key}: {value}")

        print("\nTest completed successfully!")

    except Exception as e:
        print(f"\nError during storage: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_storage())
