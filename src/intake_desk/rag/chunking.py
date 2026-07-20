"""Corpus chunking and indexing utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from intake_desk.config import Settings


@dataclass
class CorpusDocument:
    doc_id: str
    title: str
    source_url: str
    matter_types: list[str]
    jurisdiction: str
    local_path: Path | None
    notes: str = ""
    last_updated: str = ""
    license_note: str = ""
    topics: list[str] = field(default_factory=list)


@dataclass
class TextChunk:
    chunk_id: str
    doc_id: str
    source: str
    matter_types: list[str]
    jurisdiction: str
    text: str


def load_manifest(manifest_path: str | Path) -> list[CorpusDocument]:
    path = Path(manifest_path)
    if not path.exists():
        return []

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    documents: list[CorpusDocument] = []
    for entry in data.get("documents", []):
        local_path = entry.get("local_path")
        documents.append(
            CorpusDocument(
                doc_id=entry["id"],
                title=entry["title"],
                source_url=entry.get("source_url", ""),
                matter_types=entry.get("matter_types", []),
                jurisdiction=entry.get("jurisdiction", "unknown"),
                local_path=Path(local_path) if local_path else None,
                notes=entry.get("notes", ""),
                last_updated=str(entry.get("last_updated", "")),
                license_note=entry.get("license_note", ""),
                topics=entry.get("topics", []) or [],
            )
        )
    return documents


def chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    if not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - chunk_overlap, start + 1)
    return [chunk for chunk in chunks if chunk]


def build_chunks_from_manifest(settings: Settings) -> list[TextChunk]:
    documents = load_manifest(settings.corpus_manifest_path)
    chunks: list[TextChunk] = []

    for doc in documents:
        if not doc.local_path or not doc.local_path.exists():
            continue

        text = doc.local_path.read_text(encoding="utf-8")
        for index, piece in enumerate(
            chunk_text(
                text,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
        ):
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc.doc_id}:{index}",
                    doc_id=doc.doc_id,
                    source=doc.title,
                    matter_types=doc.matter_types,
                    jurisdiction=doc.jurisdiction,
                    text=piece,
                )
            )
    return chunks
