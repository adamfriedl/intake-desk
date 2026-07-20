"""Matter classification agent."""

from __future__ import annotations

import re

from intake_desk.config import Settings
from intake_desk.llm import LLMClient, parse_json_response
from intake_desk.schemas.models import IntakeRecord, MatterClassification, MatterType

CLASSIFY_SYSTEM = """You classify self-help legal matters into one of:
tenant_housing, consumer_debt, benefits_denial, unknown.
Return JSON with keys: matter_type, confidence (0-1), routing (short string),
human_review_required (bool), rationale (string).

Set human_review_required=true when the matter involves eviction/lockout risk, a lawsuit
or summons, wage garnishment, benefits appeal deadlines, alleged discrimination/retaliation,
or anything you are unsure about. Clear low-stakes info questions may be false."""

# Deterministic escalation — do not rely on the model alone for high-stakes routing.
_ESCALATION_PATTERNS = (
    r"\bevict",
    r"\block\s*out\b",
    r"\bsummons\b",
    r"\blawsuit\b",
    r"\bsued\b",
    r"\bgarnish",
    r"\bappeal\b",
    r"\bdenial\b",
    r"\bdenied\b",
    r"\boverpayment\b",
    r"\bretaliat",
    r"\bdiscriminat",
    r"\bdeadline\b",
    r"\bcourt\b",
)


def requires_human_review(
    settings: Settings,
    user_message: str,
    intake: IntakeRecord,
    classification: MatterClassification,
) -> bool:
    if classification.human_review_required:
        return True
    if classification.confidence < settings.classification_confidence_threshold:
        return True
    if classification.matter_type == MatterType.UNKNOWN:
        return True
    if intake.urgency == "high":
        return True

    haystack = " ".join(
        [
            user_message,
            " ".join(intake.facts),
            " ".join(intake.flags),
            intake.relief_sought or "",
        ]
    ).lower()
    return any(re.search(pattern, haystack) for pattern in _ESCALATION_PATTERNS)


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
    classification.human_review_required = requires_human_review(
        settings, user_message, intake, classification
    )
    return classification
