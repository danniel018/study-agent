"""Topic repository implementation."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from study_agent.domain.models.topic import Topic
from study_agent.infrastructure.database.models import TopicModel


class TopicRepository:
    """Repository for topic data access."""

    def __init__(self, session: AsyncSession):
        """Initialize topic repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(
        self,
        repository_id: int,
        title: str,
        file_paths: list[str],
        content: str,
        content_hash: str,
    ) -> Topic:
        """Create a new topic.

        Args:
            repository_id: Repository ID
            title: Topic title
            file_paths: File path in repository
            content: Topic content
            content_hash: Content hash for change detection

        Returns:
            Created topic
        """
        topic_model = TopicModel(
            repository_id=repository_id,
            title=title,
            file_paths=file_paths,
            content=content,
            content_hash=content_hash,
            last_synced_at=datetime.now(),
        )
        self.session.add(topic_model)
        await self.session.commit()
        await self.session.refresh(topic_model)

        return Topic(
            id=topic_model.id,
            repository_id=topic_model.repository_id,
            title=topic_model.title,
            file_paths=topic_model.file_paths,
            content=topic_model.content,
            content_hash=topic_model.content_hash,
            last_synced_at=topic_model.last_synced_at,
        )

    async def get_by_repository(self, repository_id: int) -> list[Topic]:
        """Get all topics for a repository.

        Args:
            repository_id: Repository ID

        Returns:
            List of topics
        """
        stmt = select(TopicModel).where(TopicModel.repository_id == repository_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [
            Topic(
                id=model.id,
                repository_id=model.repository_id,
                title=model.title,
                file_paths=model.file_paths,
                content=model.content,
                content_hash=model.content_hash,
                last_synced_at=model.last_synced_at,
            )
            for model in models
        ]

    async def get_by_id(self, topic_id: int) -> Topic | None:
        """Get topic by ID.

        Args:
            topic_id: Topic ID

        Returns:
            Topic if found, None otherwise
        """
        stmt = select(TopicModel).where(TopicModel.id == topic_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Topic(
            id=model.id,
            repository_id=model.repository_id,
            title=model.title,
            file_paths=model.file_paths,
            content=model.content,
            content_hash=model.content_hash,
            last_synced_at=model.last_synced_at,
        )

    async def get_by_user(self, user_id: int) -> list[Topic]:
        """Get all topics for a user across all repositories.

        Args:
            user_id: User ID

        Returns:
            List of topics
        """
        from study_agent.infrastructure.database.models import RepositoryModel

        stmt = select(TopicModel).join(RepositoryModel).where(RepositoryModel.user_id == user_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [
            Topic(
                id=model.id,
                repository_id=model.repository_id,
                title=model.title,
                file_paths=model.file_paths,
                content=model.content,
                content_hash=model.content_hash,
                last_synced_at=model.last_synced_at,
            )
            for model in models
        ]

    async def delete_by_repository(self, repository_id: int) -> None:
        """Delete all topics for a repository.

        Args:
            repository_id: Repository ID
        """
        stmt = select(TopicModel).where(TopicModel.repository_id == repository_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        for model in models:
            await self.session.delete(model)

        await self.session.commit()
