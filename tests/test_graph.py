from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from financial_news_rag.chunking import TokenChunker  # noqa: E402
from financial_news_rag.graph_store import (  # noqa: E402
    FinancialEntityExtractor,
    SQLiteGraphStore,
)
from financial_news_rag.parsers import parse_text  # noqa: E402


class GraphTests(unittest.TestCase):
    def test_directed_relation_is_searchable(self) -> None:
        document = parse_text(
            "政策新闻",
            "中国证监会发布《资本市场监管办法》，该政策影响证券业。",
        )
        chunks = TokenChunker(100, 10).split(document)
        relations = FinancialEntityExtractor().extract(chunks)
        self.assertTrue(any(item.source == "中国证监会" for item in relations))

        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteGraphStore(Path(directory) / "graph.sqlite3")
            store.add_relations(relations)
            found = store.search("证监会发布了什么政策？")
            self.assertTrue(found)
            self.assertGreater(store.count_entities(), 0)


if __name__ == "__main__":
    unittest.main()
