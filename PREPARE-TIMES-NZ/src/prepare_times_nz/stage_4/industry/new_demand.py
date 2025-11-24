"""
This module simply creates the commodity demand projection for NEWTECH-DEM
This commodity is defined in the subres so the output file here can be used to
switch on/off this additional electricity demand

We can make this a bit more sophisticated later.
"""

import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA

# CONSTANTS

# when the new commodity begins
START = 2026
# annual demand growth in gwh
GWH_GROWTH = 50
# how much is in the NI (assume 80%)
NI_SHARE = 0.8

# other basic inputs
COMMODITY_NAME = "NEWTECH-DEM"
PJ_PER_GWH = 0.0036
END = 2060


def create_newtech_demand():
    """
    Compiles newtech constants into standard dataframe
    """

    df = pd.DataFrame()
    df["Year"] = range(START, END + 1)
    # increase demand by 50gwh a year
    df["Value"] = GWH_GROWTH * (df["Year"] + 1 - START)
    # transform PJ
    df["Value"] = df["Value"] * PJ_PER_GWH

    # island split
    df["NI"] = df["Value"] * NI_SHARE
    df["SI"] = df["Value"] * (1 - NI_SHARE)

    return df


def make_veda_newdemand(df):
    """
    reshapes newdemand for veda
    """

    df["TimeSlice"] = ""
    df["Attribute"] = "Demand"
    df["Cset_CN"] = COMMODITY_NAME

    # reorder

    df = df[["TimeSlice", "Attribute", "Cset_CN", "Year", "NI", "SI"]]

    return df


def main():
    """entrypoint"""
    df = create_newtech_demand()
    df = make_veda_newdemand(df)

    _save_data(
        df,
        "newtech_demand.csv",
        "Demand projections for new techs",
        STAGE_4_DATA / "scen_demand",
    )


if __name__ == "__main__":
    main()
