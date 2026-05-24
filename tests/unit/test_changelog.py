from __future__ import annotations

import re
import xml.dom.minidom

import pytest

from sphinx_github_changelog import changelog, credentials, exceptions
from sphinx_github_changelog import config as config_module


@pytest.fixture
def extract_releases(mocker, release):
    return mocker.patch(
        "sphinx_github_changelog.github_releases.extract_releases",
        return_value=[release],
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
    def raise_no_token(host):
        raise exceptions.CouldNotExtract("No GitHub token found")

    monkeypatch.setattr(credentials, "get_github_token", raise_no_token)
    options = config_module.ChangelogDirectiveOptions(
        github="https://github.com/a/b/releases",
    )
    config = config_module.ChangelogConfig()
    nodes = changelog.compute_changelog(options=options, config=config)
    assert "Changelog was not built" in node_to_string(nodes[0])


def test_compute_changelog_no_url(temp_git):
    with pytest.raises(
        exceptions.ChangelogError,
        match=(
            r"^No :github: release URL provided and unable to determine it from "
            r"git remotes. "
        ),
    ):
        options = config_module.ChangelogDirectiveOptions()
        config = config_module.ChangelogConfig()
        changelog.compute_changelog(options=options, config=config)


def test_compute_changelog_token(extract_releases):
    options = config_module.ChangelogDirectiveOptions(
        github="https://github.com/a/b/releases",
    )
    config = config_module.ChangelogConfig(token="token")
    nodes = changelog.compute_changelog(options=options, config=config)
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
    "url", ["https://pypi.org/project/a", "https://pypi.org/project/a/"]
)
def test_extract_pypi_package_name(url):
    assert changelog.extract_pypi_package_name(url) == "a"


def test_extract_pypi_package_name_error():
    with pytest.raises(
        exceptions.ChangelogError, match=r"^Changelog needs a PyPI project URL"
    ):
        changelog.extract_pypi_package_name("https://example.com")


def test_node_for_release_no_pypi(release):
    assert node_to_string(
        changelog.node_for_release(release=release, pypi_name=None)
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
            <paragraph>yay</paragraph>
        </section>"""
    )


def test_node_for_release_title_tag(release):
    release.name = "Bla 1.0.0"
    assert "<title>Bla 1.0.0</title>" in node_to_string(
        changelog.node_for_release(release=release, pypi_name=None)
    )


def test_node_for_release_none_title(release):
    release.name = None
    assert "<title>1.0.0</title>" in node_to_string(
        changelog.node_for_release(release=release, pypi_name=None)
    )


def test_node_for_release_title_pypy(release):
    value = node_to_string(changelog.node_for_release(release=release, pypi_name="foo"))

    assert (
        """<reference refuri="https://pypi.org/project/foo/1.0.0/">PyPI</reference>"""
        in value
    )


def test_node_for_release_draft(release):
    release.is_draft = True
    assert changelog.node_for_release(release=release, pypi_name="foo") is None


@pytest.mark.parametrize(
    "title, tag, expected",
    [
        ("Foo", "1.0.0", "1.0.0: Foo"),
        ("1.0.0: Foo", "1.0.0", "1.0.0: Foo"),
        ("Fix 1.0.0", "1.0.1", "1.0.1: Fix 1.0.0"),
        (None, "1.0.0", "1.0.0"),
        ("Foo", "v1.0.0", "1.0.0: Foo"),
        ("1.0.0: Foo", "v1.0.0", "1.0.0: Foo"),
        (None, "v1.0.0", "1.0.0"),
    ],
)
def test_get_release_title(title, tag, expected):
    assert changelog.get_release_title(title=title, tag=tag) == expected


def test_get_token_from_env(monkeypatch):
    monkeypatch.setenv("SPHINX_GITHUB_CHANGELOG_TOKEN", "testtoken")
    assert credentials.get_token_from_env() == "testtoken"
    monkeypatch.delenv("SPHINX_GITHUB_CHANGELOG_TOKEN", raising=False)
    assert credentials.get_token_from_env() is None


ALERT_MARKDOWN = """Regular content

> [!NOTE]
> This is a note.
"""


def test_converts_alerts_by_default(release):
    release.description = ALERT_MARKDOWN
    result = changelog.node_for_release(release=release, pypi_name=None)
    result_str = node_to_string(result)
    assert "<note>" in result_str


def test_preserves_non_alert_content(release):
    release.description = ALERT_MARKDOWN
    result = changelog.node_for_release(release=release, pypi_name=None)
    result_str = node_to_string(result)
    # Regular content should still be present
    assert "Regular content" in result_str


def test_convert_markdown_to_nodes_empty():
    assert changelog.convert_markdown_to_nodes(None) == []
    assert changelog.convert_markdown_to_nodes("") == []
    assert changelog.convert_markdown_to_nodes("   ") == []
