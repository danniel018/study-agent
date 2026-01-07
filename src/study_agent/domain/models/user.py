"""User domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User entity representing a Telegram user."""
    
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    timezone: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
