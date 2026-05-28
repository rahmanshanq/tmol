import dash
from dash import html, dcc
import plotly.graph_objects as go
from .data import *

dash.register_page(__name__, path="/timeline", name="Timeline")


def _stream():
    fig = go.Figure()
    for cat in reversed(CATEGORIES):
        fig.add_trace(go.Scatter(
            x=ALL_YEARS, y=YEARLY_TRACES[cat], mode="lines", name=cat, stackgroup="one",
            line=dict(width=0.3, color=COLORS[cat]), fillcolor=COLORS[cat],
            hovertemplate="%{x}: %{y:.0f}<extra>" + cat + "</extra>",
        ))
    fig.update_layout(**DARK_LAYOUT, height=480, showlegend=True,
                      legend=dict(font=dict(size=8), orientation="h", y=1.12, x=0.5, xanchor="center"),
                      xaxis=dict(**DARK_AXIS, dtick=10),
                      yaxis=dict(**DARK_AXIS, title=""))
    for yr, label in [(1998, "Seligman's APA address"), (2011, "Keyes' flourishing model")]:
        fig.add_vline(x=yr, line_dash="dot", line_color="rgba(201,168,76,0.2)")
        fig.add_annotation(x=yr, y=0.95, yref="paper", text=label, showarrow=False,
                           font=dict(size=7, color="#c9a84c"), textangle=-90, xanchor="left")
    return fig


def _race():
    years = list(range(START_YEAR, END_YEAR + 1))
    frames = []
    for yr in years:
        d = YEARLY_COUNTS[YEARLY_COUNTS["year"] <= yr].groupby("primary_category")["count"].sum().sort_values()
        frames.append({"yr": yr, "d": d})

    init = frames[0]["d"]
    fig = go.Figure(
        data=[go.Bar(x=init.values, y=init.index, orientation="h",
                     marker_color=[COLORS.get(c, "#666") for c in init.index])],
        frames=[go.Frame(
            data=[go.Bar(x=f["d"].values, y=f["d"].index, orientation="h",
                         marker_color=[COLORS.get(c, "#666") for c in f["d"].index],
                         hovertemplate="%{y}: %{x:,}<extra></extra>")],
            name=str(f["yr"]),
            layout=go.Layout(title=dict(text=str(f["yr"]), font=dict(size=32, color="#c9a84c"),
                                        x=0.95, xanchor="right", y=0.95)),
        ) for f in frames],
    )
    fig.update_layout(
        **DARK_LAYOUT, height=620,
        xaxis=dict(**DARK_AXIS),
        yaxis=dict(tickfont=dict(size=9)),
        title=dict(text=str(START_YEAR), font=dict(size=32, color="#c9a84c"),
                   x=0.95, xanchor="right", y=0.95),
        updatemenus=[dict(
            type="buttons", showactive=True,
            x=0.0, y=1.13, xanchor="left",
            direction="left",
            font=dict(color="#c9a84c", size=11),
            pad=dict(r=10),
            buttons=[
                dict(label="  ▶  Play  ", method="animate",
                     args=[None, {"frame": {"duration": 200, "redraw": True}, "fromcurrent": True, "transition": {"duration": 100}}]),
                dict(label="  ⏸  Pause  ", method="animate",
                     args=[[None], {"frame": {"duration": 0}, "mode": "immediate"}]),
            ],
        )],
        sliders=[dict(
            active=0, steps=[
                dict(args=[[str(f["yr"])], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                     label=str(f["yr"]) if f["yr"] % 10 == 0 else "", method="animate") for f in frames
            ],
            x=0.0, len=1.0, y=-0.02, pad=dict(t=50),
            currentvalue=dict(visible=False),
            ticklen=0, font=dict(color="#64748b", size=9),
        )],
    )
    return fig


def _share():
    totals = [sum(YEARLY_TRACES[c][i] for c in CATEGORIES) for i in range(len(ALL_YEARS))]
    fig = go.Figure()
    for cat in reversed(CATEGORIES):
        pct = [YEARLY_TRACES[cat][i] / totals[i] * 100 if totals[i] > 0 else 0 for i in range(len(ALL_YEARS))]
        fig.add_trace(go.Scatter(
            x=ALL_YEARS, y=pct, mode="lines", name=cat, stackgroup="one",
            line=dict(width=0.3, color=COLORS[cat]), fillcolor=COLORS[cat],
            hovertemplate="<b>" + cat + "</b><br>%{x}: %{y:.1f}%<extra></extra>",
        ))
    fig.update_layout(**DARK_LAYOUT, height=420, showlegend=False,
                      xaxis=dict(**DARK_AXIS, dtick=10),
                      yaxis=dict(**DARK_AXIS, range=[0, 100], title=""),
                      hoverlabel=dict(namelength=-1))
    return fig


def layout():
    return html.Div([
        html.H1(["How Did We ", html.Em("Get Here"), "?"], className="page-title"),
        html.P("Seven decades of humanity asking how to live.", className="page-subtitle"),
        html.Div(className="chart-card", children=[
            html.Div("The River of Ideas", className="chart-title"),
            html.Div("Each layer flows with a tradition's scholarship.", className="chart-desc"),
            dcc.Graph(figure=_stream(), config={"displayModeBar": False}),
        ]),
        html.Div(className="chart-card", children=[
            html.Div("The Race", className="chart-title"),
            html.Div("Press play. Watch traditions accumulate year by year.", className="chart-desc"),
            dcc.Graph(figure=_race(), config={"displayModeBar": False}),
        ]),
        html.Div(className="chart-card", children=[
            html.Div("Share of the Conversation", className="chart-title"),
            html.Div("Relative weight over time. Who's gaining ground?", className="chart-desc"),
            dcc.Graph(figure=_share(), config={"displayModeBar": False}),
        ]),
    ])
