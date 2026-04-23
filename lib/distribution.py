"""Movement III: Distribution.

Action handlers for shipping each asset to its destination:
- LinkedIn: clipboard copy + open compose URL (no API)
- Gmail: send via SMTP (real)
- HubSpot CMS: push as draft blog post (real, via Blog API)
- Copy: simple clipboard target with success animation

These functions are thin wrappers that the Streamlit UI calls when
buttons are clicked. They return structured results for the UI to render.
"""
from __future__ import annotations

import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import markdown
import requests

from lib import email_sender
from lib.textutils import strip_yaml_frontmatter as _strip_yaml_canonical

LINKEDIN_COMPOSE_URL = "https://www.linkedin.com/feed/?shareActive=true"
HUBSPOT_API_BASE = "https://api.hubapi.com"
HUBSPOT_APP_BASE = "https://app.hubspot.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def strip_yaml_frontmatter(md: str) -> str:
    """Re-export of lib.textutils.strip_yaml_frontmatter for back-compat.

    Kept as a passthrough so existing call sites (app.py, composer, etc.) and
    any external scripts can keep importing from lib.distribution. The single
    canonical implementation lives in lib.textutils.
    """
    return _strip_yaml_canonical(md)


def extract_h1_title(md: str) -> tuple[str, str]:
    """Return (title, body_without_title_line).

    Lookup order:
      1. First H1 line (`# Title`)              -- canonical
      2. First H2 line (`## Title`)             -- defensive fallback for when
         Gemini emits the title at H2 level (drift-prone at temperature 0.75).
      3. "Untitled" if neither is found         -- last resort

    The matched heading line is stripped from the returned body so HubSpot
    doesn't show the title twice (once as post name, once as section heading).
    """
    lines = md.splitlines()

    h1_idx: int | None = None
    h2_idx: int | None = None
    for i, line in enumerate(lines):
        s = line.strip()
        if h1_idx is None and s.startswith("# ") and not s.startswith("## "):
            h1_idx = i
            break  # H1 wins outright; no need to keep scanning
        if h2_idx is None and s.startswith("## ") and not s.startswith("### "):
            h2_idx = i

    if h1_idx is not None:
        title = lines[h1_idx].strip()[2:].strip()
        body = "\n".join(lines[h1_idx + 1:]).strip()
        return title, body

    if h2_idx is not None:
        title = lines[h2_idx].strip()[3:].strip()
        body = "\n".join(lines[:h2_idx] + lines[h2_idx + 1:]).strip()
        return title, body

    return "Untitled", "\n".join(lines).strip()


def md_to_html(md: str) -> str:
    return markdown.markdown(md, extensions=["tables", "fenced_code", "extra"])


# ---------------------------------------------------------------------------
# LinkedIn (copy + open)
# ---------------------------------------------------------------------------


def linkedin_payload(asset_md: str) -> dict:
    """Return payload for LinkedIn copy/open action.

    Returns dict with `text` (clean post body) and `url` (compose URL).
    """
    text = strip_yaml_frontmatter(asset_md)
    return {"text": text, "url": LINKEDIN_COMPOSE_URL}


# ---------------------------------------------------------------------------
# Gmail (approval email)
# ---------------------------------------------------------------------------


def send_asset_for_approval(
    *,
    secrets,
    asset_label: str,
    asset_md: str,
    source_label: str,
) -> dict:
    """Send a single asset to the approval inbox via Gmail SMTP."""
    body_md = strip_yaml_frontmatter(asset_md)
    try:
        html, plain = email_sender.render_approval_email(
            recipient_email=secrets["APPROVAL_EMAIL"],
            asset_label=asset_label,
            source_label=source_label,
            asset_md=body_md,
            approve_url=None,
        )
        email_sender.send_email(
            gmail_address=secrets["GMAIL_ADDRESS"],
            gmail_app_password=secrets["GMAIL_APP_PASSWORD"],
            to_email=secrets["APPROVAL_EMAIL"],
            subject=f"Concerto: review {asset_label}",
            html_body=html,
            plain_body=plain,
        )
        return {"ok": True, "destination": secrets["APPROVAL_EMAIL"]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# HubSpot CMS (blog draft)
# ---------------------------------------------------------------------------


def _hubspot_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def discover_blog_id(token: str) -> str | None:
    """Find a usable HubSpot blog (contentGroupId) by inspecting recent posts."""
    url = f"{HUBSPOT_API_BASE}/cms/v3/blogs/posts"
    try:
        r = requests.get(url, headers=_hubspot_headers(token), params={"limit": 50}, timeout=30)
        if r.status_code != 200:
            return None
        posts = r.json().get("results", [])
        for p in posts:
            gid = p.get("contentGroupId")
            if gid:
                return gid
    except Exception:
        return None
    return None


@lru_cache(maxsize=4)
def discover_portal_id(token: str) -> str | None:
    """Look up the HubSpot portal (hub) ID for the account behind this token.

    Cached per-token because the portal never changes for a given account.
    Used to construct the deep-link to a draft blog post inside HubSpot's UI:
        https://app.hubspot.com/blog/{portal_id}/edit/{post_id}/content

    Returns None if the account-info endpoint fails (token lacks scope, network
    error, etc.) -- callers should fall back to https://app.hubspot.com/.
    """
    url = f"{HUBSPOT_API_BASE}/account-info/v3/details"
    try:
        r = requests.get(url, headers=_hubspot_headers(token), timeout=30)
        if r.status_code != 200:
            return None
        portal = r.json().get("portalId")
        return str(portal) if portal else None
    except Exception:
        return None


def hubspot_edit_url(portal_id: str | None, post_id: str) -> str:
    """Build the deep-link URL to edit a blog post inside HubSpot's UI."""
    if portal_id and post_id:
        return f"{HUBSPOT_APP_BASE}/blog/{portal_id}/edit/{post_id}/content"
    return hubspot_posts_url(portal_id)


def hubspot_posts_url(portal_id: str | None) -> str:
    """Build a reliable HubSpot blog manager URL for this portal."""
    if portal_id:
        return f"{HUBSPOT_APP_BASE}/blog/{portal_id}/manage/posts/all"
    return f"{HUBSPOT_APP_BASE}/"


def push_blog_to_hubspot(
    *,
    token: str,
    asset_md: str,
    blog_id: str | None = None,
    title_prefix: str = "",
) -> dict:
    """Create a draft blog post in HubSpot CMS from a markdown asset."""
    body_md = strip_yaml_frontmatter(asset_md)
    title, body_md_no_title = extract_h1_title(body_md)
    final_title = f"{title_prefix}{title}" if title_prefix else title
    body_html = md_to_html(body_md_no_title)

    if not blog_id:
        blog_id = discover_blog_id(token)
    if not blog_id:
        return {
            "ok": False,
            "error": (
                "No HubSpot blog found. Concerto pushes drafts into an existing "
                "blog (contentGroupId), but the connected HubSpot account has "
                "no blog posts yet. Fix: in HubSpot, create a blog (Marketing "
                "→ Website → Blog → New blog post → save as draft), then retry."
            ),
        }

    url = f"{HUBSPOT_API_BASE}/cms/v3/blogs/posts"
    payload = {
        "contentGroupId": blog_id,
        "name": final_title,
        "postBody": body_html,
        "state": "DRAFT",
        "language": "en",
        "metaDescription": (final_title[:155] + "...") if len(final_title) > 155 else final_title,
        "useFeaturedImage": False,
    }
    try:
        r = requests.post(url, headers=_hubspot_headers(token), json=payload, timeout=30)
        if r.status_code in (200, 201):
            data = r.json()
            post_id = data.get("id", "")
            # Try the response first, fall back to a separate account-info call.
            portal_id = data.get("portalId") or discover_portal_id(token)
            return {
                "ok": True,
                "post_id": post_id,
                "title": final_title,
                "preview_url": data.get("url", ""),
                "blog_id": blog_id,
                "portal_id": portal_id,
                "edit_url": hubspot_edit_url(portal_id, post_id),
                "manage_url": hubspot_posts_url(portal_id),
                "created_at": datetime.utcnow().isoformat(),
            }
        msg = (r.json() or {}).get("message", r.text[:200])
        return {"ok": False, "error": f"HTTP {r.status_code}: {msg}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
