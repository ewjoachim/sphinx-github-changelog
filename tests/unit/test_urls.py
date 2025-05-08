"""Test for identifying repository configuration from URLs."""

from __future__ import annotations

import pytest

from sphinx_github_changelog.urls import (
    get_github_graphql_url,
    get_github_host_from_url,
    get_root_url,
    normalize_github_url,
    parse_github_repo_from_url,
)


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://github.com/org/repo", "org/repo"),
        ("https://github.enterprise.com/org/repo", "org/repo"),
        ("https://github.com/org/repo/releases", "org/repo"),
        ("not-a-github-url", None),
    ],
)
def test_parse_github_repo_from_url(url: str, expected: str | None) -> None:
    """Should extract 'owner/repo' or return None for invalid URLs."""
    assert parse_github_repo_from_url(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://github.com/org/repo.git", "https://api.github.com/graphql"),
        (
            "https://github.enterprise.com/org/repo",
            "https://github.enterprise.com/api/graphql",
        ),
        ("not-a-github-url", "https://api.github.com/graphql"),
    ],
)
def test_get_github_graphql_url(url: str, expected: str | None) -> None:
    """Should derive the correct GraphQL endpoint or None for invalid URLs."""
    assert get_github_graphql_url(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://github.com/org/repo", "github.com"),
        ("https://github.enterprise.com/org/repo", "github.enterprise.com"),
    ],
)
def test_get_github_host_from_url(url: str, expected: str) -> None:
    """Should return the GitHub host name from the URL."""
    assert get_github_host_from_url(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://github.com/org/repo", "https://github.com/"),
        ("https://github.enterprise.com/org/repo", "https://github.enterprise.com/"),
    ],
)
def test_get_root_url(url: str, expected: str) -> None:
    """Should return the root URL (scheme + host + slash)."""
    assert get_root_url(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("git@github.com:org/repo.git", "https://github.com/org/repo"),
        (
            "https://github.enterprise.com/org/repo.git",
            "https://github.enterprise.com/org/repo",
        ),
        ("https://github.com/org/repo", "https://github.com/org/repo"),
        ("git@github.com:org/repo", "https://github.com/org/repo"),
        ("not-a-github-url", None),
    ],
)
def test_normalize_github_url(url: str, expected: str) -> None:
    """Should normalize SSH and HTTP(S) GitHub URLs to plain HTTPS."""
    assert normalize_github_url(url) == expected
