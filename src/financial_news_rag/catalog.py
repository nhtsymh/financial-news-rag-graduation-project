from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import ParsedDocument


@dataclass(slots=True)
class DocumentRecord:
    doc_id: str
    title: str
    source: str
    publish_time: str | None
    stored_path: str
    chunk_count: int
    indexed_at: str


class DocumentCatalog:
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
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    publish_time TEXT,
                    stored_path TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL
                )
                """
            )

    def upsert(self, document: ParsedDocument, stored_path: str, chunk_count: int) -> None:
        indexed_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents
                    (doc_id, title, source, publish_time, stored_path, chunk_count, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    title=excluded.title,
                    source=excluded.source,
                    publish_time=excluded.publish_time,
                    stored_path=excluded.stored_path,
                    chunk_count=excluded.chunk_count,
                    indexed_at=excluded.indexed_at
                """,
                (
                    document.doc_id,
                    document.title,
                    document.source,
                    document.publish_time,
                    stored_path,
                    chunk_count,
                    indexed_at,
                ),
            )

    def list_documents(self) -> list[DocumentRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY indexed_at DESC"
            ).fetchall()
        return [DocumentRecord(**dict(row)) for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM documents").fetchone()
        return int(row["total"])

    def get(self, doc_id: str) -> DocumentRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
            ).fetchone()
        return DocumentRecord(**dict(row)) if row else None
