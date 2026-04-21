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
from lib.theme import COLORS, GRADIENTS, inject_theme  # noqa: E402

# ---------------------------------------------------------------------------
# Page config + theme
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Concerto · Project Symphony",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme(st)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MOVEMENTS = [
    ("intelligence", "Movement I · Intelligence"),
    ("awaiting_approval", "Movement II · Approval"),
    ("executing", "Movement III · Composition"),
    ("distribution", "Movement IV · Distribution"),
]
ORDER = ["preview", "idle", "intelligence", "awaiting_approval", "executing", "distribution"]


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

DEFAULTS = {
    "phase": "preview",             # preview | idle | intelligence | awaiting_approval | executing | distribution
    "source_stem": "",
    "source_md": "",
    "debate_history": [],
    "synth_brief": "",
    "approval_token": "",
    "approval_email_sent": False,
    "approved": False,
    "started_at": None,
    "phase1_elapsed": None,
    "magic_link_arrived": False,    # True when this session loaded with ?token=...&action=approve
    # Movement III/IV state
    "assets": {},                   # {asset_id: {"content": str, "elapsed": float, "saved_path": str}}
    "composition_done": False,
    "ship_status": {},              # {asset_id: {"ok": bool, "msg": str, "url": str?}}
}
for _k, _v in DEFAULTS.items():
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
        # Render confirmation page and stop
        st.markdown(
            f"""
            <div style="padding:48px 0;text-align:center;">
              <div style="font-size:48px;margin-bottom:16px;">◆</div>
              <h1 class="symphony-h1" style="font-size:42px;">Approval received.</h1>
              <p style="color:{COLORS['text_dim']};font-size:17px;max-width:520px;margin:16px auto;">
                Concerto is now executing the campaign. Return to your original Symphony tab to watch the composition unfold in real time.
              </p>
              <div style="margin-top:32px;color:{COLORS['text_mute']};font-size:13px;letter-spacing:1.4px;text-transform:uppercase;">
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
    st.markdown(
        f'<div style="margin-bottom:8px;"><span class="symphony-eyebrow">◈ {label}</span></div>',
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
    for i, (phase_id, label) in enumerate(MOVEMENTS):
        if i < current_idx:
            cls = "complete"
        elif i == current_idx:
            cls = "active"
        else:
            cls = ""
        parts.append(
            f'<div class="symphony-phase-step {cls}">'
            f'<span class="symphony-phase-dot"></span>'
            f"<span>{label}</span>"
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


def render_debate_recap():
    """Re-render the strategic debate from session state. Used on Movements II/III/IV
    so the conductor can refer back to the debate at any time."""
    history = st.session_state.get("debate_history") or []
    brief = st.session_state.get("synth_brief") or ""
    if not history and not brief:
        return

    with st.expander("◇  View the strategic debate  ·  Movement I recap", expanded=False):
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
            st.markdown(
                f'<div style="font-size:11px;letter-spacing:1.4px;color:{COLORS["text_mute"]};text-transform:uppercase;font-weight:600;margin:24px 0 10px 0;">◆ Sterling\'s Brief</div>',
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
    html = f"""
    <div style="margin:8px 0;">
      <button id="{button_id}" style="
        background: linear-gradient(135deg, #818CF8 0%, #A78BFA 50%, #E879F9 100%);
        color: white;
        border: none;
        padding: 12px 22px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 14px;
        cursor: pointer;
        letter-spacing: 0.3px;
        box-shadow: 0 4px 16px rgba(129,140,248,0.30);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      ">in  {label}  ↗</button>
      <span id="{button_id}_status" style="margin-left:14px;color:#34D399;font-size:13px;font-weight:600;display:none;">✓ Copied</span>
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
    html = f"""
    <div style="margin:8px 0;">
      <button id="{button_id}" style="
        background: #1E2748;
        color: #F1F5F9;
        border: 1px solid #283354;
        padding: 10px 18px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
        cursor: pointer;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      ">⧉  {label}</button>
      <span id="{button_id}_status" style="margin-left:14px;color:#34D399;font-size:13px;font-weight:600;display:none;">✓ Copied to clipboard</span>
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

    cards = [
        {
            "movement": "Movement I",
            "title": "Intelligence",
            "icon": "◇",
            "duration": "~60 seconds",
            "desc": "Two AI strategists — Maya for brand, Marcus for pipeline — debate the best campaign play for the source document. Sterling, the Director, synthesizes the argument into the brief.",
        },
        {
            "movement": "Movement II",
            "title": "Approval",
            "icon": "◆",
            "duration": "~30 seconds",
            "desc": "The brief routes to the conductor's inbox. Read. Approve. Or send back for refinement. The orchestra waits for the cue.",
        },
        {
            "movement": "Movement III",
            "title": "Composition",
            "icon": "◈",
            "duration": "~90 seconds",
            "desc": "Concerto composes ten marketing assets in the PureFacts voice and ships each to its destination — LinkedIn, HubSpot CMS, the team's inbox. Distribution follows the score.",
        },
    ]

    # Collapsible composition cards -- collapsed by default so the conductor can
    # speak first, then expand on cue during the demo.
    with st.expander("◇  The Composition  ·  three movements", expanded=False):
        cols = st.columns(3, gap="medium")
        for col, card in zip(cols, cards):
            with col:
                st.markdown(
                    f"""
                    <div class="symphony-card" style="height:300px;display:flex;flex-direction:column;justify-content:space-between;">
                      <div>
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                          <span style="font-size:18px;color:{COLORS['indigo']};">{card['icon']}</span>
                          <span class="symphony-eyebrow" style="opacity:0.85;">{card['movement']}</span>
                        </div>
                        <div style="font-size:24px;font-weight:700;color:{COLORS['text']};margin-bottom:10px;">{card['title']}</div>
                        <div style="font-size:14px;color:{COLORS['text_dim']};line-height:1.55;">{card['desc']}</div>
                      </div>
                      <div style="font-size:11px;letter-spacing:1.4px;color:{COLORS['text_mute']};text-transform:uppercase;font-weight:600;margin-top:14px;">{card['duration']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("◈  Take the Podium  →", type="primary", use_container_width=True):
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

    cols = st.columns([1, 2])
    with cols[0]:
        begin = st.button(
            "◈  Compose Magic",
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

    st.markdown(
        '<div class="symphony-section-label">◇ Movement I · Intelligence</div>',
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
    st.markdown(
        '<div class="symphony-section-label">◆ Synthesis</div>',
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
    st.markdown(
        '<h1 class="symphony-h1" style="font-size:44px;">Composing.</h1>',
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
    history, brief = run_intelligence_phase(client, st.session_state.source_md)
    st.session_state.debate_history = history
    st.session_state.synth_brief = brief
    st.session_state.phase1_elapsed = time.time() - (st.session_state.started_at or time.time())

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
        st.markdown(
            f"""
            <div class="symphony-card-glow" style="margin:18px 0;">
              <div style="display:flex;align-items:center;gap:14px;">
                <div style="font-size:32px;" class="symphony-pulse">📨</div>
                <div style="flex:1;">
                  <div style="font-weight:700;font-size:16px;color:{COLORS['text']};">Brief delivered to your inbox</div>
                  <div style="color:{COLORS['text_dim']};font-size:14px;margin-top:2px;">
                    Open <strong>{st.secrets.get('APPROVAL_EMAIL', '')}</strong> and click <strong>Approve and Execute</strong>. This page will advance automatically.
                  </div>
                </div>
                <span class="symphony-pill streaming">Polling</span>
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
        for k in DEFAULTS:
            st.session_state[k] = DEFAULTS[k]
        st.rerun()


def _asset_card_html(asset: dict, status: str, elapsed: float | None = None) -> str:
    """Render the asset card header HTML with the right status pill + border."""
    if status == "composing":
        card_cls = "symphony-asset-card composing"
        pill_html = '<span class="symphony-pill streaming">Composing</span>'
        meta = ""
    elif status == "complete":
        card_cls = "symphony-asset-card complete"
        pill_html = '<span class="symphony-pill complete">Complete</span>'
        meta = (
            f'<div style="font-size:11px;letter-spacing:0.4px;color:{COLORS["text_mute"]};margin-top:6px;">'
            f"Composed in {elapsed:.1f}s · saved to /output/{escape_dollars(asset['id'])}.md"
            f"</div>"
        ) if elapsed is not None else ""
    else:
        card_cls = "symphony-asset-card"
        pill_html = '<span class="symphony-pill pending">Pending</span>'
        meta = ""

    return f"""
    <div class="{card_cls}">
      <div class="symphony-asset-card-header">
        <div class="symphony-asset-icon">{asset['icon']}</div>
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


def render_executing_phase():
    """Movement III: Composition. Generate the 10 assets via Gemini, streaming each."""
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

    composed: dict[str, dict] = {}

    for asset in composer.ASSETS:
        # Per-asset placeholders (so we can update card AND preview on completion)
        card_placeholder = st.empty()
        preview_placeholder = st.empty()

        # Initial composing state
        card_placeholder.markdown(_asset_card_html(asset, "composing"), unsafe_allow_html=True)

        t0 = time.time()
        chunks: list[str] = []
        try:
            for piece in composer.stream_asset(
                client, asset, st.session_state.source_md,
                st.session_state.synth_brief, multiply_prompt, context_bundle,
            ):
                chunks.append(piece)
                # Strip YAML noise + show last ~700 chars in a clean monospace box
                so_far = "".join(chunks)
                clean = distribution.strip_yaml_frontmatter(so_far)
                tail = clean[-700:] if len(clean) > 700 else clean
                preview_placeholder.markdown(
                    _streaming_preview_html(tail, done=False),
                    unsafe_allow_html=True,
                )
        except Exception as exc:
            card_placeholder.markdown(_asset_card_html(asset, "composing"), unsafe_allow_html=True)
            preview_placeholder.markdown(
                f'<div class="symphony-error-banner">Composition failed: {escape_dollars(str(exc))}</div>',
                unsafe_allow_html=True,
            )
            continue

        elapsed = time.time() - t0
        full_content = "".join(chunks)

        try:
            saved_path = composer.save_asset(
                st.session_state.source_stem, asset["id"], full_content
            )
        except Exception as exc:
            saved_path = None
            st.warning(f"Could not save {asset['id']}: {exc}")

        composed[asset["id"]] = {
            "content": full_content,
            "elapsed": elapsed,
            "saved_path": str(saved_path) if saved_path else "",
        }

        # Final state: green "Complete" card + clean preview snippet
        clean_final = distribution.strip_yaml_frontmatter(full_content)
        snippet = clean_final[:320] + ("..." if len(clean_final) > 320 else "")
        card_placeholder.markdown(_asset_card_html(asset, "complete", elapsed=elapsed), unsafe_allow_html=True)
        preview_placeholder.markdown(
            _streaming_preview_html(snippet, done=True),
            unsafe_allow_html=True,
        )

    st.session_state.assets = composed
    st.session_state.composition_done = True
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    if st.button("◈  Continue to Distribution  →", type="primary", use_container_width=False):
        st.session_state.phase = "distribution"
        st.rerun()


# ---------------------------------------------------------------------------
# Movement IV: Distribution
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
        if st.button("◈  Push to HubSpot CMS", key=f"action_hs_{asset_id}",
                     type="primary"):
            token = st.secrets.get("HUBSPOT_ACCESS_TOKEN", "")
            with st.spinner("Pushing draft to HubSpot..."):
                result = distribution.push_blog_to_hubspot(
                    token=token, asset_md=content,
                )
            st.session_state.ship_status[asset_id] = result
            st.rerun()

        if ship_state and ship_state.get("ok"):
            st.markdown(
                f"""
                <div class="symphony-success-banner">
                  <div class="dot"></div>
                  <div>Draft created in HubSpot CMS. Post ID: <code>{ship_state.get('post_id', '')}</code></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<a href="https://app.hubspot.com/" target="_blank" '
                f'style="display:inline-block;margin-top:4px;padding:10px 18px;background:{COLORS["surface_2"]};'
                f'border:1px solid {COLORS["border_lift"]};color:{COLORS["text"]};text-decoration:none;'
                f'border-radius:12px;font-weight:600;font-size:13px;">Open HubSpot ↗</a>',
                unsafe_allow_html=True,
            )

    elif distribution_kind == "email_approval":
        if st.button("✉  Send for Review", key=f"action_em_{asset_id}",
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
            st.markdown(
                f"""
                <div class="symphony-success-banner">
                  <div class="dot"></div>
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
    asset_by_id = {a["id"]: a for a in composer.ASSETS}
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

    st.markdown('<div style="height:36px;"></div>', unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("↻  New Performance", use_container_width=True):
            for k in DEFAULTS:
                st.session_state[k] = DEFAULTS[k]
            st.rerun()


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
        for k in DEFAULTS:
            st.session_state[k] = DEFAULTS[k]
        st.rerun()
