"""Test for detecting URLs from git remote configuration."""

import subprocess
from pathlib import Path

from sphinx_github_changelog import urls


def add_remote(name: str, url: str):
    """Add a remote to the git repository."""
    subprocess.check_call(["git", "remote", "add", name, url])


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
