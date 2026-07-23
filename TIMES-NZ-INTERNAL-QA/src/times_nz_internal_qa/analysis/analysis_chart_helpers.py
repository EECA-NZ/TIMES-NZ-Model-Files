"""
Shared helpers for analysis chart modules.

Initial data cleaning and aggregating is performed in analysis.get_data. These
helpers keep chart styling, ordering, filenames, and common plot templates in
one place so subject modules can focus on their own chart definitions.

IMPORTANT NOTE: we are following the design principle where no chart has more
than FIVE colour categories. This is to reduce visual noise but requires some
categories to be aggregated slightly.
"""

# pylint: disable=wildcard-import, unused-wildcard-import, dangerous-default-value

import re
import warnings
from pathlib import Path

import pandas as pd
from plotnine import *
from plotnine.exceptions import PlotnineWarning
from times_nz_internal_qa.utilities.filepaths import ANALYSIS_RESULTS, PREP_STAGE_2

# CONSTANTS - colour settings

eeca_colours = {
    "emerald": "#41B496",
    "teal": "#447474",
    "navy": "#164057",
    "coral": "#ED6D63",
    "forest": "#3C4C49",
    "orange": "#E94E24",
    "purple": "#C346CE",
    "paleblue": "#4184A8",
}

chart_cols = [
    eeca_colours["navy"],
    eeca_colours["coral"],
    eeca_colours["forest"],
    eeca_colours["teal"],
    eeca_colours["purple"],
    eeca_colours["emerald"],
]

chart_cols_line = [
    eeca_colours["teal"],
    eeca_colours["purple"],
    eeca_colours["emerald"],
    eeca_colours["coral"],
    eeca_colours["navy"],
    eeca_colours["forest"],
]


# CONSTANTS: category orders

SCENARIO_ORDER = [
    "Steady",
    "Shift",
]

PREFERRED_ISLAND_ORDER = ["North Island", "South Island"]

PJ_TO_GWH = 277.77777778
HOURS_PER_YEAR = 8760


# HELPER FUNCTIONS
def decimal_tick_labels(values):
    """Return compact decimal labels for smaller chart values."""

    return [
        "" if pd.isna(value) else f"{value:.2f}".rstrip("0").rstrip(".")
        for value in values
    ]


def make_filename(string):
    """
    Convert an input string to snake_case and remove special characters.

    Examples:
        "Hello World" -> "hello_world"
        "My File_Name!" -> "my_file_name"
        "2024 Report (Final)" -> "2024_report_final"
    """
    cleaned = re.sub(r"[^a-zA-Z0-9\s_-]", "", string)
    words = re.split(r"[\s_-]+", cleaned.strip())
    return "_".join(word.lower() for word in words if word)


def adaptive_tick_labels(values):
    """Return compact labels with more decimals for small axis ranges."""

    valid_values = [abs(value) for value in values if not pd.isna(value)]
    max_value = max(valid_values, default=0)

    if max_value >= 100:
        decimals = 0
    elif max_value >= 10:
        decimals = 1
    elif max_value >= 1:
        decimals = 2
    elif max_value >= 0.1:
        decimals = 3
    else:
        decimals = 4

    if decimals == 0:
        return ["" if pd.isna(value) else f"{value:,.0f}" for value in values]

    return [
        "" if pd.isna(value) else f"{value:,.{decimals}f}".rstrip("0").rstrip(".")
        for value in values
    ]


def normalise_flow_chart_type(chart_type):
    """Return the canonical flow chart unit option."""

    chart_type = str(chart_type).strip().casefold()
    chart_types = {
        "gw": "GW",
        "gwh": "GWh",
    }

    if chart_type not in chart_types:
        raise ValueError("chart_type must be either 'GW' or 'GWh'")

    return chart_types[chart_type]


def convert_timeslice_flow_units(df, chart_type="GW"):
    """Convert PJ timeslice flow values to average GW or timeslice GWh."""

    chart_type = normalise_flow_chart_type(chart_type)
    df = df.copy()

    if chart_type == "GWh":
        df["Value"] = df["Value"] * PJ_TO_GWH
        df["Unit"] = "GWh"
        return df, chart_type

    yrfr = pd.read_csv(PREP_STAGE_2 / "settings/load_curves/yrfr.csv")
    df = df.merge(yrfr, on="TimeSlice", how="left")

    if df["YRFR"].isna().any():
        missing_timeslices = sorted(df.loc[df["YRFR"].isna(), "TimeSlice"].unique())
        raise ValueError(
            "Missing year fraction values for timeslices: "
            + ", ".join(missing_timeslices)
        )

    df["Value"] = df["Value"] * PJ_TO_GWH / (df["YRFR"] * HOURS_PER_YEAR)
    df["Unit"] = "GW"
    return df.drop(columns=["YRFR"]), chart_type


def save_chart(p, filename, height=4, width=6):
    """
    Convenience wrapper for save function.

    Might extend parameters for height/width etc later. Mostly just to split
    out the workflow and allow further chart customisation before saving where
    necessary.
    """

    output_file = ANALYSIS_RESULTS / "charts" / Path(filename)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"Saving \d+(\.\d+)? x \d+(\.\d+)? in image\.",
            category=PlotnineWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r"Filename: .*",
            category=PlotnineWarning,
        )
        p.save(
            output_file,
            dpi=300,
            height=height,
            width=width,
            limitsize=False,
        )


def save_chart_data(df, filename):
    """
    Save chart data under the analysis results data_for_charts directory.
    """

    output_file = ANALYSIS_RESULTS / "data_for_charts" / Path(filename)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)


def save_chart_and_data(df, p, filename, height=4, width=6):
    """
    Save a chart as PNG and its summarised data as CSV using the same filename.
    """

    filename = Path(filename)
    save_chart(p, filename.with_suffix(".png"), height=height, width=width)
    save_chart_data(df, filename.with_suffix(".csv"))


# HELPER FUNCTIONS - SORTING


def get_scenario_facet_order(df):
    """Return preferred scenario order with any extras appended."""
    print("hello please write me")
    return df


def standardise_scenario_order(df, scenario_order=SCENARIO_ORDER):
    """
    For a df with a Scenario variable, orders these according to the constant defined order.

    If the df has additional Scenarios in the Scenario variable, these are just
    ordered at the end. We may want to expand this method later depending on
    sensitivity analysis approach.
    """

    if "Scenario" not in df.columns:
        return df

    available_scenarios = df["Scenario"].dropna().unique().tolist()
    preferred_scenarios = [
        scenario for scenario in scenario_order if scenario in available_scenarios
    ]
    extra_scenarios = sorted(set(available_scenarios) - set(preferred_scenarios))
    scenarios = preferred_scenarios + extra_scenarios

    df["Scenario"] = pd.Categorical(
        df["Scenario"],
        categories=scenarios,
        ordered=True,
    )
    return df


def standardise_island_order(df, preferred_island_order=PREFERRED_ISLAND_ORDER):
    """
    For an input df with an "Island" variable, standardises the order.

    Not all data has islands so can just skip this.
    """

    if "Island" not in df.columns:
        return df

    available_islands = df["Island"].dropna().unique().tolist()
    island_order = [
        island for island in preferred_island_order if island in available_islands
    ]
    island_order.extend(sorted(set(available_islands) - set(island_order)))
    df["Island"] = pd.Categorical(df["Island"], categories=island_order, ordered=True)

    return df


# HELPER FUNCTIONS - FINAL TIDYING


def standardise_chart_data(df):
    """
    A collection of adjustments to ensure all data heading into chart functions
    has standard parameters.
    """

    df = standardise_island_order(df)
    df = standardise_scenario_order(df)

    return df


# CHART FUNCTIONS


def get_df_unit(df):
    """
    Returns the unit listed in the dataframe.

    There should only be one: fails if multiple found.
    """
    unit_list = df["Unit"].unique()
    if len(unit_list) > 1:
        raise ValueError("Multiple units found in data: please review filters")
    return unit_list[0]


def _area_facet_cols(facet_rows=None, facet_columns=None):
    """Return the facet columns used to identify separate area panels."""
    return [col for col in [facet_rows, facet_columns] if col]


# pylint:disable = too-many-locals
def _prepare_area_chart_df(df, group_var, facet_rows=None, facet_columns=None):
    """
    Add chart-only zero rows where an area series starts or ends between periods.

    The source data is left semantically sparse: only missing points directly
    adjacent to a non-zero value are added, so geom_area can draw the boundary
    down to zero.
    """
    chart_df = df.copy()
    chart_df["Period"] = chart_df["Period"].astype(int)

    facet_cols = _area_facet_cols(facet_rows, facet_columns)
    series_cols = facet_cols + [group_var]
    extra_rows = []

    if facet_cols:
        facet_period_groups = chart_df.groupby(facet_cols, observed=True, dropna=False)
        period_lookup = {
            facet_key if isinstance(facet_key, tuple) else (facet_key,): sorted(
                facet_df["Period"].dropna().unique()
            )
            for facet_key, facet_df in facet_period_groups
        }
    else:
        period_lookup = {(): sorted(chart_df["Period"].dropna().unique())}

    for series_key, series_df in chart_df.groupby(
        series_cols, observed=True, dropna=False
    ):
        series_key = series_key if isinstance(series_key, tuple) else (series_key,)
        facet_key = series_key[: len(facet_cols)]
        periods = period_lookup.get(facet_key, [])
        if not periods:
            continue

        series_df = series_df.sort_values("Period")
        values = series_df.set_index("Period")["Value"].reindex(periods)
        adjacent_nonzero = values.shift(1).fillna(0).ne(0) | values.shift(-1).fillna(
            0
        ).ne(0)
        boundary_periods = values[values.isna() & adjacent_nonzero].index
        boundary_period_set = set(boundary_periods)
        explicit_boundary_rows = (
            series_df["Period"].isin(boundary_period_set) & series_df["Value"].isna()
        )
        chart_df.loc[series_df.index[explicit_boundary_rows], "Value"] = 0

        template = series_df.iloc[0].copy()
        existing_periods = set(series_df["Period"])
        for period in boundary_periods:
            if period in existing_periods:
                continue
            row = template.copy()
            row["Period"] = period
            row["Value"] = 0
            extra_rows.append(row)

    if not extra_rows:
        return chart_df

    extra_df = pd.DataFrame(extra_rows)
    for col in chart_df.select_dtypes(include="category").columns:
        extra_df[col] = pd.Categorical(
            extra_df[col],
            categories=chart_df[col].cat.categories,
            ordered=chart_df[col].cat.ordered,
        )

    return (
        pd.concat([chart_df, extra_df], ignore_index=True)
        .sort_values(series_cols + ["Period"])
        .reset_index(drop=True)
    )


# pylint:disable = too-many-arguments, too-many-positional-arguments
def create_area_facet_chart(
    df, chart_title, group_var, facet_rows=None, facet_columns=None, palette=chart_cols
):
    """Create an area chart with optional row/column facets."""

    unit = get_df_unit(df)
    df = _prepare_area_chart_df(df, group_var, facet_rows, facet_columns)

    row_part = facet_rows if facet_rows else ""
    col_part = facet_columns if facet_columns else ""
    facet_formula = f"{row_part} ~ {col_part}"

    p = (
        ggplot(df, aes(x="Period", y="Value", fill=group_var))
        + geom_area()
        + facet_grid(facet_formula, scales="free_y")
        + labs(
            title=chart_title,
            x="Year",
            y=unit,
            fill=group_var,
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None))
        + scale_fill_manual(values=palette)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    return p


def create_scenario_facet_chart(
    df, chart_title, group_var, facet_rows=None, palette=chart_cols
):
    """
    A convenience wrapper for create_area_facet_chart to always use scenario as
    facet columns.
    """

    return create_area_facet_chart(
        df=df,
        chart_title=chart_title,
        group_var=group_var,
        facet_rows=facet_rows,
        facet_columns="Scenario",
        palette=palette,
    )


def create_scenario_line_chart(df, chart_title, yaxis_0=True):
    """
    A chart intended to compare scenarios along a single metric.

    No more than five, and the vast majority of the time will just be two.
    """

    unit = get_df_unit(df)
    min_y = min(0, df["Value"].min()) if yaxis_0 else df["Value"].min()
    max_y = df["Value"].max()
    y_range = max_y - min_y
    min_label_gap = y_range * 0.16 if y_range else 1

    label_data = (
        df.sort_values("Period")
        .groupby("Scenario", as_index=False, observed=True)
        .tail(1)
    )
    label_data["x_location"] = label_data["Period"] + 1
    label_data = label_data.sort_values("Value").reset_index(drop=True)
    label_data["label_y"] = label_data["Value"]

    for index in range(1, len(label_data)):
        previous_y = label_data.loc[index - 1, "label_y"]
        current_y = label_data.loc[index, "label_y"]
        label_data.loc[index, "label_y"] = max(current_y, previous_y + min_label_gap)

    bottom_overrun = min_y - label_data["label_y"].min()
    if bottom_overrun > 0:
        label_data["label_y"] = label_data["label_y"] + bottom_overrun

    label_padding = y_range * 0.12 if y_range else 1
    y_upper = max(max_y, label_data["label_y"].max()) + label_padding

    label_data["Label"] = (
        label_data["Scenario"].astype(str)
        + ": \n"
        + label_data["Value"].apply(lambda x: f"{x:,.2f}")
        + label_data["Unit"]
    )

    p = (
        ggplot(df, aes(x="Period", y="Value", colour="Scenario"))
        + geom_line(size=1)
        + geom_segment(
            data=label_data,
            mapping=aes(
                x="Period",
                xend="x_location",
                y="Value",
                yend="label_y",
                colour="Scenario",
            ),
            size=0.4,
        )
        + geom_label(
            data=label_data,
            mapping=aes(x="x_location", y="label_y", label="Label", fill="Scenario"),
            colour="white",
        )
        + labs(title=chart_title, x="Year", y=unit, colour="Scenario")
        + scale_x_continuous(
            breaks=[2025, 2030, 2035, 2040, 2045, 2050], limits=[2023, 2060]
        )
        + scale_y_continuous(
            labels=adaptive_tick_labels,
            limits=(0, y_upper) if yaxis_0 else (min_y, y_upper),
        )
        + scale_colour_manual(values=chart_cols_line, na_value="grey")
        + scale_fill_manual(values=chart_cols_line)
        + theme_minimal()
        + theme(legend_position="none")
    )

    return p
