from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.error
import urllib.request
from typing import Protocol, Sequence

from .config import AppConfig


class Embedder(Protocol):
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


FEATURE_PATTERN = re.compile(r"[\u3400-\u9fff]|[A-Za-z0-9_]+", re.UNICODE)


class HashEmbedder:
    """Deterministic local embedding suitable for offline demonstrations.

    It is not a replacement for a trained embedding model, but it gives the
    repository a zero-service fallback and keeps unit tests reproducible.
    """

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    @staticmethod
    def _features(text: str) -> list[str]:
        tokens = [item.lower() for item in FEATURE_PATTERN.findall(text)]
        bigrams = [f"{tokens[i]}::{tokens[i + 1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for feature in self._features(text):
            raw = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(raw[:8], "big") % self.dimensions
            sign = 1.0 if raw[8] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]


class OpenAICompatibleEmbedder:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dimensions: int,
        timeout: int = 120,
    ):
        if not base_url:
            raise ValueError("EMBEDDING_BASE_URL is required for openai provider")
        self.url = base_url.rstrip("/")
        if not self.url.endswith("/embeddings"):
            self.url += "/embeddings"
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.timeout = timeout

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        payload = json.dumps(
            {"model": self.model, "input": list(texts)}, ensure_ascii=False
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(self.url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Embedding service request failed: {exc}") from exc
        ordered = sorted(result["data"], key=lambda item: item.get("index", 0))
        vectors = [list(map(float, item["embedding"])) for item in ordered]
        if vectors:
            self.dimensions = len(vectors[0])
        return vectors


def build_embedder(config: AppConfig) -> Embedder:
    if config.embedding_provider == "openai":
        return OpenAICompatibleEmbedder(
            base_url=config.embedding_base_url,
            api_key=config.embedding_api_key,
            model=config.embedding_model,
            dimensions=config.embedding_dimensions,
            timeout=config.llm_timeout_seconds,
        )
    return HashEmbedder(config.embedding_dimensions)
