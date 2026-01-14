"""Command handlers for the Telegram bot."""

import logging

from aiogram import Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import func, select

from study_agent.application.services.github_service import GitHubService
from study_agent.application.services.study_manager import StudyManager
from study_agent.core.exceptions import RepositoryAccessError, RepositoryNotFoundError
from study_agent.core.utils import validate_github_url
from study_agent.infrastructure.clients.gemini_client import GeminiClient
from study_agent.infrastructure.clients.github_client import GitHubClient
from study_agent.infrastructure.database.engine import AsyncSessionLocal
from study_agent.infrastructure.database.models import (
    AssessmentModel,
    PerformanceMetricsModel,
    RepositoryModel,
    StudySessionModel,
)
from study_agent.infrastructure.database.repositories.repository_repository import (
    RepositoryRepository,
)
from study_agent.infrastructure.database.repositories.topic_repository import TopicRepository
from study_agent.infrastructure.database.repositories.user_repository import UserRepository
from study_agent.presentation.telegram.states import AddRepoStates, StudyStates

logger = logging.getLogger(__name__)

router = Router()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def get_user_id_from_telegram(telegram_id: int) -> int | None:
    """Get internal user ID from telegram ID.

    Args:
        telegram_id: Telegram user ID

    Returns:
        Internal user ID or None if not found
    """
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        return user.id if user else None


# ============================================================================
# BASIC COMMANDS
# ============================================================================


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


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Handle /cancel command to exit any FSM state.

    Args:
        message: Incoming message
        state: FSM context
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Nothing to cancel. You're not in any active flow.")
        return

    await state.clear()
    await message.answer("✅ Operation cancelled. Use /help to see available commands.")


# ============================================================================
# REPOSITORY MANAGEMENT COMMANDS
# ============================================================================


@router.message(Command("addrepo"))
async def cmd_addrepo(message: Message, state: FSMContext) -> None:
    """Handle /addrepo command - start repository addition flow.

    Args:
        message: Incoming message
        state: FSM context
    """
    # Verify user is registered
    user_id = await get_user_id_from_telegram(message.from_user.id)
    if not user_id:
        await message.answer("⚠️ You need to register first. Please use /start to begin.")
        return

    await state.set_state(AddRepoStates.waiting_for_url)
    await state.update_data(user_id=user_id)

    await message.answer(
        "📦 <b>Add Repository</b>\n\n"
        "Please send me the GitHub repository URL.\n\n"
        "<b>Example:</b>\n"
        "<code>https://github.com/username/repository</code>\n\n"
        "Or send /cancel to abort."
    )


@router.message(AddRepoStates.waiting_for_url)
async def process_repo_url(message: Message, state: FSMContext) -> None:
    """Process the repository URL from user.

    Args:
        message: Incoming message with URL
        state: FSM context
    """
    url = message.text.strip()

    # Validate GitHub URL
    owner, repo_name = validate_github_url(url)

    if not owner or not repo_name:
        await message.answer(
            "❌ Invalid GitHub URL.\n\n"
            "Please provide a valid GitHub repository URL:\n"
            "<code>https://github.com/username/repository</code>\n\n"
            "Or send /cancel to abort."
        )
        return

    # Get user data from state
    data = await state.get_data()
    user_id = data["user_id"]

    # Show processing message
    processing_msg = await message.answer(
        f"⏳ Processing repository <b>{owner}/{repo_name}</b>...\n"
        "This may take a moment while I scan for content."
    )

    try:
        async with AsyncSessionLocal() as session:
            repo_repository = RepositoryRepository(session)
            topic_repository = TopicRepository(session)

            # Check if repo already exists for this user
            existing_repos = await repo_repository.get_by_user(user_id)
            for existing in existing_repos:
                if existing.repo_owner == owner and existing.repo_name == repo_name:
                    await processing_msg.edit_text(
                        f"⚠️ Repository <b>{owner}/{repo_name}</b> is already added.\n\n"
                        "Use /listrepos to see your repositories."
                    )
                    await state.clear()
                    return

            # Create repository record
            repo = await repo_repository.create(
                user_id=user_id,
                repo_url=url,
                repo_owner=owner,
                repo_name=repo_name,
            )

            # Sync content from GitHub
            github_client = GitHubClient()
            github_service = GitHubService(
                github_client=github_client,
                repo_repository=repo_repository,
                topic_repository=topic_repository,
            )

            topics_count = await github_service.sync_repository(repo.id)

            if topics_count == 0:
                await processing_msg.edit_text(
                    f"⚠️ Repository <b>{owner}/{repo_name}</b> was added but "
                    "no valid topics were found.\n\n"
                    "Make sure the repository contains markdown files "
                    "with at least 100 words of content.\n\n"
                    "Use /listrepos to see your repositories."
                )
            else:
                await processing_msg.edit_text(
                    f"✅ Repository <b>{owner}/{repo_name}</b> added successfully!\n\n"
                    f"📚 Found <b>{topics_count}</b> topic(s) for studying.\n\n"
                    "Use /topics to view them or /study to start learning!"
                )

    except RepositoryNotFoundError:
        await processing_msg.edit_text(
            f"❌ Repository <b>{owner}/{repo_name}</b> not found.\n\n"
            "Please make sure:\n"
            "• The repository exists\n"
            "• It's a public repository\n"
            "• The URL is correct\n\n"
            "Try again with /addrepo"
        )
    except RepositoryAccessError as e:
        await processing_msg.edit_text(
            f"❌ Cannot access repository <b>{owner}/{repo_name}</b>.\n\n"
            f"Error: {str(e)}\n\n"
            "Make sure the repository is public and try again."
        )
    except Exception as e:
        logger.error(f"Error adding repository: {str(e)}")
        await processing_msg.edit_text(
            "❌ An error occurred while adding the repository.\n\n"
            "Please try again later or contact support."
        )
    finally:
        await state.clear()


@router.message(Command("listrepos"))
async def cmd_listrepos(message: Message) -> None:
    """Handle /listrepos command - list user's repositories.

    Args:
        message: Incoming message
    """
    user_id = await get_user_id_from_telegram(message.from_user.id)
    if not user_id:
        await message.answer("⚠️ You need to register first. Please use /start to begin.")
        return

    async with AsyncSessionLocal() as session:
        repo_repository = RepositoryRepository(session)
        topic_repository = TopicRepository(session)

        repos = await repo_repository.get_by_user(user_id)

        if not repos:
            await message.answer(
                "📦 <b>Your Repositories</b>\n\n"
                "You haven't added any repositories yet.\n\n"
                "Use /addrepo to add your first GitHub repository!"
            )
            return

        repos_text = "📦 <b>Your Repositories</b>\n\n"
        for i, repo in enumerate(repos, 1):
            topics = await topic_repository.get_by_repository(repo.id)
            sync_status = "✅" if repo.last_synced_at else "⏳"
            sync_info = (
                f"Last sync: {repo.last_synced_at.strftime('%Y-%m-%d %H:%M')}"
                if repo.last_synced_at
                else "Never synced"
            )
            repos_text += (
                f"{i}. {sync_status} <b>{repo.repo_owner}/{repo.repo_name}</b>\n"
                f"   📚 {len(topics)} topic(s) | {sync_info}\n\n"
            )

        repos_text += "Use /removerepo to remove a repository."
        await message.answer(repos_text)


# ============================================================================
# TOPICS COMMAND
# ============================================================================


@router.message(Command("topics"))
async def cmd_topics(message: Message) -> None:
    """Handle /topics command - list all topics.

    Args:
        message: Incoming message
    """
    user_id = await get_user_id_from_telegram(message.from_user.id)
    if not user_id:
        await message.answer("⚠️ You need to register first. Please use /start to begin.")
        return

    async with AsyncSessionLocal() as session:
        topic_repository = TopicRepository(session)
        repo_repository = RepositoryRepository(session)

        topics = await topic_repository.get_by_user(user_id)

        if not topics:
            await message.answer(
                "📚 <b>Your Topics</b>\n\n"
                "No topics found. This could mean:\n"
                "• You haven't added any repositories yet\n"
                "• Your repositories don't have valid markdown content\n\n"
                "Use /addrepo to add a GitHub repository!"
            )
            return

        # Group topics by repository
        repos = await repo_repository.get_by_user(user_id)
        repo_map = {r.id: f"{r.repo_owner}/{r.repo_name}" for r in repos}

        topics_text = "📚 <b>Your Topics</b>\n\n"
        current_repo = None

        for topic in topics:
            repo_name = repo_map.get(topic.repository_id, "Unknown")
            if repo_name != current_repo:
                current_repo = repo_name
                topics_text += f"\n<b>📁 {repo_name}</b>\n"

            # Truncate title if too long
            title = topic.title[:50] + "..." if len(topic.title) > 50 else topic.title
            topics_text += f"  • {title}\n"

        topics_text += f"\n<b>Total:</b> {len(topics)} topic(s)\n"
        topics_text += "\nUse /study to start a quiz!"

        await message.answer(topics_text)


# ============================================================================
# STUDY COMMANDS
# ============================================================================


@router.message(Command("study"))
async def cmd_study(message: Message, state: FSMContext) -> None:
    """Handle /study command - start a study session.

    Args:
        message: Incoming message
        state: FSM context
    """
    user_id = await get_user_id_from_telegram(message.from_user.id)
    if not user_id:
        await message.answer("⚠️ You need to register first. Please use /start to begin.")
        return

    async with AsyncSessionLocal() as session:
        topic_repository = TopicRepository(session)
        topics = await topic_repository.get_by_user(user_id)

        if not topics:
            await message.answer(
                "📚 <b>No Topics Available</b>\n\n"
                "You need to add a repository with content first.\n\n"
                "Use /addrepo to add a GitHub repository!"
            )
            return

        # Create inline keyboard with topics
        keyboard_buttons = []
        for topic in topics[:10]:  # Limit to 10 topics
            title = topic.title[:30] + "..." if len(topic.title) > 30 else topic.title
            keyboard_buttons.append(
                [InlineKeyboardButton(text=title, callback_data=f"study_topic:{topic.id}")]
            )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await state.set_state(StudyStates.selecting_topic)
        await state.update_data(user_id=user_id)

        await message.answer(
            "📖 <b>Start Study Session</b>\n\n"
            "Select a topic to study:\n\n"
            "Or send /cancel to abort.",
            reply_markup=keyboard,
        )


@router.callback_query(StudyStates.selecting_topic, F.data.startswith("study_topic:"))
async def process_topic_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Process topic selection for study.

    Args:
        callback: Callback query
        state: FSM context
    """
    topic_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    user_id = data["user_id"]

    await callback.answer("Starting quiz...")

    # Generate quiz questions
    processing_msg = await callback.message.edit_text(
        "⏳ Generating quiz questions...\nThis may take a moment."
    )

    try:
        async with AsyncSessionLocal() as session:
            topic_repository = TopicRepository(session)
            gemini_client = GeminiClient()
            
            # Create all necessary repositories
            from study_agent.infrastructure.database.repositories import (
                AssessmentRepository,
                PerformanceMetricsRepository,
                StudySessionRepository,
            )
            
            study_session_repository = StudySessionRepository(session)
            assessment_repository = AssessmentRepository(session)
            performance_metrics_repository = PerformanceMetricsRepository(session)
            
            study_manager = StudyManager(
                gemini_client=gemini_client,
                topic_repository=topic_repository,
                study_session_repository=study_session_repository,
                assessment_repository=assessment_repository,
                performance_metrics_repository=performance_metrics_repository,
            )

            # Get topic info
            topic = await topic_repository.get_by_id(topic_id)
            if not topic:
                await processing_msg.edit_text("❌ Topic not found. Please try again with /study")
                await state.clear()
                return

            # Create study session
            study_session = await study_manager.create_study_session(
                user_id=user_id,
                topic_id=topic_id,
                session_type="manual",
            )

            # Generate questions
            assessments = await study_manager.generate_quiz_questions(
                session_id=study_session.id,
                num_questions=3,  # Start with 3 questions
            )

            if not assessments:
                await processing_msg.edit_text(
                    "❌ Could not generate questions for this topic.\n"
                    "Please try another topic with /study"
                )
                await state.clear()
                return

            # Store session data
            await state.set_state(StudyStates.answering_question)
            await state.update_data(
                study_session_id=study_session.id,
                assessments=[a.id for a in assessments],
                current_question_idx=0,
                topic_title=topic.title,
                correct_count=0,
            )

            # Show first question
            first_question = assessments[0]
            await processing_msg.edit_text(
                f"📝 <b>Quiz: {topic.title}</b>\n\n"
                f"<b>Question 1/{len(assessments)}:</b>\n"
                f"{first_question.question}\n\n"
                "Type your answer below:"
            )

    except Exception as e:
        logger.error(f"Error starting study session: {str(e)}")
        await processing_msg.edit_text(
            "❌ An error occurred while generating questions.\n\n"
            "This might be due to:\n"
            "• Gemini API issues\n"
            "• Invalid topic content\n\n"
            "Please try again later."
        )
        await state.clear()


@router.message(StudyStates.answering_question)
async def process_answer(message: Message, state: FSMContext) -> None:
    """Process user's answer to a quiz question.

    Args:
        message: Incoming message with answer
        state: FSM context
    """
    user_answer = message.text.strip()
    data = await state.get_data()

    study_session_id = data["study_session_id"]
    assessments = data["assessments"]
    current_idx = data["current_question_idx"]
    topic_title = data["topic_title"]
    correct_count = data["correct_count"]

    current_assessment_id = assessments[current_idx]

    # Show processing
    processing_msg = await message.answer("🔍 Evaluating your answer...")

    try:
        async with AsyncSessionLocal() as session:
            topic_repository = TopicRepository(session)
            gemini_client = GeminiClient()
            
            # Create all necessary repositories
            from study_agent.infrastructure.database.repositories import (
                AssessmentRepository,
                PerformanceMetricsRepository,
                StudySessionRepository,
            )
            
            study_session_repository = StudySessionRepository(session)
            assessment_repository = AssessmentRepository(session)
            performance_metrics_repository = PerformanceMetricsRepository(session)
            
            study_manager = StudyManager(
                gemini_client=gemini_client,
                topic_repository=topic_repository,
                study_session_repository=study_session_repository,
                assessment_repository=assessment_repository,
                performance_metrics_repository=performance_metrics_repository,
            )

            # Evaluate answer
            evaluation = await study_manager.evaluate_answer(
                assessment_id=current_assessment_id,
                user_answer=user_answer,
            )

            # Update correct count
            if evaluation.get("is_correct", False):
                correct_count += 1

            # Show feedback
            score = evaluation.get("score", 0)
            feedback = evaluation.get("feedback", "No feedback available")

            if score >= 0.8:
                emoji = "✅"
                verdict = "Excellent!"
            elif score >= 0.6:
                emoji = "👍"
                verdict = "Good!"
            elif score >= 0.4:
                emoji = "😐"
                verdict = "Partial credit"
            else:
                emoji = "❌"
                verdict = "Needs improvement"

            feedback_text = (
                f"{emoji} <b>{verdict}</b> (Score: {score:.0%})\n\n<b>Feedback:</b> {feedback}\n\n"
            )

            # Check if there are more questions
            next_idx = current_idx + 1
            if next_idx < len(assessments):
                # Update state and show next question
                await state.update_data(
                    current_question_idx=next_idx,
                    correct_count=correct_count,
                )

                # Get next question
                stmt = select(AssessmentModel).where(AssessmentModel.id == assessments[next_idx])
                result = await session.execute(stmt)
                next_assessment = result.scalar_one()

                await processing_msg.edit_text(
                    feedback_text + f"<b>Question {next_idx + 1}/{len(assessments)}:</b>\n"
                    f"{next_assessment.question}\n\n"
                    "Type your answer below:"
                )
            else:
                # Quiz complete - show results
                total = len(assessments)
                final_score = correct_count / total

                # Complete the session
                await study_manager.complete_session(study_session_id)

                if final_score >= 0.8:
                    result_emoji = "🏆"
                    result_msg = "Outstanding performance!"
                elif final_score >= 0.6:
                    result_emoji = "⭐"
                    result_msg = "Good job!"
                elif final_score >= 0.4:
                    result_emoji = "📚"
                    result_msg = "Keep practicing!"
                else:
                    result_emoji = "💪"
                    result_msg = "Don't give up!"

                await processing_msg.edit_text(
                    feedback_text + "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{result_emoji} <b>Quiz Complete!</b>\n\n"
                    f"<b>Topic:</b> {topic_title}\n"
                    f"<b>Score:</b> {correct_count}/{total} ({final_score:.0%})\n\n"
                    f"{result_msg}\n\n"
                    "Use /study to practice another topic!\n"
                    "Use /stats to see your overall progress."
                )
                await state.clear()

    except Exception as e:
        logger.error(f"Error evaluating answer: {str(e)}")
        await processing_msg.edit_text(
            "❌ An error occurred while evaluating your answer.\n\n"
            "Please try again or use /cancel to exit."
        )


# ============================================================================
# STATISTICS COMMANDS
# ============================================================================


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Handle /stats command - show user statistics.

    Args:
        message: Incoming message
    """
    user_id = await get_user_id_from_telegram(message.from_user.id)
    if not user_id:
        await message.answer("⚠️ You need to register first. Please use /start to begin.")
        return

    async with AsyncSessionLocal() as session:
        # Get total sessions
        sessions_stmt = select(func.count(StudySessionModel.id)).where(
            StudySessionModel.user_id == user_id
        )
        sessions_result = await session.execute(sessions_stmt)
        total_sessions = sessions_result.scalar() or 0

        # Get completed sessions
        completed_stmt = select(func.count(StudySessionModel.id)).where(
            StudySessionModel.user_id == user_id, StudySessionModel.status == "completed"
        )
        completed_result = await session.execute(completed_stmt)
        completed_sessions = completed_result.scalar() or 0

        # Get performance metrics
        metrics_stmt = select(PerformanceMetricsModel).where(
            PerformanceMetricsModel.user_id == user_id
        )
        metrics_result = await session.execute(metrics_stmt)
        metrics = metrics_result.scalars().all()

        # Calculate overall stats
        if metrics:
            total_questions = sum(m.total_questions for m in metrics)
            total_correct = sum(m.total_correct for m in metrics)
            overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
            topics_studied = len(metrics)
        else:
            total_questions = 0
            total_correct = 0
            overall_accuracy = 0
            topics_studied = 0

        # Get repository count
        repos_stmt = select(func.count(RepositoryModel.id)).where(
            RepositoryModel.user_id == user_id, RepositoryModel.is_active.is_(True)
        )
        repos_result = await session.execute(repos_stmt)
        total_repos = repos_result.scalar() or 0

        stats_text = (
            "📊 <b>Your Statistics</b>\n\n"
            "<b>Overview:</b>\n"
            f"📦 Repositories: {total_repos}\n"
            f"📚 Topics Studied: {topics_studied}\n"
            f"📝 Study Sessions: {completed_sessions}/{total_sessions}\n\n"
            "<b>Performance:</b>\n"
            f"❓ Questions Answered: {total_questions}\n"
            f"✅ Correct Answers: {total_correct}\n"
            f"🎯 Overall Accuracy: {overall_accuracy:.1f}%\n\n"
        )

        if metrics:
            # Show top performing topics
            sorted_metrics = sorted(metrics, key=lambda m: m.average_score, reverse=True)
            top_metrics = sorted_metrics[:3]

            if top_metrics:
                topic_repo = TopicRepository(session)

                stats_text += "<b>Top Topics:</b>\n"
                for m in top_metrics:
                    topic = await topic_repo.get_by_id(m.topic_id)
                    if topic:
                        title = topic.title[:25] + "..." if len(topic.title) > 25 else topic.title
                        stats_text += f"⭐ {title}: {m.average_score:.0%}\n"

        stats_text += "\nKeep studying to improve your stats! 📈"

        await message.answer(stats_text)


# ============================================================================
# TEST COMMANDS
# ============================================================================


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
        {"question": "What is the capital of France?", "answer": "Paris"},
        {"question": "What is 2 + 2?", "answer": "4"},
        {"question": "What color is the sky?", "answer": "Blue"},
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
