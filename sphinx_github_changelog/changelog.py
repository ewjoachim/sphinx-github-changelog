from typing import Any, Dict, Iterable, List, Optional

import requests
from docutils import nodes
from docutils.parsers.rst import Directive, directives


class ChangelogError(Exception):
    pass


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

    def run(self) -> Iterable[nodes.Node]:
        config = self.state.document.settings.env.config
        try:
            return compute_changelog(
                token=config.sphinx_github_changelog_token, options=self.options
            )
        except ChangelogError as exc:
            raise self.error(str(exc))


def compute_changelog(
    token: Optional[str], options: Dict[str, str]
) -> Iterable[nodes.Node]:
    if not token:
        return no_token(changelog_url=options["changelog-url"])

    owner_repo = extract_github_repo_name(url=options["github"])
    releases = extract_releases(owner_repo=owner_repo, token=token)

    pypi_name = extract_pypi_package_name(url=options.get("pypi"))

    result_nodes: List[nodes.Node] = []
    for release in releases:
        result_nodes.append(nodes_for_release(release=release, pypi_name=pypi_name))

    return result_nodes


def no_token(changelog_url: Optional[str]) -> Iterable[nodes.Node]:
    par = nodes.paragraph()
    par += nodes.Text("Changelog was not built because ")
    par += nodes.literal("", "sphinx_github_changelog_token")
    par += nodes.Text(" parameter is missing in the documentation configuration.")
    result = [nodes.warning("", par)]

    if changelog_url:
        par2 = nodes.paragraph()
        par2 += nodes.Text("Find the project changelog ")
        par2 += nodes.reference("", "here", refuri=changelog_url)
        par2 += nodes.Text(".")
        result.append(nodes.tip("", par2))

    return result


def extract_github_repo_name(url: str) -> str:
    stripped_url = url.rstrip("/")
    prefix, postfix = "https://github.com/", "/releases"
    url_is_correct = stripped_url.startswith(prefix) and stripped_url.endswith(postfix)
    if not url_is_correct:
        raise ChangelogError(
            "Changelog needs a Github releases URL "
            f"(https://github.com/:owner/:repo/releases). Received {url}"
        )

    return stripped_url[len(prefix) : -len(postfix)]


def extract_pypi_package_name(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    stripped_url = url.rstrip("/")
    prefix = "https://pypi.org/project/"
    url_is_correct = stripped_url.startswith(prefix)
    if not url_is_correct:
        raise ChangelogError(
            "Changelog needs a Github releases URL "
            f"(https://github.com/:owner/:repo/releases). Received {url}"
        )

    return stripped_url[len(prefix) :]  # noqa


def nodes_for_release(
    release: Dict[str, Any], pypi_name: Optional[str] = None
) -> Iterable[nodes.Node]:

    tag = release["tagName"]
    title = release["name"]
    date = release["publishedAt"][:10]
    title = title if tag in title else f"{tag}: {title}"

    # Section
    id_section = nodes.make_id("release-" + tag)
    section = nodes.section(ids=[id_section])

    section += nodes.title(text=title)

    subtitle = nodes.emphasis()
    subtitle += nodes.Text(f"Released on {date} - ")

    # Links
    subtitle += nodes.reference("", "GitHub", refuri=release["url"])
    if pypi_name:
        subtitle += nodes.Text(" - ")
        url = "https://pypi.org/project/" f"{pypi_name}/{tag}/"
        subtitle += nodes.reference("", "PyPI", refuri=url)

    subtitle_paragraph = nodes.paragraph()
    subtitle_paragraph += subtitle
    section += subtitle_paragraph

    # Body
    section += nodes.raw(text=release["descriptionHTML"], format="html")
    return section


def extract_releases(owner_repo: str, token: str) -> Iterable[Dict[str, Any]]:
    session = requests.Session()

    # Necessary for GraphQL
    session.headers["Authorization"] = f"token {token}"
    owner, repo = owner_repo.split("/")
    query = """
    query {
        repository(owner: "%(owner)s", name: "%(repo)s") {
            releases(orderBy: {field: CREATED_AT, direction: DESC}, first:100) {
                nodes {
                    name, descriptionHTML, url, tagName, publishedAt
                }
            }
        }
    }
    """ % {
        "owner": owner,
        "repo": repo,
    }
    query = query.replace("\n", "")

    url = "https://api.github.com/graphql"

    try:
        response = session.post(url, json={"query": query})
        response.raise_for_status()
        return response.json()["data"]["repository"]["releases"]["nodes"]
    except requests.HTTPError as exc:
        error = response.json()
        raise ChangelogError(
            "Could not retrieve changelog from github: " + error["message"]
        ) from exc
    except requests.RequestException as exc:
        raise ChangelogError(
            "Could not retrieve changelog from github: " + str(exc)
        ) from exc
