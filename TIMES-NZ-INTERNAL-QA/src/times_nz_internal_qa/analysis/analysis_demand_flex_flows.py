"""Demand-flex flow analysis charts."""

from functools import lru_cache

import pandas as pd
import times_nz_internal_qa.analysis.get_data as chart_data

# isort is clashing with pylint on what order these should go in, so disable pylint
# pylint:disable = wildcard-import, unused-wildcard-import, wrong-import-order
from plotnine import *
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    adaptive_tick_labels,
    chart_cols,
    convert_timeslice_flow_units,
    save_chart_and_data,
    standardise_chart_data,
)
from times_nz_internal_qa.app.helpers.timeslices import (
    DAY_TYPE_LABELS,
    DAY_TYPE_ORDER,
    SEASON_LABELS,
    SEASON_ORDER,
    TIME_OF_DAY_ORDER,
    TIMESLICE_ORDER,
    add_timeslice_chart_columns,
)
from times_nz_internal_qa.utilities.filepaths import SCENARIO_FILES

FLEX_UNDERLYING_PROCESS_MAP = {
    "DD-S_HEAT-FLEX": "RES-DD-ELC-HPSH-S_HEAT",
    "JD-S_HEAT-FLEX": "RES-JD-ELC-HPSH-S_HEAT",
    "DD-WH_LOW-FLEX": "RES-DD-ELC-HWATER_C-WH_LOW",
    "JD-WH_LOW-FLEX": "RES-JD-ELC-HWATER_C-WH_LOW",
    "DD-WH_LOW-SMART": "RES-DD-ELC-HWATER_C-WH_LOW",
    "JD-WH_LOW-SMART": "RES-JD-ELC-HWATER_C-WH_LOW",
}

NEGATIVE_FLOW_LABELS = (
    "Demand flex input",
    "Demand flex decrease",
    "Demand flex down",
    "Demand decrease",
    "Demand reduction",
    "Flexible demand decrease",
    "Flexible demand down",
)


def create_demand_flex_flows(group_by_col="Technology"):
    """Demand-flex flows by readable timeslice."""

    df = chart_data.get_times_data("demand_flex_flows.parquet")

    grain_vars = [
        "Scenario",
        "Variable",
        "Process",
        "Period",
        "Region",
        "TimeSlice",
        "Unit",
    ]

    group_vars = list(dict.fromkeys(grain_vars + [group_by_col]))

    df = df.groupby(group_vars)["Value"].sum().reset_index()
    df = add_timeslice_chart_columns(df)

    return df


@lru_cache(maxsize=1)
def _get_underlying_process_efficiencies():
    """Return raw output/input efficiencies for flex-linked residential technologies."""

    underlying_processes = sorted(set(FLEX_UNDERLYING_PROCESS_MAP.values()))
    usecols = [
        "Attribute",
        "Commodity",
        "Process",
        "Period",
        "Region",
        "TimeSlice",
        "PV",
    ]
    results = []
    for scenario in chart_data.STANDARD_SCENARIO_MAP:
        df = pd.read_csv(
            SCENARIO_FILES / f"{scenario}.csv", usecols=usecols, low_memory=False
        )
        df["Scenario"] = chart_data.STANDARD_SCENARIO_MAP.get(scenario, scenario)
        results.append(df)

    df = pd.concat(results, ignore_index=True)
    df = df[df["Process"].isin(underlying_processes)]
    df = df[df["Attribute"].isin(["VAR_FIn", "VAR_FOut"])]
    df["Period"] = df["Period"].astype(int)

    grain = ["Scenario", "Process", "Period", "Region", "TimeSlice"]
    df = df.groupby(grain + ["Attribute"])["PV"].sum().reset_index()
    df = df.pivot(index=grain, columns="Attribute", values="PV").reset_index()

    missing = df["VAR_FIn"].isna() | df["VAR_FOut"].isna()
    if missing.any():
        missing_rows = df.loc[missing, grain].drop_duplicates()
        raise ValueError(
            "Missing underlying input/output rows for demand-flex efficiency:\n"
            + missing_rows.to_string(index=False)
        )

    df["Efficiency"] = df["VAR_FOut"] / df["VAR_FIn"]
    df = df.rename(columns={"Process": "UnderlyingProcess"})
    return df[grain[:1] + ["UnderlyingProcess"] + grain[2:] + ["Efficiency"]]


def _convert_demand_flex_to_equivalent_input(chart_df):
    """Convert flex service/heat flows to equivalent residential electricity input."""

    chart_df = chart_df.copy()
    chart_df["UnderlyingProcess"] = chart_df["Process"].map(FLEX_UNDERLYING_PROCESS_MAP)

    missing_processes = chart_df.loc[
        chart_df["UnderlyingProcess"].isna(), "Process"
    ].unique()
    if len(missing_processes) > 0:
        raise ValueError(
            "Missing underlying technology mapping for demand-flex processes: "
            + ", ".join(sorted(missing_processes))
        )

    efficiencies = _get_underlying_process_efficiencies()
    merge_cols = [
        "Scenario",
        "UnderlyingProcess",
        "Period",
        "Region",
        "TimeSlice",
    ]
    chart_df = chart_df.merge(efficiencies, on=merge_cols, how="left")

    if chart_df["Efficiency"].isna().any():
        missing_rows = chart_df.loc[
            chart_df["Efficiency"].isna(), merge_cols
        ].drop_duplicates()
        raise ValueError(
            "Missing efficiency values for demand-flex rows:\n"
            + missing_rows.to_string(index=False)
        )

    chart_df["Value"] = chart_df["Value"] / chart_df["Efficiency"]
    chart_df = chart_df.drop(columns=["UnderlyingProcess", "Efficiency"])
    return chart_df


def _aggregate_demand_flex_chart_group(chart_df, group_by_col):
    """Aggregate converted flex rows back to the selected chart grouping."""

    group_cols = [
        "Scenario",
        "Variable",
        "Period",
        "TimeSlice",
        "Unit",
        group_by_col,
    ]
    group_cols = list(dict.fromkeys(group_cols))
    return chart_df.groupby(group_cols)["Value"].sum().reset_index()


def _complete_demand_flex_flow_timeslices(
    df, year, group_by_col="Technology", unit="GW"
):
    """Add zero rows so every flow/group has every model timeslice."""

    timeslices = [timeslice for timeslice in TIMESLICE_ORDER if timeslice != "ANNUAL"]
    group_cols = ["Scenario", "Variable", group_by_col]
    groups = df[group_cols].drop_duplicates()
    complete_index = pd.MultiIndex.from_frame(groups).to_frame(index=False)
    complete_index = complete_index.merge(
        pd.DataFrame({"TimeSlice": timeslices}),
        how="cross",
    )
    complete_index["Period"] = year

    chart_df = complete_index.merge(
        df[group_cols + ["Period", "TimeSlice", "Value"]],
        on=group_cols + ["Period", "TimeSlice"],
        how="left",
    )
    chart_df["Value"] = chart_df["Value"].fillna(0)
    chart_df["Unit"] = unit
    return add_timeslice_chart_columns(chart_df)


def _get_demand_flex_flow_axis_labels(chart_df):
    """Return compact, season-tiered x-axis labels and season dividers."""

    day_type_labels = {
        DAY_TYPE_LABELS["WK"]: "Wk",
        DAY_TYPE_LABELS["WE"]: "We",
    }
    season_label_positions = {}
    season_starts = []
    for season_index, season in enumerate(SEASON_ORDER):
        season_start = season_index * len(DAY_TYPE_ORDER) * len(TIME_OF_DAY_ORDER)
        season_starts.append(season_start - 0.5)
        season_label_positions[season_start + 2] = SEASON_LABELS[season]

    x_labels = (
        chart_df[
            [
                "TimeSliceOrder",
                "DayType",
                "TimeOfDay",
            ]
        ]
        .drop_duplicates()
        .sort_values("TimeSliceOrder")
        .reset_index(drop=True)
    )
    x_labels["SeasonAxisLabel"] = x_labels["TimeSliceOrder"].map(season_label_positions)
    x_labels["SeasonAxisLabel"] = x_labels["SeasonAxisLabel"].fillna("")
    x_labels["DayTimeAxisLabel"] = (
        x_labels["DayType"].map(day_type_labels).fillna(x_labels["DayType"])
        + "\n"
        + x_labels["TimeOfDay"].astype(str)
        + "\n\n"
        + x_labels["SeasonAxisLabel"]
    )

    return x_labels, season_starts


def _get_negative_flow_mask(chart_df, negative_flow_labels):
    """Identify demand-flex flow variables that should plot below zero."""

    negative_flow_labels = {label.casefold() for label in negative_flow_labels}
    variable_labels = chart_df["Variable"].astype(str).str.casefold()
    return variable_labels.isin(negative_flow_labels)


def create_demand_flex_flows_chart(
    df=None,
    year=2050,
    group_by_col="Technology",
    chart_type="GW",
    negative_flow_labels=NEGATIVE_FLOW_LABELS,
):
    """Create demand-flex flow chart for a single model year."""

    if df is None:
        df = create_demand_flex_flows(group_by_col=group_by_col)

    df = standardise_chart_data(df)

    chart_df = df[df["Period"].astype(int) == year].copy()
    chart_df = chart_df[chart_df["TimeSlice"].astype(str).isin(TIMESLICE_ORDER)].copy()

    if chart_df.empty:
        raise ValueError(f"No demand-flex flow data found for {year}")

    negative_flow_mask = _get_negative_flow_mask(chart_df, negative_flow_labels)
    chart_df.loc[negative_flow_mask, "Value"] = -chart_df.loc[
        negative_flow_mask, "Value"
    ]
    chart_df = _convert_demand_flex_to_equivalent_input(chart_df)
    chart_df = _aggregate_demand_flex_chart_group(chart_df, group_by_col)
    chart_df, chart_type = convert_timeslice_flow_units(chart_df, chart_type=chart_type)

    chart_df = _complete_demand_flex_flow_timeslices(
        chart_df, year, group_by_col=group_by_col, unit=chart_type
    )
    chart_df = standardise_chart_data(chart_df)
    chart_df["TimeSlice"] = chart_df["TimeSlice"].astype(str)
    chart_df["TimeSliceOrder"] = chart_df["TimeSlice"].map(TIMESLICE_ORDER.index) - 1
    chart_df = chart_df.sort_values(["Scenario", "TimeSliceOrder"])

    x_labels, season_starts = _get_demand_flex_flow_axis_labels(chart_df)

    p = (
        ggplot(
            chart_df,
            aes(x="TimeSliceOrder", y="Value", fill=group_by_col),
        )
        + geom_col(width=0.82)
        + geom_hline(yintercept=0, colour="#2F2F2F", size=0.4)
        + geom_vline(
            xintercept=season_starts,
            colour="#B8B8B8",
            size=0.5,
        )
        + facet_grid(". ~ Scenario")
        + labs(
            title=f"Demand-flex equivalent electricity input by timeslice, {year}",
            x="",
            y=chart_type,
            fill=group_by_col,
        )
        + scale_x_continuous(
            breaks=x_labels["TimeSliceOrder"].tolist(),
            labels=x_labels["DayTimeAxisLabel"].tolist(),
        )
        + scale_y_continuous(labels=adaptive_tick_labels)
        + scale_fill_manual(values=chart_cols)
        + theme_minimal()
        + theme(
            legend_position="bottom",
            axis_text_x=element_text(rotation=0, ha="center", va="top", size=7),
            panel_grid_major_x=element_blank(),
            panel_grid_minor_x=element_blank(),
            figure_size=(14, 7.5),
        )
    )

    save_chart_and_data(
        chart_df,
        p,
        f"demand_flex_flows_{chart_type.lower()}_{year}.png",
        height=7.5,
        width=14,
    )
    return p


def main():
    """Write demand-flex flow charts."""

    create_demand_flex_flows_chart(group_by_col="Technology", year=2035)
    create_demand_flex_flows_chart(group_by_col="Technology", year=2050)
    create_demand_flex_flows_chart(
        group_by_col="Technology", year=2035, chart_type="GWh"
    )
    create_demand_flex_flows_chart(
        group_by_col="Technology", year=2050, chart_type="GWh"
    )


if __name__ == "__main__":
    main()
