"""
Builds all analysis charts, grouped by subject area

Initial data cleaning and aggregating is performed in a separate module:
This module might do some mild filtering on top of these but should mostly avoid big data handling

Charts are saved to untracked analysis directory.

Calls data processing functions based on post-processed data produced for app.
"""

# need to remove these exceptions later: just getting a wip committed right now
# script wip
# pylint: disable=wildcard-import, unused-wildcard-import, unused-import, dangerous-default-value
# pylint: disable=unused-argument

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
}

chart_cols = [
    eeca_colours["navy"],
    eeca_colours["coral"],
    eeca_colours["teal"],
    eeca_colours["forest"],
    eeca_colours["emerald"],
    eeca_colours["orange"],
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
    """

    available_islands = df["Island"].dropna().unique().tolist()
    island_order = [
        island for island in preferred_island_order if island in available_islands
    ]
    island_order.extend(sorted(set(available_islands) - set(island_order)))
    df["Island"] = pd.Categorical(df["Island"], categories=island_order, ordered=True)

    return df, island_order


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


def area_facet_chart(df, chart_title, facet_rows=None, facet_columns=None):
    """
    Based on an input df with some combination of
    """

    unit = get_df_unit(df)

    filename = f"{chart_title}.png"

    p = (
        ggplot(df, aes(x="Period", y="Value", fill="Fuel"))
        + geom_area()
        + facet_grid()
        + labs(
            title=chart_title,
            x="Year",
            y=unit,
            fill="Fuel",
        )
        + scale_x_continuous(breaks=[2025, 2030, 2035, 2040, 2045, 2050])
        + scale_y_continuous(limits=(0, None), labels=adaptive_tick_labels)
        + scale_fill_manual(values=eeca_colours)
        + theme_minimal()
        + theme(legend_position="bottom")
    )

    p.save(
        f"analysis/{filename}",
        dpi=300,
        height=5,
        width=8,
        limitsize=False,
    )


def create_scenario_line_chart(df):
    """
    A chart intended to compare scenarios along a single metric
    No more than five! and the vast majority of the time will just be two
    """


# SUBJECT FUNCTIONS

# this function group is intended to output/save
# charts based on data inputs and filenames

# just to reduce some repetition


# INDICATORS
def create_ren_tfec_charts():
    """
    get ren tfec data from steady/shift, linechart with labels, save
    """
    print("Hello please write me ")


def create_ren_gen_charts():
    """
    get ren elec data from steady/shift, linechart with labels, save
    """
    print("Hello please write me ")


def create_indicators():
    """wrapper for indicator charts"""

    create_ren_tfec_charts()


# ELECTRICITY GENERATION


def create_generation_mix():
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


def create_fleet_composition_chart(enduse):
    """
    area facet chart for transport fleet counts by technology
    filtered for a specific end use (LPV, LCV, Trucks, maybe others )
    """
    print("Hello please write me ")


def make_all_transport_charts():
    """Wrarpper for transport cjarts"""

    create_fleet_composition_chart("LPV")
    create_fleet_composition_chart("LCV")
    create_fleet_composition_chart(
        ["Light", "Heavy", "Medium"]
    )  # want to do a bit of ordering here
    # other transport charts?
    # total demand would be useful to show off energy efficiency of electric vehicles


def main():
    """entrypoint. can pick and choose specific areas to run"""

    make_all_transport_charts()
    # etc
