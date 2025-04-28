"""
Credential helpers for sphinx-github-changelog.

Provides functions to obtain a GitHub token using environment variables,
git credential helpers, or the GitHub CLI.
"""

import os
import subprocess
from typing import Optional


def get_token_from_env(host: str = "github.com") -> Optional[str]:
    """
    Get GitHub token from the SPHINX_GITHUB_CHANGELOG_TOKEN environment variable.

    >>> import os; os.environ['SPHINX_GITHUB_CHANGELOG_TOKEN'] = 'abc123'
    >>> get_token_from_env()
    'abc123'
    >>> del os.environ['SPHINX_GITHUB_CHANGELOG_TOKEN']
    >>> get_token_from_env() is None
    True
    """
    return os.environ.get("SPHINX_GITHUB_CHANGELOG_TOKEN")


def get_token_from_git_credential(host: str = "github.com") -> Optional[str]:
    """
    Get a GitHub access token using git's credential helper.

    >>> token = get_token_from_git_credential('example.com')
    >>> token is None or isinstance(token, str)
    True
    """
    try:
        resp = subprocess.check_output(
            ["git", "credential", "fill"],
            input=f"protocol=https\nhost={host}\n",
            text=True,
        )
        for ln in resp.splitlines():
            key, eq, value = ln.partition("=")
            if key == "password":
                return value
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return None


def get_token_from_gh_cli(host: str = "github.com") -> Optional[str]:
    """Get a GitHub token using the GitHub CLI (gh auth token)."""
    try:
        token = subprocess.check_output(
            ["gh", "auth", "token", f"--hostname={host}"], text=True
        ).strip()
        if token:
            return token
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return None


def get_github_token(host: str = "github.com") -> Optional[str]:
    """
    Try to obtain a GitHub token using several mechanisms in order.

    1. Environment variable
    2. git credential helper
    3. gh CLI

    Returns None if no token is found.
    """
    return (
        get_token_from_env(host)
        or get_token_from_git_credential(host)
        or get_token_from_gh_cli(host)
    )
