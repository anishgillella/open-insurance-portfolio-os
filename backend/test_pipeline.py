"""Test script for the ingestion pipeline (without database).

This script tests OCR, Classification, and Extraction on local PDF files.

Usage:
    cd backend
    python test_pipeline.py "../24-25 Eastman Property & Liability proposal (AHJ) V1.pdf"
    python test_pipeline.py "../EMC - Executive South LLC - Freeman Webb Company - COI - 3 01 22.pdf"
"""

import asyncio
import json
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from app.services.ocr_service import OCRService
from app.services.classification_service import ClassificationService
from app.services.extraction_service import ExtractionService


async def test_pipeline(file_path: str) -> None:
    """Test the full ingestion pipeline on a file."""
    path = Path(file_path)

    if not path.exists():
        print(f"ERROR: File not found: {file_path}")
        return

    print("=" * 80)
    print(f"TESTING PIPELINE: {path.name}")
    print("=" * 80)

    # Step 1: OCR
    print("\n[1/3] OCR Processing (Mistral)...")
    print("-" * 40)

    ocr_service = OCRService()
    try:
        ocr_result = await ocr_service.process_file_with_metadata(path)
        markdown_text = ocr_result["markdown"]
        page_count = ocr_result["page_count"]

        print(f"  Pages: {page_count}")
        print(f"  Characters: {len(markdown_text)}")
        print(f"  Preview (first 500 chars):")
        print("  " + "-" * 38)
        preview = markdown_text[:500].replace("\n", "\n  ")
        print(f"  {preview}")
        print("  " + "-" * 38)

        # Save full OCR output for inspection
        ocr_output_path = path.with_suffix(".ocr.md")
        with open(ocr_output_path, "w") as f:
            f.write(markdown_text)
        print(f"\n  Full OCR saved to: {ocr_output_path}")

    except Exception as e:
        print(f"  ERROR: {e}")
        return

    # Step 2: Classification
    print("\n[2/3] Classification (Gemini)...")
    print("-" * 40)

    classification_service = ClassificationService()
    try:
        classification = await classification_service.classify(markdown_text)

        print(f"  Document Type: {classification.document_type.value}")
        if classification.document_subtype:
            print(f"  Subtype: {classification.document_subtype}")
        if classification.policy_type:
            print(f"  Policy Type: {classification.policy_type.value}")
        print(f"  Confidence: {classification.confidence:.2%}")
        print(f"  Carrier: {classification.carrier_name or 'N/A'}")
        print(f"  Policy #: {classification.policy_number or 'N/A'}")
        print(f"  Effective: {classification.effective_date or 'N/A'}")
        print(f"  Expiration: {classification.expiration_date or 'N/A'}")
        print(f"  Insured: {classification.insured_name or 'N/A'}")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Extraction
    print("\n[3/3] Extraction (Gemini)...")
    print("-" * 40)

    extraction_service = ExtractionService()
    try:
        extraction_result = await extraction_service.extract(markdown_text, classification)

        print(f"  Overall Confidence: {extraction_result.overall_confidence:.2%}")

        if extraction_result.policy:
            policy = extraction_result.policy
            print(f"\n  POLICY DETAILS:")
            print(f"    Type: {policy.policy_type.value}")
            print(f"    Number: {policy.policy_number or 'N/A'}")
            print(f"    Carrier: {policy.carrier_name or 'N/A'}")
            print(f"    Effective: {policy.effective_date or 'N/A'}")
            print(f"    Expiration: {policy.expiration_date or 'N/A'}")
            print(f"    Named Insured: {policy.named_insured or 'N/A'}")
            print(f"    Premium: ${policy.premium:,.2f}" if policy.premium else "    Premium: N/A")
            print(f"    Coverages: {len(policy.coverages)}")

            if policy.coverages:
                print(f"\n  COVERAGES:")
                for i, cov in enumerate(policy.coverages[:10], 1):  # Show first 10
                    limit_str = f"${cov.limit_amount:,.0f}" if cov.limit_amount else "N/A"
                    deduct_str = f"${cov.deductible_amount:,.0f}" if cov.deductible_amount else "N/A"
                    print(f"    {i}. {cov.coverage_name}")
                    print(f"       Limit: {limit_str}, Deductible: {deduct_str}")

                if len(policy.coverages) > 10:
                    print(f"    ... and {len(policy.coverages) - 10} more coverages")

        if extraction_result.coi:
            coi = extraction_result.coi
            print(f"\n  COI DETAILS:")
            print(f"    Certificate #: {coi.certificate_number or 'N/A'}")
            print(f"    Insured: {coi.insured_name or 'N/A'}")
            print(f"    Holder: {coi.holder_name or 'N/A'}")
            print(f"    GL Each Occurrence: ${coi.gl_each_occurrence:,.0f}" if coi.gl_each_occurrence else "    GL Each Occurrence: N/A")
            print(f"    GL Aggregate: ${coi.gl_general_aggregate:,.0f}" if coi.gl_general_aggregate else "    GL Aggregate: N/A")
            print(f"    Property Limit: ${coi.property_limit:,.0f}" if coi.property_limit else "    Property Limit: N/A")
            print(f"    Umbrella: ${coi.umbrella_limit:,.0f}" if coi.umbrella_limit else "    Umbrella: N/A")
            print(f"    Policies Referenced: {len(coi.policies)}")

            if coi.policies:
                print(f"\n  POLICIES ON COI:")
                for i, pol in enumerate(coi.policies, 1):
                    print(f"    {i}. {pol.policy_type.value}: {pol.policy_number or 'N/A'} ({pol.carrier_name or 'Unknown'})")

        if extraction_result.proposal:
            proposal = extraction_result.proposal
            print(f"\n  PROPOSAL DETAILS:")
            print(f"    Title: {proposal.proposal_title or 'N/A'}")
            print(f"    Type: {proposal.proposal_type or 'N/A'}")
            print(f"    Insured: {proposal.named_insured or 'N/A'}")
            print(f"    Term: {proposal.effective_date or 'N/A'} to {proposal.expiration_date or 'N/A'}")
            print(f"    Properties: {len(proposal.properties)}")
            print(f"    Carriers: {', '.join(proposal.carriers) if proposal.carriers else 'N/A'}")

            if proposal.portfolio_expiring_premium:
                print(f"\n  PORTFOLIO SUMMARY:")
                print(f"    Expiring Premium: ${proposal.portfolio_expiring_premium:,.0f}")
                print(f"    Renewal Premium: ${proposal.portfolio_renewal_premium:,.0f}" if proposal.portfolio_renewal_premium else "")
                if proposal.portfolio_premium_change:
                    print(f"    Change: ${proposal.portfolio_premium_change:,.0f} ({proposal.portfolio_premium_change_pct:.1%})" if proposal.portfolio_premium_change_pct else f"    Change: ${proposal.portfolio_premium_change:,.0f}")

            if proposal.properties:
                print(f"\n  PROPERTIES:")
                for i, prop in enumerate(proposal.properties, 1):
                    print(f"    {i}. {prop.property_name or 'Unknown'}")
                    if prop.unit_count:
                        print(f"       Units: {prop.unit_count}")
                    if prop.total_insured_value:
                        print(f"       TIV: ${prop.total_insured_value:,.0f}")
                    if prop.renewal_total_premium:
                        print(f"       Renewal Premium: ${prop.renewal_total_premium:,.0f}")
                    if prop.price_per_door_renewal:
                        print(f"       Price/Door: ${prop.price_per_door_renewal:,.0f}")

                    if prop.coverages:
                        print(f"       Coverages:")
                        for cov in prop.coverages[:5]:
                            exp = f"${cov.expiring_premium:,.0f}" if cov.expiring_premium else "N/A"
                            ren = f"${cov.renewal_premium:,.0f}" if cov.renewal_premium else "N/A"
                            carrier = f" ({cov.carrier_name})" if cov.carrier_name else ""
                            print(f"         - {cov.coverage_type}{carrier}: {exp} -> {ren}")

        # Save full extraction as JSON
        extraction_output_path = path.with_suffix(".extraction.json")
        with open(extraction_output_path, "w") as f:
            json.dump(extraction_result.model_dump(mode="json"), f, indent=2, default=str)
        print(f"\n  Full extraction saved to: {extraction_output_path}")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline.py <file_path>")
        print("\nAvailable PDFs:")
        for pdf in Path("..").glob("*.pdf"):
            print(f"  {pdf}")
        return

    file_path = sys.argv[1]
    await test_pipeline(file_path)


if __name__ == "__main__":
    asyncio.run(main())
