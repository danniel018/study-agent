"""User domain model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """User entity representing a Telegram user."""

    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
