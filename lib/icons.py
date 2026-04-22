"""Inline SVG icon library (Lucide subset).

We ship Lucide icons as inline SVG strings rather than pulling in a JS
dependency or a CDN, because:
  1. Streamlit doesn't have a clean native icon system; HTML injection is
     the path that already works for the rest of the design.
  2. Inlined SVG renders instantly with no network round-trip.
  3. currentColor + stroke-width parameters mean every icon picks up its
     parent element's color naturally -- consistent with the rest of the
     CSS-token system.

The SVG paths are taken verbatim from Lucide (https://lucide.dev,
ISC-licensed). All icons share the canonical Lucide attributes:
  viewBox=0 0 24 24, fill=none, stroke=currentColor, stroke-width=2,
  stroke-linecap=round, stroke-linejoin=round.

Use:
    from lib.icons import icon
    html = icon("sparkles", size=20)
    html = icon("send", size=16, stroke=1.6)
    html = icon("linkedin", size=18, color="#FFFFFF")
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Path data, indexed by name. Keep alphabetical for easy scanning.
# ---------------------------------------------------------------------------

_PATHS: dict[str, str] = {
    # Status / system
    "alert-circle": (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="12" x2="12" y1="8" y2="12"/>'
        '<line x1="12" x2="12.01" y1="16" y2="16"/>'
    ),
    "arrow-right": (
        '<path d="M5 12h14"/>'
        '<path d="m12 5 7 7-7 7"/>'
    ),
    "bell-ring": (
        '<path d="M10.268 21a2 2 0 0 0 3.464 0"/>'
        '<path d="M22 8c0-2.3-.8-4.3-2-6"/>'
        '<path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"/>'
        '<path d="M4 2C2.8 3.7 2 5.7 2 8"/>'
    ),
    "book-open": (
        '<path d="M12 7v14"/>'
        '<path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>'
    ),
    "check-circle": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="m9 12 2 2 4-4"/>'
    ),
    "chevron-right": (
        '<path d="m9 18 6-6-6-6"/>'
    ),
    "copy": (
        '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>'
        '<path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>'
    ),
    "external-link": (
        '<path d="M15 3h6v6"/>'
        '<path d="M10 14 21 3"/>'
        '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    ),
    "file-text": (
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
        '<path d="M10 9H8"/>'
        '<path d="M16 13H8"/>'
        '<path d="M16 17H8"/>'
    ),
    "linkedin": (
        '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>'
        '<rect width="4" height="12" x="2" y="9"/>'
        '<circle cx="4" cy="4" r="2"/>'
    ),
    "loader-2": (  # "spinning loader" -- caller adds rotate animation
        '<path d="M21 12a9 9 0 1 1-6.219-8.56"/>'
    ),
    "mail": (
        '<rect width="20" height="16" x="2" y="4" rx="2"/>'
        '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>'
    ),
    "message-square-warning": (
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
        '<path d="M12 7v2"/>'
        '<path d="M12 13h.01"/>'
    ),
    "music": (
        '<path d="M9 18V5l12-2v13"/>'
        '<circle cx="6" cy="18" r="3"/>'
        '<circle cx="18" cy="16" r="3"/>'
    ),
    "play-circle": (
        '<circle cx="12" cy="12" r="10"/>'
        '<polygon points="10 8 16 12 10 16 10 8"/>'
    ),
    "refresh-ccw": (
        '<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>'
        '<path d="M3 3v5h5"/>'
        '<path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>'
        '<path d="M16 16h5v5"/>'
    ),
    "send": (
        '<path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"/>'
        '<path d="m21.854 2.147-10.94 10.939"/>'
    ),
    "sparkles": (
        '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>'
        '<path d="M5 3v4"/>'
        '<path d="M19 17v4"/>'
        '<path d="M3 5h4"/>'
        '<path d="M17 19h4"/>'
    ),
    "target": (
        '<circle cx="12" cy="12" r="10"/>'
        '<circle cx="12" cy="12" r="6"/>'
        '<circle cx="12" cy="12" r="2"/>'
    ),
    "upload-cloud": (
        '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>'
        '<path d="M12 12v9"/>'
        '<path d="m16 16-4-4-4 4"/>'
    ),
    "wand-sparkles": (
        '<path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72"/>'
        '<path d="m14 7 3 3"/>'
        '<path d="M5 6v4"/>'
        '<path d="M19 14v4"/>'
        '<path d="M10 2v2"/>'
        '<path d="M7 8H3"/>'
        '<path d="M21 16h-4"/>'
        '<path d="M11 3H9"/>'
    ),
}


def icon(
    name: str,
    *,
    size: int = 16,
    color: str = "currentColor",
    stroke: float = 2.0,
    css_class: str = "",
) -> str:
    """Return an inline SVG string for the given Lucide icon.

    Args:
        name:        icon key from _PATHS (e.g. "sparkles", "linkedin").
        size:        pixel width/height (kept square -- 24x24 viewBox).
        color:       stroke color. "currentColor" inherits from parent CSS.
        stroke:      stroke-width in viewBox units (1.5 - 2.0 reads cleanly).
        css_class:   optional class(es) on the <svg> for hover/animation hooks.

    Returns "" for unknown names so callers can fall back gracefully.
    """
    paths = _PATHS.get(name)
    if not paths:
        return ""
    cls_attr = f' class="symphony-icon {css_class}"'.rstrip() if css_class else ' class="symphony-icon"'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round"'
        f'{cls_attr} aria-hidden="true" focusable="false" '
        f'style="display:inline-block;vertical-align:middle;flex-shrink:0;">{paths}</svg>'
    )


def known_icons() -> list[str]:
    """Return the sorted list of icon names available in this build."""
    return sorted(_PATHS.keys())
