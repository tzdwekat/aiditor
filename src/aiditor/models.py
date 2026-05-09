from pydantic import BaseModel, Field
from typing import Literal

class BrollOpportunity(BaseModel):
    timestamp_estimate: str = Field(description="Approximate location in script, e.g. '0:45-1:10'")
    script_excerpt: str = Field(description="The line or passage this B-roll would accompany")
    suggested_visual: str = Field(description="Specific visual description of what to show")
    priority: Literal["high", "medium", "low"]
    tool_recommendation: Literal["seedance", "nano_banana", "stock", "self-shot"] = Field(
        description="Which tool best fits this shot"
    )
    rationale: str = Field(description="Why this visual adds value beyond what voiceover already conveys")

class StructuralSuggestion(BaseModel):
    type: Literal["reorder", "cut", "expand"]
    section: str
    rationale: str

class LineEdit(BaseModel):
    original: str
    suggested: str
    reason: str

class MusicTone(BaseModel):
    section: str = Field(description="Which part of the script, e.g. 'opening', 'minute 3-5', 'climax'")
    tone: str = Field(description="Mood/feel: tense, contemplative, melancholic, etc.")
    tempo: str = Field(description="Rough tempo: slow, mid, building, etc.")
    rationale: str

class ScriptAnalysis(BaseModel):
    overall_assessment: str = Field(description="2-3 sentences on the script's strengths and weaknesses")
    structural_suggestions: list[StructuralSuggestion]
    line_edits: list[LineEdit]
    broll_opportunities: list[BrollOpportunity]
    music_tone_per_section: list[MusicTone]