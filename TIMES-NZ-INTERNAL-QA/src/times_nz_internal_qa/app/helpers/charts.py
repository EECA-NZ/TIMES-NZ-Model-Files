"""
Chart builders for the app to ensure consistency across all explorer sections.
"""

from dataclasses import dataclass
from html import escape

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from times_nz_internal_qa.app.helpers.timeslices import (
    TIMESLICE_ORDER,
    add_timeslice_chart_columns,
)


@dataclass(frozen=True)
class LayoutOptions:
    """Optional layout settings shared across chart types."""

    xaxis_title: str = "Year"
    height: int = 560
    bottom_margin: int = 140
    legend_y: float = -0.18
    legend_max_height: float = 0.12


DEFAULT_LAYOUT_OPTIONS = LayoutOptions()


@dataclass(frozen=True)
class SeriesContext:
    """Metadata shared across traces for one scenario/group series."""

    scenario: str
    group: str
    group_col: str
    unit: str


@dataclass(frozen=True)
class BarTraceStyle:
    """Visual configuration for bar traces."""

    color: str
    opacity: float = 1.0
    showlegend: bool = True
    x_label: str = "Year"
    x_hover_col: str | None = None


@dataclass(frozen=True)
class ScatterTraceStyle:
    """Visual configuration shared by scatter traces."""

    color: str
    showlegend: bool = True
    mode: str = "lines"
    line_width: int = 1
    dash: str | None = None
    stackgroup: str | None = None


TIMESLICE_LAYOUT_OPTIONS = LayoutOptions(
    xaxis_title="",
    height=700,
    bottom_margin=60,
    legend_y=-0.40,
    legend_max_height=0.10,
)
CHART_FONT_FAMILY = "Roboto"
CHART_FONT_WEIGHT = 425
CHART_VALUE_FONT_SIZE = 14
CHART_HEADER_FONT_SIZE = 15

BRAND_COLOURS = {
    "Moss Green": "#05422D",  # main brand colours
    "Sea Blue": "#0A3C61",
    "Sunset Purple": "#5A1A5E",
    "Fresh Teal": "#2ADEA9",
    "Sky Blue": "#74DCDB",
    "Dusky Lilac": "#D2B7FE",
    "Moss Green 600": "#376856",  # lighter variants
    "Sea Blue 600": "#3C6280",
    "Sunset Purple 600": "#7B467E",
    "Fresh Teal 300": "#57E5BA",
    "Sky Blue 300": "#91E2E2",
    "Dusky Lilac 300": "#D7C2F5",
}
BRAND_DISCRETE_SEQUENCE = []


def _chart_font(size: int) -> dict[str, str | int]:
    """Return the standard chart font configuration."""
    return {
        "family": CHART_FONT_FAMILY,
        "size": size,
        "weight": CHART_FONT_WEIGHT,
    }


def build_empty_figure(message: str) -> go.Figure:
    """Return a lightweight placeholder figure for empty states."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(
        template="plotly_white",
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=_chart_font(CHART_VALUE_FONT_SIZE),
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    return fig


def _prepare_chart_df(pdf: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Add tooltip and ordering columns used across multiple chart types."""
    chart_df = pdf.copy()
    chart_df["PeriodLabel"] = chart_df["Period"].astype(str)
    chart_df[group_col] = chart_df[group_col].astype(str)
    chart_df["Scenario"] = chart_df["Scenario"].astype(str)
    chart_df["MissingData"] = chart_df["MissingData"].fillna(False).astype(bool)

    totals_within = [
        c
        for c in chart_df.columns
        if c not in ["Value", group_col, "MissingData", "PeriodLabel"]
    ]
    chart_df["Total"] = chart_df.groupby(totals_within, observed=True)[
        "Value"
    ].transform(lambda s: s.fillna(0).sum())

    valid_share = chart_df["Total"].ne(0) & chart_df["Value"].notna()
    share_values = (chart_df["Value"] / chart_df["Total"]) * 100
    chart_df["ShareTooltip"] = "n/a"
    chart_df.loc[valid_share, "ShareTooltip"] = share_values.loc[valid_share].map(
        lambda x: f"{x:.2f}%"
    )

    unit_series = chart_df["Unit"].astype(str)
    value_text = chart_df["Value"].map(lambda x: f"{x:,.2f}")
    chart_df["ValueTooltip"] = "n/a"
    valid_value = chart_df["Value"].notna()
    chart_df.loc[valid_value, "ValueTooltip"] = (
        value_text.loc[valid_value] + " " + unit_series.loc[valid_value]
    )
    chart_df["TotalTooltip"] = (
        chart_df["Total"].map(lambda x: f"{x:,.2f}") + " " + unit_series
    )
    return chart_df


def _apply_standard_layout(
    fig: go.Figure,
    *,
    unit: str,
    options: LayoutOptions | None = None,
) -> go.Figure:
    """Apply the shared layout used across explorer charts."""
    options = options or DEFAULT_LAYOUT_OPTIONS

    fig.update_layout(
        template="plotly_white",
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="closest",
        hoverdistance=100,
        height=options.height,
        margin={
            "l": 70,
            "r": 30,
            "t": 30,
            "b": options.bottom_margin,
        },
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": options.legend_y,
            "xanchor": "center",
            "x": 0.5,
            "maxheight": options.legend_max_height,
            "font": _chart_font(CHART_VALUE_FONT_SIZE),
        },
        xaxis_title=options.xaxis_title,
        yaxis_title=unit,
        font=_chart_font(CHART_VALUE_FONT_SIZE),
    )
    fig.update_xaxes(
        tickfont=_chart_font(CHART_VALUE_FONT_SIZE),
        title_font=_chart_font(CHART_HEADER_FONT_SIZE),
    )
    fig.update_yaxes(
        tickfont=_chart_font(CHART_VALUE_FONT_SIZE),
        title_font=_chart_font(CHART_HEADER_FONT_SIZE),
    )
    return fig


def _timeslice_multicategory_x(trace_df: pd.DataFrame):
    """Build a 2-tier Plotly multicategory x-axis for timeslice charts."""
    return [
        trace_df["Season"].astype(str).tolist(),
        trace_df["TimeSliceDayTime"].fillna("").astype(str).tolist(),
    ]


def _apply_period_axis(fig: go.Figure, period_range) -> None:
    """Force all model display years to appear on year-based charts."""
    period_order = [str(p) for p in period_range]
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=period_order,
        tickmode="array",
        tickvals=period_order,
        ticktext=period_order,
        range=[-0.5, len(period_order) - 0.5],
    )


def _build_color_map(groups: list[str]) -> dict[str, str]:
    palette = (
        BRAND_DISCRETE_SEQUENCE
        if len(BRAND_DISCRETE_SEQUENCE) > 0
        else qualitative.Prism + qualitative.Vivid + qualitative.Safe
    )
    return {group: palette[i % len(palette)] for i, group in enumerate(groups)}


def _get_groups(chart_df: pd.DataFrame, group_col: str) -> list[str]:
    """Return stable, sorted chart groups."""
    return sorted(chart_df[group_col].unique().tolist())


def _tooltip_row(label: str, value: str) -> str:
    """Build one row of custom hover HTML."""
    return (
        '<div class="chart-hover-row">'
        f'<span class="chart-hover-label">{escape(str(label))}</span>'
        f'<span class="chart-hover-value">{escape(str(value))}</span>'
        "</div>"
    )


def _tooltip_html(rows: list[tuple[str, str]], status: str | None = None) -> str:
    """Build Altair-like tooltip HTML shared across traces."""
    html = '<div class="chart-hover-card">'
    html += "".join(_tooltip_row(label, value) for label, value in rows)
    if status:
        html += f'<div class="chart-hover-status">{escape(str(status))}</div>'
    html += "</div>"
    return html


def _iter_series(
    chart_df: pd.DataFrame,
    group_col: str,
    scen_list,
    *,
    sort_col: str,
    dropna: bool = False,
):
    """Yield scenario/group slices in a consistent order."""
    groups = _get_groups(chart_df, group_col)
    for scenario in scen_list:
        scenario_df = chart_df[chart_df["Scenario"] == scenario]
        for group in groups:
            trace_df = (
                scenario_df[scenario_df[group_col] == group]
                .sort_values(sort_col)
                .copy()
            )
            if dropna:
                trace_df = trace_df[trace_df["Value"].notna()]
            if not trace_df.empty:
                yield scenario, group, trace_df


def _build_bar_trace(
    trace_df: pd.DataFrame,
    *,
    x_values,
    context: SeriesContext,
    style: BarTraceStyle,
) -> go.Bar:
    """Create a bar trace with consistent hover styling."""
    plot_df = trace_df.copy()
    plot_df["HoverValueLabel"] = "Value"
    plot_df["HoverStatus"] = plot_df["MissingData"].map(
        lambda missing: "Non-model year: value interpolated" if missing else ""
    )
    plot_df["TooltipHtml"] = [
        _tooltip_html(
            [
                ("Scenario", scenario),
                (
                    style.x_label,
                    x_hover if style.x_hover_col else x_value,
                ),
                (context.group_col, context.group),
                (hover_label, f"{value:,.2f} {context.unit}"),
                ("Total", total),
                ("Share", share),
            ],
            status=status or None,
        )
        for scenario, x_hover, x_value, hover_label, value, total, share, status in zip(
            plot_df["Scenario"],
            (
                plot_df[style.x_hover_col].astype(str)
                if style.x_hover_col
                else plot_df["PeriodLabel"]
            ),
            plot_df["PeriodLabel"],
            plot_df["HoverValueLabel"],
            plot_df["Value"],
            plot_df["TotalTooltip"],
            plot_df["ShareTooltip"],
            plot_df["HoverStatus"],
            strict=False,
        )
    ]

    marker = {"color": style.color, "line": {"color": style.color, "width": 1.5}}

    return go.Bar(
        x=x_values,
        y=plot_df["Value"],
        customdata=plot_df["TooltipHtml"],
        hoverinfo="none",
        name=context.group,
        legendgroup=context.group,
        showlegend=style.showlegend,
        marker=marker,
        opacity=style.opacity,
        offsetgroup=context.scenario,
    )


def _build_scatter_trace(
    trace_df: pd.DataFrame,
    *,
    context: SeriesContext,
    style: ScatterTraceStyle,
) -> go.Scatter:
    """Create a scatter trace shared by line and area charts."""
    line = {"color": style.color, "width": style.line_width}
    if style.dash is not None:
        line["dash"] = style.dash

    tooltip_rows = [
        _tooltip_html(
            [
                ("Scenario", context.scenario),
                ("Year", year),
                (context.group_col, context.group),
                ("Value", f"{value:,.2f} {context.unit}"),
                ("Total", total),
                ("Share", share),
            ]
        )
        for year, value, total, share in zip(
            trace_df["PeriodLabel"],
            trace_df["Value"],
            trace_df["TotalTooltip"],
            trace_df["ShareTooltip"],
            strict=False,
        )
    ]

    trace_kwargs = {
        "x": trace_df["PeriodLabel"],
        "y": trace_df["Value"],
        "customdata": tooltip_rows,
        "hoverinfo": "none",
        "mode": style.mode,
        "name": context.group,
        "legendgroup": context.group,
        "showlegend": style.showlegend,
        "line": line,
    }
    if style.mode == "lines+markers":
        trace_kwargs["marker"] = {"size": 7, "color": style.color}
    if style.stackgroup is not None:
        trace_kwargs["stackgroup"] = style.stackgroup
        trace_kwargs["hoveron"] = "points"

    return go.Scatter(**trace_kwargs)


def _add_line_series(
    fig: go.Figure,
    trace_df: pd.DataFrame,
    *,
    context: SeriesContext,
    style: BarTraceStyle,
):
    """Add a line series with point-specific interpolation styling and hover."""
    series_df = trace_df.sort_values("PeriodLabel").copy()
    if series_df.empty:
        return

    fig.add_trace(
        go.Scatter(
            x=series_df["PeriodLabel"],
            y=series_df["Value"],
            mode="lines+markers",
            hoverinfo="none",
            name=context.group,
            legendgroup=context.group,
            showlegend=style.showlegend,
            line={"color": style.color, "width": 2},
            marker={
                "size": 7,
                "color": [
                    "rgba(255,255,255,1)" if missing else style.color
                    for missing in series_df["MissingData"]
                ],
                "opacity": style.opacity,
                "line": {
                    "color": [style.color for _ in series_df["MissingData"]],
                    "width": [1 for _ in series_df["MissingData"]],
                },
                "symbol": ["circle" for _ in series_df["MissingData"]],
            },
            customdata=[
                _tooltip_html(
                    [
                        ("Scenario", context.scenario),
                        ("Year", year),
                        (context.group_col, context.group),
                        (
                            "Value",
                            f"{value:,.2f} {context.unit}",
                        ),
                        ("Total", total),
                        ("Share", share),
                    ],
                    status="Non-model year: value interpolated" if missing else None,
                )
                for missing, year, value, total, share in zip(
                    series_df["MissingData"],
                    series_df["PeriodLabel"],
                    series_df["Value"],
                    series_df["TotalTooltip"],
                    series_df["ShareTooltip"],
                    strict=False,
                )
            ],
        )
    )


def build_grouped_bar(
    pdf: pd.DataFrame,
    unit: str,
    period_range,
    group_col: str,
    scen_list,
) -> go.Figure:
    """
    Grouped + stacked bar chart using Plotly.
    Legend entries are interactive by default in Plotly.
    """
    chart_df = _prepare_chart_df(pdf, group_col)
    groups = _get_groups(chart_df, group_col)
    color_map = _build_color_map(groups)
    base_scenario = scen_list[0] if scen_list else None

    fig = go.Figure()

    for scenario, group, trace_df in _iter_series(
        chart_df, group_col, scen_list, sort_col="PeriodLabel"
    ):
        opacity = 0.95 if scenario == base_scenario else 0.55
        trace_df = trace_df[trace_df["Value"].notna()]
        if trace_df.empty:
            continue
        fig.add_trace(
            _build_bar_trace(
                trace_df,
                x_values=trace_df["PeriodLabel"],
                context=SeriesContext(
                    scenario=scenario,
                    group=group,
                    group_col=group_col,
                    unit=unit,
                ),
                style=BarTraceStyle(
                    color=color_map[group],
                    opacity=opacity,
                    showlegend=scenario == base_scenario,
                ),
            )
        )

    fig.update_layout(
        barmode="relative",
    )
    _apply_period_axis(fig, period_range)
    return _apply_standard_layout(fig, unit=unit)


def build_grouped_bar_timeslice(
    pdf: pd.DataFrame, unit: str, group_col: str, scen_list
) -> go.Figure:
    """Grouped + stacked timeslice bar chart using Plotly."""
    chart_df = _prepare_chart_df(pdf, group_col)
    chart_df = chart_df[chart_df["TimeSlice"].astype(str).isin(TIMESLICE_ORDER)].copy()
    if chart_df.empty:
        return build_empty_figure("No valid timeslice data available")
    chart_df = add_timeslice_chart_columns(chart_df)
    chart_df["TimeSlice"] = pd.Categorical(
        chart_df["TimeSlice"], categories=TIMESLICE_ORDER, ordered=True
    )

    groups = _get_groups(chart_df, group_col)
    color_map = _build_color_map(groups)
    base_scenario = scen_list[0] if scen_list else None
    fig = go.Figure()

    for scenario, group, trace_df in _iter_series(
        chart_df, group_col, scen_list, sort_col="TimeSlice"
    ):
        opacity = 0.95 if scenario == base_scenario else 0.55
        fig.add_trace(
            _build_bar_trace(
                trace_df,
                x_values=_timeslice_multicategory_x(trace_df),
                context=SeriesContext(
                    scenario=scenario,
                    group=group,
                    group_col=group_col,
                    unit=unit,
                ),
                style=BarTraceStyle(
                    color=color_map[group],
                    opacity=opacity,
                    showlegend=scenario == base_scenario,
                    x_label="Timeslice",
                    x_hover_col="TimeSliceLongLabel",
                ),
            )
        )

    fig.update_xaxes(type="multicategory")

    fig.update_layout(
        barmode="relative",
    )
    fig = _apply_standard_layout(
        fig,
        unit=unit,
        options=TIMESLICE_LAYOUT_OPTIONS,
    )
    fig.update_xaxes(
        automargin=True,
        tickfont=_chart_font(12),
    )
    return fig


def build_grouped_line(
    pdf: pd.DataFrame,
    unit: str,
    period_range,
    group_col: str,
    scen_list,
) -> go.Figure:
    """Line chart version of grouped charts using Plotly."""
    chart_df = _prepare_chart_df(pdf, group_col)
    chart_df = chart_df.sort_values(["Scenario", group_col, "PeriodLabel"])
    groups = _get_groups(chart_df, group_col)
    color_map = _build_color_map(groups)

    fig = go.Figure()
    base_scenario = scen_list[0] if scen_list else None

    for scenario, group, trace_df in _iter_series(
        chart_df, group_col, scen_list, sort_col="PeriodLabel", dropna=True
    ):
        _add_line_series(
            fig,
            trace_df,
            context=SeriesContext(
                scenario=scenario,
                group=group,
                group_col=group_col,
                unit=unit,
            ),
            style=BarTraceStyle(
                color=color_map[group],
                opacity=0.95 if scenario == base_scenario else 0.55,
                showlegend=scenario == base_scenario,
            ),
        )

    _apply_period_axis(fig, period_range)
    return _apply_standard_layout(fig, unit=unit)


def build_grouped_area(
    pdf: pd.DataFrame,
    unit: str,
    period_range,
    group_col: str,
    scen_list,
) -> go.Figure:
    """Stacked area chart for a single scenario."""
    chart_df = _prepare_chart_df(pdf, group_col)
    chart_df = chart_df.sort_values(["Scenario", "PeriodLabel", group_col])
    groups = _get_groups(chart_df, group_col)
    color_map = _build_color_map(groups)
    fig = go.Figure()
    scenario = scen_list[0] if scen_list else chart_df["Scenario"].iloc[0]
    for _, group, trace_df in _iter_series(
        chart_df, group_col, [scenario], sort_col="PeriodLabel", dropna=True
    ):
        fig.add_trace(
            _build_scatter_trace(
                trace_df,
                context=SeriesContext(
                    scenario=scenario,
                    group=group,
                    group_col=group_col,
                    unit=unit,
                ),
                style=ScatterTraceStyle(
                    color=color_map[group],
                    mode="lines",
                    line_width=1,
                    stackgroup="stack",
                ),
            )
        )
    _apply_period_axis(fig, period_range)
    return _apply_standard_layout(fig, unit=unit)
