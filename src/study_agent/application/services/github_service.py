"""GitHub service for repository operations."""

import hashlib
import logging

from study_agent.config.constants import MIN_TOPIC_LENGTH_WORDS
from study_agent.core.exceptions import RepositoryError, RepositoryNotFoundError
from study_agent.core.utils import count_words
from study_agent.infrastructure.clients.gemini_client import GeminiClient
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
        gemini_client: GeminiClient,
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
        self.gemini_client = gemini_client
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
            repo_contents = await self.github_client.get_repository_contents(
                repo.repo_owner,
                repo.repo_name,
            )

            logger.info(f"Found {len(repo_contents)} items in GitHub")

            files = [item for item in repo_contents if item["type"] == "blob"]

            # main readme
            readme = next(
                (item["path"] for item in files if item["path"].lower() == "readme.md"), None
            )
            if readme:
                readme_content = await self.github_client.get_file_content(
                    repo.repo_owner,
                    repo.repo_name,
                    readme,
                )

            # get topics using LLM
            llm_topics = await self.gemini_client.get_repository_topics(
                readme_content=readme_content if readme else None,
                file_list=[item["path"] for item in files],
            )
            topics = []
            for topic in llm_topics:
                sections = []
                for file_path in topic["files"]:
                    try:
                        file_content = await self.github_client.get_file_content(
                            repo.repo_owner,
                            repo.repo_name,
                            file_path,
                        )
                        if count_words(file_content) >= MIN_TOPIC_LENGTH_WORDS:
                            ext = file_path.split(".")[-1].lower()
                            sections.append(
                                f"## File {file_path}\n```{ext}\n{file_content}\n```",
                            )

                    except RepositoryNotFoundError:
                        logger.warning(f"File {file_path} not found, skipping for topic.")
                        continue
                if sections:
                    topics.append(
                        {
                            "title": topic["title"],
                            "content": "\n\n".join(sections),
                            "file_paths": topic["files"],
                            "content_hash": hashlib.sha256("".join(sections).encode()).hexdigest(),
                        }
                    )

            # Delete existing topics for this repository
            await self.topic_repository.delete_by_repository(repo_id)

            # Create new topics
            topics_created = 0
            for topic_data in topics:
                await self.topic_repository.create(
                    repository_id=repo_id,
                    title=topic_data["title"],
                    file_paths=topic_data["file_paths"],
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
