import html as html_module
import json
import re
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

from aiditor.analyzer import analyze_script
from aiditor.shot_lister import generate_production_prompts, ShotList
from aiditor.approval import write_approval_markdown
from aiditor.generators import dispatch_generation
from aiditor.models import ScriptAnalysis, BrollOpportunity
from aiditor.loaders import script_to_text

load_dotenv()

st.set_page_config(
    page_title="aiditor",
    page_icon="🎬",
    layout="wide",
)

# ── Parchment / Library theme ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');

/* ══════════════════════════════════════════════════════
   DESK: warm tan background, the "table" the book sits on
   ══════════════════════════════════════════════════════ */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background-color: #C8A97A !important;
    background-image:
        repeating-linear-gradient(
            90deg,
            transparent,
            transparent 3px,
            rgba(0,0,0,0.015) 3px,
            rgba(0,0,0,0.015) 4px
        ),
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 3px,
            rgba(0,0,0,0.015) 3px,
            rgba(0,0,0,0.015) 4px
        );
}
[data-testid="stHeader"] {
    background-color: #C8A97A !important;
    border-bottom: 1px solid #A07840;
}
[data-testid="stSidebar"] { background-color: #B89060 !important; }

/* ══════════════════════════════════════════════════════
   PAPER: the open book / page floating on the desk
   Left + right shadows create a bound-book spine effect
   ══════════════════════════════════════════════════════ */
.main .block-container {
    background-color: #FAF7EE !important;
    max-width: 1100px;
    padding: 2.5rem 3.5rem !important;
    border-left:  1px solid #D4B896;
    border-right: 1px solid #D4B896;
    box-shadow:
        -12px 0 28px rgba(80, 40, 10, 0.22),
          12px 0 28px rgba(80, 40, 10, 0.22),
           0   4px 18px rgba(80, 40, 10, 0.15),
        /* inner gutter shadow — left edge */
        inset 6px 0 12px rgba(80, 40, 10, 0.06),
        /* inner gutter shadow — right edge */
        inset -6px 0 12px rgba(80, 40, 10, 0.06);
    min-height: 100vh;
}

/* ══════════════════════════════════════════════════════
   TYPOGRAPHY
   ══════════════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: 'EB Garamond', Georgia, 'Times New Roman', serif !important;
    color: #2C1810 !important;
}
h1 {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 2.4rem !important;
    color: #2C1810 !important;
    letter-spacing: 0.04em;
    border-bottom: 2px solid #8B6914;
    padding-bottom: 0.3rem;
    margin-bottom: 0.2rem;
}
h2, h3 {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #3D2010 !important;
    letter-spacing: 0.02em;
}
p, li, span, div, label {
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 1.05rem !important;
    color: #2C1810 !important;
    line-height: 1.75 !important;
}
small, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 0.88rem !important;
    color: #7A5530 !important;
}

/* ══════════════════════════════════════════════════════
   BUTTONS — dark leather, always cream text
   Targets the button element AND every inner text node
   ══════════════════════════════════════════════════════ */
button,
.stButton > button,
[data-testid="stFormSubmitButton"] > button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"],
[data-testid="stToolbarActionButton"],
[data-testid="stHeader"] button,
[data-testid="stToolbarActions"] button {
    background-color: #3D2B1F !important;
    color: #FFFDF5 !important;
    border: 1px solid #8B6914 !important;
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 1.05rem !important;
    border-radius: 2px !important;
    letter-spacing: 0.03em;
    padding: 0.4rem 1.2rem !important;
}
/* Force cream on every child element inside any button */
button *, button p, button span, button div,
.stButton > button *, .stButton > button p, .stButton > button span,
[data-testid="stFormSubmitButton"] > button *,
[data-testid="stBaseButton-secondary"] *,
[data-testid="stBaseButton-primary"] *,
[data-testid="stToolbarActionButton"] *,
[data-testid="stHeader"] button *,
[data-testid="stToolbarActions"] button * {
    color: #FFFDF5 !important;
    fill: #FFFDF5 !important;
}
button:hover,
.stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover,
[data-testid="stToolbarActionButton"]:hover,
[data-testid="stHeader"] button:hover {
    background-color: #5C3D2E !important;
    border-color: #C8A951 !important;
    color: #FFFDF5 !important;
}
/* Primary / burgundy */
.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    background-color: #6B2D3E !important;
    border-color: #C8A951 !important;
    font-size: 1.1rem !important;
    color: #FFFDF5 !important;
}
.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
    background-color: #8B3D52 !important;
    color: #FFFDF5 !important;
}

/* ══════════════════════════════════════════════════════
   TEXT INPUTS & AREAS
   ══════════════════════════════════════════════════════ */
.stTextArea textarea, .stTextInput input {
    background-color: #FEFBF0 !important;
    border: 1px solid #A08040 !important;
    border-radius: 2px !important;
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 1.05rem !important;
    color: #2C1810 !important;
    caret-color: #2C1810 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #C8A951 !important;
    box-shadow: 0 0 0 2px rgba(200,169,81,0.25) !important;
}

/* ══════════════════════════════════════════════════════
   BORDERED CONTAINERS (cards)
   ══════════════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background-color: #FEFBF0 !important;
    border-color: #C8A951 !important;
    border-radius: 2px !important;
}

/* ══════════════════════════════════════════════════════
   TABS — book-divider style
   ══════════════════════════════════════════════════════ */
[data-baseweb="tab-list"] {
    background-color: #EDD9A8 !important;
    border-bottom: 2px solid #8B6914 !important;
    gap: 0 !important;
    /* Stay inside the paper — never overflow the container */
    width: 100% !important;
    max-width: 100% !important;
    flex-wrap: wrap !important;
    overflow-x: hidden !important;
}
/* Tab button + all inner text nodes — explicit dark brown */
[data-baseweb="tab"],
[role="tab"] {
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 0.92rem !important;
    color: #4A2810 !important;
    background-color: transparent !important;
    border-radius: 0 !important;
    /* tighter padding so 6 tabs fit without wrapping on most screens */
    padding: 0.45rem 0.85rem !important;
    white-space: nowrap !important;
}
[data-baseweb="tab"] *,
[data-baseweb="tab"] div,
[data-baseweb="tab"] span,
[data-baseweb="tab"] p,
[role="tab"] *,
[role="tab"] div,
[role="tab"] span {
    color: #4A2810 !important;
    font-family: 'EB Garamond', Georgia, serif !important;
}
[data-baseweb="tab"]:hover,
[data-baseweb="tab"]:hover *,
[role="tab"]:hover,
[role="tab"]:hover * {
    color: #2C1810 !important;
    background-color: #E2CC90 !important;
}
/* Selected tab — exact same cream as the page */
[aria-selected="true"][data-baseweb="tab"],
[aria-selected="true"][role="tab"] {
    color: #2C1810 !important;
    background-color: #FAF7EE !important;
    border-top: 2px solid #6B2D3E !important;
    border-left: 1px solid #A08040 !important;
    border-right: 1px solid #A08040 !important;
    font-weight: 600;
}
[aria-selected="true"][data-baseweb="tab"] *,
[aria-selected="true"][role="tab"] * {
    color: #2C1810 !important;
}
/* ── Tab panel: flush cream, no borders, no inner white ── */
[data-baseweb="tab-panel"] {
    background-color: #FAF7EE !important;
    border: none !important;
    padding: 1.2rem 0 0 0 !important;
}
/* Kill the white that Streamlit injects on the stVerticalBlock
   wrapper sitting directly inside the panel */
[data-baseweb="tab-panel"] > div,
[data-baseweb="tab-panel"] > div > div,
[data-baseweb="tab-panel"] [data-testid="stVerticalBlock"],
[data-baseweb="tab-panel"] [data-testid="stVerticalBlock"] > div:not([data-testid="stVerticalBlockBorderWrapper"]) {
    background-color: #FAF7EE !important;
}

/* ══════════════════════════════════════════════════════
   ALERTS
   ══════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
    background-color: #F5EDD0 !important;
    border: 1px solid #8B6914 !important;
    border-radius: 2px !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div {
    color: #2C1810 !important;
    font-family: 'EB Garamond', Georgia, serif !important;
}

/* ══════════════════════════════════════════════════════
   METRICS
   ══════════════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background-color: #FEFBF0 !important;
    border: 1px solid #A08040 !important;
    border-radius: 2px !important;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] p { color: #7A5530 !important; }
[data-testid="stMetricValue"]  { font-family: 'Playfair Display', Georgia, serif !important; }

/* ══════════════════════════════════════════════════════
   FILE UPLOADER
   ══════════════════════════════════════════════════════ */
[data-testid="stFileUploader"] {
    background-color: #FEFBF0 !important;
    border: 1px dashed #A08040 !important;
    border-radius: 2px !important;
}
[data-testid="stFileUploader"] * { color: #7A5530 !important; }

/* ══════════════════════════════════════════════════════
   EXPANDERS
   ══════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
    background-color: #FEFBF0 !important;
    border: 1px solid #C8A951 !important;
    border-radius: 2px !important;
}
summary, [data-testid="stExpanderToggleIcon"] { color: #7A5530 !important; }

/* ══════════════════════════════════════════════════════
   CODE BLOCKS
   ══════════════════════════════════════════════════════ */
code, pre {
    background-color: #EDD9A8 !important;
    border: 1px solid #C8A951 !important;
    font-family: 'Courier New', Courier, monospace !important;
    color: #2C1810 !important;
    border-radius: 2px !important;
}

/* ══════════════════════════════════════════════════════
   DIVIDERS
   ══════════════════════════════════════════════════════ */
hr {
    border: none !important;
    border-top: 1px solid #C8A951 !important;
    opacity: 0.6 !important;
}

/* ══════════════════════════════════════════════════════
   RADIO / CHECKBOX
   ══════════════════════════════════════════════════════ */
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label {
    font-family: 'EB Garamond', Georgia, serif !important;
    color: #2C1810 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("stage", "input"),
    ("analysis", None),
    ("approved_indices", set()),
    ("shot_list", None),
    ("generation_results", None),
    ("script_name", "untitled"),
    ("script_text", ""),
    ("output_dir", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def reset_state():
    st.session_state.stage = "input"
    st.session_state.analysis = None
    st.session_state.approved_indices = set()
    st.session_state.shot_list = None
    st.session_state.generation_results = None
    st.session_state.script_text = ""
    st.session_state.output_dir = None


# ── Header ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([6, 1])
with col1:
    st.title("aiditor")
    st.caption("AI-assisted video essay production pipeline")
with col2:
    if st.session_state.stage != "input":
        if st.button("Start over"):
            reset_state()
            st.rerun()

st.divider()


# ── Annotated script builder ──────────────────────────────────────────────────
def build_annotated_script_html(script_text: str, analysis: ScriptAnalysis) -> str:
    """Full annotated script: b-roll, line edits, structural cuts/expansions."""

    # Library-palette colors for each annotation type
    BROLL_STYLE = {
        "veo":         ("background:#C8D8E8;border-bottom:2px solid #3A5068", "🎬"),
        "nano_banana": ("background:#DDD0E8;border-bottom:2px solid #6B4E7B", "🍌"),
        "stock":       ("background:#C8DCC8;border-bottom:2px solid #3A5E3A", "📼"),
        "self-shot":   ("background:#E8DEC8;border-bottom:2px solid #7A5E14", "🎥"),
    }
    ANNO_STYLE = {
        "edit":   ("background:#F0E0B0;border-bottom:2px dashed #B85010", "✏️"),
        "cut":    ("background:#EAC8C8;border-bottom:2px solid #8B3030",  "✂️"),
        "expand": ("background:#C8E8D0;border-bottom:2px solid #2A6B3A",  "➕"),
    }

    annotations: list[tuple[int, int, str, str, str]] = []

    # ── B-roll excerpts ───────────────────────────────────────────────────────
    for shot in analysis.broll_opportunities:
        excerpt = shot.script_excerpt.strip()
        if len(excerpt) < 10:
            continue
        idx = script_text.find(excerpt)
        used_excerpt = excerpt
        if idx == -1 and len(excerpt) > 60:
            short = excerpt[:70]
            idx = script_text.find(short)
            used_excerpt = short
        if idx != -1:
            tool = shot.tool_recommendation
            emoji = BROLL_STYLE.get(tool, ("", "📹"))[1]
            tip = f"{emoji} {tool.replace('_',' ')}: {shot.suggested_visual}"
            annotations.append((idx, idx + len(used_excerpt), "broll", tool, tip))

    # ── Line edits ────────────────────────────────────────────────────────────
    for edit in analysis.line_edits:
        original = edit.original.strip()
        if len(original) < 10:
            continue
        idx = script_text.find(original)
        if idx != -1:
            tip = f"Suggested rewrite: {edit.suggested}"
            annotations.append((idx, idx + len(original), "edit", "", tip))

    # ── Structural cuts — find quoted text in section description ─────────────
    for sugg in analysis.structural_suggestions:
        if sugg.type not in ("cut", "expand"):
            continue
        quoted = re.findall(r"['‘’“”]([^'\"]{15,})['‘’“”]", sugg.section)
        for q in quoted:
            idx = script_text.find(q)
            if idx != -1:
                # Extend to end of paragraph (or 250 chars, whichever comes first)
                para_end = script_text.find("\n\n", idx + 30)
                end = min(idx + 250, para_end if para_end != -1 else idx + 250)
                tip_prefix = "✂️ Cut suggested" if sugg.type == "cut" else "➕ Expand here"
                tip = f"{tip_prefix}: {sugg.rationale[:120]}"
                annotations.append((idx, end, sugg.type, "", tip))
                break

    # ── Remove overlaps (first-come, longest) ─────────────────────────────────
    annotations.sort(key=lambda x: x[0])
    clean: list[tuple[int, int, str, str, str]] = []
    cursor = 0
    for ann in annotations:
        if ann[0] >= cursor:
            clean.append(ann)
            cursor = ann[1]

    # ── Build HTML ────────────────────────────────────────────────────────────
    parts: list[str] = []
    prev = 0
    for start, end, ann_type, tool, tooltip in clean:
        parts.append(html_module.escape(script_text[prev:start]))
        excerpt_html = html_module.escape(script_text[start:end])
        tip = html_module.escape(tooltip)

        if ann_type == "broll":
            style, emoji = BROLL_STYLE.get(tool, ("background:#e8e0d0", "📹"))
        else:
            style, emoji = ANNO_STYLE.get(ann_type, ("background:#e8e0d0", "?"))

        parts.append(
            f'<span style="{style};padding:1px 4px;cursor:help;border-radius:2px;" '
            f'title="{tip}">{excerpt_html}</span>'
            f'<sup style="font-size:0.65em;margin-left:1px;vertical-align:super">{emoji}</sup>'
        )
        prev = end
    parts.append(html_module.escape(script_text[prev:]))

    body = "".join(parts).replace("\n\n", "<br><br>").replace("\n", "<br>")

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_items = [
        ("background:#C8D8E8;border-bottom:2px solid #3A5068", "🎬", "Veo (AI video)"),
        ("background:#DDD0E8;border-bottom:2px solid #6B4E7B", "🍌", "NanoBanana (AI image)"),
        ("background:#C8DCC8;border-bottom:2px solid #3A5E3A", "📼", "Stock footage"),
        ("background:#E8DEC8;border-bottom:2px solid #7A5E14", "🎥", "Self-shot"),
        ("background:#F0E0B0;border-bottom:2px dashed #B85010", "✏️", "Line edit"),
        ("background:#EAC8C8;border-bottom:2px solid #8B3030",  "✂️", "Cut"),
        ("background:#C8E8D0;border-bottom:2px solid #2A6B3A",  "➕", "Expand"),
    ]
    legend_html = (
        '<div style="margin-bottom:1.5rem;padding:0.85rem 1.1rem;'
        'background:#F0E4C8;border:1px solid #8B6914;border-radius:3px;'
        'font-family:Georgia,serif;font-size:0.83em;line-height:2.4;">'
        '<strong style="font-family:\'Playfair Display\',Georgia,serif;font-size:1.05em;">'
        'Annotation key</strong> — hover any highlight for detail<br>'
    )
    for style, emoji, label in legend_items:
        legend_html += (
            f'<span style="{style};padding:1px 7px;margin-right:6px;'
            f'border-radius:2px;">{emoji} {label}</span> '
        )
    legend_html += "</div>"

    return (
        f'<div style="font-family:Georgia,serif;line-height:2.1;font-size:0.97em;'
        f'max-width:860px;color:#2C1810;">'
        f"{legend_html}{body}</div>"
    )


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1: INPUT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.stage == "input":
    st.subheader("I. Provide Your Script")

    input_method = st.radio(
        "How would you like to provide the script?",
        ["Paste text", "Upload file (PDF, DOCX, TXT, MD)"],
        horizontal=True,
    )

    script_text = None

    if input_method == "Paste text":
        with st.form("paste_form", border=False):
            pasted = st.text_area(
                "Paste your script below",
                height=340,
                placeholder="Paste the full text of your video essay script here…",
            )
            submitted = st.form_submit_button(
                "Analyse Script →",
                type="primary",
                use_container_width=True,
            )

        if submitted and pasted.strip():
            script_text = pasted
            st.session_state.script_name = "pasted_script"

    else:
        uploaded = st.file_uploader(
            "Upload script file",
            type=["md", "txt", "docx", "pdf"],
        )
        if uploaded is not None:
            temp_path = Path("/tmp") / uploaded.name
            temp_path.write_bytes(uploaded.read())
            try:
                loaded = script_to_text(str(temp_path))
                st.session_state.script_name = uploaded.name.rsplit(".", 1)[0]
                st.success(f"Loaded **{uploaded.name}** — {len(loaded):,} characters")
                with st.expander("Preview extracted text"):
                    st.text(loaded[:1500] + ("…" if len(loaded) > 1500 else ""))
                if st.button("Analyse Script →", type="primary", use_container_width=True):
                    script_text = loaded
            except Exception as e:
                st.error(f"Failed to read file: {e}")

    # ── Run analysis ──────────────────────────────────────────────────────────
    if script_text:
        with st.spinner("Consulting the analyst… (15–30 seconds)"):
            try:
                analysis = analyze_script(script_text)
                st.session_state.analysis = analysis
                st.session_state.script_text = script_text
                st.session_state.stage = "critique"
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2: CRITIQUE & APPROVAL
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "critique":
    analysis: ScriptAnalysis = st.session_state.analysis

    st.subheader("II. Script Analysis")
    st.info(f"**Overall:** {analysis.overall_assessment}")

    tab_critique, tab_broll, tab_structure, tab_edits, tab_music, tab_script = st.tabs([
        "Script Critique",
        f"B-roll  ({len(analysis.broll_opportunities)})",
        f"Structure  ({len(analysis.structural_suggestions)})",
        f"Line Edits  ({len(analysis.line_edits)})",
        f"Music  ({len(analysis.music_tone_per_section)})",
        "Annotated Script",
    ])

    # ── Critique ──────────────────────────────────────────────────────────────
    with tab_critique:
        col_good, col_bad = st.columns(2)

        with col_good:
            st.markdown("### What's Working")
            strengths = getattr(analysis, "strengths", [])
            for s in strengths:
                st.markdown(f"- {s}")
            if not strengths:
                st.caption("Re-run analysis to populate.")

        with col_bad:
            st.markdown("### What Needs Work")
            weaknesses = getattr(analysis, "weaknesses", [])
            for w in weaknesses:
                st.markdown(f"- {w}")
            if not weaknesses:
                st.caption("Re-run analysis to populate.")

        st.divider()

        cuts    = [s for s in analysis.structural_suggestions if s.type == "cut"]
        expands = [s for s in analysis.structural_suggestions if s.type == "expand"]
        reorders= [s for s in analysis.structural_suggestions if s.type == "reorder"]

        if cuts:
            st.markdown("### ✂️ Cut")
            for s in cuts:
                with st.container(border=True):
                    st.markdown(f"**{s.section}**")
                    st.caption(s.rationale)

        if expands:
            st.markdown("### ➕ Expand")
            for s in expands:
                with st.container(border=True):
                    st.markdown(f"**{s.section}**")
                    st.caption(s.rationale)

        if reorders:
            st.markdown("### 🔀 Reorder")
            for s in reorders:
                with st.container(border=True):
                    st.markdown(f"**{s.section}**")
                    st.caption(s.rationale)

    # ── B-roll ────────────────────────────────────────────────────────────────
    with tab_broll:
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown("🎬 **veo** — AI video")
        c2.markdown("🍌 **nano_banana** — AI image")
        c3.markdown("📼 **stock** — search query")
        c4.markdown("🎥 **self-shot** — film yourself")
        st.divider()

        GEN_LABEL = {
            "veo":         "Generate this video?",
            "nano_banana": "Generate this image?",
            "stock":       "Include stock query",
            "self-shot":   "Include shooting note",
        }
        PRIORITY_COLOR = {"high": "red", "medium": "orange", "low": "gray"}

        for i, shot in enumerate(analysis.broll_opportunities):
            tool_emoji = {"veo": "🎬", "nano_banana": "🍌", "stock": "📼", "self-shot": "🎥"}.get(
                shot.tool_recommendation, "❓"
            )
            p_color = PRIORITY_COLOR.get(shot.priority, "gray")
            label   = GEN_LABEL.get(shot.tool_recommendation, "Include?")

            with st.container(border=True):
                col_chk, col_body = st.columns([1, 11])
                with col_chk:
                    checked = st.checkbox(label, key=f"approve_{i}", label_visibility="collapsed")
                    st.caption(label)
                    if checked:
                        st.session_state.approved_indices.add(i)
                    else:
                        st.session_state.approved_indices.discard(i)

                with col_body:
                    st.markdown(
                        f"**Shot {i+1}** {tool_emoji} `{shot.tool_recommendation}` "
                        f"· :{p_color}[{shot.priority.upper()}] · {shot.timestamp_estimate}"
                    )
                    st.markdown(f"> {shot.script_excerpt}")
                    st.markdown(f"**Suggested visual:** {shot.suggested_visual}")
                    with st.expander("Why this visual?"):
                        st.markdown(shot.rationale)

    # ── Structure ─────────────────────────────────────────────────────────────
    with tab_structure:
        TYPE_LABEL = {"cut": "✂️ CUT", "expand": "➕ EXPAND", "reorder": "🔀 REORDER"}
        for sugg in analysis.structural_suggestions:
            with st.container(border=True):
                st.markdown(f"**{TYPE_LABEL.get(sugg.type, sugg.type.upper())}** — {sugg.section}")
                st.markdown(sugg.rationale)

    # ── Line edits ────────────────────────────────────────────────────────────
    with tab_edits:
        for edit in analysis.line_edits:
            with st.container(border=True):
                st.markdown(f"**Original:** {edit.original}")
                st.markdown(f"**Suggested:** {edit.suggested}")
                st.caption(f"Why: {edit.reason}")

    # ── Music ─────────────────────────────────────────────────────────────────
    with tab_music:
        for music in analysis.music_tone_per_section:
            with st.container(border=True):
                st.markdown(f"**{music.section}**")
                st.markdown(f"*{music.tone}* · {music.tempo}")
                track = getattr(music, "suggested_track", None)
                if track:
                    st.markdown(f"🎵 **Track reference:** {track}")
                st.caption(music.rationale)

    # ── Annotated Script ──────────────────────────────────────────────────────
    with tab_script:
        st.caption(
            "Your script with every suggestion mapped inline. "
            "Hover any coloured passage to read the annotation."
        )
        raw_script: str = st.session_state.script_text
        if raw_script:
            st.markdown(
                build_annotated_script_html(raw_script, analysis),
                unsafe_allow_html=True,
            )
        else:
            st.info("Script text not stored — re-submit from Step I.")

    # ── Action ────────────────────────────────────────────────────────────────
    st.divider()
    n_approved = len(st.session_state.approved_indices)
    if n_approved == 0:
        st.button("Generate Production Prompts", disabled=True,
                  help="Approve at least one b-roll shot first")
    else:
        if st.button(
            f"Generate Production Prompts for {n_approved} Shot{'s' if n_approved != 1 else ''} →",
            type="primary",
        ):
            approved_shots = [
                analysis.broll_opportunities[i]
                for i in sorted(st.session_state.approved_indices)
            ]
            with st.spinner("Crafting production prompts…"):
                try:
                    shot_list = generate_production_prompts(approved_shots)
                    st.session_state.shot_list = shot_list
                    st.session_state.stage = "prompts"
                    st.rerun()
                except Exception as e:
                    st.error(f"Stage 2 failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3: PRODUCTION PROMPTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "prompts":
    shot_list: ShotList = st.session_state.shot_list

    st.subheader("III. Review Production Prompts")
    st.caption("These prompts are what will be sent to each tool. Review before generating assets.")

    by_tool: dict = {}
    for shot in shot_list.shots:
        by_tool.setdefault(shot.tool, []).append(shot)

    if "veo" in by_tool:
        n_veo = len(by_tool["veo"])
        st.warning(
            f"⚠️ {n_veo} Veo generation{'s' if n_veo != 1 else ''} will run. "
            f"Each takes 1–3 minutes and costs API credits (~$0.50–3.00 per clip)."
        )

    for tool, shots in by_tool.items():
        st.markdown(f"### `{tool}` — {len(shots)} shot{'s' if len(shots) != 1 else ''}")
        for shot in shots:
            with st.container(border=True):
                st.markdown(f"**Shot {shot.shot_index}**")
                st.code(shot.production_prompt, language="text")
                if shot.alternates:
                    with st.expander("Alternate phrasings"):
                        for alt in shot.alternates:
                            st.code(alt, language="text")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Analysis"):
            st.session_state.stage = "critique"
            st.rerun()
    with col2:
        if st.button("Generate All Assets →", type="primary"):
            st.session_state.stage = "generating"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3.5: GENERATING
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "generating":
    shot_list: ShotList = st.session_state.shot_list
    st.subheader("Generating Assets…")

    output_dir = Path("./streamlit_output") / st.session_state.script_name
    output_dir.mkdir(parents=True, exist_ok=True)

    with st.spinner(
        f"Running generators for {len(shot_list.shots)} shot(s). Veo shots may take 1–3 minutes each."
    ):
        try:
            results = dispatch_generation(shot_list, output_dir)
            st.session_state.generation_results = results
            st.session_state.output_dir = output_dir
            st.session_state.stage = "complete"
            st.rerun()
        except Exception as e:
            st.error(f"Generation failed: {e}")
            if st.button("Back to Prompts"):
                st.session_state.stage = "prompts"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4: RESULTS + ANNOTATED SCRIPT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "complete":
    results    = st.session_state.generation_results
    output_dir = st.session_state.output_dir
    analysis: ScriptAnalysis = st.session_state.analysis
    script_text: str = st.session_state.script_text

    st.subheader("IV. Generated Assets & Annotated Script")

    successes = [r for r in results if r.success]
    failures  = [r for r in results if not r.success]

    col1, col2 = st.columns(2)
    col1.metric("Succeeded", len(successes))
    col2.metric("Failed", len(failures))

    if failures:
        with st.expander(f"⚠️ {len(failures)} failed shot{'s' if len(failures) != 1 else ''}"):
            for r in failures:
                st.markdown(f"**Shot {r.shot_index}** ({r.tool}): {r.error}")

    tab_assets, tab_script = st.tabs(["Generated Assets", "Annotated Script"])

    # ── Assets tab ────────────────────────────────────────────────────────────
    with tab_assets:
        by_tool: dict = {}
        for r in successes:
            by_tool.setdefault(r.tool, []).append(r)

        if "nano_banana" in by_tool:
            st.markdown("### 🍌 Generated Images")
            cols = st.columns(min(3, len(by_tool["nano_banana"])))
            for i, r in enumerate(by_tool["nano_banana"]):
                with cols[i % 3]:
                    st.image(str(r.output_path), caption=f"Shot {r.shot_index}")

        if "veo" in by_tool:
            st.markdown("### 🎬 Generated Videos")
            for r in by_tool["veo"]:
                st.markdown(f"**Shot {r.shot_index}**")
                st.video(str(r.output_path))

        if "stock" in by_tool:
            st.markdown("### 📼 Stock Search Queries")
            stock_md_path = output_dir / "stock_queries.md"
            if stock_md_path.exists():
                st.markdown(stock_md_path.read_text())

        if "self-shot" in by_tool:
            st.markdown("### 🎥 Shooting Notes")
            notes_md_path = output_dir / "shooting_notes.md"
            if notes_md_path.exists():
                st.markdown(notes_md_path.read_text())

        st.divider()
        st.caption(f"Assets saved to `{output_dir}`")

    # ── Annotated script tab ──────────────────────────────────────────────────
    with tab_script:
        st.markdown("### The Script — Fully Annotated")
        st.caption(
            "Every highlight below is clickable on hover: b-roll placement, "
            "line edits, structural cuts, and expansions — all mapped directly to your text."
        )

        if script_text:
            annotated_html = build_annotated_script_html(script_text, analysis)
            st.markdown(annotated_html, unsafe_allow_html=True)
        else:
            st.info("Script text unavailable. Re-run from Step I to populate.")

        st.divider()

        # ── Musical score guide ───────────────────────────────────────────────
        st.markdown("### 🎵 Musical Score Guide")
        for music in analysis.music_tone_per_section:
            with st.container(border=True):
                col_sec, col_trk = st.columns([2, 3])
                with col_sec:
                    st.markdown(f"**{music.section}**")
                    st.markdown(f"*{music.tone}* · {music.tempo}")
                with col_trk:
                    track = getattr(music, "suggested_track", None)
                    if track:
                        st.markdown(f"🎵 {track}")
                    st.caption(music.rationale)

        st.divider()

        # ── Structural reference ──────────────────────────────────────────────
        st.markdown("### 🏗️ Structural Changes Reference")
        cuts    = [s for s in analysis.structural_suggestions if s.type == "cut"]
        expands = [s for s in analysis.structural_suggestions if s.type == "expand"]
        reorders= [s for s in analysis.structural_suggestions if s.type == "reorder"]

        if cuts:
            st.markdown("**✂️ Cut**")
            for s in cuts:
                st.markdown(f"- *{s.section}* — {s.rationale}")
        if expands:
            st.markdown("**➕ Expand**")
            for s in expands:
                st.markdown(f"- *{s.section}* — {s.rationale}")
        if reorders:
            st.markdown("**🔀 Reorder**")
            for s in reorders:
                st.markdown(f"- *{s.section}* — {s.rationale}")

    st.divider()
    if st.button("Analyse Another Script", type="primary"):
        reset_state()
        st.rerun()


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "**aiditor** · AI-assisted video essay production · "
    "[GitHub](https://github.com/tzdwekat/aiditor)"
)
