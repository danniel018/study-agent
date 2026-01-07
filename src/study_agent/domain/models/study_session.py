"""Study session domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal


SessionType = Literal["scheduled", "manual"]
SessionStatus = Literal["in_progress", "completed", "cancelled"]


@dataclass
class StudySession:
    """Study session entity."""
    
    id: int
    user_id: int
    topic_id: int
    session_type: SessionType
    started_at: datetime
    status: SessionStatus
    completed_at: Optional[datetime] = None
