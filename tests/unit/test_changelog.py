import re
import xml.dom.minidom

import pytest
import requests

from sphinx_github_changelog import changelog


@pytest.fixture
def extract_releases(mocker, release_dict):
    return mocker.patch(
        "sphinx_github_changelog.changelog.extract_releases",
        return_value=[release_dict],
    )


@pytest.fixture
def options():
    def _(kwargs):
        return {"changelog-url": None, "github": None, "pypi": None, **kwargs}

    return _


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


def test_compute_changelog_no_token(options):
    nodes = changelog.compute_changelog(token=None, options=options({}))
    assert len(nodes) == 1

    assert "Changelog was not built" in node_to_string(nodes[0])


def test_compute_changelog_token(options, extract_releases):
    nodes = changelog.compute_changelog(
        token="token", options=options({"github": "https://github.com/a/b/releases"})
    )
    assert "1.0.0: A new hope" in node_to_string(nodes[0])


def test_no_token_no_url():
    assert node_to_string(changelog.no_token(changelog_url=None)) == canonicalize(
        """
        <list>
            <warning>
                <paragraph>
                    Changelog was not built because
                    <literal>sphinx_github_changelog_token</literal>
                    parameter is missing in the documentation configuration.
                </paragraph>
            </warning>
        </list>"""
    )


def test_no_token_url():
    assert node_to_string(
        changelog.no_token(changelog_url="https://example.com")
    ) == canonicalize(
        """
        <list>
            <warning>
                <paragraph>
                    Changelog was not built because
                    <literal>sphinx_github_changelog_token</literal>
                    parameter is missing in the documentation configuration.
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
    with pytest.raises(changelog.ChangelogError):
        changelog.extract_github_repo_name("https://example.com")


@pytest.mark.parametrize(
    "url", ["https://pypi.org/project/a", "https://pypi.org/project/a/"]
)
def test_extract_pypi_package_name(url):
    assert changelog.extract_pypi_package_name(url) == "a"


def test_extract_pypi_package_name_error():
    with pytest.raises(changelog.ChangelogError):
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
