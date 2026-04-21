"""Persistent run state for magic-link approval flow.

Each Concerto run gets a unique token and a JSON file in /runs/{token}.json.
The original Symphony tab writes the run, the email magic link reads/updates
it, and the original tab polls until approved.
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs"


def new_token() -> str:
    """Generate a URL-safe approval token."""
    return secrets.token_urlsafe(16)


def _path_for(token: str) -> Path:
    return RUNS_DIR / f"{token}.json"


def write_run(
    token: str,
    *,
    source_stem: str,
    source_md: str,
    debate_history: list[dict],
    synth_brief: str,
) -> Path:
    """Persist a fresh run as awaiting approval."""
    RUNS_DIR.mkdir(exist_ok=True)
    payload = {
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_stem": source_stem,
        "source_md": source_md,
        "debate_history": debate_history,
        "synth_brief": synth_brief,
        "approved": False,
        "approved_at": None,
    }
    path = _path_for(token)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_run(token: str) -> dict | None:
    """Read a run by token, or None if missing/invalid."""
    path = _path_for(token)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def mark_approved(token: str) -> bool:
    """Flip a run's approved flag to True. Returns True on success."""
    data = load_run(token)
    if not data:
        return False
    if data.get("approved"):
        return True
    data["approved"] = True
    data["approved_at"] = datetime.now(timezone.utc).isoformat()
    _path_for(token).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return True


def is_approved(token: str) -> bool:
    """Quick check whether a run has been approved."""
    data = load_run(token)
    return bool(data and data.get("approved"))
