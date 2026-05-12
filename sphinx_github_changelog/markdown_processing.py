from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString, Tag
from docutils import nodes
from markdown_it import MarkdownIt
from mdit_py_plugins.gfm import gfm_plugin

# Mapping from GitHub alert types to Sphinx admonition types
ALERT_TYPE_MAP = {
    "note": "note",
    "tip": "tip",
    "important": "important",
    "warning": "warning",
    "caution": "caution",
}


def create_markdown_parser() -> MarkdownIt:
    """Create a markdown-it parser configured for GitHub Flavored Markdown."""
    md = MarkdownIt()
    md.use(gfm_plugin)
    return md


def render_markdown_to_html(markdown: str) -> str:
    """Render markdown to HTML using markdown-it with GFM support."""
    if not markdown or not markdown.strip():
        return ""
    md = create_markdown_parser()
    return md.render(markdown)


def convert_markdown_to_nodes(markdown: str) -> list[nodes.Node]:
    """
    Convert markdown to docutils nodes, with GitHub alerts as Sphinx admonitions.

    This function:
    1. Renders markdown to HTML using markdown-it-py with GFM support
    2. Parses the HTML and converts GitHub alert divs to Sphinx admonitions
    3. Returns a list of docutils nodes
    """
    if not markdown or not markdown.strip():
        return []

    html = render_markdown_to_html(markdown)
    return _convert_html_to_nodes(html)


def _convert_html_to_nodes(html: str) -> list[nodes.Node]:
    """Parse HTML and convert GitHub markdown alerts to Sphinx admonitions."""
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    result_nodes: list[nodes.Node] = []

    for element in soup.children:
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if text:
                result_nodes.append(nodes.raw(text=str(element), format="html"))
            continue

        if not isinstance(element, Tag):
            continue

        classes = element.get("class", [])

        # Check if this is a GitHub alert
        alert_type = None
        if "markdown-alert" in classes:
            for cls in classes:
                if cls.startswith("markdown-alert-") and cls != "markdown-alert":
                    type_name = cls.replace("markdown-alert-", "")
                    if type_name in ALERT_TYPE_MAP:
                        alert_type = ALERT_TYPE_MAP[type_name]
                        break

        if alert_type:
            admonition = _create_admonition_node(element, alert_type)
            result_nodes.append(admonition)
        else:
            result_nodes.append(nodes.raw(text=str(element), format="html"))

    return result_nodes


def _create_admonition_node(element: Tag, admonition_type: str) -> nodes.admonition:
    """Create a Sphinx admonition node from a GitHub alert element."""
    admonition = nodes.admonition(classes=[admonition_type])

    # Add title
    title = nodes.title(text=admonition_type.capitalize())
    admonition += title

    # Extract content (skip the .markdown-alert-title paragraph)
    for child in element.children:
        if isinstance(child, NavigableString):
            continue
        if not isinstance(child, Tag):
            continue
        classes = child.get("class", [])
        if "markdown-alert-title" in classes:
            continue

        # Add content as raw HTML
        admonition += nodes.raw(text=str(child), format="html")

    return admonition
