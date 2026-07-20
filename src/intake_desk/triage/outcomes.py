"""Triage outcomes — client-facing routing vs staff case file."""

from __future__ import annotations

from datetime import UTC, datetime

from intake_desk.schemas.models import (
    CaseFile,
    ClientResponse,
    MatterType,
    PipelineResult,
    TriageOutcome,
)

STATE_SPECIFIC_MATTERS = {MatterType.TENANT_HOUSING}


def needs_jurisdiction(result: PipelineResult) -> bool:
    if result.classification.matter_type not in STATE_SPECIFIC_MATTERS:
        return False
    jurisdiction = (result.intake.jurisdiction or "").strip().lower()
    return jurisdiction in {"", "unknown", "null"}


def determine_outcome(result: PipelineResult) -> TriageOutcome:
    if result.refused or result.classification.matter_type == MatterType.UNKNOWN:
        return TriageOutcome.REFUSE
    if (
        result.classification.human_review_required
        or needs_jurisdiction(result)
        or result.intake.urgency == "high"
    ):
        return TriageOutcome.ESCALATE
    return TriageOutcome.SELF_HELP


def build_client_response(result: PipelineResult, outcome: TriageOutcome) -> ClientResponse:
    if outcome == TriageOutcome.REFUSE:
        return ClientResponse(
            outcome=outcome,
            headline="We can't answer this from our self-help materials",
            message=result.refusal_reason
            or "This question is outside our materials or needs advocate review.",
            answer=None,
            next_steps=[
                "Contact your local legal aid organization for help.",
                "If you are in immediate danger, call emergency services.",
            ],
        )

    if outcome == TriageOutcome.ESCALATE:
        parts = [
            "Your situation has been recorded for advocate follow-up.",
            f"Reference: {result.session_id}",
        ]
        if needs_jurisdiction(result):
            parts.append(
                "We need your city or state to share location-specific housing information."
            )
        if result.classification.human_review_required:
            parts.append(
                "An advocate should review the facts before you rely on general information."
            )
        return ClientResponse(
            outcome=outcome,
            headline="An advocate will follow up",
            message=" ".join(parts),
            answer=None,
            next_steps=[
                "Watch for contact from the legal aid intake team.",
                "Gather relevant documents (lease, notices, messages).",
                "Note important dates and deadlines.",
                "If you face an immediate lockout or safety issue, seek urgent help.",
            ],
        )

    return ClientResponse(
        outcome=outcome,
        headline="General information from our materials",
        message=(
            "This is educational information with sources below — not legal advice. "
            "If your situation is more complex, request advocate follow-up."
        ),
        answer=result.answer,
        next_steps=[
            "Read the cited materials and confirm they apply to your situation.",
            "Request advocate review if anything is unclear or urgent.",
        ],
    )


def build_case_file(result: PipelineResult, outcome: TriageOutcome) -> CaseFile:
    return CaseFile(
        session_id=result.session_id,
        created_at=datetime.now(UTC),
        matter_type=result.classification.matter_type,
        routing=result.classification.routing,
        urgency=result.intake.urgency,
        jurisdiction=result.intake.jurisdiction,
        jurisdiction_missing=needs_jurisdiction(result),
        parties=result.intake.parties,
        facts=result.intake.facts,
        flags=result.intake.flags,
        relief_sought=result.intake.relief_sought,
        triage=outcome,
        human_review_required=result.classification.human_review_required,
        classification_rationale=result.classification.rationale,
        grounded_answer=result.answer,
        citations=result.citations,
        refused=result.refused,
        refusal_reason=result.refusal_reason,
    )


def compute_triage(result: PipelineResult) -> tuple[TriageOutcome, ClientResponse, CaseFile]:
    outcome = determine_outcome(result)
    return outcome, build_client_response(result, outcome), build_case_file(result, outcome)
