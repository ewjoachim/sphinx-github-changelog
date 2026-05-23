from __future__ import annotations

import dataclasses
from typing import Any, ClassVar


@dataclasses.dataclass
class ChangelogDirectiveOptions:
    changelog_url: str | None = None
    github: str | None = None
    pypi: str | None = None

    @classmethod
    def from_options(cls, options: dict[str, str]):
        return cls(
            changelog_url=options.get("changelog-url"),
            github=options.get("github"),
            pypi=options.get("pypi"),
        )


@dataclasses.dataclass
class ChangelogConfig:
    token: str | None = None
    root_repo: str | None = None
    graphql_url: str | None = None

    prefix: ClassVar[str] = "sphinx_github_changelog"

    @classmethod
    def get_field_names(cls) -> list[str]:
        return [f.name for f in dataclasses.fields(cls)]

    @classmethod
    def from_sphinx_env_config(cls, sphinx_config: Any):
        return cls(
            token=sphinx_config.sphinx_github_changelog_token,
            root_repo=sphinx_config.sphinx_github_changelog_root_repo,
            graphql_url=sphinx_config.sphinx_github_changelog_graphql_url,
        )
