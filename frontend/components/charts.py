"""
Plotly chart builders for the Streamlit frontend.

Provides:
  • Language donut chart
  • Contribution heatmap (calendar style)
  • Streak flame visual (bar chart)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go


# ── Colour palette (dark theme, matching GitHub Wrapped card) ────────────────

BG_COLOR = "rgba(0,0,0,0)"
DONUT_LINE_COLOR = "#0b0d13"
CARD_BG = "#161b22"
TEXT_COLOR = "#e6edf3"
TEXT_MUTED = "#8b949e"
GRID_COLOR = "#21262d"

LANG_COLORS_DEFAULT = [
    "#8b5cf6",  # purple
    "#38bdf8",  # cyan
    "#f59e0b",  # amber
    "#ef4444",  # red
    "#22c55e",  # green
    "#8b949e",  # grey (Other)
]

HEATMAP_COLORS = [
    [0.0, "#161b22"],
    [0.25, "#0e4429"],
    [0.5, "#006d32"],
    [0.75, "#26a641"],
    [1.0, "#39d353"],
]


def language_donut(languages: list[dict[str, Any]]) -> go.Figure:
    """
    Render a donut / pie chart of language usage.
    `languages` is a list of dicts with keys: name, percentage, color.
    """
    if not languages:
        return _empty_fig("No language data")

    names = [l["name"] for l in languages]
    values = [l["percentage"] for l in languages]
    colors = [l.get("color", LANG_COLORS_DEFAULT[i % len(LANG_COLORS_DEFAULT)])
              for i, l in enumerate(languages)]

    fig = go.Figure(
        go.Pie(
            labels=names,
            values=values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color=DONUT_LINE_COLOR, width=2)),
            textinfo="label+percent",
            textfont=dict(color=TEXT_COLOR, size=14),
            hoverinfo="label+percent+value",
        )
    )
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR),
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        height=400,
    )
    return fig


def contribution_heatmap(
    contributions: list[dict[str, Any]],
    year: int = 2025,
) -> go.Figure:
    """
    GitHub-style contribution calendar heatmap.
    `contributions` is a list of {date, count, level}.
    """
    if not contributions:
        return _empty_fig("No contribution data")

    df = pd.DataFrame(contributions)
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["weekday"] = df["date"].dt.weekday  # Mon=0, Sun=6
    df["month"] = df["date"].dt.strftime("%b")

    # Normalize count for colour mapping
    max_count = df["count"].max() or 1
    df["intensity"] = df["count"] / max_count

    fig = go.Figure(
        go.Heatmap(
            x=df["week"],
            y=df["weekday"],
            z=df["count"],
            colorscale=HEATMAP_COLORS,
            showscale=False,
            xgap=3,
            ygap=3,
            hovertemplate=(
                "Date: %{customdata}<br>"
                "Contributions: %{z}<extra></extra>"
            ),
            customdata=df["date"].dt.strftime("%Y-%m-%d"),
        )
    )

    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_MUTED, size=12),
        yaxis=dict(
            tickvals=list(range(7)),
            ticktext=weekday_labels,
            autorange="reversed",
            showgrid=False,
        ),
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
        ),
        margin=dict(t=20, b=20, l=50, r=20),
        height=220,
    )
    return fig


def streak_chart(
    longest_streak: int,
    current_streak: int,
) -> go.Figure:
    """
    Simple horizontal bar chart comparing longest vs current streak.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=["Current Streak", "Longest Streak"],
            x=[current_streak, longest_streak],
            orientation="h",
            marker=dict(
                color=["#38bdf8", "#8b5cf6"],
                line=dict(width=0),
            ),
            text=[f"{current_streak} days", f"{longest_streak} days"],
            textposition="auto",
            textfont=dict(color=TEXT_COLOR, size=16),
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR),
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            showticklabels=False,
        ),
        yaxis=dict(showgrid=False),
        margin=dict(t=10, b=10, l=120, r=20),
        height=160,
        bargap=0.35,
    )
    return fig


def hourly_radar_chart(hourly_data: list[int]) -> go.Figure:
    """
    Render a 24-hour radial (polar) chart representing commits distribution by hour.
    `hourly_data` is a list of 24 integers representing hours 0-23.
    """
    if not hourly_data or sum(hourly_data) == 0:
        return _empty_fig("No hourly activity data found")

    # The 24 hours of the day
    theta = [f"{i:02d}:00" for i in range(24)]
    # Close the loop by duplicating the first point
    r = hourly_data + [hourly_data[0]]
    theta = theta + [theta[0]]

    fig = go.Figure(
        go.Scatterpolar(
            r=r,
            theta=theta,
            fill="toself",
            fillcolor="rgba(139, 92, 246, 0.25)",
            line=dict(color="#8b5cf6", width=3),
            marker=dict(size=6, color="#38bdf8"),
            hoverinfo="theta+r",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showticklabels=True,
                tickfont=dict(color=TEXT_MUTED, size=9),
                gridcolor=GRID_COLOR,
                linecolor=GRID_COLOR,
            ),
            angularaxis=dict(
                tickfont=dict(color=TEXT_COLOR, size=10),
                gridcolor=GRID_COLOR,
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        margin=dict(t=30, b=30, l=40, r=40),
        height=320,
    )
    return fig


def _empty_fig(message: str) -> go.Figure:
    """Return a placeholder figure with a centred message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=18, color=TEXT_MUTED),
    )
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=200,
    )
    return fig
