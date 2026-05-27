from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from sphinx_github_changelog import github_releases

pytest_plugins = "sphinx.testing.fixtures"


PINNED_RELEASE_TAGS = {
    "1.0.0",
}


def _pin_release_payload(response: dict) -> dict:
    body = response.get("body", {}).get("string")
    body_was_bytes = isinstance(body, bytes)
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    if not isinstance(body, str):
        return response

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return response

    if not isinstance(payload, list):
        return response

    if payload and isinstance(payload[0], dict) and "tag_name" in payload[0]:
        payload = [r for r in payload if r.get("tag_name") in PINNED_RELEASE_TAGS]
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        response["body"]["string"] = (
            encoded.encode("utf-8") if body_was_bytes else encoded
        )

        for key in list(response.get("headers", {})):
            lowered = key.lower()
            if lowered == "content-length":
                response["headers"][key] = [str(len(encoded.encode("utf-8")))]
            if lowered == "transfer-encoding":
                del response["headers"][key]

    return response


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
        "decode_compressed_response": True,
        "before_record_response": _pin_release_payload,
    }


@pytest.fixture
def temp_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture to create a temporary git repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo)
    monkeypatch.chdir(repo)
    return repo
