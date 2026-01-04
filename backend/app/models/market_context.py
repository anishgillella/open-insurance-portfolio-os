"""Market Context model - LLM-synthesized market analysis and insights."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.property import Property


class MarketContext(BaseModel):
    """Market Context model for storing LLM-analyzed market intelligence.

    Synthesizes internal data (policies, premiums, loss history) with
    external market context to provide renewal intelligence and
    negotiation recommendations.
    """

    __tablename__ = "market_contexts"

    # Foreign Key
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Analysis Period
    analysis_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # Typically 7 days from analysis_date

    # Market Condition Assessment
    market_condition: Mapped[str] = mapped_column(String(50), nullable=False)
    # Values: hardening, softening, stable, volatile
    market_condition_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Property-Specific Analysis
    property_risk_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    carrier_relationship_assessment: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Policy Analysis (extracted from structured data)
    policy_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Structure: {
    #   "key_exclusions": ["flood", "cyber"],
    #   "notable_sublimits": [{"coverage": "wind", "limit": 500000}],
    #   "unusual_terms": ["aggregate deductible applies"],
    #   "coverage_strengths": ["comprehensive GL", "low deductibles"],
    #   "coverage_weaknesses": ["no umbrella", "high wind sublimit"]
    # }

    # Year-over-Year Changes
    yoy_changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Structure: {
    #   "premium_change_pct": 8.5,
    #   "limit_changes": [{"coverage": "property", "old": 1000000, "new": 1200000}],
    #   "deductible_changes": [],
    #   "new_exclusions": ["communicable disease"],
    #   "removed_coverages": []
    # }

    # Negotiation Intelligence
    negotiation_leverage: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Structure: ["Clean 3-year loss history", "Long-term carrier relationship", ...]

    negotiation_recommendations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Structure: [
    #   {"action": "Request removal of wind sublimit", "priority": "high", "rationale": "..."},
    #   {"action": "Negotiate 5% loyalty discount", "priority": "medium", "rationale": "..."}
    # ]

    # Risk Insights
    risk_insights: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Structure: ["Florida coastal exposure trending higher", "CAT losses impacting market"]

    # Executive Summary
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="current", nullable=False, index=True
    )
    # Values: current, expired, superseded

    # LLM Metadata
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationship
    property: Mapped["Property"] = relationship(
        "Property", back_populates="market_contexts"
    )

    def __repr__(self) -> str:
        return (
            f"<MarketContext(id={self.id}, property_id={self.property_id}, "
            f"market_condition={self.market_condition}, analysis_date={self.analysis_date})>"
        )
