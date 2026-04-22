"""Agent personas and Gemini orchestration for the Intelligence layer.

Three agents:
- Maya     -- Brand Strategist (long game, authority, category leadership)
- Marcus   -- Pipeline Strategist (this quarter, meetings, pipeline velocity)
- Sterling -- Campaign Director who reads the debate and writes the brief

Displayed titles are intentionally plain ("Brand Strategist", "Pipeline
Strategist") so a Townhall audience without GTM jargon can follow. The
strategic stance is conveyed through each agent's tagline, the debate prompt
in /prompts/03-debate.md, and Sterling's synth prompt in /prompts/04-synthesize.md.
"""
from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
CONTEXT_DIR = ROOT / "context"
PROMPTS_DIR = ROOT / "prompts"

# Model selection rationale:
#   - DEBATE_MODEL = gemini-2.5-flash: latest stable general-purpose Flash text
#     model (verified Apr 2026). Used for Maya + Marcus debate turns and the
#     composer. Fast streaming, lower cost, perfect for the per-asset workload.
#     The 3.1 Flash family is currently specialized only (Lite/TTS/Image/Live);
#     no general-purpose stable 3.1 Flash text model exists yet.
#   - SYNTH_MODEL = gemini-2.5-pro: latest stable Pro with adaptive thinking.
#     Used for Sterling synthesis so the Director "thinks longer" before writing
#     the brief. Upgrade path: switch to "gemini-3.1-pro-preview" once it
#     graduates from preview to stable for additional reasoning depth.
DEBATE_MODEL = "gemini-2.5-flash"
SYNTH_MODEL = "gemini-2.5-pro"


# ---------------------------------------------------------------------------
# Agent metadata
# ---------------------------------------------------------------------------

AGENTS = {
    "maya": {
        "id": "maya",
        "name": "Maya",
        "title": "Brand Strategist",
        "tagline": "Long game. Authority. Category leadership.",
        "avatar_initial": "M",
        "avatar_class": "a",
        "model": DEBATE_MODEL,
        "stance": "brand",
    },
    "marcus": {
        "id": "marcus",
        "name": "Marcus",
        "title": "Pipeline Strategist",
        "tagline": "This quarter. Meetings. Pipeline velocity.",
        "avatar_initial": "M",
        "avatar_class": "b",
        "model": DEBATE_MODEL,
        "stance": "pipeline",
    },
    "sterling": {
        "id": "sterling",
        "name": "Sterling",
        "title": "Campaign Director",
        "tagline": "Reads the room. Writes the brief.",
        "avatar_initial": "S",
        "avatar_class": "s",
        "model": SYNTH_MODEL,
        "stance": "synth",
    },
}

DEBATE_AGENTS = ["maya", "marcus"]


# ---------------------------------------------------------------------------
# Context loading
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_context_bundle() -> str:
    """Concatenate the 5 context files into a single reference block."""
    parts = []
    for fname in ("company.md", "icp.md", "positioning.md", "competitors.md", "brand-voice.md"):
        body = _read(CONTEXT_DIR / fname)
        if body:
            parts.append(f"<<<{fname}>>>\n{body}")
    return "\n\n".join(parts)


def load_debate_prompt() -> str:
    return _read(PROMPTS_DIR / "03-debate.md")


def load_synth_prompt() -> str:
    return _read(PROMPTS_DIR / "04-synthesize.md")


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def _system_for_agent(agent_id: str, debate_prompt: str, context: str) -> str:
    """Build the system instruction for a single debate agent."""
    agent = AGENTS[agent_id]
    return (
        f"# YOU ARE {agent['name'].upper()} ({agent['title'].upper()})\n\n"
        f"{agent['tagline']}\n\n"
        f"---\n"
        f"# DEBATE PROTOCOL\n"
        f"{debate_prompt}\n\n"
        f"---\n"
        f"# YOUR PERSONA\n"
        f"You are {agent['name']}, the {agent['title']} on the PureFacts marketing team. "
        f"Your stance is **{agent['stance']}**. Argue your perspective with conviction, "
        f"backed by PureFacts positioning, ICP language, and competitive context below.\n"
        f"You are debating {('Marcus (Pipeline Strategist)' if agent_id == 'maya' else 'Maya (Brand Strategist)')}. "
        f"Address them by name. Disagree directly when you see it differently. "
        f"Stay in character.\n\n"
        f"---\n"
        f"# PUREFACTS CONTEXT (your shared knowledge base)\n"
        f"{context}"
    )


def _system_for_synth(synth_prompt: str, context: str) -> str:
    """Build the system instruction for the synthesizer."""
    return (
        f"# YOU ARE STERLING, THE CAMPAIGN DIRECTOR\n\n"
        f"You are Sterling, the Campaign Director on the PureFacts marketing team. "
        f"You read strategy debates between Maya (Brand) and Marcus (Pipeline) and produce "
        f"a final, decisive Campaign Brief that the team can execute against.\n\n"
        f"---\n"
        f"# SYNTHESIZER PROTOCOL\n"
        f"{synth_prompt}\n\n"
        f"---\n"
        f"# PUREFACTS CONTEXT\n"
        f"{context}"
    )


def build_debate_user_turn(
    agent_id: str,
    source_md: str,
    history: list[dict],
) -> str:
    """Compose the user-turn prompt for a debate agent."""
    parts = [
        "## Source Document",
        source_md,
        "",
    ]

    if history:
        parts.append("## Debate So Far")
        for entry in history:
            other = AGENTS[entry["agent_id"]]
            parts.append(f"**{other['name']} ({other['title']}):**\n{entry['content']}\n")

    me = AGENTS[agent_id]
    if not history:
        directive = (
            f"Open the debate. As {me['name']}, lay out your case for how PureFacts should "
            f"campaign this content. Be specific about WHICH assets to lead with, WHICH ICP "
            f"to prioritize, and WHY. Argue from your stance."
        )
    else:
        opponent = AGENTS["marcus" if agent_id == "maya" else "maya"]
        directive = (
            f"Respond to {opponent['name']}'s argument. Identify where they are right, "
            f"where they are wrong, and refine your recommendation. Address them by name. "
            f"Do not concede the core of your stance."
        )

    parts.append(f"## Your Turn ({me['name']})")
    parts.append(directive)
    parts.append("\nKeep your response under 220 words. Be sharp, opinionated, and specific.")
    return "\n\n".join(parts)


def build_synth_user_turn(source_md: str, history: list[dict]) -> str:
    """Compose the synthesizer's user-turn prompt."""
    parts = ["## Source Document", source_md, "", "## Full Debate Transcript"]
    for entry in history:
        a = AGENTS[entry["agent_id"]]
        parts.append(f"**{a['name']} ({a['title']}):**\n{entry['content']}\n")
    parts.append(
        "## Your Task\n"
        "Read the source document and the debate transcript. Write the final Campaign Brief "
        "that PureFacts will execute. Follow your protocol exactly."
    )
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Streaming wrappers
# ---------------------------------------------------------------------------


def stream_agent(
    client: genai.Client,
    agent_id: str,
    source_md: str,
    history: list[dict],
    debate_prompt: str,
    context: str,
) -> Iterable[str]:
    """Yield text chunks for a single debate agent's turn."""
    agent = AGENTS[agent_id]
    system_instruction = _system_for_agent(agent_id, debate_prompt, context)
    user_prompt = build_debate_user_turn(agent_id, source_md, history)

    for chunk in client.models.generate_content_stream(
        model=agent["model"],
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.85,
        ),
    ):
        if chunk.text:
            yield chunk.text


def stream_synthesizer(
    client: genai.Client,
    source_md: str,
    history: list[dict],
    synth_prompt: str,
    context: str,
) -> Iterable[str]:
    """Yield text chunks for the synthesizer's turn."""
    sterling = AGENTS["sterling"]
    system_instruction = _system_for_synth(synth_prompt, context)
    user_prompt = build_synth_user_turn(source_md, history)

    for chunk in client.models.generate_content_stream(
        model=sterling["model"],
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.55,
        ),
    ):
        if chunk.text:
            yield chunk.text


@lru_cache(maxsize=4)
def validate_api_key(api_key: str) -> tuple[bool, str]:
    """Quick validation via a lightweight token-counting call.

    Cached per api_key so we don't fire a network call to Gemini on every
    Streamlit rerun of the intelligence phase. Cache bound is small (4) since
    we expect at most one or two distinct keys per process lifetime. If the
    key is rotated, restart the app or call validate_api_key.cache_clear().
    """
    try:
        client = genai.Client(api_key=api_key)
        client.models.count_tokens(model=DEBATE_MODEL, contents="connection test")
        return True, ""
    except Exception as exc:
        return False, str(exc)
