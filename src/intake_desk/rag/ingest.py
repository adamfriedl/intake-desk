"""Ingest corpus chunks + embeddings into Postgres/pgvector."""

from __future__ import annotations

import argparse
import asyncio
import sys

from intake_desk.config import Settings, get_settings
from intake_desk.rag.chunking import build_chunks_from_manifest, load_manifest
from intake_desk.rag.embeddings import embed_texts
from intake_desk.rag.store import VectorStore


async def ingest(settings: Settings) -> int:
    documents = load_manifest(settings.corpus_manifest_path)
    chunks = build_chunks_from_manifest(settings)
    if not chunks:
        print("No chunks built from manifest — check corpus/raw paths.", file=sys.stderr)
        return 1

    print(f"Embedding {len(chunks)} chunks from {len(documents)} documents...")
    embeddings = await embed_texts(settings, [chunk.text for chunk in chunks])

    store = VectorStore(settings)
    store.init_schema()

    doc_rows = [
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "source_url": doc.source_url,
            "jurisdiction": doc.jurisdiction,
            "matter_types": ",".join(doc.matter_types),
            "topics": ",".join(doc.topics),
            "last_updated": doc.last_updated,
        }
        for doc in documents
    ]
    count = store.replace_corpus(
        documents=doc_rows,
        chunks=list(zip(chunks, embeddings, strict=True)),
    )
    print(f"Ingested {count} chunks into {settings.database_url}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Intake Desk corpus into pgvector")
    parser.parse_args()
    settings = get_settings()
    raise SystemExit(asyncio.run(ingest(settings)))


if __name__ == "__main__":
    main()
