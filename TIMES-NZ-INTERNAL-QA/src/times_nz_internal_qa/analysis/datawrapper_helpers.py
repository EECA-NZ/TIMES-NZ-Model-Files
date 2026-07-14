"""
Functions to (for now) reformat chart data
for easy datawrapper use

More of this pipeline might be automated later

"""

import pandas as pd
from times_nz_internal_qa.utilities.filepaths import ANALYSIS_RESULTS

# constants
chart_data_directory = ANALYSIS_RESULTS / "data_for_charts"
output_dir = chart_data_directory / "datawrapper"

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
    "Battery charging and discharging, 2035": ["battery_flows_gwh_2035", True],
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


def save_scenario_version(df, scenario, output_filename):
    """
    If a dataframe is intended as a scenario facet,
    Then we need to split up the data and save steady and shift versions
    """

    df = df[df["Scenario"] == scenario].copy()
    scen_filename = f"{output_filename}_{scenario.lower()}"
    df.to_csv(output_dir / f"{scen_filename}.csv", index=False)


def save_scenario_facets(df, filename):
    """
    Saves both scenario facets for Steady, Shift
    """

    for scenario in ["Steady", "Shift"]:
        save_scenario_version(df, scenario, filename)


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

    if is_facet:
        save_scenario_facets(df, output_filename)
    else:
        df.to_csv(output_dir / f"{output_filename}.csv", index=False)


def save_all_datawrapper_data():
    """
    Iterates over the full figure list
    saves chart data to datawrapper directory
    """

    # create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # start at 2 (figure 1 is a diagram)
    fig = 2

    for filename, is_facet in figure_list.values():
        save_datawrapper_chart_data(filename, is_facet, fig)
        # iterate figure count
        fig += 1


def main():
    """entrypoint"""
    save_all_datawrapper_data()


if __name__ == "__main__":
    main()
