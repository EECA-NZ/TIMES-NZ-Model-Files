"""
Chart builders for the app to ensure consistency across all explorer sections.
"""

import math
import textwrap

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from times_nz_internal_qa.app.helpers.timeslices import (
    add_timeslice_chart_columns,
    get_timeslice_label_order,
)


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
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
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
    chart_df["Total"] = chart_df.groupby(totals_within, observed=True)["Value"].transform(
        lambda s: s.fillna(0).sum()
    )

    chart_df["ShareTooltip"] = chart_df.apply(
        lambda row: "n/a"
        if row["Total"] == 0 or pd.isna(row["Value"])
        else f"{((row['Value'] / row['Total']) * 100):.2f}%",
        axis=1,
    )
    chart_df["ValueTooltip"] = (
        chart_df["Value"].map(lambda x: "n/a" if pd.isna(x) else f"{x:,.2f}")
        + " "
        + chart_df["Unit"].astype(str)
    )
    chart_df["TotalTooltip"] = (
        chart_df["Total"].map(lambda x: f"{x:,.2f}")
        + " "
        + chart_df["Unit"].astype(str)
    )
    return chart_df


def _legend_rows(trace_count: int) -> int:
    """Estimate the number of legend rows to reserve space for."""
    items_per_row = 4
    return max(1, math.ceil(trace_count / items_per_row))


def _apply_standard_layout(
    fig: go.Figure,
    *,
    unit: str,
    legend_count: int,
    xaxis_title: str = "Year",
) -> go.Figure:
    """Shared layout so legends stay usable with many traces."""
    legend_rows = _legend_rows(legend_count)
    bottom_margin = 70 + (legend_rows * 28)
    chart_height = 420 + (legend_rows * 28)

    legend = {
        "title": {"text": None},
        "itemclick": "toggle",
        "itemdoubleclick": "toggleothers",
        "orientation": "h",
        "yanchor": "top",
        "y": -0.18,
        "xanchor": "left",
        "x": 0,
        "entrywidth": 170,
        "entrywidthmode": "pixels",
    }

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="closest",
        autosize=False,
        height=chart_height,
        margin={"l": 70, "r": 30, "t": 30, "b": bottom_margin},
        legend=legend,
        xaxis_title=xaxis_title,
        yaxis_title=unit,
        font={"size": 13},
    )
    return fig


def _build_color_map(groups: list[str]) -> dict[str, str]:
    palette = qualitative.Plotly + qualitative.Safe + qualitative.Dark24
    return {group: palette[i % len(palette)] for i, group in enumerate(groups)}


def _scenario_dash_map(scen_list: list[str]) -> dict[str, str]:
    dash_cycle = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]
    return {scenario: dash_cycle[i % len(dash_cycle)] for i, scenario in enumerate(scen_list)}


def _get_groups(chart_df: pd.DataFrame, group_col: str) -> list[str]:
    """Return stable, sorted chart groups."""
    return sorted(chart_df[group_col].unique().tolist())


def _wrap_legend_label(label: str, width: int = 24) -> str:
    """Insert line breaks into long legend labels for Plotly."""
    if len(label) <= width:
        return label
    return "<br>".join(textwrap.wrap(label, width=width, break_long_words=False))


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
    scenario: str,
    group: str,
    group_col: str,
    unit: str,
    color: str,
    opacity: float,
    showlegend: bool,
    x_label: str = "Year",
) -> go.Bar:
    """Create a bar trace with consistent hover styling."""
    plot_df = trace_df.copy()
    plot_df["HoverValueLabel"] = plot_df["MissingData"].map(
        lambda missing: "Interpolated value" if missing else "Value"
    )
    plot_df["HoverStatus"] = plot_df["MissingData"].map(
        lambda missing: "<br><b>Status:</b> non-model year placeholder"
        if missing
        else ""
    )

    marker = {"color": color, "line": {"color": color, "width": 1.5}}

    return go.Bar(
        x=x_values,
        y=plot_df["Value"],
        customdata=plot_df[["Scenario", "HoverValueLabel", "HoverStatus"]],
        name=_wrap_legend_label(group),
        legendgroup=group,
        showlegend=showlegend,
        marker=marker,
        opacity=opacity,
        offsetgroup=scenario,
        hovertemplate=(
            "<b>Scenario:</b> %{customdata[0]}<br>"
            f"<b>{x_label}:</b> %{{x}}<br>"
            f"<b>{group_col}:</b> {group}<br>"
            "<b>%{customdata[1]}:</b> %{y:,.2f} "
            + unit
            + "%{customdata[2]}"
            + "<extra></extra>"
        ),
    )


def _build_scatter_trace(
    trace_df: pd.DataFrame,
    *,
    scenario: str,
    group: str,
    group_col: str,
    unit: str,
    color: str,
    name: str,
    legendgroup: str,
    mode: str,
    line_width: int,
    showlegend: bool = True,
    dash: str | None = None,
    stackgroup: str | None = None,
) -> go.Scatter:
    """Create a scatter trace shared by line and area charts."""
    line = {"color": color, "width": line_width}
    if dash is not None:
        line["dash"] = dash

    trace_kwargs = {
        "x": trace_df["PeriodLabel"],
        "y": trace_df["Value"],
        "mode": mode,
        "name": _wrap_legend_label(name),
        "legendgroup": legendgroup,
        "showlegend": showlegend,
        "line": line,
        "hovertemplate": (
            f"<b>Scenario:</b> {scenario}<br>"
            "<b>Year:</b> %{x}<br>"
            f"<b>{group_col}:</b> {group}<br>"
            f"<b>Value:</b> %{{y:,.2f}} {unit}<extra></extra>"
        ),
    }
    if mode == "lines+markers":
        trace_kwargs["marker"] = {"size": 7, "color": color}
    if stackgroup is not None:
        trace_kwargs["stackgroup"] = stackgroup

    return go.Scatter(**trace_kwargs)


def _line_hover_label(is_interpolated: bool) -> str:
    """Return a hover label for real vs interpolated line points."""
    return "Interpolated value" if is_interpolated else "Value"


def _add_line_series(
    fig: go.Figure,
    trace_df: pd.DataFrame,
    *,
    scenario: str,
    group: str,
    group_col: str,
    unit: str,
    color: str,
    opacity: float,
    showlegend: bool,
):
    """Add a line series with point-specific interpolation styling and hover."""
    series_df = trace_df.sort_values("PeriodLabel").copy()
    if series_df.empty:
        return

    legend_name = _wrap_legend_label(group)
    fig.add_trace(
        go.Scatter(
            x=series_df["PeriodLabel"],
            y=series_df["Value"],
            mode="lines+markers",
            name=legend_name,
            legendgroup=group,
            showlegend=showlegend,
            line={"color": color, "width": 2},
            marker={
                "size": 7,
                "color": [
                    "rgba(255,255,255,1)" if missing else color
                    for missing in series_df["MissingData"]
                ],
                "opacity": opacity,
                "line": {
                    "color": [
                        color for _ in series_df["MissingData"]
                    ],
                    "width": [1 for _ in series_df["MissingData"]],
                },
                "symbol": ["circle" for _ in series_df["MissingData"]],
            },
            customdata=[
                [_line_hover_label(bool(missing)), f"{value:,.2f} {unit}"]
                for missing, value in zip(
                    series_df["MissingData"], series_df["Value"], strict=False
                )
            ],
            hovertemplate=(
                f"<b>Scenario:</b> {scenario}<br>"
                "<b>Year:</b> %{x}<br>"
                f"<b>{group_col}:</b> {group}<br>"
                "<b>%{customdata[0]}:</b> %{customdata[1]}"
                "<extra></extra>"
            ),
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
    period_order = [str(p) for p in period_range]
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
                scenario=scenario,
                group=group,
                group_col=group_col,
                unit=unit,
                color=color_map[group],
                opacity=opacity,
                showlegend=scenario == base_scenario,
            )
        )

    fig.update_layout(
        barmode="relative",
        xaxis={
            "type": "category",
            "categoryorder": "array",
            "categoryarray": period_order,
        },
    )
    return _apply_standard_layout(fig, unit=unit, legend_count=len(groups) + 1)


def build_grouped_bar_timeslice(
    pdf: pd.DataFrame, unit: str, group_col: str, scen_list
) -> go.Figure:
    """Grouped + stacked timeslice bar chart using Plotly."""
    chart_df = _prepare_chart_df(pdf, group_col)
    chart_df = add_timeslice_chart_columns(chart_df)
    label_order = get_timeslice_label_order()
    chart_df["TimeSliceLabel"] = pd.Categorical(
        chart_df["TimeSliceLabel"], categories=label_order, ordered=True
    )

    groups = _get_groups(chart_df, group_col)
    color_map = _build_color_map(groups)
    base_scenario = scen_list[0] if scen_list else None
    fig = go.Figure()

    for scenario, group, trace_df in _iter_series(
        chart_df, group_col, scen_list, sort_col="TimeSliceLabel"
    ):
        opacity = 0.95 if scenario == base_scenario else 0.55
        fig.add_trace(
            _build_bar_trace(
                trace_df,
                x_values=trace_df["TimeSliceLabel"].astype(str),
                scenario=scenario,
                group=group,
                group_col=group_col,
                unit=unit,
                color=color_map[group],
                opacity=opacity,
                showlegend=scenario == base_scenario,
                x_label="Timeslice",
            )
        )

    fig.update_layout(
        barmode="relative",
        xaxis={"type": "category", "categoryorder": "array", "categoryarray": label_order},
    )
    return _apply_standard_layout(
        fig, unit=unit, legend_count=len(groups), xaxis_title="Timeslice"
    )


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
            scenario=scenario,
            group=group,
            group_col=group_col,
            unit=unit,
            color=color_map[group],
            opacity=0.95 if scenario == base_scenario else 0.55,
            showlegend=scenario == base_scenario,
        )

    fig.update_xaxes(type="category", categoryorder="array", categoryarray=[str(p) for p in period_range])
    return _apply_standard_layout(fig, unit=unit, legend_count=len(groups))


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
    period_order = [str(p) for p in period_range]
    fig = go.Figure()
    scenario = scen_list[0] if scen_list else chart_df["Scenario"].iloc[0]
    for _, group, trace_df in _iter_series(
        chart_df, group_col, [scenario], sort_col="PeriodLabel", dropna=True
    ):
        fig.add_trace(
            _build_scatter_trace(
                trace_df,
                scenario=scenario,
                group=group,
                group_col=group_col,
                unit=unit,
                color=color_map[group],
                name=group,
                legendgroup=group,
                mode="lines",
                line_width=1,
                stackgroup="stack",
            )
        )
    fig.update_xaxes(
        type="category", categoryorder="array", categoryarray=period_order
    )
    return _apply_standard_layout(fig, unit=unit, legend_count=len(groups))
