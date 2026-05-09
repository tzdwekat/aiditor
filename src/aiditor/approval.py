import re
from pathlib import Path
from typing import List
from .models import ScriptAnalysis, BrollOpportunity


def write_approval_markdown(analysis: ScriptAnalysis, output_path: Path) -> None:
    """Write a markdown file with checkboxes for each B-roll opportunity.
    
    The user edits this file to mark which shots they want generated.
    """
    lines = []
    lines.append("# B-Roll Approval")
    lines.append("")
    lines.append("Check the boxes for shots you want to generate, then run:")
    lines.append("")
    lines.append("```")
    lines.append(f"aiditor approve {output_path.name}")
    lines.append("```")
    lines.append("")
    lines.append("Stage 2 generates production-ready prompts only for approved shots.")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for i, shot in enumerate(analysis.broll_opportunities, 1):
        lines.append(f"## Shot {i} — {shot.priority.upper()} priority")
        lines.append("")
        lines.append(f"- [ ] **Generate this shot**")
        lines.append("")
        lines.append(f"**Timestamp:** {shot.timestamp_estimate}")
        lines.append(f"**Tool:** `{shot.tool_recommendation}`")
        lines.append("")
        lines.append(f"**Script excerpt:**")
        lines.append(f"> {shot.script_excerpt}")
        lines.append("")
        lines.append(f"**Suggested visual:**")
        lines.append(f"{shot.suggested_visual}")
        lines.append("")
        lines.append(f"**Why:** {shot.rationale}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    output_path.write_text("\n".join(lines))


def read_approved_shots(approval_path: Path, analysis: ScriptAnalysis) -> List[BrollOpportunity]:
    """Read an edited approval markdown file and return the approved shots.
    
    Matches checked boxes back to the original analysis by shot order.
    """
    content = approval_path.read_text()
    
    checkbox_pattern = re.compile(r"^- \[([ xX])\] \*\*Generate this shot\*\*", re.MULTILINE)
    matches = checkbox_pattern.findall(content)
    
    if len(matches) != len(analysis.broll_opportunities):
        raise ValueError(
            f"Mismatch between approval file ({len(matches)} checkboxes) "
            f"and analysis ({len(analysis.broll_opportunities)} shots). "
            f"Did the analysis change since the approval file was generated?"
        )
    
    approved = [
        shot for shot, mark in zip(analysis.broll_opportunities, matches)
        if mark.lower() == "x"
    ]
    
    return approved