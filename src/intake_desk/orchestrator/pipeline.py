"""Multi-step intake pipeline orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from intake_desk.agents.classify import classify_matter
from intake_desk.agents.draft import build_draft_outline
from intake_desk.agents.intake import extract_intake
from intake_desk.agents.retrieve import answer_with_citations
from intake_desk.config import Settings
from intake_desk.llm import LLMClient
from intake_desk.rag.retrieval import build_retriever
from intake_desk.schemas.models import PipelineResult, PipelineStepLog


class IntakePipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm = LLMClient(settings)
        self.retriever = build_retriever(settings)

    async def run(self, user_message: str, *, include_draft: bool = True) -> PipelineResult:
        session_id = uuid4()
        audit_log: list[PipelineStepLog] = []

        intake = await self._run_step(
            audit_log,
            "intake",
            lambda: extract_intake(self.llm, user_message),
        )
        intake.session_id = session_id

        classification = await self._run_step(
            audit_log,
            "classify",
            lambda: classify_matter(self.llm, self.settings, user_message, intake),
        )

        answer, citations, refused, refusal_reason = await self._run_step(
            audit_log,
            "retrieve",
            lambda: answer_with_citations(
                self.llm,
                self.retriever,
                self.settings,
                user_message,
                intake,
                classification,
            ),
        )

        draft_outline = None
        if include_draft and answer and not refused:
            draft_outline = await self._run_step(
                audit_log,
                "draft",
                lambda: build_draft_outline(self.llm, classification, answer),
            )

        return PipelineResult(
            session_id=session_id,
            intake=intake,
            classification=classification,
            citations=citations,
            draft_outline=draft_outline,
            answer=answer or None,
            refused=refused,
            refusal_reason=refusal_reason,
            audit_log=audit_log,
        )

    async def _run_step(self, audit_log: list[PipelineStepLog], step: str, fn):
        log = PipelineStepLog(step=step, started_at=datetime.now(UTC), status="running")
        audit_log.append(log)
        try:
            result = await fn()
            log.status = "completed"
            log.completed_at = datetime.now(UTC)
            return result
        except Exception as exc:
            log.status = "failed"
            log.completed_at = datetime.now(UTC)
            log.detail = str(exc)
            raise
