"""
Chart builders for the app to ensure consistency
"""

import plotly.graph_objects as go
from plotly.colors import qualitative


# pylint:disable = too-many-locals
def build_grouped_bar(df, unit, group_col, scen_list):
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

    fig = go.Figure()
    period_order = list(df["Period"].astype(str).unique())
    scenarios = scen_list
    groups = list(df[group_col].astype(str).unique())

    palette = qualitative.Plotly
    color_map = {g: palette[i % len(palette)] for i, g in enumerate(groups)}

    for s in scenarios:
        df_s = df[df["Scenario"] == s]
        op = 0.9 if s == scenarios[0] else 0.5

        for g in groups:
            df_sg = df_s[df_s[group_col].astype(str) == g]
            if df_sg.empty:
                continue

            fig.add_bar(
                x=df_sg["Period"].astype(str),
                y=df_sg["Value"],
                name=g if s == scenarios[0] else None,
                legendgroup=g,
                showlegend=(s == scenarios[0]),
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


# pylint:disable = too-many-locals, too-many-arguments, too-many-positional-arguments
def build_grouped_bar_better(
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
