"""Application settings and configuration."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = ""

    # Gemini API Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.0-pro"

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./study_agent.db"

    # Application Settings
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"

    # Scheduler Settings
    ENABLE_SCHEDULER: bool = True
    SCHEDULER_TIMEZONE: str = "UTC"
    DEFAULT_STUDY_TIME: str = "09:00"

    # Rate Limiting
    GITHUB_RATE_LIMIT: int = 60
    GEMINI_RATE_LIMIT: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
