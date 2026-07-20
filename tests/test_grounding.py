from intake_desk.rag.grounding import check_grounding, extract_citation_ids
from intake_desk.schemas.models import RetrievalCitation


def test_extract_citation_ids():
    text = "Notice rules vary [or-notice-types:0] and deposits [or-security-deposits:1]."
    assert extract_citation_ids(text) == ["or-notice-types:0", "or-security-deposits:1"]


def test_grounding_rejects_unknown_ids():
    citations = [
        RetrievalCitation(
            chunk_id="or-notice-types:0",
            source="Notice Types",
            quoted_span="...",
            relevance_score=0.9,
        )
    ]
    ok, reason = check_grounding(
        "You can ignore the notice [fake-doc:9].",
        citations,
        require_citations=True,
    )
    assert ok is False
    assert reason and "unknown" in reason.lower()


def test_grounding_requires_citations_when_configured():
    citations = [
        RetrievalCitation(
            chunk_id="or-notice-types:0",
            source="Notice Types",
            quoted_span="...",
            relevance_score=0.9,
        )
    ]
    ok, reason = check_grounding(
        "Landlords must give proper notice before ending a tenancy.",
        citations,
        require_citations=True,
    )
    assert ok is False
    assert reason and "lacked required" in reason.lower()


def test_grounding_accepts_valid_citations():
    citations = [
        RetrievalCitation(
            chunk_id="or-notice-types:0",
            source="Notice Types",
            quoted_span="...",
            relevance_score=0.9,
        )
    ]
    ok, reason = check_grounding(
        "Notice length depends on the reason for termination [or-notice-types:0].",
        citations,
        require_citations=True,
    )
    assert ok is True
    assert reason is None
