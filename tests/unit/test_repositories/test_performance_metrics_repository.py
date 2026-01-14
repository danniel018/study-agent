"""Tests for performance metrics repository."""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio

from study_agent.infrastructure.database.repositories.performance_metrics_repository import (
    PerformanceMetricsRepository,
)
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
async def topic_in_db(test_session, repo_in_db):
    """Create a topic in the test database."""
    topic_repo = TopicRepository(test_session)
    topic = await topic_repo.create(
        repository_id=repo_in_db.id,
        title="Test Topic",
        file_path="docs/test.md",
        content="This is test content for the topic. " * 20,
        content_hash="abc123hash",
    )
    return topic


@pytest_asyncio.fixture
async def performance_metrics_repository(test_session):
    """Create a performance metrics repository instance."""
    return PerformanceMetricsRepository(test_session)


class TestPerformanceMetricsRepository:
    """Tests for PerformanceMetricsRepository."""

    @pytest.mark.asyncio
    async def test_create_performance_metrics(
        self, performance_metrics_repository, user_in_db, topic_in_db
    ):
        """Test creating new performance metrics."""
        metrics = await performance_metrics_repository.create(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
        )

        assert metrics is not None
        assert metrics.id is not None
        assert metrics.user_id == user_in_db.id
        assert metrics.topic_id == topic_in_db.id
        assert metrics.total_sessions == 0
        assert metrics.total_correct == 0
        assert metrics.total_questions == 0
        assert metrics.average_score == 0.0

    @pytest.mark.asyncio
    async def test_get_by_user_and_topic(
        self, performance_metrics_repository, user_in_db, topic_in_db
    ):
        """Test getting performance metrics by user and topic."""
        created = await performance_metrics_repository.create(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
        )

        found = await performance_metrics_repository.get_by_user_and_topic(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
        )

        assert found is not None
        assert found.id == created.id
        assert found.user_id == user_in_db.id
        assert found.topic_id == topic_in_db.id

    @pytest.mark.asyncio
    async def test_get_by_user_and_topic_not_found(
        self, performance_metrics_repository, user_in_db, topic_in_db
    ):
        """Test getting non-existent performance metrics."""
        found = await performance_metrics_repository.get_by_user_and_topic(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
        )
        assert found is None

    @pytest.mark.asyncio
    async def test_update_after_session(
        self, performance_metrics_repository, user_in_db, topic_in_db
    ):
        """Test updating performance metrics after a session."""
        now = datetime.now()
        next_review = now + timedelta(days=7)

        metrics = await performance_metrics_repository.update_after_session(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
            score=0.8,
            num_questions=5,
            last_studied_at=now,
            next_review_at=next_review,
        )

        assert metrics.total_sessions == 1
        assert metrics.total_questions == 5
        assert metrics.total_correct == 4  # 5 * 0.8
        assert metrics.average_score == 0.8
        assert metrics.last_studied_at is not None
        assert metrics.next_review_at is not None

    @pytest.mark.asyncio
    async def test_update_after_session_multiple_times(
        self, performance_metrics_repository, user_in_db, topic_in_db
    ):
        """Test updating performance metrics multiple times."""
        now = datetime.now()
        next_review = now + timedelta(days=7)

        # First session
        await performance_metrics_repository.update_after_session(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
            score=0.8,
            num_questions=5,
            last_studied_at=now,
            next_review_at=next_review,
        )

        # Second session
        metrics = await performance_metrics_repository.update_after_session(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
            score=0.6,
            num_questions=3,
            last_studied_at=now,
            next_review_at=next_review,
        )

        assert metrics.total_sessions == 2
        assert metrics.total_questions == 8  # 5 + 3
        assert metrics.total_correct == 5  # 4 + 1 (rounded)
        assert metrics.average_score == 0.7  # (0.8 + 0.6) / 2

    @pytest.mark.asyncio
    async def test_get_topics_for_review(
        self, performance_metrics_repository, user_in_db, topic_in_db
    ):
        """Test getting topics due for review."""
        now = datetime.now()
        past_review = now - timedelta(days=1)

        # Create metrics with past review date
        await performance_metrics_repository.update_after_session(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
            score=0.8,
            num_questions=5,
            last_studied_at=now - timedelta(days=8),
            next_review_at=past_review,
        )

        topics = await performance_metrics_repository.get_topics_for_review(
            user_id=user_in_db.id,
            current_time=now,
        )

        assert len(topics) == 1
        assert topics[0] == topic_in_db.id

    @pytest.mark.asyncio
    async def test_get_topics_for_review_none_due(
        self, performance_metrics_repository, user_in_db, topic_in_db
    ):
        """Test getting topics when none are due for review."""
        now = datetime.now()
        future_review = now + timedelta(days=7)

        # Create metrics with future review date
        await performance_metrics_repository.update_after_session(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
            score=0.8,
            num_questions=5,
            last_studied_at=now,
            next_review_at=future_review,
        )

        topics = await performance_metrics_repository.get_topics_for_review(
            user_id=user_in_db.id,
            current_time=now,
        )

        assert len(topics) == 0

    @pytest.mark.asyncio
    async def test_update_after_session_creates_if_not_exists(
        self, performance_metrics_repository, user_in_db, topic_in_db
    ):
        """Test that update_after_session creates metrics if they don't exist."""
        now = datetime.now()
        next_review = now + timedelta(days=7)

        # Verify metrics don't exist
        found = await performance_metrics_repository.get_by_user_and_topic(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
        )
        assert found is None

        # Update should create them
        metrics = await performance_metrics_repository.update_after_session(
            user_id=user_in_db.id,
            topic_id=topic_in_db.id,
            score=0.9,
            num_questions=5,
            last_studied_at=now,
            next_review_at=next_review,
        )

        assert metrics is not None
        assert metrics.total_sessions == 1
        assert metrics.average_score == 0.9
