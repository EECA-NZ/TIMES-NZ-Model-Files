"""
Saves all the inputs that are processed separately for syssettings

This includes things like the active periods and the year fraction definitions

"""

import pandas as pd

# active periods are never saved anywhere, we take this from the module that creates it
from prepare_times_nz.stage_0.stage_0_settings import active_periods
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_2_DATA, STAGE_4_DATA

# Constants -------------------------------------------------------
OUTPUT_LOCATION = STAGE_4_DATA / "sys_settings"

yrfr_file = STAGE_2_DATA / "settings/load_curves/yrfr.csv"


# Helpers -------------------------------------------------------


def save_settings_data(df, name):
    """save_data wrapper for settings files"""
    _save_data(df, name=name, label="Settings file", filepath=OUTPUT_LOCATION)


def get_yrfr(file_location):
    """
    Reshapes our yrfr outputs to match Veda expectations
    """
    df = pd.read_csv(file_location)
    # label
    df["Attribute"] = "YRFR"
    # rename
    df = df.rename(columns={"YRFR": "AllRegions"})
    # select
    df = df[["TimeSlice", "Attribute", "AllRegions"]]
    return df


# Execute -------------------------------------------


def main():
    """coordinates this script"""
    save_settings_data(active_periods, "active_periods.csv")
    yrfr = get_yrfr(yrfr_file)
    save_settings_data(yrfr, "yrfr.csv")


if __name__ == "__main__":
    main()
