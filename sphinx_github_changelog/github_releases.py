from __future__ import annotations

import dataclasses
import datetime
from collections.abc import Sequence

import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt

from . import exceptions, urls


class GitHubRateLimitError(Exception):
    """Raised internally to trigger retry logic on HTTP 429."""


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
    def from_rest(cls, data: dict) -> Release:
        published_or_created = data.get("published_at") or data.get("created_at")
        if not published_or_created:
            raise exceptions.GitHubAPIError(
                f"GitHub API error release has no publication date:\n{data!r}"
            )
        return cls(
            name=data["name"],
            description=data["body"],
            url=data["html_url"],
            tag_name=data["tag_name"],
            published_at=datetime.date.fromisoformat(published_or_created[:10]),
            is_draft=data["draft"],
            is_prerelease=data["prerelease"],
        )


def extract_releases(
    github_params: urls.GitHubParams,
    token: str | None,
    retries: int,
) -> Sequence[Release]:
    page = 1
    releases: list[Release] = []
    while True:
        result = github_call(
            url=github_params.releases_api_url,
            token=token,
            params={"per_page": 100, "page": page},
            retries=retries,
        )
        if not result:
            break
        try:
            releases.extend(Release.from_rest(r) for r in result)
        except (KeyError, TypeError) as exc:
            raise exceptions.GitHubAPIError(
                f"GitHub API error unexpected format:\n{result!r}"
            ) from exc
        page += 1

    # Sort by publication date descending
    return sorted(
        releases,
        key=lambda r: r.published_at,
        reverse=True,
    )


def github_call(
    url: str,
    token: str | None,
    params: dict[str, int],
    retries: int,
) -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    response: httpx.Response | None = None
    total_attempts = max(1, retries + 1)
    try:
        for attempt in Retrying(
            stop=stop_after_attempt(total_attempts),
            retry=retry_if_exception_type(GitHubRateLimitError),
            reraise=True,
        ):
            with attempt:
                try:
                    response = httpx.get(
                        url,
                        params=params,
                        headers=headers,
                    ).raise_for_status()
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 429:
                        raise GitHubRateLimitError(exc.response.text) from exc
                    raise

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise exceptions.GitHubAPIError(
                "GitHub API authentication failed (401 Unauthorized)."
            ) from exc
        raise exceptions.GitHubAPIError(
            f"Unexpected GitHub API error status code: {exc.response.status_code}\n"
            f"{exc.response.text}"
        ) from exc
    except GitHubRateLimitError as exc:
        raise exceptions.GitHubAPIError(
            f"GitHub API rate limited (429) after {retries} retries."
        ) from exc
    except httpx.HTTPError as exc:
        raise exceptions.GitHubAPIError(
            "Could not retrieve changelog from github: " + str(exc)
        ) from exc

    if response is None:
        raise NotImplementedError("Unreachable: retry loop completed without response")

    response_payload = response.json()
    if not isinstance(response_payload, list):
        raise exceptions.GitHubAPIError(
            f"GitHub API error unexpected format:\n{response_payload!r}"
        )
    return response_payload
