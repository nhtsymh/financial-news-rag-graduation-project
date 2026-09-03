from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ParsedPage:
    text: str
    page_number: int | None = None


@dataclass(slots=True)
class ParsedDocument:
    doc_id: str
    title: str
    source: str
    publish_time: str | None
    pages: list[ParsedPage]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    doc_id: str
    content: str
    title: str
    source: str
    page_number: int | None
    publish_time: str | None
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def payload(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "content": self.content,
            "title": self.title,
            "source": self.source,
            "page_number": self.page_number,
            "publish_time": self.publish_time,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Chunk":
        return cls(
            chunk_id=str(payload["chunk_id"]),
            doc_id=str(payload["doc_id"]),
            content=str(payload["content"]),
            title=str(payload.get("title", "")),
            source=str(payload.get("source", "")),
            page_number=payload.get("page_number"),
            publish_time=payload.get("publish_time"),
            chunk_index=int(payload.get("chunk_index", 0)),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(slots=True)
class SearchResult:
    chunk: Chunk
    score: float
    channel: str = "vector"


@dataclass(slots=True)
class Entity:
    name: str
    entity_type: str


@dataclass(slots=True)
class Relation:
    source: str
    relation: str
    target: str
    chunk_id: str
    doc_id: str
    confidence: float = 0.6
    source_type: str = "Entity"
    target_type: str = "Entity"


@dataclass(slots=True)
class RetrievalContext:
    question: str
    evidence: list[SearchResult]
    relations: list[Relation]
    mode: str


@dataclass(slots=True)
class Citation:
    number: int
    chunk_id: str
    title: str
    source: str
    page_number: int | None
    score: float
    excerpt: str


@dataclass(slots=True)
class AnswerBundle:
    answer: str
    citations: list[Citation]
    relations: list[Relation]
    mode: str
