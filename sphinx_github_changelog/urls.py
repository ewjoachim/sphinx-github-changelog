"""
Utilities for working with git remotes and GitHub URLs.

Includes functions to parse remote URLs and derive GraphQL endpoints.
"""

from __future__ import annotations

import re
import subprocess
from urllib.parse import urlparse


def parse_github_repo_from_url(url: str) -> str | None:
    """Parse the owner/repo from a GitHub remote URL (https or ssh).

    We also remove a trailing `/releases` if present as the expected usage
    is with the URL of the GitHub releases page.

    >>> parse_github_repo_from_url('https://github.com/org/repo')
    'org/repo'
    >>> parse_github_repo_from_url('https://github.com/org/repo/releases')
    'org/repo'
    """
    if m := re.fullmatch(r"https?://[^/]+/([^/]+/[^/.]+)(?:/releases)?", url):
        return m.group(1)
    return None


def get_github_graphql_url(repo_url: str) -> str:
    """Derive the GitHub GraphQL endpoint from a remote URL.

    >>> get_github_graphql_url('https://github.com/org/repo.git')
    'https://api.github.com/graphql'
    >>> get_github_graphql_url('https://github.enterprise.com/org/repo')
    'https://github.enterprise.com/api/graphql'
    """
    host = get_github_host_from_url(repo_url) or "github.com"
    if host == "github.com":
        return "https://api.github.com/graphql"
    return f"https://{host}/api/graphql"


def get_github_host_from_url(url: str) -> str:
    """Extract the host from a GitHub remote URL.

    >>> get_github_host_from_url('https://github.com/org/repo')
    'github.com'
    >>> get_github_host_from_url('https://github.enterprise.com/org/repo')
    'github.enterprise.com'
    """
    parsed = urlparse(url)
    return parsed.hostname or "github.com"


def get_root_url(url: str) -> str:
    """Extract the root URL from a GitHub remote URL.

    >>> get_root_url('https://github.com/org/repo')
    'https://github.com/'
    >>> get_root_url('https://github.enterprise.com/org/repo')
    'https://github.enterprise.com/'
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.hostname or 'github.com'}/"


def normalize_github_url(url: str) -> str | None:
    """Normalize a git remote URL to a plain HTTPS URL without .git.

    >>> normalize_github_url('git@github.com:org/repo.git')
    'https://github.com/org/repo'
    >>> normalize_github_url('https://github.enterprise.com/org/repo.git')
    'https://github.enterprise.com/org/repo'
    >>> normalize_github_url('https://github.com/org/repo')
    'https://github.com/org/repo'
    """
    if m := re.match(r"git@([^:]+):([^/]+/[^/]+?)(?:\.git)?$", url):
        host, repo = m.groups()
        return f"https://{host}/{repo}"
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https") and parsed.hostname and parsed.path:
        path = parsed.path
        if path.endswith(".git"):
            path = path[:-4]
        return f"{parsed.scheme}://{parsed.hostname}{path}"
    return None


def get_default_github_url() -> str | None:
    """Try to get the default GitHub remote URL from git remotes.

    Prefer upstream, then origin, if these are set and represent a
    GitHub remote.
    """
    try:
        remotes = subprocess.check_output(
            ["git", "remote", "-v"],
            text=True,
        ).splitlines()
        urls = {}
        for line in remotes:
            name, url, op = line.split(maxsplit=2)
            if op != "(fetch)":
                continue
            if clean := normalize_github_url(url):
                urls[name] = clean
        return urls.get("upstream") or urls.get("origin")
    except Exception:
        return None
