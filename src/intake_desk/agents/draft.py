"""Draft outline agent — section-level output, not filings."""

from __future__ import annotations

from intake_desk.llm import LLMClient, parse_json_response
from intake_desk.schemas.models import DraftOutline, MatterClassification

DRAFT_SYSTEM = """Create a section-level draft outline for advocate review.
Return JSON with keys: matter_type, sections (list of {title, content, status}),
disclaimer (string). Status must be one of: draft, needs_review, blocked.
Do not produce court-ready filings or guaranteed outcomes."""


async def build_draft_outline(
    llm: LLMClient,
    classification: MatterClassification,
    answer: str,
) -> DraftOutline:
    prompt = (
        f"Matter classification:\n{classification.model_dump_json()}\n\n"
        f"Grounded answer:\n{answer}"
    )
    raw = await llm.complete(DRAFT_SYSTEM, prompt, json_mode=True)
    data = parse_json_response(raw)
    return DraftOutline.model_validate(data)
