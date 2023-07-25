import importlib.metadata as importlib_metadata
from typing import Mapping


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
