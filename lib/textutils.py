"""Pure-text utilities shared across lib/ modules.

These helpers have no dependencies on Streamlit, Gemini, requests, or smtplib.
That makes them trivially unit-testable (see tests/test_textutils.py) and means
they can be imported anywhere without dragging heavy deps into the import chain.

Contents:
- strip_yaml_frontmatter(md): strip YAML/markdown code-fence wrappers from
  Gemini-emitted asset markdown, regardless of which wrapper variant Gemini
  decides to use this time.
- friendly_error(exc): translate a raw Python/Gemini/network exception into a
  one-sentence audience-safe message for on-screen error banners.
"""
from __future__ import annotations

import re


__all__ = ["strip_yaml_frontmatter", "friendly_error"]


def strip_yaml_frontmatter(md: str) -> str:
    """Strip YAML frontmatter AND any outer markdown code fence from an asset.

    Handles every Gemini output variation observed in the wild:
      1. ``---\\nyaml\\n---\\n\\nbody``                (clean YAML frontmatter)
      2. ``\\u0060\\u0060\\u0060yaml\\n...\\n\\u0060\\u0060\\u0060\\n\\nbody`` (yaml wrapped in code fence)
      3. ``\\u0060\\u0060\\u0060markdown\\n---\\n...\\n---\\nbody\\n\\u0060\\u0060\\u0060`` (whole asset wrapped in fence)
      4. ``\\u0060\\u0060\\u0060md\\n...\\n\\u0060\\u0060\\u0060``                 (md alias)
      5. plain markdown body with no wrapper                  (passthrough)

    Returns the cleaned body (no metadata, no fences, trimmed).
    """
    s = md.strip()

    # Pass 1: if the WHOLE thing is wrapped in a code fence, strip it.
    fence_match = re.match(r"^```\w*\s*\n(.*)\n```\s*$", s, flags=re.DOTALL)
    if fence_match:
        s = fence_match.group(1).strip()

    # Pass 2: strip --- ... --- YAML frontmatter at the head.
    if s.startswith("---"):
        s = re.sub(r"^---.*?---\s*", "", s, count=1, flags=re.DOTALL).strip()
        return s

    # Pass 3: strip ```yaml ... ``` style YAML block (single or multi-line).
    if re.match(r"^```ya?ml", s, flags=re.IGNORECASE):
        s = re.sub(r"^```ya?ml.*?```\s*", "", s, count=1, flags=re.DOTALL | re.IGNORECASE).strip()
        return s

    return s


def friendly_error(exc: Exception, *, fallback_prefix: str = "Concerto hit a snag") -> str:
    """Translate a raw Gemini / network exception into a one-sentence,
    audience-safe message.

    Keeps the technical detail truncated for diagnostics but leads with a
    human-readable cause so on-screen banners read calmly rather than
    ominously during a live demo. The mapping order matters -- more specific
    causes (auth, safety filter) match before generic network classifications.
    """
    raw = str(exc)
    low = raw.lower()
    if "quota" in low or "exhaust" in low or "resource_exhausted" in low or "429" in low:
        return "Gemini quota or rate limit hit. Wait a moment, then click Retry."
    if "block" in low and ("safety" in low or "filter" in low):
        return "Gemini's safety filter blocked this response. Try a different source or click Retry."
    if "timeout" in low or "timed out" in low:
        return "Network timed out talking to Gemini. Click Retry to try again."
    if "connection" in low or "network" in low or "refused" in low or "reset" in low:
        return "Network hiccup talking to Gemini. Click Retry to try again."
    if "api key" in low or "permission" in low or "unauthenticated" in low or "401" in low or "403" in low:
        return "Gemini rejected the API key. Check .streamlit/secrets.toml and restart."
    return f"{fallback_prefix}: {raw[:200]}"
