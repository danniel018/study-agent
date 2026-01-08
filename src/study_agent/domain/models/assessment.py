"""Assessment domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Assessment:
    """Assessment entity representing a quiz question and answer."""
    
    id: int
    session_id: int
    question: str
    user_answer: Optional[str]
    correct_answer: str
    is_correct: Optional[bool]
    llm_feedback: Optional[str]
    score: Optional[float]
    answered_at: Optional[datetime]
