"""
This module uses raw inputs on "sector closures",
THese are effectively an assumption per sector on the price at which the sector closes

This is achieved by generating processes that meet the sector's demand without input energy
(But at the specified cost). If the model chooses these options

We currently assume this is only possible for industrial subsectors

"""

# Libraries

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA, STAGE_4_DATA

# Constants
CLOSURE_ASSUMPTIONS_FILE = ASSUMPTIONS / "demand_projections/sector_closures.csv"
OUTPUT_LOCATION = STAGE_4_DATA / "scen_demand"
INDUSTRY_BASEYEAR_FILE = STAGE_2_DATA / "industry/baseyear_industry_demand.csv"


# Functions


def save_data(df, name):
    """_save_data wrapper"""
    label = "Saving closure assumptions"
    _save_data(df, name, label, filepath=OUTPUT_LOCATION)


def get_closure_data(
    closure_file=CLOSURE_ASSUMPTIONS_FILE, by_file=INDUSTRY_BASEYEAR_FILE
):
    """
    Read in the assumptions for some sectors with closures
    Assign these to the relevant processes using base year data
    Label new closure processes
    """

    df = pd.read_csv(closure_file)
    by_data = pd.read_csv(by_file)

    by_data = by_data[["Sector", "Process", "CommodityOut"]].drop_duplicates()
    df = df.merge(by_data, on="Sector", how="left")

    df["Process"] = df["Process"] + "-CLOSURE"

    return df


def format_closure_data(df, default_start=BASE_YEAR + 1):
    """
    Format the results for Veda
    """

    df = df.rename(
        columns={
            "ClosurePrice": "ACTCOST",
            "Process": "TechName",
            "CommodityOut": "Comm-Out",
        }
    )

    # pull in start years from assumptions, if available,
    # otherwise set to base year + 1 default
    if "Start" in df.columns:
        df["START"] = df["Start"].fillna(default_start)
    else:
        df["START"] = default_start

    # always permanent lifetimes
    df["LIFE"] = 100

    # select only relevant

    df = df[["TechName", "Comm-Out", "ACTCOST", "START", "LIFE"]]

    return df


def get_process_declarations(df):
    """
    Builds process declarations file from generated processes
    """
    df["Sets"] = "DMD"
    df["Tact"] = "PJ"
    df["Tcap"] = "PJa"

    df = df[["Sets", "TechName", "Tact", "Tcap"]]

    return df


def main():
    """
    Entry point. Orchestrates functions.
    """
    df = get_closure_data()
    closure_df = format_closure_data(df)
    declarations = get_process_declarations(closure_df)

    save_data(closure_df, "closure_parameters.csv")
    save_data(declarations, "closure_declarations.csv")


if __name__ == "__main__":
    main()
