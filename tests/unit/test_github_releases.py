from __future__ import annotations

import httpx
import pytest

from sphinx_github_changelog import exceptions, github_releases, urls


@pytest.fixture
def github_params():
    return urls.GitHubParams(hostname="github.com", owner="a", repo="b")


def test_extract_releases(github_payload, release, github_params, httpx_mock):
    httpx_mock.add_response(
        url="https://api.github.com/graphql",
        method="POST",
        json=github_payload,
    )
    assert github_releases.extract_releases(
        github_params=github_params, token="token"
    ) == [release]


def test_extract_releases_custom_graphql_url(
    github_payload, release, github_params, httpx_mock
):
    httpx_mock.add_response(
        url="https://git.privaterepo.com/graphql",
        method="POST",
        json=github_payload,
    )
    assert github_releases.extract_releases(
        github_params=github_params,
        token="token",
        graphql_url="https://git.privaterepo.com/graphql",
    ) == [release]


def test_extract_releases_remove_none(github_params, httpx_mock, release_dict):
    release_dict_2 = release_dict.copy()
    release_dict_2["name"] = "Second"
    httpx_mock.add_response(
        url="https://api.github.com/graphql",
        method="POST",
        json={
            "data": {
                "repository": {
                    "releases": {"nodes": [None, release_dict, None, release_dict_2]}
                }
            }
        },
    )
    result = github_releases.extract_releases(
        github_params=github_params, token="token"
    )
    assert len(result) == 2


def test_extract_releases_format(github_params, httpx_mock):
    httpx_mock.add_response(
        url="https://api.github.com/graphql",
        method="POST",
        json={"data": {"repository": None}},
    )
    with pytest.raises(exceptions.GitHubAPIError) as exc_info:
        github_releases.extract_releases(github_params=github_params, token="token")

    error = "GitHub API error unexpected format:\n{'data': {'repository': None}}"
    assert str(exc_info.value) == error


def test_github_call(httpx_mock):
    url = "https://api.github.com/graphql"
    payload = {"message": "foo"}
    httpx_mock.add_response(url=url, method="POST", json=payload)
    assert (
        github_releases.github_call(url=url, token="token", payload={"query": ""})
        == payload
    )


def test_github_call_errors(httpx_mock):
    url = "https://api.github.com/graphql"
    httpx_mock.add_response(
        url=url,
        method="POST",
        json={"errors": [{"message": "c"}, {"message": "d"}]},
    )
    with pytest.raises(exceptions.GitHubAPIError) as exc_info:
        github_releases.github_call(url=url, token="token", payload={"query": ""})

    assert str(exc_info.value) == "GitHub API error response: \nc\nd"


def test_github_call_http_error(httpx_mock):
    url = "https://api.github.com/graphql"
    httpx_mock.add_response(
        url=url, method="POST", status_code=400, json={"message": "foo"}
    )
    with pytest.raises(exceptions.GitHubAPIError) as exc_info:
        github_releases.github_call(url=url, token="token", payload={"query": ""})

    assert str(exc_info.value) == (
        "Unexpected GitHub API error status code: 400\n" """{"message":"foo"}"""
    )


def test_github_call_http_error_connection(httpx_mock):
    url = "https://api.github.com/graphql"
    httpx_mock.add_exception(httpx.ConnectError("bar"), url=url, method="POST")
    with pytest.raises(exceptions.GitHubAPIError) as exc_info:
        github_releases.github_call(url=url, token="token", payload={"query": ""})

    assert str(exc_info.value) == "Could not retrieve changelog from github: bar"
