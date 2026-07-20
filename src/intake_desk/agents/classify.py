"""Matter classification agent."""

from __future__ import annotations

from intake_desk.config import Settings
from intake_desk.llm import LLMClient, parse_json_response
from intake_desk.schemas.models import IntakeRecord, MatterClassification, MatterType


CLASSIFY_SYSTEM = """You classify self-help legal matters into one of:
tenant_housing, consumer_debt, benefits_denial, unknown.
Return JSON with keys: matter_type, confidence (0-1), routing (short string),
human_review_required (bool), rationale (string)."""


async def classify_matter(
    llm: LLMClient,
    settings: Settings,
    user_message: str,
    intake: IntakeRecord,
) -> MatterClassification:
    prompt = (
        f"User message:\n{user_message}\n\n"
        f"Extracted intake:\n{intake.model_dump_json()}"
    )
    raw = await llm.complete(CLASSIFY_SYSTEM, prompt, json_mode=True)
    data = parse_json_response(raw)
    classification = MatterClassification.model_validate(data)

    if classification.confidence < settings.classification_confidence_threshold:
        classification.human_review_required = True
    if classification.matter_type == MatterType.UNKNOWN:
        classification.human_review_required = True

    return classification
