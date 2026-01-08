"""Command handlers for the Telegram bot."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Dispatcher

from study_agent.infrastructure.database.engine import AsyncSessionLocal
from study_agent.infrastructure.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command.
    
    Args:
        message: Incoming message
    """
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        
        # Check if user exists
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        
        if not user:
            # Create new user
            user = await user_repo.create(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username,
                last_name=message.from_user.last_name,
            )
            logger.info(f"New user created: {user.telegram_id}")
            
            welcome_text = (
                f"👋 Welcome to Study Agent, {user.first_name}!\n\n"
                "I'm here to help you study and retain knowledge through "
                "periodic quizzes from your GitHub repositories.\n\n"
                "<b>Quick Start:</b>\n"
                "1. Add a repository with /addrepo\n"
                "2. I'll automatically schedule study sessions\n"
                "3. Answer quiz questions to reinforce learning\n\n"
                "Use /help to see all available commands."
            )
        else:
            welcome_text = (
                f"👋 Welcome back, {user.first_name}!\n\n"
                "Ready to continue your learning journey?\n\n"
                "Use /help to see all available commands."
            )
    
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command.
    
    Args:
        message: Incoming message
    """
    help_text = (
        "📚 <b>Study Agent Commands</b>\n\n"
        "<b>Getting Started:</b>\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "<b>Repository Management:</b>\n"
        "/addrepo - Add a GitHub repository\n"
        "/listrepos - List your repositories\n"
        "/removerepo - Remove a repository\n\n"
        "<b>Study Sessions:</b>\n"
        "/study - Start a manual study session\n"
        "/topics - View all available topics\n\n"
        "<b>Progress & Settings:</b>\n"
        "/stats - View your performance statistics\n"
        "/schedule - Configure study schedule\n"
        "/settings - Manage settings\n\n"
        "<b>Testing:</b>\n"
        "/testquiz - Quick test with mock questions (5 min schedule)\n\n"
        "💡 <b>Tip:</b> I'll automatically quiz you based on your schedule!"
    )
    await message.answer(help_text)


@router.message(Command("testquiz"))
async def cmd_testquiz(message: Message) -> None:
    """Handle /testquiz command for testing purposes.
    
    Args:
        message: Incoming message
    """
    test_text = (
        "🧪 <b>Test Quiz Mode</b>\n\n"
        "This will generate a quick quiz with mock questions.\n"
        "No repository needed - perfect for testing!\n\n"
        "Generating quiz questions..."
    )
    await message.answer(test_text)
    
    # Mock quiz questions
    mock_questions = [
        {
            "question": "What is the capital of France?",
            "answer": "Paris"
        },
        {
            "question": "What is 2 + 2?",
            "answer": "4"
        },
        {
            "question": "What color is the sky?",
            "answer": "Blue"
        }
    ]
    
    quiz_text = (
        "📝 <b>Quick Test Quiz</b>\n\n"
        f"Question 1/{len(mock_questions)}:\n"
        f"{mock_questions[0]['question']}\n\n"
        "Type your answer below:"
    )
    await message.answer(quiz_text)


def register_handlers(dp: Dispatcher) -> None:
    """Register all command handlers.
    
    Args:
        dp: Dispatcher instance
    """
    dp.include_router(router)
