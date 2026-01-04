"""Repository for HealthScore operations."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.health_score import HealthScore
from app.models.property import Property
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class HealthScoreRepository(BaseRepository[HealthScore]):
    """Repository for HealthScore CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(HealthScore, session)

    async def get_latest_for_property(self, property_id: str) -> HealthScore | None:
        """Get the most recent health score for a property.

        Args:
            property_id: Property ID.

        Returns:
            Most recent HealthScore or None.
        """
        stmt = (
            select(HealthScore)
            .where(
                HealthScore.property_id == property_id,
                HealthScore.deleted_at.is_(None),
            )
            .order_by(HealthScore.calculated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(
        self,
        property_id: str,
        days: int = 90,
        limit: int = 50,
    ) -> list[HealthScore]:
        """Get health score history for trend analysis.

        Args:
            property_id: Property ID.
            days: Number of days of history to fetch.
            limit: Maximum number of records.

        Returns:
            List of HealthScore records ordered by date descending.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(HealthScore)
            .where(
                HealthScore.property_id == property_id,
                HealthScore.calculated_at >= cutoff,
                HealthScore.deleted_at.is_(None),
            )
            .order_by(HealthScore.calculated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_portfolio_scores(
        self,
        organization_id: str | None = None,
        limit: int = 100,
    ) -> list[HealthScore]:
        """Get latest scores for all properties.

        Uses a subquery to get only the most recent score per property.

        Args:
            organization_id: Optional organization filter.
            limit: Maximum number of records.

        Returns:
            List of latest HealthScore per property.
        """
        # Subquery to get latest score ID per property
        latest_subq = (
            select(
                HealthScore.property_id,
                func.max(HealthScore.calculated_at).label("max_date"),
            )
            .where(HealthScore.deleted_at.is_(None))
            .group_by(HealthScore.property_id)
            .subquery()
        )

        # Main query joining with subquery
        stmt = (
            select(HealthScore)
            .options(selectinload(HealthScore.property))
            .join(
                latest_subq,
                (HealthScore.property_id == latest_subq.c.property_id)
                & (HealthScore.calculated_at == latest_subq.c.max_date),
            )
            .where(HealthScore.deleted_at.is_(None))
        )

        # Filter by organization if specified
        if organization_id:
            stmt = stmt.join(Property).where(Property.organization_id == organization_id)

        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_grade_distribution(
        self,
        organization_id: str | None = None,
    ) -> dict[str, int]:
        """Get count of properties by grade.

        Args:
            organization_id: Optional organization filter.

        Returns:
            Dictionary mapping grade to count.
        """
        # Get latest scores first
        scores = await self.get_portfolio_scores(organization_id)

        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for score in scores:
            if score.grade in distribution:
                distribution[score.grade] += 1

        return distribution

    async def create_score(
        self,
        property_id: str,
        score: int,
        grade: str,
        components: dict,
        calculated_at: datetime,
        trigger: str,
        executive_summary: str | None = None,
        recommendations: list | None = None,
        risk_factors: list | None = None,
        strengths: list | None = None,
        llm_model_used: str | None = None,
        llm_latency_ms: int | None = None,
    ) -> HealthScore:
        """Create a new health score record.

        Args:
            property_id: Property ID.
            score: Total score (0-100).
            grade: Letter grade (A-F).
            components: Component breakdown.
            calculated_at: When calculation was done.
            trigger: What triggered the calculation.
            executive_summary: LLM-generated summary.
            recommendations: LLM-generated recommendations.
            risk_factors: Identified risk factors.
            strengths: Identified strengths.
            llm_model_used: LLM model used.
            llm_latency_ms: LLM call latency.

        Returns:
            Created HealthScore.
        """
        # Get previous score for trend calculation
        previous = await self.get_latest_for_property(property_id)

        trend_direction = "new"
        trend_delta = None
        previous_score_id = None

        if previous:
            previous_score_id = previous.id
            trend_delta = score - previous.score
            if trend_delta > 0:
                trend_direction = "improving"
            elif trend_delta < 0:
                trend_direction = "declining"
            else:
                trend_direction = "stable"

        return await self.create(
            property_id=property_id,
            score=score,
            grade=grade,
            components=components,
            calculated_at=calculated_at,
            calculation_trigger=trigger,
            executive_summary=executive_summary,
            recommendations=recommendations,
            risk_factors=risk_factors,
            strengths=strengths,
            trend_direction=trend_direction,
            trend_delta=trend_delta,
            previous_score_id=previous_score_id,
            llm_model_used=llm_model_used,
            llm_latency_ms=llm_latency_ms,
        )

    async def get_with_property(self, score_id: str) -> HealthScore | None:
        """Get health score with property details.

        Args:
            score_id: Health score ID.

        Returns:
            HealthScore with property loaded or None.
        """
        stmt = (
            select(HealthScore)
            .options(selectinload(HealthScore.property))
            .where(
                HealthScore.id == score_id,
                HealthScore.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


def get_health_score_repository(session: AsyncSession) -> HealthScoreRepository:
    """Factory function to create HealthScoreRepository.

    Args:
        session: Database session.

    Returns:
        HealthScoreRepository instance.
    """
    return HealthScoreRepository(session)
