import os

from sphinx_github_changelog import changelog
from sphinx_github_changelog import metadata as _metadata_module

__all__: list = []


_metadata = _metadata_module.extract_metadata()
__author__ = _metadata["author"]
__author_email__ = _metadata["email"]
__license__ = _metadata["license"]
__url__ = _metadata["url"]
__version__ = _metadata["version"]


def setup(app):
    token_name = "sphinx_github_changelog_token"
    app.add_config_value(
        name=token_name, default=os.environ.get(token_name.upper()), rebuild="html"
    )
    app.add_directive("changelog", changelog.ChangelogDirective)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
