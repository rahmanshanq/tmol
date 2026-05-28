import dash
from dash import html, dcc, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from .data import *

dash.register_page(__name__, path="/geography", name="Geography")

_geo = dict(showframe=False, showcoastlines=True, coastlinecolor="rgba(255,255,255,0.1)",
            landcolor="#1a2332", bgcolor="rgba(0,0,0,0)", projection_type="natural earth",
            showlakes=False, countrycolor="rgba(255,255,255,0.05)")

def _volume():
    fig = px.choropleth(
        COUNTRY_COUNTS, locations="iso3", color="count", hover_name="name",
        color_continuous_scale=[[0, "#161f2e"], [0.3, "#1e3a5f"], [0.7, "#c9a84c"], [1, "#fbbf24"]],
        range_color=[0, COUNTRY_COUNTS["count"].quantile(0.92)],
        labels={"count": "Works"},
    )
    fig.update_layout(**DARK_LAYOUT, height=520, geo=_geo,
                      coloraxis_colorbar=dict(title="", tickfont=dict(color="#64748b"), len=0.6))
    fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>%{z:,} works<extra></extra>")
    return fig

def _dominant():
    cat_by_c = COUNTRY_DF.groupby(["iso3", "cat"]).size().reset_index(name="count")
    dom = cat_by_c.loc[cat_by_c.groupby("iso3")["count"].idxmax()].copy()
    dom["name"] = dom["iso3"].map(ISO3_TO_NAME)
    fig = px.choropleth(dom, locations="iso3", color="cat", hover_name="name",
                        hover_data={"count": True, "cat": True, "iso3": False},
                        labels={"cat": "Tradition"}, color_discrete_map=COLORS)
    fig.update_layout(**DARK_LAYOUT, height=520, geo=_geo,
                      legend=dict(font=dict(size=7), orientation="h", y=-0.03, x=0.5, xanchor="center"))
    return fig

def _top_countries():
    top = COUNTRY_COUNTS.head(20).copy()
    top["name"] = top["iso3"].map(ISO3_TO_NAME)
    top = top.sort_values("count")
    fig = go.Figure(go.Bar(x=top["count"], y=top["name"], orientation="h",
                           marker_color="#c9a84c",
                           hovertemplate="<b>%{y}</b><br>%{x:,} works<extra></extra>"))
    fig.update_layout(**DARK_LAYOUT, height=520, xaxis=dict(**DARK_AXIS))
    return fig

def layout():
    all_slider_years = list(range(START_YEAR, END_YEAR + 1))
    return html.Div([
        html.H1(["Whose ", html.Em("Good Life"), "?"], className="page-title"),
        html.P("Where is the meaningful life being studied? Whose understanding gets scholarly weight?", className="page-subtitle"),
        html.Div(className="chart-card", children=[
            html.Div("Research Volume", className="chart-title"),
            html.Div("Brighter = more scholarship.", className="chart-desc"),
            dcc.Graph(figure=_volume(), config={"displayModeBar": False}),
        ]),
        html.Div(className="two-col", children=[
            html.Div(className="chart-card", children=[
                html.Div("Dominant Tradition by Country", className="chart-title"),
                dcc.Graph(figure=_dominant(), config={"displayModeBar": False}),
            ]),
            html.Div(className="chart-card", children=[
                html.Div("Top 20 Countries", className="chart-title"),
                dcc.Graph(figure=_top_countries(), config={"displayModeBar": False}),
            ]),
        ]),
        html.Div(className="chart-card", children=[
            html.Div("The Map Over Time", className="chart-title"),
            html.Div("Drag to see who enters the conversation.", className="chart-desc"),
            dcc.Slider(id="geo-slider", min=START_YEAR, max=END_YEAR, step=1, value=END_YEAR,
                       marks={d: {"label": str(d), "style": {"color": "#64748b"}} for d in range(START_YEAR, END_YEAR + 1, 5)}),
            dcc.Graph(id="geo-decade", config={"displayModeBar": False}),
        ]),
    ])

@callback(Output("geo-decade", "figure"), Input("geo-slider", "value"))
def update_decade(decade):
    filtered = COUNTRY_DF[COUNTRY_DF["year"] <= decade]
    counts = filtered["iso3"].value_counts().reset_index()
    counts.columns = ["iso3", "count"]
    counts["name"] = counts["iso3"].map(ISO3_TO_NAME)
    fig = px.choropleth(counts, locations="iso3", color="count", hover_name="name",
                        color_continuous_scale=[[0, "#161f2e"], [0.3, "#1e3a5f"], [0.7, "#c9a84c"], [1, "#fbbf24"]],
                        range_color=[0, 25000], labels={"count": "Works"})
    fig.update_layout(**DARK_LAYOUT, height=480, geo=_geo,
                      title=dict(text=f"By {decade}", font=dict(size=16, color="#c9a84c")),
                      coloraxis_colorbar=dict(title="", tickfont=dict(color="#64748b"), len=0.6))
    return fig
