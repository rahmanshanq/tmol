"""The Meaning of Life Across Scholarly Disciplines"""

import dash
from dash import html, dcc, callback, Input, Output, ctx
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title="The Meaning of Life — Across Disciplines",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=IBM+Plex+Sans:wght@200;300;400;500&family=JetBrains+Mono:wght@300;400&display=swap"
    ],
)
app._favicon = "favicon.svg"
server = app.server

NAV = [
    ("/",          "◉", "Overview"),
    ("/network",   "◈", "Network"),
    ("/timeline",  "◆", "Timeline"),
    ("/geography", "◐", "Geography"),
    ("/live",      "◎", "Live Feed"),
    ("/explore",   "◇", "Explore"),
]

sidebar = html.Div(className="sidebar", children=[
    html.Div(className="sidebar-brand", children=[
        html.Div("The Meaning of Life", className="sidebar-title"),
        html.Div("Across Scholarly Disciplines", className="sidebar-title",
                 style={"fontSize": "1.1rem", "color": "#94a3b8", "fontWeight": "300", "fontStyle": "italic"}),
        html.Div("129,672 works · 16 traditions", className="sidebar-meta", style={"marginTop": "0.8rem"}),
    ]),
    html.Nav([
        dcc.Link(
            children=[html.Span(icon, className="nav-icon"), label],
            href=path, className="nav-link", id=f"nav-{label.lower().replace(' ', '-')}"
        ) for path, icon, label in NAV
    ]),
    html.Div(style={"flex": "1"}),
    html.Div(style={"padding": "1.5rem 1.8rem", "borderTop": "1px solid rgba(255,255,255,0.06)"}, children=[
        html.Div("Rahman Alshanqeeti", style={"color": "#64748b", "fontSize": "0.75rem", "fontFamily": "var(--font-body)"}),
        html.Div("DIGS 20004 · Spring 2026", style={"color": "#475569", "fontSize": "0.68rem", "fontFamily": "var(--font-mono)", "letterSpacing": "0.05em"}),
    ]),
])

app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    html.Div(className="main-content", children=[dash.page_container]),
])

@callback(
    [Output(f"nav-{label.lower().replace(' ', '-')}", "className") for _, _, label in NAV],
    Input("url", "pathname"),
)
def highlight_nav(path):
    return ["nav-link active" if p == path else "nav-link" for p, _, _ in NAV]

if __name__ == "__main__":
    app.run(debug=True, port=8050)
