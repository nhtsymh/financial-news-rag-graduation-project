from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from financial_news_rag import AppConfig, FinancialNewsRAGService  # noqa: E402


def main() -> None:
    config = AppConfig.from_env(ROOT / ".env")
    service = FinancialNewsRAGService(config)
    paths = [
        ROOT / "data" / "sample_financial_news.md",
        ROOT / "data" / "sample_company_announcement.txt",
    ]
    reports = service.index_files(paths)
    for report in reports:
        print(
            f"Indexed {report.source}: {report.chunks} chunks, "
            f"{report.relations} relations"
        )
    result = service.ask("证监会明确的资本市场监管工作主线是什么？", mode="hybrid")
    print("\nDemo answer:\n")
    print(result.answer)


if __name__ == "__main__":
    main()
