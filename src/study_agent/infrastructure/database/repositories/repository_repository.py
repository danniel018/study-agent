"""Repository repository implementation."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from study_agent.infrastructure.database.models import RepositoryModel
from study_agent.domain.models.repository import Repository


class RepositoryRepository:
    """Repository for repository data access."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository repository.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def create(
        self,
        user_id: int,
        repo_url: str,
        repo_owner: str,
        repo_name: str,
    ) -> Repository:
        """Create a new repository.
        
        Args:
            user_id: User ID
            repo_url: Repository URL
            repo_owner: Repository owner
            repo_name: Repository name
            
        Returns:
            Created repository
        """
        repo_model = RepositoryModel(
            user_id=user_id,
            repo_url=repo_url,
            repo_owner=repo_owner,
            repo_name=repo_name,
            is_active=True,
        )
        self.session.add(repo_model)
        await self.session.commit()
        await self.session.refresh(repo_model)
        
        return Repository(
            id=repo_model.id,
            user_id=repo_model.user_id,
            repo_url=repo_model.repo_url,
            repo_owner=repo_model.repo_owner,
            repo_name=repo_model.repo_name,
            is_active=repo_model.is_active,
            created_at=repo_model.created_at,
            last_synced_at=repo_model.last_synced_at,
        )
    
    async def get_by_user(self, user_id: int) -> List[Repository]:
        """Get all repositories for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of repositories
        """
        stmt = select(RepositoryModel).where(
            RepositoryModel.user_id == user_id,
            RepositoryModel.is_active == True,
        )
        result = await self.session.execute(stmt)
        repo_models = result.scalars().all()
        
        return [
            Repository(
                id=model.id,
                user_id=model.user_id,
                repo_url=model.repo_url,
                repo_owner=model.repo_owner,
                repo_name=model.repo_name,
                is_active=model.is_active,
                created_at=model.created_at,
                last_synced_at=model.last_synced_at,
            )
            for model in repo_models
        ]
    
    async def get_by_id(self, repo_id: int) -> Optional[Repository]:
        """Get repository by ID.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            Repository if found, None otherwise
        """
        stmt = select(RepositoryModel).where(RepositoryModel.id == repo_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return Repository(
            id=model.id,
            user_id=model.user_id,
            repo_url=model.repo_url,
            repo_owner=model.repo_owner,
            repo_name=model.repo_name,
            is_active=model.is_active,
            created_at=model.created_at,
            last_synced_at=model.last_synced_at,
        )
    
    async def update_last_synced(self, repo_id: int) -> None:
        """Update last synced timestamp.
        
        Args:
            repo_id: Repository ID
        """
        stmt = select(RepositoryModel).where(RepositoryModel.id == repo_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.last_synced_at = datetime.utcnow()
            await self.session.commit()
