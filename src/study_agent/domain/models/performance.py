"""Performance metrics domain model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """Performance metrics entity for spaced repetition."""

    id: int
    user_id: int
    topic_id: int
    total_sessions: int
    total_correct: int
    total_questions: int
    average_score: float
    last_studied_at: datetime | None
    next_review_at: datetime | None
    retention_score: float | None
    created_at: datetime
    updated_at: datetime
