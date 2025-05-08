from __future__ import annotations

import importlib.metadata
import os

from sphinx_github_changelog import changelog

__all__: list = []


def version() -> str:
    return importlib.metadata.version("sphinx-github-changelog")


def setup(app):
    token_name = "sphinx_github_changelog_token"
    app.add_config_value(
        name=token_name, default=os.environ.get(token_name.upper()), rebuild="html"
    )
    root_repo_name = "sphinx_github_changelog_root_repo"
    app.add_config_value(
        name=root_repo_name,
        default=os.environ.get(root_repo_name.upper()),
        rebuild="html",
    )
    graphql_url_name = "sphinx_github_changelog_graphql_url"
    app.add_config_value(
        name=graphql_url_name,
        default=os.environ.get(graphql_url_name.upper()),
        rebuild="html",
    )

    app.add_directive("changelog", changelog.ChangelogDirective)

    return {
        "version": version(),
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
