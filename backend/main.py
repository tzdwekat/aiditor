import asyncio
import json
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aiditor.analyzer import analyze_script
from aiditor.generators import dispatch_generation
from aiditor.loaders import script_to_text
from aiditor.models import BrollOpportunity
from aiditor.shot_lister import ProductionShot, ShotList, generate_production_prompts

app = FastAPI(title="aiditor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

_pool = ThreadPoolExecutor(max_workers=4)


def _run(fn, *args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_pool, fn, *args)


# ── Models ────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    script_text: str


class ShotsRequest(BaseModel):
    shots: list[dict]


class GenerateRequest(BaseModel):
    shots: list[dict]
    script_name: str = "untitled"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    suffix = Path(file.filename or "upload.txt").suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        text = await _run(script_to_text, tmp_path)
        return {"text": text, "filename": file.filename}
    except Exception as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    async def stream():
        yield f"data: {json.dumps({'type': 'progress', 'message': 'Consulting the analyst…'})}\n\n"
        try:
            analysis = await _run(analyze_script, req.script_text)
            yield f"data: {json.dumps({'type': 'complete', 'analysis': analysis.model_dump()})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/shots")
async def shots(req: ShotsRequest):
    approved = [BrollOpportunity(**s) for s in req.shots]
    try:
        result = await _run(generate_production_prompts, approved)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    shot_list = ShotList(shots=[ProductionShot(**s) for s in req.shots])
    out_dir = OUTPUT_DIR / req.script_name
    out_dir.mkdir(exist_ok=True)
    try:
        results = await _run(dispatch_generation, shot_list, out_dir)
    except Exception as exc:
        raise HTTPException(500, str(exc))

    serialized = []
    for r in results:
        url = None
        if r.success and r.output_path:
            rel = Path(r.output_path).relative_to(OUTPUT_DIR)
            url = f"/output/{rel.as_posix()}"
        serialized.append({
            "shot_index": r.shot_index,
            "tool": r.tool,
            "success": r.success,
            "error": r.error,
            "output_url": url,
        })
    return {"results": serialized}
