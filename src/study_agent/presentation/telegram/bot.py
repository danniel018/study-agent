"""Telegram bot initialization and setup."""

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

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
        self.dp = Dispatcher()

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all bot handlers."""
        command_handlers.register_handlers(self.dp)

    async def start(self) -> None:
        """Start the bot."""
        logger.info("Starting Telegram bot...")
        try:
            await self.dp.start_polling(self.bot)
        finally:
            await self.bot.session.close()

    async def stop(self) -> None:
        """Stop the bot."""
        logger.info("Stopping Telegram bot...")
        await self.bot.session.close()
