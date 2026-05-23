from __future__ import annotations

import importlib.metadata
import os

from . import changelog, config


def version() -> str:
    return importlib.metadata.version("sphinx-github-changelog")


def setup(app):
    for name in config.ChangelogConfig.get_field_names():
        option_name = f"{config.ChangelogConfig.prefix}_{name}"
        app.add_config_value(
            name=option_name,
            default=os.environ.get(option_name.upper()),
            rebuild="html",
        )

    app.add_directive("changelog", changelog.ChangelogDirective)

    return {
        "version": version(),
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
