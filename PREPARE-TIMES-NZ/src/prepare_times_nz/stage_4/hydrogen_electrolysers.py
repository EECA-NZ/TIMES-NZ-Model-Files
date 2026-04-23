"""
Creates Veda files for electrolyser specifications based on input assumptions

Need:

commodity declarations (handled directly by)
process declarations for electrolysis
distribution process declarations (remove these from downstream files)


process costs
process parameters
distribution parameters

also need to ensure that the commodities are registered with names in the explorer.
May need an explorer patch
"""

# libraries

import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_4_DATA

# constants
HYD_ASSUMPTIONS_DIR = ASSUMPTIONS / "hydrogen"
OUTPUT_DIR = STAGE_4_DATA / "subres_h2"


def save_hydrogen_data(df, filename, label):
    """
    Wrapper for save data
    """
    _save_data(df, filename, label=f"Saving hydrogen {label}", filepath=OUTPUT_DIR)


def declare_hydrogen_processes(df):
    """
    Uses the params_raw data to build the FI_Process table
    """

    df = df.copy()

    df["Tact"] = "PJ"
    df["Tcap"] = "PJa"
    df["Sets"] = "PRE"
    df["TsLvl"] = "DAYNITE"
    df["LimType"] = "FX"

    # only necessary vars
    df = df[["TechName", "Sets", "Tact", "Tcap", "TsLvl", "LimType"]]

    return df


def get_hydrogen_parameters(df):
    """
    standard params for electrolysis
    """

    df = df.copy()

    df["Comm-IN"] = "ELCDD"
    df["Comm-Out"] = "H2R"

    return df


def get_hydrogen_capex(df, scenario="Steady"):
    """
    create veda file for CAPEX
    Very simple - filter for scenario, then output
    only necessary vars
    assume params_raw data has correct var names already
    """

    df = df.copy()
    df = df[df["Scenario"] == scenario]

    df = df[["TechName", "Year", "INVCOST"]]

    return df


def main():
    """entry-point"""

    # load data
    params_raw = pd.read_csv(HYD_ASSUMPTIONS_DIR / "electrolyser_parameters.csv")
    cost_data = pd.read_csv(HYD_ASSUMPTIONS_DIR / "electrolyser_costs.csv")

    # process
    params = get_hydrogen_parameters(params_raw)
    processes = declare_hydrogen_processes(params_raw)
    costs_high = get_hydrogen_capex(cost_data, "Steady")
    costs_low = get_hydrogen_capex(cost_data, "Shift")

    # save
    save_hydrogen_data(params, "hydrogen_parameters.csv", "parameters")
    save_hydrogen_data(processes, "hydrogen_processes.csv", "processes")
    save_hydrogen_data(costs_low, "hydrogen_costs_low.csv", "low costs")
    save_hydrogen_data(costs_high, "hydrogen_costs_high.csv", "high costs")


if __name__ == "__main__":
    main()
