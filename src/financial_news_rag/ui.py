from __future__ import annotations

from pathlib import Path
from typing import Any

from .service import FinancialNewsRAGService
from .visualization import build_relation_figure


CUSTOM_CSS = """
.gradio-container { max-width: 1440px !important; }
.hero {
  padding: 26px 30px;
  border-radius: 18px;
  color: white;
  background: linear-gradient(120deg, #0f172a 0%, #1d4ed8 58%, #0891b2 100%);
  box-shadow: 0 14px 35px rgba(15, 23, 42, 0.16);
  margin-bottom: 18px;
}
.hero h1 { margin: 0 0 6px 0; font-size: 34px; }
.hero p { margin: 0; opacity: 0.92; }
.metric-card { border: 1px solid #dbeafe; border-radius: 12px; padding: 12px; }
.footer-note { color: #64748b; font-size: 13px; }
"""


def _file_paths(files: Any) -> list[str]:
    if not files:
        return []
    values = files if isinstance(files, list) else [files]
    paths: list[str] = []
    for value in values:
        if isinstance(value, (str, Path)):
            paths.append(str(value))
        elif getattr(value, "path", None):
            paths.append(str(value.path))
        elif getattr(value, "name", None):
            paths.append(str(value.name))
    return paths


def build_app(service: FinancialNewsRAGService | None = None):
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError(
            "Gradio is not installed. Run: pip install -e ."
        ) from exc

    service = service or FinancialNewsRAGService()

    def document_rows() -> list[list[Any]]:
        return [
            [
                item.doc_id,
                item.title,
                item.source,
                item.publish_time or "",
                item.chunk_count,
                item.indexed_at,
            ]
            for item in service.documents()
        ]

    def document_choices() -> list[tuple[str, str]]:
        return [
            (f"{item.title} · {item.doc_id[:8]}", item.doc_id)
            for item in service.documents()
        ]

    def stats_markdown() -> str:
        stats = service.stats()
        return (
            "### 知识库状态\n"
            f"文档 **{stats['documents']}** · 文本块 **{stats['chunks']}** · "
            f"实体 **{stats['entities']}** · 关系 **{stats['relations']}**  \n"
            f"向量后端 `{stats['vector_backend']}` · 图谱后端 `{stats['graph_backend']}`"
        )

    def refresh_documents():
        return (
            gr.update(choices=document_choices(), value=None),
            document_rows(),
            stats_markdown(),
        )

    def index_files(files):
        paths = _file_paths(files)
        if not paths:
            return (
                "请先选择文件。",
                document_rows(),
                gr.update(choices=document_choices()),
                stats_markdown(),
            )
        try:
            reports = service.index_files(paths)
            detail = "\n".join(
                f"- `{item.source}`：{item.chunks} 个文本块，{item.relations} 条关系"
                for item in reports
            )
            status = f"索引完成，共处理 {len(reports)} 个文件。\n{detail}"
        except Exception as exc:  # UI boundary: show a concise actionable error
            status = f"索引失败：{type(exc).__name__}: {exc}"
        return (
            status,
            document_rows(),
            gr.update(choices=document_choices(), value=None),
            stats_markdown(),
        )

    def ask(question, history, mode, selected_doc_ids, top_k):
        history = list(history or [])
        if not str(question or "").strip():
            return history, "", [], build_relation_figure([])
        history.append({"role": "user", "content": question})
        try:
            bundle = service.ask(
                question,
                mode=mode,
                doc_ids=selected_doc_ids or None,
                top_k=int(top_k),
            )
            history.append({"role": "assistant", "content": bundle.answer})
            citations = [
                [
                    item.number,
                    item.title,
                    item.source,
                    item.page_number or "",
                    round(item.score, 4),
                    item.excerpt,
                ]
                for item in bundle.citations
            ]
            figure = build_relation_figure(bundle.relations)
        except Exception as exc:  # UI boundary
            history.append(
                {
                    "role": "assistant",
                    "content": f"处理失败：{type(exc).__name__}: {exc}",
                }
            )
            citations = []
            figure = build_relation_figure([])
        return history, "", citations, figure

    with gr.Blocks(
        title="毕业项目",
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="cyan"),
        css=CUSTOM_CSS,
    ) as demo:
        gr.HTML(
            """
            <section class="hero">
              <h1>毕业项目</h1>
              <p>面向金融新闻的检索增强生成式问答系统</p>
            </section>
            """
        )
        stats_panel = gr.Markdown(stats_markdown())

        with gr.Tabs():
            with gr.Tab("智能问答"):
                with gr.Row():
                    with gr.Column(scale=7):
                        chatbot = gr.Chatbot(
                            label="金融新闻问答",
                            type="messages",
                            height=500,
                            placeholder="请先在“文档索引”中上传材料，然后提出问题。",
                        )
                        question = gr.Textbox(
                            label="问题",
                            placeholder="例如：证监会提出的资本市场监管主线是什么？",
                            lines=2,
                        )
                        with gr.Row():
                            ask_button = gr.Button("发送问题", variant="primary")
                            clear_button = gr.Button("清空对话")
                    with gr.Column(scale=3):
                        mode = gr.Radio(
                            choices=[
                                ("融合检索", "hybrid"),
                                ("向量检索", "vector"),
                                ("图谱检索", "graph"),
                            ],
                            value="hybrid",
                            label="检索模式",
                        )
                        selected_docs = gr.Dropdown(
                            choices=document_choices(),
                            multiselect=True,
                            label="限定文档（不选表示全部）",
                        )
                        top_k = gr.Slider(1, 12, value=service.config.top_k, step=1, label="证据数量")
                        refresh_button = gr.Button("刷新文档列表")

                with gr.Tabs():
                    with gr.Tab("证据来源"):
                        citation_table = gr.Dataframe(
                            headers=["编号", "标题", "来源", "页码", "得分", "证据片段"],
                            datatype=["number", "str", "str", "str", "number", "str"],
                            interactive=False,
                            wrap=True,
                        )
                    with gr.Tab("实体关系"):
                        graph_plot = gr.Plot(value=build_relation_figure([]))

            with gr.Tab("文档索引"):
                gr.Markdown(
                    "上传金融新闻、公告、研报或其他材料。支持 PDF、DOCX、XLSX、CSV、HTML、TXT 和 Markdown。"
                )
                files = gr.File(
                    label="选择文档",
                    file_count="multiple",
                    type="filepath",
                    file_types=[".pdf", ".docx", ".xlsx", ".csv", ".html", ".htm", ".txt", ".md"],
                )
                index_button = gr.Button("构建知识索引", variant="primary")
                index_status = gr.Markdown()
                documents_table = gr.Dataframe(
                    headers=["文档ID", "标题", "来源", "发布日期", "文本块", "索引时间"],
                    value=document_rows(),
                    interactive=False,
                    wrap=True,
                )

            with gr.Tab("项目说明"):
                gr.Markdown(
                    """
                    ## 系统说明

                    本项目实现从文档解析、文本分块、向量索引、金融实体关系抽取、
                    向量/图谱/融合检索，到带证据答案生成的完整流程。

                    - 默认配置无需外部数据库，可直接使用 SQLite 演示。
                    - 生产化配置可切换至 Qdrant 与 Neo4j。
                    - 可接入 Ollama、vLLM、LocalAI 等 OpenAI 兼容模型服务。
                    - 回答仅用于信息整理，不构成投资建议。
                    """
                )

        gr.Markdown(
            "<span class='footer-note'>毕业设计演示系统 · 请根据证据原文与发布日期核验重要结论</span>"
        )

        ask_inputs = [question, chatbot, mode, selected_docs, top_k]
        ask_outputs = [chatbot, question, citation_table, graph_plot]
        ask_button.click(ask, ask_inputs, ask_outputs)
        question.submit(ask, ask_inputs, ask_outputs)
        clear_button.click(
            lambda: ([], "", [], build_relation_figure([])),
            outputs=ask_outputs,
        )
        refresh_button.click(
            refresh_documents,
            outputs=[selected_docs, documents_table, stats_panel],
        )
        index_button.click(
            index_files,
            inputs=[files],
            outputs=[index_status, documents_table, selected_docs, stats_panel],
        )

    return demo


def run_app() -> None:
    service = FinancialNewsRAGService()
    app = build_app(service)
    app.queue(default_concurrency_limit=2).launch(
        server_name=service.config.server_name,
        server_port=service.config.server_port,
        share=service.config.share,
        show_error=True,
    )
