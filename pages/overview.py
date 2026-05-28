import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
from .data import *

dash.register_page(__name__, path="/", name="Overview")


def _treemap():
    """Treemap showing relative size of each tradition."""
    cats = sorted(CAT_SIZES.items(), key=lambda x: -x[1])
    fig = go.Figure(go.Treemap(
        labels=[c for c, _ in cats],
        parents=[""] * len(cats),
        values=[v for _, v in cats],
        marker=dict(colors=[COLORS.get(c, "#666") for c, _ in cats],
                    line=dict(width=1, color="#111821")),
        textinfo="label+value",
        textfont=dict(size=13),
        hovertemplate="<b>%{label}</b><br>%{value:,} works<br>%{percentRoot:.1%} of total<extra></extra>",
    ))
    fig.update_layout(**DARK_LAYOUT, height=500)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    return fig


def _top_bridges():
    """Top cross-tradition bridges."""
    sorted_edges = sorted(EDGE_COUNTS.items(), key=lambda x: -x[1])[:12]
    labels = [f"{a.split(' ')[0]} ↔ {b.split(' ')[0]}" for (a, b), _ in sorted_edges]
    values = [w for _, w in sorted_edges]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color="#c9a84c", line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>%{x:,} shared works<extra></extra>",
    ))
    fig.update_layout(**DARK_LAYOUT, height=420,
                      xaxis=dict(**DARK_AXIS), yaxis=dict(autorange="reversed"))
    return fig


def _insularity_chart():
    """How insular is each tradition?"""
    colors = [COLORS.get(c, "#666") for c in INSULARITY.index]
    fig = go.Figure(go.Bar(
        x=INSULARITY.values, y=INSULARITY.index, orientation="h",
        marker_color=colors,
        hovertemplate="<b>%{y}</b><br>%{x:.0%} of papers connect to no other tradition<extra></extra>",
    ))
    fig.update_layout(**DARK_LAYOUT, height=480,
                      xaxis=dict(**DARK_AXIS, tickformat=".0%"),
                      yaxis=dict(autorange="reversed", tickfont=dict(size=9)))
    return fig


def layout():
    # Compute year range from actual chart range
    yr_display = f"{START_YEAR}–{END_YEAR}"

    return html.Div([
        html.H1([html.Em("The Meaning of Life"), " Across Disciplines"], className="page-title"),
        html.P(
            "Across centuries and continents, humanity returns to the same inquiry: "
            "how should we live? This dashboard maps 129,672 scholarly works that attempt an answer.",
            className="page-subtitle",
        ),
        html.Div(className="stat-row", children=[
            html.Div(className="stat-card", children=[
                html.Div(f"{TOTAL_WORKS:,}", className="stat-number"),
                html.Div("Works", className="stat-label"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div(str(NUM_CATEGORIES), className="stat-number"),
                html.Div("Traditions", className="stat-label"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div(str(NUM_COUNTRIES), className="stat-number"),
                html.Div("Countries", className="stat-label"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div(yr_display, className="stat-number"),
                html.Div("Span", className="stat-label"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div(f"{MULTI_LABEL_RATE:.0%}", className="stat-number"),
                html.Div("Cross-tradition", className="stat-label"),
            ]),
        ]),

        html.Div(className="chart-card", children=[
            html.Div("The Landscape", className="chart-title"),
            html.Div("Each block is a tradition. Size shows how much scholarship it produces. "
                      "Psychology leads, but 15 other traditions contribute to the same conversation.", className="chart-desc"),
            dcc.Graph(figure=_treemap(), config={"displayModeBar": False}),
        ]),

        html.Div(className="two-col", children=[
            html.Div(className="chart-card", children=[
                html.Div("Strongest Bridges", className="chart-title"),
                html.Div("The traditions that share the most papers between them.", className="chart-desc"),
                dcc.Graph(figure=_top_bridges(), config={"displayModeBar": False}),
            ]),
            html.Div(className="chart-card", children=[
                html.Div("Insularity", className="chart-title"),
                html.Div("How self-contained is each tradition? Higher = more isolated.", className="chart-desc"),
                dcc.Graph(figure=_insularity_chart(), config={"displayModeBar": False}),
            ]),
        ]),
    ])
