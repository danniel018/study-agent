"""User repository implementation."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from study_agent.infrastructure.database.models import UserModel, ScheduleConfigModel
from study_agent.domain.models.user import User
from study_agent.config.settings import settings


class UserRepository:
    """Repository for user data access."""
    
    def __init__(self, session: AsyncSession):
        """Initialize user repository.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            User if found, None otherwise
        """
        stmt = select(UserModel).where(UserModel.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return None
        
        return User(
            id=user_model.id,
            telegram_id=user_model.telegram_id,
            username=user_model.username,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            timezone=user_model.timezone,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            is_active=user_model.is_active,
        )
    
    async def create(
        self,
        telegram_id: int,
        first_name: str,
        username: Optional[str] = None,
        last_name: Optional[str] = None,
        timezone: str = "UTC",
    ) -> User:
        """Create a new user.
        
        Args:
            telegram_id: Telegram user ID
            first_name: User's first name
            username: User's username
            last_name: User's last name
            timezone: User's timezone
            
        Returns:
            Created user
        """
        user_model = UserModel(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
            timezone=timezone,
        )
        self.session.add(user_model)
        await self.session.flush()
        
        # Create default schedule config
        schedule_config = ScheduleConfigModel(
            user_id=user_model.id,
            is_enabled=True,
            frequency="daily",
            preferred_time=settings.DEFAULT_STUDY_TIME,
            questions_per_session=5,
        )
        self.session.add(schedule_config)
        await self.session.commit()
        
        return User(
            id=user_model.id,
            telegram_id=user_model.telegram_id,
            username=user_model.username,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            timezone=user_model.timezone,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            is_active=user_model.is_active,
        )
