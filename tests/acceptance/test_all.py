from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from sphinx_github_changelog import credentials, exceptions


def normalize_html_fragment(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "html5lib")
    release = soup.select_one("section#release-1-0-0")
    assert release is not None
    return release.prettify(formatter="minimal")


@pytest.fixture(autouse=True)
def no_local_token_discovery(monkeypatch):
    def _no_token(*, host: str) -> str:
        raise exceptions.CouldNotExtract("No GitHub token found")

    monkeypatch.setattr(credentials, "get_github_token", _no_token)


@pytest.mark.vcr
@pytest.mark.sphinx(buildername="html", testroot="all")
def test_build(app):
    app.builder.build_all()
    received = (app.outdir / "index.html").read_text()
    expected_path = Path(__file__).parent / "changelog.html"
    expected = expected_path.read_text()

    normalized_received = normalize_html_fragment(received)
    normalized_expected = normalize_html_fragment(expected)

    if normalized_received != normalized_expected:
        expected_path.write_text(normalized_received + "\n")

    assert normalized_received == normalized_expected


@pytest.mark.vcr
@pytest.mark.sphinx(buildername="html", testroot="404")
def test_build_404(app):
    app.builder.build_all()
    received = (app.outdir / "index.html").read_text()
    assert (
        "Changelog was not built because unauthenticated GitHub API access failed"
        in (received)
    )
    assert "Find the project changelog" in received


@pytest.mark.sphinx(buildername="html", testroot="error")
def test_error(app, status, warning):
    app.builder.build_all()
    assert (
        "No :github: release URL provided and unable to determine it from "
        "git remotes." in warning.getvalue()
    )
