"""
Designed to format chart data into a way datawrapper likes it

Based on existing analysis data (which itself is saved in a big list of options)

So does very little work, just sorting out a specific grain to match
the datawrapper philosophy (max 1 grain var per table, never more)

Currently sends these to onedrive if you set that in your env, otherwise saves local untracked

"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from times_nz_internal_qa.utilities.filepaths import ANALYSIS_RESULTS, PREP_STAGE_2

# constants
load_dotenv()
chart_data_directory = ANALYSIS_RESULTS / "data_for_charts"
output_dir = Path(
    os.getenv(
        "DATAWRAPPER_OUTPUT_DIR",
        chart_data_directory / "datawrapper",
    )
)


# this list identifies each report chart, its original filename,
# and whether a facet method was required.
# the order in the list corresponds to the figure order in the report
figure_list = {
    "Total energy demand": ["total_demand_by_fuel", True],
    "Energy emissions": ["emissions_line", False],
    "Renewable share of TFEC": ["indicator_ren_tfec", False],
    "Emissions by sector": ["emissions_sector_facet", True],
    "Renewable share of electricity generation": ["indicator_ren_gen", False],
    "Electricity generation by technology": ["elec_gen_by_tech", True],
    "Fuel used by thermal electricity generation": [
        "thermal_generation_fuel_use",
        True,
    ],
    "Electricity demand by sector": ["electricity_demand_by_sector_group", True],
    "Battery capacity": ["battery_capacity", True],
    "Battery charging and discharging, 2035": ["battery_flows_gw_2035", True],
    "LNG, natural gas, and biogas supply": [
        "primary_energy_lng_natural_gas_biogas_supply",
        True,
    ],
    "Biomass and biogas supply ": ["primary_energy_biomass_biogas_supply", True],
    "Road transport demand": ["road_transport_demand", True],
    "Light passenger fleet": ["transport_lpv_capacity", True],
    "Light commercial fleet": ["transport_lcv_capacity", True],
    "Truck fleet": ["transport_truck_capacity", True],
    "Industrial demand": ["industrial_demand", True],
    "Dairy demand": ["demand_profile_dairy", True],
    "Meat demand": ["demand_profile_meat", True],
    "Residential demand": ["residential_demand", True],
    "Commercial demand": ["commercial_demand", True],
    "Electricity demand sensitivity: Shift technologies": [
        "sensitivity_shift_technology_electricity_demand",
        False,
    ],
}


# Some charts have another facet in addition to Scenario. Each value is split
# into its own Datawrapper input file, using the configured filename suffix.
additional_facets = {
    "transport_truck_capacity": {
        "column": "EndUse",
        "values": {
            "Light Truck": "light",
            "Medium Truck": "medium",
            "Heavy Truck": "heavy",
        },
    }
}


BATTERY_FLOW_SEASONS = ["Summer", "Autumn", "Winter", "Spring"]
BATTERY_FLOW_TIMES_OF_DAY = ["Day", "Peak", "Night"]


def save_scenario_version(
    df, scenario, output_filename, additional_facet=None, facet_value=None
):
    """
    If a dataframe is intended as a scenario facet,
    Then we need to split up the data and save steady and shift versions
    """

    df = df[df["Scenario"] == scenario].copy()
    df = df.drop("Scenario", axis=1)
    scen_filename = f"{output_filename}_{scenario.lower()}"

    if additional_facet is not None:
        facet_column = additional_facet["column"]
        df = df[df[facet_column] == facet_value].copy()
        df = df.drop(facet_column, axis=1)
        facet_suffix = additional_facet["values"][facet_value]
        scen_filename = f"{scen_filename}_{facet_suffix}"

    save_datawrapper_timeseries(df, scen_filename)


def save_datawrapper_timeseries(df, output_filename):
    """
    Makes the data wide, which is how datawrapper likes it, then saves
    """

    grain_columns = [
        column for column in df.columns if column not in ["Period", "Unit", "Value"]
    ]

    grain_column = grain_columns[0]
    if len(grain_columns) != 1:
        print("Grain more than 1 - can't sort!")
    else:
        category_order = None
        if isinstance(df[grain_column].dtype, pd.CategoricalDtype):
            category_order = df[grain_column].cat.categories

            wide_df = df.pivot(
                index=["Period", "Unit"], columns=grain_column, values="Value"
            )

            if category_order is not None:
                wide_df = wide_df.reindex(columns=category_order)

            wide_df.to_csv(
                output_dir / f"{output_filename}.csv",
            )


def save_datawrapper_battery_flows_grouped(df, output_filename):
    """Save time-weighted GW flows grouped by time of day, with season series."""

    required_columns = {
        "Scenario",
        "Variable",
        "Technology",
        "Season",
        "DayType",
        "TimeOfDay",
        "TimeSlice",
        "Unit",
        "Value",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(
            "Battery flow data is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    chart_df = df.copy()
    charging_mask = chart_df["Variable"].eq("Battery charging")
    discharging_mask = chart_df["Variable"].eq("Battery discharging")
    chart_df.loc[charging_mask, "Value"] = -chart_df.loc[charging_mask, "Value"].abs()
    chart_df.loc[discharging_mask, "Value"] = chart_df.loc[
        discharging_mask, "Value"
    ].abs()
    yrfr = pd.read_csv(PREP_STAGE_2 / "settings/load_curves/yrfr.csv")
    chart_df = chart_df.merge(yrfr, on="TimeSlice", how="left")
    if chart_df["YRFR"].isna().any():
        missing_timeslices = sorted(
            chart_df.loc[chart_df["YRFR"].isna(), "TimeSlice"].unique()
        )
        raise ValueError(
            "Missing year fractions for battery-flow timeslices: "
            + ", ".join(missing_timeslices)
        )
    chart_df["Weighted value"] = chart_df["Value"] * chart_df["YRFR"]

    for scenario in chart_df["Scenario"].drop_duplicates():
        scenario_df = chart_df[chart_df["Scenario"] == scenario].copy()
        units = scenario_df["Unit"].dropna().unique()
        if len(units) != 1 or units[0] != "GW":
            raise ValueError(
                f"Expected GW battery flows for {scenario}, found {list(units)}"
            )
        wide_df = scenario_df.pivot_table(
            index="TimeOfDay",
            columns="Season",
            values="Weighted value",
            aggfunc="sum",
            fill_value=0,
            sort=False,
        )
        weight_df = (
            scenario_df[["TimeSlice", "TimeOfDay", "Season", "YRFR"]]
            .drop_duplicates()
            .pivot_table(
                index="TimeOfDay",
                columns="Season",
                values="YRFR",
                aggfunc="sum",
                fill_value=0,
                sort=False,
            )
        )
        wide_df = wide_df.reindex(
            index=BATTERY_FLOW_TIMES_OF_DAY,
            columns=BATTERY_FLOW_SEASONS,
        ).fillna(0)
        weight_df = weight_df.reindex_like(wide_df)
        wide_df = wide_df.div(weight_df).fillna(0)
        wide_df.index.name = "Time of day"
        wide_df.insert(0, "Unit", units[0])

        scenario_slug = str(scenario).lower().replace(" ", "_")
        wide_df.to_csv(
            output_dir / f"{output_filename}_{scenario_slug}.csv",
        )


def save_scenario_facets(df, filename, additional_facet=None):
    """
    Saves both scenario facets for Steady, Shift
    """

    for scenario in ["Steady", "Shift"]:
        if additional_facet is None:
            save_scenario_version(df, scenario, filename)
            continue

        for facet_value in additional_facet["values"]:
            save_scenario_version(
                df,
                scenario,
                filename,
                additional_facet,
                facet_value,
            )


def order_category(df, category_column, period=None):
    """Order categories by their value in the first available period."""

    if isinstance(category_column, list):
        if len(category_column) != 1:
            raise ValueError("Exactly one category column is required")
        category_column = category_column[0]

    if period is None:
        period = df["Period"].min()

    category_order = (
        df.loc[df["Period"] == period]
        .groupby(category_column)["Value"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    # Preserve categories which are absent from the starting period by placing
    # them after the categories ranked above.
    remaining_categories = [
        category
        for category in df[category_column].dropna().unique()
        if category not in category_order
    ]
    category_order.extend(remaining_categories)

    ordered_df = df.copy()
    ordered_df[category_column] = pd.Categorical(
        ordered_df[category_column],
        categories=category_order,
        ordered=True,
    )

    return ordered_df.sort_values(
        [category_column, "Period"], na_position="last"
    ).reset_index(drop=True)


def save_datawrapper_chart_data(filename, is_facet, figure_number):
    """
    For a given dataframe, we reformat for datawrapper
    Parameters include:

    is_scenario_facet: boolean
        in the case of data for a scenario facet, we would
    """
    # get data
    df = pd.read_csv(chart_data_directory / f"{filename}.csv")
    # add leading 0s to figure count
    figure_label = f"{figure_number:02d}"
    # create label
    output_filename = f"fig_{figure_label}_{filename}"

    if filename == "battery_flows_gw_2035":
        save_datawrapper_battery_flows_grouped(df, output_filename)
        return

    # we want to find our datawrapper grain and sort these from biggest to smallest
    # we do this before splitting into scenario tables
    # so that scenario facets keep the same order
    #

    grain_columns = [
        col for col in df.columns if col not in ["Period", "Value", "Unit"]
    ]
    additional_facet = additional_facets.get(filename)

    if is_facet and "Scenario" in grain_columns:
        grain_columns.remove("Scenario")
        if additional_facet is not None:
            grain_columns.remove(additional_facet["column"])
        if len(grain_columns) == 1:
            # we've identifed the grain so can reorder it simply
            df = order_category(df, grain_columns[0])

    if is_facet:
        save_scenario_facets(df, output_filename, additional_facet)
    else:
        save_datawrapper_timeseries(df, output_filename)


def save_all_datawrapper_data():
    """
    Iterates over the full figure list
    saves chart data to datawrapper directory
    """

    # create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # start at 2 (figure 1 is a diagram)
    fig = 2

    for name, data in figure_list.items():
        filename, is_facet = data
        print(name)
        save_datawrapper_chart_data(filename, is_facet, fig)
        # iterate figure count
        fig += 1


def main():
    """entrypoint"""
    save_all_datawrapper_data()


if __name__ == "__main__":
    main()
