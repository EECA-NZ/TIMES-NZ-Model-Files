"""
Defines filepaths used by TIMES-NZ-INTERNAL-QA
"""

from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent

# main directories
QA_LOCATION = _REPO_ROOT
DATA_RAW = QA_LOCATION / "data_raw"
ASSETS = QA_LOCATION / "assets"

DATA = QA_LOCATION / "data"

SCENARIO_FILES = DATA_RAW / "scenario_files"
CONCORDANCE_PATCHES = DATA_RAW / "concordance_patches"


# External locations - for defining concordance files
PREP_LOCATION = QA_LOCATION.parent / "PREPARE-TIMES-NZ"
PREP_STAGE_0 = PREP_LOCATION / "data_intermediate/stage_0_config"
PREP_STAGE_2 = PREP_LOCATION / "data_intermediate/stage_2_baseyear_data"
PREP_STAGE_3 = PREP_LOCATION / "data_intermediate/stage_3_scenario_data"
PREP_STAGE_4 = PREP_LOCATION / "data_intermediate/stage_4_veda_format"

# Main concordance files - used for generating output data
PROCESS_CONCORDANCES = DATA / "concordances/processes"
COMMODITY_CONCORDANCES = DATA / "concordances/commodities"

# For storing results
FINAL_DATA = DATA / "clean_results"
