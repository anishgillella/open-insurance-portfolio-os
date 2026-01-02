"""CLI command for document ingestion.

Usage:
    # Ingest a single file
    python -m app.cli.ingest ./documents/policy.pdf --org-id <org-id>

    # Ingest a directory
    python -m app.cli.ingest ./documents/ --org-id <org-id> --directory

    # With property and program IDs
    python -m app.cli.ingest ./policy.pdf --org-id <org> --property-id <prop> --program-id <prog>
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import async_session_maker
from app.services.ingestion_service import IngestionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def ingest_file(
    file_path: str,
    organization_id: str,
    property_id: str | None = None,
    program_id: str | None = None,
) -> None:
    """Ingest a single file."""
    async with async_session_maker() as session:
        service = IngestionService(session)

        result = await service.ingest_file(
            file_path=file_path,
            organization_id=organization_id,
            property_id=property_id,
            program_id=program_id,
        )

        await session.commit()

    # Print results
    print("\n" + "=" * 60)
    print("INGESTION RESULT")
    print("=" * 60)
    print(f"File: {result.file_name}")
    print(f"Document ID: {result.document_id}")
    print(f"Status: {result.status}")

    if result.classification:
        print(f"\nClassification:")
        print(f"  Type: {result.classification.document_type.value}")
        if result.classification.policy_type:
            print(f"  Policy Type: {result.classification.policy_type.value}")
        print(f"  Confidence: {result.classification.confidence:.2%}")
        if result.classification.carrier_name:
            print(f"  Carrier: {result.classification.carrier_name}")
        if result.classification.policy_number:
            print(f"  Policy #: {result.classification.policy_number}")

    if result.extraction_summary:
        print(f"\nExtraction Summary:")
        for key, value in result.extraction_summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

    if result.errors:
        print(f"\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    print("=" * 60 + "\n")


async def ingest_directory(
    directory_path: str,
    organization_id: str,
    property_id: str | None = None,
    program_id: str | None = None,
) -> None:
    """Ingest all files in a directory."""
    async with async_session_maker() as session:
        service = IngestionService(session)

        results = await service.ingest_directory(
            directory_path=directory_path,
            organization_id=organization_id,
            property_id=property_id,
            program_id=program_id,
        )

        await session.commit()

    # Print summary
    print("\n" + "=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)

    completed = sum(1 for r in results if r.status == "completed")
    with_errors = sum(1 for r in results if r.status == "completed_with_errors")
    failed = sum(1 for r in results if r.status == "failed")

    print(f"Total files: {len(results)}")
    print(f"  Completed: {completed}")
    print(f"  Completed with errors: {with_errors}")
    print(f"  Failed: {failed}")

    print("\nDetails:")
    for result in results:
        status_icon = "✓" if result.status == "completed" else "⚠" if "error" in result.status else "✗"
        doc_type = result.classification.document_type.value if result.classification else "unknown"
        print(f"  {status_icon} {result.file_name} ({doc_type}) - {result.document_id}")

    print("=" * 60 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest insurance documents into the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a single PDF
  python -m app.cli.ingest ./policy.pdf --org-id abc123

  # Ingest all files in a directory
  python -m app.cli.ingest ./documents/ --org-id abc123 --directory

  # Generate a new organization ID
  python -m app.cli.ingest ./policy.pdf --new-org
        """,
    )

    parser.add_argument(
        "path",
        type=str,
        help="Path to file or directory to ingest",
    )
    parser.add_argument(
        "--org-id",
        type=str,
        help="Organization ID (required unless --new-org is used)",
    )
    parser.add_argument(
        "--new-org",
        action="store_true",
        help="Generate a new organization ID (for testing)",
    )
    parser.add_argument(
        "--property-id",
        type=str,
        help="Property ID to associate documents with",
    )
    parser.add_argument(
        "--program-id",
        type=str,
        help="Insurance program ID (enables policy/coverage record creation)",
    )
    parser.add_argument(
        "--directory",
        "-d",
        action="store_true",
        help="Treat path as a directory and ingest all files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate organization ID
    if args.new_org:
        organization_id = str(uuid4())
        print(f"Generated new organization ID: {organization_id}")
    elif args.org_id:
        organization_id = args.org_id
    else:
        parser.error("--org-id is required (or use --new-org for testing)")

    # Validate path
    path = Path(args.path)
    if not path.exists():
        parser.error(f"Path does not exist: {args.path}")

    if args.directory:
        if not path.is_dir():
            parser.error(f"Path is not a directory: {args.path}")
        asyncio.run(
            ingest_directory(
                str(path),
                organization_id=organization_id,
                property_id=args.property_id,
                program_id=args.program_id,
            )
        )
    else:
        if not path.is_file():
            parser.error(f"Path is not a file: {args.path}")
        asyncio.run(
            ingest_file(
                str(path),
                organization_id=organization_id,
                property_id=args.property_id,
                program_id=args.program_id,
            )
        )


if __name__ == "__main__":
    main()
