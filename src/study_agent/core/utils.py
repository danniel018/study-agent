"""Utility functions."""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_github_url(url: str) -> tuple[Optional[str], Optional[str]]:
    """Validate and parse GitHub repository URL.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo_name) if valid, (None, None) otherwise
        
    Examples:
        >>> validate_github_url("https://github.com/user/repo")
        ('user', 'repo')
        >>> validate_github_url("github.com/user/repo")
        ('user', 'repo')
    """
    # Handle URLs with or without protocol
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    
    parsed = urlparse(url)
    
    # Check if it's a GitHub URL
    if parsed.netloc not in ("github.com", "www.github.com"):
        return None, None
    
    # Extract owner and repo from path
    path_parts = [p for p in parsed.path.split("/") if p]
    
    if len(path_parts) < 2:
        return None, None
    
    owner = path_parts[0]
    repo = path_parts[1].replace(".git", "")
    
    return owner, repo


def count_words(text: str) -> int:
    """Count words in text.
    
    Args:
        text: Text to count words in
        
    Returns:
        Number of words
    """
    return len(text.split())


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
