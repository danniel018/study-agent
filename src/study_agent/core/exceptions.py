"""Custom exceptions for the Study Agent application."""


class StudyAgentException(Exception):
    """Base exception for all application errors."""
    
    pass


class RepositoryError(StudyAgentException):
    """Raised when there's an error with repository operations."""
    
    pass


class RepositoryNotFoundError(RepositoryError):
    """Raised when a GitHub repository is not found."""
    
    pass


class RepositoryAccessError(RepositoryError):
    """Raised when unable to access a GitHub repository."""
    
    pass


class LLMServiceError(StudyAgentException):
    """Raised when LLM service fails."""
    
    pass


class DatabaseError(StudyAgentException):
    """Raised when there's a database error."""
    
    pass


class ValidationError(StudyAgentException):
    """Raised when validation fails."""
    
    pass


class ContentError(StudyAgentException):
    """Raised when there's an error with content processing."""
    
    pass
