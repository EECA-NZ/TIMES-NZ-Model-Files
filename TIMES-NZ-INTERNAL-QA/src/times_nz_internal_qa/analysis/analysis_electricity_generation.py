"""Electricity generation analysis charts."""

import pandas as pd
import times_nz_internal_qa.analysis.get_data as chart_data

# isort is clashing with pylint on what order these should go in, so disable pylint
# pylint:disable = wildcard-import, unused-wildcard-import, wrong-import-order
from plotnine import *
from times_nz_internal_qa.analysis.analysis_chart_helpers import (
    adaptive_tick_labels,
    chart_cols,
    convert_timeslice_flow_units,
    create_scenario_facet_chart,
    create_scenario_line_chart,
    eeca_colours,
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
from times_nz_internal_qa.utilities.filepaths import PREP_STAGE_2

CAP2ACT = 31.536


def create_generation_line_chart():
    """Create total electricity generation comparison chart."""

    df = chart_data.get_elec_gen()
    df = standardise_chart_data(df)

    p = create_scenario_line_chart(df, "Electricity generation")

    save_chart_and_data(df, p, "elec_gen_line.png")


def create_generation_mix_chart():
    """Grouped area facet by scenario showing fuel mix."""

    # df = chart_data.get_elec_gen_fuel_use()
    df = chart_data.get_elec_gen(groupby_cols="TechnologyGroup")

    # custom colours!
    ele_colours = [
        eeca_colours["teal"],
        eeca_colours["navy"],
        eeca_colours["coral"],
        eeca_colours["forest"],
        eeca_colours["paleblue"],
        eeca_colours["navy"],
        eeca_colours["forest"],
    ]

    df = standardise_chart_data(df)

    p = create_scenario_facet_chart(
        df,
        chart_title="Electricity generation by technology",
        group_var="TechnologyGroup",
        palette=ele_colours,
    )
    save_chart_and_data(df, p, "elec_gen_by_tech.png")


def create_thermal_generation_charts():
    """Grouped area facet for thermal generation."""

    print("Hello please write me ")


def create_battery_capacity_chart(group_by_col="Technology"):
    """Create battery capacity comparison chart."""

    df = chart_data.get_battery_capacity(groupby_cols=group_by_col)
    df = standardise_chart_data(df)

    p = create_scenario_facet_chart(
        df,
        chart_title="Battery capacity",
        group_var=group_by_col,
    )
    save_chart_and_data(df, p, "battery_capacity.png")
    return p


def create_battery_flows(group_by_col="Technology"):
    """Battery charge and discharge flows by readable timeslice."""

    df = chart_data.get_times_data("battery_flows.parquet")

    grain_vars = [
        "Scenario",
        "Variable",
        "Period",
        "TimeSlice",
        "Unit",
    ]

    group_vars = grain_vars + [group_by_col]

    df = df.groupby(group_vars)["Value"].sum().reset_index()
    df = add_timeslice_chart_columns(df)

    return df


def _complete_battery_flow_timeslices(df, year, group_by_col="Technology", unit="GW"):
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


def _get_battery_flow_axis_labels(chart_df):
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


def create_battery_flows_chart(
    df=None, year=2050, group_by_col="Technology", chart_type="GW"
):
    """Create battery charge/discharge chart for a single model year."""

    if df is None:
        df = create_battery_flows(group_by_col=group_by_col)

    df = standardise_chart_data(df)

    chart_df = df[df["Period"].astype(int) == year].copy()
    chart_df = chart_df[chart_df["TimeSlice"].astype(str).isin(TIMESLICE_ORDER)].copy()

    if chart_df.empty:
        raise ValueError(f"No battery flow data found for {year}")

    charge_mask = chart_df["Variable"].eq("Battery charging")
    chart_df.loc[charge_mask, "Value"] = -chart_df.loc[charge_mask, "Value"]
    chart_df, chart_type = convert_timeslice_flow_units(chart_df, chart_type=chart_type)

    chart_df = _complete_battery_flow_timeslices(
        chart_df, year, group_by_col=group_by_col, unit=chart_type
    )
    chart_df["TimeSlice"] = chart_df["TimeSlice"].astype(str)
    chart_df["TimeSliceOrder"] = chart_df["TimeSlice"].map(TIMESLICE_ORDER.index) - 1
    chart_df = chart_df.sort_values(["Scenario", "TimeSliceOrder"])

    x_labels, season_starts = _get_battery_flow_axis_labels(chart_df)

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
            title=f"Battery charging and discharging by timeslice, {year}",
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
        f"battery_flows_{chart_type.lower()}_{year}.png",
        height=7.5,
        width=14,
    )
    return p


def test_battery_afs():
    """
    a brief checking function intended to:
    1) get battery output flows per slice
    2) get battery capacity per slice
    3) run comparisons
    """

    # 1: battery output flows

    df_flow = chart_data.get_times_data("battery_flows.parquet")

    df_cap = chart_data.get_times_data("batteries.parquet")
    df_cap["CapacityGW"] = df_cap["Value"]

    flow_grain = [
        "Scenario",
        "TechnologyGroup",
        "Technology",
        "Region",
        "Period",
        "Variable",
        "TimeSlice",
    ]

    flow_agg = df_flow.groupby(flow_grain)["Value"].sum().reset_index()
    flow_agg = flow_agg.rename(columns={"Value": "FlowPJ"})

    for c in df_cap.columns:
        print(c)

    cap_grain = [
        "Scenario",
        "TechnologyGroup",
        "Technology",
        "Region",
        "Period",
    ]

    cap_agg = df_cap.groupby(cap_grain)["Value"].sum().reset_index()
    cap_agg = cap_agg.rename(columns={"Value": "CapacityGW"})

    df = pd.merge(flow_agg, cap_agg, how="left", on=cap_grain)

    # add year fractions
    yrfr = pd.read_csv(PREP_STAGE_2 / "settings/load_curves/yrfr.csv")

    df = pd.merge(df, yrfr, on="TimeSlice", how="left")
    # hours not strictly necessary but sometimes helpful
    df["Hours"] = df["YRFR"] * 24 * 365
    # max output two watys

    df["MaxFlowPJ"] = df["CapacityGW"] * df["YRFR"] * CAP2ACT

    df["ActivityShare"] = df["FlowPJ"] / df["MaxFlowPJ"]

    print(flow_agg)
    print(cap_agg)

    print(df)


def main():
    """Write all electricity generation charts."""

    create_generation_line_chart()
    create_generation_mix_chart()
    create_battery_capacity_chart(group_by_col="Technology")
    create_battery_flows_chart(group_by_col="Technology", year=2035)
    create_battery_flows_chart(group_by_col="Technology", year=2050)
    create_battery_flows_chart(group_by_col="Technology", year=2035, chart_type="GWh")
    create_battery_flows_chart(group_by_col="Technology", year=2050, chart_type="GWh")


if __name__ == "__main__":
    main()
