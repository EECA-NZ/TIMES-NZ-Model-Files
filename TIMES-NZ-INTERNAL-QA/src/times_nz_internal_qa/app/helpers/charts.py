"""
Chart builders for the app to ensure consistency across all explorer sections
"""

import altair as alt
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative

alt.data_transformers.disable_max_rows()


# pylint:disable=too-many-locals
def build_grouped_bar(
    pdf: pd.DataFrame, unit: str, period_range, group_col: str, scen_list
):
    """
    Grouped+stacked bar chart in Altair.
    - Bars stack by `group_col` within each Scenario.
    - Scenarios are clustered within each Period.
    - `scen_list[0]` shown at higher opacity.
    """

    # Add numeric axis fields for continuous domain
    pdf["PeriodInt"] = pdf["Period"].astype(int)

    totals_within_vars = [v for v in pdf.columns if v not in ["Value", group_col]]

    pdf["Total"] = pdf.groupby(totals_within_vars, observed=True)["Value"].transform(
        "sum"
    )

    pdf["ShareTooltip"] = (
        ((pdf["Value"] / pdf["Total"]) * 100).map(lambda x: f"{x:.2f}")
    ) + "%"

    pdf["ValueTooltip"] = (
        pdf["Value"]
        .map(lambda x: f"{x:,.2f}")
        .str.cat(pdf["Unit"].astype(str), sep=" ")
    )

    pdf["TotalTooltip"] = (
        pdf["Total"]
        .map(lambda x: f"{x:,.2f}")
        .str.cat(pdf["Unit"].astype(str), sep=" ")
    )

    base_scen = scen_list[0] if scen_list else None

    return (
        alt.Chart(pdf)
        .mark_bar()
        .encode(
            x=alt.X(
                "PeriodInt:N",
                title="Year",
                scale=alt.Scale(domain=period_range, nice=False),
            ),
            xOffset=alt.XOffset("Scenario:N", sort=scen_list),
            y=alt.Y("Value:Q", stack="zero", title=unit),
            color=alt.Color(
                f"{group_col}:N", legend=alt.Legend(title=None, orient="top")
            ),
            opacity=alt.condition(
                alt.datum.Scenario == base_scen, alt.value(1), alt.value(0.6)
            ),
            tooltip=[
                alt.Tooltip("Scenario:N", title="Scenario"),
                alt.Tooltip("Period:N", title="Year"),
                alt.Tooltip(f"{group_col}:N", title=group_col),
                alt.Tooltip("ValueTooltip:N", title="Value"),
                alt.Tooltip("TotalTooltip:N", title="Total"),
                alt.Tooltip("ShareTooltip:N", title="Share"),
            ],
        )
        .properties(background="transparent")
    )


# pylint:disable=too-many-locals
def build_grouped_bar_timeslice(
    pdf: pd.DataFrame, unit: str, group_col: str, scen_list
):
    """
    Grouped+stacked bar chart in Altair.
    - Bars stack by `group_col` within each Scenario.
    - Scenarios are clustered within each Period.
    - `scen_list[0]` shown at higher opacity.

    Sets timeslice along the bottom, assuming data is filtered for specific year already

    """
    # Some minor adjustments for the chart tooltip?
    # possibly these need to go in the chart data function instead
    # to keep processing out of the render function?
    # we must use pandas in these functions
    totals_within_vars = [v for v in pdf.columns if v not in ["Value", group_col]]

    pdf["Total"] = pdf.groupby(totals_within_vars, observed=True)["Value"].transform(
        "sum"
    )

    pdf["ShareTooltip"] = (
        ((pdf["Value"] / pdf["Total"]) * 100).map(lambda x: f"{x:.2f}")
    ) + "%"

    pdf["ValueTooltip"] = (
        pdf["Value"]
        .map(lambda x: f"{x:,.2f}")
        .str.cat(pdf["Unit"].astype(str), sep=" ")
    )

    pdf["TotalTooltip"] = (
        pdf["Total"]
        .map(lambda x: f"{x:,.2f}")
        .str.cat(pdf["Unit"].astype(str), sep=" ")
    )

    # category orders
    # period_order = [str(p) for p in period_range]
    base_scen = scen_list[0] if scen_list else None

    chart = (
        alt.Chart(pdf)
        .mark_bar()
        .encode(
            x=alt.X("TimeSlice:N", title="Timeslice"),
            xOffset=alt.XOffset("Scenario:N", sort=scen_list),
            y=alt.Y("Value:Q", stack="zero", title=unit),
            color=alt.Color(
                f"{group_col}:N",
                legend=alt.Legend(title=None, orient="top"),
            ),
            opacity=alt.condition(
                alt.datum.Scenario == base_scen, alt.value(1), alt.value(0.6)
            ),
            tooltip=[
                alt.Tooltip("Scenario:N", title="Scenario"),
                alt.Tooltip("Period:N", title="Year"),
                alt.Tooltip(f"{group_col}:N", title=group_col),
                alt.Tooltip("ValueTooltip:N", title="Value"),
                alt.Tooltip("TotalTooltip:N", title="Total"),
                alt.Tooltip("ShareTooltip:N", title="Share"),
            ],
        )
        .properties(background="transparent")
    )

    return chart


# pylint:disable = too-many-locals, too-many-arguments, too-many-positional-arguments
def build_grouped_bar_better_plotly(
    pdf,
    unit,
    period_range,
    group_col,
    scen_list,
):
    """
    Grouped bar chart method
    Takes:
    df - input data. already processed, filtered, and grouped according to user inputs
    unit - the chart's unit, as a string
    base_cols - list of columns to always group by
    group_col - additional grouping col, used to define bar chart groups.
    scen_list - the scenario list. This is only used for formatting and ordering:
        The data should already be filtered to only include these scenarios
        Filtering does not happen in this function!
    period_range - defaults to 2023-2050 display, but can be changed.
    Returns:
    alt_chart method to wrap in a reactive decorator.
    """

    # your code here

    fig = go.Figure()
    period_order = [str(p) for p in period_range]
    groups = list(pdf[group_col].astype(str).unique())

    palette = qualitative.Plotly
    color_map = {g: palette[i % len(palette)] for i, g in enumerate(groups)}

    for s in scen_list:
        df_s = pdf[pdf["Scenario"] == s]
        op = 0.9 if s == scen_list[0] else 0.5

        for g in groups:
            df_sg = df_s[df_s[group_col].astype(str) == g]
            if df_sg.empty:
                continue

            fig.add_bar(
                x=df_sg["Period"].astype(str),
                y=df_sg["Value"],
                name=g if s == scen_list[0] else None,
                legendgroup=g,
                showlegend=(s == scen_list[0]),
                marker_color=color_map[g],
                opacity=op,
                hovertemplate=(
                    f"<b>Scenario:</b> {s}<br>"
                    "<b>Year:</b> %{x}<br>"
                    f"<b>{g}</b>: %{{y:,.2f}} {unit}<br>"
                    # remove extra tab
                    "<extra></extra>"
                ),
                offsetgroup=str(s),
                base=None,
            )

    fig.update_traces(
        hoverlabel={
            "bgcolor": "whitesmoke",
            "font_size": 12,
            "font_color": "black",
            "bordercolor": "gray",
        }
    )

    fig.update_layout(
        barmode="relative",  # stacked bars within scenario
        xaxis_title="Year",
        xaxis={
            "type": "category",
            "categoryorder": "array",
            "categoryarray": period_order,
        },
        yaxis_title=unit,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.1,
            "xanchor": "left",
            "x": 0,
            "title_text": None,
        },
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def build_grouped_line(
    pdf: pd.DataFrame,
    unit: str,
    period_range,
    group_col: str,
    scen_list,  # pylint: disable=unused-argument
):
    """
    Line chart version of `build_grouped_bar`.

    - Uses only non-zero data for plotting.
    - Displays all years in period_range on the x-axis.
    - X-axis ticks and labels are shifted horizontally by 0.5 for better centering.
    """

    # --- Preprocess ---
    line_df = pdf.copy()

    line_df["PeriodInt"] = line_df["Period"].astype(int)

    totals_within = [c for c in line_df.columns if c not in ["Value", group_col]]

    line_df["Total"] = line_df.groupby(totals_within, observed=True)["Value"].transform(
        "sum"
    )
    line_df["ShareTooltip"] = ((line_df["Value"] / line_df["Total"]) * 100).map(
        lambda x: f"{x:.2f}%"
    )

    line_df["ValueTooltip"] = (
        line_df["Value"].map(lambda x: f"{x:,.2f}") + " " + line_df["Unit"].astype(str)
    )
    line_df["TotalTooltip"] = (
        line_df["Total"].map(lambda x: f"{x:,.2f}") + " " + line_df["Unit"].astype(str)
    )

    # --- Axis setup ---
    period_min, period_max = min(period_range), max(period_range)

    # Shift ticks and labels by 0.5 horizontally
    line_df["PeriodIntShift"] = line_df["PeriodInt"] + 0.5
    tick_values = [p + 0.5 for p in period_range]

    x_axis = alt.X(
        "PeriodIntShift:Q",
        title="Year",
        scale=alt.Scale(domain=[period_min, period_max + 1], nice=False),
        axis=alt.Axis(
            values=tick_values,
            labelExpr="datum.value - 0.5",  # display real year
            format="d",
            labelAngle=-90,
            labelOverlap=False,
            grid=False,
        ),
    )

    chart = (
        alt.Chart(line_df)
        .mark_line(point=True, interpolate="linear")
        .encode(
            x=x_axis,
            y=alt.Y("Value:Q", title=unit),
            color=alt.Color(
                f"{group_col}:N",
                legend=alt.Legend(title=None, orient="top"),
            ),
            strokeDash=alt.StrokeDash(
                "Scenario:N", legend=alt.Legend(title="Scenario")
            ),
            tooltip=[
                alt.Tooltip("Scenario:N", title="Scenario"),
                alt.Tooltip("PeriodInt:Q", title="Year"),
                alt.Tooltip(f"{group_col}:N", title=group_col),
                alt.Tooltip("ValueTooltip:N", title="Value"),
                alt.Tooltip("TotalTooltip:N", title="Total"),
                alt.Tooltip("ShareTooltip:N", title="Share"),
            ],
        )
        .properties(background="transparent")
    )

    return chart
