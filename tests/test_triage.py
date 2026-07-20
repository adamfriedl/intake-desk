from uuid import uuid4

from intake_desk.schemas.models import (
    IntakeRecord,
    MatterClassification,
    MatterType,
    PipelineResult,
    TriageOutcome,
)
from intake_desk.triage.outcomes import compute_triage, determine_outcome, needs_jurisdiction


def _roommate_pipeline() -> PipelineResult:
    return PipelineResult(
        session_id=uuid4(),
        intake=IntakeRecord(
            jurisdiction=None,
            facts=["Not on lease", "Lived there 6 months", "Roommate trying to kick user out"],
            urgency="medium",
        ),
        classification=MatterClassification(
            matter_type=MatterType.TENANT_HOUSING,
            confidence=0.95,
            routing="housing-roommate",
            human_review_required=True,
        ),
        answer="Oregon tenant information with citations.",
        citations=[],
    )


def test_roommate_intake_escalates_without_jurisdiction():
    result = _roommate_pipeline()
    outcome, client, case = compute_triage(result)
    assert outcome == TriageOutcome.ESCALATE
    assert client.answer is None
    assert case.jurisdiction_missing is True
    assert "Reference:" in client.message


def test_simple_debt_can_self_help():
    result = PipelineResult(
        session_id=uuid4(),
        intake=IntakeRecord(jurisdiction="oregon", urgency="low"),
        classification=MatterClassification(
            matter_type=MatterType.CONSUMER_DEBT,
            confidence=0.9,
            routing="debt-collections",
            human_review_required=False,
        ),
        answer="Collectors must send validation notice.",
        citations=[],
    )
    outcome = determine_outcome(result)
    assert outcome == TriageOutcome.SELF_HELP


def test_refused_maps_to_refuse_outcome():
    result = PipelineResult(
        session_id=uuid4(),
        intake=IntakeRecord(),
        classification=MatterClassification(
            matter_type=MatterType.UNKNOWN,
            confidence=0.2,
            routing="unknown",
        ),
        refused=True,
        refusal_reason="No sources",
    )
    outcome, client, _ = compute_triage(result)
    assert outcome == TriageOutcome.REFUSE
    assert client.answer is None


def test_housing_without_jurisdiction_flag():
    result = _roommate_pipeline()
    assert needs_jurisdiction(result) is True
