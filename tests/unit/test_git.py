"""Test for detecting URLs from git remote configuration."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sphinx_github_changelog import credentials, exceptions, urls


def git(*args: str) -> str:
    """Run a git command and return the output."""
    return subprocess.check_output(["git", *args], text=True).strip()


def add_remote(name: str, url: str):
    """Add a remote to the git repository."""
    git("remote", "add", name, url)


def test_get_git_remote_origin(temp_git: Path):
    """Test for getting the GitHub URL from the origin remote."""
    add_remote("origin", "https://github.com/ewjoachim/sphinx-github-changelog.git")
    candidates = urls.extract_remote_candidates()
    params = urls.GitHubParams.from_remote_urls(candidates)
    assert params.repo_url == "https://github.com/ewjoachim/sphinx-github-changelog"


def test_get_git_remote_upstream(temp_git: Path):
    """Test for getting the GitHub URL from the upstream remote."""
    add_remote("origin", "https://github.com/lordmauve/sphinx-github-changelog.git")
    add_remote("upstream", "https://github.com/ewjoachim/sphinx-github-changelog.git")
    candidates = urls.extract_remote_candidates()
    params = urls.GitHubParams.from_remote_urls(candidates)
    assert params.repo_url == "https://github.com/ewjoachim/sphinx-github-changelog"


def test_get_git_no_remotes(temp_git: Path):
    """We can't get a GitHub URL if no remotes are set."""
    with pytest.raises(exceptions.CouldNotExtract, match="No fetch URL found"):
        urls.extract_remote_candidates()


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

    assert credentials.get_token_from_git_credential("github.com") == "gho_1234abcd"


def test_git_credential_password(credential_file: Path):
    """We do not attempt to use a password that does not look like a token."""
    credential_file.write_text("https://ewjoachim:hunter2@github.com\n")

    assert credentials.get_token_from_git_credential("github.com") is None


def test_git_credential_unavailable(credential_file: Path):
    """We return None if no git credentials are available."""
    credential_file.write_text("\n")
    assert credentials.get_token_from_git_credential("github.com") is None


@pytest.mark.parametrize(
    "token, expected",
    [
        ("gha_123", True),
        ("gh_123", False),
        ("gha123", False),
        ("", False),
    ],
)
def test_is_github_token(token, expected):
    assert credentials.is_github_token(token) == expected


def test_get_token_from_gh(fake_process):
    """Test for getting a GitHub token from the gh CLI.

    Because the test is disabled if the gh CLI is not available, we assume that
    the CLI is already logged into GitHub.
    """
    fake_process.register(
        ["gh", "auth", "token", "--hostname=github.com"], stdout="ghx_123"
    )
    assert credentials.get_token_from_gh_cli("github.com") == "ghx_123"


def test_get_token_from_gh_empty(fake_process):
    """gh auth token returning empty output should return None."""
    fake_process.register(["gh", "auth", "token", "--hostname=github.com"], stdout="")
    assert credentials.get_token_from_gh_cli("github.com") is None


def test_get_github_token_from_env(monkeypatch):
    """get_github_token should return a token from environment."""
    monkeypatch.setenv("SPHINX_GITHUB_CHANGELOG_TOKEN", "gho_envtoken")
    assert credentials.get_github_token("github.com") == "gho_envtoken"


def test_get_github_token_not_found(monkeypatch, fake_process):
    """get_github_token should raise CouldNotExtract when no token is found."""
    monkeypatch.delenv("SPHINX_GITHUB_CHANGELOG_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    fake_process.register(["git", "credential", "fill"], stdout="")
    fake_process.register(["gh", "auth", "token", "--hostname=github.com"], stdout="")
    with pytest.raises(exceptions.CouldNotExtract, match="No GitHub token found"):
        credentials.get_github_token("github.com")
