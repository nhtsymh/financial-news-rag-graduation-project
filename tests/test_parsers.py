from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from financial_news_rag.parsers import DocumentParser  # noqa: E402


class ParserTests(unittest.TestCase):
    def test_malformed_surrogate_is_replaced(self) -> None:
        dirty = "公式字符：\ud835，正文继续"
        cleaned = DocumentParser._sanitize_text(dirty)
        cleaned.encode("utf-8")
        self.assertIn("正文继续", cleaned)
        self.assertNotIn("\ud835", cleaned)


if __name__ == "__main__":
    unittest.main()
