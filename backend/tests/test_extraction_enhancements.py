"""Tests for LLM Extraction Enhancements.

Tests for:
- JSON mode and validation retry
- Chunking service
- Merge service
- Validation service
"""

import pytest
from datetime import date

from app.services.chunking_service import ChunkingService, DocumentChunk
from app.services.merge_service import MergeService, MergeStrategy, FieldMergeRule
from app.services.validation_service import ValidationService, ValidationResult
from app.services.extraction_service import ExtractionConfig, DEFAULT_CONFIG
from app.schemas.document import PolicyExtraction, CoverageExtraction, PolicyType


class TestChunkingService:
    """Tests for ChunkingService."""

    def test_small_document_single_chunk(self):
        """Small documents should return a single chunk."""
        service = ChunkingService(single_pass_threshold=1000)
        text = "Small document content."

        chunks = service.chunk_document(text)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].index == 0

    def test_large_document_multiple_chunks(self):
        """Large documents should be split into multiple chunks."""
        service = ChunkingService(max_chars=100, overlap_chars=10, single_pass_threshold=100)
        text = "A" * 250  # 250 chars, should split into 3+ chunks

        chunks = service.chunk_document(text)

        assert len(chunks) > 1
        # Check that chunks have proper indices
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_page_boundary_splitting(self):
        """Should prefer splitting on page boundaries."""
        service = ChunkingService(max_chars=100, overlap_chars=10, single_pass_threshold=100)
        text = "Content before. " * 5 + "<!-- Page 2 --> " + "Content after. " * 5

        chunks = service.chunk_document(text)

        # At least one chunk should end at or near a page boundary
        assert any("<!-- Page 2 -->" in chunk.content for chunk in chunks)

    def test_chunk_page_tracking(self):
        """Chunks should track their page ranges."""
        service = ChunkingService(max_chars=200, overlap_chars=20, single_pass_threshold=200)
        text = "<!-- Page 1 --> Page 1 content. <!-- Page 2 --> Page 2 content. <!-- Page 3 --> Page 3 content."

        chunks = service.chunk_document(text)

        # Each chunk should have page info
        for chunk in chunks:
            assert chunk.start_page is not None

    def test_chunk_context_string(self):
        """Should generate proper context strings for chunks."""
        service = ChunkingService()
        chunks = [
            DocumentChunk(index=0, content="", start_page=1, end_page=3, char_start=0, char_end=100),
            DocumentChunk(index=1, content="", start_page=4, end_page=5, char_start=100, char_end=200),
        ]

        context = service.get_chunk_context(chunks, 0)
        assert "Chunk 1 of 2" in context
        assert "pages 1-3" in context


class TestMergeService:
    """Tests for MergeService."""

    def test_merge_single_extraction(self):
        """Single extraction should be returned as-is."""
        service = MergeService()
        extraction = PolicyExtraction(
            policy_type=PolicyType.PROPERTY,
            policy_number="POL-123",
            carrier_name="Test Carrier",
        )

        result = service.merge([extraction])

        assert result.policy_number == "POL-123"
        assert result.carrier_name == "Test Carrier"

    def test_merge_first_non_null_strategy(self):
        """FIRST_NON_NULL should take first non-null value."""
        service = MergeService()
        ext1 = PolicyExtraction(policy_type=PolicyType.PROPERTY, policy_number="POL-001")
        ext2 = PolicyExtraction(policy_type=PolicyType.PROPERTY, policy_number="POL-002")

        result = service.merge([ext1, ext2])

        # First extraction's policy_number should win
        assert result.policy_number == "POL-001"

    def test_merge_concatenate_lists_strategy(self):
        """CONCATENATE_LISTS should merge and deduplicate lists."""
        service = MergeService()
        ext1 = PolicyExtraction(
            policy_type=PolicyType.PROPERTY,
            coverages=[
                CoverageExtraction(coverage_name="Building", limit_amount=1000000, confidence=0.8),
            ],
        )
        ext2 = PolicyExtraction(
            policy_type=PolicyType.PROPERTY,
            coverages=[
                CoverageExtraction(coverage_name="Building", limit_amount=1000000, confidence=0.9),
                CoverageExtraction(coverage_name="Contents", limit_amount=500000, confidence=0.85),
            ],
        )

        result = service.merge([ext1, ext2])

        # Should have 2 unique coverages (Building deduped, higher confidence kept)
        assert len(result.coverages) == 2
        coverage_names = {c.coverage_name for c in result.coverages}
        assert coverage_names == {"Building", "Contents"}

        # Higher confidence Building should win
        building = next(c for c in result.coverages if c.coverage_name == "Building")
        assert building.confidence == 0.9

    def test_merge_max_strategy(self):
        """MAX should take maximum numeric value."""
        service = MergeService()
        ext1 = PolicyExtraction(policy_type=PolicyType.PROPERTY, premium=10000)
        ext2 = PolicyExtraction(policy_type=PolicyType.PROPERTY, premium=15000)

        result = service.merge([ext1, ext2])

        assert result.premium == 15000

    def test_merge_average_strategy(self):
        """AVERAGE should average numeric values."""
        service = MergeService()
        ext1 = PolicyExtraction(policy_type=PolicyType.PROPERTY, confidence=0.8)
        ext2 = PolicyExtraction(policy_type=PolicyType.PROPERTY, confidence=0.9)

        result = service.merge([ext1, ext2])

        assert result.confidence == 0.85

    def test_merge_with_indices(self):
        """Should properly order extractions by chunk indices."""
        service = MergeService()
        # Extractions in wrong order
        ext1 = PolicyExtraction(policy_type=PolicyType.PROPERTY, policy_number="SECOND")
        ext2 = PolicyExtraction(policy_type=PolicyType.PROPERTY, policy_number="FIRST")

        # ext2 (index 0) should be processed first
        result = service.merge_with_indices([ext1, ext2], [1, 0])

        assert result.policy_number == "FIRST"


class TestValidationService:
    """Tests for ValidationService."""

    def test_validate_valid_extraction(self):
        """Valid extraction should pass validation."""
        service = ValidationService()
        extraction = PolicyExtraction(
            policy_type=PolicyType.PROPERTY,
            policy_number="POL-123456",
            effective_date=date(2024, 1, 1),
            expiration_date=date(2025, 1, 1),
            confidence=0.9,
        )

        result = service.validate(extraction)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_invalid_policy_number(self):
        """Short policy number should fail validation."""
        service = ValidationService()
        extraction = PolicyExtraction(
            policy_type=PolicyType.PROPERTY,
            policy_number="AB",  # Too short
        )

        result = service.validate(extraction)

        assert not result.is_valid
        assert any("policy_number" in error for error in result.errors)

    def test_validate_date_consistency(self):
        """Effective date after expiration should fail."""
        service = ValidationService()
        extraction = PolicyExtraction(
            policy_type=PolicyType.PROPERTY,
            policy_number="POL-123456",
            effective_date=date(2025, 1, 1),  # After expiration
            expiration_date=date(2024, 1, 1),
        )

        result = service.validate(extraction)

        assert not result.is_valid
        assert any("after expiration" in error for error in result.errors)

    def test_validate_negative_premium(self):
        """Negative premium should fail validation."""
        service = ValidationService()
        extraction = PolicyExtraction(
            policy_type=PolicyType.PROPERTY,
            policy_number="POL-123456",
            premium=-1000,
        )

        result = service.validate(extraction)

        assert not result.is_valid
        assert any("premium" in error.lower() for error in result.errors)

    def test_custom_validator_registration(self):
        """Should be able to register custom validators."""
        service = ValidationService(register_defaults=False)

        # Register a custom validator
        service.register_validator(
            "carrier_name",
            lambda v: (v != "UNKNOWN", "Carrier name cannot be UNKNOWN"),
        )

        extraction = PolicyExtraction(
            policy_type=PolicyType.PROPERTY,
            carrier_name="UNKNOWN",
        )

        result = service.validate(extraction)

        assert not result.is_valid
        assert any("UNKNOWN" in error for error in result.errors)

    def test_validation_result_merge(self):
        """ValidationResult.merge should combine results."""
        result1 = ValidationResult()
        result1.add_error("Error 1")
        result1.add_warning("Warning 1")

        result2 = ValidationResult()
        result2.add_error("Error 2")

        result1.merge(result2)

        assert not result1.is_valid
        assert len(result1.errors) == 2
        assert len(result1.warnings) == 1


class TestExtractionConfig:
    """Tests for ExtractionConfig."""

    def test_default_config_values(self):
        """Default config should have expected values."""
        config = DEFAULT_CONFIG

        assert config.use_json_mode is True
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.backoff_multiplier == 2.0
        assert config.max_chunk_chars == 50000
        assert config.chunk_overlap_chars == 2000

    def test_custom_config(self):
        """Should be able to create custom config."""
        config = ExtractionConfig(
            use_json_mode=False,
            max_retries=5,
            max_chunk_chars=30000,
        )

        assert config.use_json_mode is False
        assert config.max_retries == 5
        assert config.max_chunk_chars == 30000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
