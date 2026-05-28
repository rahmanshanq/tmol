import dash
from dash import html, dcc, callback, Input, Output, ctx
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from .data import *

dash.register_page(__name__, path="/explore", name="Explore")


def layout():
    cats = sorted(CATEGORIES)
    terms = sorted(TERM_MAP["search_query"].unique().tolist())
    return html.Div([
        html.H1(["Find ", html.Em("Your"), " Question"], className="page-title"),
        html.P("Filter by tradition or concept. Everything responds.", className="page-subtitle"),
        html.Div(className="filter-bar", children=[
            dcc.Dropdown(id="ex-cat", options=[{"label": c, "value": c} for c in cats],
                         placeholder="Tradition...", clearable=True, style={"width": "280px"}),
            dcc.Dropdown(id="ex-term", options=[{"label": t, "value": t} for t in terms],
                         placeholder="Search term...", clearable=True, style={"width": "280px"}),
            html.Button("✕ Clear", id="ex-reset", className="reset-btn"),
        ]),
        html.Div(id="ex-stats", className="stat-row"),
        html.Div(className="two-col", children=[
            html.Div(className="chart-card", children=[
                html.Div("Concept Sunburst", className="chart-title"),
                html.Div("Tradition → search term. Click to drill.", className="chart-desc"),
                dcc.Graph(id="ex-sun", config={"displayModeBar": False}),
            ]),
            html.Div(className="chart-card", children=[
                html.Div("Top Journals", className="chart-title"),
                dcc.Graph(id="ex-j", config={"displayModeBar": False}),
            ]),
        ]),
        html.Div(className="two-col", children=[
            html.Div(className="chart-card", children=[
                html.Div("Top Countries", className="chart-title"),
                dcc.Graph(id="ex-c", config={"displayModeBar": False}),
            ]),
            html.Div(className="chart-card", style={"maxHeight": "560px", "overflowY": "auto"}, children=[
                html.Div("Papers", className="chart-title"),
                html.Div("Click any paper to read it on OpenAlex.", className="chart-desc"),
                html.Div(id="ex-papers"),
            ]),
        ]),
    ])


@callback([Output("ex-cat", "value"), Output("ex-term", "value")],
          Input("ex-reset", "n_clicks"), prevent_initial_call=True)
def reset(n): return None, None


@callback([Output("ex-stats", "children"), Output("ex-sun", "figure"),
           Output("ex-j", "figure"), Output("ex-c", "figure"), Output("ex-papers", "children")],
          [Input("ex-cat", "value"), Input("ex-term", "value")])
def update(cat, term):
    df = WORKS.copy()
    if term:
        ids = set(TERM_MAP[TERM_MAP["search_query"] == term]["work_id"])
        df = df[df["work_id"].isin(ids)]
    if cat:
        df = df[df["primary_category"] == cat]

    n_c = set()
    for c in df["countries"].dropna():
        if c: n_c.update(c.split("|"))

    stats = [
        html.Div(className="stat-card", children=[html.Div(f"{len(df):,}", className="stat-number"), html.Div("Works", className="stat-label")]),
        html.Div(className="stat-card", children=[html.Div(str(df["primary_category"].nunique()), className="stat-number"), html.Div("Traditions", className="stat-label")]),
        html.Div(className="stat-card", children=[html.Div(str(len(n_c)), className="stat-number"), html.Div("Countries", className="stat-label")]),
    ]

    empty = go.Figure().update_layout(**DARK_LAYOUT, height=450)

    # Sunburst
    mg = TERM_MAP.merge(df[["work_id", "primary_category"]], on="work_id", how="inner")
    grp = mg.groupby(["primary_category", "search_query"]).size().reset_index(name="count")
    top = grp.sort_values("count", ascending=False).groupby("primary_category").head(5)
    if len(top) > 0:
        sun = px.sunburst(top, path=["primary_category", "search_query"], values="count",
                          color="primary_category", color_discrete_map=COLORS)
        sun.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="'IBM Plex Sans'", color="#cbd5e1"), height=500,
                          margin=dict(l=10, r=10, t=10, b=10))
        sun.update_traces(textinfo="label+percent parent", insidetextorientation="radial")
    else:
        sun = empty

    # Journals
    js = df[df["journal"].str.len() > 0]["journal"].value_counts().head(10)
    jf = go.Figure(go.Bar(x=js.values, y=js.index, orientation="h", marker_color="#c9a84c",
                           hovertemplate="<b>%{y}</b><br>%{x:,} papers<extra></extra>")) if len(js) else empty
    jf.update_layout(**DARK_LAYOUT, height=450, xaxis=dict(**DARK_AXIS), yaxis=dict(autorange="reversed", tickfont=dict(size=9)))

    # Countries — full names
    all_c = [c for cs in df["countries"].dropna() if cs for c in cs.split("|")]
    if all_c:
        cc = pd.Series(all_c).value_counts().head(12)
        # Map ISO2 to full names
        names = [ISO3_TO_NAME.get(ISO2_TO_ISO3.get(c, ""), c) for c in cc.index]
        cf = go.Figure(go.Bar(x=cc.values, y=names, orientation="h", marker_color="#34d399",
                               hovertemplate="<b>%{y}</b><br>%{x:,} papers<extra></extra>"))
        cf.update_layout(**DARK_LAYOUT, height=450, xaxis=dict(**DARK_AXIS), yaxis=dict(autorange="reversed", tickfont=dict(size=9)))
    else:
        cf = empty

    # Papers — clickable links
    papers = []
    for _, r in df.head(25).iterrows():
        t = r.get("title", "")
        if not t: continue
        wid = r.get("work_id", "")
        url = wid.replace("https://openalex.org/", "https://openalex.org/works/") if wid else "#"
        papers.append(html.A(
            className="feed-item", href=url, target="_blank",
            style={"display": "block", "textDecoration": "none", "cursor": "pointer"},
            children=[
                html.Div(t[:110], className="feed-title"),
                html.Div(className="feed-meta", children=[
                    html.Span(r.get("primary_category", ""), className="feed-tag"),
                    f" · {r.get('journal', '')} · {int(r['year']) if pd.notna(r.get('year')) else ''}",
                ]),
            ],
        ))
    if not papers:
        papers = [html.Div("No results.", style={"color": "#475569", "padding": "1rem"})]

    return stats, sun, jf, cf, papers
