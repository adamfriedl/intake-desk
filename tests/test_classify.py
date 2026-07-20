from intake_desk.agents.classify import requires_human_review
from intake_desk.config import Settings
from intake_desk.schemas.models import IntakeRecord, MatterClassification, MatterType


def test_requires_human_review_for_summons():
    settings = Settings()
    classification = MatterClassification(
        matter_type=MatterType.CONSUMER_DEBT,
        confidence=0.95,
        routing="debt",
        human_review_required=False,
    )
    assert requires_human_review(
        settings,
        "I was served with a summons for a credit card lawsuit",
        IntakeRecord(urgency="medium"),
        classification,
    )


def test_requires_human_review_for_low_confidence():
    settings = Settings(classification_confidence_threshold=0.75)
    classification = MatterClassification(
        matter_type=MatterType.TENANT_HOUSING,
        confidence=0.4,
        routing="housing",
        human_review_required=False,
    )
    assert requires_human_review(
        settings,
        "rent question",
        IntakeRecord(urgency="low"),
        classification,
    )
