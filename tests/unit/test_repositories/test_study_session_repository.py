"""Tests for study session repository."""

from datetime import UTC, datetime

import pytest
import pytest_asyncio

from study_agent.infrastructure.database.repositories.repository_repository import (
    RepositoryRepository,
)
from study_agent.infrastructure.database.repositories.study_session_repository import (
    StudySessionRepository,
)
from study_agent.infrastructure.database.repositories.topic_repository import TopicRepository
from study_agent.infrastructure.database.repositories.user_repository import UserRepository


@pytest_asyncio.fixture
async def user_in_db(test_session, mock_user_data):
    """Create a user in the test database."""
    user_repo = UserRepository(test_session)
    user = await user_repo.create(**mock_user_data)
    return user


@pytest_asyncio.fixture
async def repo_in_db(test_session, user_in_db):
    """Create a repository in the test database."""
    repo_repo = RepositoryRepository(test_session)
    repo = await repo_repo.create(
        user_id=user_in_db.id,
        repo_url="https://github.com/testuser/testrepo",
        repo_owner="testuser",
        repo_name="testrepo",
    )
    return repo


@pytest_asyncio.fixture
async def topic_in_db(test_session, repo_in_db):
    """Create a topic in the test database."""
    topic_repo = TopicRepository(test_session)
    topic = await topic_repo.create(
        repository_id=repo_in_db.id,
        title="Test Topic",
        file_paths=["docs/test.md"],
        content="This is test content for the topic. " * 20,
        content_hash="abc123hash",
    )
    return topic


@pytest_asyncio.fixture
async def study_session_repository(test_session):
    """Create a study session repository instance."""
    return StudySessionRepository(test_session)


class TestStudySessionRepository:
    """Tests for StudySessionRepository."""

    @pytest.mark.asyncio
    async def test_create_study_session(self, study_session_repository, user_in_db, topic_in_db):
        """Test creating a new study session."""
        session = await study_session_repository.create(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
            session_type="manual",
        )

        assert session is not None
        assert session.id is not None
        assert session.user_id == user_in_db.id
        assert session.topic_id == topic_in_db.id
        assert session.session_type == "manual"
        assert session.status == "in_progress"
        assert session.started_at is not None
        assert session.completed_at is None

    @pytest.mark.asyncio
    async def test_get_by_id(self, study_session_repository, user_in_db, topic_in_db):
        """Test getting study session by ID."""
        created = await study_session_repository.create(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
            session_type="scheduled",
        )

        found = await study_session_repository.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.user_id == user_in_db.id
        assert found.topic_id == topic_in_db.id
        assert found.session_type == "scheduled"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, study_session_repository):
        """Test getting non-existent study session."""
        found = await study_session_repository.get_by_id(99999)
        assert found is None

    @pytest.mark.asyncio
    async def test_update_status(self, study_session_repository, user_in_db, topic_in_db):
        """Test updating study session status."""
        session = await study_session_repository.create(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
            session_type="manual",
        )

        completed_at = datetime.now(UTC)
        updated = await study_session_repository.update_status(
            session_id=session.id,
            status="completed",
            completed_at=completed_at,
        )

        assert updated.status == "completed"
        assert updated.completed_at is not None
        assert updated.id == session.id

    @pytest.mark.asyncio
    async def test_create_with_default_session_type(
        self, study_session_repository, user_in_db, topic_in_db
    ):
        """Test creating study session with default session type."""
        session = await study_session_repository.create(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
        )

        assert session.session_type == "manual"
