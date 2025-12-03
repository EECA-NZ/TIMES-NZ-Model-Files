"""
Outputs new battery storage files for Veda
These are not currently adjusted per scenario, but probably should be
"""

# Libraries  ---------------------------------------------------------------


import numpy as np
import pandas as pd
from prepare_times_nz.stage_4.electricity.common import (
    CAP2ACT,
    SETS_STG,
    create_process_file,
)
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    DATA_RAW,
    STAGE_4_DATA,
)

# Constants  ---------------------------------------------------------------

NZD_AUD = 0.924
# how much more expensive distributed batteries are than utility-scale equivalents, per kW
DIST_FACTOR = 2
# level of FOM (as share of CAPEX)
FOM_FACTOR = 0.01

# Input file locations ---------------------------------------------------------------

FUTURE_TECH_ASSUMPTIONS = ASSUMPTIONS / "electricity_generation/future_techs/"
BATTERY_COSTS_CSIRO = DATA_RAW / "external_data/csiro/BatteryCosts.csv"
BATTERY_TECH_ASSUMPTIONS = FUTURE_TECH_ASSUMPTIONS / "Batteries.csv"

# output file location  ---------------------------------------------------------------

OUTPUT_LOCATION = STAGE_4_DATA / "subres_elc/storage"

# helpers  ---------------------------------------------------------------


def save_battery_data(df, name, filepath=OUTPUT_LOCATION):
    """Wrapper for saving battery files"""
    label = "Saving battery data"
    _save_data(df, name, label, filepath=filepath)


# Functions ---------------------------------------------------------------


def create_battery_main_file():
    """
    Reads and relabels main battery assumptions (excl costs)

    Note: the only moderately tricky thing in here is the availability.
    See p130 of TIMES PT II documentation for background

    Basically we represent a 2 hour battery as the share of the full day

    So the storage ratio should be divided by 24 to provide the availability factor

    """
    df = pd.read_csv(BATTERY_TECH_ASSUMPTIONS)

    df = df.rename(
        columns={
            "PeakContribution": "NCAP_PKCNT",
            "StorageEfficiency": "S_EFF",
            # just setting the output to the commodity - should default to this being input also
            "Commodity": "Comm-OUT",
            "PlantLife": "Life",
            "StorageRatio": "NCAP_AFC",
        }
    )

    # availability curve set as a fraction of 24 hours
    # we max out at 1 (not possible to have ratios above 24)
    df["NCAP_AFC"] = np.minimum(df["NCAP_AFC"] / 24, 1)
    df["CAP2ACT"] = CAP2ACT

    return df


def get_battery_cost_curves():
    """
    Reads raw CSIRO prices for diff scenarios
    outputs a Veda table based on the input scenario

    Includes cost conversions from CSIRO data
    and OPEX/dist assumptions
    """

    df = pd.read_csv(BATTERY_COSTS_CSIRO)
    scenario_mapping = {
        "Current policies": "Traditional",
        "Global NZE by 2050": "Transformation",
    }

    # Get Our scenarios
    df["Scenario"] = df["ScenarioCSIRO"].map(scenario_mapping)
    # NZD conversion
    df["Value"] = df["Value"] / NZD_AUD
    # from $/kWh to $/kW
    df["CAPEX"] = df["Value"] * df["Hours"]
    df["Unit"] = "NZD/kW"  # we delete this soon but just so you know

    # build technames
    df["TechName"] = "ELC_BAT_" + df["Hours"].astype(str) + "H"

    # trim vars down
    df = df[["TechName", "Scenario", "Year", "CAPEX"]]

    # add 2hr distributed

    df_dist = df[df["TechName"] == "ELC_BAT_2H"].copy()

    df_dist["TechName"] = "ELC_BAT_DIST"
    df_dist["CAPEX"] = df_dist["CAPEX"] * DIST_FACTOR

    # add distributed to main table
    df = pd.concat([df, df_dist])

    # build fixed operating maintenance costs

    # we assume these don't curve at all so only take from year 1
    df_fom = df[df["Year"] == df["Year"].min()].copy()

    df_fom["FOM"] = df_fom["CAPEX"] * FOM_FACTOR

    df_fom = df_fom[["TechName", "Scenario", "FOM"]]

    # add the FOM to main table

    df = df.merge(df_fom, on=["Scenario", "TechName"], how="left")

    return df


def get_battery_scenario_curves(df, scenario):
    """
    reshapes and renames  the cost curve assumptions, filtering per scenario
    Note: Right now the inputs are very simple
    These currently have TechName set directly, so these TechNames
    need to align with TechNames set in the main battery assumption input
    """

    df = df[df["Scenario"] == scenario].copy()

    df = df[["TechName", "Year", "CAPEX", "FOM"]]

    df = df.rename(columns={"CAPEX": "INVCOST", "FOM": "FIXOM"})

    df = df.sort_values(["TechName", "Year"])

    return df


# Main ---------------------------------------------------------------


def main():
    """Wrapper for all battery formatting functions"""

    df = create_battery_main_file()
    save_battery_data(df, "battery_parameters.csv")

    df_process = create_process_file(df, sets=SETS_STG)
    save_battery_data(df_process, "battery_processes.csv")

    # ensure batteries available on either island
    battery_ava = df_process[["TechName"]]
    battery_ava = battery_ava.rename(columns={"TechName": "PSet_PN"})
    battery_ava["AllRegions"] = 1
    save_battery_data(battery_ava, "battery_availability.csv")

    battery_cost_curves = get_battery_cost_curves()

    batt_cost_traditional = get_battery_scenario_curves(
        battery_cost_curves, "Traditional"
    )

    batt_cost_transformation = get_battery_scenario_curves(
        battery_cost_curves, "Transformation"
    )

    save_battery_data(batt_cost_traditional, "battery_costs_traditional.csv")
    save_battery_data(batt_cost_transformation, "battery_costs_transformation.csv")


if __name__ == "__main__":
    main()
