"""GitHub API client."""

import httpx
import base64
import hashlib
from typing import List, Dict, Any, Optional

from study_agent.core.exceptions import RepositoryNotFoundError, RepositoryAccessError
from study_agent.core.utils import count_words
from study_agent.config.constants import MIN_TOPIC_LENGTH_WORDS


class GitHubClient:
    """Async client for GitHub API operations."""
    
    def __init__(self, github_token: Optional[str] = None):
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
        path: str = "",
    ) -> List[Dict[str, Any]]:
        """Get repository contents at a path.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Path within repository (empty for root)
            
        Returns:
            List of content items
            
        Raises:
            RepositoryNotFoundError: If repository not found
            RepositoryAccessError: If unable to access repository
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
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
                
                return response.json()
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
                    raise RepositoryAccessError(f"Failed to fetch file: HTTP {response.status_code}")
                
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
        path: str = "",
    ) -> List[str]:
        """Recursively list all markdown files in repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Starting path
            
        Returns:
            List of markdown file paths
        """
        markdown_files = []
        
        try:
            contents = await self.get_repository_contents(owner, repo, path)
        except (RepositoryNotFoundError, RepositoryAccessError):
            return []
        
        for item in contents:
            if item["type"] == "file" and item["name"].endswith(".md"):
                markdown_files.append(item["path"])
            elif item["type"] == "dir":
                # Recursively scan directories
                subdir_files = await self.list_markdown_files(owner, repo, item["path"])
                markdown_files.extend(subdir_files)
        
        return markdown_files
    
    async def fetch_all_topics(
        self,
        owner: str,
        repo: str,
    ) -> List[Dict[str, str]]:
        """Fetch all study topics from a repository.
        
        This evaluates all markdown file content to extract topics.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of topic dictionaries with 'title', 'content', 'file_path', 'content_hash'
        """
        markdown_files = await self.list_markdown_files(owner, repo)
        topics = []
        
        for file_path in markdown_files:
            try:
                content = await self.get_file_content(owner, repo, file_path)
                
                # Skip files that are too short
                if count_words(content) < MIN_TOPIC_LENGTH_WORDS:
                    continue
                
                # Use file name (without .md) as title
                title = file_path.split("/")[-1].replace(".md", "").replace("-", " ").replace("_", " ").title()
                
                # Calculate content hash for change detection
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                
                topics.append({
                    "title": title,
                    "content": content,
                    "file_path": file_path,
                    "content_hash": content_hash,
                })
            except (RepositoryNotFoundError, RepositoryAccessError):
                # Skip files that can't be accessed
                continue
        
        return topics
