"""Postgres/pgvector persistence for corpus chunks."""

from __future__ import annotations

from collections.abc import Sequence

from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text, create_engine, func, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from intake_desk.config import Settings
from intake_desk.rag.chunking import TextChunk
from intake_desk.schemas.models import MatterType, RetrievalCitation


class Base(DeclarativeBase):
    pass


class DocumentRow(Base):
    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    source_url: Mapped[str] = mapped_column(String(1024), default="")
    jurisdiction: Mapped[str] = mapped_column(String(64), default="unknown")
    matter_types: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    topics: Mapped[str] = mapped_column(Text, default="")
    last_updated: Mapped[str] = mapped_column(String(32), default="")


class ChunkRow(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(128), index=True)
    source: Mapped[str] = mapped_column(String(512))
    matter_types: Mapped[str] = mapped_column(Text, default="")
    jurisdiction: Mapped[str] = mapped_column(String(64), default="unknown")
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    embedding_dim: Mapped[int] = mapped_column(Integer, default=1536)


def _matter_filter_value(matter_type: MatterType | None) -> str | None:
    return matter_type.value if matter_type else None


class VectorStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.engine = create_engine(settings.database_url, pool_pre_ping=True)

    def init_schema(self) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(self.engine)

    def replace_corpus(
        self,
        *,
        documents: Sequence[dict[str, str]],
        chunks: Sequence[tuple[TextChunk, list[float]]],
    ) -> int:
        """Idempotent full replace of documents + chunks for the current corpus."""
        with Session(self.engine) as session:
            session.execute(text("DELETE FROM chunks"))
            session.execute(text("DELETE FROM documents"))
            for doc in documents:
                session.add(
                    DocumentRow(
                        doc_id=doc["doc_id"],
                        title=doc["title"],
                        source_url=doc.get("source_url", ""),
                        jurisdiction=doc.get("jurisdiction", "unknown"),
                        matter_types=doc.get("matter_types", ""),
                        topics=doc.get("topics", ""),
                        last_updated=doc.get("last_updated", ""),
                    )
                )
            for chunk, embedding in chunks:
                session.add(
                    ChunkRow(
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        source=chunk.source,
                        matter_types=",".join(chunk.matter_types),
                        jurisdiction=chunk.jurisdiction,
                        text=chunk.text,
                        embedding=embedding,
                        embedding_dim=len(embedding),
                    )
                )
            session.commit()
            return len(chunks)

    def search(
        self,
        query_embedding: list[float],
        *,
        matter_type: MatterType | None = None,
        jurisdiction: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievalCitation]:
        matter = _matter_filter_value(matter_type)
        # Cosine distance via pgvector: smaller is better; convert to similarity.
        distance = ChunkRow.embedding.cosine_distance(query_embedding).label("distance")
        stmt = select(ChunkRow, distance)

        if matter:
            stmt = stmt.where(ChunkRow.matter_types.contains(matter))
        if jurisdiction:
            stmt = stmt.where(
                ChunkRow.jurisdiction.in_([jurisdiction, "oregon", "federal", "unknown"])
            )

        stmt = stmt.order_by(distance).limit(top_k)

        citations: list[RetrievalCitation] = []
        with Session(self.engine) as session:
            rows = session.execute(stmt).all()
            for chunk_row, dist in rows:
                similarity = max(0.0, 1.0 - float(dist))
                citations.append(
                    RetrievalCitation(
                        chunk_id=chunk_row.chunk_id,
                        source=chunk_row.source,
                        quoted_span=chunk_row.text[:240],
                        relevance_score=round(similarity, 4),
                    )
                )
        return citations

    def chunk_count(self) -> int:
        with Session(self.engine) as session:
            return int(session.scalar(select(func.count()).select_from(ChunkRow)) or 0)

    def get_chunk(self, chunk_id: str) -> dict[str, str] | None:
        with Session(self.engine) as session:
            row = session.get(ChunkRow, chunk_id)
            if not row:
                return None
            doc = session.get(DocumentRow, row.doc_id)
            return {
                "chunk_id": row.chunk_id,
                "doc_id": row.doc_id,
                "source": row.source,
                "text": row.text,
                "jurisdiction": row.jurisdiction,
                "matter_types": row.matter_types,
                "source_url": doc.source_url if doc else "",
            }
