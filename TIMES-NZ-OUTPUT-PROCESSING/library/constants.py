"""
This module contains constants used by the scripts
that label the TIMES-NZ output dataframe.
"""

import re
import os

TIMES_NZ_VERSION = os.getenv("TIMES_NZ_VERSION", "0.1.0")

VERSION_STR = TIMES_NZ_VERSION.replace(".", "_")

TOL = 1e-6

GROUP_COLUMNS = [
    "Scenario",
    "Sector",
    "Subsector",
    "Technology",
    "Enduse",
    "Unit",
    "Parameters",
    "Fuel",
    "Period",
    "FuelGroup",
    "Technology_Group",
    "ProcessSet",
    "CommoditySet",
]

PATH_TO_SCENARIOS = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "../../TIMES-NZ-GAMS/times_scenarios"
)

SCENARIO_INPUT_FILES = {
    "Kea": os.path.join(
        PATH_TO_SCENARIOS,
        f"kea-v{VERSION_STR}",
        f"kea-v{VERSION_STR}.vd"
    ),
    "Tui": os.path.join(
        PATH_TO_SCENARIOS,
        f"tui-v{VERSION_STR}",
        f"tui-v{VERSION_STR}.vd"
    ),
}

NEEDED_ATTRIBUTES = ["VAR_Cap", "VAR_FIn", "VAR_FOut"]

NON_EMISSION_FUEL = [
    "Electricity",
    "Wood",
    "Hydrogen",
    "Hydro",
    "Wind",
    "Solar",
    "Biogas",
]

FOSSIL_FROM_RENEWABLE_FUEL_MAP = {
    "Drop-In Diesel": "Diesel",
    "Drop-In Jet": "Jet Fuel",
    "Biodiesel": "Diesel",
}


def get_project_base_path():
    """
    Determines and returns the absolute path to the
    project base directory.

    Assumes the script is located within a subdirectory
    of the project base directory, commonly under a
    'scripts' or similar directory. This function calculates
    the path relative to the current file's location (__file__).

    Returns:
        str: The absolute path to the project base directory.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.dirname(script_dir)


# Initialize the base path for the project, used for constructing paths to other resources.
project_base_path = get_project_base_path()

# List of VEDA Data (VD) files to be read and processed.
INPUT_VD_FILES = [
    os.path.join(
        project_base_path,
        "../TIMES-NZ-GAMS/times_scenarios",
        f"kea-v{VERSION_STR}",
        f"kea-v{VERSION_STR}.vd",
    ),
    os.path.join(
        project_base_path,
        "../TIMES-NZ-GAMS/times_scenarios",
        f"tui-v{VERSION_STR}",
        f"tui-v{VERSION_STR}.vd",
    ),
]

# Path to a TIMES base.dd file containing commodity to unit mappings.
BASE_DD_FILEPATH = os.path.join(
    project_base_path, f"../TIMES-NZ-GAMS/times_scenarios/kea-v{VERSION_STR}", "base.dd"
)

ITEMS_LIST_COMMODITY_CSV = os.path.join(
    project_base_path, "data/input", "Items-List-Commodity.csv"
)

ITEMS_LIST_PROCESS_CSV = os.path.join(
    project_base_path, "data/input", "Items-List-Process.csv"
)

ITEMS_LIST_COMMODITY_GROUPS_CSV = os.path.join(
    project_base_path, "data/input", "Items-List-Commodity-Groups.csv"
)

# Attributes to retain during data processing.
ATTRIBUTE_ROWS_TO_KEEP = ["VAR_Cap", "VAR_FIn", "VAR_FOut"]

# Define output and supplementary columns for the resulting DataFrame.
OUT_COLS = [
    "Attribute",
    "Process",
    "Commodity",
    "Sector",
    "Subsector",
    "Technology",
    "Fuel",
    "Enduse",
    "Unit",
    "Parameters",
    "FuelGroup",
]
SUP_COLS = ["ProcessSet", "CommoditySet", "DisplayCapacity"]

# Mapping for sanitizing unit names.
SANITIZE_UNITS = {
    None: None,
    "PJ": "PJ",
    "kt": "kt CO2",
    "BVkm": "Billion Vehicle Kilometres",
}

# Define the path to the output schema CSV file.
OUTPUT_SCHEMA_FILEPATH = os.path.join(
    project_base_path, f"data/output/output_schema_df_v{VERSION_STR}.csv"
)

# Define the path to the output cleaned DataFrame CSV file.
OUTPUT_COMBINED_DF_FILEPATH = os.path.join(
    project_base_path, f"data/output/output_combined_df_v{VERSION_STR}.csv"
)

IGNORE_EXPORT_COMMODITIES = [
    "TB_ELC_NI_SI_01",
    "TU_DID_NI_SI_01",
    "TU_PET_NI_SI_01",
    "TU_OTH_NI_SI_01",
    "TU_FOL_NI_SI_01",
    "TU_DIJ_NI_SI_01",
    "TU_COA_NI_SI_01",
    "TU_COL_NI_SI_01",
    "TU_COA_SI_NI_01",
    "TU_LPG_NI_SI_01",
    "TU_DSL_NI_SI_01",
    "TU_JET_NI_SI_01",
    "TU_COL_SI_NI_01",
]

# these are excluded from consideration when allocating
# emissions reductions to end-use processes:
trade_processes = re.compile(
    r"^TU_(PET|LPG|DSL|FOL|DID|DIJ|JET|OTH|COA|COL).*"
)

elc_exchange_processes = re.compile(r"^TB_ELC.*")

elc_grid_processes = re.compile(r"^G_ELC.*")

import_processes = re.compile(r"^IMP(COA|DSL|FOL|JET|LPG|OIL|OTH|PET|DIJ).*")

export_processes = re.compile(r"^EXP(DSL|FOL|JET|LPG|OIL|OTH|PET).*")
