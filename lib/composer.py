"""Movement III: the Composer.

Generates the 10 marketing assets via Gemini, informed by the approved
campaign brief. Each asset is streamed individually and saved to /output/.
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
OUTPUT_DIR = ROOT / "output"

COMPOSER_MODEL = "gemini-2.5-flash"

# ---------------------------------------------------------------------------
# Asset catalog
# ---------------------------------------------------------------------------

# Each asset has:
#   id            -- matches output filename (without .md)
#   label         -- shown on the card
#   icon          -- visual marker
#   category      -- groups assets in distribution view
#   distribution  -- which action button(s) appear in Movement IV
#   spec          -- inline summary of what to generate

ASSETS = [
    {
        "id": "linkedin-narsingh",
        "label": "LinkedIn Post · Narsingh",
        "icon": "in",
        "category": "linkedin",
        "distribution": "linkedin",
        "spec": (
            "A 150-220 word LinkedIn post in Narsingh's voice (direct, mildly contrarian, "
            "data-backed, short paragraphs). Must lead with the counterintuitive insight, "
            "back it with one EXTRACT data point and one positioning.md proof point. End "
            "with a sharp question to the reader. No mention of PureFacts by name."
        ),
    },
    {
        "id": "linkedin-ceo",
        "label": "LinkedIn Post · Rob Madej (CEO)",
        "icon": "in",
        "category": "linkedin",
        "distribution": "linkedin",
        "spec": (
            "A 150-220 word LinkedIn post in Rob Madej's CEO voice (measured, industry-forward, "
            "founder gravitas). Lead with a macro trend the source illuminates. Reference one "
            "data point. Subtly position PureFacts' worldview without selling. No product names."
        ),
    },
    {
        "id": "nurture-email-1-wealth",
        "label": "Nurture Email 1 · Top of Funnel",
        "icon": "✉",
        "category": "email",
        "distribution": "copy",
        "spec": (
            "Top-of-funnel nurture email for wealth manager (Head of Ops / CFO). 120-180 words "
            "in body. Subject line, preview text, then body. Open with a wealth-manager pain "
            "point, reframe with one EXTRACT insight, soft CTA to read full analysis at "
            "https://purefacts.com/resources/. Sign off as Narsingh, Director of Product Marketing, "
            "PureFacts. Do NOT mention PureFacts products. Use 'Hi [First Name],'."
        ),
    },
    {
        "id": "nurture-email-2-wealth",
        "label": "Nurture Email 2 · Mid Funnel",
        "icon": "✉",
        "category": "email",
        "distribution": "copy",
        "spec": (
            "Mid-funnel nurture email for wealth manager. 120-180 words in body. Subject line, "
            "preview text, body. Acknowledge problem (callback to email 1), pivot to 'what "
            "leading firms are doing,' introduce PureFacts obliquely via the $13M case study or "
            "85% dispute reduction stat. Medium CTA: 'See how one firm unlocked $13M' linking to "
            "https://purefacts.com/how-a-leading-wealth-manager-unlocked-over-13m-in-annual-value-by-replacing-legacy-infrastructure/. "
            "Sign off as Narsingh."
        ),
    },
    {
        "id": "nurture-email-3-wealth",
        "label": "Nurture Email 3 · Bottom Funnel",
        "icon": "✉",
        "category": "email",
        "distribution": "copy",
        "spec": (
            "Bottom-of-funnel nurture email for wealth manager. <150 words in body. Subject, "
            "preview, body. Direct ask. Name PureFacts for the first time, one sentence on what "
            "we do (from positioning.md core), one proof point, then ask for 20 minutes with a "
            "CTA linking to https://purefacts.com/contact/. Sign off as Narsingh with title and "
            "contact placeholder for phone."
        ),
    },
    {
        "id": "bdr-sequence-asset-mgr",
        "label": "BDR Sequence · Asset Manager",
        "icon": "◎",
        "category": "outreach",
        "distribution": "copy",
        "spec": (
            "3-touch BDR outbound sequence for asset manager (COO / CFO / Head of Fund Admin). "
            "Each touch ≤90 words. Use asset-manager vocabulary (fee realization, NAV impact, "
            "fund administration, domiciles). Touch 1 cold open with EXTRACT data point. Touch 2 "
            "(3-4 days later) value add with PureFacts proof point (£750B+ AUM client, 30%+ "
            "billing cycle reduction). Touch 3 (5-7 days later) breakup, offer one-pager."
        ),
    },
    {
        "id": "sales-one-pager",
        "label": "Sales One-Pager",
        "icon": "❒",
        "category": "sales",
        "distribution": "email_approval",
        "spec": (
            "350-500 word sales one-pager. Four labeled sections: THE PROBLEM (3-4 bullets with "
            "EXTRACT data + ICP pain), THE SOLUTION (3-4 outcome-focused bullets from positioning.md), "
            "THE PROOF (table of 5-7 metrics from company.md), NEXT STEP (single CTA: 'Schedule a "
            "20-minute revenue assessment' linking to https://purefacts.com/contact/). Use Markdown "
            "headers and tables. Make it scannable in 15 seconds."
        ),
    },
    {
        "id": "objection-handling",
        "label": "Objection Handling",
        "icon": "⟲",
        "category": "enablement",
        "distribution": "copy",
        "spec": (
            "400-600 word objection handler for internal sales team. 5 objections that the "
            "source-document topic helps counter. For each: Objection (verbatim prospect line), "
            "Why they say it (1 sentence), Response (2-3 sentences: empathy → reframe → proof), "
            "Proof point. Conversational — what an AE would actually say on a call. Reframe "
            "competitors, never bash."
        ),
    },
    {
        "id": "blog-post",
        "label": "Blog Post",
        "icon": "❡",
        "category": "blog",
        "distribution": "hubspot",
        "spec": (
            "600-800 word blog post in PureFacts corporate voice. **Title MUST be 65 characters "
            "or fewer.** Open with the counterintuitive insight from EXTRACT (2-3 sentence hook). "
            "Three sections: The Problem (~200 words, expand with data), Why This Matters Now "
            "(~150 words, why-now from positioning.md), A Better Approach (~200 words, PureFacts "
            "philosophy + proof points). Closing CTA linking to https://purefacts.com/contact/."
        ),
    },
    {
        "id": "enablement-talking-points",
        "label": "AE Talking Points",
        "icon": "♪",
        "category": "enablement",
        "distribution": "copy",
        "spec": (
            "300-450 word AE enablement document. Four labeled sections, all bullets: "
            "DISCOVERY QUESTIONS (5-7 natural-sounding probes), KEY TALKING POINTS (5-7 verbatim "
            "lines an AE can say), PROOF POINTS (4-5 stats pre-formatted for verbal delivery), "
            "COMPETITIVE HANDLES (3-4 reframes vs. BillFin, Advent, in-house, do-nothing). "
            "Practical, not slide-deck language."
        ),
    },
]


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_multiply_prompt() -> str:
    return _read(PROMPTS_DIR / "02-multiply.md")


def _system_for_composer(multiply_prompt: str, context_bundle: str) -> str:
    """Single system prompt used for every asset; spec is injected per-asset."""
    return (
        "# YOU ARE THE COMPOSER\n\n"
        "You are the Composer agent inside Concerto. You produce a single marketing asset "
        "to spec. Quality bar: deployable as-is, no placeholder brackets, no TODO markers, "
        "no AI tells, no banned phrases. You are writing for the PureFacts marketing team, "
        "not for a client.\n\n"
        "---\n"
        "# GLOBAL ASSET SPEC\n"
        f"{multiply_prompt}\n\n"
        "---\n"
        "# PUREFACTS CONTEXT (your shared knowledge base)\n"
        f"{context_bundle}"
    )


def _user_prompt_for_asset(
    asset: dict,
    source_md: str,
    brief_md: str,
) -> str:
    """User-turn prompt: asset spec + source + approved brief."""
    return (
        f"# Asset to Compose\n"
        f"**ID**: `{asset['id']}`\n"
        f"**Label**: {asset['label']}\n\n"
        f"## Spec\n{asset['spec']}\n\n"
        f"---\n\n"
        f"## Approved Campaign Brief (Sterling's call)\n"
        f"This brief was just approved by the conductor. Let it inform the strategic angle "
        f"of this asset -- which ICP to lead with, how aggressive, what to emphasize.\n\n"
        f"{brief_md}\n\n"
        f"---\n\n"
        f"## Source Document\n"
        f"{source_md}\n\n"
        f"---\n\n"
        f"## Your Task\n"
        f"Produce only the asset content, ready to ship.\n\n"
        f"**FORMAT RULES (HARD CONSTRAINTS):**\n"
        f"- Output raw Markdown text. Do NOT wrap your output in a code fence "
        f"(no ```markdown, no ```md, no ``` of any kind around the whole asset).\n"
        f"- Begin with a YAML metadata block delimited by exactly three dashes:\n"
        f"  ```\n"
        f"  ---\n"
        f"  type: ...\n"
        f"  icp: ...\n"
        f"  words: ...\n"
        f"  voice: ...\n"
        f"  ---\n"
        f"  ```\n"
        f"- After the closing `---`, the asset body begins.\n"
        f"- No commentary, no explanation, no preamble. Just the metadata block and the asset."
    )


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------


def stream_asset(
    client: genai.Client,
    asset: dict,
    source_md: str,
    brief_md: str,
    multiply_prompt: str,
    context_bundle: str,
) -> Iterable[str]:
    """Yield text chunks for one asset's composition."""
    system = _system_for_composer(multiply_prompt, context_bundle)
    user = _user_prompt_for_asset(asset, source_md, brief_md)

    for chunk in client.models.generate_content_stream(
        model=COMPOSER_MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.75,
        ),
    ):
        if chunk.text:
            yield chunk.text


# ---------------------------------------------------------------------------
# Output persistence
# ---------------------------------------------------------------------------


def save_asset(source_stem: str, asset_id: str, content: str) -> Path:
    """Write one composed asset to /output/{source_stem}/{asset_id}.md"""
    out_dir = OUTPUT_DIR / source_stem
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{asset_id}.md"
    path.write_text(content, encoding="utf-8")
    return path
