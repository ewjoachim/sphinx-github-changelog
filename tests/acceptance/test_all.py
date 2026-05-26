from __future__ import annotations

import pytest

from sphinx_github_changelog import credentials, exceptions


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
    assert "Released on" in received
    assert "https://github.com/ewjoachim/sphinx-github-changelog/releases/tag/" in (
        received
    )


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
