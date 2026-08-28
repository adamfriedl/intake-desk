"""Retrieval layer — pgvector search with in-memory fallback for offline tests."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from intake_desk.config import Settings
from intake_desk.rag.chunking import TextChunk, build_chunks_from_manifest
from intake_desk.rag.embeddings import embed_texts
from intake_desk.rag.store import VectorStore
from intake_desk.schemas.models import MatterType, RetrievalCitation

log = logging.getLogger(__name__)


@dataclass
class IndexedChunk:
    chunk: TextChunk
    embedding: list[float]


class InMemoryRetriever:
    """Cosine search over an in-process index — used when Postgres is unavailable."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._index: list[IndexedChunk] = []

    async def build_index(self) -> int:
        chunks = build_chunks_from_manifest(self.settings)
        if not chunks:
            return 0

        embeddings = await embed_texts(self.settings, [chunk.text for chunk in chunks])
        self._index = [
            IndexedChunk(chunk=chunk, embedding=embedding)
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        return len(self._index)

    async def search(
        self,
        query: str,
        *,
        matter_type: MatterType | None = None,
        jurisdiction: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievalCitation]:
        if not self._index:
            await self.build_index()
        if not self._index:
            return []

        query_embedding = (await embed_texts(self.settings, [query]))[0]
        scored: list[tuple[float, IndexedChunk]] = []

        for item in self._index:
            if matter_type and matter_type.value not in item.chunk.matter_types:
                continue
            if jurisdiction and item.chunk.jurisdiction not in {
                jurisdiction,
                "oregon",
                "federal",
                "unknown",
            }:
                continue
            score = _cosine_similarity(query_embedding, item.embedding)
            scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        citations: list[RetrievalCitation] = []
        for score, item in scored[:top_k]:
            citations.append(
                RetrievalCitation(
                    chunk_id=item.chunk.chunk_id,
                    source=item.chunk.source,
                    quoted_span=item.chunk.text[:240],
                    relevance_score=round(score, 4),
                )
            )
        return citations

    def get_chunk(self, chunk_id: str) -> dict[str, str] | None:
        if not self._index:
            return None
        for item in self._index:
            if item.chunk.chunk_id == chunk_id:
                return {
                    "chunk_id": item.chunk.chunk_id,
                    "doc_id": item.chunk.doc_id,
                    "source": item.chunk.source,
                    "text": item.chunk.text,
                    "jurisdiction": item.chunk.jurisdiction,
                    "matter_types": ",".join(item.chunk.matter_types),
                    "source_url": "",
                }
        return None


class PgvectorRetriever:
    def __init__(self, settings: Settings, store: VectorStore | None = None) -> None:
        self.settings = settings
        self.store = store or VectorStore(settings)

    async def search(
        self,
        query: str,
        *,
        matter_type: MatterType | None = None,
        jurisdiction: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievalCitation]:
        query_embedding = (await embed_texts(self.settings, [query]))[0]
        return self.store.search(
            query_embedding,
            matter_type=matter_type,
            jurisdiction=jurisdiction,
            top_k=top_k,
        )

    def get_chunk(self, chunk_id: str) -> dict[str, str] | None:
        return self.store.get_chunk(chunk_id)


def get_chunk_detail(settings: Settings, chunk_id: str) -> dict[str, str] | None:
    retriever = build_retriever(settings)
    if hasattr(retriever, "get_chunk"):
        chunk = retriever.get_chunk(chunk_id)
        if chunk:
            return chunk
    for chunk in build_chunks_from_manifest(settings):
        if chunk.chunk_id == chunk_id:
            return {
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "source": chunk.source,
                "text": chunk.text,
                "jurisdiction": chunk.jurisdiction,
                "matter_types": ",".join(chunk.matter_types),
                "source_url": "",
            }
    return None


def build_retriever(settings: Settings):
    """Prefer pgvector when the database is reachable; otherwise in-memory."""
    store = VectorStore(settings)
    try:
        store.init_schema()
        if store.chunk_count() > 0:
            return PgvectorRetriever(settings, store)
    except Exception:
        log.debug("pgvector unavailable; using in-memory retriever", exc_info=True)
    return InMemoryRetriever(settings)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
