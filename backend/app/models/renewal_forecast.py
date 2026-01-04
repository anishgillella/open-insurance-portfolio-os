"""Renewal Forecast model - Premium predictions and renewal intelligence."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.insurance_program import InsuranceProgram
    from app.models.policy import Policy
    from app.models.property import Property


class RenewalForecast(BaseModel):
    """Renewal Forecast model for premium predictions.

    Combines rule-based point estimates with LLM-generated range predictions.
    Stores factor-by-factor analysis and reasoning for transparency.
    """

    __tablename__ = "renewal_forecasts"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("insurance_programs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    policy_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("policies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Renewal Context
    renewal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    current_expiration_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    current_premium: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )

    # Rule-Based Point Estimate
    rule_based_estimate: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    rule_based_change_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # e.g., +7.5%

    # LLM Range Prediction
    llm_predicted_low: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    llm_predicted_mid: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    llm_predicted_high: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    llm_confidence_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 0-100

    # Factor Breakdown (JSONB for flexibility)
    # Structure: {
    #   "loss_history": {"weight": 0.30, "impact": +2.5, "reasoning": "..."},
    #   "market_trends": {"weight": 0.25, "impact": +6.0, "reasoning": "..."},
    #   "property_changes": {"weight": 0.15, "impact": 0, "reasoning": "..."},
    #   "coverage_changes": {"weight": 0.15, "impact": -1.0, "reasoning": "..."},
    #   "carrier_appetite": {"weight": 0.15, "impact": +1.5, "reasoning": "..."}
    # }
    factor_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # LLM Analysis
    llm_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_market_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_negotiation_points: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Structure: ["3-year clean loss history", "Long-term relationship", ...]

    # Forecast Status
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, index=True
    )
    # Values: active, superseded, expired

    # Calculation Metadata
    forecast_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    forecast_trigger: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Values: scheduled, manual, ingestion, renewal_approaching

    # LLM Metadata
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="renewal_forecasts")
    program: Mapped["InsuranceProgram | None"] = relationship(
        "InsuranceProgram", back_populates="renewal_forecasts"
    )
    policy: Mapped["Policy | None"] = relationship(
        "Policy", back_populates="renewal_forecasts"
    )

    def __repr__(self) -> str:
        return (
            f"<RenewalForecast(id={self.id}, property_id={self.property_id}, "
            f"renewal_year={self.renewal_year}, llm_predicted_mid={self.llm_predicted_mid})>"
        )
