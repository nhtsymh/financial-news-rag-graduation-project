from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .catalog import DocumentCatalog
from .chunking import TokenChunker
from .embeddings import Embedder
from .graph_store import FinancialEntityExtractor, GraphStore
from .parsers import DocumentParser
from .vector_store import VectorStore


@dataclass(slots=True)
class IndexReport:
    doc_id: str
    title: str
    source: str
    chunks: int
    relations: int
    stored_path: str


class FinancialIndexer:
    def __init__(
        self,
        parser: DocumentParser,
        chunker: TokenChunker,
        embedder: Embedder,
        vector_store: VectorStore,
        graph_store: GraphStore,
        catalog: DocumentCatalog,
        upload_dir: str | Path,
        extractor: FinancialEntityExtractor | None = None,
    ):
        self.parser = parser
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.catalog = catalog
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = extractor or FinancialEntityExtractor()

    def index_paths(self, paths: Sequence[str | Path]) -> list[IndexReport]:
        reports: list[IndexReport] = []
        for path_value in paths:
            source_path = Path(path_value)
            document = self.parser.parse(source_path)
            stored_path = self.upload_dir / f"{document.doc_id}{source_path.suffix.lower()}"
            if source_path.resolve() != stored_path.resolve():
                shutil.copy2(source_path, stored_path)
            document.metadata["stored_path"] = str(stored_path)

            chunks = self.chunker.split(document)
            if not chunks:
                raise ValueError(f"No searchable text found in {source_path.name}")
            vectors = self.embedder.embed([chunk.content for chunk in chunks])
            self.vector_store.upsert(chunks, vectors)

            relations = self.extractor.extract(chunks)
            self.graph_store.add_relations(relations)
            self.catalog.upsert(document, str(stored_path), len(chunks))
            reports.append(
                IndexReport(
                    doc_id=document.doc_id,
                    title=document.title,
                    source=document.source,
                    chunks=len(chunks),
                    relations=len(relations),
                    stored_path=str(stored_path),
                )
            )
        return reports
