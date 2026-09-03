from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from financial_news_rag.chunking import TokenChunker  # noqa: E402
from financial_news_rag.parsers import parse_text  # noqa: E402


class TokenChunkerTests(unittest.TestCase):
    def test_overlap_and_unique_ids(self) -> None:
        document = parse_text("测试文档", "资本市场监管强调防风险。" * 20)
        chunks = TokenChunker(chunk_size=30, overlap=8).split(document)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(len(chunks), len({item.chunk_id for item in chunks}))
        self.assertTrue(all(item.doc_id == document.doc_id for item in chunks))

    def test_rejects_invalid_overlap(self) -> None:
        with self.assertRaises(ValueError):
            TokenChunker(chunk_size=10, overlap=10)


if __name__ == "__main__":
    unittest.main()
