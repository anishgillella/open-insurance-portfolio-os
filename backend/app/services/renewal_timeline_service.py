"""Renewal Timeline Service - Expiration tracking and configurable alerts.

This service provides:
1. Renewal timeline listing with upcoming expirations
2. Configurable alert thresholds (default: 90, 60, 30 days)
3. Alert generation and management
4. LLM-enhanced priority scoring and strategy suggestions

Uses Gemini 2.5 Flash via OpenRouter for LLM enhancement.
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.insurance_program import InsuranceProgram
from app.models.policy import Policy
from app.models.property import Property
from app.models.renewal_alert import RenewalAlert, RenewalAlertConfig
from app.models.renewal_forecast import RenewalForecast

logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"

# Default alert configuration
DEFAULT_THRESHOLDS = [90, 60, 30]
DEFAULT_SEVERITY_MAPPING = {
    90: "info",
    60: "warning",
    30: "critical",
}


class RenewalTimelineError(Exception):
    """Base exception for renewal timeline errors."""
    pass


class RenewalTimelineAPIError(RenewalTimelineError):
    """Raised when LLM API returns an error."""
    pass


@dataclass
class TimelineItem:
    """Single item in the renewal timeline."""

    property_id: str
    property_name: str
    policy_id: str
    policy_number: str | None
    policy_type: str
    carrier_name: str | None
    expiration_date: date
    days_until_expiration: int
    severity: str
    current_premium: Decimal | None
    predicted_premium: Decimal | None
    has_forecast: bool
    has_active_alerts: bool
    alert_count: int


@dataclass
class TimelineSummary:
    """Summary of renewal timeline."""

    total_renewals: int
    expiring_30_days: int
    expiring_60_days: int
    expiring_90_days: int
    total_premium_at_risk: Decimal


@dataclass
class AlertSummary:
    """Summary of alerts."""

    total: int
    critical: int
    warning: int
    info: int
    pending: int


# LLM Prompts for prioritization
PRIORITY_SYSTEM_PROMPT = """You are an expert insurance renewal strategist. Analyze the provided renewal and provide prioritization guidance.

Respond in JSON format:
{
    "priority_score": <1-10, 10 being highest priority>,
    "renewal_strategy": "2-3 sentence strategy recommendation",
    "key_actions": ["Action 1", "Action 2", "Action 3"]
}"""


class RenewalTimelineService:
    """Service for managing renewal timeline and alerts."""

    def __init__(self, session: AsyncSession, api_key: str | None = None):
        """Initialize renewal timeline service.

        Args:
            session: Database session.
            api_key: OpenRouter API key. Defaults to settings.
        """
        self.session = session
        self.api_key = api_key or settings.openrouter_api_key
        self.model = MODEL

        if not self.api_key:
            logger.warning("OpenRouter API key not configured for renewal timeline")

    # ==========================================================================
    # Timeline Methods
    # ==========================================================================

    async def get_timeline(
        self,
        organization_id: str | None = None,
        days_ahead: int = 120,
    ) -> tuple[list[TimelineItem], TimelineSummary]:
        """Get renewal timeline for upcoming expirations.

        Args:
            organization_id: Filter by organization.
            days_ahead: How many days ahead to look.

        Returns:
            Tuple of (timeline items, summary).
        """
        today = date.today()
        cutoff_date = date.today().replace(
            day=today.day,
            month=today.month,
        )
        # Calculate cutoff date properly
        from datetime import timedelta
        cutoff_date = today + timedelta(days=days_ahead)

        # Query policies with upcoming expirations
        stmt = (
            select(Policy)
            .options(
                selectinload(Policy.program).selectinload(InsuranceProgram.property),
                selectinload(Policy.coverages),
            )
            .join(InsuranceProgram)
            .join(Property)
            .where(
                Policy.expiration_date.isnot(None),
                Policy.expiration_date >= today,
                Policy.expiration_date <= cutoff_date,
                Policy.deleted_at.is_(None),
                InsuranceProgram.deleted_at.is_(None),
                Property.deleted_at.is_(None),
            )
            .order_by(Policy.expiration_date.asc())
        )

        if organization_id:
            stmt = stmt.where(Property.organization_id == organization_id)

        result = await self.session.execute(stmt)
        policies = list(result.scalars().all())

        # Build timeline items
        timeline = []
        total_premium = Decimal("0")
        exp_30 = 0
        exp_60 = 0
        exp_90 = 0

        for policy in policies:
            if not policy.program or not policy.program.property:
                continue

            prop = policy.program.property
            days_until = (policy.expiration_date - today).days

            # Get severity
            severity = self._get_severity(days_until)

            # Check for forecast
            forecast = await self._get_forecast(prop.id)

            # Check for active alerts
            alert_count = await self._count_active_alerts(policy.id)

            item = TimelineItem(
                property_id=prop.id,
                property_name=prop.name,
                policy_id=policy.id,
                policy_number=policy.policy_number,
                policy_type=policy.policy_type,
                carrier_name=policy.carrier_name,
                expiration_date=policy.expiration_date,
                days_until_expiration=days_until,
                severity=severity,
                current_premium=policy.premium,
                predicted_premium=forecast.llm_predicted_mid if forecast else None,
                has_forecast=forecast is not None,
                has_active_alerts=alert_count > 0,
                alert_count=alert_count,
            )
            timeline.append(item)

            # Update summary counts
            if policy.premium:
                total_premium += policy.premium

            if days_until <= 30:
                exp_30 += 1
            elif days_until <= 60:
                exp_60 += 1
            elif days_until <= 90:
                exp_90 += 1

        summary = TimelineSummary(
            total_renewals=len(timeline),
            expiring_30_days=exp_30,
            expiring_60_days=exp_60,
            expiring_90_days=exp_90,
            total_premium_at_risk=total_premium,
        )

        return timeline, summary

    # ==========================================================================
    # Alert Methods
    # ==========================================================================

    async def generate_alerts(
        self,
        organization_id: str | None = None,
        include_llm_enhancement: bool = True,
    ) -> int:
        """Generate alerts for upcoming renewals based on thresholds.

        Args:
            organization_id: Filter by organization.
            include_llm_enhancement: Include LLM priority scoring.

        Returns:
            Number of new alerts generated.
        """
        today = date.today()
        new_alerts = 0

        # Get all properties with their alert configs
        stmt = select(Property).options(
            selectinload(Property.insurance_programs).selectinload(
                InsuranceProgram.policies
            ),
            selectinload(Property.renewal_alert_config),
        ).where(Property.deleted_at.is_(None))

        if organization_id:
            stmt = stmt.where(Property.organization_id == organization_id)

        result = await self.session.execute(stmt)
        properties = list(result.scalars().all())

        for prop in properties:
            # Get thresholds for this property
            config = prop.renewal_alert_config
            thresholds = config.thresholds if config and config.enabled else DEFAULT_THRESHOLDS

            if config and not config.enabled:
                continue

            # Check each policy
            for program in prop.insurance_programs:
                if program.status != "active":
                    continue

                for policy in program.policies:
                    if not policy.expiration_date:
                        continue

                    days_until = (policy.expiration_date - today).days

                    # Check each threshold
                    for threshold in thresholds:
                        if days_until <= threshold:
                            # Check if alert already exists
                            existing = await self._get_existing_alert(
                                policy.id, threshold
                            )
                            if existing:
                                continue

                            # Create new alert
                            severity = self._get_severity_for_threshold(
                                threshold, config
                            )

                            alert = RenewalAlert(
                                property_id=prop.id,
                                policy_id=policy.id,
                                threshold_days=threshold,
                                days_until_expiration=days_until,
                                expiration_date=datetime.combine(
                                    policy.expiration_date, datetime.min.time()
                                ).replace(tzinfo=timezone.utc),
                                severity=severity,
                                title=f"Policy expiring in {days_until} days",
                                message=self._build_alert_message(
                                    policy, prop, days_until, threshold
                                ),
                                status="pending",
                                triggered_at=datetime.now(timezone.utc),
                            )

                            # Enhance with LLM if enabled
                            if include_llm_enhancement and self.api_key:
                                try:
                                    await self._enhance_alert_with_llm(
                                        alert, policy, prop
                                    )
                                except Exception as e:
                                    logger.warning(f"LLM enhancement failed: {e}")

                            self.session.add(alert)
                            new_alerts += 1

                            # Only create one alert per policy (for the most urgent threshold)
                            break

        await self.session.flush()
        logger.info(f"Generated {new_alerts} new renewal alerts")
        return new_alerts

    async def list_alerts(
        self,
        organization_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> tuple[list[RenewalAlert], AlertSummary]:
        """List alerts with optional filtering.

        Args:
            organization_id: Filter by organization.
            status: Filter by status (pending, acknowledged, resolved).
            severity: Filter by severity (info, warning, critical).

        Returns:
            Tuple of (alerts, summary).
        """
        stmt = (
            select(RenewalAlert)
            .options(
                selectinload(RenewalAlert.property),
                selectinload(RenewalAlert.policy),
            )
            .where(RenewalAlert.deleted_at.is_(None))
            .order_by(
                RenewalAlert.severity.desc(),
                RenewalAlert.days_until_expiration.asc(),
            )
        )

        if organization_id:
            stmt = stmt.join(Property).where(
                Property.organization_id == organization_id
            )

        if status:
            stmt = stmt.where(RenewalAlert.status == status)

        if severity:
            stmt = stmt.where(RenewalAlert.severity == severity)

        result = await self.session.execute(stmt)
        alerts = list(result.scalars().all())

        # Build summary
        summary = AlertSummary(
            total=len(alerts),
            critical=len([a for a in alerts if a.severity == "critical"]),
            warning=len([a for a in alerts if a.severity == "warning"]),
            info=len([a for a in alerts if a.severity == "info"]),
            pending=len([a for a in alerts if a.status == "pending"]),
        )

        return alerts, summary

    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str | None = None,
        notes: str | None = None,
    ) -> RenewalAlert:
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID.
            acknowledged_by: User who acknowledged.
            notes: Optional notes.

        Returns:
            Updated alert.
        """
        stmt = select(RenewalAlert).where(
            RenewalAlert.id == alert_id,
            RenewalAlert.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        alert = result.scalar_one_or_none()

        if not alert:
            raise RenewalTimelineError(f"Alert {alert_id} not found")

        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = acknowledged_by
        alert.acknowledgement_notes = notes

        await self.session.flush()
        return alert

    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str | None = None,
        notes: str | None = None,
    ) -> RenewalAlert:
        """Resolve an alert.

        Args:
            alert_id: Alert ID.
            resolved_by: User who resolved.
            notes: Resolution notes.

        Returns:
            Updated alert.
        """
        stmt = select(RenewalAlert).where(
            RenewalAlert.id == alert_id,
            RenewalAlert.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        alert = result.scalar_one_or_none()

        if not alert:
            raise RenewalTimelineError(f"Alert {alert_id} not found")

        alert.status = "resolved"
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by = resolved_by
        alert.resolution_notes = notes

        await self.session.flush()
        return alert

    # ==========================================================================
    # Alert Configuration Methods
    # ==========================================================================

    async def get_alert_config(self, property_id: str) -> RenewalAlertConfig | None:
        """Get alert configuration for a property.

        Args:
            property_id: Property ID.

        Returns:
            Alert config or None.
        """
        stmt = select(RenewalAlertConfig).where(
            RenewalAlertConfig.property_id == property_id,
            RenewalAlertConfig.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_alert_config(
        self,
        property_id: str,
        thresholds: list[int] | None = None,
        enabled: bool | None = None,
        severity_mapping: dict[str, str] | None = None,
    ) -> RenewalAlertConfig:
        """Update or create alert configuration for a property.

        Args:
            property_id: Property ID.
            thresholds: New thresholds.
            enabled: Enable/disable alerts.
            severity_mapping: Custom severity mapping.

        Returns:
            Updated or created config.
        """
        config = await self.get_alert_config(property_id)

        if config:
            if thresholds is not None:
                config.thresholds = thresholds
            if enabled is not None:
                config.enabled = enabled
            if severity_mapping is not None:
                config.severity_mapping = severity_mapping
        else:
            config = RenewalAlertConfig(
                property_id=property_id,
                thresholds=thresholds or DEFAULT_THRESHOLDS,
                enabled=enabled if enabled is not None else True,
                severity_mapping=severity_mapping,
            )
            self.session.add(config)

        await self.session.flush()
        return config

    # ==========================================================================
    # Private Helper Methods
    # ==========================================================================

    def _get_severity(self, days_until: int) -> str:
        """Get severity based on days until expiration."""
        if days_until <= 30:
            return "critical"
        elif days_until <= 60:
            return "warning"
        else:
            return "info"

    def _get_severity_for_threshold(
        self,
        threshold: int,
        config: RenewalAlertConfig | None,
    ) -> str:
        """Get severity for a specific threshold."""
        if config and config.severity_mapping:
            return config.severity_mapping.get(str(threshold), "info")

        return DEFAULT_SEVERITY_MAPPING.get(threshold, "info")

    async def _get_forecast(self, property_id: str) -> RenewalForecast | None:
        """Get active forecast for a property."""
        stmt = (
            select(RenewalForecast)
            .where(
                RenewalForecast.property_id == property_id,
                RenewalForecast.status == "active",
                RenewalForecast.deleted_at.is_(None),
            )
            .order_by(RenewalForecast.forecast_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _count_active_alerts(self, policy_id: str) -> int:
        """Count active alerts for a policy."""
        stmt = select(RenewalAlert).where(
            RenewalAlert.policy_id == policy_id,
            RenewalAlert.status.in_(["pending", "acknowledged"]),
            RenewalAlert.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))

    async def _get_existing_alert(
        self,
        policy_id: str,
        threshold: int,
    ) -> RenewalAlert | None:
        """Check if alert already exists for policy and threshold."""
        stmt = select(RenewalAlert).where(
            RenewalAlert.policy_id == policy_id,
            RenewalAlert.threshold_days == threshold,
            RenewalAlert.status.in_(["pending", "acknowledged"]),
            RenewalAlert.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _build_alert_message(
        self,
        policy: Policy,
        prop: Property,
        days_until: int,
        threshold: int,
    ) -> str:
        """Build alert message."""
        return (
            f"The {policy.policy_type} policy ({policy.policy_number or 'N/A'}) "
            f"for {prop.name} is expiring in {days_until} days on {policy.expiration_date}. "
            f"Carrier: {policy.carrier_name or 'Unknown'}. "
            f"Annual premium: ${float(policy.premium or 0):,.0f}."
        )

    async def _enhance_alert_with_llm(
        self,
        alert: RenewalAlert,
        policy: Policy,
        prop: Property,
    ) -> None:
        """Enhance alert with LLM-generated priority and strategy."""
        context = f"""
Property: {prop.name} ({prop.property_type or 'Unknown type'})
Location: {prop.city or ''}, {prop.state or ''}
Policy Type: {policy.policy_type}
Carrier: {policy.carrier_name or 'Unknown'}
Premium: ${float(policy.premium or 0):,.0f}
Expiration: {policy.expiration_date}
Days Until: {alert.days_until_expiration}
"""

        start_time = time.time()
        response = await self._call_llm(
            PRIORITY_SYSTEM_PROMPT,
            f"Analyze this upcoming renewal:\n\n{context}",
        )
        latency_ms = int((time.time() - start_time) * 1000)

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = self._extract_json_from_response(response)

        alert.llm_priority_score = int(result.get("priority_score", 5))
        alert.llm_renewal_strategy = result.get("renewal_strategy", "")
        alert.llm_key_actions = result.get("key_actions", [])

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call the LLM API."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://open-insurance.app",
                    "X-Title": "Open Insurance Renewal Timeline",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.3,
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenRouter API error: {response.status_code} - {error_detail}")
                raise RenewalTimelineAPIError(
                    f"OpenRouter API error: {response.status_code} - {error_detail}"
                )

            result = response.json()
            choices = result.get("choices", [])
            if not choices:
                raise RenewalTimelineError("No response from LLM")

            return choices[0].get("message", {}).get("content", "")

    def _extract_json_from_response(self, response: str) -> dict:
        """Extract JSON from a response that may contain extra text."""
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "priority_score": 5,
            "renewal_strategy": "",
            "key_actions": [],
        }


def get_renewal_timeline_service(session: AsyncSession) -> RenewalTimelineService:
    """Factory function to create RenewalTimelineService.

    Args:
        session: Database session.

    Returns:
        RenewalTimelineService instance.
    """
    return RenewalTimelineService(session)
