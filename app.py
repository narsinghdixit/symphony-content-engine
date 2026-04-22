"""Concerto -- a Project Symphony composition.

Three movements: Intelligence, Approval, Composition + Distribution.
PureFacts' GTM intelligence + action layer.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
from google import genai
from streamlit_autorefresh import st_autorefresh

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import json  # noqa: E402

import streamlit.components.v1 as components  # noqa: E402

from lib import agents as agentlib  # noqa: E402
from lib import composer, distribution, email_sender, runs  # noqa: E402
from lib.icons import icon  # noqa: E402
from lib.textutils import friendly_error  # noqa: E402
from lib.theme import COLORS, GRADIENTS, inject_theme  # noqa: E402

# ---------------------------------------------------------------------------
# Page config + theme
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Concerto · Project Symphony",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme(st)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Concerto's structure: three Movements with The Cue between Movement I and II.
# A concerto is canonically 3 movements; the conductor's cue between movements
# is a structural pause, not a movement of its own. Approval = the Cue.
#   tuple = (phase_id, kind, label)   where kind in {"movement", "cue"}.
MOVEMENTS = [
    ("intelligence", "movement", "Movement I · Intelligence"),
    # The Cue label embeds an inline bell-ring icon at render time so it picks
    # up the active/complete color automatically via stroke=currentColor.
    ("awaiting_approval", "cue", "The Cue"),
    ("executing", "movement", "Movement II · Composition"),
    ("distribution", "movement", "Movement III · Distribution"),
]


# ---------------------------------------------------------------------------
# Source document ingest helpers
# ---------------------------------------------------------------------------


def ingest_uploaded_file(uploaded) -> tuple[str, str]:
    """Convert an uploaded file (.docx, .pdf, .md, .txt) to markdown text."""
    name = uploaded.name
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    raw_bytes = uploaded.getvalue()

    if suffix == ".docx":
        from io import BytesIO

        from docx import Document

        doc = Document(BytesIO(raw_bytes))
        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            style = para.style.name if para.style else ""
            if style.startswith("Heading"):
                level = style[-1] if style[-1].isdigit() else "2"
                lines.append(f"{'#' * int(level)} {text}")
            else:
                lines.append(text)
        body = "\n\n".join(lines)
    elif suffix == ".pdf":
        from io import BytesIO

        import pdfplumber

        pages = []
        with pdfplumber.open(BytesIO(raw_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        body = "\n\n---\n\n".join(pages)
    elif suffix in (".md", ".txt"):
        body = raw_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return stem, f"# {stem}\n\n{body}"


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

def _fresh_defaults() -> dict:
    """Return a fresh copy of session defaults.

    Defined as a function (not a module-level dict) so every reset / init gets
    its own mutable instances. Otherwise multiple sessions share the same
    {} / [] objects and state leaks across runs.
    """
    return {
        "phase": "preview",             # preview | idle | intelligence | awaiting_approval | executing | distribution
        "source_stem": "",
        "source_md": "",
        "debate_history": [],
        "synth_brief": "",
        "approval_token": "",
        "approval_email_sent": False,
        "approved": False,
        "started_at": None,
        "magic_link_arrived": False,    # True when this session loaded with ?token=...&action=approve
        # Movement II / III state
        "assets": {},                   # {asset_id: {"content": str, "elapsed": float, "saved_path": str}}
        "assets_failed": {},            # {asset_id: error_msg} -- assets that failed in last attempt
        "composition_done": False,
        "ship_status": {},              # {asset_id: {"ok": bool, "msg": str, "url": str?}}
    }


def reset_session_to_defaults() -> None:
    """Wipe and re-initialize all session_state keys we own."""
    for _k, _v in _fresh_defaults().items():
        st.session_state[_k] = _v


# Initialize any missing keys on first load (preserves keys already in session).
for _k, _v in _fresh_defaults().items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ---------------------------------------------------------------------------
# Magic link URL handler -- runs every page load
# ---------------------------------------------------------------------------


def get_app_base_url() -> str:
    """Detect the app's externally-reachable URL for magic links.

    Order of precedence:
      1. SYMPHONY_BASE_URL secret (production override, e.g. on Streamlit Cloud)
      2. The Host header on the current request (works for any local port)
      3. Hardcoded localhost fallback
    """
    override = st.secrets.get("SYMPHONY_BASE_URL", "")
    if override:
        return override.rstrip("/")

    # Try to read the actual Host header from the current request
    try:
        headers = st.context.headers if hasattr(st, "context") else {}
        host = headers.get("host", "") if headers else ""
        proto = headers.get("x-forwarded-proto", "http") if headers else "http"
        if host:
            return f"{proto}://{host}"
    except Exception:
        pass

    return "http://localhost:8501"


def handle_magic_link():
    """If the URL contains ?token=...&action=approve, mark the run approved
    and show the 'approval received' confirmation page.
    """
    qp = st.query_params
    token = qp.get("token", "")
    action = qp.get("action", "")
    if not token:
        return False

    run = runs.load_run(token)
    if not run:
        st.error("Approval link is invalid or has expired.")
        st.stop()

    if action == "approve":
        runs.mark_approved(token)
        # Clear the URL params so a refresh / reload doesn't re-trap this
        # browser tab on the confirmation page. Without this, ?token=...&action=
        # persists in the URL and every rerun calls handle_magic_link again,
        # making it impossible to navigate to any other phase from this tab.
        try:
            st.query_params.clear()
        except Exception:
            pass
        check_glyph = icon("check-circle", size=48, color=COLORS["success"], stroke=1.6)
        st.markdown(
            f"""
            <div style="padding:48px 0;text-align:center;">
              <div style="margin-bottom:18px;display:flex;justify-content:center;">{check_glyph}</div>
              <h1 class="symphony-h1" style="font-size:44px;">Approval received.</h1>
              <p style="color:{COLORS['text_dim']};font-size:17px;max-width:520px;margin:16px auto;">
                Concerto is now executing the campaign. Return to your original Symphony tab to watch the composition unfold in real time.
              </p>
              <div style="margin-top:32px;color:{COLORS['text_mute']};font-size:11px;letter-spacing:0.6px;text-transform:uppercase;font-weight:600;">
                Run · {run['source_stem']}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    return False


# ---------------------------------------------------------------------------
# UI fragments
# ---------------------------------------------------------------------------


def render_eyebrow(label: str = "PROJECT SYMPHONY · A LIVE PREVIEW"):
    glyph = icon("sparkles", size=12, color=COLORS["indigo"], stroke=2.0)
    st.markdown(
        f'<div style="margin-bottom:8px;display:inline-flex;align-items:center;gap:8px;">'
        f'{glyph}<span class="symphony-eyebrow">{label}</span></div>',
        unsafe_allow_html=True,
    )


def render_phase_rail():
    current = st.session_state.phase
    if current in ("preview", "idle"):
        current_idx = -1  # before any movement
    else:
        try:
            current_idx = [m[0] for m in MOVEMENTS].index(current)
        except ValueError:
            current_idx = -1

    parts = ['<div class="symphony-phase-rail">']
    for i, (_phase_id, kind, label) in enumerate(MOVEMENTS):
        if i < current_idx:
            cls = "complete"
        elif i == current_idx:
            cls = "active"
        else:
            cls = ""
        kind_cls = "cue" if kind == "cue" else "movement"

        # Cue stops get a small bell-ring SVG inline instead of the diamond
        # glyph; the SVG inherits color via stroke=currentColor so it tracks
        # the cue's italic violet / fuchsia / violet states automatically.
        if kind == "cue":
            cue_svg = icon("bell-ring", size=12, stroke=1.8)
            label_html = f'{cue_svg}<span style="margin-left:4px;">{label}</span>'
        else:
            label_html = f"<span>{label}</span>"

        parts.append(
            f'<div class="symphony-phase-step {kind_cls} {cls}" style="display:inline-flex;align-items:center;gap:8px;">'
            f'<span class="symphony-phase-dot"></span>'
            f"{label_html}"
            f"</div>"
        )
        if i < len(MOVEMENTS) - 1:
            parts.append('<span class="symphony-phase-line"></span>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def render_agent_header(agent_id: str, status: str = "thinking"):
    a = agentlib.AGENTS[agent_id]
    status_label = {
        "thinking": "Thinking",
        "streaming": "Streaming",
        "complete": "Complete",
        "pending": "Pending",
    }.get(status, status.title())
    st.markdown(
        f"""
        <div class="symphony-agent-header">
          <div class="symphony-agent-avatar {a['avatar_class']}">{a['avatar_initial']}</div>
          <div style="flex:1;">
            <div class="symphony-agent-name">{a['name']}</div>
            <div class="symphony-agent-title">{a['title']}</div>
          </div>
          <span class="symphony-pill {status}">{status_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def escape_dollars(text: str) -> str:
    return text.replace("$", r"\$")


# friendly_error() lives in lib/textutils.py so it can be unit-tested without
# pulling in Streamlit. Imported above; usage unchanged at call sites.


def render_debate_recap():
    """Re-render the strategic debate from session state. Used on Movements II/III/IV
    so the conductor can refer back to the debate at any time."""
    history = st.session_state.get("debate_history") or []
    brief = st.session_state.get("synth_brief") or ""
    if not history and not brief:
        return

    with st.expander("View the strategic debate · Movement I recap", expanded=False):
        for i, entry in enumerate(history):
            agent = agentlib.AGENTS[entry["agent_id"]]
            round_num = (i // 2) + 1
            if i % 2 == 0:
                st.markdown(
                    f'<div style="font-size:11px;letter-spacing:1.4px;color:{COLORS["text_mute"]};text-transform:uppercase;font-weight:600;margin:18px 0 8px 0;">Round {round_num} of 2</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f"""
                <div class="symphony-agent-header" style="margin-bottom:6px;">
                  <div class="symphony-agent-avatar {agent['avatar_class']}">{agent['avatar_initial']}</div>
                  <div style="flex:1;">
                    <div class="symphony-agent-name">{agent['name']}</div>
                    <div class="symphony-agent-title">{agent['title']}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="symphony-content" style="margin-bottom:18px;">{escape_dollars(entry["content"])}</div>',
                unsafe_allow_html=True,
            )

        if brief:
            wand_svg = icon("wand-sparkles", size=11, color=COLORS["violet"], stroke=2.0)
            st.markdown(
                f'<div style="font-size:11px;letter-spacing:0.6px;color:{COLORS["violet"]};text-transform:uppercase;font-weight:600;margin:24px 0 10px 0;display:inline-flex;align-items:center;gap:6px;">'
                f'{wand_svg}Sterling\'s Brief</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="symphony-content">{escape_dollars(brief)}</div>',
                unsafe_allow_html=True,
            )


def linkedin_copy_open_button(text: str, button_id: str, label: str = "Copy + Open LinkedIn"):
    """Inject a one-click button that copies text to clipboard AND opens LinkedIn.

    Uses the browser's clipboard API + window.open in a single user gesture.
    """
    payload = json.dumps(text)
    li_svg = icon("linkedin", size=16, color="#FFFFFF", stroke=2.0)
    arrow_svg = icon("external-link", size=14, color="#FFFFFF", stroke=2.0)
    html = f"""
    <div style="margin:8px 0;">
      <button id="{button_id}" type="button"
              aria-label="{label}: copy LinkedIn post to clipboard and open the LinkedIn composer in a new tab"
              style="
        background: linear-gradient(135deg, #818CF8 0%, #A78BFA 50%, #E879F9 100%);
        color: white;
        border: none;
        padding: 11px 20px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        letter-spacing: 0.1px;
        box-shadow: 0 4px 16px rgba(129,140,248,0.30);
        font-family: 'Geist', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        display: inline-flex; align-items: center; gap: 10px;
        transition: filter 150ms ease, box-shadow 150ms ease;
      "
      onmouseover="this.style.filter='brightness(1.08)';this.style.boxShadow='0 8px 28px rgba(129,140,248,0.45)';"
      onmouseout="this.style.filter='';this.style.boxShadow='0 4px 16px rgba(129,140,248,0.30)';">
        {li_svg}<span>{label}</span>{arrow_svg}
      </button>
      <span id="{button_id}_status" role="status" aria-live="polite" style="margin-left:14px;color:#34D399;font-size:13px;font-weight:600;display:none;">✓ Copied</span>
    </div>
    <script>
      (function() {{
        const btn = document.getElementById("{button_id}");
        const status = document.getElementById("{button_id}_status");
        if (!btn) return;
        btn.addEventListener("click", async function() {{
          try {{
            await navigator.clipboard.writeText({payload});
            status.style.display = "inline";
          }} catch (e) {{
            // Fallback: use the deprecated execCommand
            const ta = document.createElement("textarea");
            ta.value = {payload};
            document.body.appendChild(ta);
            ta.select();
            try {{ document.execCommand("copy"); status.style.display = "inline"; }} catch (e2) {{}}
            document.body.removeChild(ta);
          }}
          window.open("https://www.linkedin.com/feed/?shareActive=true", "_blank");
        }});
      }})();
    </script>
    """
    components.html(html, height=70)


def universal_copy_button(text: str, button_id: str, label: str = "Copy text"):
    """Inject a one-click clipboard copy button."""
    payload = json.dumps(text)
    copy_svg = icon("copy", size=14, color="#F1F5F9", stroke=1.8)
    html = f"""
    <div style="margin:8px 0;">
      <button id="{button_id}" type="button"
              aria-label="{label}: copy asset content to clipboard"
              style="
        background: {COLORS['surface_2']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        padding: 9px 16px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
        cursor: pointer;
        font-family: 'Geist', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        display: inline-flex; align-items: center; gap: 8px;
        transition: border-color 150ms ease, background-color 150ms ease;
      "
      onmouseover="this.style.borderColor='{COLORS['indigo']}';this.style.background='{COLORS['surface_3']}';"
      onmouseout="this.style.borderColor='{COLORS['border']}';this.style.background='{COLORS['surface_2']}';">
        {copy_svg}<span>{label}</span>
      </button>
      <span id="{button_id}_status" role="status" aria-live="polite" style="margin-left:14px;color:#34D399;font-size:13px;font-weight:600;display:none;">✓ Copied to clipboard</span>
    </div>
    <script>
      (function() {{
        const btn = document.getElementById("{button_id}");
        const status = document.getElementById("{button_id}_status");
        if (!btn) return;
        btn.addEventListener("click", async function() {{
          try {{
            await navigator.clipboard.writeText({payload});
            status.style.display = "inline";
          }} catch (e) {{
            const ta = document.createElement("textarea");
            ta.value = {payload};
            document.body.appendChild(ta);
            ta.select();
            try {{ document.execCommand("copy"); status.style.display = "inline"; }} catch (e2) {{}}
            document.body.removeChild(ta);
          }}
        }});
      }})();
    </script>
    """
    components.html(html, height=60)


# ---------------------------------------------------------------------------
# Preview page (the new opening)
# ---------------------------------------------------------------------------


def render_preview_page():
    render_eyebrow("PROJECT SYMPHONY · A LIVE PREVIEW")

    st.markdown(
        f"""
        <h1 class="symphony-h1">Concerto</h1>
        <p class="symphony-tagline" style="font-size:20px;color:{COLORS['text']};margin-bottom:6px;">
          Three movements. One campaign. <strong>Composed in minutes.</strong>
        </p>
        <p class="symphony-tagline">
          Concerto is the first composition from Project Symphony — PureFacts' GTM
          intelligence and action layer. AI strategists debate the play. The brief
          routes for approval. Then ten marketing assets get composed and shipped to
          LinkedIn, HubSpot, and the team. One run, end to end.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # Three Movements. The Cue (approval) sits between Movements I and II as
    # a structural pause -- mentioned verbally, not given its own card.
    # Descriptions intentionally trimmed to roughly equal length so the three
    # cards read parallel. The fuller narrative lives in the demo voiceover.
    cards = [
        {
            "movement": "Movement I",
            "title": "Intelligence",
            "icon_name": "sparkles",
            "duration": "~60 seconds",
            "desc": "Two AI strategists — Maya for brand, Marcus for pipeline — debate the campaign. Sterling, the Director, writes the brief and routes it for the cue.",
        },
        {
            "movement": "Movement II",
            "title": "Composition",
            "icon_name": "wand-sparkles",
            "duration": "~90 seconds",
            "desc": "Once the conductor cues, Concerto composes ten marketing assets in the PureFacts voice — posts, emails, BDR sequence, blog, one-pager, enablement.",
        },
        {
            "movement": "Movement III",
            "title": "Distribution",
            "icon_name": "send",
            "duration": "~30 seconds",
            "desc": "Each asset ships to its destination — LinkedIn, HubSpot CMS, the team's inbox — with a single click per channel. The performance reaches the audience.",
        },
    ]

    # Composition cards collapsed by default. The conductor introduces the
    # three movements verbally first, then expands on cue. Stops the audience
    # from reading ahead while the speaker is still framing.
    with st.expander("The Composition · three movements", expanded=False):
        cols = st.columns(3, gap="medium")
        for col, card in zip(cols, cards):
            with col:
                glyph = icon(card["icon_name"], size=22, color=COLORS["indigo"], stroke=1.7)
                # min-height: 340px (was fixed 300px which clipped longer descs
                # and hid the duration footer). Auto-grows for any card that
                # still needs more space. Three cards in a row don't auto-equalize
                # in Streamlit columns -- min-height anchors the visual rhythm.
                st.markdown(
                    f"""
                    <div class="symphony-card" style="min-height:340px;display:flex;flex-direction:column;justify-content:space-between;">
                      <div>
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
                          <span style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:10px;background:rgba(129,140,248,0.12);border:1px solid rgba(129,140,248,0.24);">{glyph}</span>
                          <span class="symphony-eyebrow" style="opacity:0.85;">{card['movement']}</span>
                        </div>
                        <div style="font-size:24px;font-weight:700;color:{COLORS['text']};margin-bottom:10px;letter-spacing:-0.4px;">{card['title']}</div>
                        <div style="font-size:14px;color:{COLORS['text_dim']};line-height:1.55;">{card['desc']}</div>
                      </div>
                      <div style="font-size:11px;letter-spacing:0.6px;color:{COLORS['text_mute']};text-transform:uppercase;font-weight:600;margin-top:18px;">{card['duration']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    # Wider button column (was [1, 3] = ~25% width) so the singular CTA reads
    # confidently from the back of a Townhall room on a projector.
    cols = st.columns([2, 3])
    with cols[0]:
        if st.button("Take the Podium  →", type="primary", use_container_width=True):
            st.session_state.phase = "idle"
            st.rerun()


# ---------------------------------------------------------------------------
# Phase functions
# ---------------------------------------------------------------------------


def render_idle_page():
    render_eyebrow("CONCERTO · UPLOAD")
    st.markdown(
        '<h1 class="symphony-h1" style="font-size:44px;">Drop the source.</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="symphony-tagline">'
        "Whitepaper, blog draft, press release, analyst report, product brief. "
        ".docx, .pdf, .md, or .txt. Up to 25 MB."
        "</p>",
        unsafe_allow_html=True,
    )

    render_phase_rail()

    uploaded = st.file_uploader(
        "Source document",
        type=["docx", "pdf", "md", "txt"],
        label_visibility="collapsed",
    )

    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    # Wider button column (was [1, 2] = ~33% width) so the primary action is
    # visible from the back of a Townhall room.
    cols = st.columns([2, 3])
    with cols[0]:
        begin = st.button(
            "Compose Magic",
            type="primary",
            use_container_width=True,
            disabled=uploaded is None,
        )
    with cols[1]:
        if uploaded:
            st.markdown(
                f'<div style="display:flex;align-items:center;height:100%;color:{COLORS["text_dim"]};font-size:14px;">'
                f"Ready: <strong style=\"color:{COLORS['text']};margin-left:6px;\">{uploaded.name}</strong>"
                f' · {len(uploaded.getvalue()) // 1024} KB'
                f"</div>",
                unsafe_allow_html=True,
            )

    if begin and uploaded:
        try:
            stem, body = ingest_uploaded_file(uploaded)
        except Exception as exc:
            st.error(f"Could not ingest file: {exc}")
            st.stop()

        st.session_state.source_stem = stem
        st.session_state.source_md = body
        st.session_state.phase = "intelligence"
        st.session_state.started_at = time.time()
        st.rerun()


def run_intelligence_phase(client: genai.Client, source_md: str) -> tuple[list[dict], str]:
    debate_prompt = agentlib.load_debate_prompt()
    synth_prompt = agentlib.load_synth_prompt()
    context = agentlib.load_context_bundle()

    history: list[dict] = []

    section_glyph = icon("sparkles", size=12, color=COLORS["indigo"], stroke=2.0)
    st.markdown(
        f'<div class="symphony-section-label" style="display:inline-flex;align-items:center;gap:8px;">'
        f'{section_glyph}Movement I · Intelligence</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<h2 class="symphony-h2">Maya vs. Marcus</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#A8B0C7;margin-bottom:24px;font-size:15px;">'
        "Two rounds. Brand vs. pipeline. Direct argument. No moderator."
        "</p>",
        unsafe_allow_html=True,
    )

    for round_idx in range(2):
        st.markdown(
            f'<div class="symphony-section-label" style="opacity:0.85;">'
            f"Round {round_idx + 1} of 2"
            f"</div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(2, gap="large")
        for col, agent_id in zip(cols, agentlib.DEBATE_AGENTS):
            with col:
                with st.container(border=False):
                    render_agent_header(agent_id, status="streaming")
                    placeholder = st.empty()
                    placeholder.markdown(
                        '<div class="symphony-shimmer" style="height:14px;width:60%;margin:8px 0;"></div>'
                        '<div class="symphony-shimmer" style="height:14px;width:90%;margin:8px 0;"></div>'
                        '<div class="symphony-shimmer" style="height:14px;width:75%;margin:8px 0;"></div>',
                        unsafe_allow_html=True,
                    )

                    t0 = time.time()
                    chunks: list[str] = []
                    for piece in agentlib.stream_agent(
                        client, agent_id, source_md, history, debate_prompt, context
                    ):
                        chunks.append(piece)
                        placeholder.markdown(
                            f'<div class="symphony-content">{escape_dollars("".join(chunks))}'
                            f'<span class="symphony-cursor"></span></div>',
                            unsafe_allow_html=True,
                        )
                    elapsed = time.time() - t0
                    placeholder.markdown(
                        f'<div class="symphony-content">{escape_dollars("".join(chunks))}</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(f"Responded in {elapsed:.1f}s")

                    history.append(
                        {
                            "agent_id": agent_id,
                            "content": "".join(chunks),
                            "elapsed": elapsed,
                        }
                    )

    st.markdown("<br/>", unsafe_allow_html=True)
    synth_glyph = icon("wand-sparkles", size=12, color=COLORS["violet"], stroke=2.0)
    st.markdown(
        f'<div class="symphony-section-label" style="display:inline-flex;align-items:center;gap:8px;'
        f'color:{COLORS["violet"]};background:rgba(167,139,250,0.10);border-color:rgba(167,139,250,0.30);">'
        f'{synth_glyph}Synthesis</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<h2 class="symphony-h2">Sterling, the Director</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#A8B0C7;margin-bottom:24px;font-size:15px;">'
        "Reads the room. Makes the call. Writes the brief."
        "</p>",
        unsafe_allow_html=True,
    )

    with st.container(border=False):
        render_agent_header("sterling", status="streaming")
        synth_placeholder = st.empty()
        synth_placeholder.markdown(
            '<div class="symphony-shimmer" style="height:14px;width:50%;margin:8px 0;"></div>'
            '<div class="symphony-shimmer" style="height:14px;width:80%;margin:8px 0;"></div>'
            '<div class="symphony-shimmer" style="height:14px;width:65%;margin:8px 0;"></div>'
            '<div class="symphony-shimmer" style="height:14px;width:90%;margin:8px 0;"></div>',
            unsafe_allow_html=True,
        )

        t0 = time.time()
        synth_chunks: list[str] = []
        for piece in agentlib.stream_synthesizer(
            client, source_md, history, synth_prompt, context
        ):
            synth_chunks.append(piece)
            synth_placeholder.markdown(
                f'<div class="symphony-content">{escape_dollars("".join(synth_chunks))}'
                f'<span class="symphony-cursor"></span></div>',
                unsafe_allow_html=True,
            )
        synth_elapsed = time.time() - t0
        synth_placeholder.markdown(
            f'<div class="symphony-content">{escape_dollars("".join(synth_chunks))}</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Brief written in {synth_elapsed:.1f}s")

    return history, "".join(synth_chunks)


def send_brief_for_approval(brief_md: str, source_stem: str, approve_url: str) -> bool:
    secrets = st.secrets
    try:
        html, plain = email_sender.render_approval_email(
            recipient_email=secrets["APPROVAL_EMAIL"],
            asset_label="Campaign Brief",
            source_label=f"{source_stem} (uploaded {datetime.now().strftime('%b %d, %Y')})",
            asset_md=brief_md,
            approve_url=approve_url,
        )
        email_sender.send_email(
            gmail_address=secrets["GMAIL_ADDRESS"],
            gmail_app_password=secrets["GMAIL_APP_PASSWORD"],
            to_email=secrets["APPROVAL_EMAIL"],
            subject=f"Concerto: approve campaign brief for {source_stem}?",
            html_body=html,
            plain_body=plain,
        )
        return True
    except Exception as exc:
        st.error(f"Email send failed: {exc}")
        return False


def render_intelligence_phase():
    render_eyebrow(f"CONCERTO · {st.session_state.source_stem}")
    # H1 is "Strategy." -- single noun parallel to "Composition." and
    # "Distribution." Avoids collision with Movement II's "Composing/Composition."
    st.markdown(
        '<h1 class="symphony-h1" style="font-size:44px;">Strategy.</h1>',
        unsafe_allow_html=True,
    )
    render_phase_rail()

    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    if not api_key:
        st.error("GOOGLE_API_KEY missing from .streamlit/secrets.toml")
        st.stop()

    valid, err = agentlib.validate_api_key(api_key)
    if not valid:
        st.error(f"Gemini API key invalid: {err}")
        st.stop()

    client = genai.Client(api_key=api_key)

    # Wrap the streaming so a Gemini hiccup (rate limit, network drop, content
    # filter, RESOURCE_EXHAUSTED) becomes a recoverable on-screen card instead
    # of a Python traceback in the most attention-heavy moment of the demo.
    try:
        history, brief = run_intelligence_phase(client, st.session_state.source_md)
    except Exception as exc:
        st.markdown(
            f'<div class="symphony-error-banner" style="margin-top:18px;">'
            f"Movement I — {escape_dollars(friendly_error(exc, fallback_prefix='Movement I hit a snag'))}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="color:{COLORS["text_dim"]};margin:14px 0 22px 0;font-size:15px;">'
            "This usually means a temporary network or quota hiccup with Gemini. "
            "Click below to re-run Movement I from the top, or fall back to the upload screen."
            "</p>",
            unsafe_allow_html=True,
        )
        cols = st.columns([1, 1, 2])
        with cols[0]:
            if st.button("↻  Retry Movement I", type="primary", use_container_width=True):
                st.session_state.started_at = time.time()
                st.rerun()
        with cols[1]:
            if st.button("←  Back to Upload", use_container_width=True):
                reset_session_to_defaults()
                st.session_state.phase = "idle"
                st.rerun()
        st.stop()

    st.session_state.debate_history = history
    st.session_state.synth_brief = brief

    # Persist run + send magic link email
    token = runs.new_token()
    runs.write_run(
        token,
        source_stem=st.session_state.source_stem,
        source_md=st.session_state.source_md,
        debate_history=history,
        synth_brief=brief,
    )
    st.session_state.approval_token = token

    base = get_app_base_url()
    approve_url = f"{base}/?token={token}&action=approve"

    with st.spinner("Sending brief to your inbox..."):
        sent = send_brief_for_approval(brief, st.session_state.source_stem, approve_url)
    st.session_state.approval_email_sent = sent
    st.session_state.phase = "awaiting_approval"
    st.rerun()


def render_awaiting_approval_page():
    render_eyebrow(f"CONCERTO · {st.session_state.source_stem}")
    st.markdown(
        '<h1 class="symphony-h1" style="font-size:44px;">Awaiting your sign-off.</h1>',
        unsafe_allow_html=True,
    )
    render_phase_rail()

    # Poll the run file every 2 seconds for approval (max 5 minutes / 150 polls)
    token = st.session_state.approval_token
    if token:
        poll_count = st_autorefresh(interval=2000, limit=150, key="approval_poll")
        if runs.is_approved(token):
            st.session_state.approved = True
            st.session_state.phase = "executing"
            st.rerun()

    if st.session_state.approval_email_sent:
        mail_glyph = icon("mail", size=22, color=COLORS["indigo"], stroke=1.7)
        st.markdown(
            f"""
            <div class="symphony-card-glow" style="margin:18px 0;">
              <div style="display:flex;align-items:center;gap:16px;">
                <div class="symphony-pulse"
                     style="display:inline-flex;align-items:center;justify-content:center;
                            width:44px;height:44px;border-radius:12px;
                            background:rgba(129,140,248,0.14);
                            border:1px solid rgba(129,140,248,0.30);">{mail_glyph}</div>
                <div style="flex:1;">
                  <div style="font-weight:700;font-size:16px;color:{COLORS['text']};letter-spacing:-0.1px;">Brief delivered to your inbox</div>
                  <div style="color:{COLORS['text_dim']};font-size:14px;margin-top:2px;">
                    Open <strong>{st.secrets.get('APPROVAL_EMAIL', '')}</strong> and click <strong>Approve and Execute</strong>. This page will advance automatically.
                  </div>
                </div>
                <span class="symphony-pill thinking">Polling</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("Email failed to send. Use the in-app button below to approve.")

    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    # Strategic debate recap (collapsed)
    render_debate_recap()

    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    # Show the brief
    st.markdown(
        '<div class="symphony-section-label">Brief Preview</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="symphony-card symphony-content" style="padding:32px;">'
        f"{escape_dollars(st.session_state.synth_brief)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    cols = st.columns([1, 1, 2])
    with cols[0]:
        approve = st.button(
            "✓  Approve in App",
            type="primary",
            use_container_width=True,
        )
    with cols[1]:
        restart = st.button("↻  Restart", use_container_width=True)

    if approve:
        if token:
            runs.mark_approved(token)
        st.session_state.approved = True
        st.session_state.phase = "executing"
        st.rerun()
    if restart:
        reset_session_to_defaults()
        st.rerun()


def _asset_card_html(
    asset: dict,
    status: str,
    elapsed: float | None = None,
    error: str | None = None,
    source_stem: str | None = None,
) -> str:
    """Render the asset card header HTML with the right status pill + border.

    Statuses:
      - "composing": pink border, "Composing" pill
      - "complete":  green border, "Complete" pill, elapsed + saved-path meta
      - "failed":    red border, "Failed" pill, error message meta
      - anything else: neutral, "Pending" pill
    """
    if status == "composing":
        card_cls = "symphony-asset-card composing"
        pill_html = '<span class="symphony-pill streaming">Composing</span>'
        meta = ""
    elif status == "complete":
        card_cls = "symphony-asset-card complete"
        pill_html = '<span class="symphony-pill complete">Complete</span>'
        path_segment = (
            f"{escape_dollars(source_stem)}/{escape_dollars(asset['id'])}.md"
            if source_stem
            else f"{escape_dollars(asset['id'])}.md"
        )
        meta = (
            f'<div style="font-size:11px;letter-spacing:0.4px;color:{COLORS["text_mute"]};margin-top:6px;">'
            f"Composed in {elapsed:.1f}s · saved to /output/{path_segment}"
            f"</div>"
        ) if elapsed is not None else ""
    elif status == "failed":
        card_cls = "symphony-asset-card failed"
        pill_html = '<span class="symphony-pill failed">Failed</span>'
        err_text = escape_dollars(error or "unknown error")
        meta = (
            f'<div style="font-size:12px;color:{COLORS["danger"]};margin-top:8px;line-height:1.45;">'
            f"{err_text}"
            f"</div>"
        )
    else:
        card_cls = "symphony-asset-card"
        pill_html = '<span class="symphony-pill pending">Pending</span>'
        meta = ""

    # Render the asset glyph as an inline Lucide SVG; tint the surrounding
    # icon chip by category so LinkedIn / outreach / blog read distinct.
    glyph_name = asset.get("icon_name") or "sparkles"
    glyph_svg = icon(glyph_name, size=16, stroke=1.8)
    icon_class = ""
    cat = asset.get("category", "")
    if cat == "linkedin":
        icon_class = " linkedin"
    elif cat == "outreach":
        icon_class = " outreach"
    elif cat == "blog":
        icon_class = " blog"

    return f"""
    <div class="{card_cls}">
      <div class="symphony-asset-card-header">
        <div class="symphony-asset-icon{icon_class}">{glyph_svg}</div>
        <div class="symphony-asset-label">{asset['label']}</div>
        {pill_html}
      </div>
      {meta}
    </div>
    """


def _streaming_preview_html(text: str, done: bool = False) -> str:
    """Render the streaming text in a clean, monospaced container.

    No markdown rendering -- shows raw text with whitespace preserved so the
    YAML frontmatter and headings don't blow up the layout.
    """
    cursor = "" if done else '<span class="symphony-cursor"></span>'
    # Simple HTML-escape (we're embedding inside a <pre>)
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    border_color = "rgba(52,211,153,0.30)" if done else "rgba(232,121,249,0.40)"
    return (
        f'<pre style="background:#0B1020;border:1px solid {border_color};border-radius:10px;'
        f'padding:14px 16px;margin:6px 0 14px 0;font-size:12.5px;color:#A8B0C7;line-height:1.5;'
        f'max-height:200px;overflow:auto;white-space:pre-wrap;word-wrap:break-word;'
        f'font-family:\'SF Mono\',Menlo,Consolas,monospace;">{safe}{cursor}</pre>'
    )


def _emit_autoscroll() -> None:
    """Inject a tiny iframe that scrolls the Streamlit page to its bottom.

    Used during Movement II so the audience always sees the currently-composing
    card without the conductor needing to scroll. Triggered once per asset
    transition (not per stream chunk) so the scroll feels deliberate, not jumpy.
    """
    components.html(
        """
        <script>
          try {
            const doc = window.parent ? window.parent.document : document;
            // Streamlit's main scroll container lives under section.main; the
            // selector list covers older + newer Streamlit versions.
            const main =
                doc.querySelector('section.main') ||
                doc.querySelector('[data-testid="stMain"]') ||
                doc.scrollingElement ||
                doc.body;
            if (main && main.scrollTo) {
              main.scrollTo({top: main.scrollHeight, behavior: 'smooth'});
            }
          } catch (e) { /* popup blockers / cross-origin -- no-op */ }
        </script>
        """,
        height=0,
    )


def render_executing_phase():
    """Movement II: Composition. Generate the 10 assets via Gemini, streaming each."""
    render_eyebrow(f"CONCERTO · {st.session_state.source_stem}")
    st.markdown(
        '<h1 class="symphony-h1" style="font-size:44px;">Composition.</h1>',
        unsafe_allow_html=True,
    )
    render_phase_rail()

    st.markdown(
        '<p class="symphony-tagline" style="font-size:15px;">'
        "Ten marketing assets composing in sequence. Each one informed by Sterling's brief, "
        "grounded in PureFacts positioning, ICP language, and brand voice."
        "</p>",
        unsafe_allow_html=True,
    )

    # Already done? Skip straight to Distribution.
    if st.session_state.composition_done:
        st.session_state.phase = "distribution"
        st.rerun()

    # Recap of strategic debate, collapsed
    render_debate_recap()
    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    if not api_key:
        st.error("GOOGLE_API_KEY missing.")
        st.stop()

    client = genai.Client(api_key=api_key)
    multiply_prompt = composer.load_multiply_prompt()
    context_bundle = agentlib.load_context_bundle()
    source_stem = st.session_state.source_stem

    # Iterate every asset. If it's already in session_state.assets (from a
    # previous attempt), we re-render the green "Complete" card and skip the
    # Gemini call -- this is what makes "Retry failed assets" cheap. Failed
    # assets get re-attempted; new failures stay tracked in assets_failed.
    for asset in composer.ASSETS:
        asset_id = asset["id"]
        card_placeholder = st.empty()
        preview_placeholder = st.empty()

        # Already composed in a prior attempt -- replay the card and move on.
        if asset_id in st.session_state.assets:
            existing = st.session_state.assets[asset_id]
            card_placeholder.markdown(
                _asset_card_html(
                    asset, "complete",
                    elapsed=existing.get("elapsed"),
                    source_stem=source_stem,
                ),
                unsafe_allow_html=True,
            )
            clean_final = distribution.strip_yaml_frontmatter(existing.get("content", ""))
            snippet = clean_final[:320] + ("..." if len(clean_final) > 320 else "")
            preview_placeholder.markdown(
                _streaming_preview_html(snippet, done=True),
                unsafe_allow_html=True,
            )
            continue

        # Fresh attempt (or a retry of a previously-failed asset).
        card_placeholder.markdown(_asset_card_html(asset, "composing"), unsafe_allow_html=True)
        # Auto-scroll the page so the active card stays in view -- once per
        # asset transition, not per stream chunk (avoids jumpy behavior).
        _emit_autoscroll()

        t0 = time.time()
        chunks: list[str] = []
        try:
            for piece in composer.stream_asset(
                client, asset, st.session_state.source_md,
                st.session_state.synth_brief, multiply_prompt, context_bundle,
            ):
                chunks.append(piece)
                so_far = "".join(chunks)
                clean = distribution.strip_yaml_frontmatter(so_far)
                tail = clean[-700:] if len(clean) > 700 else clean
                preview_placeholder.markdown(
                    _streaming_preview_html(tail, done=False),
                    unsafe_allow_html=True,
                )
        except Exception as exc:
            err_msg = friendly_error(exc, fallback_prefix="Composer hit a snag")
            st.session_state.assets_failed[asset_id] = err_msg
            card_placeholder.markdown(
                _asset_card_html(asset, "failed", error=err_msg),
                unsafe_allow_html=True,
            )
            preview_placeholder.empty()
            continue

        elapsed = time.time() - t0
        full_content = "".join(chunks)

        try:
            saved_path = composer.save_asset(source_stem, asset_id, full_content)
        except Exception as exc:
            saved_path = None
            st.warning(f"Could not save {asset_id}: {exc}")

        st.session_state.assets[asset_id] = {
            "content": full_content,
            "elapsed": elapsed,
            "saved_path": str(saved_path) if saved_path else "",
        }
        st.session_state.assets_failed.pop(asset_id, None)

        clean_final = distribution.strip_yaml_frontmatter(full_content)
        snippet = clean_final[:320] + ("..." if len(clean_final) > 320 else "")
        card_placeholder.markdown(
            _asset_card_html(asset, "complete", elapsed=elapsed, source_stem=source_stem),
            unsafe_allow_html=True,
        )
        preview_placeholder.markdown(
            _streaming_preview_html(snippet, done=True),
            unsafe_allow_html=True,
        )

    # Decide what action UI to show based on what survived.
    n_failed = len(st.session_state.assets_failed)
    n_done = len(st.session_state.assets)
    n_total = len(composer.ASSETS)

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    if n_failed == 0:
        # Clean run -- mark composition complete, offer the primary continue button.
        st.session_state.composition_done = True
        if st.button("Continue to Distribution  →", type="primary", use_container_width=False):
            st.session_state.phase = "distribution"
            st.rerun()
    else:
        # Partial run -- offer Retry (re-attempt only failures) or Continue
        # (ship the assets that did succeed). composition_done stays False
        # so the auto-skip at the top of this function doesn't fire.
        st.markdown(
            f'<div class="symphony-error-banner" style="margin:0 0 14px 0;">'
            f"{n_failed} of {n_total} assets failed to compose. "
            f"Retry to re-attempt them, or continue with the {n_done} that succeeded."
            f"</div>",
            unsafe_allow_html=True,
        )
        cols = st.columns([1, 1, 2])
        with cols[0]:
            if st.button("↻  Retry Failed Assets", type="primary", use_container_width=True):
                st.rerun()
        with cols[1]:
            if st.button(f"Continue with {n_done} →", use_container_width=True):
                st.session_state.composition_done = True
                st.session_state.phase = "distribution"
                st.rerun()


# ---------------------------------------------------------------------------
# Movement III: Distribution
# ---------------------------------------------------------------------------


CATEGORIES = [
    ("linkedin", "LinkedIn", "Two posts, ready to publish."),
    ("blog", "Blog · HubSpot CMS", "Push directly to CMS as a draft."),
    ("email", "Nurture Emails", "Top → mid → bottom of funnel, wealth manager."),
    ("sales", "Sales", "One-pager, ready for review."),
    ("outreach", "Outbound", "BDR sequence, asset manager."),
    ("enablement", "Enablement", "Talk tracks for the AE team."),
]


def render_distribution_card(asset: dict, content: str):
    """Render a single asset card with its appropriate action button(s)."""
    asset_id = asset["id"]
    ship_state = st.session_state.ship_status.get(asset_id)
    shipped = bool(ship_state and ship_state.get("ok"))
    distribution_kind = asset.get("distribution", "copy")

    card_class = "symphony-asset-card shipped" if shipped else "symphony-asset-card complete"
    status_pill = (
        '<span class="symphony-pill complete">Shipped</span>'
        if shipped
        else '<span class="symphony-pill complete">Ready</span>'
    )

    st.markdown(
        f"""
        <div class="{card_class}">
          <div class="symphony-asset-card-header">
            <div class="symphony-asset-icon">{asset['icon']}</div>
            <div class="symphony-asset-label">{asset['label']}</div>
            {status_pill}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Preview / full content (collapsible) -- strip YAML so the rendered preview is clean
    clean_body = distribution.strip_yaml_frontmatter(content)
    with st.expander("Read the asset", expanded=False):
        st.markdown(
            f'<div class="symphony-content">{escape_dollars(clean_body)}</div>',
            unsafe_allow_html=True,
        )

    # ----- Distribution action -----
    if distribution_kind == "linkedin":
        # One-click browser-side copy + open
        linkedin_copy_open_button(clean_body, button_id=f"li_btn_{asset_id}")

    elif distribution_kind == "hubspot":
        if st.button("Push to HubSpot CMS", key=f"action_hs_{asset_id}",
                     type="primary"):
            token = st.secrets.get("HUBSPOT_ACCESS_TOKEN", "")
            with st.spinner("Pushing draft to HubSpot..."):
                result = distribution.push_blog_to_hubspot(
                    token=token, asset_md=content,
                )
            st.session_state.ship_status[asset_id] = result
            st.rerun()

        if ship_state and ship_state.get("ok"):
            portal_id = ship_state.get("portal_id")
            manage_url = ship_state.get("manage_url") or distribution.hubspot_posts_url(portal_id)
            edit_url = ship_state.get("edit_url") or manage_url
            post_title = ship_state.get("title", "")
            post_id = ship_state.get("post_id", "")

            # 1) Auto-open the blog manager view (more reliable than deep-links
            #    across portal permissions + stale editor routes). We track via
            #    session_state so reruns don't keep opening tabs.
            opened_key = f"hs_opened_{asset_id}"
            if not st.session_state.get(opened_key):
                components.html(
                    f"""
                    <script>
                      try {{
                        window.open({json.dumps(manage_url)}, '_blank', 'noopener,noreferrer');
                      }} catch (e) {{}}
                    </script>
                    """,
                    height=0,
                )
                st.session_state[opened_key] = True

            # 2) Visceral success state: title + post id + reliable primary CTA.
            check_svg = icon("check-circle", size=20, color=COLORS["success"], stroke=2.0)
            ext_svg = icon("external-link", size=14, color="#FFFFFF", stroke=2.0)
            st.markdown(
                f"""
                <div class="symphony-success-banner">
                  <div style="flex-shrink:0;display:flex;align-items:center;justify-content:center;">{check_svg}</div>
                  <div style="flex:1;">
                    <div style="font-weight:700;letter-spacing:-0.1px;">Draft live in HubSpot CMS</div>
                    <div style="color:{COLORS['text_dim']};font-weight:400;font-size:13px;margin-top:2px;">
                      <strong style="color:{COLORS['text']};font-weight:600;">{escape_dollars(post_title)}</strong>
                      &nbsp;·&nbsp; Post ID <code>{post_id}</code>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<a href="{manage_url}" target="_blank" rel="noopener" '
                f'style="display:inline-flex;align-items:center;gap:8px;'
                f'margin-top:10px;padding:11px 20px;'
                f'background:{GRADIENTS["brand"]};border:none;color:white;text-decoration:none;'
                f'border-radius:12px;font-weight:600;font-size:14px;letter-spacing:0.1px;'
                f'box-shadow:0 4px 16px rgba(129,140,248,0.30);">View in HubSpot Blog Posts{ext_svg}</a>',
                unsafe_allow_html=True,
            )
            if edit_url != manage_url and "/edit/" in edit_url:
                st.markdown(
                    f'<a href="{edit_url}" target="_blank" rel="noopener" '
                    f'style="display:inline-flex;align-items:center;margin-top:8px;'
                    f'color:{COLORS["indigo"]};text-decoration:none;font-size:13px;font-weight:600;">'
                    f"Open Draft Editor Directly</a>",
                    unsafe_allow_html=True,
                )

    elif distribution_kind == "email_approval":
        if st.button("Send for Review", key=f"action_em_{asset_id}",
                     type="primary"):
            with st.spinner("Sending..."):
                result = distribution.send_asset_for_approval(
                    secrets=st.secrets,
                    asset_label=asset["label"],
                    asset_md=content,
                    source_label=st.session_state.source_stem,
                )
            st.session_state.ship_status[asset_id] = result
            st.rerun()

        if ship_state and ship_state.get("ok"):
            send_check = icon("check-circle", size=18, color=COLORS["success"], stroke=2.0)
            st.markdown(
                f"""
                <div class="symphony-success-banner">
                  <div style="flex-shrink:0;display:flex;align-items:center;justify-content:center;">{send_check}</div>
                  <div>Sent to <strong>{ship_state.get('destination', '')}</strong>. Check your inbox.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:  # copy
        universal_copy_button(clean_body, button_id=f"cp_btn_{asset_id}")

    # Render error banner if any action failed
    if ship_state and not ship_state.get("ok"):
        st.markdown(
            f'<div class="symphony-error-banner">Failed: {escape_dollars(ship_state.get("error", "unknown error"))}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)


def _format_composition_time(total_seconds: float) -> str:
    """Render a compact mm·ss / Xs label for the curtain-call composition stat."""
    if total_seconds <= 0:
        return "0s"
    rounded = int(round(total_seconds))
    if rounded < 60:
        return f"{rounded}s"
    minutes, seconds = divmod(rounded, 60)
    return f"{minutes}m {seconds:02d}s"


def render_curtain_call():
    """Closing 'Conductor's Curtain Call' panel for Movement III.

    Replaces the bare 'New Performance' button with a calm finale:
    brand mark, headline, three honest stats, a closing line, and a
    single primary 'Encore' CTA. No game elements -- this is the bow,
    not another act.
    """
    n_assets = len(st.session_state.assets)
    n_shipped = sum(
        1 for s in st.session_state.ship_status.values() if s and s.get("ok")
    )
    shipped_categories = {
        a["category"]
        for a in composer.ASSETS
        if (st.session_state.ship_status.get(a["id"]) or {}).get("ok")
    }
    n_channels = len(shipped_categories)

    total_compose_seconds = sum(
        float(meta.get("elapsed") or 0.0)
        for meta in st.session_state.assets.values()
    )
    compose_label = _format_composition_time(total_compose_seconds)

    sparkle = icon("sparkles", size=24, color="#FFFFFF", stroke=2.0)
    source_label = escape_dollars(st.session_state.source_stem or "this performance")

    st.markdown(
        f"""
        <div class="symphony-curtain">
          <div class="symphony-curtain-mark">{sparkle}</div>
          <div class="symphony-curtain-eyebrow">Finale · The Curtain Call</div>
          <h2 class="symphony-curtain-title">Performance complete.</h2>
          <p class="symphony-curtain-subtitle">
            {source_label} composed, distributed, and delivered. The campaign is in market.
          </p>

          <div class="symphony-curtain-stats">
            <div class="symphony-curtain-stat">
              <div class="symphony-curtain-stat-value">{n_assets}</div>
              <div class="symphony-curtain-stat-label">Assets composed</div>
            </div>
            <div class="symphony-curtain-stat-divider"></div>
            <div class="symphony-curtain-stat">
              <div class="symphony-curtain-stat-value">{n_shipped}</div>
              <div class="symphony-curtain-stat-label">Assets shipped</div>
            </div>
            <div class="symphony-curtain-stat-divider"></div>
            <div class="symphony-curtain-stat">
              <div class="symphony-curtain-stat-value">{n_channels}</div>
              <div class="symphony-curtain-stat-label">Channels activated</div>
            </div>
            <div class="symphony-curtain-stat-divider"></div>
            <div class="symphony-curtain-stat">
              <div class="symphony-curtain-stat-value">{compose_label}</div>
              <div class="symphony-curtain-stat-label">Composition time</div>
            </div>
          </div>

          <p class="symphony-curtain-tagline">
            From <strong>one source</strong>, a complete campaign.<br>
            Three movements. One performance. <strong>Yours.</strong>
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    cols = st.columns([1, 1, 2])
    with cols[0]:
        if st.button("Encore — New Performance", type="primary", use_container_width=True):
            reset_session_to_defaults()
            st.rerun()
    with cols[1]:
        if st.button("Return to Upload", use_container_width=True):
            reset_session_to_defaults()
            st.session_state.phase = "idle"
            st.rerun()


def render_distribution_phase():
    render_eyebrow(f"CONCERTO · {st.session_state.source_stem}")
    st.markdown(
        '<h1 class="symphony-h1" style="font-size:44px;">Distribution.</h1>',
        unsafe_allow_html=True,
    )
    render_phase_rail()

    n_assets = len(st.session_state.assets)
    n_shipped = sum(
        1 for s in st.session_state.ship_status.values() if s and s.get("ok")
    )
    st.markdown(
        f'<p class="symphony-tagline" style="font-size:15px;">'
        f"<strong>{n_assets} assets composed.</strong> Ship each to its destination — "
        f"LinkedIn, HubSpot CMS, the team's inbox. <strong style=\"color:{COLORS['success']};\">{n_shipped} shipped.</strong>"
        f"</p>",
        unsafe_allow_html=True,
    )

    # Recap of strategic debate, collapsed
    render_debate_recap()
    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    # Group assets by category and render
    for cat_id, cat_title, cat_subtitle in CATEGORIES:
        cat_assets = [a for a in composer.ASSETS if a["category"] == cat_id]
        if not cat_assets:
            continue
        st.markdown(
            f"""
            <div class="symphony-category-header">
              <div style="flex:1;">
                <div class="symphony-category-title">{cat_title}</div>
                <div style="color:{COLORS['text_mute']};font-size:13px;margin-top:2px;">{cat_subtitle}</div>
              </div>
              <div class="symphony-category-count">{len(cat_assets)} asset{'s' if len(cat_assets) > 1 else ''}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for asset in cat_assets:
            content = st.session_state.assets.get(asset["id"], {}).get("content", "")
            if content:
                render_distribution_card(asset, content)

    render_curtain_call()


# ---------------------------------------------------------------------------
# Main router
# ---------------------------------------------------------------------------

# Magic link arrival -- if URL has ?token=...&action=approve, handle and stop
handle_magic_link()

phase = st.session_state.phase
if phase == "preview":
    render_preview_page()
elif phase == "idle":
    render_idle_page()
elif phase == "intelligence":
    render_intelligence_phase()
elif phase == "awaiting_approval":
    render_awaiting_approval_page()
elif phase == "executing":
    render_executing_phase()
elif phase == "distribution":
    render_distribution_phase()
else:
    st.error(f"Unknown phase: {phase}")
    if st.button("Reset"):
        reset_session_to_defaults()
        st.rerun()
