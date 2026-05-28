import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import requests
import pandas as pd
from datetime import datetime, timedelta
from .data import DARK_LAYOUT, DARK_AXIS, ALL_TERMS
import random

dash.register_page(__name__, path="/live", name="Live Feed")

# Sample 30 terms from the full list for each refresh to cover breadth
SAMPLE_SIZE = 30

def _fetch(days=30, per=5):
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    terms = random.sample(ALL_TERMS, min(SAMPLE_SIZE, len(ALL_TERMS)))
    results, seen = [], set()
    for term in terms:
        try:
            url = (f"https://api.openalex.org/works?filter=default.search:{requests.utils.quote(term)},"
                   f"from_publication_date:{cutoff}&per_page={per}&sort=publication_date:desc"
                   f"&select=id,title,publication_year,primary_location,authorships,primary_topic,keywords")
            resp = requests.get(url, timeout=8)
            if resp.status_code != 200: continue
            for w in resp.json().get("results", []):
                wid = w.get("id", "")
                if wid in seen: continue
                seen.add(wid)
                loc = w.get("primary_location", {}) or {}
                src = loc.get("source", {}) or {}
                pt = w.get("primary_topic", {}) or {}
                countries = {c for a in w.get("authorships", []) for c in a.get("countries", [])}
                kws = [k["display_name"] for k in (w.get("keywords") or []) if k.get("display_name")]
                # Build OpenAlex URL
                oa_url = wid.replace("https://openalex.org/", "https://openalex.org/works/") if wid else ""
                results.append({
                    "title": w.get("title", ""), "year": w.get("publication_year", ""),
                    "journal": src.get("display_name", ""), "url": oa_url,
                    "field": pt.get("field", {}).get("display_name", "") if pt.get("field") else "",
                    "countries": ", ".join(sorted(countries)), "keywords": kws[:5], "term": term,
                })
        except: pass
    return results

def layout():
    return html.Div([
        html.H1(["What's Happening ", html.Em("Now"), "?"], className="page-title"),
        html.P(f"Sampling {SAMPLE_SIZE} terms from {len(ALL_TERMS)} each refresh. Click any paper to read it.", className="page-subtitle"),
        html.Div(className="stat-row", children=[
            html.Div(className="stat-card", children=[html.Div(id="lv-count", className="stat-number", children="—"), html.Div("Papers", className="stat-label")]),
            html.Div(className="stat-card", children=[html.Div(str(len(ALL_TERMS)), className="stat-number"), html.Div("Total terms", className="stat-label")]),
            html.Div(className="stat-card", children=[html.Div(id="lv-time", className="stat-number", children="—"), html.Div("Last refresh", className="stat-label")]),
        ]),
        html.Button("⟳  Refresh", id="lv-btn", className="action-btn", style={"marginBottom": "1.5rem"}),
        html.Div(className="two-col", children=[
            html.Div(className="chart-card", style={"maxHeight": "750px", "overflowY": "auto"}, children=[
                html.Div("Feed", className="chart-title"),
                html.Div(id="lv-feed", children=[
                    html.Div("Press Refresh to load.", style={"color": "#475569", "padding": "2rem", "textAlign": "center"}),
                ]),
            ]),
            html.Div(children=[
                html.Div(className="chart-card", children=[
                    html.Div("By Term", className="chart-title"),
                    dcc.Graph(id="lv-terms", config={"displayModeBar": False}),
                ]),
                html.Div(className="chart-card", children=[
                    html.Div("Top Keywords", className="chart-title"),
                    dcc.Graph(id="lv-kw", config={"displayModeBar": False}),
                ]),
            ]),
        ]),
        dcc.Interval(id="lv-interval", interval=300_000, n_intervals=0),
        dcc.Store(id="lv-store"),
    ])

@callback([Output("lv-store", "data"), Output("lv-count", "children"), Output("lv-time", "children")],
          [Input("lv-btn", "n_clicks"), Input("lv-interval", "n_intervals")], prevent_initial_call=True)
def refresh(n, i):
    r = _fetch()
    return r, str(len(r)), datetime.now().strftime("%H:%M")

@callback(Output("lv-feed", "children"), Input("lv-store", "data"), prevent_initial_call=True)
def feed(data):
    if not data: return html.Div("No results.", style={"color": "#475569", "padding": "1rem"})
    items = []
    for p in data[:60]:
        kw_tags = [html.Span(k, className="feed-tag", style={"background": "rgba(201,168,76,0.1)", "color": "#c9a84c"}) for k in p.get("keywords", [])[:3]]
        items.append(html.A(
            className="feed-item", href=p.get("url", "#"), target="_blank",
            style={"display": "block", "textDecoration": "none", "cursor": "pointer"},
            children=[
                html.Div(p["title"], className="feed-title"),
                html.Div(className="feed-meta", children=[
                    html.Span(p["term"], className="feed-tag"),
                    html.Span(p["field"], className="feed-tag", style={"background": "rgba(52,211,153,0.1)", "color": "#34d399"}) if p["field"] else None,
                    f" · {p['journal']}" if p["journal"] else "",
                    f" · {p['countries']}" if p["countries"] else "",
                ]),
                html.Div(kw_tags, style={"marginTop": "0.2rem"}) if kw_tags else None,
            ],
        ))
    return items

@callback([Output("lv-terms", "figure"), Output("lv-kw", "figure")],
          Input("lv-store", "data"), prevent_initial_call=True)
def charts(data):
    empty = go.Figure().update_layout(**DARK_LAYOUT, height=250)
    if not data: return empty, empty
    df = pd.DataFrame(data)
    tc = df["term"].value_counts().head(12)
    f1 = go.Figure(go.Bar(x=tc.values, y=tc.index, orientation="h", marker_color="#c9a84c",
                           hovertemplate="%{y}: %{x}<extra></extra>"))
    f1.update_layout(**DARK_LAYOUT, height=300, xaxis=dict(**DARK_AXIS))
    all_kw = [k for kws in df["keywords"] if isinstance(kws, list) for k in kws]
    kc = pd.Series(all_kw).value_counts().head(12)
    f2 = go.Figure(go.Bar(x=kc.values, y=kc.index, orientation="h", marker_color="#34d399",
                           hovertemplate="%{y}: %{x}<extra></extra>"))
    f2.update_layout(**DARK_LAYOUT, height=300, xaxis=dict(**DARK_AXIS))
    return f1, f2
