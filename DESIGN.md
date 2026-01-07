# Study Agent Chatbot - System Design Document

## Executive Summary

This document outlines the architectural design for a Study Agent Chatbot - an AI-powered system that proactively helps users study and review topics from their GitHub repositories through scheduled quizzes via Telegram.

## System Overview

### Core Purpose
Build a maintainable, scalable, and testable AI agent that:
- Periodically reviews user study topics from GitHub repositories
- Assesses users through quiz-style interactions
- Tracks performance history to optimize future assessments
- Reinforces knowledge and improves retention

### Tech Stack
- **Language**: Python 3.14
- **Bot Framework**: Aiogram (Telegram)
- **HTTP Client**: HTTPX (async)
- **Database**: SQLite with SQLAlchemy ORM
- **LLM**: Google Gemini
- **Async Runtime**: asyncio
- **Testing**: Pytest (90% coverage target)

## Architectural Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT INTERFACE                    │
│                         (Aiogram)                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Bot        │  │  Scheduler   │  │  Assessment  │      │
│  │   Handlers   │  │  Service     │  │  Service     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   GitHub     │  │     LLM      │  │   Study      │      │
│  │   Service    │  │   Service    │  │   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Database    │  │   GitHub     │  │   Gemini     │      │
│  │  Repository  │  │   Client     │  │   Client     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. **Telegram Bot Interface Layer**
- Handle incoming messages and commands
- Manage conversation flows
- Format and send responses
- Handle user interactions during quizzes

#### 2. **Application Layer**
- **Bot Handlers**: Command handlers, message handlers, callback handlers
- **Scheduler Service**: APScheduler for periodic assessments
- **Assessment Service**: Orchestrate quiz sessions and scoring

#### 3. **Domain Layer**
- **GitHub Service**: Fetch and parse study materials from repositories
- **LLM Service**: Generate quizzes and evaluate answers using Gemini
- **Study Manager**: Business logic for study sessions and progress tracking

#### 4. **Infrastructure Layer**
- **Database Repository**: SQLAlchemy models and data access
- **GitHub Client**: HTTPX-based async GitHub API client
- **Gemini Client**: Async wrapper for Google Gemini API

## Component Design

### 1. Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    timezone TEXT DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Repositories Table
```sql
CREATE TABLE repositories (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    repo_url TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, repo_owner, repo_name)
);
```

#### Topics Table
```sql
CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    repository_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repository_id) REFERENCES repositories(id)
);
```

#### Study Sessions Table
```sql
CREATE TABLE study_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    session_type TEXT NOT NULL, -- 'scheduled', 'manual'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'in_progress', -- 'in_progress', 'completed', 'cancelled'
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);
```

#### Assessments Table
```sql
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    user_answer TEXT,
    correct_answer TEXT,
    is_correct BOOLEAN,
    llm_feedback TEXT,
    score FLOAT, -- 0.0 to 1.0
    answered_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions(id)
);
```

#### Performance Metrics Table
```sql
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    average_score FLOAT DEFAULT 0.0,
    last_studied_at TIMESTAMP,
    next_review_at TIMESTAMP,
    retention_score FLOAT, -- Calculated spaced repetition score
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    UNIQUE(user_id, topic_id)
);
```

#### Schedule Config Table
```sql
CREATE TABLE schedule_config (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    frequency TEXT DEFAULT 'daily', -- 'daily', 'weekly', 'custom'
    preferred_time TEXT, -- HH:MM format
    days_of_week TEXT, -- JSON array for weekly: [1,3,5]
    questions_per_session INTEGER DEFAULT 5,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id)
);
```

### 2. Core Services

#### GitHub Service
```python
class GitHubService:
    """Handles fetching and parsing study materials from GitHub repositories."""
    
    async def fetch_repository_topics(self, repo_url: str) -> List[Topic]:
        """Fetch all markdown files from a repository that contain study topics."""
        
    async def parse_topic_content(self, content: str) -> ParsedTopic:
        """Parse markdown content to extract topics and notes."""
        
    async def sync_repository(self, repo_id: int) -> None:
        """Sync repository content with local database."""
```

#### LLM Service (Gemini)
```python
class LLMService:
    """Handles all LLM interactions using Google Gemini."""
    
    async def generate_quiz_questions(
        self, 
        topic_content: str, 
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> List[Question]:
        """Generate quiz questions based on topic content."""
        
    async def evaluate_answer(
        self, 
        question: str, 
        user_answer: str, 
        context: str
    ) -> EvaluationResult:
        """Evaluate user's answer and provide feedback."""
        
    async def generate_study_summary(
        self, 
        session: StudySession
    ) -> str:
        """Generate a summary of the study session."""
```

#### Study Manager
```python
class StudyManager:
    """Orchestrates study sessions and assessment logic."""
    
    async def create_study_session(
        self, 
        user_id: int, 
        topic_id: int,
        session_type: str = "scheduled"
    ) -> StudySession:
        """Create a new study session."""
        
    async def conduct_assessment(self, session_id: int) -> None:
        """Conduct quiz assessment for a study session."""
        
    async def calculate_next_review(
        self, 
        user_id: int, 
        topic_id: int
    ) -> datetime:
        """Calculate next review time using spaced repetition."""
        
    async def get_topics_for_review(self, user_id: int) -> List[Topic]:
        """Get topics that are due for review."""
```

#### Scheduler Service
```python
class SchedulerService:
    """Manages scheduled assessments using APScheduler."""
    
    async def schedule_user_assessments(self, user_id: int) -> None:
        """Schedule periodic assessments for a user."""
        
    async def trigger_scheduled_assessment(self, user_id: int) -> None:
        """Trigger a scheduled assessment."""
        
    async def update_schedule(self, user_id: int, config: ScheduleConfig) -> None:
        """Update user's assessment schedule."""
```

### 3. Telegram Bot Handlers

#### Command Handlers
- `/start` - Initialize bot and register user
- `/help` - Show help message with available commands
- `/addrepo <repo_url>` - Add a GitHub repository
- `/listprepos` - List all registered repositories
- `/removerepo <repo_id>` - Remove a repository
- `/topics` - List all available topics
- `/study [topic_id]` - Start a manual study session
- `/schedule` - Configure assessment schedule
- `/stats` - View performance statistics
- `/settings` - Manage user settings

#### Conversation Flows
1. **Repository Setup Flow**
   - Prompt for repository URL
   - Validate repository access
   - Sync repository content
   - Confirm topics found

2. **Quiz Flow**
   - Present question
   - Wait for user answer
   - Evaluate answer
   - Provide feedback
   - Move to next question
   - Show session summary

3. **Schedule Configuration Flow**
   - Ask for frequency preference
   - Ask for preferred time
   - Ask for questions per session
   - Confirm configuration

## Design Patterns & Principles

### 1. Dependency Injection
- Use Protocol classes for interface definitions
- Constructor injection for dependencies
- Facilitate testing with mock implementations

### 2. Repository Pattern
- Abstract database operations
- Single source of truth for data access
- Enable easy database migration

### 3. Service Layer Pattern
- Business logic in service classes
- Keep handlers thin (presentation layer)
- Services are async and independently testable

### 4. Strategy Pattern
- Different scheduling strategies (daily, weekly, custom)
- Different assessment difficulty levels
- Pluggable LLM providers

### 5. Factory Pattern
- Create appropriate parsers for different file types
- Create quiz questions based on difficulty

## Async Patterns

### 1. Concurrent Operations
```python
# Fetch multiple repositories concurrently
async def sync_all_repositories(user_id: int):
    repos = await repo_repository.get_user_repos(user_id)
    tasks = [github_service.sync_repository(repo.id) for repo in repos]
    await asyncio.gather(*tasks)
```

### 2. Connection Pooling
```python
# Use async connection pools for database and HTTP clients
db_engine = create_async_engine(
    database_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=10,
    max_overflow=20
)
```

### 3. Rate Limiting
```python
# Implement rate limiting for GitHub and Gemini API calls
class RateLimiter:
    async def acquire(self):
        """Wait if rate limit reached."""
```

## Error Handling Strategy

### 1. Custom Exceptions
```python
class StudyAgentException(Exception):
    """Base exception for all application errors."""

class RepositoryNotFoundError(StudyAgentException):
    """Raised when GitHub repository is not found."""

class LLMServiceError(StudyAgentException):
    """Raised when LLM service fails."""
```

### 2. Error Recovery
- Retry failed API calls with exponential backoff
- Graceful degradation (e.g., use cached content if GitHub unavailable)
- User-friendly error messages in bot responses

### 3. Logging
- Structured logging with context
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Separate log files for bot, services, and database

## Testing Strategy

### 1. Unit Tests (70% coverage target)
- Test individual service methods
- Mock external dependencies (GitHub API, Gemini API)
- Test database repositories with in-memory SQLite

### 2. Integration Tests (15% coverage target)
- Test service integration
- Test database operations with real SQLite
- Test bot handlers with simulated messages

### 3. End-to-End Tests (5% coverage target)
- Test complete workflows
- Use test Telegram bot
- Mock external APIs

### 4. Test Structure
```
tests/
├── unit/
│   ├── services/
│   ├── repositories/
│   └── handlers/
├── integration/
│   ├── test_study_flow.py
│   └── test_schedule_flow.py
└── e2e/
    └── test_complete_workflow.py
```

## Security Considerations

### 1. API Keys
- Store in environment variables
- Never commit to version control
- Use `.env` files locally

### 2. Database Security
- Parameterized queries (SQLAlchemy protects against SQL injection)
- Encrypt sensitive data at rest (if needed)
- Regular backups

### 3. GitHub Access
- Support only public repositories initially
- Add PAT support for private repos (future)
- Validate repository URLs

### 4. Rate Limiting
- Limit requests per user
- Prevent abuse of bot commands

## Scalability Considerations

### 1. Current Design (MVP)
- SQLite database (single instance)
- Single bot instance
- Suitable for < 1000 users

### 2. Future Scaling Path
- PostgreSQL for concurrent access
- Redis for caching and rate limiting
- Multiple bot instances with webhook mode
- Background workers for long-running tasks
- Message queue (RabbitMQ/Redis) for task distribution

## Deployment Strategy

### 1. Environment Setup
```bash
# .env file
TELEGRAM_BOT_TOKEN=your_token_here
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=sqlite+aiosqlite:///./study_agent.db
LOG_LEVEL=INFO
```

### 2. Docker Support (Future)
```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "study_agent"]
```

### 3. Continuous Integration
- GitHub Actions for testing
- Automated test runs on PR
- Coverage reporting

## Monitoring & Observability

### 1. Metrics to Track
- Active users
- Study sessions per day
- Average quiz scores
- API response times
- Error rates

### 2. Logging
- Application logs
- Access logs
- Error logs with stack traces

### 3. Health Checks
- Bot connectivity
- Database connectivity
- External API availability

## Future Enhancements

### 1. Phase 1 (MVP) - Current Design
- Basic Telegram bot
- GitHub repository integration
- Quiz generation and evaluation
- Basic scheduling
- Performance tracking

### 2. Phase 2
- Advanced spaced repetition algorithm
- Multiple quiz formats (MCQ, fill-in-blank)
- Topic recommendations
- Study streak tracking
- Peer comparison (opt-in)

### 3. Phase 3
- WhatsApp integration (see WHATSAPP_INTEGRATION.md)
- Private repository support
- Team/group study features
- Export study history
- Integration with other platforms (Notion, Obsidian)

## Conclusion

This design provides a solid foundation for a maintainable, testable, and scalable study agent chatbot. The architecture follows clean code principles, leverages async patterns throughout, and provides clear separation of concerns that facilitates testing and future enhancements.
