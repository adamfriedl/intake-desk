"""Intake extraction agent."""

from __future__ import annotations

from intake_desk.llm import LLMClient, parse_json_response
from intake_desk.schemas.models import IntakeRecord


INTAKE_SYSTEM = """You extract structured legal intake facts from layperson messages.
Return JSON with keys: parties (list), jurisdiction (string or null), facts (list),
relief_sought (string or null), urgency (low|medium|high), flags (list of strings).
Do not provide legal advice. Only extract what the user stated or clearly implied."""


async def extract_intake(llm: LLMClient, user_message: str) -> IntakeRecord:
    raw = await llm.complete(INTAKE_SYSTEM, user_message, json_mode=True)
    data = parse_json_response(raw)
    return IntakeRecord.model_validate(data)
