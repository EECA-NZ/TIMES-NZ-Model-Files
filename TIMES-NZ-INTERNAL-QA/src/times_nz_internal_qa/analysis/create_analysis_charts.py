"""
Builds all analysis charts, grouped by subject area

Initial data cleaning and aggregating is performed in a separate module:
This module might do some mild filtering on top of these but should mostly avoid big data handling

Charts are saved to untracked analysis directory.

Calls data processing functions based on post-processed data produced for app.



All bespoke chart functions follow this general pattern:

(named `create_[X]_chart()`)

1) Load the data using imported data functions
2) (Optional) additional minor data filtering
3) Chart generation function
4) (optional) additional minor chart tweaks
5) Write png

This script includes generated chart functions and other helpers to standardise methods

IMPORTANT NOTE: we are following the design principle where no
chart has more than FIVE colour categories
This is to reduce visual noise but requires some categories to be aggregated slightly

"""

# need to remove these exceptions later: just getting a wip committed right now
# script wip
# pylint: disable=wildcard-import, unused-wildcard-import, unused-import, dangerous-default-value
# pylint: disable=unused-argument

import re

import pandas as pd
import times_nz_internal_qa.analysis.get_data as chart_data
from mizani.labels import comma_format, percent_format
from plotnine import *

# CONSTANTS - colour settings

eeca_colours = {
    "emerald": "#41B496",
    "teal": "#447474",
    "navy": "#164057",
    "coral": "#ED6D63",
    "forest": "#3C4C49",
    "orange": "#E94E24",
    "purple": "#C346CE",
}

chart_cols = [
    eeca_colours["teal"],
    eeca_colours["coral"],
    eeca_colours["navy"],
    eeca_colours["purple"],
    eeca_colours["emerald"],
    eeca_colours["forest"],
    eeca_colours["emerald"],
]


# CONSTANTS: category orders

SCENARIO_ORDER = [
    "Steady",
    "Shift",
]

PREFERRED_ISLAND_ORDER = ["North Island", "South Island"]


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
    # Remove special characters, keeping letters, numbers, spaces, underscores, and hyphens
    cleaned = re.sub(r"[^a-zA-Z0-9\s_-]", "", string)

    # Split on spaces, underscores, and hyphens
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

    return [
        "" if pd.isna(value) else f"{value:,.{decimals}f}".rstrip("0").rstrip(".")
        for value in values
    ]


def save_chart(p, filename):
    """
    Convenience wrapper for save function
    Might extend parameters for h/w etc later
    Mostly just to split out the workflow and allow further
    chart customisation before saving where necessary
    """

    p.save(
        f"analysis/{filename}",
        dpi=300,
        height=4,
        width=6,
        limitsize=False,
    )


# HELPER FUNCTIONS - SORTING


def get_scenario_facet_order(df):
    """Return preferred scenario order with any extras appended."""
    print("hello please write me")


def standardise_scenario_order(df, scenario_order=SCENARIO_ORDER):
    """
    For a df with a Scenario variable, orders these according to the constant defined order
    If the df has additional Scenarios in the Scenario variable, these are just ordered at the end
    We may want to expand this method later depending on sensitivity analysis approach

    """

    # Technically possible for data to have no scenario name
    # Seems unlikely but we'll add a skip anyway
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
    For an input df with an "Island" variable, standardises the order
    by creating a categorical var

    not all data has islands so can just skip this
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
    A collection of adjustments to
    ensure all data heading into chart functions has standard parameters
    """

    # sort scenarios

    df = standardise_island_order(df)
    df = standardise_scenario_order(df)

    return df


# CHART FUNCTIONS


def get_df_unit(df):
    """
    Returns the unit listed in the dataframe
    There should only be one: fails if multiple found
    """
    unit_list = df["Unit"].unique()
    if len(unit_list) > 1:
        raise ValueError("Multiple units found in data: please review filters")
    return unit_list[0]


def _area_facet_cols(facet_rows=None, facet_columns=None):
    """Return the facet columns used to identify separate area panels."""
    return [col for col in [facet_rows, facet_columns] if col]


# might be best to refactor this out a bit!
# pylint:disable = too-many-locals
def _prepare_area_chart_df(df, group_var, facet_rows=None, facet_columns=None):
    """
    Add chart-only zero rows where an area series starts or ends between periods.

    The source data is left semantically sparse: only missing points directly adjacent
    to a non-zero value are added, so geom_area can draw the boundary down to zero.
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

    return (
        pd.concat([chart_df, pd.DataFrame(extra_rows)], ignore_index=True)
        .sort_values(series_cols + ["Period"])
        .reset_index(drop=True)
    )


def create_area_facet_chart(
    df, chart_title, group_var, facet_rows=None, facet_columns=None
):
    """
    Based on an input df with some combination of facets!
    """

    unit = get_df_unit(df)
    df = _prepare_area_chart_df(df, group_var, facet_rows, facet_columns)

    # Build facet formula
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
        + scale_fill_manual(values=chart_cols)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    return p


def create_scenario_facet_chart(df, chart_title, group_var, facet_rows=None):
    """
    A convenience wrapper for create_area_facet_chart
    to always uses scenario as facet cols
    (common use)
    """

    return create_area_facet_chart(
        df=df,
        chart_title=chart_title,
        group_var=group_var,
        facet_rows=facet_rows,
        facet_columns="Scenario",
    )


def create_scenario_line_chart(df, chart_title, yaxis_0=True):
    """
    A chart intended to compare scenarios along a single metric
    No more than five! and the vast majority of the time will just be two
    """

    unit = get_df_unit(df)

    # new df for filling in labels
    label_data = df.sort_values("Period").groupby("Scenario", as_index=False).tail(1)
    label_data["x_location"] = label_data["Period"] + 1
    label_data["Label"] = (
        label_data["Scenario"]
        + ": \n"
        + label_data["Value"].apply(lambda x: f"{x:,.2f}")
        + label_data["Unit"]
    )

    p = (
        ggplot(df, aes(x="Period", y="Value", colour="Scenario"))
        + geom_line(size=1)
        + geom_label(
            data=label_data,
            mapping=aes(x="x_location", label="Label", fill="Scenario"),
            colour="white",
        )
        + labs(title=chart_title, x="Year", y=unit, colour="Scenario")
        # + lwd(1)
        + scale_x_continuous(
            breaks=[2025, 2030, 2035, 2040, 2045, 2050], limits=[2023, 2052]
        )
        + scale_y_continuous(labels=adaptive_tick_labels)
        # default needed for linter here
        + scale_colour_manual(values=chart_cols, na_value="grey")
        + scale_fill_manual(values=chart_cols)
        + theme_minimal()
        + theme(legend_position="none")
    )

    # usually we zero the y axis, but not always
    if yaxis_0:
        p = p + scale_y_continuous(limits=(0, None))
    return p


# SUBJECT FUNCTIONS

# this function group is intended to output/save
# charts based on data inputs and filenames

# just to reduce some repetition


# INDICATORS
def create_ren_tfec_chart():
    """
    get ren tfec data from steady/shift, linechart with labels, save
    """
    tfec_df = chart_data.get_renewable_tfec()
    # some mild formatting for creatting a percentage
    tfec_df["Value"] = tfec_df["RenewableShareOfTFEC"] * 100
    tfec_df["Unit"] = "%"

    p = create_scenario_line_chart(tfec_df, "Renewable share of TFEC")
    save_chart(p, "indicator_ren_tfec.png")


def create_ren_gen_chart():
    """
    get ren elec data from steady/shift, linechart with labels, save
    """
    ren_elec = chart_data.get_renewable_electricity_share()
    ren_elec["Value"] = ren_elec["RenewableShareOfElectricity"] * 100
    ren_elec["Unit"] = "%"

    p = create_scenario_line_chart(
        ren_elec, "Renewable share of electricity generation", yaxis_0=False
    )
    save_chart(p, "indicator_ren_gen.png")


def create_indicators():
    """runs all indicatorcharts"""
    create_ren_gen_chart()
    create_ren_tfec_chart()


# ELECTRICITY GENERATION


def create_generation_mix_chart():
    """
    grouped area facet (facet by scenario??)
    """

    print("Hello please write me ")


def create_thermal_generation_charts():
    """
    grouped area facet (facet by scenario??)
    """
    print("Hello please write me ")


def create_battery_capacity():
    """
    battery capacity by tech group (grid/dist)
    """
    print("Hello please write me ")


# Emissions

# want both a key line (with other model comparisons! ) and an area facet chart


def create_emissions_line(comparison=False):
    """
    Line chart comparing up to 5 emission tracks with labels etc
    """
    print("Hello please write me ")


def create_emissions_breakdown():
    """
    area facet for emissions share by sector
    """
    print("Hello please write me ")


def create_emissions_charts():
    """
    wrapper for all emissions charts, including comparison options for other models!!
    Note: do the transpower scenarios come with full emissions models?? I thought it was just elc
    so possibly not needed
    """

    create_emissions_line()
    create_emissions_line(comparison=True)
    create_emissions_breakdown()


# TRANSPORT


def create_fleet_composition_chart(enduse_list, title, filename, facet_rows=None):
    """
    area facet chart for transport fleet counts by technology
    filtered for a specific end use (LPV, LCV, Trucks, maybe others )
    """

    fleet_df = chart_data.get_transport_capacity(enduse_list)
    fleet_df = standardise_chart_data(fleet_df)

    # shorter tech names for chart legend
    tech_rename_mapping = {
        "Battery Electric Vehicle": "BEV",
        "Hybrid Vehicle": "Hybrid",
        "Internal Combustion Engine": "ICE",
        "Plug-in Hybrid Vehicle": "PHEV",
    }

    fleet_df["TechnologyGroup"] = fleet_df["TechnologyGroup"].map(tech_rename_mapping)

    p = create_scenario_facet_chart(fleet_df, title, "TechnologyGroup", facet_rows)

    save_chart(p, filename)


def quick_truck_maths():
    """
    short analysis script:

    A heavy electric vehicle might travel XXkm per year,
    which could mean $$ worth of fuel for a diesel ICE engine,
    compared to potentially only XX$ worth of electricity.
    """

    heavy_truck_high_util = 74_246
    med_truck_low_util = 12_047
    # med_truck_high_util = 74_246

    heavy_truck_ice_eff = 0.05  # bvkt/pj
    heavy_truck_bev_eff = 0.2

    heavy_truck_ice_gj_demand = heavy_truck_high_util / heavy_truck_ice_eff / 1000
    heavy_truck_bev_gj_demand = heavy_truck_high_util / heavy_truck_bev_eff / 1000

    # penalty
    heavy_truck_bev_gj_demand = heavy_truck_bev_gj_demand * 1.1

    bev_fuel_costs = 62.82
    ice_fuel_costs = 39.74

    print(f"Heavy trukc bev uses {heavy_truck_bev_gj_demand} gj")
    print(f"Heavy trukc ice uses {heavy_truck_ice_gj_demand} gj")
    print(f"Heavy trukc bev costs {heavy_truck_bev_gj_demand*bev_fuel_costs} pa")
    print(f"Heavy trukc ice costs {heavy_truck_ice_gj_demand*ice_fuel_costs} pa")

    # MEDIUM TRUCKS

    med_truck_ice_eff = 0.06
    med_truck_bev_eff = 0.3

    med_truck_bev_gj_demand = med_truck_low_util / med_truck_bev_eff / 1000
    med_truck_ice_gj_demand = med_truck_low_util / med_truck_ice_eff / 1000

    print(f"Medium Truck bev uses {med_truck_bev_gj_demand} gj")
    print(f"Medium Truck ice uses {med_truck_ice_gj_demand} gj")
    print(f"Medium Truck bev costs {med_truck_bev_gj_demand*bev_fuel_costs} pa")
    print(f"Medium Truck ice costs {med_truck_ice_gj_demand*ice_fuel_costs} pa")


def make_all_transport_charts():
    """Wrarpper for transport cjarts"""

    create_fleet_composition_chart(
        ["Light Passenger Vehicle"],
        "Light passenger fleet",
        "transport_lpv_capacity.png",
    )

    create_fleet_composition_chart(
        ["Light Commercial Vehicle"],
        "Light commercial fleet",
        "transport_lcv_capacity.png",
    )

    create_fleet_composition_chart(
        ["Light Truck", "Heavy Truck", "Medium Truck"],
        "Truck fleet",
        "transport_truck_capacity.png",
        "EndUse",
    )

    # quick_truck_maths()

    # want to do a bit of ordering here
    # other transport charts?
    # total demand would be useful to show off energy efficiency of electric vehicles


# RES/COM


def create_residential_demand_chart():
    """
    Get res demand, make area chart, dw about groups
    """

    group_vars = [
        "Scenario",
        "Period",
        "Unit",
        "Fuel",
    ]

    res_df = chart_data.get_fuel_use_by_island_and_sector(sector_group="Residential")

    # fuel aggregation
    res_fuel_aggregation = {
        "Coal": "Other",
        "Diesel": "Diesel/Petrol",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Natural gas": "Natural gas",
        "Petrol": "Diesel/Petrol",
        "Solar": "Other",
        "Wood": "Woody biomass",
    }

    res_df["Fuel"] = res_df["Fuel"].map(res_fuel_aggregation)
    res_df = res_df.groupby(group_vars)["Value"].sum().reset_index()

    # data standardisation

    res_df = standardise_chart_data(res_df)

    p = create_scenario_facet_chart(res_df, "Residential demand", group_var="Fuel")

    # p = p +theme(legend_position = "right")
    save_chart(p, "residential_demand.png")


def create_commercial_demand_chart():
    """
    Commercial demand area charts, with minor tweaks for nicenenss
    """

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    com_df = chart_data.get_fuel_use_by_island_and_sector(sector_group="Commercial")

    fuels = com_df["Fuel"].unique()

    for f in fuels:
        print(f)

    com_fuel_aggregation = {
        "Coal": "Other",
        "Diesel": "Diesel/Petrol",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Natural gas": "Natural gas",
        "Petrol": "Diesel/Petrol",
        "Solar": "Other",
        "Geothermal": "Other",
        "Biogas": "Biogas",
        "Biomethane": "Biomethane",
        "Wood": "Woody biomass",
    }

    com_df["Fuel"] = com_df["Fuel"].map(com_fuel_aggregation)
    com_df = com_df.groupby(group_vars)["Value"].sum().reset_index()

    com_df = standardise_chart_data(com_df)

    p = create_scenario_facet_chart(
        com_df, group_var="Fuel", chart_title="Commercial demand "
    )

    save_chart(p, "commercial_demand.png")


def create_industrial_demand_chart():
    """
    this could use refactoring probably

    I would not mind doing a specific fuel colour palette and making those consistent as well
    """

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    ind_df = chart_data.get_fuel_use_by_island_and_sector(
        sector_group="Industry",
    )

    fuels = ind_df["Fuel"].unique()

    for f in fuels:
        print(f)

    ind_fuel_aggregation = {
        "Coal": "Other",
        "Diesel": "Diesel/Petrol",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Natural gas": "Natural gas",
        "Petrol": "Diesel/Petrol",
        "Solar": "Other",
        "Geothermal": "Other",
        "Biogas": "Biogas",
        "Biomethane": "Biomethane",
        "Wood": "Woody biomass",
    }

    ind_df["Fuel"] = ind_df["Fuel"].map(ind_fuel_aggregation)
    ind_df = ind_df.groupby(group_vars)["Value"].sum().reset_index()

    ind_df = standardise_chart_data(ind_df)
    p = create_scenario_facet_chart(
        ind_df, group_var="Fuel", chart_title="Industrial demand "
    )

    save_chart(p, "industrial_demand.png")


def create_industry_sector_demand_chart(subsector_list, name):
    """
    wrapper for industry area charts
    """

    group_vars = ["Scenario", "Period", "Unit", "Fuel"]

    ind_df = chart_data.get_fuel_use_by_island_and_sector(
        sector_group="Industry",
    )

    df = ind_df[ind_df["Sector"].isin(subsector_list)].copy()

    ind_fuel_aggregation = {
        "Coal": "Coal",
        "Diesel": "Diesel",
        "Electricity": "Electricity",
        "LPG": "LPG",
        "Natural gas": "Natural gas",
        "Petrol": "Petrol",
        "Solar": "Other",
        "Geothermal": "Other",
        "Biogas": "Biogas",
        "Biomethane": "Biogas",
        "Wood": "Woody biomass",
    }

    df["Fuel"] = df["Fuel"].map(ind_fuel_aggregation)
    df = df.groupby(group_vars)["Value"].sum().reset_index()

    filename = make_filename(name)
    df = standardise_chart_data(df)
    print(df)
    p = create_scenario_facet_chart(df, group_var="Fuel", chart_title=f"{name} demand")
    save_chart(p, f"demand_profile_{filename}.png")


def create_industry_demand_charts():
    """
    Wrapper for various sector demands
    """
    # total demand
    create_industrial_demand_chart()
    # subsectors
    create_industry_sector_demand_chart(["Dairy"], "Dairy")
    create_industry_sector_demand_chart(["Meat"], "Meat")
    create_industry_sector_demand_chart(["Methanol", "Urea"], "Methanex/Ballance")


def main():
    """entrypoint. can pick and choose specific areas to run"""

    create_indicators()
    create_emissions_charts()
    create_residential_demand_chart()
    create_commercial_demand_chart()
    create_industry_demand_charts()
    make_all_transport_charts()

    # etc


if __name__ == "__main__":
    main()
