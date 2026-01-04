"""Repository for CoverageGap operations."""

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.coverage_gap import CoverageGap
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class GapRepository(BaseRepository[CoverageGap]):
    """Repository for CoverageGap CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CoverageGap, session)

    async def get_by_property(
        self,
        property_id: str,
        status: str | None = None,
        severity: str | None = None,
        gap_type: str | None = None,
        limit: int = 100,
    ) -> list[CoverageGap]:
        """Get gaps for a property with optional filters.

        Args:
            property_id: Property ID.
            status: Filter by status (open, acknowledged, resolved).
            severity: Filter by severity (critical, warning, info).
            gap_type: Filter by gap type.
            limit: Maximum results.

        Returns:
            List of CoverageGap instances.
        """
        stmt = (
            select(CoverageGap)
            .where(
                CoverageGap.property_id == property_id,
                CoverageGap.deleted_at.is_(None),
            )
            .order_by(
                # Order by severity: critical first, then warning, then info
                CoverageGap.severity.desc(),
                CoverageGap.detected_at.desc(),
            )
            .limit(limit)
        )

        if status:
            stmt = stmt.where(CoverageGap.status == status)
        if severity:
            stmt = stmt.where(CoverageGap.severity == severity)
        if gap_type:
            stmt = stmt.where(CoverageGap.gap_type == gap_type)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_open_gaps(
        self,
        property_id: str | None = None,
        organization_id: str | None = None,
        severity: str | None = None,
        gap_type: str | None = None,
        limit: int = 100,
    ) -> list[CoverageGap]:
        """Get all open gaps with optional filters.

        Args:
            property_id: Filter by property ID.
            organization_id: Filter by organization ID.
            severity: Filter by severity.
            gap_type: Filter by gap type.
            limit: Maximum results.

        Returns:
            List of open CoverageGap instances.
        """
        stmt = (
            select(CoverageGap)
            .options(selectinload(CoverageGap.property))
            .where(
                CoverageGap.status == "open",
                CoverageGap.deleted_at.is_(None),
            )
            .order_by(CoverageGap.severity.desc(), CoverageGap.detected_at.desc())
            .limit(limit)
        )

        if property_id:
            stmt = stmt.where(CoverageGap.property_id == property_id)
        if severity:
            stmt = stmt.where(CoverageGap.severity == severity)
        if gap_type:
            stmt = stmt.where(CoverageGap.gap_type == gap_type)

        # Organization filter requires join
        if organization_id:
            from app.models.property import Property

            stmt = stmt.join(Property).where(Property.organization_id == organization_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear_open_gaps_for_property(self, property_id: str) -> int:
        """Clear all open gaps for a property before regenerating.

        Only deletes gaps with status='open'. Acknowledged and resolved
        gaps are preserved.

        Args:
            property_id: Property ID.

        Returns:
            Number of gaps deleted.
        """
        stmt = (
            delete(CoverageGap)
            .where(
                CoverageGap.property_id == property_id,
                CoverageGap.status == "open",
            )
            .returning(CoverageGap.id)
        )
        result = await self.session.execute(stmt)
        deleted_ids = result.scalars().all()
        count = len(deleted_ids)

        if count > 0:
            logger.info(f"Cleared {count} open gaps for property {property_id}")

        return count

    async def create_gap(
        self,
        property_id: str,
        gap_type: str,
        severity: str,
        title: str,
        description: str | None = None,
        coverage_name: str | None = None,
        current_value: str | None = None,
        recommended_value: str | None = None,
        gap_amount: float | None = None,
        policy_id: str | None = None,
        program_id: str | None = None,
        detection_method: str = "auto",
    ) -> CoverageGap:
        """Create a new coverage gap.

        Args:
            property_id: Property ID.
            gap_type: Type of gap (underinsurance, high_deductible, etc.).
            severity: Severity level (critical, warning, info).
            title: Short title describing the gap.
            description: Detailed description.
            coverage_name: Name of the coverage affected.
            current_value: Current coverage value.
            recommended_value: Recommended coverage value.
            gap_amount: Numeric gap amount (if applicable).
            policy_id: Related policy ID (if applicable).
            program_id: Related program ID (if applicable).
            detection_method: How the gap was detected (auto, manual).

        Returns:
            Created CoverageGap instance.
        """
        from decimal import Decimal

        return await self.create(
            property_id=property_id,
            policy_id=policy_id,
            program_id=program_id,
            gap_type=gap_type,
            severity=severity,
            title=title,
            description=description,
            coverage_name=coverage_name,
            current_value=current_value,
            recommended_value=recommended_value,
            gap_amount=Decimal(str(gap_amount)) if gap_amount else None,
            status="open",
            detected_at=datetime.now(timezone.utc),
            detection_method=detection_method,
        )

    async def acknowledge_gap(
        self,
        gap_id: str,
        acknowledged_by: str | None = None,
        notes: str | None = None,
    ) -> CoverageGap | None:
        """Mark a gap as acknowledged (reviewed but not resolved).

        Args:
            gap_id: Gap ID.
            acknowledged_by: User ID who acknowledged.
            notes: Optional notes.

        Returns:
            Updated CoverageGap or None if not found.
        """
        return await self.update(
            gap_id,
            status="acknowledged",
            resolution_notes=notes,
        )

    async def resolve_gap(
        self,
        gap_id: str,
        resolved_by: str | None = None,
        notes: str | None = None,
    ) -> CoverageGap | None:
        """Mark a gap as resolved.

        Args:
            gap_id: Gap ID.
            resolved_by: User ID who resolved.
            notes: Resolution notes.

        Returns:
            Updated CoverageGap or None if not found.
        """
        return await self.update(
            gap_id,
            status="resolved",
            resolved_at=datetime.now(timezone.utc),
            resolved_by=resolved_by,
            resolution_notes=notes,
        )

    async def count_by_severity(
        self,
        property_id: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, int]:
        """Count open gaps by severity.

        Args:
            property_id: Filter by property ID.
            organization_id: Filter by organization ID.

        Returns:
            Dictionary with counts by severity.
        """
        from sqlalchemy import func

        from app.models.property import Property

        stmt = (
            select(
                CoverageGap.severity,
                func.count(CoverageGap.id).label("count"),
            )
            .where(
                CoverageGap.status == "open",
                CoverageGap.deleted_at.is_(None),
            )
            .group_by(CoverageGap.severity)
        )

        if property_id:
            stmt = stmt.where(CoverageGap.property_id == property_id)

        if organization_id:
            stmt = stmt.join(Property).where(Property.organization_id == organization_id)

        result = await self.session.execute(stmt)
        counts = {row.severity: row.count for row in result}

        return {
            "critical": counts.get("critical", 0),
            "warning": counts.get("warning", 0),
            "info": counts.get("info", 0),
            "total": sum(counts.values()),
        }

    async def get_with_property(self, gap_id: str) -> CoverageGap | None:
        """Get a gap with its property loaded.

        Args:
            gap_id: Gap ID.

        Returns:
            CoverageGap with property or None.
        """
        stmt = (
            select(CoverageGap)
            .options(selectinload(CoverageGap.property))
            .where(
                CoverageGap.id == gap_id,
                CoverageGap.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
