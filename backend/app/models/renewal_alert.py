"""Renewal Alert model - Configurable renewal timeline alerts."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.policy import Policy
    from app.models.property import Property


class RenewalAlert(BaseModel):
    """Renewal Alert model for tracking expiration alerts.

    Alerts are generated based on configurable thresholds (default: 90, 60, 30 days).
    Each alert has a severity level and can be acknowledged/resolved.
    """

    __tablename__ = "renewal_alerts"

    # Foreign Keys
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Alert Details
    threshold_days: Mapped[int] = mapped_column(Integer, nullable=False)
    # e.g., 90, 60, 30
    days_until_expiration: Mapped[int] = mapped_column(Integer, nullable=False)
    expiration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Values: info (90 days), warning (60 days), critical (30 days)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status Tracking
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    # Values: pending, acknowledged, resolved, expired

    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Acknowledgement
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledgement_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Resolution
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # LLM Enhancement (optional priority/strategy suggestions)
    llm_priority_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 1-10 complexity/priority rating
    llm_renewal_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_key_actions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Structure: ["Request quotes", "Update SOV", ...]

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="renewal_alerts")
    policy: Mapped["Policy"] = relationship("Policy", back_populates="renewal_alerts")

    def __repr__(self) -> str:
        return (
            f"<RenewalAlert(id={self.id}, property_id={self.property_id}, "
            f"threshold_days={self.threshold_days}, severity={self.severity}, status={self.status})>"
        )


class RenewalAlertConfig(BaseModel):
    """Configuration for renewal alert thresholds per property.

    Allows customizing alert thresholds on a per-property basis.
    If no config exists for a property, default thresholds are used.
    """

    __tablename__ = "renewal_alert_configs"

    # Foreign Key
    property_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Configuration
    thresholds: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, default=[90, 60, 30]
    )
    # Array of days before expiration to trigger alerts

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Optional custom severity mapping
    severity_mapping: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Structure: {"90": "info", "60": "warning", "30": "critical"}

    # Relationship
    property: Mapped["Property"] = relationship(
        "Property", back_populates="renewal_alert_config"
    )

    def __repr__(self) -> str:
        return (
            f"<RenewalAlertConfig(id={self.id}, property_id={self.property_id}, "
            f"thresholds={self.thresholds}, enabled={self.enabled})>"
        )
