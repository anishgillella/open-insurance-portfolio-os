"""Custom Validation Service for Extracted Insurance Data.

This service provides a framework for registering and running custom
validation functions on extracted data. It supports:

- Built-in insurance-specific validators
- User-defined custom validators
- Field-level and document-level validation
- Validation with warnings vs errors
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Dict, List

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Type for validation functions
# Returns (is_valid, error_message_or_none)
ValidatorFn = Callable[[Any], tuple[bool, str | None]]


@dataclass
class ValidationResult:
    """Result of running validators on extracted data."""

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add a validation error."""
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a validation warning (doesn't affect is_valid)."""
        self.warnings.append(message)

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one."""
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


class ValidationService:
    """Service for custom validation of extracted insurance data."""

    def __init__(self, register_defaults: bool = True):
        """Initialize validation service.

        Args:
            register_defaults: Whether to register default insurance validators.
        """
        self.validators: Dict[str, List[ValidatorFn]] = {}
        self.document_validators: List[Callable[[BaseModel], ValidationResult]] = []

        if register_defaults:
            self._register_default_validators()

    def register_validator(self, field_path: str, validator: ValidatorFn) -> None:
        """Register a custom validator for a field.

        Args:
            field_path: Dot-notation path to field (e.g., "policy.coverages.limit").
            validator: Function that takes a value and returns (is_valid, error_msg).
        """
        if field_path not in self.validators:
            self.validators[field_path] = []
        self.validators[field_path].append(validator)

    def register_document_validator(
        self, validator: Callable[[BaseModel], ValidationResult]
    ) -> None:
        """Register a document-level validator.

        Args:
            validator: Function that takes the full extraction and returns ValidationResult.
        """
        self.document_validators.append(validator)

    def validate(self, data: BaseModel) -> ValidationResult:
        """Run all validators on extracted data.

        Args:
            data: Pydantic model with extracted data.

        Returns:
            ValidationResult with errors and warnings.
        """
        result = ValidationResult()
        data_dict = data.model_dump()

        # Run field-level validators
        for field_path, validators in self.validators.items():
            value = self._get_nested_value(data_dict, field_path)

            # Skip validation if field doesn't exist
            if value is None:
                continue

            for validator in validators:
                try:
                    is_valid, error = validator(value)
                    if not is_valid and error:
                        result.add_error(f"{field_path}: {error}")
                except Exception as e:
                    logger.warning(f"Validator for {field_path} raised exception: {e}")
                    result.add_warning(f"{field_path}: Validator error - {e}")

        # Run document-level validators
        for doc_validator in self.document_validators:
            try:
                doc_result = doc_validator(data)
                result.merge(doc_result)
            except Exception as e:
                logger.warning(f"Document validator raised exception: {e}")
                result.add_warning(f"Document validation error: {e}")

        return result

    def validate_dict(self, data: Dict[str, Any]) -> ValidationResult:
        """Run validators on a dictionary (for pre-Pydantic validation).

        Args:
            data: Dictionary with extracted data.

        Returns:
            ValidationResult with errors and warnings.
        """
        result = ValidationResult()

        for field_path, validators in self.validators.items():
            value = self._get_nested_value(data, field_path)

            if value is None:
                continue

            for validator in validators:
                try:
                    is_valid, error = validator(value)
                    if not is_valid and error:
                        result.add_error(f"{field_path}: {error}")
                except Exception as e:
                    logger.warning(f"Validator for {field_path} raised exception: {e}")

        return result

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dict using dot notation.

        Args:
            data: Dictionary to search.
            path: Dot-notation path (e.g., "policy.coverages").

        Returns:
            Value at path, or None if not found.
        """
        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                idx = int(key)
                value = value[idx] if idx < len(value) else None
            else:
                return None

            if value is None:
                return None

        return value

    def _register_default_validators(self) -> None:
        """Register default insurance-specific validators."""

        # Policy number format
        self.register_validator(
            "policy_number",
            lambda v: (
                bool(v and len(str(v)) >= 3),
                "Policy number must be at least 3 characters" if v else None,
            ),
        )

        # Date validations
        self.register_validator("effective_date", self._validate_date)
        self.register_validator("expiration_date", self._validate_date)
        self.register_validator("issue_date", self._validate_date)

        # Premium validation
        self.register_validator(
            "total_premium",
            lambda v: (
                v is None or (isinstance(v, (int, float)) and v >= 0),
                f"Premium must be a non-negative number, got: {v}",
            ),
        )
        self.register_validator(
            "premium",
            lambda v: (
                v is None or (isinstance(v, (int, float)) and v >= 0),
                f"Premium must be a non-negative number, got: {v}",
            ),
        )

        # Coverage limit validation
        self.register_validator("coverages", self._validate_coverages)

        # Confidence score validation
        self.register_validator(
            "confidence",
            lambda v: (
                v is None or (isinstance(v, (int, float)) and 0 <= v <= 1),
                f"Confidence must be between 0 and 1, got: {v}",
            ),
        )

        # Register document-level validator for date consistency
        self.register_document_validator(self._validate_date_consistency)

    @staticmethod
    def _validate_date(value: Any) -> tuple[bool, str | None]:
        """Validate date format.

        Args:
            value: Date value (string or date object).

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value is None:
            return True, None

        if isinstance(value, date):
            return True, None

        if isinstance(value, str):
            # Check YYYY-MM-DD format
            date_pattern = r"^\d{4}-\d{2}-\d{2}$"
            if not re.match(date_pattern, value):
                return False, f"Date must be in YYYY-MM-DD format, got: {value}"

            # Try to parse the date
            try:
                parts = value.split("-")
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if not (1900 <= year <= 2100):
                    return False, f"Year must be between 1900-2100, got: {year}"
                if not (1 <= month <= 12):
                    return False, f"Month must be between 1-12, got: {month}"
                if not (1 <= day <= 31):
                    return False, f"Day must be between 1-31, got: {day}"
                return True, None
            except (ValueError, IndexError):
                return False, f"Invalid date format: {value}"

        return False, f"Date must be string or date object, got: {type(value).__name__}"

    @staticmethod
    def _validate_coverages(coverages: Any) -> tuple[bool, str | None]:
        """Validate coverage data.

        Args:
            coverages: List of coverage dictionaries.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not coverages:
            return True, None

        if not isinstance(coverages, list):
            return False, f"Coverages must be a list, got: {type(coverages).__name__}"

        for i, cov in enumerate(coverages):
            if isinstance(cov, dict):
                if not cov.get("coverage_name"):
                    return False, f"Coverage {i} missing coverage_name"

                # Validate limit if present
                limit = cov.get("limit_amount")
                if limit is not None and not isinstance(limit, (int, float)):
                    return False, f"Coverage {i} limit must be numeric, got: {type(limit).__name__}"

        return True, None

    @staticmethod
    def _validate_date_consistency(data: BaseModel) -> ValidationResult:
        """Validate that expiration date is after effective date.

        Args:
            data: Full extraction model.

        Returns:
            ValidationResult with any date consistency errors.
        """
        result = ValidationResult()
        data_dict = data.model_dump()

        effective = data_dict.get("effective_date")
        expiration = data_dict.get("expiration_date")

        if effective and expiration:
            try:
                if isinstance(effective, str):
                    effective = date.fromisoformat(effective)
                if isinstance(expiration, str):
                    expiration = date.fromisoformat(expiration)

                if effective > expiration:
                    result.add_error(
                        f"Effective date ({effective}) is after expiration date ({expiration})"
                    )
            except (ValueError, TypeError):
                # Date parsing already validated elsewhere
                pass

        return result


# Factory function for creating validation service with custom rules
def create_validation_service(
    custom_validators: Dict[str, List[ValidatorFn]] | None = None,
    include_defaults: bool = True,
) -> ValidationService:
    """Create a validation service with optional custom validators.

    Args:
        custom_validators: Dict mapping field paths to validator functions.
        include_defaults: Whether to include default insurance validators.

    Returns:
        Configured ValidationService instance.
    """
    service = ValidationService(register_defaults=include_defaults)

    if custom_validators:
        for field_path, validators in custom_validators.items():
            for validator in validators:
                service.register_validator(field_path, validator)

    return service


# Singleton instance with defaults
_validation_service: ValidationService | None = None


def get_validation_service() -> ValidationService:
    """Get or create validation service instance."""
    global _validation_service
    if _validation_service is None:
        _validation_service = ValidationService()
    return _validation_service
