"""SQLAlchemy database models."""

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from study_agent.infrastructure.database.engine import Base


class UserModel(Base):
    """User table model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    timezone = Column(String, default="UTC", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    repositories = relationship("RepositoryModel", back_populates="user")
    study_sessions = relationship("StudySessionModel", back_populates="user")
    performance_metrics = relationship("PerformanceMetricsModel", back_populates="user")
    schedule_config = relationship("ScheduleConfigModel", back_populates="user", uselist=False)


class RepositoryModel(Base):
    """Repository table model."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    repo_url = Column(String, nullable=False)
    repo_owner = Column(String, nullable=False)
    repo_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    last_synced_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="repositories")
    topics = relationship("TopicModel", back_populates="repository")

    __table_args__ = (UniqueConstraint("user_id", "repo_owner", "repo_name", name="uq_user_repo"),)


class TopicModel(Base):
    """Topic table model."""

    __tablename__ = "topics"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    file_paths = Column(JSON, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String, nullable=False)
    last_synced_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    repository = relationship("RepositoryModel", back_populates="topics")
    study_sessions = relationship("StudySessionModel", back_populates="topic")
    performance_metrics = relationship("PerformanceMetricsModel", back_populates="topic")


class StudySessionModel(Base):
    """Study session table model."""

    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    session_type = Column(String, nullable=False)  # 'scheduled', 'manual'
    started_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(
        String, default="in_progress", nullable=False
    )  # 'in_progress', 'completed', 'cancelled'

    # Relationships
    user = relationship("UserModel", back_populates="study_sessions")
    topic = relationship("TopicModel", back_populates="study_sessions")
    assessments = relationship("AssessmentModel", back_populates="session")


class AssessmentModel(Base):
    """Assessment table model."""

    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    llm_feedback = Column(Text, nullable=True)
    score = Column(Float, nullable=True)  # 0.0 to 1.0
    answered_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("StudySessionModel", back_populates="assessments")


class PerformanceMetricsModel(Base):
    """Performance metrics table model."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    total_sessions = Column(Integer, default=0, nullable=False)
    total_correct = Column(Integer, default=0, nullable=False)
    total_questions = Column(Integer, default=0, nullable=False)
    average_score = Column(Float, default=0.0, nullable=False)
    last_studied_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    retention_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user = relationship("UserModel", back_populates="performance_metrics")
    topic = relationship("TopicModel", back_populates="performance_metrics")

    __table_args__ = (UniqueConstraint("user_id", "topic_id", name="uq_user_topic_metrics"),)


class ScheduleConfigModel(Base):
    """Schedule configuration table model."""

    __tablename__ = "schedule_config"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    frequency = Column(String, default="daily", nullable=False)  # 'daily', 'weekly', 'custom'
    preferred_time = Column(String, nullable=True)  # HH:MM format
    days_of_week = Column(String, nullable=True)  # JSON array for weekly
    questions_per_session = Column(Integer, default=5, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="schedule_config")
