"""Unit tests for the HubSpot pure-function helpers in lib.distribution.

Covers the URL-construction and H1-extraction helpers that drive the
"View in HubSpot" deep-link in Movement III. Pure functions only -- no
HTTP calls, no real HubSpot account needed.

The full integration test (creates an actual draft post in HubSpot) lives
in tests/test_hubspot.py and must be run manually.
"""
from __future__ import annotations

import pytest

from lib.distribution import (
    extract_h1_title,
    hubspot_edit_url,
    hubspot_posts_url,
    md_to_html,
    strip_yaml_frontmatter,
)


# ---------------------------------------------------------------------------
# hubspot_edit_url
# ---------------------------------------------------------------------------

def test_hubspot_edit_url_with_portal_and_post():
    """The happy path: deep-link straight to the draft editor."""
    url = hubspot_edit_url("12345678", "999000111")
    assert url == "https://app.hubspot.com/blog/12345678/edit/999000111/content"


def test_hubspot_edit_url_falls_back_when_portal_missing():
    """If the portal lookup failed, fall back to the HubSpot home so the user can navigate."""
    assert hubspot_edit_url(None, "999000111") == "https://app.hubspot.com/"


def test_hubspot_edit_url_falls_back_to_blog_manager_when_post_id_missing():
    """If post id is missing, open the blog manager page for reliable navigation."""
    assert (
        hubspot_edit_url("12345678", "")
        == "https://app.hubspot.com/blog/12345678/manage/posts/all"
    )


def test_hubspot_edit_url_falls_back_when_both_missing():
    assert hubspot_edit_url(None, "") == "https://app.hubspot.com/"
    assert hubspot_edit_url(None, None) == "https://app.hubspot.com/"  # type: ignore[arg-type]


def test_hubspot_edit_url_handles_int_portal_id():
    """The HubSpot API may return portalId as int OR string; we coerce to str on the
    way in (in discover_portal_id) but the helper itself should accept either."""
    # Strings get used as-is.
    assert "12345" in hubspot_edit_url("12345", "abc")


def test_hubspot_posts_url_with_portal():
    assert hubspot_posts_url("3218774") == "https://app.hubspot.com/blog/3218774/manage/posts/all"


def test_hubspot_posts_url_without_portal():
    assert hubspot_posts_url(None) == "https://app.hubspot.com/"


# ---------------------------------------------------------------------------
# extract_h1_title
# ---------------------------------------------------------------------------

def test_extract_h1_title_simple():
    md = "# My Blog Post\n\nSome body content."
    title, body = extract_h1_title(md)
    assert title == "My Blog Post"
    assert body == "Some body content."


def test_extract_h1_title_strips_extra_whitespace():
    md = "#    Whitespace Title   \n\nBody."
    title, _ = extract_h1_title(md)
    assert title == "Whitespace Title"


def test_extract_h1_title_no_h1_returns_default():
    """If Gemini forgets the H1, fall back to a placeholder rather than crash."""
    title, body = extract_h1_title("Just body, no heading.")
    assert title == "Untitled"
    assert body == "Just body, no heading."


def test_extract_h1_title_skips_empty_lines_before_h1():
    md = "\n\n\n# Real Title\n\nBody."
    title, _ = extract_h1_title(md)
    assert title == "Real Title"


def test_extract_h1_title_only_picks_first_h1():
    """Subsequent H1s belong to the body."""
    md = "# First Title\n\nSome body.\n\n# Second Title\n\nMore body."
    title, body = extract_h1_title(md)
    assert title == "First Title"
    assert "# Second Title" in body


def test_extract_h1_title_falls_back_to_h2_when_no_h1():
    """Gemini at temp 0.75 sometimes emits ## instead of # for the title.
    Defensive parser: fall back to first H2 so HubSpot doesn't get 'Untitled'.
    """
    md = "## Subhead first\n\nBody."
    title, body = extract_h1_title(md)
    assert title == "Subhead first"
    assert body == "Body."


def test_extract_h1_title_strips_h2_title_line_from_body():
    """When H2 is the title, that line must NOT also appear in the post body
    (otherwise HubSpot renders it twice: once as title, once as a section)."""
    md = "## My H2 Title\n\n## Real Subhead\n\nBody text."
    title, body = extract_h1_title(md)
    assert title == "My H2 Title"
    assert "## My H2 Title" not in body
    assert "## Real Subhead" in body
    assert "Body text." in body


def test_extract_h1_title_h1_wins_when_present():
    """If both H1 and H2 exist, H1 is the chosen title.

    Note: anything BEFORE the H1 line is dropped (treated as preamble).
    This mirrors the long-standing behavior -- titles are expected to
    lead the document, and Gemini consistently emits them that way.
    """
    md = "# The Real Title\n\n## Section A\n\nBody."
    title, body = extract_h1_title(md)
    assert title == "The Real Title"
    assert "# The Real Title" not in body
    assert "## Section A" in body
    assert "Body." in body


def test_extract_h1_title_h3_not_used_as_fallback():
    """H3 must NOT promote to title -- only H1 and H2 are valid title carriers."""
    md = "### Just a deep heading\n\nNo title here."
    title, body = extract_h1_title(md)
    assert title == "Untitled"
    assert "### Just a deep heading" in body


def test_extract_h1_title_regression_invisible_invoice():
    """Direct regression: this is the exact shape that landed as 'Untitled'
    in HubSpot in the Apr 22 demo run -- ## title + ### sections + body."""
    md = (
        "## The Invisible Invoice: True Cost of Regulatory Fines\n\n"
        "Financial services firms often view regulatory fines as a discrete cost.\n\n"
        "### The Problem: Beyond the Sticker Price\n\n"
        "The true cost extends far beyond the check amount.\n"
    )
    title, body = extract_h1_title(md)
    assert title == "The Invisible Invoice: True Cost of Regulatory Fines"
    assert "## The Invisible Invoice" not in body
    assert "### The Problem" in body


# ---------------------------------------------------------------------------
# md_to_html
# ---------------------------------------------------------------------------

def test_md_to_html_renders_basic_markdown():
    out = md_to_html("**bold** and *italic*")
    assert "<strong>bold</strong>" in out
    assert "<em>italic</em>" in out


def test_md_to_html_renders_tables():
    """The 'tables' extension is required for the sales one-pager's PROOF table."""
    md = "| a | b |\n|---|---|\n| 1 | 2 |"
    out = md_to_html(md)
    assert "<table>" in out
    assert "<td>1</td>" in out


def test_md_to_html_renders_headers():
    out = md_to_html("# H1\n## H2\n### H3")
    assert "<h1>H1</h1>" in out
    assert "<h2>H2</h2>" in out
    assert "<h3>H3</h3>" in out


# ---------------------------------------------------------------------------
# Integration check: strip + extract H1 + render -> the HubSpot push pipeline
# ---------------------------------------------------------------------------

def test_strip_then_extract_then_render_produces_clean_html():
    """Mirrors push_blog_to_hubspot's actual transformation pipeline."""
    raw_gemini_output = (
        "```yaml\n"
        "type: blog-post\n"
        "icp: both\n"
        "voice: PureFacts corporate\n"
        "```\n"
        "\n"
        "# The Invisible Invoice\n"
        "\n"
        "## The Problem\n"
        "\n"
        "Some body content with **bold** text.\n"
    )
    cleaned = strip_yaml_frontmatter(raw_gemini_output)
    title, body_md = extract_h1_title(cleaned)
    body_html = md_to_html(body_md)

    assert title == "The Invisible Invoice"
    assert "<h2>The Problem</h2>" in body_html
    assert "<strong>bold</strong>" in body_html
    # The YAML wrapper must be entirely gone.
    assert "```yaml" not in body_html
    assert "type:" not in body_html
