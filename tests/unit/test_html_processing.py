from __future__ import annotations

import pytest
from docutils import nodes

from sphinx_github_changelog.html_processing import (
    ALERT_TYPE_MAP,
    convert_alerts_to_admonitions,
    create_admonition_node,
)

SAMPLE_NOTE_HTML = """
<div class="markdown-alert markdown-alert-note">
  <p class="markdown-alert-title">Note</p>
  <p>This is a note.</p>
</div>
"""

SAMPLE_MIXED_HTML = """
<p>Regular paragraph</p>
<div class="markdown-alert markdown-alert-warning">
  <p class="markdown-alert-title">Warning</p>
  <p>This is a warning.</p>
</div>
<p>Another paragraph</p>
"""

SAMPLE_MULTIPLE_ALERTS_HTML = """
<div class="markdown-alert markdown-alert-note">
  <p class="markdown-alert-title">Note</p>
  <p>First note.</p>
</div>
<div class="markdown-alert markdown-alert-tip">
  <p class="markdown-alert-title">Tip</p>
  <p>A helpful tip.</p>
</div>
"""


class TestConvertAlertsToAdmonitions:
    def test_converts_note_alert(self):
        result = convert_alerts_to_admonitions(SAMPLE_NOTE_HTML)
        assert len(result) == 1
        assert isinstance(result[0], nodes.admonition)
        assert "note" in result[0]["classes"]

    def test_preserves_non_alert_content(self):
        result = convert_alerts_to_admonitions(SAMPLE_MIXED_HTML)
        assert len(result) == 3
        assert isinstance(result[0], nodes.raw)  # Regular paragraph
        assert isinstance(result[1], nodes.admonition)  # Warning
        assert isinstance(result[2], nodes.raw)  # Another paragraph

    def test_warning_alert_has_correct_class(self):
        result = convert_alerts_to_admonitions(SAMPLE_MIXED_HTML)
        assert "warning" in result[1]["classes"]

    def test_all_alert_types(self):
        for github_class, sphinx_type in ALERT_TYPE_MAP.items():
            html = f'<div class="markdown-alert {github_class}"><p>Content</p></div>'
            result = convert_alerts_to_admonitions(html)
            assert len(result) == 1
            assert sphinx_type in result[0]["classes"]

    def test_empty_html(self):
        result = convert_alerts_to_admonitions("")
        assert result == []

    def test_whitespace_only_html(self):
        result = convert_alerts_to_admonitions("   \n\t  ")
        assert result == []

    def test_no_alerts(self):
        html = "<p>Just a paragraph</p>"
        result = convert_alerts_to_admonitions(html)
        assert len(result) == 1
        assert isinstance(result[0], nodes.raw)

    def test_multiple_alerts(self):
        result = convert_alerts_to_admonitions(SAMPLE_MULTIPLE_ALERTS_HTML)
        assert len(result) == 2
        assert isinstance(result[0], nodes.admonition)
        assert isinstance(result[1], nodes.admonition)
        assert "note" in result[0]["classes"]
        assert "tip" in result[1]["classes"]

    def test_admonition_has_title(self):
        result = convert_alerts_to_admonitions(SAMPLE_NOTE_HTML)
        admonition = result[0]
        # Find the title node
        title_nodes = [n for n in admonition.children if isinstance(n, nodes.title)]
        assert len(title_nodes) == 1
        assert title_nodes[0].astext() == "Note"

    def test_admonition_has_content(self):
        result = convert_alerts_to_admonitions(SAMPLE_NOTE_HTML)
        admonition = result[0]
        # Find raw content nodes (skip title)
        content_nodes = [n for n in admonition.children if isinstance(n, nodes.raw)]
        assert len(content_nodes) >= 1
        # Content should contain the note text
        combined_content = "".join(str(n) for n in content_nodes)
        assert "This is a note." in combined_content

    def test_alert_title_is_skipped_in_content(self):
        result = convert_alerts_to_admonitions(SAMPLE_NOTE_HTML)
        admonition = result[0]
        content_nodes = [n for n in admonition.children if isinstance(n, nodes.raw)]
        combined_content = "".join(str(n) for n in content_nodes)
        # The title paragraph should not be in the content
        assert "markdown-alert-title" not in combined_content


class TestCreateAdmonitionNode:
    def test_creates_admonition_with_correct_class(self):
        from bs4 import BeautifulSoup

        html = '<div class="markdown-alert markdown-alert-tip"><p>Content</p></div>'
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")
        admonition = create_admonition_node(element, "tip")
        assert "tip" in admonition["classes"]

    def test_title_is_capitalized(self):
        from bs4 import BeautifulSoup

        html = '<div class="markdown-alert markdown-alert-important"><p>Content</p></div>'
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")
        admonition = create_admonition_node(element, "important")
        title_nodes = [n for n in admonition.children if isinstance(n, nodes.title)]
        assert title_nodes[0].astext() == "Important"


class TestAlertTypeMap:
    def test_all_github_alert_types_covered(self):
        expected_types = {"note", "tip", "important", "warning", "caution"}
        assert set(ALERT_TYPE_MAP.values()) == expected_types

    def test_all_github_classes_have_correct_prefix(self):
        for github_class in ALERT_TYPE_MAP:
            assert github_class.startswith("markdown-alert-")
