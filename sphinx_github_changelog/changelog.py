from __future__ import annotations

from docutils import nodes
from docutils.frontend import get_default_settings
from docutils.parsers.rst import Directive, directives
from docutils.utils import new_document
from myst_parser.parsers.docutils_ import Parser

from . import config as config_module
from . import credentials, exceptions, github_releases, urls


class ChangelogDirective(Directive):
    # defines the parameter the directive expects
    # directives.unchanged means you get the raw value from RST
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "changelog-url": directives.unchanged,
        "github": directives.unchanged,
        "pypi": directives.unchanged,
    }
    has_content = False
    add_index = False

    def run(self) -> list[nodes.Node]:
        options = config_module.ChangelogDirectiveOptions.from_options(self.options)
        config = config_module.ChangelogConfig.from_sphinx_env_config(
            self.state.document.settings.env.config
        )
        try:
            return compute_changelog(options=options, config=config)
        except exceptions.ChangelogError as exc:
            raise self.error(str(exc))


def compute_changelog(
    options: config_module.ChangelogDirectiveOptions,
    config: config_module.ChangelogConfig,
) -> list[nodes.Node]:
    try:
        github_params = urls.extract_github_params(options=options, config=config)
    except exceptions.CouldNotExtract as exc:
        raise exceptions.ChangelogError(
            "No :github: release URL provided and unable to determine it from "
            "git remotes. Please provide a GitHub release URL in the format "
            "(https://github.com/:owner/:repo/releases)"
        ) from exc

    # If token is not provided, try to get it from helpers
    token = config.token
    if not token:
        try:
            token = credentials.get_github_token(host=github_params.hostname)
        except exceptions.CouldNotExtract:
            return no_token(changelog_url=options.changelog_url)

    releases = github_releases.extract_releases(
        github_params=github_params,
        token=token,
        graphql_url=config.graphql_url,
    )

    pypi_name = extract_pypi_package_name(url=options.pypi)

    if not config.include_prereleases:
        releases = [r for r in releases if not r.is_prerelease]

    result_nodes = (
        node_for_release(release=release, pypi_name=pypi_name) for release in releases
    )

    return [n for n in result_nodes if n is not None]


def no_token(changelog_url: str | None) -> list[nodes.Node]:
    par = nodes.paragraph()
    par += nodes.Text(
        "Changelog was not built because no GitHub authentication token was found. "
        "An access token can be provided using the "
    )
    par += nodes.literal("", "SPHINX_GITHUB_CHANGELOG_TOKEN")
    par += nodes.Text(" environment variable or the ")
    par += nodes.literal("", "sphinx_github_changelog_token")
    par += nodes.Text(" parameter in ")
    par += nodes.literal("", "conf.py")
    par += nodes.Text(
        ", or it can be automatically located from a configured git credential helper."
    )
    result: list[nodes.Node] = [nodes.warning("", par)]

    if changelog_url:
        par2 = nodes.paragraph()
        par2 += nodes.Text("Find the project changelog ")
        par2 += nodes.reference("", "here", refuri=changelog_url)
        par2 += nodes.Text(".")
        result.append(nodes.tip("", par2))

    return result


def extract_pypi_package_name(url: str | None) -> str | None:
    if not url:
        return None
    stripped_url = url.rstrip("/")
    prefix = "https://pypi.org/project/"
    url_is_correct = stripped_url.startswith(prefix)
    if not url_is_correct:
        raise exceptions.ChangelogError(
            "Changelog needs a PyPI project URL "
            f"(https://pypi.org/project/:project). Received {url}"
        )

    return stripped_url[len(prefix) :]


def get_release_title(title: str | None, tag: str):
    version = tag.removeprefix("v")
    if not title:
        return version
    return title if version in title else f"{version}: {title}"


def node_for_release(
    release: github_releases.Release,
    pypi_name: str | None = None,
) -> nodes.Node | None:
    if release.is_draft:
        return None  # For now, draft releases are excluded

    tag = release.tag_name
    version = tag.removeprefix("v")
    title = release.name
    date = release.published_at.isoformat()
    title = get_release_title(title=title, tag=tag)

    # Section
    id_section = nodes.make_id("release-" + version)
    section = nodes.section(ids=[id_section])

    section += nodes.title(text=title)

    subtitle = nodes.emphasis()
    subtitle += nodes.Text(f"Released on {date} - ")

    # Links
    subtitle += nodes.reference("", "GitHub", refuri=release.url)
    if pypi_name:
        subtitle += nodes.Text(" - ")
        url = f"https://pypi.org/project/{pypi_name}/{version}/"
        subtitle += nodes.reference("", "PyPI", refuri=url)

    subtitle_paragraph = nodes.paragraph()
    subtitle_paragraph += subtitle
    section += subtitle_paragraph

    section += convert_markdown_to_nodes(release.description)
    return section


def convert_markdown_to_nodes(markdown: str | None) -> list[nodes.Node]:
    """
    Convert markdown to docutils nodes
    """
    if not markdown or not markdown.strip():
        return []
    parser = Parser()
    settings = get_default_settings(parser)

    settings.myst_gfm_only = True

    settings.myst_heading_anchors = 3

    document = new_document("changelog_text", settings=settings)

    parser.parse(markdown, document)

    return document.children
