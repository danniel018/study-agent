"""GitHub service for repository operations."""

import logging

from study_agent.core.exceptions import RepositoryError
from study_agent.infrastructure.clients.github_client import GitHubClient
from study_agent.infrastructure.database.repositories.repository_repository import (
    RepositoryRepository,
)
from study_agent.infrastructure.database.repositories.topic_repository import TopicRepository

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for GitHub repository operations."""

    def __init__(
        self,
        github_client: GitHubClient,
        repo_repository: RepositoryRepository,
        topic_repository: TopicRepository,
    ):
        """Initialize GitHub service.

        Args:
            github_client: GitHub API client
            repo_repository: Repository data access
            topic_repository: Topic data access
        """
        self.github_client = github_client
        self.repo_repository = repo_repository
        self.topic_repository = topic_repository

    async def sync_repository(self, repo_id: int) -> int:
        """Sync repository content from GitHub.

        Args:
            repo_id: Repository ID

        Returns:
            Number of topics synced

        Raises:
            RepositoryError: If sync fails
        """
        # Get repository info
        repo = await self.repo_repository.get_by_id(repo_id)
        if not repo:
            raise RepositoryError(f"Repository {repo_id} not found")

        logger.info(f"Syncing repository: {repo.repo_owner}/{repo.repo_name}")

        try:
            # Fetch all topics from GitHub
            github_topics = await self.github_client.fetch_all_topics(
                repo.repo_owner,
                repo.repo_name,
            )

            logger.info(f"Found {len(github_topics)} topics in GitHub")

            # Delete existing topics for this repository
            await self.topic_repository.delete_by_repository(repo_id)

            # Create new topics
            topics_created = 0
            for topic_data in github_topics:
                await self.topic_repository.create(
                    repository_id=repo_id,
                    title=topic_data["title"],
                    file_path=topic_data["file_path"],
                    content=topic_data["content"],
                    content_hash=topic_data["content_hash"],
                )
                topics_created += 1

            # Update last synced timestamp
            await self.repo_repository.update_last_synced(repo_id)

            logger.info(f"Successfully synced {topics_created} topics")
            return topics_created

        except Exception as e:
            logger.error(f"Failed to sync repository: {str(e)}")
            raise RepositoryError(f"Sync failed: {str(e)}")
