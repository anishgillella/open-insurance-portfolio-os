"""Common Pydantic schemas used across the API.

This module provides shared schemas for API responses including
error handling and standard response structures.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Error Schemas
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error context"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail


# ---------------------------------------------------------------------------
# List Response Schemas
# ---------------------------------------------------------------------------


class ListResponse(BaseModel, Generic[T]):
    """Generic list response with total count."""

    items: list[T]
    total_count: int = Field(..., description="Total number of items")


# ---------------------------------------------------------------------------
# Address Schema
# ---------------------------------------------------------------------------


class AddressSchema(BaseModel):
    """Property address information."""

    street: str | None = Field(default=None, description="Street address")
    city: str | None = Field(default=None, description="City")
    state: str | None = Field(default=None, description="State code")
    zip: str | None = Field(default=None, description="ZIP code")
    county: str | None = Field(default=None, description="County")
    country: str = Field(default="US", description="Country code")


# ---------------------------------------------------------------------------
# Timestamp Mixin
# ---------------------------------------------------------------------------


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps."""

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# ID Response
# ---------------------------------------------------------------------------


class IDResponse(BaseModel):
    """Response containing just an ID."""

    id: str = Field(..., description="Resource ID")
    message: str | None = Field(default=None, description="Optional message")
