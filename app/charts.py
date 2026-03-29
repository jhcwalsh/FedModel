"""
charts.py — Plotly chart builders for FRB/US simulation outputs.

All charts show impulse response functions (deviation from baseline)
or level paths depending on user selection.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.runner import OUTPUT_SERIES, ALL_SERIES

# Colour palette consistent with EcoOutlook
COLOURS = {
    "baseline": "#6B7280",   # grey
    "shocked": "#2563EB",    # blue
    "deviation": "#DC2626",  # red for negative, green for positive
    "positive": "#16A34A",
    "negative": "#DC2626",
    "band": "rgba(37, 99, 235, 0.12)",
}

CHART_HEIGHT = 380


def _quarters_index(df: pd.DataFrame) -> list:
    """Return index as list of strings for x-axis labels."""
    return [str(i) for i in df.index]


def deviation_chart(
    baseline: pd.DataFrame,
    shocked: pd.DataFrame,
    variable: str,
    label: str,
    unit: str = "pp deviation",
) -> go.Figure:
    """Single variable impulse response (deviation from baseline)."""
    dev = shocked[variable] - baseline[variable]
    x = _quarters_index(dev)
    colour = COLOURS["positive"] if dev.mean() >= 0 else COLOURS["negative"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=dev.values,
        name="Deviation from baseline",
        marker_color=[COLOURS["positive"] if v >= 0 else COLOURS["negative"] for v in dev.values],
        showlegend=False,
    ))
    fig.add_hline(y=0, line_color=COLOURS["baseline"], line_width=1)
    fig.update_layout(
        title=dict(text=label, font=dict(size=13)),
        xaxis_title="Quarter",
        yaxis_title=unit,
        height=CHART_HEIGHT,
        margin=dict(l=40, r=20, t=40, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
    )
    fig.update_xaxes(gridcolor="#F3F4F6", showgrid=True)
    fig.update_yaxes(gridcolor="#F3F4F6", showgrid=True, zeroline=True, zerolinecolor="#D1D5DB")
    return fig


def level_chart(
    baseline: pd.DataFrame,
    shocked: pd.DataFrame,
    variable: str,
    label: str,
    unit: str = "level",
) -> go.Figure:
    """Single variable level path: baseline vs shocked."""
    x = _quarters_index(baseline)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=baseline[variable].values,
        name="Baseline",
        line=dict(color=COLOURS["baseline"], width=2, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=x, y=shocked[variable].values,
        name="Shocked",
        line=dict(color=COLOURS["shocked"], width=2),
        fill="tonexty",
        fillcolor=COLOURS["band"],
    ))
    fig.update_layout(
        title=dict(text=label, font=dict(size=13)),
        xaxis_title="Quarter",
        yaxis_title=unit,
        height=CHART_HEIGHT,
        margin=dict(l=40, r=20, t=40, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="#F3F4F6", showgrid=True)
    fig.update_yaxes(gridcolor="#F3F4F6", showgrid=True, zeroline=True, zerolinecolor="#D1D5DB")
    return fig


def tab_charts(
    baseline: pd.DataFrame,
    shocked: pd.DataFrame,
    group_name: str,
    mode: str = "deviation",
) -> list[tuple[str, go.Figure]]:
    """
    Return list of (variable_label, figure) for all variables in a group.
    mode: "deviation" | "level"
    """
    group = OUTPUT_SERIES.get(group_name, {})
    charts = []
    for var, label in group.items():
        if var not in baseline.columns:
            continue
        if mode == "deviation":
            fig = deviation_chart(baseline, shocked, var, label)
        else:
            fig = level_chart(baseline, shocked, var, label)
        charts.append((label, fig))
    return charts


def summary_grid(
    baseline: pd.DataFrame,
    shocked: pd.DataFrame,
) -> go.Figure:
    """
    4-panel summary: GDP, Unemployment, PCE Inflation, FFR — deviations.
    Shown at top of results page.
    """
    panels = [
        ("xgdp", "Real GDP", "pp dev"),
        ("lur", "Unemployment", "pp dev"),
        ("pcxfe", "Core PCE Inflation", "pp dev"),
        ("rff", "Fed Funds Rate", "pp dev"),
    ]
    available = [(v, l, u) for v, l, u in panels if v in baseline.columns]
    n = len(available)
    if n == 0:
        return go.Figure()

    cols = 2
    rows = (n + 1) // 2
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[l for _, l, _ in available],
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )
    for i, (var, label, unit) in enumerate(available):
        row = i // cols + 1
        col = i % cols + 1
        dev = shocked[var] - baseline[var]
        x = _quarters_index(dev)
        colours = [COLOURS["positive"] if v >= 0 else COLOURS["negative"] for v in dev.values]
        fig.add_trace(
            go.Bar(x=x, y=dev.values, marker_color=colours, showlegend=False),
            row=row, col=col,
        )
    fig.update_layout(
        height=320 * rows,
        margin=dict(l=40, r=20, t=60, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        title=dict(text="Impulse Responses — Deviation from Baseline", font=dict(size=14)),
    )
    fig.update_xaxes(gridcolor="#F3F4F6", showgrid=True)
    fig.update_yaxes(gridcolor="#F3F4F6", showgrid=True, zeroline=True, zerolinecolor="#D1D5DB")
    return fig
