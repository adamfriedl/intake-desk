"""Retrieval regression tests — integration tier uses live embeddings."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from intake_desk.config import Settings
from intake_desk.rag.retrieval import InMemoryRetriever, build_retriever
from intake_desk.schemas.models import MatterType

pytestmark_integration = pytest.mark.integration


def _load_queries() -> list[dict]:
    path = Path(__file__).parent / "fixtures" / "retrieval_queries.yaml"
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("queries", [])


def _has_openrouter_key() -> bool:
    return bool(Settings().openrouter_api_key or Settings().openai_api_key)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("case", _load_queries(), ids=lambda c: c["expect_doc_prefix"])
async def test_retrieval_returns_expected_doc(case: dict):
    if not _has_openrouter_key():
        pytest.skip("OPENROUTER_API_KEY or OPENAI_API_KEY required for embedding retrieval tests")

    retriever = build_retriever(Settings())
    matter = MatterType(case["matter_type"])
    citations = await retriever.search(
        case["query"],
        matter_type=matter,
        jurisdiction=case.get("jurisdiction"),
        top_k=5,
    )
    assert citations, f"No citations for query: {case['query']}"
    matched = any(
        citation.chunk_id.startswith(f"{case['expect_doc_prefix']}:")
        for citation in citations
    )
    assert matched, (
        f"Expected doc prefix {case['expect_doc_prefix']} in top-k, "
        f"got {[c.chunk_id for c in citations]}"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_in_memory_retrieval_builds_index():
    if not _has_openrouter_key():
        pytest.skip("OPENROUTER_API_KEY or OPENAI_API_KEY required for embedding retrieval tests")

    retriever = InMemoryRetriever(Settings())
    count = await retriever.build_index()
    assert count >= 100
