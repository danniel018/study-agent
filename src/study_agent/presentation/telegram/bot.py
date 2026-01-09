"""Telegram bot initialization and setup."""

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from study_agent.application.services.scheduler_service import (
    get_scheduler_service,
    init_scheduler_service,
)
from study_agent.config.settings import settings
from study_agent.presentation.telegram.handlers import command_handlers

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot wrapper."""

    def __init__(self):
        """Initialize Telegram bot."""
        self.bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        # Use MemoryStorage for FSM states
        self.dp = Dispatcher(storage=MemoryStorage())

        # Register handlers
        self._register_handlers()

        # Initialize scheduler service
        self.scheduler = init_scheduler_service(self.bot)

    def _register_handlers(self) -> None:
        """Register all bot handlers."""
        command_handlers.register_handlers(self.dp)

    async def start(self) -> None:
        """Start the bot."""
        logger.info("Starting Telegram bot...")

        # Start scheduler
        await self.scheduler.start()

        try:
            await self.dp.start_polling(self.bot)
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the bot."""
        logger.info("Stopping Telegram bot...")

        # Stop scheduler
        scheduler = get_scheduler_service()
        if scheduler:
            await scheduler.stop()

        await self.bot.session.close()
