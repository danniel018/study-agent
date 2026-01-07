"""Database initialization script."""

import asyncio
import logging

from study_agent.infrastructure.database.engine import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize the database."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())
