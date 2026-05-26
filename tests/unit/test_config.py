from __future__ import annotations

import dataclasses

import pytest

from sphinx_github_changelog import config


def test_get_config_defaults_int_uses_dataclass_default(monkeypatch):
    monkeypatch.delenv("SPHINX_GITHUB_CHANGELOG_RETRIES", raising=False)

    defaults = dict(config.ChangelogConfig.get_config_defaults())

    assert defaults["sphinx_github_changelog_retries"] == 3


def test_get_config_defaults_int_uses_env_value(monkeypatch):
    monkeypatch.setenv("SPHINX_GITHUB_CHANGELOG_RETRIES", "7")

    defaults = dict(config.ChangelogConfig.get_config_defaults())

    assert defaults["sphinx_github_changelog_retries"] == 7


def test_get_config_defaults_int_invalid_default_raises(monkeypatch):
    monkeypatch.delenv("SPHINX_GITHUB_CHANGELOG_RETRIES", raising=False)

    @dataclasses.dataclass
    class BrokenConfig:
        retries: int = "oops"

        prefix = "sphinx_github_changelog"

        get_config_defaults = classmethod(
            config.ChangelogConfig.get_config_defaults.__func__
        )

    with pytest.raises(TypeError, match="Unexpected default type for retries"):
        dict(BrokenConfig.get_config_defaults())
