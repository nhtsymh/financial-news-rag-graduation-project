from __future__ import annotations

import statistics
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from financial_news_rag import AppConfig, FinancialNewsRAGService  # noqa: E402


QUESTIONS = [
    "证监会明确的资本市场监管工作主线是什么？",
    "监管政策如何影响证券业？",
    "星河科技的研发投入用于哪些方向？",
]


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        config = AppConfig(data_dir=Path(directory), chunk_size=160, chunk_overlap=40)
        config.ensure_directories()
        service = FinancialNewsRAGService(config)
        service.index_files(
            [
                ROOT / "data" / "sample_financial_news.md",
                ROOT / "data" / "sample_company_announcement.txt",
            ]
        )
        print("mode,average_seconds,citations")
        for mode in ("vector", "graph", "hybrid"):
            durations: list[float] = []
            citation_counts: list[int] = []
            for question in QUESTIONS:
                start = time.perf_counter()
                result = service.ask(question, mode=mode)
                durations.append(time.perf_counter() - start)
                citation_counts.append(len(result.citations))
            print(
                f"{mode},{statistics.mean(durations):.6f},"
                f"{statistics.mean(citation_counts):.2f}"
            )


if __name__ == "__main__":
    main()
