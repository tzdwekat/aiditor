from pathlib import Path
from .base import GenerationResult
from ..shot_lister import ProductionShot


class StockQueryGenerator:
    """Writes stock search queries to a markdown file. No API calls."""
    
    def generate(self, shot: ProductionShot, output_dir: Path) -> GenerationResult:
        output_path = output_dir / "stock_queries.md"
        
        with open(output_path, "a") as f:
            f.write(f"## Shot {shot.shot_index}\n\n")
            f.write(f"**Primary query:**\n```\n{shot.production_prompt}\n```\n\n")
            if shot.alternates:
                f.write("**Alternate queries:**\n")
                for alt in shot.alternates:
                    f.write(f"- `{alt}`\n")
                f.write("\n")
            f.write("---\n\n")
        
        return GenerationResult(
            shot_index=shot.shot_index,
            tool="stock",
            success=True,
            output_path=output_path,
            metadata={"queries": [shot.production_prompt] + shot.alternates},
        )