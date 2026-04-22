#!/usr/bin/env python3
"""Manual integration script for the HubSpot CMS Blog draft creation flow.

WARNING -- This is NOT a unit test. It is a manual smoke-runner that creates a
REAL draft post in your HubSpot CMS account. It is intentionally named test_*.py
for historical reasons but pytest will skip it (no test_* function defined).
DO NOT run before the demo -- it pollutes the HubSpot drafts list with
"[Symphony Test]" entries that have to be cleaned up by hand.

Run only when manually verifying the HubSpot token + scopes end-to-end:
    python3 tests/test_hubspot.py

For fast pure-function unit tests, see tests/test_textutils.py, test_runs.py,
test_hubspot_helpers.py (no API calls, no draft pollution).
"""
import re
import sys
from pathlib import Path

import markdown
import requests
import tomllib

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / ".streamlit" / "secrets.toml"
SAMPLE = ROOT / "output" / "Whitepaper - True Enterprise Cost of Regulatory Fines" / "blog-post.md"

API_BASE = "https://api.hubapi.com"


def load_secrets() -> dict:
    if not SECRETS.exists():
        print(f"Secrets not found: {SECRETS}")
        sys.exit(1)
    with open(SECRETS, "rb") as f:
        return tomllib.load(f)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def strip_yaml(md: str) -> str:
    if md.lstrip().startswith("---"):
        md = re.sub(r"^---.*?---\s*", "", md, count=1, flags=re.DOTALL)
    return md.strip()


def extract_title(md: str) -> tuple[str, str]:
    """Pull H1 title from the markdown body and return (title, body_without_title)."""
    lines = md.splitlines()
    title = "Symphony Test Blog Post"
    body_start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:]).strip()
    return title, body


def md_to_html(md: str) -> str:
    return markdown.markdown(md, extensions=["tables", "fenced_code", "extra"])


def list_blogs(token: str) -> dict:
    """List available blogs (content groups) on the HubSpot account."""
    url = f"{API_BASE}/cms/v3/blogs/posts"
    r = requests.get(url, headers=auth_headers(token), params={"limit": 1}, timeout=30)
    return {"status": r.status_code, "body": r.json() if r.text else {}}


def get_blog_groups(token: str) -> list[dict]:
    """Get distinct contentGroupIds from existing posts."""
    url = f"{API_BASE}/cms/v3/blogs/posts"
    r = requests.get(url, headers=auth_headers(token), params={"limit": 50}, timeout=30)
    if r.status_code != 200:
        return []
    posts = r.json().get("results", [])
    groups: dict[str, dict] = {}
    for p in posts:
        gid = p.get("contentGroupId")
        if gid and gid not in groups:
            groups[gid] = {
                "id": gid,
                "blog_name": p.get("name", "(unknown)"),
                "domain": p.get("domain", ""),
            }
    return list(groups.values())


def create_draft_post(token: str, content_group_id: str, title: str,
                      html_body: str, meta_desc: str = "") -> dict:
    url = f"{API_BASE}/cms/v3/blogs/posts"
    payload = {
        "contentGroupId": content_group_id,
        "name": title,
        "postBody": html_body,
        "state": "DRAFT",
        "language": "en",
        "metaDescription": meta_desc[:160] if meta_desc else title[:160],
        "useFeaturedImage": False,
    }
    r = requests.post(url, headers=auth_headers(token), json=payload, timeout=30)
    return {"status": r.status_code, "body": r.json() if r.text else {}}


def main() -> int:
    secrets = load_secrets()
    token = secrets.get("HUBSPOT_ACCESS_TOKEN", "")
    if not token or "your-" in token:
        print("Missing HUBSPOT_ACCESS_TOKEN in .streamlit/secrets.toml")
        return 1

    print("Step 1: Verify token has Blog API access...")
    list_result = list_blogs(token)
    print(f"  HTTP {list_result['status']}")
    if list_result["status"] != 200:
        print(f"  Response: {list_result['body']}")
        if list_result["status"] == 401:
            print("\n[FAIL] Token rejected. Verify it was copied correctly and has 'content' scope.")
        elif list_result["status"] == 403:
            print("\n[FAIL] Token lacks 'content' scope. Edit the app and add it.")
        return 1
    total = list_result["body"].get("total", 0)
    print(f"  [OK] Token valid. Account has {total} blog posts.")

    print("\nStep 2: Discover available blogs (content groups)...")
    groups = get_blog_groups(token)
    if not groups:
        print("  [WARN] No existing blog posts found, so no contentGroupId to use.")
        print("  Symphony will need a blog to exist in HubSpot before pushing drafts.")
        print("  Workaround: create one blank post manually in HubSpot first, or")
        print("  we can hardcode a blog ID once you confirm one exists.")
        return 1
    print(f"  [OK] Found {len(groups)} blog(s):")
    for g in groups:
        print(f"    - blog_id={g['id']}  domain={g['domain']}  example_post={g['blog_name'][:60]}")

    chosen = groups[0]
    print(f"\n  Using: {chosen['id']} ({chosen['domain']})")

    if not SAMPLE.exists():
        print(f"\n[SKIP] No sample blog post found: {SAMPLE}")
        print("Token works, blog discovered. Skipping draft creation test.")
        return 0

    print("\nStep 3: Create a draft blog post in HubSpot CMS...")
    md = strip_yaml(SAMPLE.read_text(encoding="utf-8"))
    title, body_md = extract_title(md)
    body_html = md_to_html(body_md)
    title_with_marker = f"[Symphony Test] {title}"

    create_result = create_draft_post(
        token=token,
        content_group_id=chosen["id"],
        title=title_with_marker,
        html_body=body_html,
        meta_desc="Test draft created by the Symphony Content Engine.",
    )
    print(f"  HTTP {create_result['status']}")
    if create_result["status"] in (200, 201):
        body = create_result["body"]
        post_id = body.get("id", "?")
        post_url = body.get("url", "")
        portal_id = body.get("portalId", "")
        edit_url = f"https://app.hubspot.com/blog/{portal_id}/edit/{post_id}/content" if portal_id else ""
        print(f"  [OK] Draft created.")
        print(f"  Post ID: {post_id}")
        print(f"  Title: {title_with_marker}")
        if edit_url:
            print(f"  Edit in HubSpot: {edit_url}")
        if post_url:
            print(f"  Preview URL: {post_url}")
        print("\n  Verify: HubSpot > Marketing > Website > Blog > Drafts")
        return 0
    else:
        msg = create_result["body"].get("message", "")
        print(f"  [FAIL] Could not create draft: {msg}")
        print(f"  Full response: {create_result['body']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
