"""Tests for GitHub service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from study_agent.application.services.github_service import GitHubService
from study_agent.core.exceptions import RepositoryError
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
async def repo_repository(test_session):
    """Create a repository repository instance."""
    return RepositoryRepository(test_session)


@pytest_asyncio.fixture
async def topic_repository(test_session):
    """Create a topic repository instance."""
    return TopicRepository(test_session)


class TestGitHubService:
    """Tests for GitHubService."""

    @pytest.mark.asyncio
    async def test_sync_repository_success(self, repo_repository, topic_repository, repo_in_db):
        """Test successful repository sync."""
        # Mock GitHub client
        mock_github_client = MagicMock()
        mock_github_client.fetch_all_topics = AsyncMock(
            return_value=[
                {
                    "title": "Test Topic",
                    "file_path": "docs/test.md",
                    "content": "Test content " * 20,
                    "content_hash": "hash123",
                }
            ]
        )

        service = GitHubService(
            github_client=mock_github_client,
            repo_repository=repo_repository,
            topic_repository=topic_repository,
        )

        topics_count = await service.sync_repository(repo_in_db.id)

        assert topics_count == 1
        mock_github_client.fetch_all_topics.assert_called_once_with(
            repo_in_db.repo_owner,
            repo_in_db.repo_name,
        )

    @pytest.mark.asyncio
    async def test_sync_repository_not_found(self, repo_repository, topic_repository):
        """Test sync with non-existent repository."""
        mock_github_client = MagicMock()

        service = GitHubService(
            github_client=mock_github_client,
            repo_repository=repo_repository,
            topic_repository=topic_repository,
        )

        with pytest.raises(RepositoryError) as exc_info:
            await service.sync_repository(99999)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sync_repository_no_topics(self, repo_repository, topic_repository, repo_in_db):
        """Test sync when no topics found."""
        mock_github_client = MagicMock()
        mock_github_client.fetch_all_topics = AsyncMock(return_value=[])

        service = GitHubService(
            github_client=mock_github_client,
            repo_repository=repo_repository,
            topic_repository=topic_repository,
        )

        topics_count = await service.sync_repository(repo_in_db.id)

        assert topics_count == 0

    @pytest.mark.asyncio
    async def test_sync_repository_replaces_old_topics(
        self, repo_repository, topic_repository, repo_in_db
    ):
        """Test that sync replaces old topics."""
        # First, create some existing topics
        await topic_repository.create(
            repository_id=repo_in_db.id,
            title="Old Topic",
            file_path="old.md",
            content="Old content " * 20,
            content_hash="oldhash",
        )

        existing = await topic_repository.get_by_repository(repo_in_db.id)
        assert len(existing) == 1

        # Mock GitHub client with new topics
        mock_github_client = MagicMock()
        mock_github_client.fetch_all_topics = AsyncMock(
            return_value=[
                {
                    "title": "New Topic 1",
                    "file_path": "new1.md",
                    "content": "New content 1 " * 20,
                    "content_hash": "newhash1",
                },
                {
                    "title": "New Topic 2",
                    "file_path": "new2.md",
                    "content": "New content 2 " * 20,
                    "content_hash": "newhash2",
                },
            ]
        )

        service = GitHubService(
            github_client=mock_github_client,
            repo_repository=repo_repository,
            topic_repository=topic_repository,
        )

        topics_count = await service.sync_repository(repo_in_db.id)

        assert topics_count == 2

        # Verify old topic was replaced
        current_topics = await topic_repository.get_by_repository(repo_in_db.id)
        assert len(current_topics) == 2
        titles = [t.title for t in current_topics]
        assert "Old Topic" not in titles
        assert "New Topic 1" in titles
        assert "New Topic 2" in titles
