# Development Guide - Study Agent

## Prerequisites

- Python 3.11 or higher
- Git
- A Telegram account
- A Google AI Studio account (for Gemini API)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/danniel018/study-agent.git
cd study-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .
```

### 4. Get API Keys

#### Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

#### Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the API key

### 5. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Gemini API Configuration  
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./study_agent.db

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development

# Scheduler Settings
ENABLE_SCHEDULER=true
SCHEDULER_TIMEZONE=UTC
DEFAULT_STUDY_TIME=09:00

# Rate Limiting
GITHUB_RATE_LIMIT=60
GEMINI_RATE_LIMIT=60
```

### 6. Initialize Database

```bash
python scripts/init_db.py
```

This will create the SQLite database and all necessary tables.

### 7. Run the Bot

```bash
python -m study_agent
```

You should see output like:
```
INFO - Starting Study Agent...
INFO - Initializing database...
INFO - Starting Telegram bot...
```

### 8. Test the Bot

1. Open Telegram
2. Search for your bot using the username you created
3. Send `/start` command
4. You should see a welcome message!

## Available Commands

Once the bot is running, you can use these commands in Telegram:

- `/start` - Initialize the bot and register your account
- `/help` - Show all available commands
- `/testquiz` - Quick test with mock questions (no repository needed)
- `/addrepo` - Add a GitHub repository (coming soon)
- `/listrepos` - List your repositories (coming soon)
- `/study` - Start a manual study session (coming soon)
- `/topics` - View all available topics (coming soon)
- `/stats` - View your performance statistics (coming soon)
- `/schedule` - Configure study schedule (coming soon)

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Tests

```bash
# Run only utility tests
pytest tests/unit/test_utils/

# Run only repository tests
pytest tests/unit/test_repositories/

# Run with coverage report
pytest --cov=src/study_agent --cov-report=html
```

### View Coverage Report

After running tests with coverage, open `htmlcov/index.html` in your browser.

## Development Workflow

### Code Formatting

Format code with Black:

```bash
black src/ tests/
```

### Linting

Lint code with Ruff:

```bash
ruff check src/ tests/
```

### Type Checking

Check types with MyPy:

```bash
mypy src/
```

## Project Structure

```
study-agent/
├── src/study_agent/          # Main application code
│   ├── config/               # Configuration
│   ├── domain/               # Domain models
│   ├── infrastructure/       # Database, clients
│   ├── application/          # Business logic services
│   ├── presentation/         # Telegram bot interface
│   └── core/                 # Core utilities
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── conftest.py          # Test fixtures
├── scripts/                  # Utility scripts
└── docs/                     # Documentation
```

## Key Features Implemented

### ✅ Phase 1 (MVP) - Completed

- [x] Configuration management with environment variables
- [x] Database models for users, repositories, topics, sessions, assessments
- [x] User repository with automatic schedule config creation
- [x] Gemini LLM client for quiz generation and evaluation
- [x] GitHub client for repository content fetching
- [x] Study manager with spaced repetition algorithm
- [x] Basic Telegram bot with command handlers
- [x] Test infrastructure with pytest

### 🚧 Phase 1 (MVP) - In Progress

- [ ] Complete Telegram command handlers (addrepo, study, stats, schedule)
- [ ] Quiz conversation flow with FSM states
- [ ] Scheduler service with 5-minute test mode
- [ ] Integration tests
- [ ] 90% test coverage

### 📅 Phase 2 (Future)

- [ ] Advanced spaced repetition (SM-2 algorithm)
- [ ] Private repository support with GitHub PAT
- [ ] Multiple quiz formats (MCQ, True/False, Fill-in-blank)
- [ ] Rich statistics and visualizations
- [ ] Export/import functionality

### 🌟 Phase 3 (Future)

- [ ] WhatsApp integration
- [ ] Web dashboard
- [ ] Team/group study features
- [ ] Community topic sharing

## Troubleshooting

### Bot doesn't respond

1. Check that the bot is running (look for "Starting Telegram bot..." log)
2. Verify your Telegram bot token in `.env`
3. Make sure you're messaging the correct bot
4. Check the logs for errors

### Database errors

1. Delete the database file: `rm study_agent.db`
2. Reinitialize: `python scripts/init_db.py`
3. Restart the bot

### Gemini API errors

1. Verify your API key in `.env`
2. Check your API quota at [Google AI Studio](https://makersuite.google.com/)
3. Make sure you're using Gemini 2.0 or higher (gemini-2.0-flash-exp)

### GitHub API errors

1. Check if the repository is public
2. Verify the repository URL format
3. Check rate limits (60 requests/hour for unauthenticated)

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Write tests for new functionality
4. Run tests and ensure they pass
5. Format code with Black
6. Submit a pull request

## Support

For issues and questions:
- Check the [DESIGN.md](DESIGN.md) for architecture details
- Review [QUESTIONS_AND_CLARIFICATIONS.md](QUESTIONS_AND_CLARIFICATIONS.md)
- Open an issue on GitHub

## License

MIT License - see LICENSE file for details
