from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from intake_desk.config import get_settings
from intake_desk.orchestrator.pipeline import IntakePipeline
from intake_desk.schemas.models import PipelineResult

router = APIRouter()
WEB_DIR = Path(__file__).resolve().parents[3] / "web"


class IntakeRequest(BaseModel):
    message: str = Field(min_length=8, max_length=8000)
    include_draft: bool = True


@router.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/intake", response_model=PipelineResult)
async def run_intake(request: IntakeRequest) -> PipelineResult:
    settings = get_settings()
    if not (
        settings.openrouter_api_key
        or settings.anthropic_api_key
        or settings.openai_api_key
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "No LLM API key configured. Copy .env.example to .env and set "
                "OPENROUTER_API_KEY (recommended)."
            ),
        )

    pipeline = IntakePipeline(settings)
    try:
        return await pipeline.run(request.message, include_draft=request.include_draft)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
