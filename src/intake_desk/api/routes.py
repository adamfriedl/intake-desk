from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from intake_desk.config import get_settings
from intake_desk.orchestrator.pipeline import IntakePipeline
from intake_desk.rag.retrieval import get_chunk_detail
from intake_desk.review.store import session_store
from intake_desk.schemas.models import (
    ChunkDetail,
    SectionReviewUpdate,
    SessionRecord,
)

router = APIRouter()
WEB_DIR = Path(__file__).resolve().parents[3] / "web"


class IntakeRequest(BaseModel):
    message: str = Field(min_length=8, max_length=8000)
    include_draft: bool = True


def _llm_configured() -> bool:
    settings = get_settings()
    return bool(
        settings.openrouter_api_key or settings.anthropic_api_key or settings.openai_api_key
    )


@router.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/intake", response_model=SessionRecord)
async def run_intake(request: IntakeRequest) -> SessionRecord:
    if not _llm_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "No LLM API key configured. Copy .env.example to .env and set "
                "OPENROUTER_API_KEY (recommended)."
            ),
        )

    settings = get_settings()
    pipeline = IntakePipeline(settings)
    try:
        result = await pipeline.run(request.message, include_draft=request.include_draft)
        return session_store.save_pipeline(result)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api/sessions/{session_id}", response_model=SessionRecord)
async def get_session(session_id: UUID) -> SessionRecord:
    record = session_store.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return record


@router.get("/api/chunks/{chunk_id}", response_model=ChunkDetail)
async def get_chunk(chunk_id: str) -> ChunkDetail:
    detail = get_chunk_detail(get_settings(), chunk_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return ChunkDetail.model_validate(detail)


@router.patch("/api/review/{session_id}/sections/{index}", response_model=SessionRecord)
async def update_section_review(
    session_id: UUID,
    index: int,
    update: SectionReviewUpdate,
) -> SessionRecord:
    try:
        return session_store.update_section(session_id, index, update)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/review/{session_id}/approve-all", response_model=SessionRecord)
async def approve_all_sections(session_id: UUID) -> SessionRecord:
    try:
        return session_store.approve_all(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
