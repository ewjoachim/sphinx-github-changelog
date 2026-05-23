from __future__ import annotations


class ChangelogError(Exception):
    pass


class CouldNotExtract(ChangelogError):
    pass


class GitHubAPIError(ChangelogError):
    pass
