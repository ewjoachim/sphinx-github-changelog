"""
Utilities for working with git remotes and GitHub URLs.

Includes functions to parse remote URLs and derive GraphQL endpoints.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import subprocess
from typing import Self
from urllib.parse import urlparse

from . import config as config_module
from . import exceptions


@dataclasses.dataclass
class GitHubParams:
    hostname: str
    owner: str
    repo: str

    @classmethod
    def from_http_url(cls, url: str) -> Self:
        parsed = urlparse(url)
        if not parsed.hostname:
            raise exceptions.CouldNotExtract(f"Configured URL ({url}) has no hostname")
        try:
            # 0 is /, and then 1, 2, ... are path elements.
            owner, repo = pathlib.PurePosixPath(parsed.path).parts[1:3]
        except ValueError as exc:
            raise exceptions.CouldNotExtract(
                f"Could not extract org and repository from URL {url}"
            ) from exc

        return cls(hostname=parsed.hostname, owner=owner, repo=repo)

    @classmethod
    def from_ssh_url(cls, url: str) -> Self:
        """Parse a git SSH remote URL into GitHubParams.

        >>> GitHubParams.from_ssh_url('git@github.com:org/repo.git')
        GitHubParams(hostname='github.com', owner='org', repo='repo')
        """
        if not (
            m := re.match(
                r"git@(?P<hostname>[^:]+):(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
                url,
            )
        ):
            raise exceptions.CouldNotExtract(
                f"Did not recognize github ssh remote url ({url})"
            )
        return cls(**m.groupdict())

    @classmethod
    def from_remote_urls(cls, urls: list[str]) -> Self:
        excs: list[exceptions.CouldNotExtract] = []
        for url in urls:
            try:
                if url.startswith("http"):
                    return cls.from_http_url(url.removesuffix(".git"))
                return cls.from_ssh_url(url)
            except exceptions.CouldNotExtract as exc:
                excs.append(exc)
                continue
        raise ExceptionGroup("All configured remotes have failed", excs)

    @property
    def is_github_com(self) -> bool:
        return self.hostname == "github.com"

    @property
    def repo_url(self) -> str:
        return f"https://{self.hostname}/{self.owner}/{self.repo}"

    @property
    def graphql_url(self) -> str:
        if self.is_github_com:
            return "https://api.github.com/graphql"
        return f"https://{self.hostname}/api/graphql"


def extract_github_params(
    options: config_module.ChangelogDirectiveOptions,
    config: config_module.ChangelogConfig,
) -> GitHubParams:
    if options.github:
        return GitHubParams.from_http_url(options.github)

    return GitHubParams.from_remote_urls(extract_remote_candidates())


def extract_remote_candidates() -> list[str]:
    """Try to get the default GitHub remote URL from git remotes.

    Prefer upstream, then origin, if these are set and represent a
    GitHub remote.
    """

    remotes = subprocess.check_output(["git", "remote", "-v"], text=True).splitlines()
    urls: dict[str, str] = {}
    for line in remotes:
        name, url, op = line.split(maxsplit=2)
        if op != "(fetch)":
            continue
        urls[name] = url

    if not urls:
        raise exceptions.CouldNotExtract("No fetch URL found in remotes")

    return [
        url
        for _, url in sorted(
            urls.items(),
            key=lambda kv: (kv[0] == "upstream", kv[0] == "origin"),
            reverse=True,
        )
    ]
