"""
Constants and helpers for creating electricity files for Veda.
We can offload functions and constants here if they're used in multiple places

"""

# Libraries ---------------------------------------

import pandas as pd

# Constants ----------------------------------

CAPACITY_UNIT = "GW"
ACTIVITY_UNIT = "PJ"
TIMESLICE_LEVEL = "DAYNITE"
VINTAGE_TRACKING = "YES"
SETS_STG = "ELE, STG"
SETS_ELE = "ELE"
CAP2ACT = 31.536


# Helpers ---------------------------------------


def create_process_file(df, sets=SETS_ELE):
    """
    Takes an input file including TechName
    automatically produces the table appropriate for FI_Process

    can use different sets if needed (eg for storage technologies)
    but otherwise inherits all the constants set in this script
    """

    out = pd.DataFrame()
    out["TechName"] = df["TechName"].unique()

    # arrange sets first
    out["Sets"] = sets
    out = out[["Sets", "TechName"]]
    # add the rest of the inputs for the process table

    out["Tact"] = ACTIVITY_UNIT
    out["Tcap"] = CAPACITY_UNIT
    out["Tslvl"] = TIMESLICE_LEVEL
    out["Vintage"] = VINTAGE_TRACKING

    return out
