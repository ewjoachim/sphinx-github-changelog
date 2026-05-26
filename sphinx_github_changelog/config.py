from __future__ import annotations

import dataclasses
import os
from collections.abc import Iterator
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
    include_prereleases: bool = True
    retries: int = 3

    prefix: ClassVar[str] = "sphinx_github_changelog"

    @classmethod
    def get_config_defaults(cls) -> Iterator[tuple[str, str | bool | int | None]]:
        for field in dataclasses.fields(cls):
            option_name = f"{cls.prefix}_{field.name}"
            env_value = os.environ.get(option_name.upper())
            if field.type == "bool":
                default: str | bool | int | None = (
                    env_value.lower() not in ("0", "false", "no")
                    if env_value
                    else bool(field.default)
                )
            elif field.type == "int":
                if env_value is not None:
                    default = int(env_value)
                elif isinstance(field.default, int):
                    default = field.default
                else:
                    raise TypeError(
                        f"Unexpected default type for {field.name}: {field.default!r}"
                    )
            else:
                default = env_value
            yield option_name, default

    @classmethod
    def from_sphinx_env_config(cls, sphinx_config: Any):
        return cls(
            token=sphinx_config.sphinx_github_changelog_token,
            root_repo=sphinx_config.sphinx_github_changelog_root_repo,
            include_prereleases=sphinx_config.sphinx_github_changelog_include_prereleases,
            retries=sphinx_config.sphinx_github_changelog_retries,
        )
