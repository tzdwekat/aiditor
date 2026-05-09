import os
from pathlib import Path
from google import genai
from google.genai import types
from .base import GenerationResult
from ..shot_lister import ProductionShot


class NanoBananaGenerator:
    """Generates static images using Google's Nano Banana (Gemini Flash Image model)."""
    
    def __init__(self, model: str = "gemini-2.5-flash-image"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        self.client = genai.Client(api_key=api_key)
        self.model = model
    
    def generate(self, shot: ProductionShot, output_dir: Path) -> GenerationResult:
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=shot.production_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["Image"],
                ),
            )
            
            # Extract image bytes from response
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    output_path = images_dir / f"shot_{shot.shot_index:02d}.png"
                    output_path.write_bytes(part.inline_data.data)
                    
                    return GenerationResult(
                        shot_index=shot.shot_index,
                        tool="nano_banana",
                        success=True,
                        output_path=output_path,
                    )
            
            return GenerationResult(
                shot_index=shot.shot_index,
                tool="nano_banana",
                success=False,
                error="No image data in response",
            )
        
        except Exception as e:
            return GenerationResult(
                shot_index=shot.shot_index,
                tool="nano_banana",
                success=False,
                error=str(e),
            )