from pathlib import Path
from typing import List
from .base import Generator, GenerationResult
from .veo import VeoGenerator
from .nano_banana import NanoBananaGenerator
from .stock import StockQueryGenerator
from .self_shot import SelfShotNotesGenerator
from ..shot_lister import ShotList


GENERATOR_REGISTRY = {
    "veo": VeoGenerator,
    "nano_banana": NanoBananaGenerator,
    "stock": StockQueryGenerator,
    "self-shot": SelfShotNotesGenerator,
}


def dispatch_generation(shot_list: ShotList, output_dir: Path) -> List[GenerationResult]:
    """Run each shot through the appropriate generator.
    
    Lazy initialization: generators are only constructed if a shot needs them.
    Means you don't need a Gemini key set if all your approved shots are stock 
    or self-shot.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    instantiated: dict[str, Generator] = {}
    results: list[GenerationResult] = []
    
    for shot in shot_list.shots:
        if shot.tool not in GENERATOR_REGISTRY:
            results.append(GenerationResult(
                shot_index=shot.shot_index,
                tool=shot.tool,
                success=False,
                error=f"No generator registered for tool: {shot.tool}",
            ))
            continue
        
        if shot.tool not in instantiated:
            generator_class = GENERATOR_REGISTRY[shot.tool]
            instantiated[shot.tool] = generator_class()
        
        result = instantiated[shot.tool].generate(shot, output_dir)
        results.append(result)
    
    return results