"""Test utilities."""

from study_agent.core.utils import count_words, truncate_text, validate_github_url


def test_validate_github_url():
    """Test GitHub URL validation."""
    # Valid URLs
    owner, repo = validate_github_url("https://github.com/user/repo")
    assert owner == "user"
    assert repo == "repo"

    owner, repo = validate_github_url("github.com/user/repo")
    assert owner == "user"
    assert repo == "repo"

    owner, repo = validate_github_url("https://github.com/user/repo.git")
    assert owner == "user"
    assert repo == "repo"

    # Invalid URLs
    owner, repo = validate_github_url("https://gitlab.com/user/repo")
    assert owner is None
    assert repo is None

    owner, repo = validate_github_url("not-a-url")
    assert owner is None
    assert repo is None


def test_count_words():
    """Test word counting."""
    assert count_words("hello world") == 2
    assert count_words("one") == 1
    assert count_words("") == 0  # Empty string should have 0 words
    assert count_words("a b c d e") == 5


def test_truncate_text():
    """Test text truncation."""
    short_text = "Short"
    assert truncate_text(short_text, 100) == "Short"

    long_text = "a" * 200
    truncated = truncate_text(long_text, 100)
    assert len(truncated) == 100
    assert truncated.endswith("...")
