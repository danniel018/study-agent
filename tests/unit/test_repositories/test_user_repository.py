"""Test for user repository."""

import pytest

from study_agent.infrastructure.database.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_create_user(test_session, mock_user_data):
    """Test creating a new user."""
    repo = UserRepository(test_session)

    user = await repo.create(
        telegram_id=mock_user_data["telegram_id"],
        first_name=mock_user_data["first_name"],
        last_name=mock_user_data["last_name"],
        username=mock_user_data["username"],
    )

    assert user is not None
    assert user.telegram_id == mock_user_data["telegram_id"]
    assert user.first_name == mock_user_data["first_name"]
    assert user.is_active is True


@pytest.mark.asyncio
async def test_get_user_by_telegram_id(test_session, mock_user_data):
    """Test retrieving user by Telegram ID."""
    repo = UserRepository(test_session)

    # Create user
    created_user = await repo.create(
        telegram_id=mock_user_data["telegram_id"],
        first_name=mock_user_data["first_name"],
    )

    # Retrieve user
    retrieved_user = await repo.get_by_telegram_id(mock_user_data["telegram_id"])

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.telegram_id == mock_user_data["telegram_id"]


@pytest.mark.asyncio
async def test_get_nonexistent_user(test_session):
    """Test retrieving a non-existent user."""
    repo = UserRepository(test_session)

    user = await repo.get_by_telegram_id(999999999)

    assert user is None
