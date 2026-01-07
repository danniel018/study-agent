"""Performance metrics domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
    last_studied_at: Optional[datetime]
    next_review_at: Optional[datetime]
    retention_score: Optional[float]
    created_at: datetime
    updated_at: datetime
