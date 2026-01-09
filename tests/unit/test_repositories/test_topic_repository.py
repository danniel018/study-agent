"""Tests for topic repository."""

import pytest
import pytest_asyncio

from study_agent.infrastructure.database.repositories.repository_repository import (
    RepositoryRepository,
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
async def topic_repository(test_session):
    """Create a topic repository instance."""
    return TopicRepository(test_session)


@pytest.fixture
def mock_topic_data():
    """Mock topic data for testing."""
    return {
        "title": "Test Topic",
        "file_path": "docs/test.md",
        "content": "This is test content for the topic. " * 20,
        "content_hash": "abc123hash",
    }


class TestTopicRepository:
    """Tests for TopicRepository."""

    @pytest.mark.asyncio
    async def test_create_topic(self, topic_repository, repo_in_db, mock_topic_data):
        """Test creating a new topic."""
        topic = await topic_repository.create(
            repository_id=repo_in_db.id,
            **mock_topic_data,
        )

        assert topic is not None
        assert topic.id is not None
        assert topic.repository_id == repo_in_db.id
        assert topic.title == mock_topic_data["title"]
        assert topic.file_path == mock_topic_data["file_path"]
        assert topic.content == mock_topic_data["content"]
        assert topic.content_hash == mock_topic_data["content_hash"]

    @pytest.mark.asyncio
    async def test_get_by_repository(self, topic_repository, repo_in_db, mock_topic_data):
        """Test getting topics by repository."""
        # Create multiple topics
        await topic_repository.create(
            repository_id=repo_in_db.id,
            title="Topic 1",
            file_path="docs/topic1.md",
            content="Content 1 " * 20,
            content_hash="hash1",
        )
        await topic_repository.create(
            repository_id=repo_in_db.id,
            title="Topic 2",
            file_path="docs/topic2.md",
            content="Content 2 " * 20,
            content_hash="hash2",
        )

        topics = await topic_repository.get_by_repository(repo_in_db.id)

        assert len(topics) == 2
        assert all(t.repository_id == repo_in_db.id for t in topics)

    @pytest.mark.asyncio
    async def test_get_by_id(self, topic_repository, repo_in_db, mock_topic_data):
        """Test getting topic by ID."""
        created = await topic_repository.create(
            repository_id=repo_in_db.id,
            **mock_topic_data,
        )

        found = await topic_repository.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.title == mock_topic_data["title"]

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, topic_repository):
        """Test getting non-existent topic."""
        found = await topic_repository.get_by_id(99999)
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_user(
        self, test_session, topic_repository, repo_in_db, user_in_db, mock_topic_data
    ):
        """Test getting topics by user."""
        await topic_repository.create(
            repository_id=repo_in_db.id,
            **mock_topic_data,
        )

        topics = await topic_repository.get_by_user(user_in_db.id)

        assert len(topics) == 1
        assert topics[0].title == mock_topic_data["title"]

    @pytest.mark.asyncio
    async def test_delete_by_repository(self, topic_repository, repo_in_db, mock_topic_data):
        """Test deleting topics by repository."""
        # Create topics
        await topic_repository.create(
            repository_id=repo_in_db.id,
            title="Topic 1",
            file_path="docs/topic1.md",
            content="Content 1 " * 20,
            content_hash="hash1",
        )
        await topic_repository.create(
            repository_id=repo_in_db.id,
            title="Topic 2",
            file_path="docs/topic2.md",
            content="Content 2 " * 20,
            content_hash="hash2",
        )

        # Verify topics exist
        topics_before = await topic_repository.get_by_repository(repo_in_db.id)
        assert len(topics_before) == 2

        # Delete all topics
        await topic_repository.delete_by_repository(repo_in_db.id)

        # Verify topics are deleted
        topics_after = await topic_repository.get_by_repository(repo_in_db.id)
        assert len(topics_after) == 0

    @pytest.mark.asyncio
    async def test_get_by_repository_empty(self, topic_repository, repo_in_db):
        """Test getting topics for repository with no topics."""
        topics = await topic_repository.get_by_repository(repo_in_db.id)
        assert topics == []
