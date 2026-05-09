import os
import time
import urllib.request
from pathlib import Path
from google import genai
from .base import GenerationResult
from ..shot_lister import ProductionShot
from google.genai import types


class VeoGenerator:
    """Generates motion video clips with native audio using Google Veo via Gemini API."""
    
    def __init__(self, model: str = "veo-3.1-fast-generate-preview"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        self.client = genai.Client(api_key=api_key)
        self.model = model
    
    def generate(self, shot: ProductionShot, output_dir: Path) -> GenerationResult:
        videos_dir = output_dir / "videos"
        videos_dir.mkdir(exist_ok=True)
        
        try:
            operation = self.client.models.generate_videos(
                model=self.model,
                prompt=shot.production_prompt,
                config=types.GenerateVideosConfig(
                    duration_seconds=8,
                ),
            )
            
            # Poll for completion — Veo typically takes 1-3 minutes
            while not operation.done:
                time.sleep(10)
                operation = self.client.operations.get(operation)
            
            # Extract the generated video file reference
            generated = operation.response.generated_videos[0]

            # Download to local disk via the SDK (handles auth automatically)
            output_path = videos_dir / f"shot_{shot.shot_index:02d}.mp4"
            self.client.files.download(file=generated.video)
            generated.video.save(str(output_path))
            
            return GenerationResult(
                shot_index=shot.shot_index,
                tool="veo",
                success=True,
                output_path=output_path,
            )
        
        except Exception as e:
            import traceback
            
            # Try to extract the API's response body which contains the actual error reason
            error_details = []
            error_details.append(f"Exception type: {type(e).__name__}")
            error_details.append(f"Exception message: {str(e)}")
            
            # urllib HTTPError has a .read() method that contains the response body
            if hasattr(e, 'read'):
                try:
                    body = e.read().decode('utf-8')
                    error_details.append(f"Response body: {body}")
                except Exception:
                    pass
            
            # google-genai SDK errors often have a .response or .details attribute
            if hasattr(e, 'response'):
                error_details.append(f"Response: {e.response}")
            if hasattr(e, 'details'):
                error_details.append(f"Details: {e.details}")
            if hasattr(e, 'code'):
                error_details.append(f"Code: {e.code}")
            
            error_details.append(f"Traceback:\n{traceback.format_exc()}")
            full_error = "\n".join(error_details)
            
            return GenerationResult(
                shot_index=shot.shot_index,
                tool="veo",
                success=False,
                error=full_error,
            )