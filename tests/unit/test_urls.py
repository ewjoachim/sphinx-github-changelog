"""Test for identifying repository configuration from URLs."""

from __future__ import annotations

import pytest

from sphinx_github_changelog import exceptions, urls


@pytest.mark.parametrize(
    "url, expected_owner, expected_repo",
    [
        ("https://github.com/org/repo", "org", "repo"),
        ("https://github.enterprise.com/org/repo", "org", "repo"),
        ("https://github.com/org/repo/releases", "org", "repo"),
        ("https://github.com/org/repo/releases/", "org", "repo"),
    ],
)
def test_from_http_url(url, expected_owner, expected_repo):
    params = urls.GitHubParams.from_http_url(url)
    assert params.owner == expected_owner
    assert params.repo == expected_repo


def test_from_http_url_no_hostname():
    with pytest.raises(exceptions.CouldNotExtract, match="has no hostname"):
        urls.GitHubParams.from_http_url("not-a-url")


def test_from_http_url_no_path():
    with pytest.raises(exceptions.CouldNotExtract, match="Could not extract"):
        urls.GitHubParams.from_http_url("https://github.com/")


@pytest.mark.parametrize(
    "url, expected_hostname, expected_owner, expected_repo",
    [
        ("git@github.com:org/repo.git", "github.com", "org", "repo"),
        ("git@github.com:org/repo", "github.com", "org", "repo"),
        (
            "git@github.enterprise.com:org/repo.git",
            "github.enterprise.com",
            "org",
            "repo",
        ),
    ],
)
def test_from_ssh_url(url, expected_hostname, expected_owner, expected_repo):
    params = urls.GitHubParams.from_ssh_url(url)
    assert params.hostname == expected_hostname
    assert params.owner == expected_owner
    assert params.repo == expected_repo


def test_from_ssh_url_invalid():
    with pytest.raises(exceptions.CouldNotExtract, match="Did not recognize"):
        urls.GitHubParams.from_ssh_url("not-a-url")


def test_from_remote_urls_http():
    params = urls.GitHubParams.from_remote_urls(["https://github.com/org/repo.git"])
    assert params.owner == "org"
    assert params.repo == "repo"


def test_from_remote_urls_ssh():
    params = urls.GitHubParams.from_remote_urls(["git@github.com:org/repo.git"])
    assert params.owner == "org"
    assert params.repo == "repo"


def test_from_remote_urls_all_invalid():
    with pytest.raises(ExceptionGroup):
        urls.GitHubParams.from_remote_urls(["not-a-url", "also-not-a-url"])


def test_is_github_com():
    params = urls.GitHubParams(hostname="github.com", owner="org", repo="repo")
    assert params.is_github_com is True


def test_is_not_github_com():
    params = urls.GitHubParams(
        hostname="github.enterprise.com", owner="org", repo="repo"
    )
    assert params.is_github_com is False


def test_repo_url():
    params = urls.GitHubParams(hostname="github.com", owner="org", repo="repo")
    assert params.repo_url == "https://github.com/org/repo"


def test_graphql_url_github_com():
    params = urls.GitHubParams(hostname="github.com", owner="org", repo="repo")
    assert params.graphql_url == "https://api.github.com/graphql"


def test_graphql_url_enterprise():
    params = urls.GitHubParams(
        hostname="github.enterprise.com", owner="org", repo="repo"
    )
    assert params.graphql_url == "https://github.enterprise.com/api/graphql"
