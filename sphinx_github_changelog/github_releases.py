from __future__ import annotations

import dataclasses
import datetime
from collections.abc import Sequence

import httpx

from . import exceptions, urls


@dataclasses.dataclass
class Release:
    name: str | None
    description: str | None
    url: str
    tag_name: str
    published_at: datetime.date
    is_draft: bool
    is_prerelease: bool

    @classmethod
    def from_graphql(cls, data: dict) -> Release:
        return cls(
            name=data["name"],
            description=data["description"],
            url=data["url"],
            tag_name=data["tagName"],
            published_at=datetime.date.fromisoformat(data["publishedAt"][:10]),
            is_draft=data["isDraft"],
            is_prerelease=data["isPrerelease"],
        )


def extract_releases(
    github_params: urls.GitHubParams,
    token: str,
    graphql_url: str | None = None,
) -> Sequence[Release]:
    query = """
    query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
            releases(orderBy: {field: CREATED_AT, direction: DESC}, first:100) {
                nodes {
                    name, description, url, tagName, publishedAt, isDraft, isPrerelease
                }
            }
        }
    }
    """
    payload = {
        "query": query,
        "variables": {"owner": github_params.owner, "repo": github_params.repo},
    }
    url = graphql_url or github_params.graphql_url
    result = github_call(url=url, payload=payload, token=token)
    try:
        releases = result["data"]["repository"]["releases"]["nodes"]
        # If you don't have the right to see draft releases, they're "None"
        return [Release.from_graphql(r) for r in releases if r]
    except (KeyError, TypeError):
        raise exceptions.GitHubAPIError(
            f"GitHub API error unexpected format:\n{result!r}"
        )


def github_call(url: str, token: str, payload: dict) -> dict:
    try:
        response = httpx.post(
            url, json=payload, headers={"Authorization": f"token {token}"}
        ).raise_for_status()

    except httpx.HTTPStatusError as exc:
        # GraphQL always responds 200
        raise exceptions.GitHubAPIError(
            f"Unexpected GitHub API error status code: {exc.response.status_code}\n"
            f"{exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise exceptions.GitHubAPIError(
            "Could not retrieve changelog from github: " + str(exc)
        ) from exc

    response_payload = response.json()
    if "errors" in response_payload:
        raise exceptions.GitHubAPIError(
            "GitHub API error response: \n"
            + "\n".join(e.get("message", str(e)) for e in response_payload["errors"])
        )
    return response_payload
