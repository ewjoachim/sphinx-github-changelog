"""Test for detecting URLs from git remote configuration."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from sphinx_github_changelog import urls
from sphinx_github_changelog.credentials import (
    get_token_from_gh_cli,
    get_token_from_git_credential,
    is_github_token,
)


def git(*args: str) -> str:
    """Run a git command and return the output."""
    return subprocess.check_output(["git", *args], text=True).strip()


def add_remote(name: str, url: str):
    """Add a remote to the git repository."""
    git("remote", "add", name, url)


def test_get_git_remote_origin(temp_git: Path):
    """Test for getting the GitHub URL from the origin remote."""
    add_remote("origin", "https://github.com/ewjoachim/sphinx-github-changelog.git")
    assert (
        urls.get_default_github_url()
        == "https://github.com/ewjoachim/sphinx-github-changelog"
    )


def test_get_git_remote_upstream(temp_git: Path):
    """Test for getting the GitHub URL from the upsteam remote."""
    add_remote("origin", "https://github.com/lordmauve/sphinx-github-changelog.git")
    add_remote("upstream", "https://github.com/ewjoachim/sphinx-github-changelog.git")
    assert (
        urls.get_default_github_url()
        == "https://github.com/ewjoachim/sphinx-github-changelog"
    )


def test_get_git_no_remotes(temp_git: Path):
    """We can't get a GitHub URL if no remotes are set."""
    assert urls.get_default_github_url() is None


@pytest.fixture
def credential_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture to configure a temporary git repo with a credential file.

    Disable git's other credential mechanisms and isolate its configurations.
    """
    cred_file = tmp_path / "cred"

    # Disable system and global git config to avoid polluting the test
    # environment.
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.delenv("GIT_ASKPASS", raising=False)
    monkeypatch.delenv("SSH_ASKPASS", raising=False)

    # Configure a credential store and write credentials.
    git("config", "credential.helper", f"store --file={cred_file.as_posix()}")

    return cred_file


def test_git_credential(credential_file: Path):
    """Test for getting a git token from the git credential helper."""
    credential_file.write_text("https://x:gho_1234abcd@github.com\n")

    assert get_token_from_git_credential("github.com") == "gho_1234abcd"


def test_git_credential_password(credential_file: Path):
    """We do not attempt to use a password that does not look like a token."""
    credential_file.write_text("https://ewjoachim:hunter2@github.com\n")

    assert get_token_from_git_credential("github.com") is None


def test_git_credential_unavailable(credential_file: Path):
    """We return None if no git credentials are available."""
    credential_file.write_text("\n")
    assert get_token_from_git_credential("github.com") is None


@pytest.mark.skipif(
    shutil.which("gh") is None,
    reason="GitHub CLI is not installed or not in PATH",
)
def test_get_token_from_gh():
    """Test for getting a GitHub token from the gh CLI.

    Because the test is disabled if the gh CLI is not available, we assume that
    the CLI is already logged into GitHub.
    """
    assert is_github_token(get_token_from_gh_cli("github.com"))
