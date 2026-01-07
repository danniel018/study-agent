# Study Agent - Design Summary

## 🎯 Executive Summary

This document provides a high-level summary of the Study Agent Chatbot design. For detailed information, refer to the individual documentation files.

---

## 📊 System Architecture Overview

### Three-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                               │
│                  (Telegram Bot - aiogram)                        │
│                                                                  │
│  Commands: /start, /addrepo, /study, /stats, /schedule          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                              │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   GitHub    │  │     LLM      │  │    Study     │          │
│  │   Service   │  │   Service    │  │   Manager    │          │
│  └─────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐                             │
│  │ Assessment  │  │  Scheduler   │                             │
│  │  Service    │  │   Service    │                             │
│  └─────────────┘  └──────────────┘                             │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                             │
│                                                                  │
│  ┌─────────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   SQLite Database   │  │ GitHub API   │  │  Gemini API  │  │
│  │   (SQLAlchemy)      │  │  (httpx)     │  │  (httpx)     │  │
│  └─────────────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 User Journey

### 1️⃣ Onboarding Flow
```
User → /start
       ↓
Bot: Welcome! Set timezone?
       ↓
User: UTC-5
       ↓
Bot: Preferred study time?
       ↓
User: 9:00 AM
       ↓
Bot: Add GitHub repository URL
       ↓
User: https://github.com/user/study-notes
       ↓
Bot: Syncing... Found 12 topics!
       ↓
Bot: Configure schedule?
       ↓
User: Daily at 9 AM
       ↓
Bot: ✅ Setup complete!
```

### 2️⃣ Study Session Flow
```
Bot → (Scheduled) Time to study! 📚
      ↓
Bot: Topic: Python Data Structures
     Question 1/5: What is a list comprehension?
      ↓
User: A concise way to create lists...
      ↓
Bot: ✅ Correct! Score: 0.95
     (Shows explanation)
      ↓
Bot: Question 2/5: ...
      ↓
... (continue for all questions) ...
      ↓
Bot: Session complete! 
     Score: 4.5/5 (90%)
     Next review: Jan 10, 2026
```

### 3️⃣ Progress Tracking
```
User → /stats
       ↓
Bot: 📊 Your Statistics
     
     Overall Score: 85%
     Topics Mastered: 8
     In Progress: 4
     Study Streak: 7 days 🔥
     
     Top Topics:
     1. Python Basics - 95%
     2. Data Structures - 90%
     3. Algorithms - 80%
```

---

## 🗄️ Database Schema (Simplified)

```
┌─────────────┐         ┌──────────────┐
│    Users    │────────▶│ Repositories │
└─────────────┘         └──────────────┘
      │                        │
      │                        ▼
      │                 ┌─────────────┐
      │                 │   Topics    │
      │                 └─────────────┘
      │                        │
      ▼                        │
┌──────────────┐               │
│ Performance  │◀──────────────┘
│   Metrics    │
└──────────────┘
      ▲
      │
      ▼
┌──────────────┐         ┌──────────────┐
│    Study     │────────▶│ Assessments  │
│   Sessions   │         └──────────────┘
└──────────────┘
```

**Key Tables**:
- **Users**: Store user profiles and preferences
- **Repositories**: GitHub repos containing study materials
- **Topics**: Individual study topics from repos
- **Study Sessions**: Records of study sessions
- **Assessments**: Quiz questions and user answers
- **Performance Metrics**: Historical performance for spaced repetition

---

## 🧠 Core Services

### 1. GitHub Service
**Responsibility**: Fetch and parse study materials
```python
async def fetch_repository_topics(repo_url: str) -> List[Topic]
async def sync_repository(repo_id: int) -> None
```

### 2. LLM Service (Gemini)
**Responsibility**: Generate quizzes and evaluate answers
```python
async def generate_quiz_questions(topic: str, num: int) -> List[Question]
async def evaluate_answer(question: str, answer: str) -> Score
```

### 3. Study Manager
**Responsibility**: Orchestrate study sessions
```python
async def create_study_session(user_id: int, topic_id: int) -> Session
async def conduct_assessment(session_id: int) -> None
```

### 4. Scheduler Service
**Responsibility**: Manage scheduled assessments
```python
async def schedule_user_assessments(user_id: int) -> None
async def trigger_scheduled_assessment(user_id: int) -> None
```

---

## 🔁 Spaced Repetition Algorithm (Simple Version for MVP)

```python
def calculate_next_review_interval(score: float, last_interval: int) -> int:
    """
    Simple spaced repetition algorithm.
    
    Args:
        score: Quiz score from 0.0 to 1.0
        last_interval: Previous interval in days
        
    Returns:
        Next interval in days
    """
    if score >= 0.8:      # Excellent (80%+)
        return last_interval * 2.5  # e.g., 1 → 2 → 5 → 12 → 30 days
    elif score >= 0.6:    # Good (60-80%)
        return last_interval * 1.5  # e.g., 1 → 1 → 2 → 3 → 4 days
    else:                 # Needs work (<60%)
        return 1                    # Reset to daily review
```

**Example progression for a well-learned topic**:
- Day 1: Initial study
- Day 2: First review (1 day later)
- Day 4: Second review (2 days later)
- Day 9: Third review (5 days later)
- Day 21: Fourth review (12 days later)
- Day 51: Fifth review (30 days later)

---

## 🎯 Key Features

### ✅ MVP Features
1. **GitHub Integration**: Sync markdown files as study topics
2. **AI Quiz Generation**: Gemini generates contextual questions
3. **Scheduled Assessments**: Daily/weekly quizzes
4. **Performance Tracking**: Historical scores and trends
5. **Spaced Repetition**: Intelligent review scheduling
6. **Telegram Interface**: Full-featured bot commands

### 🚀 Phase 2 Features
1. Advanced spaced repetition (SM-2 algorithm)
2. Private repository support (with GitHub PAT)
3. Multiple quiz formats (MCQ, True/False, Fill-blank)
4. Rich statistics and visualizations
5. Goal setting and achievements
6. Export/import functionality

### 🌟 Phase 3 Features
1. WhatsApp integration
2. Web dashboard
3. Team/group study features
4. Community topic sharing
5. Integration with note apps (Notion, Obsidian)
6. Voice interaction

---

## 🛠️ Technology Stack

### Core
| Component | Technology | Why |
|-----------|------------|-----|
| Language | Python 3.14 | Latest features, async support |
| Bot Framework | aiogram 3.x | Modern, async Telegram framework |
| Database | SQLite + SQLAlchemy | Simple, portable, upgradable |
| HTTP Client | httpx | Async HTTP for GitHub/Gemini |
| LLM | Google Gemini | Powerful, cost-effective |
| Scheduler | APScheduler | Flexible job scheduling |

### Development
| Tool | Purpose |
|------|---------|
| pytest | Testing with async support |
| black | Code formatting |
| ruff | Fast linting |
| mypy | Static type checking |
| alembic | Database migrations |

---

## 📁 Project Structure (Simplified)

```
study-agent/
├── src/study_agent/
│   ├── config/              # Configuration
│   ├── domain/              # Business entities
│   ├── infrastructure/      # DB, APIs, clients
│   ├── application/         # Services, use cases
│   ├── presentation/        # Telegram bot
│   └── scheduler/           # Background jobs
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
├── docs/                   # Documentation
└── scripts/               # Utility scripts
```

---

## 🔐 Security & Privacy

### API Keys Management
- Environment variables (`.env`)
- Never committed to version control
- Secure key rotation

### Data Protection
- Parameterized SQL queries
- Input validation and sanitization
- Rate limiting
- GitHub URL validation

### User Privacy
- Minimal data collection
- Data export capability
- Account deletion support
- GDPR compliance ready

---

## 📈 Scalability Strategy

### Current (MVP): Single Instance
- SQLite database
- Single bot instance
- Long polling
- Suitable for: **< 1,000 users**

### Phase 2: Small Scale
- PostgreSQL database
- Redis caching
- Webhook mode
- Suitable for: **1,000 - 10,000 users**

### Phase 3: Production Scale
- Multi-instance deployment
- Load balancer
- Message queue (RabbitMQ/Redis)
- Background workers
- Suitable for: **10,000+ users**

---

## 🧪 Testing Strategy

### Coverage Goals
- **Overall Target**: 90%
- Unit Tests: 70%
- Integration Tests: 15%
- E2E Tests: 5%

### Test Types
```python
# Unit Test Example
@pytest.mark.asyncio
async def test_calculate_next_review():
    interval = calculate_next_review(score=0.9, last_interval=1)
    assert interval == 2

# Integration Test Example  
@pytest.mark.asyncio
async def test_complete_study_session():
    session = await study_manager.create_session(user_id=1, topic_id=1)
    await study_manager.conduct_assessment(session.id)
    assert session.status == "completed"

# E2E Test Example
@pytest.mark.asyncio
async def test_full_user_journey():
    # Send /start command
    # Add repository
    # Complete quiz
    # Check stats
    pass
```

---

## 🤔 Critical Questions (Need Answers)

Before implementation begins, we need answers to:

1. **Repository Structure**: How to identify study topics? (H1, H2, or config file?)
2. **Question Types**: Multiple choice, open-ended, or both?
3. **Scheduling**: Simple or advanced spaced repetition for MVP?
4. **Multi-Repository**: Support multiple repos from start?
5. **Deployment**: Self-hosted, cloud, or PaaS?
6. **Private Repos**: Required for MVP or Phase 2?

**See [QUESTIONS_AND_CLARIFICATIONS.md](QUESTIONS_AND_CLARIFICATIONS.md) for full list**.

---

## 📋 Implementation Checklist

### Prerequisites
- [x] Design architecture
- [x] Define database schema
- [x] Document project structure
- [x] Identify questions/clarifications
- [ ] Get answers to critical questions
- [ ] Finalize technical decisions

### Phase 1: Foundation
- [ ] Set up project structure
- [ ] Configure development environment
- [ ] Set up CI/CD pipeline
- [ ] Create database models
- [ ] Implement repositories

### Phase 2: Core Services
- [ ] GitHub service implementation
- [ ] LLM service implementation
- [ ] Study manager implementation
- [ ] Scheduler service implementation

### Phase 3: Bot Interface
- [ ] Basic command handlers
- [ ] Conversation flows (FSM)
- [ ] Quiz interface
- [ ] Statistics display

### Phase 4: Testing & Quality
- [ ] Unit tests (70% coverage)
- [ ] Integration tests (15% coverage)
- [ ] E2E tests (5% coverage)
- [ ] Code review and refactoring

### Phase 5: Deployment
- [ ] Documentation finalization
- [ ] Deployment scripts
- [ ] Monitoring setup
- [ ] Beta testing

---

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and getting started |
| [DESIGN.md](DESIGN.md) | Comprehensive system design |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | File structure and coding guidelines |
| [QUESTIONS_AND_CLARIFICATIONS.md](QUESTIONS_AND_CLARIFICATIONS.md) | Open questions and decisions |
| [WHATSAPP_INTEGRATION.md](WHATSAPP_INTEGRATION.md) | WhatsApp platform integration guide |
| [DESIGN_SUMMARY.md](DESIGN_SUMMARY.md) | This document |

---

## 🎯 Success Metrics

### Technical Metrics
- ✅ 90% test coverage
- ✅ Response time < 1 second
- ✅ Quiz generation < 5 seconds
- ✅ Zero SQL injection vulnerabilities
- ✅ No secrets in code

### User Metrics
- 📈 User retention rate
- 📈 Study streak completion
- 📈 Quiz completion rate
- 📈 User satisfaction score
- 📈 Knowledge retention improvement

---

## 🚀 Next Steps

### For Review
1. ✅ Review design documents
2. ✅ Review project structure
3. ⏳ Answer critical questions
4. ⏳ Approve design or suggest changes

### For Implementation (Pending Approval)
1. Set up development environment
2. Initialize project structure
3. Implement database layer
4. Build service layer
5. Create Telegram bot
6. Write tests
7. Deploy and iterate

---

## 💡 Design Philosophy

### Principles
1. **Clean Architecture**: Clear separation of concerns
2. **Async First**: All I/O operations are async
3. **Type Safety**: Type hints everywhere
4. **Test Driven**: High test coverage
5. **Maintainable**: Well-documented, readable code
6. **Scalable**: Easy to extend and scale

### Why This Design?
- ✅ **Maintainable**: Clear structure, easy to navigate
- ✅ **Testable**: Each layer can be tested independently
- ✅ **Extensible**: Easy to add features (WhatsApp, web UI)
- ✅ **Performant**: Async operations, efficient queries
- ✅ **Reliable**: Error handling, retry logic, monitoring
- ✅ **Secure**: Input validation, secure storage, rate limiting

---

**Status**: 🔧 Awaiting approval to begin implementation

**Last Updated**: January 7, 2026
