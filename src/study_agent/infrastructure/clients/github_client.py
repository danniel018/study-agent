"""GitHub API client."""

import base64
import warnings
from typing import Any

import httpx

from study_agent.core.exceptions import RepositoryAccessError, RepositoryNotFoundError


class GitHubClient:
    """Async client for GitHub API operations."""

    def __init__(self, github_token: str | None = None):
        """Initialize GitHub client.

        Args:
            github_token: Optional GitHub personal access token for private repos
        """
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

    async def get_repository_contents(
        self,
        owner: str,
        repo: str,
    ) -> list[dict[str, Any]]:
        """Get repository contents from tree recursively.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of repository items (files/directories)

        Raises:
            RepositoryNotFoundError: If repository not found
            RepositoryAccessError: If unable to access repository
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/main?recursive=1"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=30.0)

                if response.status_code == 404:
                    raise RepositoryNotFoundError(f"Repository {owner}/{repo} not found")
                elif response.status_code == 403:
                    raise RepositoryAccessError(f"Access denied to {owner}/{repo}")
                elif response.status_code != 200:
                    raise RepositoryAccessError(
                        f"Failed to fetch contents: HTTP {response.status_code}"
                    )

                return response.json().get("tree", [])
            except httpx.TimeoutException:
                raise RepositoryAccessError("Request timeout")
            except httpx.RequestError as e:
                raise RepositoryAccessError(f"Request failed: {str(e)}")

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
    ) -> str:
        """Get decoded file content.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path

        Returns:
            Decoded file content as string

        Raises:
            RepositoryNotFoundError: If file not found
            RepositoryAccessError: If unable to access file
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=30.0)

                if response.status_code == 404:
                    raise RepositoryNotFoundError(f"File {path} not found")
                elif response.status_code != 200:
                    raise RepositoryAccessError(
                        f"Failed to fetch file: HTTP {response.status_code}"
                    )

                data = response.json()

                # Decode base64 content
                if data.get("encoding") == "base64":
                    content_bytes = base64.b64decode(data["content"])
                    return content_bytes.decode("utf-8")

                return data.get("content", "")
            except httpx.TimeoutException:
                raise RepositoryAccessError("Request timeout")
            except httpx.RequestError as e:
                raise RepositoryAccessError(f"Request failed: {str(e)}")

    async def list_markdown_files(
        self,
        owner: str,
        repo: str,
    ) -> list[str]:
        """Recursively list all markdown files in repository.

        .. deprecated::
            This method is deprecated. Use get_repository_contents() instead
            and filter for markdown files directly from the tree response.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of markdown file paths
        """
        warnings.warn(
            "list_markdown_files is deprecated. Use get_repository_contents() "
            "and filter for .md files from the tree response instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        try:
            contents = await self.get_repository_contents(owner, repo)
        except (RepositoryNotFoundError, RepositoryAccessError):
            return []

        return [
            item["path"]
            for item in contents
            if item["type"] == "blob" and item["path"].endswith(".md")
        ]
