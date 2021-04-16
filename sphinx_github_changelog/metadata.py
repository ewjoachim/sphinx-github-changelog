import sys
from typing import Mapping

if sys.version_info[:2] >= (3, 8):  # pragma: no cover
    import importlib.metadata as importlib_metadata
else:  # pragma: no cover
    import importlib_metadata


def extract_metadata() -> Mapping[str, str]:

    # Backport of Python 3.8's future importlib.metadata()
    metadata = importlib_metadata.metadata("sphinx-github-changelog")

    return {
        "author": metadata["Author"],
        "email": metadata["Author-email"],
        "license": metadata["License"],
        "url": metadata["Home-page"],
        "version": metadata["Version"],
    }
