#!/usr/bin/env python3
"""Manual integration script for the LinkedIn Copy + Open Composer flow.

WARNING -- This is NOT a unit test. It is a manual smoke-runner that writes
to your system clipboard and opens LinkedIn's compose page in your default
browser. macOS only (uses pbcopy). It is intentionally named test_*.py for
historical reasons but pytest will skip it (no test_* function defined).
DO NOT run during the demo -- it overwrites the clipboard and pops a tab.

Run only when manually verifying clipboard + browser plumbing:
    python3 tests/test_linkedin.py

For fast pure-function unit tests, see tests/test_textutils.py.
"""
import re
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "output" / "Whitepaper - True Enterprise Cost of Regulatory Fines" / "linkedin-narsingh.md"
LINKEDIN_COMPOSE_URL = "https://www.linkedin.com/feed/?shareActive=true"


def strip_yaml_frontmatter(text: str) -> str:
    """Remove YAML frontmatter block (--- ... ---) from the top."""
    if text.lstrip().startswith("---"):
        text = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.DOTALL)
    return text.strip()


def copy_to_clipboard_macos(text: str) -> None:
    """Copy text to macOS clipboard via pbcopy."""
    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)


def main() -> int:
    if not SAMPLE.exists():
        print(f"Sample LinkedIn post not found: {SAMPLE}")
        print("Run the Symphony pipeline first (Cursor: 'symphony, compose magic')")
        return 1

    raw = SAMPLE.read_text(encoding="utf-8")
    clean = strip_yaml_frontmatter(raw)

    print("=" * 60)
    print("LINKEDIN POST PREVIEW")
    print("=" * 60)
    print(clean[:300] + ("..." if len(clean) > 300 else ""))
    print("=" * 60)
    print(f"Total length: {len(clean)} characters")

    copy_to_clipboard_macos(clean)
    print("\n[OK] Post copied to clipboard")

    webbrowser.open(LINKEDIN_COMPOSE_URL)
    print(f"[OK] Opened {LINKEDIN_COMPOSE_URL}")
    print("\nNext: paste (Cmd+V) into the LinkedIn composer and click Post.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
