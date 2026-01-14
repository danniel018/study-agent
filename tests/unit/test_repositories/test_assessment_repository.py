"""Tests for assessment repository."""

import pytest
import pytest_asyncio

from study_agent.infrastructure.database.repositories.assessment_repository import (
    AssessmentRepository,
)
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
        file_path="docs/test.md",
        content="This is test content for the topic. " * 20,
        content_hash="abc123hash",
    )
    return topic


@pytest_asyncio.fixture
async def study_session_in_db(test_session, user_in_db, topic_in_db):
    """Create a study session in the test database."""
    session_repo = StudySessionRepository(test_session)
    session = await session_repo.create(
        user_id=user_in_db.id,
        topic_id=topic_in_db.id,
        session_type="manual",
    )
    return session


@pytest_asyncio.fixture
async def assessment_repository(test_session):
    """Create an assessment repository instance."""
    return AssessmentRepository(test_session)


class TestAssessmentRepository:
    """Tests for AssessmentRepository."""

    @pytest.mark.asyncio
    async def test_create_assessment(
        self, assessment_repository, study_session_in_db
    ):
        """Test creating a new assessment."""
        assessment = await assessment_repository.create(
            session_id=study_session_in_db.id,
            question="What is Python?",
            correct_answer="A programming language",
        )

        assert assessment is not None
        assert assessment.id is not None
        assert assessment.session_id == study_session_in_db.id
        assert assessment.question == "What is Python?"
        assert assessment.correct_answer == "A programming language"
        assert assessment.user_answer is None
        assert assessment.score is None
        assert assessment.is_correct is None

    @pytest.mark.asyncio
    async def test_get_by_id(self, assessment_repository, study_session_in_db):
        """Test getting assessment by ID."""
        created = await assessment_repository.create(
            session_id=study_session_in_db.id,
            question="Test question?",
            correct_answer="Test answer",
        )

        found = await assessment_repository.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.question == "Test question?"
        assert found.correct_answer == "Test answer"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, assessment_repository):
        """Test getting non-existent assessment."""
        found = await assessment_repository.get_by_id(99999)
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_session(
        self, assessment_repository, study_session_in_db
    ):
        """Test getting all assessments for a session."""
        # Create multiple assessments
        await assessment_repository.create(
            session_id=study_session_in_db.id,
            question="Question 1?",
            correct_answer="Answer 1",
        )
        await assessment_repository.create(
            session_id=study_session_in_db.id,
            question="Question 2?",
            correct_answer="Answer 2",
        )

        assessments = await assessment_repository.get_by_session(
            study_session_in_db.id
        )

        assert len(assessments) == 2
        assert all(a.session_id == study_session_in_db.id for a in assessments)

    @pytest.mark.asyncio
    async def test_update_evaluation(
        self, assessment_repository, study_session_in_db
    ):
        """Test updating assessment with evaluation results."""
        assessment = await assessment_repository.create(
            session_id=study_session_in_db.id,
            question="What is 2+2?",
            correct_answer="4",
        )

        updated = await assessment_repository.update_evaluation(
            assessment_id=assessment.id,
            user_answer="4",
            score=1.0,
            is_correct=True,
            llm_feedback="Excellent!",
        )

        assert updated.user_answer == "4"
        assert updated.score == 1.0
        assert updated.is_correct is True
        assert updated.llm_feedback == "Excellent!"
        assert updated.answered_at is not None

    @pytest.mark.asyncio
    async def test_get_by_session_empty(
        self, assessment_repository, study_session_in_db
    ):
        """Test getting assessments for session with no assessments."""
        assessments = await assessment_repository.get_by_session(
            study_session_in_db.id
        )
        assert assessments == []

    @pytest.mark.asyncio
    async def test_update_evaluation_partial_credit(
        self, assessment_repository, study_session_in_db
    ):
        """Test updating assessment with partial credit."""
        assessment = await assessment_repository.create(
            session_id=study_session_in_db.id,
            question="What is the capital of France?",
            correct_answer="Paris",
        )

        updated = await assessment_repository.update_evaluation(
            assessment_id=assessment.id,
            user_answer="paris",
            score=0.8,
            is_correct=True,
            llm_feedback="Correct, but watch your capitalization.",
        )

        assert updated.score == 0.8
        assert updated.is_correct is True
        assert "capitalization" in updated.llm_feedback
