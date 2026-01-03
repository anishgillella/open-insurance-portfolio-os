#!/usr/bin/env python3
"""Test script to process a document through the full pipeline.

Usage: python test_document.py <path_to_pdf>
"""

import asyncio
import json
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))

from app.services.ocr_service import OCRService
from app.services.classification_service import ClassificationService
from app.services.extraction_service import ExtractionService


async def process_document(file_path: str):
    """Process a document through OCR → Classification → Extraction."""

    file_path = Path(file_path)

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    print("=" * 70)
    print(f"PROCESSING: {file_path.name}")
    print("=" * 70)

    # Step 1: OCR
    print("\n📄 STEP 1: OCR")
    print("-" * 40)

    ocr_service = OCRService()

    try:
        ocr_result = await ocr_service.process_file_with_metadata(str(file_path))
        markdown = ocr_result.get("markdown", "")
        page_count = ocr_result.get("page_count", 1)
        print(f"✓ OCR completed: {page_count} pages, {len(markdown):,} chars")

        # Save OCR output for reference
        ocr_output_path = file_path.with_suffix(".ocr.md")
        with open(ocr_output_path, "w") as f:
            f.write(markdown)
        print(f"✓ OCR saved to: {ocr_output_path.name}")

    except Exception as e:
        print(f"❌ OCR failed: {e}")
        return

    # Step 2: Classification
    print("\n🏷️  STEP 2: CLASSIFICATION")
    print("-" * 40)

    classification_service = ClassificationService()

    try:
        # Pattern detection
        detected = classification_service._detect_patterns(markdown)
        carriers = classification_service._count_carriers(markdown)
        print(f"Pattern detection: {len(detected)} types, {carriers} carriers")

        classification = await classification_service.classify(markdown)
        print(f"✓ Document Type: {classification.document_type.value}")
        print(f"  Policy Type: {classification.policy_type.value if classification.policy_type else 'N/A'}")
        print(f"  Confidence: {classification.confidence:.2f}")
        print(f"  Carrier: {classification.carrier_name}")
        print(f"  Policy #: {classification.policy_number}")
        print(f"  Insured: {classification.insured_name}")
        print(f"  Dates: {classification.effective_date} to {classification.expiration_date}")

    except Exception as e:
        print(f"❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Extraction
    print("\n📊 STEP 3: EXTRACTION")
    print("-" * 40)

    extraction_service = ExtractionService()

    try:
        result = await extraction_service.extract(markdown, classification)
        print(f"✓ Extraction completed (confidence: {result.overall_confidence:.2f})")

        # Display results based on document type
        if result.program:
            print_program_results(result.program)
        elif result.policy:
            print_policy_results(result.policy)
        elif result.coi:
            print_coi_results(result.coi)
        else:
            print("  No structured extraction available")

        # Save extraction to JSON
        extraction_output_path = file_path.with_suffix(".extraction.json")
        with open(extraction_output_path, "w") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, default=str)
        print(f"\n✓ Extraction saved to: {extraction_output_path.name}")

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 70)
    print("✅ PROCESSING COMPLETE")
    print("=" * 70)


def print_program_results(program):
    """Print program extraction results."""
    print(f"\n  PROGRAM DETAILS:")
    print(f"    Program Name: {program.program_name}")
    print(f"    Account #: {program.account_number}")
    print(f"    Confidence: {program.confidence:.2f}")

    if program.carriers:
        print(f"\n  CARRIERS ({len(program.carriers)}):")
        for c in program.carriers:
            print(f"    • {c.carrier_name}")
            print(f"      Policy #: {c.policy_number}")
            if c.participation_percentage:
                print(f"      Participation: {c.participation_percentage}%")

    if program.sublimits:
        print(f"\n  SUBLIMITS:")
        s = program.sublimits
        if s.maximum_limit_of_liability:
            print(f"    Max Limit: ${s.maximum_limit_of_liability:,.0f}")
        if s.earth_movement_aggregate:
            print(f"    Earth Movement: ${s.earth_movement_aggregate:,.0f}")
        if s.flood_aggregate:
            print(f"    Flood: ${s.flood_aggregate:,.0f}")
        else:
            print(f"    Flood: NOT COVERED")
        if s.accounts_receivable:
            print(f"    Accounts Receivable: ${s.accounts_receivable:,.0f}")
        if s.debris_removal_limit:
            print(f"    Debris Removal: ${s.debris_removal_limit:,.0f}")
        if s.valuable_papers_records:
            print(f"    Valuable Papers: ${s.valuable_papers_records:,.0f}")

    if program.deductibles:
        print(f"\n  DEDUCTIBLES:")
        d = program.deductibles
        if d.base_property_deductible:
            print(f"    Base Property: ${d.base_property_deductible:,.0f}")
        if d.named_storm_percentage:
            pct = d.named_storm_percentage * 100 if d.named_storm_percentage < 1 else d.named_storm_percentage
            print(f"    Named Storm: {pct}%")
        if d.named_storm_minimum:
            print(f"    Named Storm Min: ${d.named_storm_minimum:,.0f}")
        if d.earth_movement_percentage:
            pct = d.earth_movement_percentage * 100 if d.earth_movement_percentage < 1 else d.earth_movement_percentage
            print(f"    Earth Movement: {pct}%")
        if d.earth_movement_minimum:
            print(f"    Earth Movement Min: ${d.earth_movement_minimum:,.0f}")


def print_policy_results(policy):
    """Print policy extraction results."""
    print(f"\n  POLICY DETAILS:")
    print(f"    Policy Type: {policy.policy_type.value if policy.policy_type else 'Unknown'}")
    print(f"    Policy #: {policy.policy_number}")
    print(f"    Carrier: {policy.carrier_name}")
    print(f"    Insured: {policy.insured_name}")
    print(f"    Confidence: {policy.confidence:.2f}")

    if policy.coverages:
        print(f"\n  COVERAGES ({len(policy.coverages)}):")
        for cov in policy.coverages[:5]:
            print(f"    • {cov.coverage_name}")
            if cov.limit_amount:
                print(f"      Limit: ${cov.limit_amount:,.0f}")


def print_coi_results(coi):
    """Print COI extraction results."""
    print(f"\n  COI DETAILS:")
    print(f"    Certificate #: {coi.certificate_number}")
    print(f"    Insured: {coi.insured_name}")
    print(f"    Producer: {coi.producer_name}")
    print(f"    Confidence: {coi.confidence:.2f}")

    if coi.policies:
        print(f"\n  POLICIES ({len(coi.policies)}):")
        for p in coi.policies:
            print(f"    • {p.policy_type.value if p.policy_type else 'Unknown'}: {p.policy_number}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_document.py <path_to_pdf>")
        print("\nExample:")
        print("  python test_document.py ../sample_docs/document.pdf")
        sys.exit(1)

    asyncio.run(process_document(sys.argv[1]))
