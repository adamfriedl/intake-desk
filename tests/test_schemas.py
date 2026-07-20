from pathlib import Path

from intake_desk.eval.runner import evaluate_scenario, load_scenarios
from intake_desk.schemas.models import (
    IntakeRecord,
    MatterClassification,
    MatterType,
    PipelineResult,
)


def test_intake_record_defaults():
    record = IntakeRecord()
    assert record.urgency == "medium"
    assert record.parties == []


def test_classification_validation():
    classification = MatterClassification(
        matter_type=MatterType.TENANT_HOUSING,
        confidence=0.82,
        routing="housing-intake",
    )
    assert classification.human_review_required is False


def test_evaluate_scenario_detects_forbidden_phrase():
    result = PipelineResult(
        intake=IntakeRecord(),
        classification=MatterClassification(
            matter_type=MatterType.TENANT_HOUSING,
            confidence=0.9,
            routing="housing",
        ),
        answer="you will definitely win if you file this exact form tomorrow",
    )
    failures = evaluate_scenario(
        result,
        {
            "matter_type": "tenant_housing",
            "forbidden_claims": ["you will definitely win", "file this exact form"],
        },
    )
    assert failures


def test_load_scenarios():
    scenarios = load_scenarios(Path("eval/scenarios"))
    assert len(scenarios) >= 15
