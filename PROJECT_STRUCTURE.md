# Study Agent Chatbot - Project Structure

## Overview

This document outlines the complete project structure following Python best practices, clean architecture principles, and maintainable organization.

## Directory Structure

```
study-agent/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # CI/CD pipeline
│       └── coverage.yml              # Coverage reporting
├── docs/
│   ├── DESIGN.md                     # System design document
│   ├── API.md                        # API documentation
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── DEVELOPMENT.md                # Development setup guide
│   ├── WHATSAPP_INTEGRATION.md       # WhatsApp integration guide
│   └── ARCHITECTURE.md               # Architecture diagrams
├── src/
│   └── study_agent/
│       ├── __init__.py
│       ├── __main__.py               # Entry point
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py           # Configuration management
│       │   └── constants.py          # Application constants
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models/               # Domain models (entities)
│       │   │   ├── __init__.py
│       │   │   ├── user.py
│       │   │   ├── repository.py
│       │   │   ├── topic.py
│       │   │   ├── study_session.py
│       │   │   ├── assessment.py
│       │   │   └── performance.py
│       │   ├── protocols/            # Interfaces/protocols
│       │   │   ├── __init__.py
│       │   │   ├── repository.py
│       │   │   ├── llm_service.py
│       │   │   └── github_service.py
│       │   └── value_objects/        # Value objects
│       │       ├── __init__.py
│       │       ├── schedule_config.py
│       │       └── evaluation_result.py
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── database/
│       │   │   ├── __init__.py
│       │   │   ├── engine.py         # Database engine setup
│       │   │   ├── models.py         # SQLAlchemy models
│       │   │   ├── migrations/       # Alembic migrations
│       │   │   │   ├── env.py
│       │   │   │   ├── script.py.mako
│       │   │   │   └── versions/
│       │   │   └── repositories/     # Data access implementations
│       │   │       ├── __init__.py
│       │   │       ├── user_repository.py
│       │   │       ├── repository_repository.py
│       │   │       ├── topic_repository.py
│       │   │       ├── session_repository.py
│       │   │       ├── assessment_repository.py
│       │   │       └── performance_repository.py
│       │   ├── clients/
│       │   │   ├── __init__.py
│       │   │   ├── github_client.py  # GitHub API client
│       │   │   ├── gemini_client.py  # Gemini API client
│       │   │   └── rate_limiter.py   # Rate limiting utility
│       │   └── logging/
│       │       ├── __init__.py
│       │       └── logger.py         # Logging configuration
│       ├── application/
│       │   ├── __init__.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── github_service.py # GitHub operations
│       │   │   ├── llm_service.py    # LLM operations
│       │   │   ├── study_manager.py  # Study session management
│       │   │   ├── scheduler_service.py # Scheduling logic
│       │   │   ├── assessment_service.py # Assessment orchestration
│       │   │   └── user_service.py   # User management
│       │   ├── dto/                  # Data Transfer Objects
│       │   │   ├── __init__.py
│       │   │   ├── quiz_dto.py
│       │   │   ├── session_dto.py
│       │   │   └── stats_dto.py
│       │   └── use_cases/            # Application use cases
│       │       ├── __init__.py
│       │       ├── add_repository.py
│       │       ├── start_study_session.py
│       │       ├── configure_schedule.py
│       │       └── get_user_stats.py
│       ├── presentation/
│       │   ├── __init__.py
│       │   ├── telegram/
│       │   │   ├── __init__.py
│       │   │   ├── bot.py            # Bot initialization
│       │   │   ├── handlers/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── command_handlers.py
│       │   │   │   ├── message_handlers.py
│       │   │   │   ├── callback_handlers.py
│       │   │   │   └── error_handlers.py
│       │   │   ├── keyboards/        # Inline/reply keyboards
│       │   │   │   ├── __init__.py
│       │   │   │   ├── main_keyboard.py
│       │   │   │   └── quiz_keyboard.py
│       │   │   ├── middlewares/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── auth_middleware.py
│       │   │   │   └── logging_middleware.py
│       │   │   ├── states/           # FSM states
│       │   │   │   ├── __init__.py
│       │   │   │   ├── repository_states.py
│       │   │   │   ├── quiz_states.py
│       │   │   │   └── schedule_states.py
│       │   │   └── filters/
│       │   │       ├── __init__.py
│       │   │       └── custom_filters.py
│       │   └── formatters/           # Response formatters
│       │       ├── __init__.py
│       │       ├── quiz_formatter.py
│       │       └── stats_formatter.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── exceptions.py         # Custom exceptions
│       │   ├── utils.py              # Utility functions
│       │   └── decorators.py         # Custom decorators
│       └── scheduler/
│           ├── __init__.py
│           ├── job_scheduler.py      # APScheduler setup
│           └── jobs/
│               ├── __init__.py
│               └── assessment_job.py # Scheduled assessment jobs
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration & fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_services/
│   │   │   ├── __init__.py
│   │   │   ├── test_github_service.py
│   │   │   ├── test_llm_service.py
│   │   │   ├── test_study_manager.py
│   │   │   └── test_scheduler_service.py
│   │   ├── test_repositories/
│   │   │   ├── __init__.py
│   │   │   ├── test_user_repository.py
│   │   │   └── test_topic_repository.py
│   │   ├── test_handlers/
│   │   │   ├── __init__.py
│   │   │   ├── test_command_handlers.py
│   │   │   └── test_callback_handlers.py
│   │   └── test_utils/
│   │       ├── __init__.py
│   │       └── test_utils.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_study_flow.py
│   │   ├── test_repository_sync.py
│   │   └── test_assessment_flow.py
│   ├── e2e/
│   │   ├── __init__.py
│   │   └── test_complete_workflow.py
│   └── fixtures/
│       ├── __init__.py
│       ├── sample_repositories.py
│       └── sample_topics.md
├── scripts/
│   ├── init_db.py                    # Database initialization
│   ├── seed_data.py                  # Seed test data
│   └── run_migrations.py             # Migration runner
├── .env.example                      # Environment variables template
├── .gitignore
├── .python-version                   # Python version (3.14)
├── alembic.ini                       # Alembic configuration
├── pyproject.toml                    # Project metadata & dependencies
├── requirements.txt                  # Pinned dependencies
├── requirements-dev.txt              # Development dependencies
├── setup.py                          # Package setup
├── pytest.ini                        # Pytest configuration
├── .coveragerc                       # Coverage configuration
├── README.md                         # Project overview
├── CONTRIBUTING.md                   # Contribution guidelines
├── LICENSE                           # License file
└── CHANGELOG.md                      # Version changelog
```

## Module Responsibilities

### 1. `src/study_agent/config/`
Configuration management using Pydantic settings or similar.

**Files:**
- `settings.py`: Environment-based configuration (API keys, database URL, etc.)
- `constants.py`: Application-wide constants

### 2. `src/study_agent/domain/`
Core business entities and interfaces. No external dependencies.

**Subdirectories:**
- `models/`: Domain entities (User, Topic, StudySession, etc.)
- `protocols/`: Interface definitions using typing.Protocol
- `value_objects/`: Immutable value objects

### 3. `src/study_agent/infrastructure/`
External integrations and technical implementations.

**Subdirectories:**
- `database/`: SQLAlchemy models, engine, migrations, repositories
- `clients/`: HTTP clients for external APIs (GitHub, Gemini)
- `logging/`: Logging configuration

### 4. `src/study_agent/application/`
Business logic and use cases. Orchestrates domain and infrastructure.

**Subdirectories:**
- `services/`: Business logic services
- `dto/`: Data transfer objects for inter-layer communication
- `use_cases/`: Specific application use cases

### 5. `src/study_agent/presentation/`
User interface layer (Telegram bot).

**Subdirectories:**
- `telegram/`: All Telegram-related code
  - `handlers/`: Message and command handlers
  - `keyboards/`: Telegram keyboard definitions
  - `middlewares/`: Request middlewares
  - `states/`: FSM state definitions
  - `filters/`: Custom message filters
- `formatters/`: Format data for presentation

### 6. `src/study_agent/core/`
Core utilities and cross-cutting concerns.

**Files:**
- `exceptions.py`: Custom exception hierarchy
- `utils.py`: General utility functions
- `decorators.py`: Custom decorators (retry, logging, etc.)

### 7. `src/study_agent/scheduler/`
Background job scheduling.

**Files:**
- `job_scheduler.py`: APScheduler configuration
- `jobs/`: Individual job definitions

### 8. `tests/`
Comprehensive test suite with 90% coverage target.

**Structure:**
- `unit/`: Fast, isolated unit tests
- `integration/`: Integration tests with real dependencies
- `e2e/`: End-to-end workflow tests
- `fixtures/`: Test data and fixtures

## Key Files

### `pyproject.toml`
```toml
[project]
name = "study-agent"
version = "0.1.0"
description = "AI-powered study assistant chatbot"
requires-python = ">=3.14"
dependencies = [
    "aiogram>=3.0.0",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.19.0",
    "httpx>=0.25.0",
    "google-generativeai>=0.3.0",
    "apscheduler>=3.10.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "alembic>=1.12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "black>=23.7.0",
    "ruff>=0.0.285",
    "mypy>=1.5.0",
    "pre-commit>=3.3.0",
]

[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src/study_agent --cov-report=html --cov-report=term-missing --cov-fail-under=90"

[tool.coverage.run]
source = ["src/study_agent"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.black]
line-length = 100
target-version = ["py314"]

[tool.ruff]
line-length = 100
target-version = "py314"
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.14"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### `.env.example`
```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./study_agent.db

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development

# GitHub Configuration (optional for private repos)
GITHUB_TOKEN=

# Scheduler Settings
ENABLE_SCHEDULER=true
SCHEDULER_TIMEZONE=UTC

# Rate Limiting
GITHUB_RATE_LIMIT=60
GEMINI_RATE_LIMIT=60
```

### `README.md` (Brief Structure)
```markdown
# Study Agent Chatbot

AI-powered study assistant that helps you learn through scheduled quizzes.

## Features
- GitHub repository integration
- AI-generated quizzes
- Performance tracking
- Spaced repetition
- Telegram interface

## Quick Start
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` file
4. Initialize database: `python scripts/init_db.py`
5. Run: `python -m study_agent`

## Documentation
- [Design Document](docs/DESIGN.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [API Documentation](docs/API.md)

## Testing
```bash
pytest tests/ --cov
```

## License
MIT
```

## Dependency Management

### Core Dependencies
- **aiogram**: Telegram Bot API framework
- **sqlalchemy**: ORM for database operations
- **aiosqlite**: Async SQLite driver
- **httpx**: Async HTTP client
- **google-generativeai**: Google Gemini API
- **apscheduler**: Job scheduling
- **pydantic**: Data validation

### Development Dependencies
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **black**: Code formatting
- **ruff**: Fast Python linter
- **mypy**: Static type checking

## Configuration Management

### Environment Variables
All sensitive configuration loaded from environment variables using `pydantic-settings`.

### Settings Hierarchy
1. Environment variables
2. `.env` file
3. Default values in `settings.py`

## Database Migrations

Using Alembic for schema migrations:
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Code Style Guidelines

### 1. Naming Conventions
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### 2. Type Hints
All functions must have type hints:
```python
async def fetch_topics(repo_id: int) -> list[Topic]:
    ...
```

### 3. Docstrings
Google-style docstrings:
```python
async def calculate_score(answers: list[Answer]) -> float:
    """Calculate the overall score for a quiz session.
    
    Args:
        answers: List of user answers with evaluation results.
        
    Returns:
        Float between 0.0 and 1.0 representing the score.
        
    Raises:
        ValueError: If answers list is empty.
    """
    ...
```

### 4. Async/Await
- All I/O operations must be async
- Use `asyncio.gather()` for concurrent operations
- Prefer `async with` for context managers

## Testing Guidelines

### 1. Test Structure
```python
# tests/unit/test_services/test_study_manager.py
import pytest
from study_agent.application.services.study_manager import StudyManager

class TestStudyManager:
    @pytest.mark.asyncio
    async def test_create_study_session(
        self, 
        study_manager: StudyManager,
        mock_user: User,
        mock_topic: Topic
    ):
        """Test creating a new study session."""
        session = await study_manager.create_study_session(
            mock_user.id, 
            mock_topic.id
        )
        assert session.status == "in_progress"
```

### 2. Fixtures
Define reusable fixtures in `conftest.py`:
```python
# tests/conftest.py
import pytest
from study_agent.domain.models.user import User

@pytest.fixture
def mock_user() -> User:
    return User(
        id=1,
        telegram_id=123456789,
        username="testuser"
    )
```

### 3. Mocking External Services
```python
@pytest.mark.asyncio
async def test_fetch_repository(mocker):
    mock_httpx = mocker.patch("httpx.AsyncClient.get")
    mock_httpx.return_value.status_code = 200
    # ... test implementation
```

## Git Workflow

### Branch Naming
- Feature: `feature/description`
- Bugfix: `bugfix/description`
- Hotfix: `hotfix/description`

### Commit Messages
Follow conventional commits:
- `feat: add quiz generation service`
- `fix: resolve database connection issue`
- `docs: update API documentation`
- `test: add tests for study manager`

## CI/CD Pipeline

### GitHub Actions Workflow
1. Lint code (ruff)
2. Type check (mypy)
3. Run tests (pytest)
4. Check coverage (≥90%)
5. Build package

## Security Best Practices

1. Never commit `.env` files
2. Use environment variables for secrets
3. Sanitize user inputs
4. Implement rate limiting
5. Validate GitHub repository URLs
6. Use parameterized SQL queries (SQLAlchemy handles this)

## Performance Considerations

1. Use connection pooling
2. Implement caching where appropriate
3. Batch database operations
4. Use async operations for I/O
5. Implement pagination for large datasets

## Future Structure Extensions

### WhatsApp Integration
```
src/study_agent/presentation/whatsapp/
├── __init__.py
├── bot.py
└── handlers/
```

### Additional LLM Providers
```
src/study_agent/infrastructure/clients/
├── gemini_client.py
├── openai_client.py
└── anthropic_client.py
```

### Multi-tenancy Support
```
src/study_agent/domain/models/
├── organization.py
└── team.py
```

## Conclusion

This structure provides a clean, maintainable foundation that:
- Separates concerns clearly
- Facilitates testing
- Supports async operations
- Enables easy extension
- Follows Python best practices
