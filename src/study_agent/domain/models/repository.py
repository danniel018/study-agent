"""Repository domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Repository:
    """Repository entity representing a GitHub repository."""
    
    id: int
    user_id: int
    repo_url: str
    repo_owner: str
    repo_name: str
    is_active: bool
    created_at: datetime
    last_synced_at: Optional[datetime] = None
