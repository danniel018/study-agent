"""Assessment repository implementation."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from study_agent.domain.models.assessment import Assessment
from study_agent.infrastructure.database.models import AssessmentModel


class AssessmentRepository:
    """Repository for assessment data access."""

    def __init__(self, session: AsyncSession):
        """Initialize assessment repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(
        self,
        session_id: int,
        question: str,
        correct_answer: str,
    ) -> Assessment:
        """Create a new assessment.

        Args:
            session_id: Study session ID
            question: Question text
            correct_answer: Correct answer text

        Returns:
            Created assessment
        """
        assessment_model = AssessmentModel(
            session_id=session_id,
            question=question,
            correct_answer=correct_answer,
        )
        self.session.add(assessment_model)
        await self.session.commit()
        await self.session.refresh(assessment_model)

        return Assessment(
            id=assessment_model.id,
            session_id=assessment_model.session_id,
            question=assessment_model.question,
            user_answer=assessment_model.user_answer,
            correct_answer=assessment_model.correct_answer,
            is_correct=assessment_model.is_correct,
            llm_feedback=assessment_model.llm_feedback,
            score=assessment_model.score,
            answered_at=assessment_model.answered_at,
        )

    async def get_by_id(self, assessment_id: int) -> Assessment | None:
        """Get assessment by ID.

        Args:
            assessment_id: Assessment ID

        Returns:
            Assessment if found, None otherwise
        """
        stmt = select(AssessmentModel).where(AssessmentModel.id == assessment_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Assessment(
            id=model.id,
            session_id=model.session_id,
            question=model.question,
            user_answer=model.user_answer,
            correct_answer=model.correct_answer,
            is_correct=model.is_correct,
            llm_feedback=model.llm_feedback,
            score=model.score,
            answered_at=model.answered_at,
        )

    async def get_by_session(self, session_id: int) -> list[Assessment]:
        """Get all assessments for a study session.

        Args:
            session_id: Study session ID

        Returns:
            List of assessments
        """
        stmt = select(AssessmentModel).where(AssessmentModel.session_id == session_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [
            Assessment(
                id=model.id,
                session_id=model.session_id,
                question=model.question,
                user_answer=model.user_answer,
                correct_answer=model.correct_answer,
                is_correct=model.is_correct,
                llm_feedback=model.llm_feedback,
                score=model.score,
                answered_at=model.answered_at,
            )
            for model in models
        ]

    async def update_evaluation(
        self,
        assessment_id: int,
        user_answer: str,
        score: float,
        is_correct: bool,
        llm_feedback: str,
    ) -> Assessment:
        """Update assessment with evaluation results.

        Args:
            assessment_id: Assessment ID
            user_answer: User's answer
            score: Score (0.0-1.0)
            is_correct: Whether answer is correct
            llm_feedback: LLM feedback

        Returns:
            Updated assessment
        """
        stmt = select(AssessmentModel).where(AssessmentModel.id == assessment_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        model.user_answer = user_answer
        model.score = score
        model.is_correct = is_correct
        model.llm_feedback = llm_feedback
        model.answered_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(model)

        return Assessment(
            id=model.id,
            session_id=model.session_id,
            question=model.question,
            user_answer=model.user_answer,
            correct_answer=model.correct_answer,
            is_correct=model.is_correct,
            llm_feedback=model.llm_feedback,
            score=model.score,
            answered_at=model.answered_at,
        )
