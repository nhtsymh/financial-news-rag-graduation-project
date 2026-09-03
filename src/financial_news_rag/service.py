from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .catalog import DocumentCatalog, DocumentRecord
from .chunking import TokenChunker
from .config import AppConfig
from .embeddings import build_embedder
from .graph_store import build_graph_store
from .indexing import FinancialIndexer, IndexReport
from .llm import build_llm
from .models import AnswerBundle
from .parsers import DocumentParser
from .qa import FinancialQAEngine
from .retrieval import FinancialRetriever
from .vector_store import build_vector_store


class FinancialNewsRAGService:
    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig.from_env()
        self.config.ensure_directories()
        self.embedder = build_embedder(self.config)
        self.vector_store = build_vector_store(self.config, self.embedder.dimensions)
        self.graph_store = build_graph_store(self.config)
        self.catalog = DocumentCatalog(self.config.catalog_db)
        self.indexer = FinancialIndexer(
            parser=DocumentParser(),
            chunker=TokenChunker(self.config.chunk_size, self.config.chunk_overlap),
            embedder=self.embedder,
            vector_store=self.vector_store,
            graph_store=self.graph_store,
            catalog=self.catalog,
            upload_dir=self.config.data_dir / "uploads",
        )
        self.retriever = FinancialRetriever(
            self.embedder,
            self.vector_store,
            self.graph_store,
            self.config.top_k,
            self.config.graph_hops,
        )
        self.engine = FinancialQAEngine(self.retriever, build_llm(self.config))

    def index_files(self, paths: Sequence[str | Path]) -> list[IndexReport]:
        return self.indexer.index_paths(paths)

    def ask(
        self,
        question: str,
        mode: str = "hybrid",
        doc_ids: Sequence[str] | None = None,
        top_k: int | None = None,
    ) -> AnswerBundle:
        return self.engine.answer(question, mode, doc_ids, top_k)

    def documents(self) -> list[DocumentRecord]:
        return self.catalog.list_documents()

    def stats(self) -> dict[str, int | str]:
        return {
            "documents": self.catalog.count(),
            "chunks": self.vector_store.count(),
            "entities": self.graph_store.count_entities(),
            "relations": self.graph_store.count_relations(),
            "vector_backend": self.config.vector_backend,
            "graph_backend": self.config.graph_backend,
        }
