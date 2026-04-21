"""Movement IV: Distribution.

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
from pathlib import Path

import markdown
import requests

from lib import email_sender

LINKEDIN_COMPOSE_URL = "https://www.linkedin.com/feed/?shareActive=true"
HUBSPOT_API_BASE = "https://api.hubapi.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def strip_yaml_frontmatter(md: str) -> str:
    """Strip YAML frontmatter AND any outer markdown code fence from an asset.

    Handles every LLM output variation we've seen:
      1. ---\nyaml\n---\n\nbody              (clean frontmatter)
      2. ```yaml\n...\n```\n\nbody           (yaml wrapped in code fence)
      3. ```markdown\n---\n...\n---\nbody\n``` (whole asset wrapped in fence)
      4. ```md\n...\n```                     (md alias)
    """
    s = md.strip()

    # Pass 1: if the WHOLE thing is wrapped in a code fence, strip it
    fence_match = re.match(r"^```\w*\s*\n(.*)\n```\s*$", s, flags=re.DOTALL)
    if fence_match:
        s = fence_match.group(1).strip()

    # Pass 2: strip --- ... --- YAML frontmatter
    if s.startswith("---"):
        s = re.sub(r"^---.*?---\s*", "", s, count=1, flags=re.DOTALL).strip()
        return s

    # Pass 3: strip ```yaml ... ``` style YAML block (single or multi-line)
    if re.match(r"^```ya?ml", s, flags=re.IGNORECASE):
        s = re.sub(r"^```ya?ml.*?```\s*", "", s, count=1, flags=re.DOTALL | re.IGNORECASE).strip()
        return s

    return s


def extract_h1_title(md: str) -> tuple[str, str]:
    """Return (title, body_without_h1). Falls back to a default title."""
    lines = md.splitlines()
    title = "Untitled"
    body_start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            body_start = i + 1
            break
    return title, "\n".join(lines[body_start:]).strip()


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
        return {"ok": False, "error": "Could not find a HubSpot blog to publish to."}

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
            return {
                "ok": True,
                "post_id": data.get("id", ""),
                "title": final_title,
                "preview_url": data.get("url", ""),
                "blog_id": blog_id,
                "created_at": datetime.utcnow().isoformat(),
            }
        msg = (r.json() or {}).get("message", r.text[:200])
        return {"ok": False, "error": f"HTTP {r.status_code}: {msg}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
