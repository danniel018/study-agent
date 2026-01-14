"""Study session repository implementation."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from study_agent.domain.models.study_session import StudySession
from study_agent.infrastructure.database.models import StudySessionModel


class StudySessionRepository:
    """Repository for study session data access."""

    def __init__(self, session: AsyncSession):
        """Initialize study session repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(
        self,
        user_id: int,
        topic_id: int,
        session_type: str = "manual",
    ) -> StudySession:
        """Create a new study session.

        Args:
            user_id: User ID
            topic_id: Topic ID
            session_type: Type of session ('manual' or 'scheduled')

        Returns:
            Created study session
        """
        session_model = StudySessionModel(
            user_id=user_id,
            topic_id=topic_id,
            session_type=session_type,
            started_at=datetime.now(UTC),
            status="in_progress",
        )
        self.session.add(session_model)
        await self.session.commit()
        await self.session.refresh(session_model)

        return StudySession(
            id=session_model.id,
            user_id=session_model.user_id,
            topic_id=session_model.topic_id,
            session_type=session_model.session_type,  # type: ignore
            started_at=session_model.started_at,
            status=session_model.status,  # type: ignore
            completed_at=session_model.completed_at,
        )

    async def get_by_id(self, session_id: int) -> StudySession | None:
        """Get study session by ID.

        Args:
            session_id: Study session ID

        Returns:
            Study session if found, None otherwise
        """
        stmt = select(StudySessionModel).where(StudySessionModel.id == session_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return StudySession(
            id=model.id,
            user_id=model.user_id,
            topic_id=model.topic_id,
            session_type=model.session_type,  # type: ignore
            started_at=model.started_at,
            status=model.status,  # type: ignore
            completed_at=model.completed_at,
        )

    async def update_status(
        self,
        session_id: int,
        status: str,
        completed_at: datetime | None = None,
    ) -> StudySession:
        """Update study session status.

        Args:
            session_id: Study session ID
            status: New status
            completed_at: Completion timestamp

        Returns:
            Updated study session
        """
        stmt = select(StudySessionModel).where(StudySessionModel.id == session_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        model.status = status
        if completed_at:
            model.completed_at = completed_at

        await self.session.commit()
        await self.session.refresh(model)

        return StudySession(
            id=model.id,
            user_id=model.user_id,
            topic_id=model.topic_id,
            session_type=model.session_type,  # type: ignore
            started_at=model.started_at,
            status=model.status,  # type: ignore
            completed_at=model.completed_at,
        )
