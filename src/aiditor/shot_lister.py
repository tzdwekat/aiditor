import json
from pathlib import Path
from typing import List
from anthropic import Anthropic
from pydantic import BaseModel
from .models import BrollOpportunity

PROMPT_PATH = Path(__file__).parent / "prompts" / "shot_lister_system.md"


class ProductionShot(BaseModel):
    shot_index: int
    tool: str
    production_prompt: str
    alternates: list[str] = []


class ShotList(BaseModel):
    shots: list[ProductionShot]


def generate_production_prompts(
    approved_shots: List[BrollOpportunity],
    model: str = "claude-sonnet-4-5-20250929"
) -> ShotList:
    """Stage 2: Take approved B-roll shots and generate production-ready prompts.
    
    Only fires for approved shots — this is where the lazy evaluation pays off.
    Different tools get different prompt formats (veo prompts are cinematic
    descriptions, stock are search queries, etc.).
    """
    if not approved_shots:
        return ShotList(shots=[])
    
    client = Anthropic()
    system_prompt = PROMPT_PATH.read_text()
    
    shots_text = "\n\n".join([
        f"Shot {i}:\n"
        f"  Tool: {shot.tool_recommendation}\n"
        f"  Script excerpt: {shot.script_excerpt}\n"
        f"  Suggested visual: {shot.suggested_visual}\n"
        f"  Rationale: {shot.rationale}"
        for i, shot in enumerate(approved_shots, 1)
    ])
    
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Generate production prompts for these approved shots:\n\n{shots_text}"
        }]
    )
    
    raw_text = response.content[0].text.strip()
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1])
    
    data = json.loads(raw_text)
    return ShotList.model_validate(data)