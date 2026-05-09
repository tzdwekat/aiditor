import json
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

# Stage tracking
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "approved_indices" not in st.session_state:
    st.session_state.approved_indices = set()
if "shot_list" not in st.session_state:
    st.session_state.shot_list = None
if "generation_results" not in st.session_state:
    st.session_state.generation_results = None
if "script_name" not in st.session_state:
    st.session_state.script_name = "untitled"


def reset_state():
    """Reset to start-over state."""
    st.session_state.stage = "input"
    st.session_state.analysis = None
    st.session_state.approved_indices = set()
    st.session_state.shot_list = None
    st.session_state.generation_results = None


# Header
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
# ============================================================
# STAGE 1: INPUT
# ============================================================
if st.session_state.stage == "input":
    st.subheader("Step 1: Provide your script")
    
    input_method = st.radio(
        "How do you want to provide the script?",
        ["Paste text", "Upload file"],
        horizontal=True,
    )
    
    script_text = None
    
    if input_method == "Paste text":
        pasted = st.text_area(
            "Paste your script here",
            height=300,
            placeholder="Paste the full text of your video essay script...",
        )
        if pasted.strip():
            script_text = pasted
            st.session_state.script_name = "pasted_script"
    
    else:
        uploaded = st.file_uploader(
            "Upload script file",
            type=["md", "txt", "docx", "pdf"],
        )
        if uploaded is not None:
            # Save uploaded file to a temp location and convert
            temp_path = Path("/tmp") / uploaded.name
            temp_path.write_bytes(uploaded.read())
            
            try:
                script_text = script_to_text(str(temp_path))
                st.session_state.script_name = uploaded.name.rsplit(".", 1)[0]
                st.success(f"Loaded {uploaded.name} ({len(script_text):,} characters)")
            except Exception as e:
                st.error(f"Failed to read file: {e}")
    
    if script_text:
        st.divider()
        if st.button("Analyze script", type="primary"):
            with st.spinner("Running analyzer... (15-30 seconds)"):
                try:
                    analysis = analyze_script(script_text)
                    st.session_state.analysis = analysis
                    st.session_state.stage = "approval"
                    st.rerun()
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

# ============================================================
# STAGE 2: ANALYSIS & APPROVAL
# ============================================================
elif st.session_state.stage == "approval":
    analysis: ScriptAnalysis = st.session_state.analysis
    
    st.subheader("Step 2: Review analysis & approve shots")
    
    # Overall assessment as a prominent callout
    st.info(f"**Overall assessment:** {analysis.overall_assessment}")
    
    # Tabs for the different analysis sections
    tab_broll, tab_structure, tab_edits, tab_music = st.tabs([
        f"B-roll ({len(analysis.broll_opportunities)})",
        f"Structure ({len(analysis.structural_suggestions)})",
        f"Line edits ({len(analysis.line_edits)})",
        f"Music ({len(analysis.music_tone_per_section)})",
    ])
    
    with tab_broll:
        st.caption("Check the boxes for shots you want to generate.")
        
        # Tool palette legend
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown("🎬 **veo** — AI video")
        col2.markdown("🍌 **nano_banana** — AI image")
        col3.markdown("📼 **stock** — search query")
        col4.markdown("🎥 **self-shot** — film yourself")
        
        st.divider()
        
        for i, shot in enumerate(analysis.broll_opportunities):
            tool_emoji = {
                "veo": "🎬",
                "nano_banana": "🍌",
                "stock": "📼",
                "self-shot": "🎥",
            }.get(shot.tool_recommendation, "❓")
            
            priority_color = {
                "high": "red",
                "medium": "orange",
                "low": "gray",
            }.get(shot.priority, "gray")
            
            with st.container(border=True):
                col_check, col_content = st.columns([1, 11])
                
                with col_check:
                    is_approved = st.checkbox(
                        "Approve",
                        key=f"approve_{i}",
                        label_visibility="collapsed",
                    )
                    if is_approved:
                        st.session_state.approved_indices.add(i)
                    else:
                        st.session_state.approved_indices.discard(i)
                
                with col_content:
                    st.markdown(
                        f"**Shot {i+1}** {tool_emoji} `{shot.tool_recommendation}` "
                        f"· :{priority_color}[{shot.priority.upper()}] "
                        f"· {shot.timestamp_estimate}"
                    )
                    st.markdown(f"> {shot.script_excerpt}")
                    st.markdown(f"**Suggested visual:** {shot.suggested_visual}")
                    with st.expander("Why this visual?"):
                        st.markdown(shot.rationale)
    
    with tab_structure:
        for sugg in analysis.structural_suggestions:
            with st.container(border=True):
                st.markdown(f"**[{sugg.type.upper()}]** {sugg.section}")
                st.markdown(sugg.rationale)
    
    with tab_edits:
        for edit in analysis.line_edits:
            with st.container(border=True):
                st.markdown(f"**Original:** {edit.original}")
                st.markdown(f"**Suggested:** {edit.suggested}")
                st.caption(f"Why: {edit.reason}")
    
    with tab_music:
        for music in analysis.music_tone_per_section:
            with st.container(border=True):
                st.markdown(f"**{music.section}**")
                st.markdown(f"Tone: *{music.tone}* · Tempo: *{music.tempo}*")
                st.caption(music.rationale)
    
    # Action buttons
    st.divider()
    n_approved = len(st.session_state.approved_indices)
    
    if n_approved == 0:
        st.button("Generate production prompts", disabled=True, help="Approve at least one shot first")
    else:
        if st.button(
            f"Generate production prompts for {n_approved} shot{'s' if n_approved != 1 else ''}",
            type="primary",
        ):
            approved_shots = [
                analysis.broll_opportunities[i]
                for i in sorted(st.session_state.approved_indices)
            ]
            
            with st.spinner("Generating tool-specific production prompts..."):
                try:
                    shot_list = generate_production_prompts(approved_shots)
                    st.session_state.shot_list = shot_list
                    st.session_state.stage = "prompts"
                    st.rerun()
                except Exception as e:
                    st.error(f"Stage 2 failed: {e}")

# ============================================================
# STAGE 3: PRODUCTION PROMPTS REVIEW
# ============================================================
elif st.session_state.stage == "prompts":
    shot_list: ShotList = st.session_state.shot_list
    
    st.subheader("Step 3: Review production prompts")
    st.caption("These prompts are what will be sent to each tool. Review before generating assets.")
    
    # Group by tool
    by_tool = {}
    for shot in shot_list.shots:
        by_tool.setdefault(shot.tool, []).append(shot)
    
    # Cost warning if veo is present
    if "veo" in by_tool:
        n_veo = len(by_tool["veo"])
        st.warning(
            f"⚠️ {n_veo} Veo generation{'s' if n_veo != 1 else ''} will run. "
            f"Each takes 1-3 minutes and costs API credits "
            f"(~$0.50-3.00 per clip depending on duration)."
        )
    
    for tool, shots in by_tool.items():
        st.markdown(f"### `{tool}` ({len(shots)} shot{'s' if len(shots) != 1 else ''})")
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
        if st.button("← Back to approval"):
            st.session_state.stage = "approval"
            st.rerun()
    with col2:
        if st.button("Generate all assets", type="primary"):
            st.session_state.stage = "generating"
            st.rerun()


# ============================================================
# STAGE 3.5: GENERATING (in progress)
# ============================================================
elif st.session_state.stage == "generating":
    shot_list: ShotList = st.session_state.shot_list
    
    st.subheader("Generating assets...")
    
    output_dir = Path("./streamlit_output") / st.session_state.script_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with st.spinner(f"Running generators for {len(shot_list.shots)} shot(s). Veo shots may take 1-3 minutes each."):
        try:
            results = dispatch_generation(shot_list, output_dir)
            st.session_state.generation_results = results
            st.session_state.output_dir = output_dir
            st.session_state.stage = "complete"
            st.rerun()
        except Exception as e:
            st.error(f"Generation failed: {e}")
            if st.button("Back to prompts"):
                st.session_state.stage = "prompts"
                st.rerun()

# ============================================================
# STAGE 4: RESULTS
# ============================================================
elif st.session_state.stage == "complete":
    results = st.session_state.generation_results
    output_dir = st.session_state.output_dir
    
    st.subheader("Step 4: Generated assets")
    
    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]
    
    col1, col2 = st.columns(2)
    col1.metric("Succeeded", len(successes))
    col2.metric("Failed", len(failures))
    
    if failures:
        with st.expander(f"⚠️ {len(failures)} failed shot{'s' if len(failures) != 1 else ''}"):
            for r in failures:
                st.markdown(f"**Shot {r.shot_index}** ({r.tool}): {r.error}")
    
    st.divider()
    
    # Group successes by tool for display
    by_tool = {}
    for r in successes:
        by_tool.setdefault(r.tool, []).append(r)
    
    # Render images
    if "nano_banana" in by_tool:
        st.markdown("### 🍌 Generated images")
        cols = st.columns(min(3, len(by_tool["nano_banana"])))
        for i, r in enumerate(by_tool["nano_banana"]):
            with cols[i % 3]:
                st.image(str(r.output_path), caption=f"Shot {r.shot_index}")
    
    # Render videos
    if "veo" in by_tool:
        st.markdown("### 🎬 Generated videos")
        for r in by_tool["veo"]:
            st.markdown(f"**Shot {r.shot_index}**")
            st.video(str(r.output_path))
    
    # Render stock queries
    if "stock" in by_tool:
        st.markdown("### 📼 Stock search queries")
        stock_md_path = output_dir / "stock_queries.md"
        if stock_md_path.exists():
            st.markdown(stock_md_path.read_text())
    
    # Render shooting notes
    if "self-shot" in by_tool:
        st.markdown("### 🎥 Shooting notes")
        notes_md_path = output_dir / "shooting_notes.md"
        if notes_md_path.exists():
            st.markdown(notes_md_path.read_text())
    
    st.divider()
    st.caption(f"All assets saved to `{output_dir}`")
    
    if st.button("Run another script", type="primary"):
        reset_state()
        st.rerun()


# Footer
st.divider()
st.caption(
    "**aiditor** is a portfolio project demonstrating LLM-augmented "
    "video essay production. [GitHub](https://github.com/tzdwekat/aiditor)"
)