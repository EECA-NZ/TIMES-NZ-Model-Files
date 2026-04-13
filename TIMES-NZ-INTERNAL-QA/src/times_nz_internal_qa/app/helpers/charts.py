"""
Chart builders for the app to ensure consistency across all explorer sections.
"""

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from times_nz_internal_qa.app.helpers.timeslices import (
    TIMESLICE_ORDER,
    add_timeslice_chart_columns,
    get_timeslice_label_order,
)


@dataclass(frozen=True)
class LayoutOptions:
    """Optional layout settings shared across chart types."""

    xaxis_title: str = "Year"
    extra_height: int = 0
    legend_y: float = -0.2


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


@dataclass(frozen=True)
class ScatterTraceStyle:
    """Visual configuration shared by scatter traces."""

    color: str
    showlegend: bool = True
    mode: str = "lines"
    line_width: int = 1
    dash: str | None = None
    stackgroup: str | None = None


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
    """Apply a simple shared layout and keep Plotly's default legend behavior."""
    options = options or LayoutOptions()

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="closest",
        height=520 + options.extra_height,
        margin={"l": 70, "r": 30, "t": 30, "b": 120},
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": options.legend_y,
            "xanchor": "left",
            "x": 0,
        },
        xaxis_title=options.xaxis_title,
        yaxis_title=unit,
        font={"size": 13},
    )
    return fig


def _timeslice_ticktext(labels: list[str]) -> list[str]:
    """Render timeslice labels on two lines for a more compact x-axis."""
    return [label.replace("|", "<br>") for label in labels]


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
    )


def _build_color_map(groups: list[str]) -> dict[str, str]:
    palette = qualitative.Plotly + qualitative.Safe + qualitative.Dark24
    return {group: palette[i % len(palette)] for i, group in enumerate(groups)}


def _scenario_dash_map(scen_list: list[str]) -> dict[str, str]:
    dash_cycle = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]
    return {
        scenario: dash_cycle[i % len(dash_cycle)]
        for i, scenario in enumerate(scen_list)
    }


def _get_groups(chart_df: pd.DataFrame, group_col: str) -> list[str]:
    """Return stable, sorted chart groups."""
    return sorted(chart_df[group_col].unique().tolist())


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
    plot_df["HoverValueLabel"] = plot_df["MissingData"].map(
        lambda missing: "Interpolated value" if missing else "Value"
    )
    plot_df["HoverStatus"] = plot_df["MissingData"].map(
        lambda missing: (
            "<br><b>Status:</b> non-model year placeholder" if missing else ""
        )
    )

    marker = {"color": style.color, "line": {"color": style.color, "width": 1.5}}

    return go.Bar(
        x=x_values,
        y=plot_df["Value"],
        customdata=plot_df[
            [
                "Scenario",
                "HoverValueLabel",
                "TotalTooltip",
                "ShareTooltip",
                "HoverStatus",
            ]
        ],
        name=context.group,
        legendgroup=context.group,
        showlegend=style.showlegend,
        marker=marker,
        opacity=style.opacity,
        offsetgroup=context.scenario,
        hovertemplate=(
            "<b>Scenario:</b> %{customdata[0]}<br>"
            f"<b>{style.x_label}:</b> %{{x}}<br>"
            f"<b>{context.group_col}:</b> {context.group}<br>"
            "<b>%{customdata[1]}:</b> %{y:,.2f} "
            + context.unit
            + "<br><b>Total:</b> %{customdata[2]}"
            + "<br><b>Share:</b> %{customdata[3]}"
            + "%{customdata[4]}"
            + "<extra></extra>"
        ),
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

    trace_kwargs = {
        "x": trace_df["PeriodLabel"],
        "y": trace_df["Value"],
        "customdata": trace_df[["TotalTooltip", "ShareTooltip"]],
        "mode": style.mode,
        "name": context.group,
        "legendgroup": context.group,
        "showlegend": style.showlegend,
        "line": line,
        "hovertemplate": (
            f"<b>Scenario:</b> {context.scenario}<br>"
            "<b>Year:</b> %{x}<br>"
            f"<b>{context.group_col}:</b> {context.group}<br>"
            f"<b>Value:</b> %{{y:,.2f}} {context.unit}"
            "<br><b>Total:</b> %{customdata[0]}"
            "<br><b>Share:</b> %{customdata[1]}"
            "<extra></extra>"
        ),
    }
    if style.mode == "lines+markers":
        trace_kwargs["marker"] = {"size": 7, "color": style.color}
    if style.stackgroup is not None:
        trace_kwargs["stackgroup"] = style.stackgroup

    return go.Scatter(**trace_kwargs)


def _line_hover_label(is_interpolated: bool) -> str:
    """Return a hover label for real vs interpolated line points."""
    return "Interpolated value" if is_interpolated else "Value"


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
                [
                    _line_hover_label(bool(missing)),
                    f"{value:,.2f} {context.unit}",
                    total,
                    share,
                ]
                for missing, value, total, share in zip(
                    series_df["MissingData"],
                    series_df["Value"],
                    series_df["TotalTooltip"],
                    series_df["ShareTooltip"],
                    strict=False,
                )
            ],
            hovertemplate=(
                f"<b>Scenario:</b> {context.scenario}<br>"
                "<b>Year:</b> %{x}<br>"
                f"<b>{context.group_col}:</b> {context.group}<br>"
                "<b>%{customdata[0]}:</b> %{customdata[1]}"
                "<br><b>Total:</b> %{customdata[2]}"
                "<br><b>Share:</b> %{customdata[3]}"
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
                ),
            )
        )

    fig.update_layout(
        barmode="relative",
        xaxis={
            "type": "category",
            "categoryorder": "array",
            "categoryarray": label_order,
            "tickmode": "array",
            "tickvals": label_order,
            "ticktext": _timeslice_ticktext(label_order),
        },
    )
    return _apply_standard_layout(
        fig,
        unit=unit,
        options=LayoutOptions(
            xaxis_title="Timeslice",
            extra_height=72,
            legend_y=-0.28,
        ),
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
