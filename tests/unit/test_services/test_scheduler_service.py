"""Tests for scheduler service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from study_agent.application.services.scheduler_service import SchedulerService


class TestSchedulerService:
    """Tests for SchedulerService."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.fixture
    def scheduler_service(self, mock_bot):
        """Create a scheduler service instance."""
        return SchedulerService(mock_bot)

    def test_init(self, scheduler_service, mock_bot):
        """Test scheduler initialization."""
        assert scheduler_service.bot == mock_bot
        assert scheduler_service._is_running is False

    @pytest.mark.asyncio
    async def test_start_scheduler(self, scheduler_service):
        """Test starting the scheduler."""
        with patch.object(scheduler_service.scheduler, "start") as mock_start:
            with patch.object(scheduler_service.scheduler, "add_job"):
                await scheduler_service.start()

                mock_start.assert_called_once()
                assert scheduler_service._is_running is True

    @pytest.mark.asyncio
    async def test_start_scheduler_disabled(self, mock_bot):
        """Test starting scheduler when disabled."""
        with patch("study_agent.application.services.scheduler_service.settings") as mock_settings:
            mock_settings.ENABLE_SCHEDULER = False
            mock_settings.SCHEDULER_TIMEZONE = "UTC"

            service = SchedulerService(mock_bot)
            await service.start()

            assert service._is_running is False

    @pytest.mark.asyncio
    async def test_stop_scheduler(self, scheduler_service):
        """Test stopping the scheduler."""
        scheduler_service._is_running = True

        with patch.object(scheduler_service.scheduler, "shutdown") as mock_shutdown:
            await scheduler_service.stop()

            mock_shutdown.assert_called_once_with(wait=False)
            assert scheduler_service._is_running is False

    @pytest.mark.asyncio
    async def test_stop_scheduler_not_running(self, scheduler_service):
        """Test stopping scheduler when not running."""
        scheduler_service._is_running = False

        with patch.object(scheduler_service.scheduler, "shutdown") as mock_shutdown:
            await scheduler_service.stop()

            mock_shutdown.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_study_reminder(self, scheduler_service, mock_bot):
        """Test sending study reminder."""
        mock_user = MagicMock()
        mock_user.telegram_id = 123456789

        await scheduler_service._send_study_reminder(mock_user)

        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 123456789
        assert "Time to Study" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_send_study_reminder_error(self, scheduler_service, mock_bot):
        """Test sending study reminder with error."""
        mock_user = MagicMock()
        mock_user.telegram_id = 123456789
        mock_bot.send_message = AsyncMock(side_effect=Exception("Network error"))

        # Should not raise exception
        await scheduler_service._send_study_reminder(mock_user)

    @pytest.mark.asyncio
    async def test_schedule_user_study(self, scheduler_service, test_session, mock_user_data):
        """Test scheduling study for a user."""
        from study_agent.infrastructure.database.repositories.user_repository import UserRepository

        # Create user first
        user_repo = UserRepository(test_session)
        user = await user_repo.create(**mock_user_data)

        await scheduler_service.schedule_user_study(
            user_id=user.id,
            preferred_time="10:00",
            days_of_week="monday,wednesday,friday",
        )

        # Verify schedule was created (this would need to query the database)
        # For now, just verify it doesn't raise an exception

    @pytest.mark.asyncio
    async def test_disable_user_schedule(self, scheduler_service, test_session, mock_user_data):
        """Test disabling schedule for a user."""
        from study_agent.infrastructure.database.repositories.user_repository import UserRepository

        # Create user first
        user_repo = UserRepository(test_session)
        user = await user_repo.create(**mock_user_data)

        # First schedule, then disable
        await scheduler_service.schedule_user_study(
            user_id=user.id,
            preferred_time="10:00",
        )
        await scheduler_service.disable_user_schedule(user.id)

        # Should not raise an exception
