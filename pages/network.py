import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import plotly.graph_objects as go
import pandas as pd
from .data import *

dash.register_page(__name__, path="/network", name="Network")


def _network(hl=None):
    edge_traces = []
    for a, b, d in GRAPH.edges(data=True):
        x0, y0 = GRAPH_POS[a]; x1, y1 = GRAPH_POS[b]
        w = d["weight"]
        if hl and (a == hl or b == hl):
            width = max(1.5, min(8, w / 400))
            color = f"rgba(201,168,76,{min(0.8, max(0.25, w / 2000))})"
        elif hl:
            width = 0.3
            color = "rgba(148,163,184,0.03)"
        else:
            width = max(0.5, min(5, w / 600))
            color = f"rgba(148,163,184,{min(0.4, max(0.06, w / 3000))})"

        # Make edges clickable by adding customdata with both tradition names
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None], mode="lines",
            line=dict(width=width, color=color),
            hoverinfo="text", text=f"{a} ↔ {b}: {w:,}<br><i>Click to see papers</i>",
            showlegend=False,
        ))
        # Invisible clickable midpoint marker for each edge
        if w >= 50:
            edge_traces.append(go.Scatter(
                x=[mid_x], y=[mid_y], mode="markers",
                marker=dict(size=max(8, min(25, width * 3)), color="rgba(0,0,0,0)"),
                hoverinfo="text", hovertext=f"{a} ↔ {b}: {w:,}<br><i>Click to see papers</i>",
                showlegend=False, customdata=[f"edge:{a}||{b}"],
            ))

    nodes = list(GRAPH.nodes())
    sizes = [max(20, min(65, GRAPH.nodes[n]["size"] / 350)) for n in nodes]
    colors = [COLORS.get(n, "#999") if (hl is None or n == hl) else "rgba(100,116,139,0.2)" for n in nodes]
    borders = ["#c9a84c" if n == hl else "rgba(255,255,255,0.2)" for n in nodes]
    bw = [3 if n == hl else 1.5 for n in nodes]

    hover = []
    for n in nodes:
        conns = sorted(GRAPH[n].items(), key=lambda x: x[1]["weight"], reverse=True)[:4]
        txt = "<br>".join([f"  → {c}: {d['weight']:,}" for c, d in conns])
        hover.append(f"<b>{n}</b><br>{GRAPH.nodes[n]['size']:,} works<br>{txt}")

    labels = [n.replace(" & ", "\n").replace(" Thought", "") for n in nodes]
    node_trace = go.Scatter(
        x=[GRAPH_POS[n][0] for n in nodes], y=[GRAPH_POS[n][1] for n in nodes],
        mode="markers+text", marker=dict(size=sizes, color=colors, line=dict(width=bw, color=borders)),
        text=labels, textposition="top center", textfont=dict(size=8, color="rgba(255,255,255,0.7)"),
        hovertext=hover, hoverinfo="text", showlegend=False, customdata=[f"node:{n}" for n in nodes],
    )
    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(**DARK_LAYOUT, height=680,
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False))
    return fig


def _connections(hl=None):
    if hl:
        conn = {}
        for (a, b), w in EDGE_COUNTS.items():
            if a == hl: conn[b] = conn.get(b, 0) + w
            elif b == hl: conn[a] = conn.get(a, 0) + w
        s = pd.Series(conn).sort_values(ascending=True)
        fig = go.Figure(go.Bar(
            x=s.values, y=s.index, orientation="h",
            marker_color=[COLORS.get(c, "#666") for c in s.index],
            hovertemplate="<b>%{y}</b><br>%{x:,} shared works<br><i>Click to see papers</i><extra></extra>",
        ))
        fig.update_layout(**DARK_LAYOUT, height=500, xaxis=dict(**DARK_AXIS))
    else:
        cats = CATEGORIES
        short = [c.replace(" & ", "\n").replace(" Thought", "").replace("Cultural Concepts", "CC") for c in cats]
        matrix = pd.DataFrame(0, index=cats, columns=cats)
        for (a, b), w in EDGE_COUNTS.items():
            if a in cats and b in cats:
                matrix.loc[a, b] = w; matrix.loc[b, a] = w
        fig = go.Figure(go.Heatmap(
            z=matrix.values, x=short, y=short,
            colorscale=[[0, "#161f2e"], [0.5, "#1e3a5f"], [1, "#c9a84c"]],
            hovertemplate="%{x} ↔ %{y}: %{z:,}<extra></extra>",
        ))
        fig.update_layout(**DARK_LAYOUT, height=550,
                          xaxis=dict(tickangle=45, tickfont=dict(size=7)),
                          yaxis=dict(tickfont=dict(size=7)))
    return fig


def _papers_panel(cat1=None, cat2=None, sel_cat=None):
    if cat1 and cat2:
        papers = get_bridge_papers(cat1, cat2, n=10)
        title = f"Papers bridging {cat1.split(' ')[0]} & {cat2.split(' ')[0]}"
    elif sel_cat:
        papers = get_tradition_papers(sel_cat, n=10)
        title = f"Key papers in {sel_cat}"
    else:
        return html.Div([
            html.Div("Select a tradition or click a connection to see papers.", className="chart-desc",
                     style={"padding": "2rem", "textAlign": "center"}),
        ])

    items = []
    for p in papers:
        wid = p.get("work_id", "")
        url = wid.replace("https://openalex.org/", "https://openalex.org/works/") if wid else "#"
        items.append(html.A(
            className="feed-item", href=url, target="_blank",
            style={"display": "block", "textDecoration": "none", "cursor": "pointer"},
            children=[
                html.Div(p.get("title", "Untitled")[:100], className="feed-title"),
                html.Div(className="feed-meta", children=[
                    html.Span(p.get("primary_category", ""), className="feed-tag"),
                    f" · {p.get('journal', '')} · {p.get('year', '')}",
                ]),
            ],
        ))
    if not items:
        items = [html.Div("No papers found for this combination.", style={"color": "#475569", "padding": "1rem"})]
    return html.Div([html.Div(title, className="chart-title", style={"marginBottom": "0.5rem"})] + items)


def layout():
    return html.Div([
        html.H1(["Who Talks to ", html.Em("Whom"), "?"], className="page-title"),
        html.P("Click a node to focus on a tradition. Click a link or connection bar to see bridging papers. "
               "All papers are clickable.", className="page-subtitle"),
        html.Div(id="net-banner"),
        html.Div(className="chart-card", children=[
            html.Div(className="chart-header", children=[
                html.Div("Constellation of Ideas", className="chart-title"),
                html.Button("✕ Reset All", id="net-reset", className="reset-btn"),
            ]),
            dcc.Graph(id="net-graph", config={"displayModeBar": False}),
        ]),
        html.Div(className="two-col", children=[
            html.Div(className="chart-card", children=[
                html.Div(className="chart-header", children=[
                    html.Div(id="net-ht", className="chart-title", children="Connection Strength"),
                    html.Button("✕ Clear", id="net-heat-reset", className="reset-btn"),
                ]),
                html.Div("Click any bar to see bridging papers.", className="chart-desc"),
                dcc.Graph(id="net-heat", config={"displayModeBar": False}),
            ]),
            html.Div(className="chart-card", style={"maxHeight": "560px", "overflowY": "auto"}, children=[
                html.Div(id="net-papers"),
            ]),
        ]),
        dcc.Store(id="net-sel", data=None),
        dcc.Store(id="net-bridge", data=None),
    ])


@callback(Output("net-sel", "data"),
          [Input("net-graph", "clickData"), Input("net-reset", "n_clicks")],
          State("net-sel", "data"), prevent_initial_call=True)
def toggle_node(click, reset, cur):
    if ctx.triggered_id == "net-reset": return None
    if click and click.get("points"):
        pt = click["points"][0]
        cd = pt.get("customdata", "")
        if isinstance(cd, str) and cd.startswith("node:"):
            node = cd[5:]
            return None if node == cur else node
        elif isinstance(cd, str) and cd.startswith("edge:"):
            # Edge click — don't change node selection
            return dash.no_update
    return None


@callback(Output("net-bridge", "data"),
          [Input("net-heat", "clickData"), Input("net-graph", "clickData"),
           Input("net-heat-reset", "n_clicks"), Input("net-reset", "n_clicks")],
          State("net-sel", "data"), State("net-bridge", "data"), prevent_initial_call=True)
def toggle_bridge(heat_click, graph_click, heat_reset, full_reset, sel, cur_bridge):
    trigger = ctx.triggered_id
    if trigger in ("net-heat-reset", "net-reset"):
        return None
    if trigger == "net-heat" and heat_click and heat_click.get("points") and sel:
        clicked = heat_click["points"][0].get("y")
        if clicked == cur_bridge:
            return None  # toggle off
        return clicked
    if trigger == "net-graph" and graph_click and graph_click.get("points"):
        cd = graph_click["points"][0].get("customdata", "")
        if isinstance(cd, str) and cd.startswith("edge:"):
            parts = cd[5:].split("||")
            if len(parts) == 2:
                return f"{parts[0]}||{parts[1]}"
    return dash.no_update


@callback([Output("net-graph", "figure"), Output("net-heat", "figure"),
           Output("net-ht", "children"), Output("net-banner", "children"),
           Output("net-papers", "children")],
          [Input("net-sel", "data"), Input("net-bridge", "data")])
def update(sel, bridge):
    title = f"Bridges from {sel}" if sel else "Connection Strength"
    banner = html.Div(className="selection-banner", children=[
        "Focused: ", html.Span(sel, className="tag"),
    ]) if sel else None

    # Determine which papers to show
    if bridge and "||" in str(bridge):
        parts = bridge.split("||")
        papers = _papers_panel(cat1=parts[0], cat2=parts[1])
    elif bridge and sel:
        papers = _papers_panel(cat1=sel, cat2=bridge)
    elif sel:
        papers = _papers_panel(sel_cat=sel)
    else:
        papers = _papers_panel()

    return _network(sel), _connections(sel), title, banner, papers
