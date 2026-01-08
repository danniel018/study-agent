"""Assessment domain model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Assessment:
    """Assessment entity representing a quiz question and answer."""

    id: int
    session_id: int
    question: str
    user_answer: str | None
    correct_answer: str
    is_correct: bool | None
    llm_feedback: str | None
    score: float | None
    answered_at: datetime | None
