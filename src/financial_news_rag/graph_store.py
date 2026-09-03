from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Protocol, Sequence

from .config import AppConfig
from .models import Chunk, Entity, Relation


QUESTION_TOKEN_PATTERN = re.compile(r"[\u3400-\u9fff]{2,}|[A-Za-z0-9_]{2,}")
SENTENCE_SPLIT_PATTERN = re.compile(r"[。！？!?；;\n]+")
COMPANY_PATTERN = re.compile(
    r"(?:^|[，。；：、\s])([\u3400-\u9fffA-Za-z0-9·]{2,18}?"
    r"(?:股份有限公司|有限责任公司|集团|银行|证券|保险|科技|公司))"
)
QUOTED_PATTERN = re.compile(r"[《“\"]([^》”\"]{3,32})[》”\"]")

KNOWN_INSTITUTIONS = {
    "中国证监会": "机构",
    "证监会": "机构",
    "中国人民银行": "机构",
    "央行": "机构",
    "国家金融监督管理总局": "机构",
    "金融监管总局": "机构",
    "上海证券交易所": "机构",
    "深圳证券交易所": "机构",
    "上交所": "机构",
    "深交所": "机构",
}
ENTITY_ALIASES = {
    "证监会": "中国证监会",
    "央行": "中国人民银行",
    "金融监管总局": "国家金融监督管理总局",
    "上交所": "上海证券交易所",
    "深交所": "深圳证券交易所",
}
INDUSTRY_TERMS = {
    "人工智能",
    "半导体",
    "新能源汽车",
    "新能源",
    "房地产",
    "银行业",
    "证券业",
    "保险业",
    "医药",
    "消费电子",
    "资本市场",
}
EVENT_TERMS = {
    "财报",
    "并购",
    "融资",
    "上市",
    "处罚",
    "合作",
    "投资",
    "增持",
    "减持",
    "回购",
    "分红",
    "改革",
    "监管",
}
RELATION_RULES = (
    ("属于", "属于"),
    ("任职", "任职于"),
    ("发布", "发布"),
    ("投资", "投资"),
    ("合作", "合作"),
    ("收购", "收购"),
    ("并购", "并购"),
    ("影响", "影响"),
    ("推动", "推动"),
    ("促进", "促进"),
    ("导致", "导致"),
    ("监管", "监管"),
)


def _question_terms(question: str) -> list[str]:
    terms = [token.lower() for token in QUESTION_TOKEN_PATTERN.findall(question)]
    for alias, canonical in ENTITY_ALIASES.items():
        if alias in question or canonical in question:
            terms.extend([alias.lower(), canonical.lower()])
    return list(dict.fromkeys(terms))


class GraphStore(Protocol):
    def add_relations(self, relations: Sequence[Relation]) -> None: ...

    def search(
        self,
        question: str,
        hops: int = 2,
        limit: int = 30,
        doc_ids: Sequence[str] | None = None,
    ) -> list[Relation]: ...

    def count_entities(self) -> int: ...

    def count_relations(self) -> int: ...


class FinancialEntityExtractor:
    """Transparent rule-based extractor used as the offline default.

    Production deployments can replace this class with an LLM or trained NER
    implementation without changing the indexing pipeline.
    """

    @staticmethod
    def _entities(sentence: str) -> list[Entity]:
        candidates: list[tuple[int, Entity]] = []
        for name, entity_type in sorted(
            KNOWN_INSTITUTIONS.items(), key=lambda item: len(item[0]), reverse=True
        ):
            if name in sentence:
                canonical = ENTITY_ALIASES.get(name, name)
                candidates.append((sentence.index(name), Entity(canonical, entity_type)))
        for match in COMPANY_PATTERN.finditer(sentence):
            name = match.group(1).strip()
            candidates.append((match.start(1), Entity(name, "公司")))
        for term in INDUSTRY_TERMS:
            if term in sentence:
                candidates.append((sentence.index(term), Entity(term, "行业")))
        for match in QUOTED_PATTERN.finditer(sentence):
            name = match.group(1).strip()
            entity_type = "政策" if any(
                key in name for key in ("意见", "办法", "规定", "规划", "通知")
            ) else "事件"
            candidates.append((match.start(1), Entity(name, entity_type)))
        found: dict[str, tuple[int, Entity]] = {}
        for position, entity in candidates:
            previous = found.get(entity.name)
            if previous is None or position < previous[0]:
                found[entity.name] = (position, entity)
        return [item[1] for item in sorted(found.values(), key=lambda item: item[0])]

    @staticmethod
    def _relation_name(sentence: str) -> str:
        for marker, relation in RELATION_RULES:
            if marker in sentence:
                return relation
        return "关联"

    def extract(self, chunks: Sequence[Chunk]) -> list[Relation]:
        relations: dict[tuple[str, str, str, str], Relation] = {}
        for chunk in chunks:
            for sentence in SENTENCE_SPLIT_PATTERN.split(chunk.content):
                sentence = sentence.strip()
                if not sentence:
                    continue
                entities = self._entities(sentence)
                relation_name = self._relation_name(sentence)
                if len(entities) >= 2:
                    for left, right in zip(entities, entities[1:]):
                        relation = Relation(
                            source=left.name,
                            relation=relation_name,
                            target=right.name,
                            chunk_id=chunk.chunk_id,
                            doc_id=chunk.doc_id,
                            confidence=0.72 if relation_name != "关联" else 0.55,
                            source_type=left.entity_type,
                            target_type=right.entity_type,
                        )
                        relations[(left.name, relation_name, right.name, chunk.chunk_id)] = relation
                elif len(entities) == 1:
                    entity = entities[0]
                    event = next((term for term in EVENT_TERMS if term in sentence), None)
                    if event and event != entity.name:
                        relation = Relation(
                            source=entity.name,
                            relation=relation_name,
                            target=event,
                            chunk_id=chunk.chunk_id,
                            doc_id=chunk.doc_id,
                            confidence=0.62,
                            source_type=entity.entity_type,
                            target_type="事件",
                        )
                        relations[(entity.name, relation_name, event, chunk.chunk_id)] = relation
                for entity in entities:
                    source_relation = Relation(
                        source=entity.name,
                        relation="来源于",
                        target=chunk.title,
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        confidence=1.0,
                        source_type=entity.entity_type,
                        target_type="文档",
                    )
                    key = (entity.name, "来源于", chunk.title, chunk.chunk_id)
                    relations[key] = source_relation
        return list(relations.values())


class SQLiteGraphStore:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    PRIMARY KEY(name, entity_type)
                );
                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    target TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source_type TEXT NOT NULL,
                    target_type TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source);
                CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target);
                CREATE INDEX IF NOT EXISTS idx_relations_doc ON relations(doc_id);
                """
            )

    @staticmethod
    def _relation_id(relation: Relation) -> str:
        value = (
            f"{relation.source}|{relation.relation}|{relation.target}|"
            f"{relation.chunk_id}|{relation.doc_id}"
        )
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]

    def add_relations(self, relations: Sequence[Relation]) -> None:
        with self._connect() as connection:
            for item in relations:
                connection.execute(
                    "INSERT OR IGNORE INTO entities(name, entity_type) VALUES (?, ?)",
                    (item.source, item.source_type),
                )
                connection.execute(
                    "INSERT OR IGNORE INTO entities(name, entity_type) VALUES (?, ?)",
                    (item.target, item.target_type),
                )
                connection.execute(
                    """
                    INSERT INTO relations
                        (id, source, relation, target, chunk_id, doc_id,
                         confidence, source_type, target_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET confidence=excluded.confidence
                    """,
                    (
                        self._relation_id(item),
                        item.source,
                        item.relation,
                        item.target,
                        item.chunk_id,
                        item.doc_id,
                        item.confidence,
                        item.source_type,
                        item.target_type,
                    ),
                )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Relation:
        return Relation(
            source=row["source"],
            relation=row["relation"],
            target=row["target"],
            chunk_id=row["chunk_id"],
            doc_id=row["doc_id"],
            confidence=float(row["confidence"]),
            source_type=row["source_type"],
            target_type=row["target_type"],
        )

    def search(
        self,
        question: str,
        hops: int = 2,
        limit: int = 30,
        doc_ids: Sequence[str] | None = None,
    ) -> list[Relation]:
        tokens = _question_terms(question)
        if not tokens:
            return []
        doc_sql = ""
        doc_parameters: list[str] = []
        if doc_ids:
            doc_sql = f" AND doc_id IN ({','.join('?' for _ in doc_ids)})"
            doc_parameters = list(doc_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM relations WHERE 1=1 {doc_sql}", doc_parameters
            ).fetchall()

        all_relations = [self._from_row(row) for row in rows]
        seeds = {
            endpoint
            for relation in all_relations
            for endpoint in (relation.source, relation.target)
            if endpoint in question
            or any(token in endpoint.lower() or endpoint.lower() in token for token in tokens)
        }
        if not seeds:
            return [
                relation
                for relation in all_relations
                if any(
                    token in relation.relation.lower()
                    or token in relation.source.lower()
                    or token in relation.target.lower()
                    for token in tokens
                )
            ][:limit]

        selected: list[Relation] = []
        seen_relations: set[tuple[str, str, str, str]] = set()
        frontier = set(seeds)
        visited = set(seeds)
        for _ in range(max(1, hops)):
            next_frontier: set[str] = set()
            for relation in all_relations:
                if relation.source not in frontier and relation.target not in frontier:
                    continue
                key = (
                    relation.source,
                    relation.relation,
                    relation.target,
                    relation.chunk_id,
                )
                if key not in seen_relations:
                    selected.append(relation)
                    seen_relations.add(key)
                next_frontier.update({relation.source, relation.target})
                if len(selected) >= limit:
                    return selected
            frontier = next_frontier - visited
            visited.update(next_frontier)
            if not frontier:
                break
        return selected

    def count_entities(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM entities").fetchone()
        return int(row["total"])

    def count_relations(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM relations").fetchone()
        return int(row["total"])


class Neo4jGraphStore:
    def __init__(self, uri: str, user: str, password: str):
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise RuntimeError("Neo4j backend requires the neo4j Python driver") from exc
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver.verify_connectivity()
        with self.driver.session() as session:
            session.run(
                "CREATE CONSTRAINT fnrag_entity_id IF NOT EXISTS "
                "FOR (e:FinancialEntity) REQUIRE e.entity_id IS UNIQUE"
            )

    @staticmethod
    def _entity_id(name: str, entity_type: str) -> str:
        return hashlib.sha256(f"{entity_type}:{name}".encode("utf-8")).hexdigest()

    def add_relations(self, relations: Sequence[Relation]) -> None:
        query = """
        MERGE (s:FinancialEntity {entity_id: $source_id})
          SET s.name = $source, s.type = $source_type
        MERGE (t:FinancialEntity {entity_id: $target_id})
          SET t.name = $target, t.type = $target_type
        MERGE (s)-[r:RELATES {
          relation: $relation, chunk_id: $chunk_id, doc_id: $doc_id
        }]->(t)
          SET r.confidence = $confidence
        """
        with self.driver.session() as session:
            for item in relations:
                session.run(
                    query,
                    source_id=self._entity_id(item.source, item.source_type),
                    source=item.source,
                    source_type=item.source_type,
                    target_id=self._entity_id(item.target, item.target_type),
                    target=item.target,
                    target_type=item.target_type,
                    relation=item.relation,
                    chunk_id=item.chunk_id,
                    doc_id=item.doc_id,
                    confidence=item.confidence,
                )

    def search(
        self,
        question: str,
        hops: int = 2,
        limit: int = 30,
        doc_ids: Sequence[str] | None = None,
    ) -> list[Relation]:
        safe_hops = min(max(int(hops), 1), 4)
        tokens = _question_terms(question)
        query = f"""
        MATCH p=(seed:FinancialEntity)-[:RELATES*1..{safe_hops}]-(other)
        WHERE ($question CONTAINS seed.name
               OR any(token IN $tokens WHERE toLower(seed.name) CONTAINS token))
        UNWIND relationships(p) AS rel
        WITH DISTINCT startNode(rel) AS s, rel, endNode(rel) AS t
        WHERE size($doc_ids) = 0 OR rel.doc_id IN $doc_ids
        RETURN s.name AS source, s.type AS source_type,
               rel.relation AS relation, t.name AS target,
               t.type AS target_type, rel.chunk_id AS chunk_id,
               rel.doc_id AS doc_id, rel.confidence AS confidence
        LIMIT $limit
        """
        with self.driver.session() as session:
            rows = session.run(
                query,
                question=question,
                tokens=tokens,
                doc_ids=list(doc_ids or []),
                limit=limit,
            )
            return [Relation(**dict(row)) for row in rows]

    def count_entities(self) -> int:
        with self.driver.session() as session:
            row = session.run("MATCH (e:FinancialEntity) RETURN count(e) AS total").single()
        return int(row["total"])

    def count_relations(self) -> int:
        with self.driver.session() as session:
            row = session.run("MATCH ()-[r:RELATES]->() RETURN count(r) AS total").single()
        return int(row["total"])

    def close(self) -> None:
        self.driver.close()


def build_graph_store(config: AppConfig) -> GraphStore:
    if config.graph_backend == "neo4j":
        return Neo4jGraphStore(
            config.neo4j_uri,
            config.neo4j_user,
            config.neo4j_password,
        )
    return SQLiteGraphStore(config.graph_db)
