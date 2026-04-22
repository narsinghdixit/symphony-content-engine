"""Unit tests for lib.textutils.

Covers two pure functions used in demo-critical paths:
- strip_yaml_frontmatter: protects against the "raw YAML/markdown fence
  shows up in the email body or on-disk asset file" regression we already
  hit once.
- friendly_error: protects against the "Python traceback appears on screen
  during the President's demo" regression by guaranteeing the error
  classifier always returns audience-safe one-line copy.

Also asserts parity between lib.textutils.strip_yaml_frontmatter and the
back-compat re-exports in lib.distribution and lib.email_sender, so the
two callers can never silently drift apart again.
"""
from __future__ import annotations

import pytest

from lib import distribution, email_sender
from lib.textutils import friendly_error, strip_yaml_frontmatter


# ---------------------------------------------------------------------------
# strip_yaml_frontmatter -- the wrapper variants Gemini emits
# ---------------------------------------------------------------------------

STRIP_CASES = [
    pytest.param(
        "---\ntype: linkedin-post\nicp: general\n---\n\nHello body",
        "Hello body",
        id="plain-frontmatter",
    ),
    pytest.param(
        "```yaml\ntype: linkedin-post\nicp: general\n```\n\nHello body",
        "Hello body",
        id="yaml-fence",
    ),
    pytest.param(
        "```markdown\n---\ntype: blog\n---\n\nHello body\n```",
        "Hello body",
        id="markdown-wrapper-around-frontmatter",
    ),
    pytest.param(
        "```md\n---\ntype: email\n---\n\nHello body\n```",
        "Hello body",
        id="md-alias-wrapper",
    ),
    pytest.param(
        "Plain markdown with no wrapper",
        "Plain markdown with no wrapper",
        id="no-wrapper-passthrough",
    ),
    pytest.param(
        "  \n  \n```yaml\ntype: x\n```\n\nBody with leading whitespace",
        "Body with leading whitespace",
        id="leading-whitespace-tolerant",
    ),
    pytest.param(
        "---\ntype: linkedin-post\nicp: general\nwords: 150-220\nvoice: Narsingh\n---\n\n# Heading\n\nMulti-paragraph\n\nbody.",
        "# Heading\n\nMulti-paragraph\n\nbody.",
        id="frontmatter-then-h1-and-paragraphs",
    ),
]


@pytest.mark.parametrize("inp,expected", STRIP_CASES)
def test_strip_yaml_frontmatter(inp, expected):
    """Canonical implementation must strip every wrapper variant correctly."""
    assert strip_yaml_frontmatter(inp) == expected


@pytest.mark.parametrize("inp,expected", STRIP_CASES)
def test_distribution_strip_parity(inp, expected):
    """lib.distribution.strip_yaml_frontmatter must match canonical (back-compat re-export)."""
    assert distribution.strip_yaml_frontmatter(inp) == expected


@pytest.mark.parametrize("inp,expected", STRIP_CASES)
def test_email_sender_strip_parity(inp, expected):
    """lib.email_sender._strip_yaml must match canonical (used by approval emails)."""
    assert email_sender._strip_yaml(inp) == expected


def test_strip_returns_empty_for_empty_input():
    assert strip_yaml_frontmatter("") == ""
    assert strip_yaml_frontmatter("   \n  ") == ""


def test_strip_does_not_eat_inline_dashes():
    """Three dashes inside body content should not be confused with frontmatter."""
    body = "Body content\n\n---\n\nMore body after a horizontal rule."
    # No leading frontmatter marker -> body is returned as-is (rule preserved).
    assert strip_yaml_frontmatter(body) == body


# ---------------------------------------------------------------------------
# friendly_error -- the on-screen recovery banner copy
# ---------------------------------------------------------------------------

FRIENDLY_CASES = [
    # (raw exception message, fragment that must appear in friendly output)
    pytest.param("RESOURCE_EXHAUSTED quota exceeded", "quota or rate limit", id="resource-exhausted"),
    pytest.param("Error 429 Too Many Requests", "quota or rate limit", id="429"),
    pytest.param("Quota exhausted for project", "quota or rate limit", id="quota-keyword"),
    pytest.param("Response was blocked by safety filter", "safety filter blocked", id="safety-filter"),
    pytest.param("blocked due to safety", "safety filter blocked", id="safety-without-filter-keyword"),
    pytest.param("Connection timeout after 30s", "timed out", id="timeout-spelled-as-one-word"),
    pytest.param("Request timed out", "timed out", id="timed-out-phrase"),
    pytest.param("Connection refused by upstream", "Network hiccup", id="connection-refused"),
    pytest.param("Network is unreachable", "Network hiccup", id="network-unreachable"),
    pytest.param("Connection reset by peer", "Network hiccup", id="connection-reset"),
    pytest.param("API key invalid", "rejected the API key", id="api-key-invalid"),
    pytest.param("401 Unauthorized", "rejected the API key", id="401"),
    pytest.param("403 Permission denied", "rejected the API key", id="403"),
    pytest.param("UNAUTHENTICATED", "rejected the API key", id="unauthenticated"),
    pytest.param("Some random error nobody anticipated", "Concerto hit a snag", id="fallback"),
]


class _FakeExc(Exception):
    pass


@pytest.mark.parametrize("raw,must_contain", FRIENDLY_CASES)
def test_friendly_error_classification(raw, must_contain):
    """Each well-known error category must produce the expected human copy."""
    out = friendly_error(_FakeExc(raw))
    assert must_contain.lower() in out.lower(), f"got {out!r}"


def test_friendly_error_truncates_long_fallback():
    """Unknown errors get a length-capped fallback to keep banners on one line."""
    long_raw = "x" * 1000
    out = friendly_error(_FakeExc(long_raw))
    # 200-char cap on the raw + ~30 chars of "Concerto hit a snag: " prefix.
    assert len(out) < 250


def test_friendly_error_custom_prefix():
    """The fallback prefix is overridable so each call site can localize."""
    out = friendly_error(_FakeExc("weird thing"), fallback_prefix="Movement I hit a snag")
    assert out.startswith("Movement I hit a snag")


def test_friendly_error_returns_string_for_any_exception_type():
    """The classifier must never raise -- it has to be safe to call from any except."""
    for exc in [ValueError("v"), RuntimeError("r"), TypeError("t"), Exception("e")]:
        result = friendly_error(exc)
        assert isinstance(result, str)
        assert len(result) > 0
