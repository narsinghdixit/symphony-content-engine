#!/usr/bin/env python3
"""Headless visual inspection of Concerto for the agent.

Uses Playwright Python (userspace pip install, no admin) and the system's
installed Microsoft Edge (no Chromium download, no IT approval needed) to
take full-page screenshots of the Concerto UI. The screenshots get written
to /tmp/concerto_*.png so the agent can read them directly with its image
tool and visually diagnose CSS / icon / layout issues without bothering the
user for screenshots every iteration.

Usage:
    python3 tools/visual_check.py                     # all screens
    python3 tools/visual_check.py preview             # just preview
    python3 tools/visual_check.py preview idle        # specific screens

Requires:
- streamlit running on localhost:8505 (or pass --port)
- Microsoft Edge installed at /Applications/Microsoft Edge.app
- playwright python lib (pip install --user playwright)

Outputs:
- /tmp/concerto_<screen>.png  full-page screenshots
- /tmp/concerto_console.txt   captured browser console errors
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, ConsoleMessage

EDGE_PATH = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
DEFAULT_PORT = 8505
DEFAULT_VIEWPORT = {"width": 1280, "height": 1600}
SCREENS = ["preview", "preview-expanded", "idle"]   # idle requires clicking through preview


def wait_for_streamlit(page: Page, timeout_ms: int = 15000) -> None:
    """Wait for Streamlit's React app to finish hydrating + render content."""
    page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    # Streamlit injects content into <div id="root">. Wait for the wordmark or
    # any of our custom .symphony-* classes to appear.
    page.wait_for_function(
        """() => {
            const root = document.getElementById('root');
            if (!root) return false;
            // Look for our custom theme classes -- guarantees CSS injected too.
            return root.querySelector('.symphony-h1, .symphony-eyebrow, .symphony-tagline');
        }""",
        timeout=timeout_ms,
    )
    # Small extra settle so animations + fonts complete the first paint.
    page.wait_for_load_state("networkidle", timeout=timeout_ms)
    time.sleep(1.5)


def capture_screen(page: Page, name: str, port: int, console_log: list[str]) -> Path:
    """Navigate to the given screen state, screenshot it, return the path."""
    url = f"http://localhost:{port}/"
    page.goto(url, wait_until="domcontentloaded", timeout=20000)
    wait_for_streamlit(page)

    if name == "preview-expanded":
        # Click the expander to reveal the 3 Movement cards. Streamlit's
        # expander summary is the clickable element.
        page.get_by_text("The Composition · three movements").first.click(timeout=5000)
        # Wait for the cards to appear (look for "Intelligence" title).
        page.wait_for_function(
            """() => {
                const titles = document.querySelectorAll('div');
                return Array.from(titles).some(el =>
                    el.textContent === 'Intelligence' && el.children.length === 0);
            }""",
            timeout=8000,
        )
        time.sleep(1.0)

    if name == "idle":
        # Click "Take the Podium" to advance from preview -> idle.
        # The button label is exactly "Take the Podium  →".
        button = page.get_by_role("button", name="Take the Podium")
        button.first.click(timeout=5000)
        # Wait for the new page render (H1 changes to "Drop the source.").
        page.wait_for_function(
            """() => {
                const h1s = document.querySelectorAll('.symphony-h1');
                return Array.from(h1s).some(el => el.textContent.includes('Drop the source'));
            }""",
            timeout=10000,
        )
        time.sleep(1.0)

    out_path = Path("/tmp") / f"concerto_{name}.png"
    page.screenshot(path=str(out_path), full_page=True)
    print(f"[OK] {name}: {out_path} ({out_path.stat().st_size:,} bytes)")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screens", nargs="*", default=SCREENS,
                        help=f"screens to capture (default: {' '.join(SCREENS)})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"streamlit port (default: {DEFAULT_PORT})")
    parser.add_argument("--show", action="store_true",
                        help="run with browser visible (useful for debugging)")
    args = parser.parse_args()

    invalid = [s for s in args.screens if s not in SCREENS]
    if invalid:
        print(f"Unknown screens: {invalid}. Valid: {SCREENS}", file=sys.stderr)
        return 1

    if not Path(EDGE_PATH).exists():
        print(f"Microsoft Edge not found at {EDGE_PATH}", file=sys.stderr)
        return 1

    console_log: list[str] = []
    captured: list[Path] = []

    with sync_playwright() as p:
        # Use installed Edge; no Chromium download required.
        browser = p.chromium.launch(
            executable_path=EDGE_PATH,
            headless=not args.show,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )
        context = browser.new_context(
            viewport=DEFAULT_VIEWPORT,
            device_scale_factor=2,   # retina-quality screenshots
            color_scheme="dark",
        )
        page = context.new_page()

        # Capture console errors / warnings
        def on_console(msg: ConsoleMessage) -> None:
            if msg.type in ("error", "warning"):
                console_log.append(f"[{msg.type.upper()}] {msg.text}")

        page.on("console", on_console)
        page.on("pageerror", lambda e: console_log.append(f"[PAGEERROR] {e}"))

        try:
            for screen in args.screens:
                captured.append(capture_screen(page, screen, args.port, console_log))
        finally:
            console_path = Path("/tmp/concerto_console.txt")
            console_path.write_text("\n".join(console_log) if console_log else "(no console errors)\n")
            print(f"[OK] console log -> {console_path}")
            browser.close()

    print(f"\nCaptured {len(captured)} screenshot(s):")
    for p in captured:
        print(f"  {p}")
    if console_log:
        print(f"\n{len(console_log)} console message(s) recorded; see /tmp/concerto_console.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
