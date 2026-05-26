from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sphinx_github_changelog import github_releases

pytest_plugins = "sphinx.testing.fixtures"


@pytest.fixture(scope="session")
def rootdir():
    return Path(__file__).parent.absolute() / "roots"


@pytest.fixture
def release_dict():
    return {
        "name": "A new hope",
        "body": "yay",
        "html_url": "https://example.com",
        "tag_name": "1.0.0",
        "published_at": "2000-01-01",
        "created_at": "2000-01-01",
        "draft": False,
        "prerelease": False,
    }


@pytest.fixture
def release(release_dict):
    return github_releases.Release.from_rest(release_dict)


@pytest.fixture
def github_payload(release_dict):
    return [release_dict]


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.delenv("SPHINX_GITHUB_CHANGELOG_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [("authorization", "DUMMY")],
    }


@pytest.fixture
def temp_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture to create a temporary git repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo)
    monkeypatch.chdir(repo)
    return repo
