from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString, Tag
from docutils import nodes

# Mapping from GitHub alert classes to Sphinx admonition types
ALERT_TYPE_MAP = {
    "markdown-alert-note": "note",
    "markdown-alert-tip": "tip",
    "markdown-alert-important": "important",
    "markdown-alert-warning": "warning",
    "markdown-alert-caution": "caution",
}


def convert_alerts_to_admonitions(html: str) -> list[nodes.Node]:
    """
    Parse HTML and convert GitHub markdown alerts to Sphinx admonitions.

    Returns a list of docutils nodes - either raw HTML nodes or admonition nodes.
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    result_nodes: list[nodes.Node] = []

    # Process top-level elements
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
                if cls in ALERT_TYPE_MAP:
                    alert_type = ALERT_TYPE_MAP[cls]
                    break

        if alert_type:
            # Convert to Sphinx admonition
            admonition = create_admonition_node(element, alert_type)
            result_nodes.append(admonition)
        else:
            # Keep as raw HTML
            result_nodes.append(nodes.raw(text=str(element), format="html"))

    return result_nodes


def create_admonition_node(element: Tag, admonition_type: str) -> nodes.admonition:
    """Create a Sphinx admonition node from a GitHub alert element."""
    # Create the admonition node
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
            continue  # Skip the title element

        # Add content as raw HTML (preserves formatting)
        admonition += nodes.raw(text=str(child), format="html")

    return admonition
