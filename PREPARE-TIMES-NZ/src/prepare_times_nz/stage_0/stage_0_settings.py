"""

This script reads and surfaces several useful settings as constants you can import

These are effectively inputs for SysSettings, including:

a) Base year
b) Milestone years
c) Period definitions (PDef)

NOTE: This was developed slightly late in the process.
However, a lot of items should really be importing base and milestone years from here
So some scripts should be refactored

Year fractions are processed separately in load curves so are not included here
"""

# Libraries ------------------------------------------

import tomllib

import pandas as pd
from prepare_times_nz.utilities.filepaths import DATA_INTERMEDIATE, DATA_RAW
from prepare_times_nz.utilities.logger_setup import logger

# File locations ------------------------------------------
SETTINGS_ASSUMPTIONS = DATA_RAW / "user_config/settings"
SYSSETTINGS_TOML = DATA_INTERMEDIATE / "stage_0_config/SysSettings.toml"
MILESTONE_YEARS_FILE = SETTINGS_ASSUMPTIONS / "milestone_years.csv"

# Constants to distribute ----------------------------------------

CAP2ACT_PJGW: float = 31.536  # PJ per GW at 100 % utilisation (365 * 24 / 1000)


# Functions -----------------------------------------------


def get_sys_settings_data():
    """
    Reads SysSettings from the normalised toml files and return all data
    """
    syssettings_toml = SYSSETTINGS_TOML

    with open(syssettings_toml, "rb") as f:
        data = tomllib.load(f)

    return data


def get_base_year(data):
    """
    extracts base year from the syssettings data
    Note: StartYear is the name of the table and the column
    So we extract:
    THe table (StartYear)
    then its Data
    Then the StartYear variable
    Then the first element
    """
    return data["StartYear"]["Data"]["StartYear"][0]


def get_active_pdef(data):
    """
    Returns the name of the active PDef
    """
    return data["ActivePDef"]["Data"]["ActivePDef"][0]


def get_milestone_years_for_pdef(active_pdef, file=MILESTONE_YEARS_FILE):
    """
    Takes the input data of milestone years (assumptions file)
    This file can have an arbitrary set of possibilities
    Selects the Active PDef and returns only those values
    """
    df = pd.read_csv(file)

    # fail loud and early if nothing found
    if active_pdef not in df.columns:
        logger.error("No milestone years found for '%s'", active_pdef)
    # select only the relevant entry
    df = df[[active_pdef]]
    # remove nulls
    df = df[~df[active_pdef].isna()]
    # ensure integers
    df[active_pdef] = df[active_pdef].astype(int)

    # sort values (in unlikely event they aren't already)
    df = df.sort_values(active_pdef)

    return df


def create_period_definitions(by, df):
    """
    Using the milestone years and base year definition,
    create the active pdef years (returning a dataframe)

    by: the base year
    df: milestone year data
    Expects df to have only one variable, which is the current active_pdef

    """

    df = df.copy()

    if len(df.columns) != 1:
        logger.warning(
            "ALERT: period definitions data should have exactly one variable"
        )
        print(df)

    var_name = df.columns[0]

    # calculate relevant milestone years
    # (subtracting base year then taking the difference from previous milestone years)
    df[var_name] = df[var_name] - by + 1
    df[var_name] = df[var_name].diff().fillna(df[var_name])
    # make int again
    df[var_name] = df[var_name].astype(int)

    return df


# Execute -----------------------------------------------
# to have constants available to export

sys_settings_data = get_sys_settings_data()

# BASE_YEAR to be exported
BASE_YEAR = get_base_year(sys_settings_data)
pdef = get_active_pdef(sys_settings_data)
milestone_years = get_milestone_years_for_pdef(pdef)
active_periods = create_period_definitions(BASE_YEAR, milestone_years)

# other constants to export
MILESTONE_YEAR_LIST = milestone_years[pdef].tolist()
ACTIVE_PERIOD_LIST = active_periods[pdef].tolist()
