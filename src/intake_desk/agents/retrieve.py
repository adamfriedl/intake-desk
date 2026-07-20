"""Retrieval-backed answer agent with mandatory citations and grounding checks."""

from __future__ import annotations

from intake_desk.config import Settings
from intake_desk.llm import LLMClient
from intake_desk.rag.grounding import check_grounding
from intake_desk.rag.retrieval import InMemoryRetriever, PgvectorRetriever
from intake_desk.schemas.models import IntakeRecord, MatterClassification, RetrievalCitation

Retriever = InMemoryRetriever | PgvectorRetriever

RETRIEVE_SYSTEM = """You are a legal information assistant using only the provided sources.
Rules:
1. Every factual claim must cite a source id in brackets, e.g. [or-notice-types:0].
2. Only cite ids that appear in the Sources block. Never invent ids.
3. If sources are insufficient for the question (wrong topic, wrong jurisdiction, or missing
   facts), refuse clearly. Say that the sources are insufficient and what is missing.
4. Do not provide legal advice, predict case outcomes, or tell the user which form guarantees success.
5. Use plain language for lay users. Decision-support only."""


async def answer_with_citations(
    llm: LLMClient,
    retriever: Retriever,
    settings: Settings,
    user_message: str,
    intake: IntakeRecord,
    classification: MatterClassification,
) -> tuple[str, list[RetrievalCitation], bool, str | None]:
    citations = await retriever.search(
        user_message,
        matter_type=classification.matter_type,
        jurisdiction=intake.jurisdiction,
    )

    if not citations:
        return (
            "",
            [],
            True,
            "No relevant sources found in the corpus for this question.",
        )

    source_block = "\n\n".join(
        f"[{citation.chunk_id}] ({citation.source})\n{citation.quoted_span}"
        for citation in citations
    )
    prompt = (
        f"User question:\n{user_message}\n\n"
        f"Intake:\n{intake.model_dump_json()}\n\n"
        f"Sources:\n{source_block}"
    )
    answer = await llm.complete(RETRIEVE_SYSTEM, prompt)

    ok, reason = check_grounding(
        answer,
        citations,
        require_citations=settings.require_citations,
    )
    if not ok:
        return answer, citations, True, reason

    return answer, citations, False, None
