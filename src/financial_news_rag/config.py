from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    """Load a small .env file without adding a runtime dependency."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class AppConfig:
    data_dir: Path
    vector_backend: str = "sqlite"
    graph_backend: str = "sqlite"
    embedding_provider: str = "hash"
    embedding_dimensions: int = 384
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = "nomic-embed-text"
    llm_provider: str = "extractive"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "qwen2.5:7b"
    llm_timeout_seconds: int = 120
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "financial_news_chunks"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    chunk_size: int = 1024
    chunk_overlap: int = 256
    top_k: int = 5
    graph_hops: int = 2
    server_name: str = "127.0.0.1"
    server_port: int = 7860
    share: bool = False

    @classmethod
    def from_env(cls, env_path: str | Path = ".env") -> "AppConfig":
        load_dotenv(env_path)
        data_dir = Path(os.getenv("FNRAG_DATA_DIR", "./runtime_data")).resolve()
        config = cls(
            data_dir=data_dir,
            vector_backend=os.getenv("VECTOR_BACKEND", "sqlite").lower(),
            graph_backend=os.getenv("GRAPH_BACKEND", "sqlite").lower(),
            embedding_provider=os.getenv("EMBEDDING_PROVIDER", "hash").lower(),
            embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "384")),
            embedding_base_url=os.getenv("EMBEDDING_BASE_URL", ""),
            embedding_api_key=os.getenv("EMBEDDING_API_KEY", ""),
            embedding_model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            llm_provider=os.getenv("LLM_PROVIDER", "extractive").lower(),
            llm_base_url=os.getenv("LLM_BASE_URL", ""),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "qwen2.5:7b"),
            llm_timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "120")),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY", ""),
            qdrant_collection=os.getenv(
                "QDRANT_COLLECTION", "financial_news_chunks"
            ),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1024")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "256")),
            top_k=int(os.getenv("TOP_K", "5")),
            graph_hops=int(os.getenv("GRAPH_HOPS", "2")),
            server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
            server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
            share=_as_bool(os.getenv("GRADIO_SHARE"), False),
        )
        config.validate()
        config.ensure_directories()
        return config

    def validate(self) -> None:
        if self.vector_backend not in {"sqlite", "qdrant"}:
            raise ValueError("VECTOR_BACKEND must be sqlite or qdrant")
        if self.graph_backend not in {"sqlite", "neo4j"}:
            raise ValueError("GRAPH_BACKEND must be sqlite or neo4j")
        if self.embedding_provider not in {"hash", "openai"}:
            raise ValueError("EMBEDDING_PROVIDER must be hash or openai")
        if self.llm_provider not in {"extractive", "openai"}:
            raise ValueError("LLM_PROVIDER must be extractive or openai")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if self.top_k < 1:
            raise ValueError("TOP_K must be positive")

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "uploads").mkdir(parents=True, exist_ok=True)

    @property
    def catalog_db(self) -> Path:
        return self.data_dir / "catalog.sqlite3"

    @property
    def vector_db(self) -> Path:
        return self.data_dir / "vectors.sqlite3"

    @property
    def graph_db(self) -> Path:
        return self.data_dir / "graph.sqlite3"
