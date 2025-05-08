"""
Credential helpers for sphinx-github-changelog.

Provides functions to obtain a GitHub token using environment variables,
git credential helpers, or the GitHub CLI.
"""

from __future__ import annotations

import os
import subprocess
from contextlib import suppress


def get_token_from_env(host: str = "github.com") -> str | None:
    """Get a GitHub token from the SPHINX_GITHUB_CHANGELOG_TOKEN env var.

    Return None if the environment variable is not set.
    """
    return os.environ.get("SPHINX_GITHUB_CHANGELOG_TOKEN")


def is_github_token(token: str) -> bool:
    """Check if the given string appears to be a GitHub token.

    See
    https://github.blog/changelog/2021-03-31-authentication-token-format-updates-are-generally-available/
    for the prefixes that indicate a GitHub token.

    As of 2025-05-08 the prefixes are `ghp_`, `gho_`, `ghu_`, and `ghs_`. We
    use a generic check for `gh?_` to allow for future prefixes.
    """
    return token.startswith("gh") and token[3] == "_"


def get_token_from_git_credential(host: str = "github.com") -> str | None:
    """
    Get a GitHub access token using git's credential helper.

    >>> token = get_token_from_git_credential('example.com')
    >>> token is None or isinstance(token, str)
    True
    """
    with suppress(subprocess.CalledProcessError, FileNotFoundError):
        resp = subprocess.check_output(
            ["git", "credential", "fill"],
            input=f"protocol=https\nhost={host}\n",
            text=True,
        )
        for ln in resp.splitlines():
            key, eq, value = ln.partition("=")
            if key == "password" and is_github_token(value):
                return value
    return None


def get_token_from_gh_cli(host: str = "github.com") -> str | None:
    """Get a GitHub token using the GitHub CLI (gh auth token)."""
    with suppress(subprocess.CalledProcessError, FileNotFoundError):
        token = subprocess.check_output(
            ["gh", "auth", "token", f"--hostname={host}"], text=True
        ).strip()
        if token:
            return token
    return None


def get_github_token(host: str = "github.com") -> str | None:
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
