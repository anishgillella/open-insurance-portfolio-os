#!/usr/bin/env python3
"""Test the full classification + extraction pipeline on PROP 2324 document.

This script runs the complete pipeline and checks if we extracted all critical information.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.classification_service import ClassificationService
from app.services.extraction_service import ExtractionService
from app.schemas.document import DocumentType


# Expected values from the document (ground truth)
EXPECTED_VALUES = {
    "classification": {
        "document_type": "program",
        "policy_type": "property",
        "insured_name": "110 Chanticleer Property LLC",
        "policy_number": "AMR-81904",
        "effective_date": "2023-05-17",
        "expiration_date": "2024-05-17",
    },
    "carriers": [
        "Certain Underwriters at Lloyd's, London",
        "QBE Specialty Insurance Company",
        "Steadfast Insurance Company",
        "Old Republic Union Insurance Company",
        "GeoVera Specialty Insurance Company",
        "Transverse Specialty Insurance Company",
        "National Fire & Marine Insurance Company",
        "Spinnaker Specialty Insurance Company",
    ],
    "limits": {
        "maximum_limit": 24823864,
        "earth_movement_aggregate": 24823864,
        "flood": "NOT COVERED",
        "cyber_aggregate": 100000,
    },
    "deductibles": {
        "base_deductible": 10000,
        "earth_movement_percentage": 2.0,
        "earth_movement_minimum": 100000,
        "windstorm_percentage": 1.0,
        "windstorm_minimum": 100000,
        "named_storm_percentage": 5.0,
        "named_storm_minimum": 1241193,
    },
    "sublimits": {
        "accounts_receivable": 100000,
        "civil_authority_days": 30,
        "civil_authority_limit": 100000,
        "contingent_time_element_days": 60,
        "contingent_time_element_limit": 100000,
        "debris_removal_percentage": 25,
        "debris_removal_limit": 5000000,
        "electronic_data_media": 50000,
        "errors_omissions": 25000,
        "extended_period_indemnity_days": 365,
        "extra_expense": 25000,
        "fine_arts": 50000,
        "fungus_mold_aggregate": 15000,
        "ingress_egress_days": 30,
        "ingress_egress_limit": 50000,
        "newly_acquired_days": 60,
        "newly_acquired_limit": 1000000,
        "service_interruption": 50000,
        "valuable_papers": 100000,
    },
}


async def test_classification(ocr_text: str) -> dict:
    """Test classification on the document."""
    print("\n" + "=" * 60)
    print("STEP 1: CLASSIFICATION")
    print("=" * 60)

    service = ClassificationService()

    # First test pattern detection (doesn't need API key)
    print("\nPattern Detection (local):")
    detected = service._detect_patterns(ocr_text)
    carriers = service._count_carriers(ocr_text)

    print(f"  - Program indicators: {len(detected.get('program', []))}")
    print(f"  - Carriers detected: {carriers}")
    print(f"  - Other patterns: {[k for k in detected.keys() if k != 'program']}")

    # Test first 10 pages extraction
    first_10 = service._extract_first_n_pages(ocr_text, n_pages=10)
    print(f"\nFirst 10 pages: {len(first_10):,} chars (from {len(ocr_text):,} total)")

    # Check if API key is configured
    if not service.api_key:
        print("\n⚠️  OpenRouter API key not configured - using pattern-based fallback")
        classification = service._pattern_based_fallback(detected, carriers)
    else:
        print("\nCalling LLM for classification...")
        classification = await service.classify(ocr_text)

    print(f"\nClassification Result:")
    print(f"  - Document Type: {classification.document_type.value}")
    print(f"  - Policy Type: {classification.policy_type.value if classification.policy_type else 'N/A'}")
    print(f"  - Confidence: {classification.confidence:.2f}")
    print(f"  - Carrier: {classification.carrier_name}")
    print(f"  - Policy #: {classification.policy_number}")
    print(f"  - Insured: {classification.insured_name}")
    print(f"  - Dates: {classification.effective_date} to {classification.expiration_date}")

    # Check against expected
    expected = EXPECTED_VALUES["classification"]
    print(f"\nValidation:")
    if classification.document_type.value == expected["document_type"]:
        print(f"  ✓ Document type correct: {expected['document_type']}")
    else:
        print(f"  ✗ Document type WRONG: expected {expected['document_type']}, got {classification.document_type.value}")

    return {"classification": classification, "detected_patterns": detected, "carrier_count": carriers}


async def test_extraction(ocr_text: str, classification) -> dict:
    """Test extraction on the document."""
    print("\n" + "=" * 60)
    print("STEP 2: EXTRACTION")
    print("=" * 60)

    service = ExtractionService()

    if not service.api_key:
        print("\n⚠️  OpenRouter API key not configured - cannot run extraction")
        return {}

    print(f"\nExtracting as: {classification.document_type.value}")
    print("This may take a minute for large documents...")

    result = await service.extract(ocr_text, classification)

    print(f"\nExtraction Result:")
    print(f"  - Overall Confidence: {result.overall_confidence:.2f}")

    if result.program:
        program = result.program
        print(f"\nProgram Extraction:")
        print(f"  - Program Name: {program.program_name}")
        print(f"  - Account Number: {program.account_number}")
        print(f"  - Carriers: {len(program.carriers) if program.carriers else 0}")

        if program.carriers:
            for c in program.carriers[:3]:
                print(f"    - {c.carrier_name}: {c.policy_number}")
            if len(program.carriers) > 3:
                print(f"    ... and {len(program.carriers) - 3} more")

        # Check sublimits
        if program.sublimits:
            print(f"\n  Sublimits Schedule:")
            sublimits = program.sublimits
            print(f"    - Accounts Receivable: ${sublimits.accounts_receivable:,.0f}" if sublimits.accounts_receivable else "    - Accounts Receivable: Not extracted")
            print(f"    - Debris Removal: ${sublimits.debris_removal_limit:,.0f}" if sublimits.debris_removal_limit else "    - Debris Removal: Not extracted")
            print(f"    - Electronic Data: ${sublimits.electronic_data_media:,.0f}" if sublimits.electronic_data_media else "    - Electronic Data: Not extracted")
            print(f"    - Civil Authority Days: {sublimits.civil_authority_days}" if sublimits.civil_authority_days else "    - Civil Authority Days: Not extracted")
            print(f"    - Civil Authority Limit: ${sublimits.civil_authority_limit:,.0f}" if sublimits.civil_authority_limit else "    - Civil Authority Limit: Not extracted")
            print(f"    - Valuable Papers: ${sublimits.valuable_papers_records:,.0f}" if sublimits.valuable_papers_records else "    - Valuable Papers: Not extracted")
            print(f"    - Extra Expense: ${sublimits.extra_expense:,.0f}" if sublimits.extra_expense else "    - Extra Expense: Not extracted")
            print(f"    - Earth Movement Agg: ${sublimits.earth_movement_aggregate:,.0f}" if sublimits.earth_movement_aggregate else "    - Earth Movement Agg: Not extracted")
            print(f"    - Flood: ${sublimits.flood_aggregate:,.0f}" if sublimits.flood_aggregate else "    - Flood: NOT COVERED")
            print(f"    - Max Limit: ${sublimits.maximum_limit_of_liability:,.0f}" if sublimits.maximum_limit_of_liability else "    - Max Limit: Not extracted")

        # Check deductibles
        if program.deductibles:
            print(f"\n  Deductibles Schedule:")
            deductibles = program.deductibles
            print(f"    - Base Property: ${deductibles.base_property_deductible:,.0f}" if deductibles.base_property_deductible else "    - Base Property: Not extracted")
            print(f"    - Named Storm Min: ${deductibles.named_storm_minimum:,.0f}" if deductibles.named_storm_minimum else "    - Named Storm Min: Not extracted")
            print(f"    - Named Storm %: {deductibles.named_storm_percentage}%" if deductibles.named_storm_percentage else "    - Named Storm %: Not extracted")
            print(f"    - Earth Movement %: {deductibles.earth_movement_percentage}%" if deductibles.earth_movement_percentage else "    - Earth Movement %: Not extracted")
            print(f"    - Earth Movement Min: ${deductibles.earth_movement_minimum:,.0f}" if deductibles.earth_movement_minimum else "    - Earth Movement Min: Not extracted")
            print(f"    - Windstorm %: {deductibles.windstorm_hail_percentage}%" if deductibles.windstorm_hail_percentage else "    - Windstorm %: Not extracted")
            print(f"    - Windstorm Min: ${deductibles.windstorm_hail_minimum:,.0f}" if deductibles.windstorm_hail_minimum else "    - Windstorm Min: Not extracted")

        return {"program": program.model_dump()}

    elif result.policy:
        print("\nPolicy Extraction (should have been Program!):")
        return {"policy": result.policy.model_dump()}

    return {}


def compare_with_expected(extraction_result: dict):
    """Compare extraction results with expected values."""
    print("\n" + "=" * 60)
    print("STEP 3: VALIDATION AGAINST EXPECTED VALUES")
    print("=" * 60)

    if not extraction_result:
        print("\n⚠️  No extraction result to validate")
        return

    program = extraction_result.get("program", {})

    # Check carriers
    print("\nCarriers:")
    expected_carriers = EXPECTED_VALUES["carriers"]
    extracted_carriers = [c.get("carrier_name", "") for c in program.get("carriers", [])]

    for expected in expected_carriers:
        if any(expected.lower() in ec.lower() for ec in extracted_carriers):
            print(f"  ✓ {expected}")
        else:
            print(f"  ✗ MISSING: {expected}")

    # Check sublimits
    print("\nSublimits:")
    sublimits = program.get("sublimits", {})
    expected_sublimits = EXPECTED_VALUES["sublimits"]

    for field, expected_value in expected_sublimits.items():
        actual = sublimits.get(field)
        if actual == expected_value:
            print(f"  ✓ {field}: ${expected_value:,}")
        elif actual:
            print(f"  ~ {field}: got ${actual:,}, expected ${expected_value:,}")
        else:
            print(f"  ✗ {field}: NOT EXTRACTED (expected ${expected_value:,})")

    # Check deductibles
    print("\nDeductibles:")
    deductibles = program.get("deductibles", {})
    expected_deductibles = EXPECTED_VALUES["deductibles"]

    for field, expected_value in expected_deductibles.items():
        actual = deductibles.get(field)
        if actual == expected_value:
            print(f"  ✓ {field}: {expected_value}")
        elif actual:
            print(f"  ~ {field}: got {actual}, expected {expected_value}")
        else:
            print(f"  ✗ {field}: NOT EXTRACTED (expected {expected_value})")


async def main():
    """Run the full pipeline test."""
    print("=" * 60)
    print("FULL PIPELINE TEST: PROP 2324 New Policy")
    print("Using: Gemini 2.5 Flash via OpenRouter")
    print("=" * 60)

    # Load the OCR'd document
    ocr_path = Path(__file__).parent.parent / "sample_docs" / "PROP 2324 New Policy Eff 51723.ocr.md"

    if not ocr_path.exists():
        print(f"\n✗ OCR file not found: {ocr_path}")
        return

    with open(ocr_path, "r") as f:
        ocr_text = f.read()

    print(f"\nLoaded OCR text: {len(ocr_text):,} characters")

    # Step 1: Classification
    class_result = await test_classification(ocr_text)

    # Step 2: Extraction
    if class_result.get("classification"):
        extraction_result = await test_extraction(ocr_text, class_result["classification"])

        # Step 3: Validation
        compare_with_expected(extraction_result)

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
