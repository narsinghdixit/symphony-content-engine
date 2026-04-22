"""Symphony design system -- color tokens, typography, custom CSS injection.

V2 design lift (Apr 2026):
- Custom typography: Geist Sans for body, Geist Mono for streaming preview.
  Inter is the fallback. System fonts are the final fallback.
- Restrained color palette: indigo is THE accent. Violet/fuchsia exist only
  as gradient stops (signature gradient on Concerto wordmark + primary CTA).
  Maya = sky blue, Marcus = warm gold (warm/cool flanks).
- Border radius scale standardized: 6 (small chips), 12 (medium buttons/cards),
  16 (large panels), 999 (pills only).
- Card hover: brightness/border lift instead of translateY (app pattern, not
  marketing-website pattern).
- Hero motion: ambient breathing orb glow behind the wordmark on the preview.
- Background: near-solid #0A0E1A canvas with a single soft glow + subtle noise
  texture overlay (Anthropic / Vercel pattern).
- Phase rail: refined progress indicator with gradient connector fill.
- Streaming cursor: thin bar with soft glow, slower rhythm (1.2s).

These tokens are also reflected in .streamlit/config.toml at the file level.
"""

# ---------------------------------------------------------------------------
# Color tokens
# ---------------------------------------------------------------------------

COLORS = {
    # Surfaces
    "bg":          "#0A0E1A",   # near-black canvas with hint of blue
    "surface_1":   "#11172B",   # card backgrounds
    "surface_2":   "#1A2240",   # elevated cards
    "surface_3":   "#252E54",   # hover / focus
    "border":      "#252E54",   # subtle dividers
    "border_lift": "#3B4870",   # brighter borders for emphasis

    # Text
    "text":        "#F1F5F9",   # primary
    "text_dim":    "#A8B0C7",   # secondary
    "text_mute":   "#6B748E",   # tertiary / captions
    "text_inv":    "#0A0E1A",   # text on light surfaces

    # Brand -- single primary accent, gradient stops, agent flanks
    "indigo":      "#818CF8",   # PRIMARY accent (links, focus, phase rail)
    "violet":      "#A78BFA",   # gradient stop only (do not use solo)
    "fuchsia":     "#E879F9",   # gradient stop + streaming cursor only

    # Agent accents (warm/cool flanks around the gradient signature)
    "maya":        "#7DD3FC",   # sky-300, brand strategist (cool)
    "marcus":      "#F59E0B",   # amber-500, pipeline strategist (warm)

    # Status
    "success":     "#34D399",
    "warn":        "#F59E0B",
    "danger":      "#FB7185",
    "info":        "#818CF8",

    # Legacy aliases kept for back-compat with code that read them directly.
    "cyan":        "#7DD3FC",   # -> maya
    "amber":       "#F59E0B",   # -> marcus
}

GRADIENTS = {
    # THE signature gradient. Used scarce: wordmark + primary CTA + Sterling
    # avatar + success banner background. Nowhere else.
    "brand":      "linear-gradient(135deg, #818CF8 0%, #A78BFA 50%, #E879F9 100%)",
    # Agent gradients are the avatar rendering only.
    "agent_a":    "linear-gradient(135deg, #7DD3FC 0%, #818CF8 100%)",
    "agent_b":    "linear-gradient(135deg, #F59E0B 0%, #FB923C 100%)",
    "synth":      "linear-gradient(135deg, #A78BFA 0%, #E879F9 100%)",
    "success":    "linear-gradient(135deg, #34D399 0%, #7DD3FC 100%)",
    "subtle":     "linear-gradient(180deg, rgba(129,140,248,0.08) 0%, rgba(167,139,250,0) 100%)",
}

# ---------------------------------------------------------------------------
# Border radius scale
# ---------------------------------------------------------------------------

RADIUS = {
    "sm":   "6px",    # chips, status pill inner blocks
    "md":   "12px",   # buttons, asset cards, expanders
    "lg":   "16px",   # large panels, hero cards
    "pill": "999px",  # pills only
}


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = f"""
<!-- Geist (Vercel's open-source typeface) + Inter fallback. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {{
    --symphony-font-sans: "Geist", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    --symphony-font-mono: "Geist Mono", "SF Mono", Menlo, Consolas, monospace;
    --symphony-radius-sm: {RADIUS['sm']};
    --symphony-radius-md: {RADIUS['md']};
    --symphony-radius-lg: {RADIUS['lg']};
}}

/* ---------- Reset Streamlit chrome ---------- */
#MainMenu {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
footer {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}

/* ---------- Base layout ---------- */
/* Set body font WITHOUT !important and WITHOUT [class*="st-"]. The previous
   selector matched Streamlit's emotion-cache classes including its Material
   Symbols icon containers, breaking the icon-font ligature substitution
   ("arrow_right" leaked as raw text into expander chevrons, alerts, file
   uploader cloud icons). The fix: scope font-family to text containers only
   and explicitly preserve Material Symbols on icon spans. */
html, body {{
    font-family: var(--symphony-font-sans);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
}}

/* Apply Geist to Streamlit's text components without nuking icon spans.
   These selectors target text-bearing widgets explicitly. */
.stMarkdown, .stMarkdown *,
.stText, .stTextInput input, .stTextArea textarea,
.stButton > button, .stDownloadButton > button,
.stCheckbox, .stRadio, .stSelectbox, .stMultiSelect,
.stCaption, .stAlert,
[data-testid="stMarkdownContainer"],
[data-testid="stText"],
[data-testid="stHeader"],
[data-testid="stWidgetLabel"],
[data-testid="stExpander"] summary > div {{
    font-family: var(--symphony-font-sans);
}}

/* CRITICAL: preserve Material Symbols Rounded on Streamlit's icon spans.
   Streamlit renders chevrons / alerts / uploader cloud as <span> with
   font-family set inline + literal text like "arrow_right" that the icon
   font substitutes via ligature. Inheriting text-transform from a parent
   (like our uppercase expander summary) breaks the ligature -- "arrow_right"
   becomes "ARROW_RIGHT" which has no glyph. We override BOTH font-family
   (defensive, in case any rule wins over inline style) AND text-transform
   (so the literal ligature input stays lowercase). */
[style*="Material Symbols"],
[class*="material-symbols"],
[class*="MaterialIcon"],
[data-testid*="Icon"] span[style*="font-family"] {{
    font-family: 'Material Symbols Rounded' !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    word-spacing: normal !important;
    white-space: nowrap !important;
    direction: ltr !important;
    -webkit-font-feature-settings: 'liga' !important;
    font-feature-settings: 'liga' !important;
    font-variation-settings: normal !important;
}}

.stApp {{
    /* Near-solid canvas + multi-orb ambient gradient layers + film-grain
       noise. Stacked as static background-images on .stApp -- safe, no
       positioning shenanigans, no pointer-event interference.
       Earlier attempt with position:fixed pseudo-element orbs broke the
       stacking context and hid the page content. Lesson: keep ambient
       depth in the background-image stack, not in absolutely-positioned
       overlays. */
    background:
        /* top-center signature orb (indigo, brightest) */
        radial-gradient(ellipse 60% 35% at 50% 5%, rgba(129, 140, 248, 0.18) 0%, transparent 55%),
        /* upper-right ambient orb (violet) */
        radial-gradient(ellipse 50% 40% at 85% 25%, rgba(167, 139, 250, 0.10) 0%, transparent 55%),
        /* mid-left ambient orb (fuchsia) */
        radial-gradient(ellipse 45% 35% at 8% 55%, rgba(232, 121, 249, 0.08) 0%, transparent 55%),
        /* bottom-right ambient orb (indigo, balances the layout) */
        radial-gradient(ellipse 55% 40% at 90% 90%, rgba(129, 140, 248, 0.10) 0%, transparent 55%),
        /* film-grain noise texture */
        url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>"),
        {COLORS['bg']};
    background-attachment: fixed, fixed, fixed, fixed, fixed, fixed;
    color: {COLORS['text']};
    font-family: var(--symphony-font-sans);
}}

.block-container {{
    padding-top: 2.5rem !important;
    padding-bottom: 6rem !important;
    max-width: 1200px !important;
}}

/* ---------- Typography ---------- */
.symphony-eyebrow {{
    font-size: 11px;
    letter-spacing: 1.2px;
    font-weight: 600;
    text-transform: uppercase;
    color: {COLORS['indigo']};
    opacity: 0.95;
    font-family: var(--symphony-font-sans);
}}

.symphony-h1 {{
    font-size: 64px;
    font-weight: 700;
    letter-spacing: -2.4px;
    line-height: 1.0;
    margin: 8px 0 14px 0;
    font-family: var(--symphony-font-sans);
    background: {GRADIENTS['brand']};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    /* Hero motion: ambient breathing glow lives in ::before, see below.
       isolation:isolate creates a stacking context so ::before with
       z-index:-1 stays BEHIND the H1 text but doesn't sink below the page
       background (where it would be invisible). */
    position: relative;
    display: inline-block;
    isolation: isolate;
}}

.symphony-h1::before {{
    /* Inner glow -- saturated, breathing. */
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    width: 160%;
    height: 320%;
    transform: translate(-50%, -50%);
    background: radial-gradient(ellipse,
        rgba(167, 139, 250, 0.55) 0%,
        rgba(232, 121, 249, 0.28) 30%,
        rgba(129, 140, 248, 0.10) 55%,
        transparent 75%);
    filter: blur(36px);
    z-index: -1;
    pointer-events: none;
    animation: orb-breathe 6s ease-in-out infinite;
}}

.symphony-h1::after {{
    /* Outer halo -- larger, softer, slower counter-breath for depth. */
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    width: 240%;
    height: 480%;
    transform: translate(-50%, -50%);
    background: radial-gradient(ellipse,
        rgba(232, 121, 249, 0.18) 0%,
        rgba(129, 140, 248, 0.08) 40%,
        transparent 70%);
    filter: blur(60px);
    z-index: -2;
    pointer-events: none;
    animation: orb-breathe-slow 9s ease-in-out infinite;
}}

@keyframes orb-breathe {{
    0%, 100% {{ opacity: 0.70; transform: translate(-50%, -50%) scale(0.94); }}
    50%      {{ opacity: 1.00; transform: translate(-50%, -50%) scale(1.10); }}
}}

@keyframes orb-breathe-slow {{
    0%, 100% {{ opacity: 0.40; transform: translate(-50%, -50%) scale(1.00); }}
    50%      {{ opacity: 0.85; transform: translate(-50%, -50%) scale(1.15); }}
}}

.symphony-tagline {{
    font-size: 17px;
    color: {COLORS['text_dim']};
    line-height: 1.55;
    max-width: 720px;
    margin-bottom: 32px;
    font-family: var(--symphony-font-sans);
}}

.symphony-h2 {{
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -0.6px;
    color: {COLORS['text']};
    margin: 0 0 8px 0;
    font-family: var(--symphony-font-sans);
}}

.symphony-section-label {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: var(--symphony-radius-pill, 999px);
    background: rgba(129, 140, 248, 0.10);
    border: 1px solid rgba(129, 140, 248, 0.30);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: {COLORS['indigo']};
    margin-bottom: 12px;
    font-family: var(--symphony-font-sans);
}}

/* Inline icon utility -- inherits surrounding color via stroke=currentColor. */
.symphony-icon {{
    color: inherit;
    line-height: 0;
    vertical-align: -2px;
}}

/* ---------- Cards ---------- */
.symphony-card {{
    background: {COLORS['surface_1']};
    border: 1px solid {COLORS['border']};
    border-radius: var(--symphony-radius-lg);
    padding: 24px 28px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.20);
    transition: border-color 200ms ease, box-shadow 200ms ease, background-color 200ms ease;
}}

.symphony-card:hover {{
    border-color: {COLORS['border_lift']};
    background-color: #131A33;
    box-shadow: 0 8px 32px rgba(129, 140, 248, 0.10);
}}

.symphony-card-glow {{
    background: {COLORS['surface_1']};
    border: 1px solid transparent;
    border-radius: var(--symphony-radius-lg);
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
    border-radius: var(--symphony-radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
    font-family: var(--symphony-font-sans);
}}

.symphony-agent-avatar.a {{ background: {GRADIENTS['agent_a']}; }}
.symphony-agent-avatar.b {{ background: {GRADIENTS['agent_b']}; }}
.symphony-agent-avatar.s {{ background: {GRADIENTS['synth']}; }}

.symphony-agent-name {{
    font-size: 15px;
    font-weight: 700;
    color: {COLORS['text']};
    line-height: 1.1;
    letter-spacing: -0.1px;
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
    border-radius: var(--symphony-radius-pill, 999px);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    font-family: var(--symphony-font-sans);
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
    border-radius: var(--symphony-radius-md) !important;
    font-weight: 600 !important;
    letter-spacing: 0.1px !important;
    border: 1px solid {COLORS['border']} !important;
    background: {COLORS['surface_2']} !important;
    color: {COLORS['text']} !important;
    transition: border-color 150ms ease, background-color 150ms ease, box-shadow 150ms ease !important;
    padding: 10px 18px !important;
    font-family: var(--symphony-font-sans) !important;
}}

.stButton > button:hover {{
    border-color: {COLORS['indigo']} !important;
    background: {COLORS['surface_3']} !important;
    box-shadow: 0 4px 16px rgba(129, 140, 248, 0.18);
}}

/* PRIMARY -- the signature gradient. Reserved for hero CTAs. */
.stButton > button[kind="primary"] {{
    background: {GRADIENTS['brand']} !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 16px rgba(129, 140, 248, 0.30);
}}

.stButton > button[kind="primary"]:hover {{
    box-shadow: 0 8px 28px rgba(129, 140, 248, 0.45) !important;
    filter: brightness(1.08);
}}

/* ---------- File uploader ---------- */
[data-testid="stFileUploader"] section {{
    background: {COLORS['surface_1']} !important;
    border: 2px dashed {COLORS['border_lift']} !important;
    border-radius: var(--symphony-radius-lg) !important;
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

/* ---------- Streaming cursor (refined: thin bar with soft glow) ---------- */
.symphony-cursor {{
    display: inline-block;
    width: 2px;
    height: 1.05em;
    background: {COLORS['fuchsia']};
    box-shadow: 0 0 6px rgba(232, 121, 249, 0.70);
    margin-left: 2px;
    vertical-align: text-bottom;
    border-radius: 1px;
    animation: cursor-blink 1.2s ease-in-out infinite;
}}

@keyframes cursor-blink {{
    0%, 45%   {{ opacity: 1; }}
    50%, 95%  {{ opacity: 0.15; }}
    100%      {{ opacity: 1; }}
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
    font-family: var(--symphony-font-sans);
}}

.symphony-content h1, .symphony-content h2, .symphony-content h3 {{
    color: {COLORS['text']};
    font-weight: 700;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
    letter-spacing: -0.3px;
    font-family: var(--symphony-font-sans);
}}

.symphony-content strong {{ color: {COLORS['text']}; }}

.symphony-content blockquote {{
    border-left: 3px solid {COLORS['indigo']};
    padding-left: 14px;
    color: {COLORS['text_dim']};
    margin: 12px 0;
}}

.symphony-content code {{
    font-family: var(--symphony-font-mono);
    font-size: 0.92em;
    background: rgba(129, 140, 248, 0.10);
    padding: 1px 6px;
    border-radius: var(--symphony-radius-sm);
}}

/* ---------- Sidebar polish ---------- */
[data-testid="stSidebar"] {{
    background: {COLORS['surface_1']} !important;
    border-right: 1px solid {COLORS['border']};
}}

/* ---------- Phase rail (more confident) ---------- */
.symphony-phase-rail {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 36px;
    padding: 16px 0;
    font-family: var(--symphony-font-sans);
}}

.symphony-phase-step {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: -0.1px;
    color: {COLORS['text_mute']};
    transition: color 200ms ease;
    white-space: nowrap;
}}

.symphony-phase-step.active {{
    color: {COLORS['indigo']};
}}

.symphony-phase-step.complete {{
    color: {COLORS['success']};
}}

.symphony-phase-dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: {COLORS['surface_3']};
    border: 2px solid {COLORS['border']};
    transition: all 200ms ease;
    flex-shrink: 0;
}}

.symphony-phase-step.active .symphony-phase-dot {{
    background: {COLORS['indigo']};
    border-color: {COLORS['indigo']};
    box-shadow: 0 0 0 5px rgba(129, 140, 248, 0.22);
    animation: phase-pulse 2.4s ease-in-out infinite;
}}

@keyframes phase-pulse {{
    0%, 100% {{ box-shadow: 0 0 0 5px rgba(129, 140, 248, 0.22); }}
    50%      {{ box-shadow: 0 0 0 9px rgba(129, 140, 248, 0.08); }}
}}

.symphony-phase-step.complete .symphony-phase-dot {{
    background: {COLORS['success']};
    border-color: {COLORS['success']};
}}

.symphony-phase-line {{
    flex: 1;
    height: 2px;
    background: linear-gradient(90deg, {COLORS['border']} 0%, {COLORS['border']} 100%);
    border-radius: 1px;
    max-width: 72px;
    min-width: 32px;
    transition: background 300ms ease;
}}

/* The Cue: visually distinct from the numbered Movement steps. */
.symphony-phase-step.cue {{
    color: {COLORS['violet']};
    font-style: italic;
    letter-spacing: 0.4px;
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
    animation: phase-pulse 2.4s ease-in-out infinite;
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
    border-radius: var(--symphony-radius-md) !important;
    transition: border-color 200ms ease;
}}

[data-testid="stExpander"] details:hover {{
    border-color: {COLORS['border_lift']} !important;
}}

[data-testid="stExpander"] summary {{
    /* Sentence case (NOT uppercase) so the Material Symbols ligature on the
       chevron child doesn't break. The chevron's text is "arrow_right" /
       "arrow_down" and uppercasing it kills the icon-font substitution. */
    padding: 14px 18px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: -0.05px !important;
    color: {COLORS['indigo']} !important;
    border-radius: var(--symphony-radius-md) !important;
    font-family: var(--symphony-font-sans) !important;
}}

[data-testid="stExpander"] summary:hover {{
    color: {COLORS['violet']} !important;
}}

[data-testid="stExpander"] details[open] summary {{
    border-bottom: 1px solid {COLORS['border']} !important;
    border-radius: var(--symphony-radius-md) var(--symphony-radius-md) 0 0 !important;
}}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    padding: 24px 20px !important;
}}

/* ---------- Asset cards (Movement II/III) ---------- */
.symphony-asset-card {{
    background: {COLORS['surface_1']};
    border: 1px solid {COLORS['border']};
    border-radius: var(--symphony-radius-md);
    padding: 18px 22px;
    margin-bottom: 12px;
    transition: border-color 200ms ease, background-color 200ms ease;
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

/* Asset icon: solid surface, indigo glyph (NOT the brand gradient -- that's
   reserved for the wordmark and primary CTA). */
.symphony-asset-icon {{
    width: 32px;
    height: 32px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(129, 140, 248, 0.14);
    color: {COLORS['indigo']};
    flex-shrink: 0;
    border: 1px solid rgba(129, 140, 248, 0.24);
}}

.symphony-asset-icon.linkedin {{
    background: rgba(125, 211, 252, 0.14);
    color: {COLORS['maya']};
    border-color: rgba(125, 211, 252, 0.30);
}}

.symphony-asset-icon.outreach {{
    background: rgba(245, 158, 11, 0.14);
    color: {COLORS['marcus']};
    border-color: rgba(245, 158, 11, 0.30);
}}

.symphony-asset-icon.blog {{
    background: rgba(167, 139, 250, 0.14);
    color: {COLORS['violet']};
    border-color: rgba(167, 139, 250, 0.30);
}}

.symphony-asset-label {{
    font-weight: 600;
    font-size: 15px;
    color: {COLORS['text']};
    flex: 1;
    letter-spacing: -0.1px;
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
    letter-spacing: 0.6px;
    color: {COLORS['text_mute']};
    text-transform: uppercase;
    font-weight: 600;
}}

.symphony-success-banner {{
    background: linear-gradient(135deg, rgba(52, 211, 153, 0.16) 0%, rgba(125, 211, 252, 0.10) 100%);
    border: 1px solid rgba(52, 211, 153, 0.40);
    border-radius: var(--symphony-radius-md);
    padding: 14px 18px;
    margin: 8px 0 4px 0;
    display: flex;
    align-items: center;
    gap: 12px;
    color: {COLORS['success']};
    font-size: 14px;
    font-weight: 600;
    font-family: var(--symphony-font-sans);
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
    border-radius: var(--symphony-radius-md);
    padding: 12px 16px;
    margin: 8px 0;
    color: {COLORS['danger']};
    font-size: 13px;
    font-family: var(--symphony-font-sans);
}}

.symphony-asset-preview {{
    background: {COLORS['bg']};
    border: 1px solid {COLORS['border']};
    border-radius: var(--symphony-radius-md);
    padding: 14px 16px;
    margin: 8px 0 12px 0;
    font-size: 13px;
    color: {COLORS['text_dim']};
    line-height: 1.55;
    max-height: 180px;
    overflow: hidden;
    position: relative;
    font-family: var(--symphony-font-mono);
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
    border-radius: var(--symphony-radius-sm);
}}

@keyframes shimmer {{
    0%   {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}

/* ---------- Curtain Call (distribution finale) ---------- */
.symphony-curtain {{
    position: relative;
    margin: 36px 0 18px 0;
    padding: 40px 36px 36px 36px;
    border-radius: var(--symphony-radius-lg);
    background: {COLORS['surface_1']};
    border: 1px solid transparent;
    background-image:
      linear-gradient({COLORS['surface_1']}, {COLORS['surface_1']}),
      {GRADIENTS['brand']};
    background-origin: border-box;
    background-clip: padding-box, border-box;
    box-shadow: 0 12px 48px rgba(129, 140, 248, 0.16);
    overflow: hidden;
    isolation: isolate;
}}

.symphony-curtain::before {{
    content: "";
    position: absolute;
    top: -120px;
    left: 50%;
    transform: translateX(-50%);
    width: 480px;
    height: 240px;
    background: radial-gradient(
        ellipse at center,
        rgba(167, 139, 250, 0.20) 0%,
        rgba(129, 140, 248, 0.10) 35%,
        rgba(129, 140, 248, 0) 70%
    );
    z-index: -1;
    pointer-events: none;
    animation: curtain-glow 6s ease-in-out infinite;
}}

@keyframes curtain-glow {{
    0%, 100% {{ opacity: 0.85; transform: translateX(-50%) scale(1); }}
    50%      {{ opacity: 1.00; transform: translateX(-50%) scale(1.06); }}
}}

.symphony-curtain-mark {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: {GRADIENTS['brand']};
    box-shadow: 0 8px 24px rgba(129, 140, 248, 0.32);
    margin-bottom: 18px;
    color: #FFFFFF;
}}

.symphony-curtain-eyebrow {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2.4px;
    text-transform: uppercase;
    color: {COLORS['indigo']};
    margin-bottom: 8px;
    font-family: var(--symphony-font-sans);
}}

.symphony-curtain-title {{
    font-size: 38px;
    font-weight: 700;
    line-height: 1.05;
    letter-spacing: -1.2px;
    color: {COLORS['text']};
    margin: 0 0 6px 0;
    font-family: var(--symphony-font-sans);
}}

.symphony-curtain-subtitle {{
    font-size: 16px;
    color: {COLORS['text_dim']};
    margin: 0 0 28px 0;
    line-height: 1.5;
    max-width: 560px;
}}

.symphony-curtain-stats {{
    display: flex;
    align-items: center;
    gap: 0;
    margin: 28px 0 32px 0;
    padding: 22px 24px;
    border: 1px solid {COLORS['border']};
    border-radius: var(--symphony-radius-md);
    background: rgba(10, 14, 26, 0.55);
}}

.symphony-curtain-stat {{
    flex: 1;
    text-align: center;
    padding: 0 16px;
}}

.symphony-curtain-stat-value {{
    font-size: 32px;
    font-weight: 700;
    color: {COLORS['text']};
    line-height: 1.1;
    letter-spacing: -0.6px;
    font-family: var(--symphony-font-sans);
    background: {GRADIENTS['brand']};
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
}}

.symphony-curtain-stat-label {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    color: {COLORS['text_mute']};
    margin-top: 8px;
}}

.symphony-curtain-stat-divider {{
    width: 1px;
    align-self: stretch;
    background: {COLORS['border']};
    flex-shrink: 0;
}}

.symphony-curtain-tagline {{
    font-size: 17px;
    line-height: 1.55;
    color: {COLORS['text_dim']};
    font-style: italic;
    margin: 0 0 28px 0;
    max-width: 560px;
}}

.symphony-curtain-tagline strong {{
    color: {COLORS['text']};
    font-weight: 600;
    font-style: normal;
}}

.symphony-curtain-meta {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-top: 22px;
    padding-top: 20px;
    border-top: 1px solid {COLORS['border']};
    font-size: 12px;
    color: {COLORS['text_mute']};
    letter-spacing: 0.4px;
}}

.symphony-curtain-meta strong {{
    color: {COLORS['text_dim']};
    font-weight: 600;
}}

/* ---------- Mobile responsiveness ---------- */
@media (max-width: 600px) {{
    .symphony-h1 {{
        font-size: 40px !important;
        letter-spacing: -1.4px !important;
    }}
    .symphony-h2 {{
        font-size: 22px !important;
    }}
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
    }}
    .symphony-phase-rail {{
        flex-wrap: wrap;
        gap: 8px 12px;
    }}
    .symphony-phase-step {{
        font-size: 11px;
        letter-spacing: 0.2px;
    }}
    .symphony-phase-line {{
        max-width: 18px;
    }}
    .symphony-tagline {{
        font-size: 15px;
    }}
    .symphony-curtain {{
        padding: 28px 22px 24px 22px;
    }}
    .symphony-curtain-title {{
        font-size: 28px;
        letter-spacing: -0.6px;
    }}
    .symphony-curtain-stats {{
        flex-wrap: wrap;
        gap: 16px 0;
        padding: 18px 8px;
    }}
    .symphony-curtain-stat {{
        flex: 0 0 50%;
        padding: 8px 6px;
    }}
    .symphony-curtain-stat-divider {{
        display: none;
    }}
    .symphony-curtain-stat-value {{
        font-size: 26px;
    }}
}}
</style>
"""


def inject_theme(st_module) -> None:
    """Inject Symphony custom CSS. Call once at the top of app.py after st.set_page_config."""
    st_module.markdown(CUSTOM_CSS, unsafe_allow_html=True)
