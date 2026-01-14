"""Performance metrics repository implementation."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from study_agent.domain.models.performance import PerformanceMetrics
from study_agent.infrastructure.database.models import PerformanceMetricsModel


class PerformanceMetricsRepository:
    """Repository for performance metrics data access."""

    def __init__(self, session: AsyncSession):
        """Initialize performance metrics repository.

        Args:
            session: Database session
        """
        self.session = session

    async def get_by_user_and_topic(
        self,
        user_id: int,
        topic_id: int,
    ) -> PerformanceMetrics | None:
        """Get performance metrics by user and topic.

        Args:
            user_id: User ID
            topic_id: Topic ID

        Returns:
            Performance metrics if found, None otherwise
        """
        stmt = select(PerformanceMetricsModel).where(
            PerformanceMetricsModel.user_id == user_id,
            PerformanceMetricsModel.topic_id == topic_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return PerformanceMetrics(
            id=model.id,
            user_id=model.user_id,
            topic_id=model.topic_id,
            total_sessions=model.total_sessions,
            total_correct=model.total_correct,
            total_questions=model.total_questions,
            average_score=model.average_score,
            last_studied_at=model.last_studied_at,
            next_review_at=model.next_review_at,
            retention_score=model.retention_score,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def create(
        self,
        user_id: int,
        topic_id: int,
    ) -> PerformanceMetrics:
        """Create new performance metrics.

        Args:
            user_id: User ID
            topic_id: Topic ID

        Returns:
            Created performance metrics
        """
        metrics_model = PerformanceMetricsModel(
            user_id=user_id,
            topic_id=topic_id,
            total_sessions=0,
            total_correct=0,
            total_questions=0,
            average_score=0.0,
        )
        self.session.add(metrics_model)
        await self.session.commit()
        await self.session.refresh(metrics_model)

        return PerformanceMetrics(
            id=metrics_model.id,
            user_id=metrics_model.user_id,
            topic_id=metrics_model.topic_id,
            total_sessions=metrics_model.total_sessions,
            total_correct=metrics_model.total_correct,
            total_questions=metrics_model.total_questions,
            average_score=metrics_model.average_score,
            last_studied_at=metrics_model.last_studied_at,
            next_review_at=metrics_model.next_review_at,
            retention_score=metrics_model.retention_score,
            created_at=metrics_model.created_at,
            updated_at=metrics_model.updated_at,
        )

    async def update_after_session(
        self,
        user_id: int,
        topic_id: int,
        score: float,
        num_questions: int,
        last_studied_at: datetime,
        next_review_at: datetime,
    ) -> PerformanceMetrics:
        """Update performance metrics after a study session.

        Args:
            user_id: User ID
            topic_id: Topic ID
            score: Session score (0.0-1.0)
            num_questions: Number of questions answered
            last_studied_at: Last study timestamp
            next_review_at: Next review timestamp

        Returns:
            Updated performance metrics
        """
        # Get or create metrics
        metrics = await self.get_by_user_and_topic(user_id, topic_id)

        if not metrics:
            metrics = await self.create(user_id, topic_id)

        # Get the model to update
        stmt = select(PerformanceMetricsModel).where(
            PerformanceMetricsModel.user_id == user_id,
            PerformanceMetricsModel.topic_id == topic_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        # Update metrics
        model.total_sessions += 1
        model.total_questions += num_questions
        model.total_correct += int(num_questions * score)
        model.average_score = (
            model.average_score * (model.total_sessions - 1) + score
        ) / model.total_sessions
        model.last_studied_at = last_studied_at
        model.next_review_at = next_review_at

        await self.session.commit()
        await self.session.refresh(model)

        return PerformanceMetrics(
            id=model.id,
            user_id=model.user_id,
            topic_id=model.topic_id,
            total_sessions=model.total_sessions,
            total_correct=model.total_correct,
            total_questions=model.total_questions,
            average_score=model.average_score,
            last_studied_at=model.last_studied_at,
            next_review_at=model.next_review_at,
            retention_score=model.retention_score,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_topics_for_review(self, user_id: int, current_time: datetime) -> list[int]:
        """Get topics that are due for review.

        Args:
            user_id: User ID
            current_time: Current timestamp

        Returns:
            List of topic IDs due for review
        """
        stmt = select(PerformanceMetricsModel).where(
            PerformanceMetricsModel.user_id == user_id,
            PerformanceMetricsModel.next_review_at <= current_time,
        )
        result = await self.session.execute(stmt)
        metrics = result.scalars().all()

        return [m.topic_id for m in metrics]
