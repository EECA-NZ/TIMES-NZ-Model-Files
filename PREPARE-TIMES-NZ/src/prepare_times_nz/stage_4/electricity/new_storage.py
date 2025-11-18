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
    STAGE_4_DATA,
)

# Constants  ---------------------------------------------------------------


# Input file locations ---------------------------------------------------------------

FUTURE_TECH_ASSUMPTIONS = ASSUMPTIONS / "electricity_generation/future_techs/"
battery_costs = FUTURE_TECH_ASSUMPTIONS / "BatteryCosts.csv"
batteries = FUTURE_TECH_ASSUMPTIONS / "Batteries.csv"

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
    df = pd.read_csv(batteries)

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


def create_battery_cost_curves():
    """
    reshapes and renames  the cost curve assumptions
    Note: Right now the inputs are very simple
    Ideally we should instead read and process CSIRO data then map to our techs
    Instead, we read in hardcoded assumptions. This method could be expanded

    These currently have TechName set directly, so these TechNames
    need to align with TechNames set in the main battery assumption input
    """

    df = pd.read_csv(battery_costs)

    df = df[["TechName", "Year", "CAPEX", "FOM"]].copy()

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

    cost_curves = create_battery_cost_curves()
    save_battery_data(cost_curves, "battery_costs.csv")


if __name__ == "__main__":
    main()
