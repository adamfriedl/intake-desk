"""Citation grounding checks for retrieve-agent answers."""

from __future__ import annotations

import re

from intake_desk.schemas.models import RetrievalCitation

CITATION_PATTERN = re.compile(r"\[([a-z0-9][a-z0-9._:-]*)\]", re.IGNORECASE)

REFUSAL_MARKERS = (
    "insufficient",
    "cannot answer",
    "can't answer",
    "do not have enough",
    "don't have enough",
    "not enough information in the sources",
    "sources do not cover",
    "sources don't cover",
    "outside the corpus",
    "i must refuse",
    "i have to refuse",
)


def extract_citation_ids(answer: str) -> list[str]:
    return list(dict.fromkeys(CITATION_PATTERN.findall(answer)))


def looks_like_refusal(answer: str) -> bool:
    lowered = answer.lower()
    return any(marker in lowered for marker in REFUSAL_MARKERS)


def check_grounding(
    answer: str,
    citations: list[RetrievalCitation],
    *,
    require_citations: bool = True,
) -> tuple[bool, str | None]:
    """Return (ok, refusal_reason). ok=False means caller should refuse/escalate."""
    if not answer.strip():
        return False, "Empty answer from retrieval agent."

    if looks_like_refusal(answer):
        return False, "Model refused due to insufficient sources."

    allowed = {citation.chunk_id for citation in citations}
    cited = extract_citation_ids(answer)
    unknown = [cid for cid in cited if cid not in allowed]

    if unknown:
        return False, f"Answer cited unknown or non-retrieved chunk ids: {', '.join(unknown)}"

    if require_citations and citations and not cited:
        return False, "Answer lacked required bracketed citations to retrieved sources."

    return True, None
