"""Repository for CoverageConflict operations."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.coverage_conflict import CoverageConflict
from app.models.property import Property
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ConflictRepository(BaseRepository[CoverageConflict]):
    """Repository for CoverageConflict CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CoverageConflict, session)

    async def get_by_property(
        self,
        property_id: str,
        status: str | None = None,
        severity: str | None = None,
        conflict_type: str | None = None,
        limit: int = 100,
    ) -> list[CoverageConflict]:
        """Get conflicts for a property with optional filters.

        Args:
            property_id: Property ID.
            status: Optional status filter (open, acknowledged, resolved).
            severity: Optional severity filter (critical, warning, info).
            conflict_type: Optional conflict type filter.
            limit: Maximum number of records.

        Returns:
            List of CoverageConflict records.
        """
        stmt = (
            select(CoverageConflict)
            .where(
                CoverageConflict.property_id == property_id,
                CoverageConflict.deleted_at.is_(None),
            )
            .order_by(
                CoverageConflict.severity.desc(),
                CoverageConflict.detected_at.desc(),
            )
            .limit(limit)
        )

        if status:
            stmt = stmt.where(CoverageConflict.status == status)
        if severity:
            stmt = stmt.where(CoverageConflict.severity == severity)
        if conflict_type:
            stmt = stmt.where(CoverageConflict.conflict_type == conflict_type)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_open_conflicts(
        self,
        property_id: str | None = None,
        organization_id: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[CoverageConflict]:
        """Get all open conflicts with optional filters.

        Args:
            property_id: Optional property filter.
            organization_id: Optional organization filter.
            severity: Optional severity filter.
            limit: Maximum records.

        Returns:
            List of open CoverageConflict records.
        """
        stmt = (
            select(CoverageConflict)
            .options(selectinload(CoverageConflict.property))
            .where(
                CoverageConflict.status == "open",
                CoverageConflict.deleted_at.is_(None),
            )
            .order_by(
                CoverageConflict.severity.desc(),
                CoverageConflict.detected_at.desc(),
            )
            .limit(limit)
        )

        if property_id:
            stmt = stmt.where(CoverageConflict.property_id == property_id)
        if severity:
            stmt = stmt.where(CoverageConflict.severity == severity)
        if organization_id:
            stmt = stmt.join(Property).where(Property.organization_id == organization_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear_open_conflicts(self, property_id: str) -> int:
        """Clear all open conflicts for a property before re-detection.

        Soft deletes open conflicts. Acknowledged and resolved conflicts are preserved.

        Args:
            property_id: Property ID.

        Returns:
            Number of conflicts cleared.
        """
        # Get open conflicts
        stmt = (
            select(CoverageConflict)
            .where(
                CoverageConflict.property_id == property_id,
                CoverageConflict.status == "open",
                CoverageConflict.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        conflicts = list(result.scalars().all())

        # Soft delete each
        now = datetime.now(timezone.utc)
        for conflict in conflicts:
            conflict.deleted_at = now

        await self.session.flush()
        logger.info(f"Cleared {len(conflicts)} open conflicts for property {property_id}")
        return len(conflicts)

    async def create_conflict(
        self,
        property_id: str,
        conflict_type: str,
        severity: str,
        title: str,
        description: str | None = None,
        affected_policy_ids: list[str] | None = None,
        gap_amount: float | None = None,
        potential_savings: float | None = None,
        recommendation: str | None = None,
        detection_method: str = "llm",
        llm_reasoning: str | None = None,
        llm_analysis: dict | None = None,
        llm_model_used: str | None = None,
    ) -> CoverageConflict:
        """Create a new conflict record.

        Args:
            property_id: Property ID.
            conflict_type: Type of conflict.
            severity: Severity level.
            title: Human-readable title.
            description: Detailed description.
            affected_policy_ids: List of affected policy IDs.
            gap_amount: Financial gap amount if applicable.
            potential_savings: Potential savings if applicable.
            recommendation: Recommended action.
            detection_method: How conflict was detected.
            llm_reasoning: LLM reasoning for detection.
            llm_analysis: Full LLM analysis data.
            llm_model_used: LLM model used.

        Returns:
            Created CoverageConflict.
        """
        from decimal import Decimal

        return await self.create(
            property_id=property_id,
            conflict_type=conflict_type,
            severity=severity,
            title=title,
            description=description,
            affected_policy_ids=affected_policy_ids or [],
            gap_amount=Decimal(str(gap_amount)) if gap_amount else None,
            potential_savings=Decimal(str(potential_savings)) if potential_savings else None,
            recommendation=recommendation,
            detection_method=detection_method,
            llm_reasoning=llm_reasoning,
            llm_analysis=llm_analysis,
            llm_analyzed_at=datetime.now(timezone.utc) if llm_reasoning else None,
            llm_model_used=llm_model_used,
            detected_at=datetime.now(timezone.utc),
            status="open",
        )

    async def acknowledge_conflict(
        self,
        conflict_id: str,
        acknowledged_by: str | None = None,
        notes: str | None = None,
    ) -> CoverageConflict | None:
        """Mark a conflict as acknowledged.

        Args:
            conflict_id: Conflict ID.
            acknowledged_by: User ID who acknowledged.
            notes: Acknowledgment notes.

        Returns:
            Updated CoverageConflict or None if not found.
        """
        return await self.update(
            conflict_id,
            status="acknowledged",
            acknowledged_at=datetime.now(timezone.utc),
            acknowledged_by=acknowledged_by,
            acknowledged_notes=notes,
        )

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolved_by: str | None = None,
        notes: str | None = None,
    ) -> CoverageConflict | None:
        """Mark a conflict as resolved.

        Args:
            conflict_id: Conflict ID.
            resolved_by: User ID who resolved.
            notes: Resolution notes.

        Returns:
            Updated CoverageConflict or None if not found.
        """
        return await self.update(
            conflict_id,
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
        """Get count of open conflicts by severity.

        Args:
            property_id: Optional property filter.
            organization_id: Optional organization filter.

        Returns:
            Dictionary mapping severity to count.
        """
        stmt = (
            select(
                CoverageConflict.severity,
                func.count(CoverageConflict.id).label("count"),
            )
            .where(
                CoverageConflict.status == "open",
                CoverageConflict.deleted_at.is_(None),
            )
            .group_by(CoverageConflict.severity)
        )

        if property_id:
            stmt = stmt.where(CoverageConflict.property_id == property_id)
        if organization_id:
            stmt = stmt.join(Property).where(Property.organization_id == organization_id)

        result = await self.session.execute(stmt)
        rows = result.all()

        counts = {"critical": 0, "warning": 0, "info": 0}
        for row in rows:
            if row.severity in counts:
                counts[row.severity] = row.count

        return counts

    async def get_with_property(self, conflict_id: str) -> CoverageConflict | None:
        """Get conflict with property details.

        Args:
            conflict_id: Conflict ID.

        Returns:
            CoverageConflict with property loaded or None.
        """
        stmt = (
            select(CoverageConflict)
            .options(selectinload(CoverageConflict.property))
            .where(
                CoverageConflict.id == conflict_id,
                CoverageConflict.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


def get_conflict_repository(session: AsyncSession) -> ConflictRepository:
    """Factory function to create ConflictRepository.

    Args:
        session: Database session.

    Returns:
        ConflictRepository instance.
    """
    return ConflictRepository(session)
