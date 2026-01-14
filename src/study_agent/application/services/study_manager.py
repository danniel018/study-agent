"""Study manager service for session orchestration."""

import logging
from datetime import UTC, datetime, timedelta

from study_agent.config.constants import (
    EXCELLENT_MULTIPLIER,
    EXCELLENT_SCORE_THRESHOLD,
    GOOD_MULTIPLIER,
    GOOD_SCORE_THRESHOLD,
    INITIAL_INTERVAL_DAYS,
)
from study_agent.domain.models.assessment import Assessment
from study_agent.domain.models.study_session import StudySession
from study_agent.infrastructure.clients.gemini_client import GeminiClient
from study_agent.infrastructure.database.repositories.assessment_repository import (
    AssessmentRepository,
)
from study_agent.infrastructure.database.repositories.performance_metrics_repository import (
    PerformanceMetricsRepository,
)
from study_agent.infrastructure.database.repositories.study_session_repository import (
    StudySessionRepository,
)
from study_agent.infrastructure.database.repositories.topic_repository import TopicRepository

logger = logging.getLogger(__name__)


class StudyManager:
    """Service for managing study sessions and spaced repetition."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        topic_repository: TopicRepository,
        study_session_repository: StudySessionRepository,
        assessment_repository: AssessmentRepository,
        performance_metrics_repository: PerformanceMetricsRepository,
    ):
        """Initialize study manager.

        Args:
            gemini_client: Gemini LLM client
            topic_repository: Topic repository
            study_session_repository: Study session repository
            assessment_repository: Assessment repository
            performance_metrics_repository: Performance metrics repository
        """
        self.gemini_client = gemini_client
        self.topic_repository = topic_repository
        self.study_session_repository = study_session_repository
        self.assessment_repository = assessment_repository
        self.performance_metrics_repository = performance_metrics_repository

    async def create_study_session(
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
        session = await self.study_session_repository.create(
            user_id=user_id,
            topic_id=topic_id,
            session_type=session_type,
        )

        logger.info(f"Created study session {session.id} for user {user_id}")

        return session

    async def generate_quiz_questions(
        self,
        session_id: int,
        num_questions: int = 5,
    ) -> list[Assessment]:
        """Generate quiz questions for a study session.

        Args:
            session_id: Study session ID
            num_questions: Number of questions to generate

        Returns:
            List of assessments with questions
        """
        # Get session
        session = await self.study_session_repository.get_by_id(session_id)
        if not session:
            raise ValueError("Study session not found")

        # Get topic
        topic = await self.topic_repository.get_by_id(session.topic_id)
        if not topic:
            raise ValueError("Topic not found")

        logger.info(f"Generating {num_questions} questions for session {session_id}")

        # Generate questions using Gemini
        questions = await self.gemini_client.generate_quiz_questions(
            topic_content=topic.content,
            topic_title=topic.title,
            num_questions=num_questions,
        )

        # Create assessment records
        assessments = []
        for q in questions:
            assessment = await self.assessment_repository.create(
                session_id=session_id,
                question=q["question"],
                correct_answer=q["answer"],
            )
            assessments.append(assessment)

        return assessments

    async def evaluate_answer(
        self,
        assessment_id: int,
        user_answer: str,
    ) -> dict:
        """Evaluate a user's answer.

        Args:
            assessment_id: Assessment ID
            user_answer: User's answer

        Returns:
            Evaluation result with score and feedback
        """
        # Get assessment
        assessment = await self.assessment_repository.get_by_id(assessment_id)
        if not assessment:
            raise ValueError("Assessment not found")

        # Get session and topic
        session = await self.study_session_repository.get_by_id(assessment.session_id)
        if not session:
            raise ValueError("Study session not found")

        topic = await self.topic_repository.get_by_id(session.topic_id)

        # Evaluate with Gemini
        evaluation = await self.gemini_client.evaluate_answer(
            question=assessment.question,
            user_answer=user_answer,
            correct_answer=assessment.correct_answer or "",
            context=topic.content if topic else "",
        )

        # Update assessment
        await self.assessment_repository.update_evaluation(
            assessment_id=assessment_id,
            user_answer=user_answer,
            score=evaluation["score"],
            is_correct=evaluation["is_correct"],
            llm_feedback=evaluation["feedback"],
        )

        logger.info(f"Evaluated assessment {assessment_id}: score={evaluation['score']}")

        return evaluation

    async def complete_session(self, session_id: int) -> float:
        """Complete a study session and update performance metrics.

        Args:
            session_id: Study session ID

        Returns:
            Average score for the session
        """
        # Get session
        session = await self.study_session_repository.get_by_id(session_id)
        if not session:
            raise ValueError("Study session not found")

        # Get assessments
        assessments = await self.assessment_repository.get_by_session(session_id)

        # Calculate average score
        answered_assessments = [a for a in assessments if a.score is not None]
        if not answered_assessments:
            avg_score = 0.0
        else:
            avg_score = sum(a.score for a in answered_assessments) / len(answered_assessments)

        # Update session
        await self.study_session_repository.update_status(
            session_id=session_id,
            status="completed",
            completed_at=datetime.now(),
        )

        # Update or create performance metrics
        await self._update_performance_metrics(
            user_id=session.user_id,
            topic_id=session.topic_id,
            score=avg_score,
            num_questions=len(answered_assessments),
        )

        logger.info(f"Completed session {session_id}: avg_score={avg_score:.2f}")

        return avg_score

    async def _update_performance_metrics(
        self,
        user_id: int,
        topic_id: int,
        score: float,
        num_questions: int,
    ) -> None:
        """Update performance metrics for spaced repetition.

        Args:
            user_id: User ID
            topic_id: Topic ID
            score: Session score (0.0-1.0)
            num_questions: Number of questions answered
        """
        # Get existing metrics
        metrics = await self.performance_metrics_repository.get_by_user_and_topic(
            user_id=user_id,
            topic_id=topic_id,
        )

        # Calculate next review date using spaced repetition
        last_interval_days = INITIAL_INTERVAL_DAYS
        if metrics and metrics.last_studied_at and metrics.next_review_at:
            last_interval_days = self._get_last_interval_days(
                metrics.last_studied_at, metrics.next_review_at
            )

        next_review = self._calculate_next_review(
            score=score,
            last_interval_days=last_interval_days,
        )

        # Update metrics
        await self.performance_metrics_repository.update_after_session(
            user_id=user_id,
            topic_id=topic_id,
            score=score,
            num_questions=num_questions,
            last_studied_at=datetime.now(),
            next_review_at=next_review,
        )

    def _calculate_next_review(
        self,
        score: float,
        last_interval_days: int,
    ) -> datetime:
        """Calculate next review date based on performance.

        Args:
            score: Session score (0.0-1.0)
            last_interval_days: Previous interval in days

        Returns:
            Next review datetime
        """
        if score >= EXCELLENT_SCORE_THRESHOLD:
            # Excellent performance: increase interval significantly
            next_interval = int(last_interval_days * EXCELLENT_MULTIPLIER)
        elif score >= GOOD_SCORE_THRESHOLD:
            # Good performance: increase interval moderately
            next_interval = int(last_interval_days * GOOD_MULTIPLIER)
        else:
            # Poor performance: reset to initial interval
            next_interval = INITIAL_INTERVAL_DAYS

        return datetime.now(UTC) + timedelta(days=next_interval)

    def _get_last_interval_days(
        self,
        last_studied: datetime | None,
        next_review: datetime | None,
    ) -> int:
        """Get the last interval in days.

        Args:
            last_studied: Last study date
            next_review: Next review date

        Returns:
            Interval in days
        """
        if last_studied and next_review:
            interval = (next_review - last_studied).days
            return max(interval, INITIAL_INTERVAL_DAYS)
        return INITIAL_INTERVAL_DAYS

    async def get_topics_for_review(self, user_id: int) -> list[int]:
        """Get topics that are due for review.

        Args:
            user_id: User ID

        Returns:
            List of topic IDs due for review
        """
        return await self.performance_metrics_repository.get_topics_for_review(
            user_id=user_id,
            current_time=datetime.now(),
        )
