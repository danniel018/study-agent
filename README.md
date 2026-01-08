# Study Agent Chatbot

> An AI-powered study assistant that helps you learn and retain knowledge through scheduled quizzes from your GitHub repositories.

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📚 Overview

Study Agent is an intelligent chatbot that proactively helps users study and review their study topics and notes to reinforce knowledge and improve retention. It integrates with your GitHub repositories containing study materials and generates personalized quizzes using Google's Gemini AI.

### Key Features

- 🤖 **Telegram Bot Interface**: Easy-to-use chat interface for studying on the go
- 📖 **GitHub Integration**: Automatically syncs study materials from your repositories
- 🧠 **AI-Powered Quizzes**: Gemini generates contextual questions from your notes
- 📅 **Spaced Repetition**: Smart scheduling algorithm for optimal knowledge retention
- 📊 **Performance Tracking**: Track your progress and identify areas for improvement
- ⚡ **Async Architecture**: Fast, responsive, and scalable design
- 🧪 **Comprehensive Testing**: 90% code coverage target with pytest

## 🏗️ Architecture

This project follows clean architecture principles with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│     Presentation Layer (Telegram)       │
├─────────────────────────────────────────┤
│     Application Layer (Services)        │
├─────────────────────────────────────────┤
│     Domain Layer (Business Logic)       │
├─────────────────────────────────────────┤
│  Infrastructure Layer (DB, APIs, etc.)  │
└─────────────────────────────────────────┘
```

## 📋 Current Status

**Status**: 🚀 **MVP Implementation In Progress**

### Implemented Features

✅ **Core Architecture**
- Configuration management with Pydantic settings
- SQLAlchemy database models (7 tables)
- Async database engine with connection pooling
- Clean architecture with separation of concerns

✅ **Infrastructure Layer**
- Gemini 2.0+ client for quiz generation and answer evaluation
- GitHub API client for repository content fetching
- User, Repository, and Topic repositories with CRUD operations

✅ **Application Layer**
- GitHub service for repository syncing
- Study manager with spaced repetition algorithm
- Quiz generation and answer evaluation
- Performance metrics tracking

✅ **Presentation Layer**
- Telegram bot with aiogram 3.x
- Command handlers: `/start`, `/help`, `/testquiz`
- User registration with default schedule configuration

✅ **Testing**
- Unit tests for utilities and repositories
- Test fixtures and configuration
- Async test support with pytest-asyncio

### In Progress

🚧 Additional command handlers (addrepo, study, stats, schedule)
🚧 Quiz conversation flow with FSM states
🚧 Scheduler service with 5-minute test mode
🚧 Integration tests
🚧 Test coverage improvement to 90%

### Coming Soon

📅 Private repository support with GitHub PAT
📅 Advanced statistics and progress visualization
📅 Goal setting and achievements
📅 WhatsApp integration (see [WHATSAPP_INTEGRATION.md](WHATSAPP_INTEGRATION.md))

### Design Documents

| Document | Description |
|----------|-------------|
| [DESIGN.md](DESIGN.md) | Complete system architecture and technical design |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Detailed project structure and file organization |
| [WHATSAPP_INTEGRATION.md](WHATSAPP_INTEGRATION.md) | Guide for future WhatsApp platform support |
| [QUESTIONS_AND_CLARIFICATIONS.md](QUESTIONS_AND_CLARIFICATIONS.md) | Open questions requiring answers before implementation |

## 🎯 Problem Statement

As per the agentic execution plan, we are following a structured approach:

**Step 1** ✅: Propose initial design and project structure
- Complete system design document created
- Project structure defined
- Architecture patterns selected
- Technology stack confirmed

**Step 2** ⏳: Address questions and undefined processes
- See [QUESTIONS_AND_CLARIFICATIONS.md](QUESTIONS_AND_CLARIFICATIONS.md)
- Critical decisions needed before implementation

## 🛠️ Tech Stack

### Core Technologies
- **Python 3.14**: Latest Python with enhanced performance
- **aiogram 3.x**: Modern Telegram Bot framework with async support
- **SQLAlchemy 2.x**: Powerful ORM with async support
- **SQLite/aiosqlite**: Lightweight database (PostgreSQL for scale)
- **httpx**: Modern async HTTP client
- **Google Gemini**: AI model for quiz generation and evaluation

### Development Tools
- **pytest**: Testing framework with async support
- **black**: Code formatting
- **ruff**: Fast Python linter
- **mypy**: Static type checking
- **alembic**: Database migrations

## 📖 Documentation

### For Developers

- **[DESIGN.md](DESIGN.md)**: In-depth system architecture, database schema, service layer design, and design patterns
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**: Complete project file structure, module responsibilities, and coding guidelines
- **[QUESTIONS_AND_CLARIFICATIONS.md](QUESTIONS_AND_CLARIFICATIONS.md)**: Open questions and decision points

### For Future Enhancements

- **[WHATSAPP_INTEGRATION.md](WHATSAPP_INTEGRATION.md)**: Step-by-step guide for adding WhatsApp support using Twilio API

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Telegram account
- Google AI Studio account (for Gemini API key)

### Installation

```bash
# Clone the repository
git clone https://github.com/danniel018/study-agent.git
cd study-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys:
# - TELEGRAM_BOT_TOKEN (from @BotFather on Telegram)
# - GEMINI_API_KEY (from Google AI Studio)
```

### Initialize & Run

```bash
# Initialize database
python scripts/init_db.py

# Start the bot
python -m study_agent
```

### Test the Bot

1. Open Telegram
2. Search for your bot
3. Send `/start` to begin
4. Use `/testquiz` for a quick test with mock questions

📚 **For detailed setup instructions, see [DEVELOPMENT.md](DEVELOPMENT.md)**

## 📚 How It Works

1. **Setup**: User adds GitHub repository URLs containing study materials (markdown files)
2. **Sync**: Bot fetches and parses all content from repositories
3. **Schedule**: User configures preferred study schedule (default: daily at 9 AM)
4. **Quiz**: Bot generates personalized quizzes using Gemini AI
5. **Assess**: User answers questions, receives immediate feedback with scores
6. **Track**: System tracks performance and schedules future reviews using spaced repetition
7. **Improve**: Over time, the system optimizes review intervals based on retention patterns

### Spaced Repetition Algorithm

The bot uses a simple but effective spaced repetition algorithm:

- **Excellent performance (≥80%)**: Next review in 2.5× previous interval
- **Good performance (60-80%)**: Next review in 1.5× previous interval  
- **Needs work (<60%)**: Reset to daily review

Example progression: Day 1 → Day 2 → Day 4 → Day 9 → Day 21 → Day 51...

## 🎨 Design Principles

### Clean Architecture
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Separation of Concerns**: Each layer has a single, well-defined responsibility
- **Testability**: All components are independently testable with clear interfaces

### Async First
- All I/O operations are async
- Concurrent operations where beneficial
- Efficient resource utilization

### Type Safety
- Type hints throughout the codebase
- MyPy static type checking
- Runtime validation with Pydantic

### Code Quality
- Black for consistent formatting
- Ruff for fast linting
- 90% test coverage target
- Comprehensive docstrings

## 🔧 Configuration Options (Planned)

Users will be able to configure:
- Study schedule (daily, weekly, custom)
- Questions per session (3-10)
- Preferred study time
- Notification preferences
- Difficulty level
- Repository inclusion/exclusion

## 📊 Database Schema (Designed)

Key entities:
- **Users**: Telegram user information and preferences
- **Repositories**: GitHub repositories containing study materials
- **Topics**: Parsed study topics from repositories
- **Study Sessions**: Individual study session records
- **Assessments**: Quiz questions and answers
- **Performance Metrics**: Historical performance data for spaced repetition

See [DESIGN.md](DESIGN.md#1-database-schema) for complete schema.

## 🧪 Testing Strategy

### Coverage Targets
- Unit Tests: 70%
- Integration Tests: 15%
- E2E Tests: 5%
- **Overall: 90%**

### Test Structure
```
tests/
├── unit/              # Fast, isolated tests
├── integration/       # Service integration tests
├── e2e/              # Complete workflow tests
└── fixtures/         # Test data and mocks
```

## 🔐 Security Considerations

- API keys stored in environment variables
- Parameterized queries (SQL injection protection)
- Rate limiting on external API calls
- Input validation and sanitization
- GitHub repository URL validation
- Secure token storage

## 📈 Scalability Path

### Current Design (MVP)
- SQLite database
- Single bot instance
- Suitable for <1000 users

### Future Scaling
- PostgreSQL for concurrent access
- Redis for caching
- Multiple bot instances
- Message queue for background tasks
- Docker/Kubernetes deployment

## 🤝 Contributing (Future)

Contributions are welcome! This project follows:
- Conventional Commits
- Feature branch workflow
- Code review requirements
- Test coverage requirements

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **aiogram**: Excellent Telegram bot framework
- **Google Gemini**: Powerful AI for quiz generation
- **SQLAlchemy**: Robust ORM with great async support

## 📞 Support

- Create an issue for bugs or feature requests
- Check documentation in `/docs` directory
- Review design documents for architecture questions

## 🗺️ Roadmap

### Phase 1: MVP (Current)
- [ ] Finalize design decisions (Step 2)
- [ ] Implement core architecture
- [ ] Basic Telegram bot commands
- [ ] GitHub repository integration
- [ ] Quiz generation with Gemini
- [ ] Simple scheduling
- [ ] Performance tracking

### Phase 2: Enhancements
- [ ] Advanced spaced repetition (SM-2)
- [ ] Private repository support
- [ ] Multiple quiz formats
- [ ] Rich statistics and analytics
- [ ] Export functionality

### Phase 3: Platform Expansion
- [ ] WhatsApp integration
- [ ] Web dashboard
- [ ] Mobile app
- [ ] Team study features
- [ ] Community topic sharing

---

## 🎯 Next Steps

**For Project Owner**:
1. Review [QUESTIONS_AND_CLARIFICATIONS.md](QUESTIONS_AND_CLARIFICATIONS.md)
2. Provide answers to critical questions (1-6)
3. Approve design or suggest modifications
4. Authorize implementation to begin

**For Implementation** (Pending approval):
1. Set up project structure
2. Implement database layer
3. Create service layer
4. Build Telegram bot handlers
5. Integrate with GitHub and Gemini APIs
6. Write comprehensive tests
7. Deploy and iterate

---

**Built with ❤️ for effective learning and knowledge retention**
