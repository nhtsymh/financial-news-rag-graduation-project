from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Protocol

from .config import AppConfig


class LanguageModel(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class OpenAICompatibleLLM:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 120,
    ):
        if not base_url:
            raise ValueError("LLM_BASE_URL is required for openai provider")
        self.url = base_url.rstrip("/")
        if not self.url.endswith("/chat/completions"):
            self.url += "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "stream": False,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(self.url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"LLM service request failed: {exc}") from exc
        return str(result["choices"][0]["message"]["content"]).strip()


class ExtractiveLLM:
    """Offline fallback that creates an evidence-only answer."""

    EVIDENCE_PATTERN = re.compile(
        r"\[证据(\d+)\].*?\n内容：(.*?)(?=\n\[证据\d+\]|\n\n图谱关系：|\Z)",
        re.DOTALL,
    )

    @staticmethod
    def _first_sentence(text: str, limit: int = 180) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        sentence = re.split(r"(?<=[。！？!?])", compact, maxsplit=1)[0]
        if len(sentence) > limit:
            sentence = sentence[:limit].rstrip() + "…"
        return sentence

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        del system_prompt
        matches = self.EVIDENCE_PATTERN.findall(user_prompt)
        if not matches:
            return "当前知识库没有检索到足够证据，暂时无法给出可靠结论。"
        lines = ["根据当前知识库，可以得到以下信息："]
        for number, content in matches[:3]:
            sentence = self._first_sentence(content)
            if sentence:
                lines.append(f"- {sentence}[证据{number}]")
        lines.append("\n以上结论仅依据已索引材料，请结合原文发布日期和完整上下文核验。")
        return "\n".join(lines)


def build_llm(config: AppConfig) -> LanguageModel:
    if config.llm_provider == "openai":
        return OpenAICompatibleLLM(
            config.llm_base_url,
            config.llm_api_key,
            config.llm_model,
            config.llm_timeout_seconds,
        )
    return ExtractiveLLM()
