from __future__ import annotations

import json
import math
import sqlite3
import uuid
from pathlib import Path
from typing import Protocol, Sequence

from .config import AppConfig
from .models import Chunk, SearchResult


class VectorStore(Protocol):
    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None: ...

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int,
        doc_ids: Sequence[str] | None = None,
    ) -> list[SearchResult]: ...

    def get_chunks(self, chunk_ids: Sequence[str]) -> list[Chunk]: ...

    def count(self) -> int: ...


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


class SQLiteVectorStore:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vectors (
                    chunk_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    embedding TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_vectors_doc_id ON vectors(doc_id)"
            )

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        rows = [
            (
                chunk.chunk_id,
                chunk.doc_id,
                json.dumps(chunk.payload(), ensure_ascii=False),
                json.dumps(list(map(float, vector))),
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO vectors (chunk_id, doc_id, payload, embedding)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    doc_id=excluded.doc_id,
                    payload=excluded.payload,
                    embedding=excluded.embedding
                """,
                rows,
            )

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int,
        doc_ids: Sequence[str] | None = None,
    ) -> list[SearchResult]:
        sql = "SELECT payload, embedding FROM vectors"
        parameters: list[str] = []
        if doc_ids:
            placeholders = ",".join("?" for _ in doc_ids)
            sql += f" WHERE doc_id IN ({placeholders})"
            parameters.extend(doc_ids)
        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        scored = [
            SearchResult(
                chunk=Chunk.from_payload(json.loads(row["payload"])),
                score=cosine_similarity(query_vector, json.loads(row["embedding"])),
            )
            for row in rows
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def get_chunks(self, chunk_ids: Sequence[str]) -> list[Chunk]:
        if not chunk_ids:
            return []
        placeholders = ",".join("?" for _ in chunk_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT payload FROM vectors WHERE chunk_id IN ({placeholders})",
                list(chunk_ids),
            ).fetchall()
        chunks = {item.chunk_id: item for item in (Chunk.from_payload(json.loads(row["payload"])) for row in rows)}
        return [chunks[item] for item in chunk_ids if item in chunks]

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM vectors").fetchone()
        return int(row["total"])


class QdrantVectorStore:
    """Qdrant adapter used when VECTOR_BACKEND=qdrant."""

    def __init__(self, url: str, api_key: str, collection: str, dimensions: int):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError as exc:
            raise RuntimeError("Qdrant backend requires qdrant-client") from exc
        self.client = QdrantClient(url=url, api_key=api_key or None)
        self.collection = collection
        if not self.client.collection_exists(collection):
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE),
            )

    @staticmethod
    def _point_id(chunk_id: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"fnrag:{chunk_id}"))

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=self._point_id(chunk.chunk_id),
                vector=list(map(float, vector)),
                payload=chunk.payload(),
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        if points:
            self.client.upsert(collection_name=self.collection, points=points, wait=True)

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int,
        doc_ids: Sequence[str] | None = None,
    ) -> list[SearchResult]:
        from qdrant_client.models import FieldCondition, Filter, MatchAny

        query_filter = None
        if doc_ids:
            query_filter = Filter(
                must=[FieldCondition(key="doc_id", match=MatchAny(any=list(doc_ids)))]
            )
        response = self.client.query_points(
            collection_name=self.collection,
            query=list(map(float, query_vector)),
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        return [
            SearchResult(
                chunk=Chunk.from_payload(dict(point.payload or {})),
                score=float(point.score),
            )
            for point in response.points
        ]

    def get_chunks(self, chunk_ids: Sequence[str]) -> list[Chunk]:
        if not chunk_ids:
            return []
        from qdrant_client.models import FieldCondition, Filter, MatchAny

        points, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="chunk_id", match=MatchAny(any=list(chunk_ids)))]
            ),
            limit=max(len(chunk_ids), 1),
            with_payload=True,
            with_vectors=False,
        )
        chunks = {
            str(point.payload["chunk_id"]): Chunk.from_payload(dict(point.payload))
            for point in points
            if point.payload
        }
        return [chunks[item] for item in chunk_ids if item in chunks]

    def count(self) -> int:
        result = self.client.count(collection_name=self.collection, exact=True)
        return int(result.count)


def build_vector_store(config: AppConfig, dimensions: int) -> VectorStore:
    if config.vector_backend == "qdrant":
        return QdrantVectorStore(
            config.qdrant_url,
            config.qdrant_api_key,
            config.qdrant_collection,
            dimensions,
        )
    return SQLiteVectorStore(config.vector_db)
