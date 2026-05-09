import json
import os
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
from .models import ScriptAnalysis

load_dotenv()

PROMPT_PATH = Path(__file__).parent / "prompts" / "analyzer_system.md"

def analyze_script(script_text: str, model: str = "claude-sonnet-4-5-20250929") -> ScriptAnalysis:
    """Run Stage 1 analysis on a script using Claude.
    
    Returns a structured ScriptAnalysis object.
    """
    client = Anthropic()
    system_prompt = PROMPT_PATH.read_text()
    
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Analyze the following video essay script:\n\n{script_text}"
            }
        ]
    )
    
    raw_text = response.content[0].text.strip()
    
    # Strip code fences if Claude added them despite instructions
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1])
    
    data = json.loads(raw_text)
    return ScriptAnalysis.model_validate(data)