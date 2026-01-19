"""Topic domain model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Topic:
    """Topic entity representing a study topic from a repository."""

    id: int
    repository_id: int
    title: str
    file_paths: list[str]
    content: str
    content_hash: str
    last_synced_at: datetime
