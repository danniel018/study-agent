"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from study_agent.infrastructure.database.engine import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
    """Create a test database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_db):
    """Create a test database session."""
    async_test_session = async_sessionmaker(
        test_db,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_test_session() as session:
        yield session


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "telegram_id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
    }
