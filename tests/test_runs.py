"""Unit tests for lib.runs (the magic-link approval state machine).

Covers the entire round-trip used by the approval flow:
  1. new_token() generates a unique, URL-safe token
  2. write_run() persists the run as awaiting approval
  3. load_run() reads it back unchanged
  4. is_approved() reflects the un-approved state
  5. mark_approved() flips the state
  6. is_approved() now reflects the approved state
  7. Replays of mark_approved are idempotent
  8. prune_stale_runs() correctly deletes old runs and preserves fresh ones

Each test points lib.runs.RUNS_DIR at a tmp_path so we never touch the real
runs/ directory.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from lib import runs


@pytest.fixture(autouse=True)
def isolated_runs_dir(tmp_path, monkeypatch):
    """Every test in this file gets its own throwaway runs directory."""
    monkeypatch.setattr(runs, "RUNS_DIR", tmp_path)
    yield tmp_path


def _sample_payload(stem: str = "test-source"):
    return {
        "source_stem": stem,
        "source_md": "# Test\n\nSome body.",
        "debate_history": [
            {"agent_id": "maya", "content": "Brand argument", "elapsed": 12.3},
            {"agent_id": "marcus", "content": "Pipeline argument", "elapsed": 11.8},
        ],
        "synth_brief": "# Campaign Brief\n\nSterling's call.",
    }


# ---------------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------------

def test_new_token_is_unique():
    """Successive tokens must not collide (sanity check on the secrets module)."""
    tokens = {runs.new_token() for _ in range(50)}
    assert len(tokens) == 50


def test_new_token_is_url_safe():
    """Magic-link tokens go in URL query params -- no '/', '+', '=' chars."""
    for _ in range(20):
        tok = runs.new_token()
        assert tok
        assert all(c.isalnum() or c in "-_" for c in tok), f"unsafe char in {tok!r}"


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

def test_write_then_load_round_trip():
    tok = runs.new_token()
    runs.write_run(tok, **_sample_payload())
    loaded = runs.load_run(tok)
    assert loaded is not None
    assert loaded["token"] == tok
    assert loaded["source_stem"] == "test-source"
    assert loaded["synth_brief"].startswith("# Campaign Brief")
    assert loaded["approved"] is False
    assert loaded["approved_at"] is None
    assert "created_at" in loaded


def test_load_missing_run_returns_none():
    assert runs.load_run("nonexistent-token-xyz") is None


def test_load_corrupt_json_returns_none(isolated_runs_dir):
    """A malformed JSON file should not crash callers."""
    bad = isolated_runs_dir / "corrupt.json"
    bad.write_text("{ this is not valid json", encoding="utf-8")
    assert runs.load_run("corrupt") is None


# ---------------------------------------------------------------------------
# Approval state machine
# ---------------------------------------------------------------------------

def test_unapproved_after_write():
    tok = runs.new_token()
    runs.write_run(tok, **_sample_payload())
    assert runs.is_approved(tok) is False


def test_mark_approved_flips_state():
    tok = runs.new_token()
    runs.write_run(tok, **_sample_payload())
    assert runs.mark_approved(tok) is True
    assert runs.is_approved(tok) is True


def test_mark_approved_records_timestamp():
    tok = runs.new_token()
    runs.write_run(tok, **_sample_payload())
    runs.mark_approved(tok)
    loaded = runs.load_run(tok)
    assert loaded["approved_at"] is not None
    # Must be parseable as an ISO timestamp.
    parsed = datetime.fromisoformat(loaded["approved_at"])
    assert parsed.tzinfo is not None


def test_mark_approved_is_idempotent():
    """Magic-link clicks can fire twice (refresh, double-click). Don't break."""
    tok = runs.new_token()
    runs.write_run(tok, **_sample_payload())
    assert runs.mark_approved(tok) is True
    first_ts = runs.load_run(tok)["approved_at"]
    # Second mark_approved should not raise and should keep the original timestamp.
    assert runs.mark_approved(tok) is True
    second_ts = runs.load_run(tok)["approved_at"]
    assert first_ts == second_ts, "timestamp must not change on idempotent re-approve"


def test_mark_approved_unknown_token_returns_false():
    assert runs.mark_approved("never-existed") is False


def test_is_approved_unknown_token_returns_false():
    assert runs.is_approved("never-existed") is False


# ---------------------------------------------------------------------------
# TTL pruning
# ---------------------------------------------------------------------------

def test_prune_keeps_fresh_runs():
    fresh_tok = runs.new_token()
    runs.write_run(fresh_tok, **_sample_payload("fresh"))
    deleted = runs.prune_stale_runs(ttl_hours=24)
    assert deleted == 0
    assert runs.load_run(fresh_tok) is not None


def test_prune_deletes_old_runs(isolated_runs_dir):
    """Prune in isolation -- no other writes that could trigger it implicitly."""
    # Plant two runs by hand: one stale (48h old), one fresh.
    stale_path = isolated_runs_dir / "stale-test-token.json"
    fresh_path = isolated_runs_dir / "fresh-test-token.json"
    now = datetime.now(timezone.utc)
    stale_path.write_text(json.dumps({
        "token": "stale-test-token",
        "created_at": (now - timedelta(hours=48)).isoformat(),
        "source_stem": "old", "source_md": "x", "debate_history": [],
        "synth_brief": "y", "approved": False, "approved_at": None,
    }), encoding="utf-8")
    fresh_path.write_text(json.dumps({
        "token": "fresh-test-token",
        "created_at": (now - timedelta(hours=1)).isoformat(),
        "source_stem": "new", "source_md": "x", "debate_history": [],
        "synth_brief": "y", "approved": False, "approved_at": None,
    }), encoding="utf-8")

    deleted = runs.prune_stale_runs(ttl_hours=24)
    assert deleted == 1
    assert not stale_path.exists()
    assert fresh_path.exists()


def test_prune_handles_corrupt_files_gracefully(isolated_runs_dir):
    """A corrupt JSON file should not crash the prune loop or block other deletions."""
    (isolated_runs_dir / "garbage.json").write_text("not json at all", encoding="utf-8")
    fresh_tok = runs.new_token()
    runs.write_run(fresh_tok, **_sample_payload("fresh"))
    # Should not raise.
    runs.prune_stale_runs(ttl_hours=24)
    # Fresh run still readable.
    assert runs.load_run(fresh_tok) is not None


def test_write_run_triggers_opportunistic_prune(isolated_runs_dir):
    """write_run should invoke prune_stale_runs so the dir doesn't grow forever."""
    # Plant a stale run.
    stale_path = isolated_runs_dir / "stale.json"
    stale_path.write_text(
        json.dumps({
            "token": "stale",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat(),
            "source_stem": "old", "source_md": "x", "debate_history": [],
            "synth_brief": "y", "approved": False, "approved_at": None,
        }),
        encoding="utf-8",
    )

    new_tok = runs.new_token()
    runs.write_run(new_tok, **_sample_payload("new"))

    # The stale one should be gone after the new write.
    assert not stale_path.exists()
    # The new one is present and loadable.
    assert runs.load_run(new_tok) is not None
