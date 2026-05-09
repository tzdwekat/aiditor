from pathlib import Path
from .base import GenerationResult
from ..shot_lister import ProductionShot


class SelfShotNotesGenerator:
    """Writes shooting notes to a markdown file. No API calls."""
    
    def generate(self, shot: ProductionShot, output_dir: Path) -> GenerationResult:
        output_path = output_dir / "shooting_notes.md"
        
        with open(output_path, "a") as f:
            f.write(f"## Shot {shot.shot_index}\n\n")
            f.write(f"{shot.production_prompt}\n\n")
            if shot.alternates:
                f.write("**Alternative approaches:**\n")
                for alt in shot.alternates:
                    f.write(f"- {alt}\n")
                f.write("\n")
            f.write("---\n\n")
        
        return GenerationResult(
            shot_index=shot.shot_index,
            tool="self-shot",
            success=True,
            output_path=output_path,
        )