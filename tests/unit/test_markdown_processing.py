from __future__ import annotations

from docutils import nodes

from sphinx_github_changelog.markdown_processing import (
    ALERT_TYPE_MAP,
    convert_markdown_to_nodes,
    render_markdown_to_html,
)

SAMPLE_NOTE_MARKDOWN = """
> [!NOTE]
> This is a note.
"""

SAMPLE_MIXED_MARKDOWN = """
Regular paragraph

> [!WARNING]
> This is a warning.

Another paragraph
"""

SAMPLE_MULTIPLE_ALERTS_MARKDOWN = """
> [!NOTE]
> First note.

> [!TIP]
> A helpful tip.
"""


class TestRenderMarkdownToHtml:
    def test_renders_basic_markdown(self):
        html = render_markdown_to_html("# Hello")
        assert "<h1>Hello</h1>" in html

    def test_renders_alert_to_html(self):
        html = render_markdown_to_html(SAMPLE_NOTE_MARKDOWN)
        assert "markdown-alert" in html
        assert "markdown-alert-note" in html

    def test_empty_string(self):
        assert render_markdown_to_html("") == ""

    def test_whitespace_only(self):
        assert render_markdown_to_html("   \n\t  ") == ""


class TestConvertMarkdownToNodes:
    def test_converts_note_alert(self):
        result = convert_markdown_to_nodes(SAMPLE_NOTE_MARKDOWN)
        assert len(result) == 1
        assert isinstance(result[0], nodes.admonition)
        assert "note" in result[0]["classes"]

    def test_preserves_non_alert_content(self):
        result = convert_markdown_to_nodes(SAMPLE_MIXED_MARKDOWN)
        assert len(result) == 3
        assert isinstance(result[0], nodes.raw)  # Regular paragraph
        assert isinstance(result[1], nodes.admonition)  # Warning
        assert isinstance(result[2], nodes.raw)  # Another paragraph

    def test_warning_alert_has_correct_class(self):
        result = convert_markdown_to_nodes(SAMPLE_MIXED_MARKDOWN)
        assert "warning" in result[1]["classes"]

    def test_all_alert_types(self):
        for alert_type in ALERT_TYPE_MAP:
            markdown = f"> [!{alert_type.upper()}]\n> Content"
            result = convert_markdown_to_nodes(markdown)
            assert len(result) == 1
            assert ALERT_TYPE_MAP[alert_type] in result[0]["classes"]

    def test_empty_markdown(self):
        result = convert_markdown_to_nodes("")
        assert result == []

    def test_whitespace_only_markdown(self):
        result = convert_markdown_to_nodes("   \n\t  ")
        assert result == []

    def test_no_alerts(self):
        markdown = "Just a paragraph"
        result = convert_markdown_to_nodes(markdown)
        assert len(result) == 1
        assert isinstance(result[0], nodes.raw)

    def test_multiple_alerts(self):
        result = convert_markdown_to_nodes(SAMPLE_MULTIPLE_ALERTS_MARKDOWN)
        assert len(result) == 2
        assert isinstance(result[0], nodes.admonition)
        assert isinstance(result[1], nodes.admonition)
        assert "note" in result[0]["classes"]
        assert "tip" in result[1]["classes"]

    def test_admonition_has_title(self):
        result = convert_markdown_to_nodes(SAMPLE_NOTE_MARKDOWN)
        admonition = result[0]
        title_nodes = [n for n in admonition.children if isinstance(n, nodes.title)]
        assert len(title_nodes) == 1
        assert title_nodes[0].astext() == "Note"

    def test_admonition_has_content(self):
        result = convert_markdown_to_nodes(SAMPLE_NOTE_MARKDOWN)
        admonition = result[0]
        content_nodes = [n for n in admonition.children if isinstance(n, nodes.raw)]
        assert len(content_nodes) >= 1
        combined_content = "".join(str(n) for n in content_nodes)
        assert "This is a note." in combined_content


class TestAlertTypeMap:
    def test_all_github_alert_types_covered(self):
        expected_types = {"note", "tip", "important", "warning", "caution"}
        assert set(ALERT_TYPE_MAP.values()) == expected_types
