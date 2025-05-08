from __future__ import annotations

import re
import xml.dom.minidom

import pytest
import requests

from sphinx_github_changelog import changelog, credentials


@pytest.fixture
def extract_releases(mocker, release_dict):
    return mocker.patch(
        "sphinx_github_changelog.changelog.extract_releases",
        return_value=[release_dict],
    )


def node_to_string(node):
    if isinstance(node, list):
        return canonicalize(
            "<list>" + "".join(node_to_string(e) for e in node) + "</list>"
        )
    return canonicalize(node.asdom().toxml())


def canonicalize(value):
    if not value.strip():
        return ""
    value = value.replace(r"""<raw format="html" xml:space="preserve">""", "")
    value = value.replace(r"""</raw>""", "")
    value = value.replace(r"""&lt;""", "<")
    value = value.replace(r"""&gt;""", ">")

    value = re.sub(r"( |\n)+", " ", value)
    value = re.sub(r" <", "<", value)
    value = re.sub(r"> ", ">", value)
    return (
        xml.dom.minidom.parseString(value)
        .toprettyxml(indent=" " * 4)
        .replace("""<?xml version="1.0" ?>\n""", "")
    )


def test_compute_changelog_no_token(monkeypatch):
    monkeypatch.setattr(credentials, "get_github_token", lambda host: None)
    nodes = changelog.compute_changelog(
        token=None, options={"github": "https://github.com/a/b/releases"}
    )
    assert "Changelog was not built" in node_to_string(nodes[0])


def test_compute_changelog_no_url(temp_git):
    with pytest.raises(
        changelog.ChangelogError,
        match=(
            r"^No :github: release URL provided and unable to determine it from "
            r"git remotes. "
        ),
    ):
        changelog.compute_changelog(token=None, options={})


def test_compute_changelog_token(extract_releases):
    nodes = changelog.compute_changelog(
        token="token", options={"github": "https://github.com/a/b/releases"}
    )
    assert "1.0.0: A new hope" in node_to_string(nodes[0])


def test_no_token_no_url():
    assert node_to_string(changelog.no_token(changelog_url=None)) == canonicalize(
        """
        <list>
            <warning>
                <paragraph>
                    Changelog was not built because no GitHub authentication token
                    was found. An access token can be provided using the
                    <literal>SPHINX_GITHUB_CHANGELOG_TOKEN</literal>
                    environment variable or the
                    <literal>sphinx_github_changelog_token</literal>
                    parameter in
                    <literal>conf.py</literal>
                    , or it can be automatically located from a configured git
                    credential helper.
                </paragraph>
            </warning>
        </list>
        """
    )


def test_no_token_url():
    assert node_to_string(
        changelog.no_token(changelog_url="https://example.com")
    ) == canonicalize(
        """
        <list>
            <warning>
                <paragraph>
                    Changelog was not built because no GitHub authentication token
                    was found. An access token can be provided using the
                    <literal>SPHINX_GITHUB_CHANGELOG_TOKEN</literal>
                    environment variable or the
                    <literal>sphinx_github_changelog_token</literal>
                    parameter in
                    <literal>conf.py</literal>
                    , or it can be automatically located from a configured git
                    credential helper.
                </paragraph>
            </warning>
            <tip>
                <paragraph>
                    Find the project changelog
                    <reference refuri="https://example.com">here</reference>
                    .
                </paragraph>
            </tip>
        </list>
        """
    )


@pytest.mark.parametrize(
    "url", ["https://github.com/a/b/releases", "https://github.com/a/b/releases/"]
)
def test_extract_github_repo_name(url):
    assert changelog.extract_github_repo_name(url) == "a/b"


def test_extract_github_repo_name_error():
    with pytest.raises(
        changelog.ChangelogError, match="^Changelog needs a Github releases URL"
    ):
        changelog.extract_github_repo_name("https://example.com")


@pytest.mark.parametrize(
    "url",
    [
        "https://git.privaterepo.com/a/b/releases",
        "https://git.privaterepo.com/a/b/releases/",
    ],
)
def test_extract_github_repo_different_root_url(url):
    with pytest.raises(
        changelog.ChangelogError, match="^Changelog needs a Github releases URL"
    ):
        changelog.extract_github_repo_name(url)

    assert (
        changelog.extract_github_repo_name(url, "https://git.privaterepo.com/") == "a/b"
    )
    assert (
        changelog.extract_github_repo_name(url, "https://git.privaterepo.com") == "a/b"
    )


@pytest.mark.parametrize(
    "url", ["https://pypi.org/project/a", "https://pypi.org/project/a/"]
)
def test_extract_pypi_package_name(url):
    assert changelog.extract_pypi_package_name(url) == "a"


def test_extract_pypi_package_name_error():
    with pytest.raises(
        changelog.ChangelogError, match="^Changelog needs a PyPI project URL"
    ):
        changelog.extract_pypi_package_name("https://example.com")


def test_node_for_release_no_pypi(release_dict):
    assert node_to_string(
        changelog.node_for_release(release=release_dict, pypi_name=None)
    ) == canonicalize(
        """
        <section ids="release-1-0-0">
            <title>1.0.0: A new hope</title>
            <paragraph>
                <emphasis>
                    Released on 2000-01-01 -
                    <reference refuri="https://example.com">GitHub</reference>
                </emphasis>
            </paragraph>
            <p>yay</p>
        </section>"""
    )


def test_node_for_release_title_tag(release_dict):
    release_dict["name"] = "Bla 1.0.0"
    assert "<title>Bla 1.0.0</title>" in node_to_string(
        changelog.node_for_release(release=release_dict, pypi_name=None)
    )


def test_node_for_release_none_title(release_dict):
    release_dict["name"] = None
    assert "<title>1.0.0</title>" in node_to_string(
        changelog.node_for_release(release=release_dict, pypi_name=None)
    )


def test_node_for_release_title_pypy(release_dict):
    value = node_to_string(
        changelog.node_for_release(release=release_dict, pypi_name="foo")
    )

    assert (
        """<reference refuri="https://pypi.org/project/foo/1.0.0/">PyPI</reference>"""
        in value
    )


def test_node_for_release_draft(release_dict):
    release_dict["isDraft"] = True
    assert changelog.node_for_release(release=release_dict, pypi_name="foo") is None


def test_extract_releases(github_payload, release_dict, mocker):
    mocker.patch(
        "sphinx_github_changelog.changelog.github_call", return_value=github_payload
    )
    assert changelog.extract_releases(owner_repo="a/b", token="token") == [
        release_dict,
    ]


def test_extract_releases_custom_graphql_url(github_payload, release_dict, mocker):
    mocker.patch(
        "sphinx_github_changelog.changelog.github_call", return_value=github_payload
    )
    assert changelog.extract_releases(
        owner_repo="a/b",
        token="token",
        graphql_url="https://git.privaterepo.com/graphql",
    ) == [
        release_dict,
    ]


def test_extract_releases_remove_none(github_payload, release_dict, mocker):
    mocker.patch(
        "sphinx_github_changelog.changelog.github_call",
        return_value={
            "data": {"repository": {"releases": {"nodes": [None, 1, None, 2]}}}
        },
    )
    assert changelog.extract_releases(owner_repo="a/b", token="token") == [1, 2]


def test_extract_releases_errors(github_payload, release_dict, mocker):
    mocker.patch(
        "sphinx_github_changelog.changelog.github_call",
        return_value={"errors": [{"message": "c"}, {"message": "d"}]},
    )
    with pytest.raises(changelog.ChangelogError) as exc_info:
        changelog.extract_releases(owner_repo="a/b", token="token")

    assert str(exc_info.value) == "GitHub API error response: \nc\nd"


def test_extract_releases_format(github_payload, release_dict, mocker):
    mocker.patch(
        "sphinx_github_changelog.changelog.github_call",
        return_value={"data": {"repository": None}},
    )
    with pytest.raises(changelog.ChangelogError) as exc_info:
        changelog.extract_releases(owner_repo="a/b", token="token")

    error = "GitHub API error unexpected format:\n{'data': {'repository': None}}"
    assert str(exc_info.value) == error


def test_github_call(requests_mock):
    url = "https://api.github.com/graphql"
    payload = {"message": "foo"}
    requests_mock.post(url, json=payload)
    assert changelog.github_call(url=url, token="token", query="") == payload


def test_github_call_http_error(requests_mock):
    url = "https://api.github.com/graphql"
    requests_mock.post(url, status_code=400, json={"message": "foo"})
    with pytest.raises(changelog.ChangelogError) as exc_info:
        changelog.github_call(url=url, token="token", query="")

    assert str(exc_info.value) == (
        "Unexpected GitHub API error status code: 400\n" """{"message": "foo"}"""
    )


def test_github_call_http_error_connection(requests_mock):
    url = "https://api.github.com/graphql"
    requests_mock.post(url, exc=requests.ConnectionError("bar"))
    with pytest.raises(changelog.ChangelogError) as exc_info:
        changelog.github_call(url=url, token="token", query="")

    assert str(exc_info.value) == "Could not retrieve changelog from github: bar"


@pytest.mark.parametrize(
    "title, tag, expected",
    [
        ("Foo", "1.0.0", "1.0.0: Foo"),
        ("1.0.0: Foo", "1.0.0", "1.0.0: Foo"),
        ("Fix 1.0.0", "1.0.1", "1.0.1: Fix 1.0.0"),
        (None, "1.0.0", "1.0.0"),
    ],
)
def test_get_release_title(title, tag, expected):
    assert changelog.get_release_title(title=title, tag=tag) == expected


def test_get_token_from_env(monkeypatch):
    monkeypatch.setenv("SPHINX_GITHUB_CHANGELOG_TOKEN", "testtoken")
    assert credentials.get_token_from_env() == "testtoken"
    monkeypatch.delenv("SPHINX_GITHUB_CHANGELOG_TOKEN", raising=False)
    assert credentials.get_token_from_env() is None
