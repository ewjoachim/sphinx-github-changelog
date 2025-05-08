from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx(buildername="html", testroot="all")
def test_build(app, requests_mock, github_payload):
    github = requests_mock.post("https://api.github.com/graphql", json=github_payload)
    app.builder.build_all()
    expected = (Path(__file__).parent / "changelog.html").read_text()

    received = (app.outdir / "index.html").read_text()
    print(received)
    assert github.called
    query = github.request_history[0].json()["query"]
    assert query.lstrip().startswith("query {")
    assert expected in received


@pytest.mark.sphinx(buildername="html", testroot="error")
def test_error(app, status, warning):
    app.builder.build_all()
    assert (
        "Changelog needs a Github releases URL "
        "(https://wrong-url.com/:owner/:repo/releases). "
        "Received https://wrong-url.com/" in warning.getvalue()
    )
