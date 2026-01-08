"""Study manager service for session orchestration."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from study_agent.infrastructure.database.models import (
    StudySessionModel,
    AssessmentModel,
    PerformanceMetricsModel,
)
from study_agent.domain.models.study_session import StudySession
from study_agent.domain.models.assessment import Assessment
from study_agent.infrastructure.clients.gemini_client import GeminiClient
from study_agent.infrastructure.database.repositories.topic_repository import TopicRepository
from study_agent.config.constants import (
    INITIAL_INTERVAL_DAYS,
    EXCELLENT_SCORE_THRESHOLD,
    GOOD_SCORE_THRESHOLD,
    EXCELLENT_MULTIPLIER,
    GOOD_MULTIPLIER,
)

logger = logging.getLogger(__name__)


class StudyManager:
    """Service for managing study sessions and spaced repetition."""
    
    def __init__(
        self,
        session: AsyncSession,
        gemini_client: GeminiClient,
        topic_repository: TopicRepository,
    ):
        """Initialize study manager.
        
        Args:
            session: Database session
            gemini_client: Gemini LLM client
            topic_repository: Topic repository
        """
        self.session = session
        self.gemini_client = gemini_client
        self.topic_repository = topic_repository
    
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
        session_model = StudySessionModel(
            user_id=user_id,
            topic_id=topic_id,
            session_type=session_type,
            started_at=datetime.utcnow(),
            status="in_progress",
        )
        self.session.add(session_model)
        await self.session.commit()
        await self.session.refresh(session_model)
        
        logger.info(f"Created study session {session_model.id} for user {user_id}")
        
        return StudySession(
            id=session_model.id,
            user_id=session_model.user_id,
            topic_id=session_model.topic_id,
            session_type=session_model.session_type,  # type: ignore
            started_at=session_model.started_at,
            status=session_model.status,  # type: ignore
            completed_at=session_model.completed_at,
        )
    
    async def generate_quiz_questions(
        self,
        session_id: int,
        num_questions: int = 5,
    ) -> List[Assessment]:
        """Generate quiz questions for a study session.
        
        Args:
            session_id: Study session ID
            num_questions: Number of questions to generate
            
        Returns:
            List of assessments with questions
        """
        # Get session
        stmt = select(StudySessionModel).where(StudySessionModel.id == session_id)
        result = await self.session.execute(stmt)
        session_model = result.scalar_one()
        
        # Get topic
        topic = await self.topic_repository.get_by_id(session_model.topic_id)
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
            assessment_model = AssessmentModel(
                session_id=session_id,
                question=q["question"],
                correct_answer=q["answer"],
            )
            self.session.add(assessment_model)
            assessments.append(assessment_model)
        
        await self.session.commit()
        
        return [
            Assessment(
                id=a.id,
                session_id=a.session_id,
                question=a.question,
                user_answer=a.user_answer,
                correct_answer=a.correct_answer,
                is_correct=a.is_correct,
                llm_feedback=a.llm_feedback,
                score=a.score,
                answered_at=a.answered_at,
            )
            for a in assessments
        ]
    
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
        # Get assessment and topic
        stmt = select(AssessmentModel).where(AssessmentModel.id == assessment_id)
        result = await self.session.execute(stmt)
        assessment = result.scalar_one()
        
        # Get session and topic
        session_stmt = select(StudySessionModel).where(StudySessionModel.id == assessment.session_id)
        session_result = await self.session.execute(session_stmt)
        session = session_result.scalar_one()
        
        topic = await self.topic_repository.get_by_id(session.topic_id)
        
        # Evaluate with Gemini
        evaluation = await self.gemini_client.evaluate_answer(
            question=assessment.question,
            user_answer=user_answer,
            correct_answer=assessment.correct_answer or "",
            context=topic.content if topic else "",
        )
        
        # Update assessment
        assessment.user_answer = user_answer
        assessment.score = evaluation["score"]
        assessment.is_correct = evaluation["is_correct"]
        assessment.llm_feedback = evaluation["feedback"]
        assessment.answered_at = datetime.utcnow()
        
        await self.session.commit()
        
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
        stmt = select(StudySessionModel).where(StudySessionModel.id == session_id)
        result = await self.session.execute(stmt)
        session = result.scalar_one()
        
        # Get assessments
        assess_stmt = select(AssessmentModel).where(AssessmentModel.session_id == session_id)
        assess_result = await self.session.execute(assess_stmt)
        assessments = assess_result.scalars().all()
        
        # Calculate average score
        answered_assessments = [a for a in assessments if a.score is not None]
        if not answered_assessments:
            avg_score = 0.0
        else:
            avg_score = sum(a.score for a in answered_assessments) / len(answered_assessments)
        
        # Update session
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        
        # Update or create performance metrics
        await self._update_performance_metrics(
            user_id=session.user_id,
            topic_id=session.topic_id,
            score=avg_score,
            num_questions=len(answered_assessments),
        )
        
        await self.session.commit()
        
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
        # Get or create performance metrics
        stmt = select(PerformanceMetricsModel).where(
            PerformanceMetricsModel.user_id == user_id,
            PerformanceMetricsModel.topic_id == topic_id,
        )
        result = await self.session.execute(stmt)
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            metrics = PerformanceMetricsModel(
                user_id=user_id,
                topic_id=topic_id,
                total_sessions=0,
                total_correct=0,
                total_questions=0,
                average_score=0.0,
            )
            self.session.add(metrics)
        
        # Update metrics
        metrics.total_sessions += 1
        metrics.total_questions += num_questions
        metrics.total_correct += int(num_questions * score)
        metrics.average_score = (
            (metrics.average_score * (metrics.total_sessions - 1) + score)
            / metrics.total_sessions
        )
        metrics.last_studied_at = datetime.utcnow()
        
        # Calculate next review date using spaced repetition
        next_review = self._calculate_next_review(
            score=score,
            last_interval_days=self._get_last_interval_days(metrics.last_studied_at, metrics.next_review_at),
        )
        metrics.next_review_at = next_review
        
        await self.session.commit()
    
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
        
        return datetime.utcnow() + timedelta(days=next_interval)
    
    def _get_last_interval_days(
        self,
        last_studied: Optional[datetime],
        next_review: Optional[datetime],
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
    
    async def get_topics_for_review(self, user_id: int) -> List[int]:
        """Get topics that are due for review.
        
        Args:
            user_id: User ID
            
        Returns:
            List of topic IDs due for review
        """
        now = datetime.utcnow()
        
        stmt = select(PerformanceMetricsModel).where(
            PerformanceMetricsModel.user_id == user_id,
            PerformanceMetricsModel.next_review_at <= now,
        )
        result = await self.session.execute(stmt)
        metrics = result.scalars().all()
        
        return [m.topic_id for m in metrics]
