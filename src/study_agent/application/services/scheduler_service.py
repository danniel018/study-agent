"""Scheduler service for automatic study session notifications."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from study_agent.config.settings import settings
from study_agent.infrastructure.database.engine import AsyncSessionLocal
from study_agent.infrastructure.database.models import (
    PerformanceMetricsModel,
    ScheduleConfigModel,
    UserModel,
)
from study_agent.infrastructure.database.repositories.topic_repository import TopicRepository

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling automatic study reminders and quizzes."""

    def __init__(self, bot: "Bot"):
        """Initialize scheduler service.

        Args:
            bot: Telegram bot instance for sending messages
        """
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=settings.SCHEDULER_TIMEZONE)
        self._is_running = False

    async def start(self) -> None:
        """Start the scheduler service."""
        if not settings.ENABLE_SCHEDULER:
            logger.info("Scheduler is disabled in settings")
            return

        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        # Add the main check job that runs every hour
        self.scheduler.add_job(
            self._check_scheduled_reviews,
            CronTrigger(minute=0),  # Run at the start of every hour
            id="check_scheduled_reviews",
            replace_existing=True,
        )

        # Add a job to check topics due for review every 30 minutes
        self.scheduler.add_job(
            self._check_topics_for_review,
            CronTrigger(minute="*/30"),  # Run every 30 minutes
            id="check_topics_for_review",
            replace_existing=True,
        )

        self.scheduler.start()
        self._is_running = True
        logger.info("Scheduler service started")

    async def stop(self) -> None:
        """Stop the scheduler service."""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("Scheduler service stopped")

    async def _check_scheduled_reviews(self) -> None:
        """Check for users who should receive their scheduled study session."""
        current_time = datetime.now()
        current_hour_minute = current_time.strftime("%H:%M")

        logger.debug(f"Checking scheduled reviews at {current_hour_minute}")

        try:
            async with AsyncSessionLocal() as session:
                # Get all schedule configs where preferred_time matches current hour
                stmt = select(ScheduleConfigModel).where(
                    ScheduleConfigModel.is_enabled.is_(True),
                    ScheduleConfigModel.preferred_time == current_hour_minute,
                )
                result = await session.execute(stmt)
                configs = result.scalars().all()

                for config in configs:
                    # Check if today is in the user's scheduled days
                    current_day = current_time.strftime("%A").lower()
                    if config.days_of_week:
                        days = [d.strip().lower() for d in config.days_of_week.split(",")]
                        if current_day not in days:
                            continue

                    # Get user
                    user_stmt = select(UserModel).where(UserModel.id == config.user_id)
                    user_result = await session.execute(user_stmt)
                    user = user_result.scalar_one_or_none()

                    if user:
                        await self._send_study_reminder(user)

        except Exception as e:
            logger.error(f"Error checking scheduled reviews: {str(e)}")

    async def _check_topics_for_review(self) -> None:
        """Check for topics that are due for spaced repetition review."""
        current_time = datetime.now()

        logger.debug("Checking topics due for review")

        try:
            async with AsyncSessionLocal() as session:
                # Get all performance metrics where next_review_at is in the past
                stmt = select(PerformanceMetricsModel).where(
                    PerformanceMetricsModel.next_review_at <= current_time,
                    PerformanceMetricsModel.next_review_at.isnot(None),
                )
                result = await session.execute(stmt)
                metrics = result.scalars().all()

                # Group by user
                user_topics: dict[int, list[int]] = {}
                for metric in metrics:
                    if metric.user_id not in user_topics:
                        user_topics[metric.user_id] = []
                    user_topics[metric.user_id].append(metric.topic_id)

                # Send reminders for each user
                for user_id, topic_ids in user_topics.items():
                    user_stmt = select(UserModel).where(UserModel.id == user_id)
                    user_result = await session.execute(user_stmt)
                    user = user_result.scalar_one_or_none()

                    if user:
                        await self._send_review_reminder(user, topic_ids, session)

        except Exception as e:
            logger.error(f"Error checking topics for review: {str(e)}")

    async def _send_study_reminder(self, user: UserModel) -> None:
        """Send a study reminder to a user.

        Args:
            user: User model
        """
        try:
            message = (
                "📚 <b>Time to Study!</b>\n\n"
                "Your scheduled study session is ready.\n\n"
                "Use /study to start a quiz and reinforce your learning!"
            )
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="HTML",
            )
            logger.info(f"Sent study reminder to user {user.telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send study reminder to {user.telegram_id}: {str(e)}")

    async def _send_review_reminder(
        self,
        user: UserModel,
        topic_ids: list[int],
        session,
    ) -> None:
        """Send a review reminder for specific topics.

        Args:
            user: User model
            topic_ids: List of topic IDs due for review
            session: Database session
        """
        try:
            topic_repo = TopicRepository(session)

            # Get topic names
            topic_names = []
            for topic_id in topic_ids[:5]:  # Limit to 5 topics in message
                topic = await topic_repo.get_by_id(topic_id)
                if topic:
                    name = topic.title[:30] + "..." if len(topic.title) > 30 else topic.title
                    topic_names.append(f"• {name}")

            topics_text = "\n".join(topic_names)
            extra = f"\n• ...and {len(topic_ids) - 5} more" if len(topic_ids) > 5 else ""

            message = (
                "🔔 <b>Topics Due for Review!</b>\n\n"
                "Based on spaced repetition, these topics are ready for review:\n\n"
                f"{topics_text}{extra}\n\n"
                "Use /study to select a topic and reinforce your memory!"
            )

            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="HTML",
            )
            logger.info(
                f"Sent review reminder to user {user.telegram_id} for {len(topic_ids)} topics"
            )
        except Exception as e:
            logger.error(f"Failed to send review reminder to {user.telegram_id}: {str(e)}")

    async def schedule_user_study(
        self,
        user_id: int,
        preferred_time: str,
        days_of_week: str = "monday,tuesday,wednesday,thursday,friday",
    ) -> None:
        """Schedule study sessions for a specific user.

        Args:
            user_id: User ID
            preferred_time: Preferred time in HH:MM format
            days_of_week: Comma-separated list of days
        """
        async with AsyncSessionLocal() as session:
            stmt = select(ScheduleConfigModel).where(ScheduleConfigModel.user_id == user_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if config:
                config.preferred_time = preferred_time
                config.days_of_week = days_of_week
                config.is_enabled = True
            else:
                config = ScheduleConfigModel(
                    user_id=user_id,
                    preferred_time=preferred_time,
                    days_of_week=days_of_week,
                    is_enabled=True,
                )
                session.add(config)

            await session.commit()
            logger.info(f"Updated schedule for user {user_id}: {preferred_time} on {days_of_week}")

    async def disable_user_schedule(self, user_id: int) -> None:
        """Disable scheduled study sessions for a user.

        Args:
            user_id: User ID
        """
        async with AsyncSessionLocal() as session:
            stmt = select(ScheduleConfigModel).where(ScheduleConfigModel.user_id == user_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if config:
                config.is_enabled = False
                await session.commit()
                logger.info(f"Disabled schedule for user {user_id}")


# Global scheduler instance (initialized when bot starts)
scheduler_service: SchedulerService | None = None


def get_scheduler_service() -> SchedulerService | None:
    """Get the global scheduler service instance.

    Returns:
        Scheduler service or None if not initialized
    """
    return scheduler_service


def init_scheduler_service(bot: "Bot") -> SchedulerService:
    """Initialize the global scheduler service.

    Args:
        bot: Telegram bot instance

    Returns:
        Initialized scheduler service
    """
    global scheduler_service
    scheduler_service = SchedulerService(bot)
    return scheduler_service
