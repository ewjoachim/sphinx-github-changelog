from pathlib import Path

import pytest


@pytest.fixture
def github(requests_mock):
    releases = [
        {
            "name": "A new hope",
            "descriptionHTML": "<p>yay</p>",
            "url": "https://example.com",
            "tagName": "1.0.0",
            "publishedAt": "2000-01-01",
        }
    ]
    gh = requests_mock.post(
        "https://api.github.com/graphql",
        request_headers={"Authorization": "token token"},
        json={"data": {"repository": {"releases": {"nodes": releases}}}},
    )
    return gh


@pytest.mark.sphinx(buildername="html", testroot="all")
def test_build(app, github):
    app.builder.build_all()
    with open(Path(__file__).parent / "changelog.html") as f:
        expected = f.read()

    received = (app.outdir / "index.html").read_text()
    print(received)
    assert github.called
    query = github.request_history[0].json()["query"]
    assert query.lstrip().startswith("query {")
    assert expected in received
