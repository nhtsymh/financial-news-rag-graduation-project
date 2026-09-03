from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from financial_news_rag import AppConfig, FinancialNewsRAGService  # noqa: E402


class EndToEndTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        data_dir = Path(self.temporary.name) / "runtime"
        self.config = AppConfig(
            data_dir=data_dir,
            chunk_size=80,
            chunk_overlap=20,
            top_k=3,
            embedding_dimensions=192,
        )
        self.config.validate()
        self.config.ensure_directories()
        self.service = FinancialNewsRAGService(self.config)
        self.news = Path(self.temporary.name) / "news.md"
        self.news.write_text(
            """# 资本市场监管工作\n"
            "发布时间：2026-01-15\n"
            "中国证监会发布《资本市场监管工作安排》，"
            "明确强监管、防风险、促进高质量发展的工作主线。"
            "该政策影响证券业合规管理。\n""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_index_and_hybrid_answer(self) -> None:
        reports = self.service.index_files([self.news])
        self.assertEqual(len(reports), 1)
        self.assertGreater(reports[0].chunks, 0)
        self.assertGreater(reports[0].relations, 0)

        result = self.service.ask("证监会的监管工作主线是什么？", mode="hybrid")
        self.assertIn("证据", result.answer)
        self.assertTrue(result.citations)
        self.assertTrue(result.relations)
        self.assertEqual(self.service.stats()["documents"], 1)

    def test_document_scope(self) -> None:
        report = self.service.index_files([self.news])[0]
        result = self.service.ask(
            "资本市场监管",
            mode="vector",
            doc_ids=[report.doc_id],
        )
        self.assertTrue(result.citations)
        self.assertTrue(all(item.chunk_id for item in result.citations))


if __name__ == "__main__":
    unittest.main()
