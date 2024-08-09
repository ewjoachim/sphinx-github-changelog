from typing import Any, Dict, Iterable, List, Optional

import requests
from docutils import nodes

# types-docutils (from typeshed) is usable but incomplete.
# docutils-stubs is more complete but
# https://github.com/tk0miya/docutils-stubs/issues/33
from docutils.parsers.rst import Directive, directives  # type: ignore


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

    def run(self) -> List[nodes.Node]:
        config = self.state.document.settings.env.config
        try:
            return compute_changelog(
                token=config.sphinx_github_changelog_token,
                options=self.options,
                root_url=config.sphinx_github_changelog_root_repo,
                graphql_url=config.sphinx_github_changelog_graphql_url,
            )
        except ChangelogError as exc:
            raise self.error(str(exc))


def compute_changelog(
    token: Optional[str],
    options: Dict[str, str],
    root_url: Optional[str] = None,
    graphql_url: Optional[str] = None,
) -> List[nodes.Node]:
    if not token:
        return no_token(changelog_url=options.get("changelog-url"))

    owner_repo = extract_github_repo_name(url=options["github"], root_url=root_url)
    releases = extract_releases(
        owner_repo=owner_repo, token=token, graphql_url=graphql_url
    )

    pypi_name = extract_pypi_package_name(url=options.get("pypi"))

    result_nodes = (
        node_for_release(release=release, pypi_name=pypi_name) for release in releases
    )

    return [n for n in result_nodes if n is not None]


def no_token(changelog_url: Optional[str]) -> List[nodes.Node]:
    par = nodes.paragraph()
    par += nodes.Text("Changelog was not built because ")
    par += nodes.literal("", "sphinx_github_changelog_token")
    par += nodes.Text(" parameter is missing in the documentation configuration.")
    result: List[nodes.Node] = [nodes.warning("", par)]

    if changelog_url:
        par2 = nodes.paragraph()
        par2 += nodes.Text("Find the project changelog ")
        par2 += nodes.reference("", "here", refuri=changelog_url)
        par2 += nodes.Text(".")
        result.append(nodes.tip("", par2))

    return result


def extract_github_repo_name(url: str, root_url: Optional[str] = None) -> str:
    stripped_url = url.rstrip("/")
    prefix, postfix = (
        root_url if root_url is not None else "https://github.com/",
        "/releases",
    )
    if not prefix.endswith("/"):
        prefix += "/"
    url_is_correct = stripped_url.startswith(prefix) and stripped_url.endswith(postfix)
    if not url_is_correct:
        raise ChangelogError(
            "Changelog needs a Github releases URL "
            f"({prefix}:owner/:repo/releases). Received {url}"
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
            "Changelog needs a PyPI project URL "
            f"(https://pypi.org/project/:project). Received {url}"
        )

    return stripped_url[len(prefix) :]  # noqa


def get_release_title(title: Optional[str], tag: str):
    if not title:
        return tag
    return title if tag in title else f"{tag}: {title}"


def node_for_release(
    release: Dict[str, Any], pypi_name: Optional[str] = None
) -> Optional[nodes.Node]:
    if release["isDraft"]:
        return None  # For now, draft releases are excluded

    tag = release["tagName"]
    title = release["name"]
    date = release["publishedAt"][:10]
    title = get_release_title(title=title, tag=tag)

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


def extract_releases(
    owner_repo: str, token: str, graphql_url: Optional[str] = None
) -> Iterable[Dict[str, Any]]:
    # Necessary for GraphQL
    owner, repo = owner_repo.split("/")
    query = """
    query {{
        repository(owner: "{owner}", name: "{repo}") {{
            releases(orderBy: {{field: CREATED_AT, direction: DESC}}, first:100) {{
                nodes {{
                    name, descriptionHTML, url, tagName, publishedAt, isDraft
                }}
            }}
        }}
    }}
    """.format(
        owner=owner,
        repo=repo,
    )
    full_query = {"query": query.replace("\n", "")}

    url = "https://api.github.com/graphql" if graphql_url is None else graphql_url

    try:
        result = github_call(url=url, query=full_query, token=token)
        if "errors" in result:
            raise ChangelogError(
                "GitHub API error response: \n"
                + "\n".join(e.get("message", str(e)) for e in result["errors"])
            )

        releases = result["data"]["repository"]["releases"]["nodes"]
        # If you don't have the right to see draft releases, they're "None"
        return [r for r in releases if r]
    except (KeyError, TypeError):
        raise ChangelogError(f"GitHub API error unexpected format:\n{result!r}")


def github_call(url, token, query):
    try:
        response = requests.post(
            url, json=query, headers={"Authorization": f"token {token}"}
        )
        response.raise_for_status()
        # Let's not imagine if GitHub responds non-json...
        return response.json()

    except requests.HTTPError as exc:
        # GraphQL always responds 200
        raise ChangelogError(
            f"Unexpected GitHub API error status code: {response.status_code}\n"
            f"{response.text}"
        ) from exc
    except requests.RequestException as exc:
        raise ChangelogError(
            "Could not retrieve changelog from github: " + str(exc)
        ) from exc
