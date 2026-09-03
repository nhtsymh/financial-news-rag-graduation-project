from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Sequence

from .embeddings import Embedder
from .graph_store import GraphStore
from .models import Relation, RetrievalContext, SearchResult
from .vector_store import VectorStore


VALID_MODES = {"vector", "graph", "hybrid"}


def _date_bonus(publish_time: str | None) -> float:
    if not publish_time:
        return 0.0
    normalized = publish_time.replace("年", "-").replace("月", "-").replace("日", "")
    normalized = normalized.replace("/", "-").replace(".", "-")
    try:
        published = datetime.strptime(normalized, "%Y-%m-%d")
    except ValueError:
        return 0.0
    age_days = max((datetime.now() - published).days, 0)
    return 0.03 / (1.0 + age_days / 365.0)


class FinancialRetriever:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        graph_store: GraphStore,
        top_k: int = 5,
        graph_hops: int = 2,
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.top_k = top_k
        self.graph_hops = graph_hops

    def retrieve(
        self,
        question: str,
        mode: str = "hybrid",
        doc_ids: Sequence[str] | None = None,
        top_k: int | None = None,
    ) -> RetrievalContext:
        mode = mode.lower()
        if mode not in VALID_MODES:
            raise ValueError(f"Unknown retrieval mode: {mode}")
        limit = top_k or self.top_k
        query_vector = self.embedder.embed([question])[0]

        vector_results: list[SearchResult] = []
        if mode in {"vector", "hybrid"}:
            vector_results = self.vector_store.search(
                query_vector,
                top_k=limit * (2 if mode == "hybrid" else 1),
                doc_ids=doc_ids,
            )
            for result in vector_results:
                result.score += _date_bonus(result.chunk.publish_time)

        relations: list[Relation] = []
        graph_results: list[SearchResult] = []
        if mode in {"graph", "hybrid"}:
            relations = self.graph_store.search(
                question,
                hops=self.graph_hops,
                limit=max(30, limit * 4),
                doc_ids=doc_ids,
            )
            ordered_chunk_ids = list(dict.fromkeys(item.chunk_id for item in relations))
            chunks = self.vector_store.get_chunks(ordered_chunk_ids)
            confidence_by_chunk: dict[str, float] = defaultdict(float)
            for relation in relations:
                confidence_by_chunk[relation.chunk_id] = max(
                    confidence_by_chunk[relation.chunk_id], relation.confidence
                )
            graph_results = [
                SearchResult(
                    chunk=chunk,
                    score=confidence_by_chunk[chunk.chunk_id],
                    channel="graph",
                )
                for chunk in chunks
            ]

        if mode == "vector":
            evidence = vector_results[:limit]
        elif mode == "graph":
            evidence = sorted(graph_results, key=lambda item: item.score, reverse=True)[:limit]
        else:
            evidence = self._reciprocal_rank_fusion(vector_results, graph_results, limit)

        return RetrievalContext(
            question=question,
            evidence=evidence,
            relations=relations,
            mode=mode,
        )

    @staticmethod
    def _reciprocal_rank_fusion(
        vector_results: Sequence[SearchResult],
        graph_results: Sequence[SearchResult],
        limit: int,
        constant: int = 60,
    ) -> list[SearchResult]:
        by_id: dict[str, SearchResult] = {}
        scores: dict[str, float] = defaultdict(float)
        channels: dict[str, set[str]] = defaultdict(set)
        for channel, results, weight in (
            ("vector", vector_results, 1.0),
            ("graph", graph_results, 0.9),
        ):
            for rank, result in enumerate(results, start=1):
                chunk_id = result.chunk.chunk_id
                by_id.setdefault(chunk_id, result)
                scores[chunk_id] += weight / (constant + rank)
                channels[chunk_id].add(channel)
        ranked = sorted(scores, key=scores.get, reverse=True)[:limit]
        return [
            SearchResult(
                chunk=by_id[chunk_id].chunk,
                score=scores[chunk_id],
                channel="+".join(sorted(channels[chunk_id])),
            )
            for chunk_id in ranked
        ]
