from uuid import uuid4

from intake_desk.review.store import SessionStore
from intake_desk.schemas.models import (
    DraftOutline,
    DraftSection,
    IntakeRecord,
    MatterClassification,
    MatterType,
    PipelineResult,
    SectionReviewStatus,
    SectionReviewUpdate,
)


def test_session_store_tracks_section_edits():
    store = SessionStore()
    result = PipelineResult(
        session_id=uuid4(),
        intake=IntakeRecord(),
        classification=MatterClassification(
            matter_type=MatterType.TENANT_HOUSING,
            confidence=0.9,
            routing="housing",
        ),
        draft_outline=DraftOutline(
            matter_type=MatterType.TENANT_HOUSING,
            sections=[
                DraftSection(title="Background", content="Original text"),
            ],
        ),
    )
    record = store.save_pipeline(result)
    updated = store.update_section(
        record.session_id,
        0,
        SectionReviewUpdate(content="Edited text", review_status=SectionReviewStatus.EDITED),
    )
    assert updated.reviewed_sections[0].content == "Edited text"
    assert updated.reviewed_sections[0].review_status == SectionReviewStatus.EDITED


def test_approve_all_marks_pending_sections():
    store = SessionStore()
    result = PipelineResult(
        session_id=uuid4(),
        intake=IntakeRecord(),
        classification=MatterClassification(
            matter_type=MatterType.CONSUMER_DEBT,
            confidence=0.9,
            routing="debt",
        ),
        draft_outline=DraftOutline(
            matter_type=MatterType.CONSUMER_DEBT,
            sections=[DraftSection(title="Next steps", content="Call legal aid")],
        ),
    )
    record = store.save_pipeline(result)
    approved = store.approve_all(record.session_id)
    assert approved.reviewed_sections[0].review_status == SectionReviewStatus.APPROVED
