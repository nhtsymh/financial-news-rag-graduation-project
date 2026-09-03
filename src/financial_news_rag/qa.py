from __future__ import annotations

from typing import Sequence

from .llm import LanguageModel
from .models import AnswerBundle, Citation, RetrievalContext
from .retrieval import FinancialRetriever


SYSTEM_PROMPT = """你是金融新闻证据问答助手。必须遵守以下规则：
1. 仅依据提供的证据与图谱关系回答，不得补写材料中不存在的数字或事实。
2. 每个关键事实后使用[证据N]标注来源；图谱关系只能作为辅助，不能替代原文证据。
3. 材料不足、互相矛盾或缺少日期时，要明确说明不确定性。
4. 区分事实、推断和建议；不要给出个性化投资建议。
5. 使用简洁、专业的中文回答。"""


class FinancialQAEngine:
    def __init__(self, retriever: FinancialRetriever, llm: LanguageModel):
        self.retriever = retriever
        self.llm = llm

    @staticmethod
    def _build_prompt(context: RetrievalContext) -> str:
        evidence_parts: list[str] = []
        for index, item in enumerate(context.evidence, start=1):
            chunk = item.chunk
            evidence_parts.append(
                "\n".join(
                    [
                        f"[证据{index}]",
                        f"标题：{chunk.title}",
                        f"来源：{chunk.source}",
                        f"发布日期：{chunk.publish_time or '未提供'}",
                        f"页码：{chunk.page_number or '无'}",
                        f"内容：{chunk.content}",
                    ]
                )
            )
        graph_parts = [
            f"{item.source} --{item.relation}--> {item.target}"
            for item in context.relations[:30]
        ]
        evidence_text = "\n\n".join(evidence_parts) or "无"
        graph_text = "\n".join(graph_parts) or "无"
        return (
            f"用户问题：{context.question}\n\n"
            f"文本证据：\n{evidence_text}\n\n"
            f"图谱关系：\n{graph_text}\n\n"
            "请直接给出答案，并按规则引用证据。"
        )

    def answer(
        self,
        question: str,
        mode: str = "hybrid",
        doc_ids: Sequence[str] | None = None,
        top_k: int | None = None,
    ) -> AnswerBundle:
        if not question.strip():
            raise ValueError("问题不能为空")
        context = self.retriever.retrieve(question, mode, doc_ids, top_k)
        prompt = self._build_prompt(context)
        answer = self.llm.generate(SYSTEM_PROMPT, prompt)
        citations = [
            Citation(
                number=index,
                chunk_id=item.chunk.chunk_id,
                title=item.chunk.title,
                source=item.chunk.source,
                page_number=item.chunk.page_number,
                score=item.score,
                excerpt=(item.chunk.content[:220] + "…")
                if len(item.chunk.content) > 220
                else item.chunk.content,
            )
            for index, item in enumerate(context.evidence, start=1)
        ]
        return AnswerBundle(answer, citations, context.relations, context.mode)
