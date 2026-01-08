"""Main entry point for Study Agent."""

import asyncio
import logging

from study_agent.config.settings import settings
from study_agent.infrastructure.database.engine import init_db, close_db
from study_agent.presentation.telegram.bot import TelegramBot

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main application entry point."""
    logger.info("Starting Study Agent...")
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    
    # Create and start bot
    bot = TelegramBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await bot.stop()
        await close_db()
        logger.info("Study Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
