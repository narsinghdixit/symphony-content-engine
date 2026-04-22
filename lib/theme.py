"""Symphony design system -- color tokens, typography, custom CSS injection."""

# Color tokens (also reflected in .streamlit/config.toml)
COLORS = {
    # Surfaces
    "bg":          "#0B1020",   # Deep navy-black, the canvas
    "surface_1":   "#141B33",   # Card backgrounds
    "surface_2":   "#1E2748",   # Elevated cards
    "surface_3":   "#2A3556",   # Hover / focus states
    "border":      "#283354",   # Subtle dividers
    "border_lift": "#3A4670",   # Brighter borders for emphasis

    # Text
    "text":        "#F1F5F9",   # Primary text
    "text_dim":    "#A8B0C7",   # Secondary text
    "text_mute":   "#6B748E",   # Tertiary / captions
    "text_inv":    "#0B1020",   # Text on light surfaces

    # Brand accents
    "indigo":      "#818CF8",   # Symphony primary
    "violet":      "#A78BFA",   # Synthesizer / decision moments
    "fuchsia":     "#E879F9",   # Highlight / streaming cursor
    "cyan":        "#67E8F9",   # Agent A: brand strategist (cool)
    "amber":       "#FBBF24",   # Agent B: pipeline strategist (warm)

    # Status
    "success":     "#34D399",   # Approval / publish
    "warn":        "#FBBF24",
    "danger":      "#FB7185",
    "info":        "#818CF8",
}

GRADIENTS = {
    "brand":      "linear-gradient(135deg, #818CF8 0%, #A78BFA 50%, #E879F9 100%)",
    "agent_a":    "linear-gradient(135deg, #67E8F9 0%, #818CF8 100%)",
    "agent_b":    "linear-gradient(135deg, #FBBF24 0%, #FB7185 100%)",
    "synth":      "linear-gradient(135deg, #A78BFA 0%, #E879F9 100%)",
    "success":    "linear-gradient(135deg, #34D399 0%, #67E8F9 100%)",
    "subtle":     "linear-gradient(180deg, rgba(129,140,248,0.08) 0%, rgba(167,139,250,0) 100%)",
}


CUSTOM_CSS = f"""
<style>
/* ---------- Reset Streamlit chrome ---------- */
#MainMenu {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
footer {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}

/* ---------- Base layout ---------- */
.stApp {{
    background: radial-gradient(ellipse at top, #1E2748 0%, {COLORS['bg']} 60%);
    background-attachment: fixed;
    color: {COLORS['text']};
}}

.block-container {{
    padding-top: 2.5rem !important;
    padding-bottom: 6rem !important;
    max-width: 1200px !important;
}}

/* ---------- Typography ---------- */
.symphony-eyebrow {{
    font-size: 11px;
    letter-spacing: 2.4px;
    font-weight: 700;
    text-transform: uppercase;
    color: {COLORS['indigo']};
    opacity: 0.95;
}}

.symphony-h1 {{
    font-size: 56px;
    font-weight: 800;
    letter-spacing: -1.5px;
    line-height: 1.05;
    margin: 8px 0 12px 0;
    background: {GRADIENTS['brand']};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.symphony-tagline {{
    font-size: 17px;
    color: {COLORS['text_dim']};
    line-height: 1.55;
    max-width: 720px;
    margin-bottom: 32px;
}}

.symphony-h2 {{
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: {COLORS['text']};
    margin: 0 0 8px 0;
}}

.symphony-section-label {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 999px;
    background: rgba(129, 140, 248, 0.10);
    border: 1px solid rgba(129, 140, 248, 0.30);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {COLORS['indigo']};
    margin-bottom: 12px;
}}

/* ---------- Cards ---------- */
.symphony-card {{
    background: {COLORS['surface_1']};
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
    padding: 24px 28px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.20);
    transition: all 200ms ease;
}}

.symphony-card:hover {{
    border-color: {COLORS['border_lift']};
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.28);
}}

.symphony-card-glow {{
    background: {COLORS['surface_1']};
    border: 1px solid transparent;
    border-radius: 16px;
    padding: 24px 28px;
    background-image:
      linear-gradient({COLORS['surface_1']}, {COLORS['surface_1']}),
      {GRADIENTS['brand']};
    background-origin: border-box;
    background-clip: padding-box, border-box;
    box-shadow: 0 8px 40px rgba(129, 140, 248, 0.18);
}}

/* ---------- Agent panels ---------- */
.symphony-agent-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 12px;
    margin-bottom: 14px;
    border-bottom: 1px solid {COLORS['border']};
}}

.symphony-agent-avatar {{
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
}}

.symphony-agent-avatar.a {{ background: {GRADIENTS['agent_a']}; }}
.symphony-agent-avatar.b {{ background: {GRADIENTS['agent_b']}; }}
.symphony-agent-avatar.s {{ background: {GRADIENTS['synth']}; }}

.symphony-agent-name {{
    font-size: 15px;
    font-weight: 700;
    color: {COLORS['text']};
    line-height: 1.1;
}}

.symphony-agent-title {{
    font-size: 12px;
    color: {COLORS['text_mute']};
    margin-top: 2px;
}}

/* ---------- Status pills ---------- */
.symphony-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}}

.symphony-pill.thinking {{
    background: rgba(129, 140, 248, 0.16);
    border: 1px solid rgba(129, 140, 248, 0.36);
    color: {COLORS['indigo']};
}}

.symphony-pill.streaming {{
    background: rgba(232, 121, 249, 0.16);
    border: 1px solid rgba(232, 121, 249, 0.36);
    color: {COLORS['fuchsia']};
}}

.symphony-pill.complete {{
    background: rgba(52, 211, 153, 0.16);
    border: 1px solid rgba(52, 211, 153, 0.40);
    color: {COLORS['success']};
}}

.symphony-pill.pending {{
    background: rgba(168, 176, 199, 0.10);
    border: 1px solid rgba(168, 176, 199, 0.24);
    color: {COLORS['text_dim']};
}}

.symphony-pill.failed {{
    background: rgba(251, 113, 133, 0.16);
    border: 1px solid rgba(251, 113, 133, 0.40);
    color: {COLORS['danger']};
}}

/* ---------- Buttons (custom on top of Streamlit) ---------- */
.stButton > button {{
    border-radius: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    border: 1px solid {COLORS['border']} !important;
    background: {COLORS['surface_2']} !important;
    color: {COLORS['text']} !important;
    transition: all 150ms ease !important;
    padding: 10px 18px !important;
}}

.stButton > button:hover {{
    border-color: {COLORS['indigo']} !important;
    background: {COLORS['surface_3']} !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(129, 140, 248, 0.20);
}}

.stButton > button[kind="primary"] {{
    background: {GRADIENTS['brand']} !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 16px rgba(129, 140, 248, 0.30);
}}

.stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(129, 140, 248, 0.45) !important;
}}

/* ---------- File uploader ---------- */
[data-testid="stFileUploader"] section {{
    background: {COLORS['surface_1']} !important;
    border: 2px dashed {COLORS['border_lift']} !important;
    border-radius: 16px !important;
    padding: 32px !important;
    transition: all 200ms ease;
}}

[data-testid="stFileUploader"] section:hover {{
    border-color: {COLORS['indigo']} !important;
    background: {COLORS['surface_2']} !important;
}}

[data-testid="stFileUploader"] small {{
    color: {COLORS['text_mute']} !important;
}}

/* ---------- Streaming cursor animation ---------- */
.symphony-cursor {{
    display: inline-block;
    width: 2px;
    height: 1em;
    background: {COLORS['fuchsia']};
    margin-left: 2px;
    vertical-align: text-bottom;
    animation: blink 0.9s steps(2, start) infinite;
}}

@keyframes blink {{
    to {{ visibility: hidden; }}
}}

/* ---------- Pulse for thinking states ---------- */
.symphony-pulse {{
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.55; }}
}}

/* ---------- Markdown content inside cards ---------- */
.symphony-content p {{
    color: {COLORS['text_dim']};
    line-height: 1.62;
    margin-bottom: 0.65em;
}}

.symphony-content h1, .symphony-content h2, .symphony-content h3 {{
    color: {COLORS['text']};
    font-weight: 700;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
}}

.symphony-content strong {{ color: {COLORS['text']}; }}

.symphony-content blockquote {{
    border-left: 3px solid {COLORS['indigo']};
    padding-left: 14px;
    color: {COLORS['text_dim']};
    margin: 12px 0;
}}

/* ---------- Sidebar polish ---------- */
[data-testid="stSidebar"] {{
    background: {COLORS['surface_1']} !important;
    border-right: 1px solid {COLORS['border']};
}}

/* ---------- Phase progress bar ---------- */
.symphony-phase-rail {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 32px;
    padding: 12px 0;
}}

.symphony-phase-step {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    color: {COLORS['text_mute']};
    transition: color 200ms ease;
}}

.symphony-phase-step.active {{
    color: {COLORS['indigo']};
}}

.symphony-phase-step.complete {{
    color: {COLORS['success']};
}}

.symphony-phase-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: {COLORS['surface_3']};
    border: 2px solid {COLORS['border']};
    transition: all 200ms ease;
}}

.symphony-phase-step.active .symphony-phase-dot {{
    background: {COLORS['indigo']};
    border-color: {COLORS['indigo']};
    box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.20);
}}

.symphony-phase-step.complete .symphony-phase-dot {{
    background: {COLORS['success']};
    border-color: {COLORS['success']};
}}

.symphony-phase-line {{
    flex: 1;
    height: 1px;
    background: {COLORS['border']};
    max-width: 60px;
}}

/* Cue rail step: a structural pause between movements (the conductor's cue). */
/* Same dot size so it doesn't read as "lesser," but italic label + violet tint */
/* makes it visually distinct from the numbered Movement steps. */
.symphony-phase-step.cue {{
    color: {COLORS['violet']};
    font-style: italic;
    letter-spacing: 0.6px;
}}

.symphony-phase-step.cue.active {{
    color: {COLORS['fuchsia']};
}}

.symphony-phase-step.cue .symphony-phase-dot {{
    background: transparent;
    border-color: {COLORS['violet']};
    border-style: dashed;
}}

.symphony-phase-step.cue.active .symphony-phase-dot {{
    background: {COLORS['violet']};
    border-style: solid;
    box-shadow: 0 0 0 4px rgba(167, 139, 250, 0.20);
}}

.symphony-phase-step.cue.complete .symphony-phase-dot {{
    background: {COLORS['violet']};
    border-color: {COLORS['violet']};
    border-style: solid;
}}

/* ---------- Expander (composition reveal) ---------- */
[data-testid="stExpander"] details {{
    background: {COLORS['surface_1']} !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: 14px !important;
    transition: all 200ms ease;
}}

[data-testid="stExpander"] details:hover {{
    border-color: {COLORS['border_lift']} !important;
}}

[data-testid="stExpander"] summary {{
    padding: 16px 20px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 1.4px !important;
    text-transform: uppercase !important;
    color: {COLORS['indigo']} !important;
    border-radius: 14px !important;
}}

[data-testid="stExpander"] summary:hover {{
    color: {COLORS['violet']} !important;
}}

[data-testid="stExpander"] details[open] summary {{
    border-bottom: 1px solid {COLORS['border']} !important;
    border-radius: 14px 14px 0 0 !important;
}}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    padding: 24px 20px !important;
}}

/* ---------- Asset cards (Movement III/IV) ---------- */
.symphony-asset-card {{
    background: {COLORS['surface_1']};
    border: 1px solid {COLORS['border']};
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 12px;
    transition: all 200ms ease;
    position: relative;
}}

.symphony-asset-card.complete {{
    border-color: rgba(52, 211, 153, 0.30);
}}

.symphony-asset-card.composing {{
    border-color: rgba(232, 121, 249, 0.40);
    background-image: linear-gradient(180deg, rgba(232, 121, 249, 0.06) 0%, rgba(232, 121, 249, 0) 60%);
}}

.symphony-asset-card.shipped {{
    border-color: rgba(52, 211, 153, 0.50);
    background-image: linear-gradient(180deg, rgba(52, 211, 153, 0.08) 0%, rgba(52, 211, 153, 0) 60%);
}}

.symphony-asset-card.failed {{
    border-color: rgba(251, 113, 133, 0.50);
    background-image: linear-gradient(180deg, rgba(251, 113, 133, 0.08) 0%, rgba(251, 113, 133, 0) 60%);
}}

.symphony-asset-card-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}}

.symphony-asset-icon {{
    width: 32px;
    height: 32px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    background: {GRADIENTS['brand']};
    color: white;
    flex-shrink: 0;
}}

.symphony-asset-label {{
    font-weight: 700;
    font-size: 15px;
    color: {COLORS['text']};
    flex: 1;
}}

.symphony-category-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 28px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid {COLORS['border']};
}}

.symphony-category-title {{
    font-size: 18px;
    font-weight: 700;
    color: {COLORS['text']};
    letter-spacing: -0.3px;
}}

.symphony-category-count {{
    font-size: 11px;
    letter-spacing: 1.4px;
    color: {COLORS['text_mute']};
    text-transform: uppercase;
    font-weight: 600;
}}

.symphony-success-banner {{
    background: linear-gradient(135deg, rgba(52, 211, 153, 0.16) 0%, rgba(103, 232, 249, 0.10) 100%);
    border: 1px solid rgba(52, 211, 153, 0.40);
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0 4px 0;
    display: flex;
    align-items: center;
    gap: 12px;
    color: {COLORS['success']};
    font-size: 14px;
    font-weight: 600;
}}

.symphony-success-banner .dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {COLORS['success']};
    box-shadow: 0 0 0 4px rgba(52, 211, 153, 0.20);
    flex-shrink: 0;
}}

.symphony-error-banner {{
    background: rgba(251, 113, 133, 0.10);
    border: 1px solid rgba(251, 113, 133, 0.36);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
    color: {COLORS['danger']};
    font-size: 13px;
}}

.symphony-asset-preview {{
    background: {COLORS['bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 14px 16px;
    margin: 8px 0 12px 0;
    font-size: 13px;
    color: {COLORS['text_dim']};
    line-height: 1.55;
    max-height: 180px;
    overflow: hidden;
    position: relative;
}}

.symphony-asset-preview::after {{
    content: "";
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 40px;
    background: linear-gradient(180deg, transparent 0%, {COLORS['bg']} 100%);
    pointer-events: none;
}}

/* ---------- Composer progress rail ---------- */
.symphony-progress-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
    font-size: 14px;
    color: {COLORS['text_dim']};
}}

.symphony-progress-marker {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 2px solid {COLORS['border']};
    background: {COLORS['surface_2']};
    flex-shrink: 0;
}}

.symphony-progress-marker.active {{
    background: {COLORS['fuchsia']};
    border-color: {COLORS['fuchsia']};
    box-shadow: 0 0 0 4px rgba(232, 121, 249, 0.16);
    animation: pulse 1.4s ease-in-out infinite;
}}

.symphony-progress-marker.done {{
    background: {COLORS['success']};
    border-color: {COLORS['success']};
}}

/* ---------- Loading shimmer ---------- */
.symphony-shimmer {{
    background: linear-gradient(
        90deg,
        {COLORS['surface_1']} 0%,
        {COLORS['surface_2']} 50%,
        {COLORS['surface_1']} 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.4s ease-in-out infinite;
    border-radius: 6px;
}}

@keyframes shimmer {{
    0% {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}

/* ---------- Mobile responsiveness ---------- */
/* Townhall audience may peek on phones. The phase rail at 4 stops + 3
   connectors overflows horizontally on iPhone-width viewports without these
   tweaks. The H1 at 56px also dominates a portrait phone screen. */
@media (max-width: 600px) {{
    .symphony-h1 {{
        font-size: 36px !important;
        letter-spacing: -1px !important;
    }}
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
    }}
    /* Phase rail wraps to a vertical stack on phones; the connector lines
       collapse so the steps remain readable end-to-end. */
    .symphony-phase-rail {{
        flex-wrap: wrap;
        gap: 8px 12px;
    }}
    .symphony-phase-step {{
        font-size: 11px;
        letter-spacing: 0.3px;
    }}
    .symphony-phase-line {{
        max-width: 18px;
    }}
    .symphony-tagline {{
        font-size: 15px;
    }}
}}
</style>
"""


def inject_theme(st_module) -> None:
    """Inject Symphony custom CSS. Call once at the top of app.py after st.set_page_config."""
    st_module.markdown(CUSTOM_CSS, unsafe_allow_html=True)
