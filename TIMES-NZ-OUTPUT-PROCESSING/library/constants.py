"""
This module contains constants used by the scripts (under development) that aim to re-generate the schema dataframe.
"""
import re
import os

TIMES_NZ_VERSION = os.getenv('TIMES_NZ_VERSION', '2.1.2')
VERSION_STR = TIMES_NZ_VERSION.replace('.', '_')

def get_project_base_path():
    """
    Determines and returns the absolute path to the project base directory.

    Assumes the script is located within a subdirectory of the project base directory,
    commonly under a 'scripts' or similar directory. This function calculates the path
    relative to the current file's location (__file__).

    Returns:
        str: The absolute path to the project base directory.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.dirname(script_dir)

# Initialize the base path for the project, used for constructing paths to other resources.
project_base_path = get_project_base_path()

# List of VEDA Data (VD) files to be read and processed.
INPUT_VD_FILES = [
    os.path.join(project_base_path, "../TIMES-NZ-GAMS/scenarios", f"kea-v{VERSION_STR}", f"kea-v{VERSION_STR}.vd"),
    os.path.join(project_base_path, "../TIMES-NZ-GAMS/scenarios", f"tui-v{VERSION_STR}", f"tui-v{VERSION_STR}.vd"),
]

# Path to a TIMES base.dd file containing commodity to unit mappings.
BASE_DD_FILEPATH = os.path.join(project_base_path, f"../TIMES-NZ-GAMS/scenarios/kea-v{VERSION_STR}", "base.dd")

ITEMS_LIST_COMMODITY_CSV = os.path.join(project_base_path, "data/input", "Items-List-Commodity.csv")

ITEMS_LIST_PROCESS_CSV = os.path.join(project_base_path, "data/input", "Items-List-Process.csv")

ITEMS_LIST_COMMODITY_GROUPS_CSV = os.path.join(project_base_path, "data/input", "Items-List-Commodity-Groups.csv")

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
SUP_COLS = [
    "Set",
    "DisplayCapacity"
]

# Mapping for sanitizing unit names.
SANITIZE_UNITS = {
    None: None,
    "PJ": "PJ",
    "kt": "kt CO2",
    "BVkm": "Billion Vehicle Kilometres",
}

# Define the path to the output schema CSV file.
OUTPUT_SCHEMA_FILEPATH = os.path.join(project_base_path, f"data/output/output_schema_df_v{VERSION_STR}.csv")

# Define the path to the reference (manually created) schema CSV file.
REFERENCE_SCHEMA_FILEPATH = os.path.join(project_base_path, f"data/reference/reference_schema_df_v2_0_0.csv")

# Define the path to the output cleaned DataFrame CSV file.
OUTPUT_COMBINED_DF_FILEPATH = os.path.join(project_base_path, f"data/output/output_combined_df_v{VERSION_STR}.csv")

# Define the path to the reference (manually created) cleaned DataFrame CSV file.
REFERENCE_COMBINED_DF_FILEPATH = os.path.join(project_base_path, f"data/reference/reference_combined_df_v2_0_0.csv")

IGNORE_EXPORT_COMMODITIES =[
    'TB_ELC_NI_SI_01',
    'TU_DID_NI_SI_01',
    'TU_PET_NI_SI_01',
    'TU_OTH_NI_SI_01',
    'TU_FOL_NI_SI_01',
    'TU_DIJ_NI_SI_01',
    'TU_COA_NI_SI_01',
    'TU_COL_NI_SI_01',
    'TU_COA_SI_NI_01',
    'TU_LPG_NI_SI_01',
    'TU_DSL_NI_SI_01',
    'TU_JET_NI_SI_01',
    'TU_COL_SI_NI_01'
]

trade_processes = re.compile(r'^TU_(PET|LPG|DSL|FOL|DID|DIJ|JET|OTH|COA|COL).*') # these are excluded from consideration when allocating emissions reductions to end-use processes.

elc_exchange_processes = re.compile(r'^TB_ELC.*')

elc_grid_processes = re.compile(r'^G_ELC.*')

import_processes = re.compile(r'^IMP(COA|DSL|FOL|JET|LPG|OIL|OTH|PET|DIJ).*')

export_processes = re.compile(r'^EXP(DSL|FOL|JET|LPG|OIL|OTH|PET).*')

