"""In-memory advocate review session store (Phase 3 scaffold)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from intake_desk.schemas.models import (
    PipelineResult,
    ReviewedSection,
    SectionReviewStatus,
    SectionReviewUpdate,
    SessionRecord,
)
from intake_desk.triage.outcomes import compute_triage


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[UUID, SessionRecord] = {}

    def save_pipeline(self, result: PipelineResult) -> SessionRecord:
        sections: list[ReviewedSection] = []
        if result.draft_outline:
            for index, section in enumerate(result.draft_outline.sections):
                sections.append(
                    ReviewedSection(
                        index=index,
                        title=section.title,
                        content=section.content,
                        original_content=section.content,
                    )
                )
        triage, client_response, case_file = compute_triage(result)
        record = SessionRecord(
            session_id=result.session_id,
            pipeline=result,
            triage=triage,
            client_response=client_response,
            case_file=case_file,
            reviewed_sections=sections,
            updated_at=datetime.now(UTC),
        )
        self._sessions[result.session_id] = record
        return record

    def get(self, session_id: UUID) -> SessionRecord | None:
        return self._sessions.get(session_id)

    def update_section(
        self,
        session_id: UUID,
        index: int,
        update: SectionReviewUpdate,
    ) -> SessionRecord:
        record = self._require(session_id)
        if index < 0 or index >= len(record.reviewed_sections):
            raise KeyError(f"Section index {index} not found")

        section = record.reviewed_sections[index]
        if update.content is not None:
            section.content = update.content
            if update.review_status is None and update.content != section.original_content:
                section.review_status = SectionReviewStatus.EDITED
        if update.review_status is not None:
            section.review_status = update.review_status

        record.updated_at = datetime.now(UTC)
        self._sessions[session_id] = record
        return record

    def approve_all(self, session_id: UUID) -> SessionRecord:
        record = self._require(session_id)
        for section in record.reviewed_sections:
            if section.review_status == SectionReviewStatus.PENDING:
                section.review_status = SectionReviewStatus.APPROVED
        record.updated_at = datetime.now(UTC)
        self._sessions[session_id] = record
        return record

    def _require(self, session_id: UUID) -> SessionRecord:
        record = self.get(session_id)
        if record is None:
            raise KeyError(f"Session {session_id} not found")
        return record


session_store = SessionStore()
