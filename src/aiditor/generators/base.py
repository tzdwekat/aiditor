from pathlib import Path
from typing import Protocol
from ..shot_lister import ProductionShot


class GenerationResult:
    """Result of running a single shot through a generator."""
    def __init__(
        self,
        shot_index: int,
        tool: str,
        success: bool,
        output_path: Path | None = None,
        error: str | None = None,
        metadata: dict | None = None,
    ):
        self.shot_index = shot_index
        self.tool = tool
        self.success = success
        self.output_path = output_path
        self.error = error
        self.metadata = metadata or {}


class Generator(Protocol):
    """Common interface every generator implements.
    
    Some generators call APIs (veo, nano_banana). Others just write 
    structured outputs to disk (stock, self-shot). The interface is the same
    so the dispatcher doesn't care which kind it's calling.
    """
    def generate(self, shot: ProductionShot, output_dir: Path) -> GenerationResult:
        ...