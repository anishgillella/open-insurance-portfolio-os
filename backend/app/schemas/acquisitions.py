"""Schemas for Acquisition Calculator feature.

This module defines the request/response models for the acquisition
premium estimation endpoint.
"""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class AcquisitionCalculateRequest(BaseModel):
    """Request schema for acquisition calculation."""

    # Property Identification
    address: str = Field(
        ...,
        description="Full street address of the property",
        min_length=1,
        examples=["123 East Street, Fort Wayne, IN 46802"],
    )
    link: str | None = Field(
        default=None,
        description="Optional URL to property listing",
    )

    # Building Characteristics
    unit_count: int = Field(
        ...,
        ge=1,
        description="Total number of units",
        examples=[150],
    )
    vintage: int = Field(
        ...,
        ge=1800,
        le=2030,
        description="Year the property was built",
        examples=[2002],
    )
    stories: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of stories/floors",
        examples=[3],
    )
    total_buildings: int = Field(
        ...,
        ge=1,
        description="Total number of buildings on property",
        examples=[3],
    )
    total_sf: int = Field(
        ...,
        ge=100,
        description="Total gross square footage",
        examples=[40000],
    )

    # Financial & Occupancy
    current_occupancy_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Current occupancy percentage (0-100)",
        examples=[80.0],
    )
    estimated_annual_income: Decimal = Field(
        ...,
        ge=0,
        description="Estimated gross annual income",
        examples=[1000000],
    )

    # Additional Context
    notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional notes about the property",
        examples=["Next to a lakefront, recently renovated lobby"],
    )


class PremiumRange(BaseModel):
    """Premium range with low/mid/high estimates."""

    low: Decimal = Field(
        ...,
        description="Lower bound premium estimate ($/unit)",
        examples=[100],
    )
    mid: Decimal = Field(
        ...,
        description="Mid-point premium estimate ($/unit)",
        examples=[200],
    )
    high: Decimal = Field(
        ...,
        description="Upper bound premium estimate ($/unit)",
        examples=[800],
    )


class ComparableProperty(BaseModel):
    """A comparable property with premium data."""

    property_id: str = Field(
        ...,
        description="Unique identifier of the comparable property",
    )
    name: str = Field(
        ...,
        description="Property name",
        examples=["Shoaff Park Apartments"],
    )
    address: str = Field(
        ...,
        description="Property address",
        examples=["Fort Wayne, IN"],
    )
    premium_per_unit: Decimal = Field(
        ...,
        description="Premium per unit ($/unit)",
        examples=[1827],
    )
    premium_date: date = Field(
        ...,
        description="Date of the premium data",
        examples=["2025-06-15"],
    )
    similarity_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="LLM-assigned similarity score (0-100)",
        examples=[85],
    )
    similarity_reason: str | None = Field(
        default=None,
        description="LLM explanation of why this property is comparable",
    )


class RiskFactor(BaseModel):
    """An insurance risk factor identified by LLM."""

    name: str = Field(
        ...,
        description="Risk factor name",
        examples=["Flood Zone"],
    )
    severity: Literal["info", "warning", "critical"] = Field(
        ...,
        description="Severity level of the risk",
    )
    reason: str | None = Field(
        default=None,
        description="LLM explanation of why this risk applies",
        examples=["Address mentions lakefront proximity"],
    )


class AcquisitionCalculateResponse(BaseModel):
    """Complete response from acquisition calculation."""

    # Uniqueness Detection
    is_unique: bool = Field(
        ...,
        description="True if property is too unique for automated pricing",
    )
    uniqueness_reason: str | None = Field(
        default=None,
        description="LLM explanation of why property is unique",
    )

    # Confidence
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="Confidence level in the estimate",
    )

    # Premium Estimates
    premium_range: PremiumRange | None = Field(
        default=None,
        description="Premium range estimates ($/unit)",
    )
    premium_range_label: str | None = Field(
        default=None,
        description="Human-readable premium range description",
        examples=["medium range ($200-$800)"],
    )

    # For unique properties
    preliminary_estimate: PremiumRange | None = Field(
        default=None,
        description="Best-guess estimate for unique properties",
    )

    # User Message
    message: str | None = Field(
        default=None,
        description="User-friendly summary or action message",
    )

    # Comparable Properties
    comparables: list[ComparableProperty] = Field(
        default_factory=list,
        description="List of comparable properties used in calculation",
    )

    # Risk Factors
    risk_factors: list[RiskFactor] = Field(
        default_factory=list,
        description="Identified risk factors affecting premium",
    )

    # LLM Explanation
    llm_explanation: str | None = Field(
        default=None,
        description="LLM's overall explanation of the analysis",
    )
