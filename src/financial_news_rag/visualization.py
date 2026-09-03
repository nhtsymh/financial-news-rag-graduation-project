from __future__ import annotations

from .models import Relation


TYPE_COLORS = {
    "公司": "#2563eb",
    "机构": "#7c3aed",
    "行业": "#059669",
    "政策": "#dc2626",
    "事件": "#d97706",
    "文档": "#64748b",
    "Entity": "#0891b2",
}


def build_relation_figure(relations: list[Relation]):
    try:
        import networkx as nx
        import plotly.graph_objects as go
    except ImportError as exc:
        raise RuntimeError("Graph visualization requires networkx and plotly") from exc

    if not relations:
        figure = go.Figure()
        figure.add_annotation(
            text="当前问题没有检索到图谱关系",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"size": 16, "color": "#64748b"},
        )
        figure.update_layout(
            height=460,
            xaxis={"visible": False},
            yaxis={"visible": False},
            margin={"l": 10, "r": 10, "t": 30, "b": 10},
        )
        return figure

    graph = nx.DiGraph()
    for relation in relations:
        graph.add_node(relation.source, entity_type=relation.source_type)
        graph.add_node(relation.target, entity_type=relation.target_type)
        graph.add_edge(
            relation.source,
            relation.target,
            relation=relation.relation,
            confidence=relation.confidence,
        )
    positions = nx.spring_layout(graph, seed=42, k=1.2)
    figure = go.Figure()

    for source, target, attributes in graph.edges(data=True):
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        relation_name = attributes.get("relation", "关联")
        figure.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={"width": 1.4, "color": "#94a3b8"},
                hoverinfo="text",
                text=[relation_name, relation_name],
                showlegend=False,
            )
        )
        figure.add_annotation(
            x=x1,
            y=y1,
            ax=x0,
            ay=y0,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            text=relation_name,
            showarrow=True,
            arrowhead=3,
            arrowsize=1,
            arrowwidth=1.2,
            arrowcolor="#64748b",
            font={"size": 9, "color": "#475569"},
            bgcolor="rgba(255,255,255,0.75)",
        )

    node_x: list[float] = []
    node_y: list[float] = []
    labels: list[str] = []
    colors: list[str] = []
    sizes: list[int] = []
    hover: list[str] = []
    for node, attributes in graph.nodes(data=True):
        x, y = positions[node]
        entity_type = attributes.get("entity_type", "Entity")
        node_x.append(float(x))
        node_y.append(float(y))
        labels.append(node if len(node) <= 12 else node[:11] + "…")
        colors.append(TYPE_COLORS.get(entity_type, TYPE_COLORS["Entity"]))
        sizes.append(min(20 + graph.degree(node) * 4, 48))
        hover.append(f"{node}<br>类型：{entity_type}<br>连接数：{graph.degree(node)}")
    figure.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=labels,
            textposition="top center",
            hovertext=hover,
            hoverinfo="text",
            marker={
                "size": sizes,
                "color": colors,
                "line": {"width": 1.5, "color": "white"},
            },
            showlegend=False,
        )
    )
    figure.update_layout(
        title="金融实体关系图",
        height=520,
        hovermode="closest",
        paper_bgcolor="#f8fafc",
        plot_bgcolor="#f8fafc",
        margin={"l": 10, "r": 10, "t": 45, "b": 10},
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return figure
