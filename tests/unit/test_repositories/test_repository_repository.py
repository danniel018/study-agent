"""Tests for repository repository."""

import pytest
import pytest_asyncio

from study_agent.infrastructure.database.repositories.repository_repository import (
    RepositoryRepository,
)
from study_agent.infrastructure.database.repositories.user_repository import UserRepository


@pytest_asyncio.fixture
async def user_in_db(test_session, mock_user_data):
    """Create a user in the test database."""
    user_repo = UserRepository(test_session)
    user = await user_repo.create(**mock_user_data)
    return user


@pytest_asyncio.fixture
async def repo_repository(test_session):
    """Create a repository repository instance."""
    return RepositoryRepository(test_session)


@pytest.fixture
def mock_repo_data():
    """Mock repository data for testing."""
    return {
        "repo_url": "https://github.com/testuser/testrepo",
        "repo_owner": "testuser",
        "repo_name": "testrepo",
    }


class TestRepositoryRepository:
    """Tests for RepositoryRepository."""

    @pytest.mark.asyncio
    async def test_create_repository(self, repo_repository, user_in_db, mock_repo_data):
        """Test creating a new repository."""
        repo = await repo_repository.create(
            user_id=user_in_db.id,
            **mock_repo_data,
        )

        assert repo is not None
        assert repo.id is not None
        assert repo.user_id == user_in_db.id
        assert repo.repo_url == mock_repo_data["repo_url"]
        assert repo.repo_owner == mock_repo_data["repo_owner"]
        assert repo.repo_name == mock_repo_data["repo_name"]
        assert repo.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_user(self, repo_repository, user_in_db, mock_repo_data):
        """Test getting repositories by user."""
        # Create multiple repos
        await repo_repository.create(
            user_id=user_in_db.id,
            repo_url="https://github.com/user/repo1",
            repo_owner="user",
            repo_name="repo1",
        )
        await repo_repository.create(
            user_id=user_in_db.id,
            repo_url="https://github.com/user/repo2",
            repo_owner="user",
            repo_name="repo2",
        )

        repos = await repo_repository.get_by_user(user_in_db.id)

        assert len(repos) == 2
        assert all(r.user_id == user_in_db.id for r in repos)

    @pytest.mark.asyncio
    async def test_get_by_id(self, repo_repository, user_in_db, mock_repo_data):
        """Test getting repository by ID."""
        created = await repo_repository.create(
            user_id=user_in_db.id,
            **mock_repo_data,
        )

        found = await repo_repository.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.repo_name == mock_repo_data["repo_name"]

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo_repository):
        """Test getting non-existent repository."""
        found = await repo_repository.get_by_id(99999)
        assert found is None

    @pytest.mark.asyncio
    async def test_update_last_synced(self, repo_repository, user_in_db, mock_repo_data):
        """Test updating last synced timestamp."""
        repo = await repo_repository.create(
            user_id=user_in_db.id,
            **mock_repo_data,
        )

        assert repo.last_synced_at is None

        await repo_repository.update_last_synced(repo.id)

        updated = await repo_repository.get_by_id(repo.id)
        assert updated.last_synced_at is not None

    @pytest.mark.asyncio
    async def test_get_by_user_empty(self, repo_repository, user_in_db):
        """Test getting repositories for user with no repos."""
        repos = await repo_repository.get_by_user(user_in_db.id)
        assert repos == []
