from __future__ import annotations

import importlib.metadata as importlib_metadata
from collections.abc import Mapping


def extract_metadata() -> Mapping[str, str]:
    metadata = importlib_metadata.metadata("sphinx-github-changelog")

    return {
        "author": metadata["Author"],
        "email": metadata["Author-email"],
        "license": metadata["License"],
        "url": metadata["Home-page"],
        "version": metadata["Version"],
    }
