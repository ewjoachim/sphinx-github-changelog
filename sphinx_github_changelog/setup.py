from __future__ import annotations

import importlib.metadata

from . import changelog, config


def version() -> str:
    return importlib.metadata.version("sphinx-github-changelog")


def setup(app):
    for option_name, default in config.ChangelogConfig.get_config_defaults():
        app.add_config_value(
            name=option_name,
            default=default,
            rebuild="html",
        )

    app.add_directive("changelog", changelog.ChangelogDirective)

    return {
        "version": version(),
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
