"""Custom exceptions for the Study Agent application."""


class StudyAgentError(Exception):
    """Base exception for all application errors."""

    pass


class RepositoryError(StudyAgentError):
    """Raised when there's an error with repository operations."""

    pass


class RepositoryNotFoundError(RepositoryError):
    """Raised when a GitHub repository is not found."""

    pass


class RepositoryAccessError(RepositoryError):
    """Raised when unable to access a GitHub repository."""

    pass


class LLMServiceError(StudyAgentError):
    """Raised when LLM service fails."""

    pass


class DatabaseError(StudyAgentError):
    """Raised when there's a database error."""

    pass


class ValidationError(StudyAgentError):
    """Raised when validation fails."""

    pass


class ContentError(StudyAgentError):
    """Raised when there's an error with content processing."""

    pass
