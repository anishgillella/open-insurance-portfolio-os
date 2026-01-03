"""Generic Merge Service for Combining Chunk Extractions.

This service provides a flexible framework for merging multiple partial
extractions from document chunks into a single cohesive result.

Features:
- Configurable merge strategies per field
- Automatic deduplication for list fields
- Confidence-based conflict resolution
- Support for nested objects
"""

import logging
import statistics
from enum import Enum
from typing import Any, Dict, List, Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class MergeStrategy(str, Enum):
    """Strategies for merging field values from multiple extractions."""

    # Take first non-null value (good for metadata from early chunks)
    FIRST_NON_NULL = "first_non_null"

    # Take last non-null value
    LAST_NON_NULL = "last_non_null"

    # Take value with highest confidence score
    HIGHEST_CONFIDENCE = "highest_confidence"

    # Merge lists, deduplicate by key
    CONCATENATE_LISTS = "concatenate_lists"

    # Sum numeric values
    SUM = "sum"

    # Take maximum value
    MAX = "max"

    # Take minimum value
    MIN = "min"

    # Take most frequently occurring value
    MOST_COMMON = "most_common"

    # Average numeric values
    AVERAGE = "average"

    # Merge dictionaries (update)
    MERGE_DICT = "merge_dict"


class FieldMergeRule:
    """Rule for merging a specific field."""

    def __init__(
        self,
        strategy: MergeStrategy,
        dedup_key: str | None = None,  # For list deduplication
        confidence_field: str = "confidence",  # Field containing confidence score
    ):
        """Initialize merge rule.

        Args:
            strategy: The merge strategy to use.
            dedup_key: For lists, the key to use for deduplication.
            confidence_field: Field name containing confidence scores.
        """
        self.strategy = strategy
        self.dedup_key = dedup_key
        self.confidence_field = confidence_field


# Default merge rules for common insurance document fields
DEFAULT_MERGE_RULES: Dict[str, FieldMergeRule] = {
    # Metadata fields - take first (usually from declarations page)
    "policy_number": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    "account_number": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    "insured_name": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    "named_insured": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    "carrier_name": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    "effective_date": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    "expiration_date": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    "certificate_number": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    "producer_name": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    "program_name": FieldMergeRule(MergeStrategy.FIRST_NON_NULL),
    # List fields - concatenate and deduplicate
    "coverages": FieldMergeRule(
        MergeStrategy.CONCATENATE_LISTS, dedup_key="coverage_name"
    ),
    "carriers": FieldMergeRule(
        MergeStrategy.CONCATENATE_LISTS, dedup_key="carrier_name"
    ),
    "policies": FieldMergeRule(
        MergeStrategy.CONCATENATE_LISTS, dedup_key="policy_number"
    ),
    "locations": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS, dedup_key="address"),
    "properties": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS, dedup_key="address"),
    "endorsements": FieldMergeRule(
        MergeStrategy.CONCATENATE_LISTS, dedup_key="endorsement_number"
    ),
    "exclusions": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS),
    "additional_insureds": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS),
    "special_conditions": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS),
    "major_exclusions": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS),
    "additional_named_insureds": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS),
    "lloyds_syndicates": FieldMergeRule(
        MergeStrategy.CONCATENATE_LISTS, dedup_key="syndicate_number"
    ),
    "valuation_bases": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS),
    "restrictions": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS),
    "service_of_suit": FieldMergeRule(
        MergeStrategy.CONCATENATE_LISTS, dedup_key="carrier_name"
    ),
    "forms_schedule": FieldMergeRule(
        MergeStrategy.CONCATENATE_LISTS, dedup_key="form_number"
    ),
    "source_pages": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS),
    "line_items": FieldMergeRule(MergeStrategy.CONCATENATE_LISTS),
    # Numeric fields - take max (usually the correct total)
    "total_premium": FieldMergeRule(MergeStrategy.MAX),
    "total_cost": FieldMergeRule(MergeStrategy.MAX),
    "total_insured_value": FieldMergeRule(MergeStrategy.MAX),
    "total_amount": FieldMergeRule(MergeStrategy.MAX),
    "premium": FieldMergeRule(MergeStrategy.MAX),
    # Dict fields - merge
    "insurers": FieldMergeRule(MergeStrategy.MERGE_DICT),
    "premium_by_state": FieldMergeRule(MergeStrategy.MERGE_DICT),
    "state_notices": FieldMergeRule(MergeStrategy.MERGE_DICT),
    "carrier_premiums": FieldMergeRule(MergeStrategy.MERGE_DICT),
    # Confidence - average
    "confidence": FieldMergeRule(MergeStrategy.AVERAGE),
}


class MergeService:
    """Service for merging multiple extractions into one."""

    def __init__(self, custom_rules: Dict[str, FieldMergeRule] | None = None):
        """Initialize merge service.

        Args:
            custom_rules: Custom merge rules to add/override defaults.
        """
        self.rules = {**DEFAULT_MERGE_RULES, **(custom_rules or {})}

    def merge(self, extractions: List[T], schema: Type[T] | None = None) -> T:
        """Merge multiple extractions into a single result.

        Args:
            extractions: List of extraction results (ordered by chunk index).
            schema: Pydantic schema class (optional, inferred from first item).

        Returns:
            Merged extraction result.

        Raises:
            ValueError: If extractions list is empty.
        """
        if not extractions:
            raise ValueError("Cannot merge empty extraction list")

        if len(extractions) == 1:
            return extractions[0]

        # Infer schema from first extraction
        if schema is None:
            schema = type(extractions[0])

        # Convert to dicts for easier manipulation
        dicts = [e.model_dump() for e in extractions]

        # Get all field names from all extractions
        field_names = set()
        for d in dicts:
            field_names.update(d.keys())

        # Merge each field
        merged_data = {}
        for field_name in field_names:
            values = [d.get(field_name) for d in dicts]
            rule = self.rules.get(field_name, FieldMergeRule(MergeStrategy.FIRST_NON_NULL))
            merged_data[field_name] = self._merge_field(values, rule)

        return schema.model_validate(merged_data)

    def merge_with_indices(
        self,
        extractions: List[T],
        chunk_indices: List[int],
        schema: Type[T] | None = None,
    ) -> T:
        """Merge extractions with chunk index ordering.

        Sorts extractions by chunk index before merging, ensuring
        early chunks (declaration pages) are prioritized for metadata.

        Args:
            extractions: List of extraction results.
            chunk_indices: Original chunk indices for each extraction.
            schema: Pydantic schema class.

        Returns:
            Merged extraction result.
        """
        if len(extractions) != len(chunk_indices):
            raise ValueError("Extractions and indices must have same length")

        # Sort by chunk index
        indexed = list(zip(chunk_indices, extractions))
        indexed.sort(key=lambda x: x[0])
        sorted_extractions = [e for _, e in indexed]

        return self.merge(sorted_extractions, schema)

    def _merge_field(self, values: List[Any], rule: FieldMergeRule) -> Any:
        """Merge a single field according to its rule.

        Args:
            values: List of values for this field from all extractions.
            rule: The merge rule to apply.

        Returns:
            Merged field value.
        """
        # Filter out None values for most strategies
        non_null = [v for v in values if v is not None]

        if not non_null:
            return None

        match rule.strategy:
            case MergeStrategy.FIRST_NON_NULL:
                return non_null[0]

            case MergeStrategy.LAST_NON_NULL:
                return non_null[-1]

            case MergeStrategy.CONCATENATE_LISTS:
                return self._merge_lists(non_null, rule.dedup_key)

            case MergeStrategy.SUM:
                nums = [v for v in non_null if isinstance(v, (int, float))]
                return sum(nums) if nums else None

            case MergeStrategy.MAX:
                nums = [v for v in non_null if isinstance(v, (int, float))]
                return max(nums) if nums else None

            case MergeStrategy.MIN:
                nums = [v for v in non_null if isinstance(v, (int, float))]
                return min(nums) if nums else None

            case MergeStrategy.AVERAGE:
                nums = [v for v in non_null if isinstance(v, (int, float))]
                return statistics.mean(nums) if nums else None

            case MergeStrategy.MOST_COMMON:
                try:
                    # For hashable values
                    hashable = [v for v in non_null if isinstance(v, (str, int, float, bool))]
                    return statistics.mode(hashable) if hashable else non_null[0]
                except statistics.StatisticsError:
                    return non_null[0]

            case MergeStrategy.MERGE_DICT:
                return self._merge_dicts(non_null)

            case MergeStrategy.HIGHEST_CONFIDENCE:
                # Requires items to have confidence field
                return self._get_highest_confidence(non_null, rule.confidence_field)

            case _:
                return non_null[0]

    def _merge_lists(self, lists: List[List], dedup_key: str | None) -> List:
        """Merge multiple lists with optional deduplication.

        Args:
            lists: List of lists to merge.
            dedup_key: Key to use for deduplication (for list of dicts).

        Returns:
            Merged and deduplicated list.
        """
        all_items = []
        for lst in lists:
            if isinstance(lst, list):
                all_items.extend(lst)
            elif isinstance(lst, set):
                all_items.extend(list(lst))

        if not all_items:
            return []

        if not dedup_key:
            # For simple values, deduplicate by value
            if all(isinstance(item, (str, int, float)) for item in all_items):
                return list(dict.fromkeys(all_items))  # Preserves order
            return all_items

        # Deduplicate dicts by key, keeping highest confidence
        seen: Dict[Any, Any] = {}
        for item in all_items:
            if isinstance(item, dict):
                key_value = item.get(dedup_key)
                if key_value is None:
                    # No key, just add it
                    seen[id(item)] = item
                    continue

                # Normalize key for comparison
                key = key_value.lower() if isinstance(key_value, str) else key_value

                existing = seen.get(key)
                if existing is None:
                    seen[key] = item
                else:
                    # Keep item with higher confidence
                    new_conf = item.get("confidence", 0) or 0
                    old_conf = existing.get("confidence", 0) or 0
                    if new_conf > old_conf:
                        seen[key] = item
            elif hasattr(item, "model_dump"):
                # Pydantic model
                item_dict = item.model_dump()
                key_value = item_dict.get(dedup_key)
                key = key_value.lower() if isinstance(key_value, str) else key_value
                if key not in seen:
                    seen[key] = item
            else:
                # Unknown type, just add
                seen[id(item)] = item

        return list(seen.values())

    def _merge_dicts(self, dicts: List[Dict]) -> Dict:
        """Merge multiple dictionaries.

        Later values override earlier ones.

        Args:
            dicts: List of dictionaries to merge.

        Returns:
            Merged dictionary.
        """
        result = {}
        for d in dicts:
            if isinstance(d, dict):
                result.update(d)
        return result

    def _get_highest_confidence(
        self, items: List[Any], confidence_field: str
    ) -> Any:
        """Get item with highest confidence score.

        Args:
            items: List of items (dicts or objects with confidence).
            confidence_field: Name of the confidence field.

        Returns:
            Item with highest confidence.
        """
        best = items[0]
        best_conf = 0

        for item in items:
            if isinstance(item, dict):
                conf = item.get(confidence_field, 0) or 0
            elif hasattr(item, confidence_field):
                conf = getattr(item, confidence_field, 0) or 0
            else:
                conf = 0

            if conf > best_conf:
                best = item
                best_conf = conf

        return best


# Singleton instance
_merge_service: MergeService | None = None


def get_merge_service() -> MergeService:
    """Get or create merge service instance."""
    global _merge_service
    if _merge_service is None:
        _merge_service = MergeService()
    return _merge_service
