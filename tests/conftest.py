import os

import pytest
from sphinx.testing.path import path

pytest_plugins = "sphinx.testing.fixtures"


@pytest.fixture(scope="session")
def rootdir():
    return path(__file__).parent.abspath() / "roots"


@pytest.fixture(autouse=True)
def env():
    old_env = os.environ.copy()
    os.environ.pop("SPHINX_GITHUB_CHANGELOG_TOKEN", None)
    yield os.environ
    os.environ.clear()
    os.environ.update(old_env)
