"""
This file surfaces our directory locations for anything else to reference

This way any scripts can use these without hardcoding,
which ensures consistent locations for the whole system
We use Path variables to ensure consistency across separate environments.

Note that this file expects to be in a specific location to find _REPO_ROOT
That means if this file is moved, the _REPO_ROOT definition will need to change

Note that output and data intermediate directories are currently wiped on each run
THese are based on the addresses defined in this file.

"""

from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent

# main directories
PREP_LIBRARY_LOCATION = _THIS_DIR
PREP_LOCATION = _REPO_ROOT
TIMES_LOCATION = _REPO_ROOT.parent

# Data directories (Top-level)
OUTPUT_LOCATION = PREP_LOCATION / "output"
DATA_INTERMEDIATE = PREP_LOCATION / "data_intermediate"
DATA_RAW = PREP_LOCATION / "data_raw"

# Data raw subfolders

ASSUMPTIONS = DATA_RAW / "coded_assumptions"
CONCORDANCES = DATA_RAW / "concordances"

# Data intermediate subfolders

STAGE_1_DATA = DATA_INTERMEDIATE / "stage_1_input_data"
STAGE_2_DATA = DATA_INTERMEDIATE / "stage_2_baseyear_data"
STAGE_3_DATA = DATA_INTERMEDIATE / "stage_3_scenario_data"
STAGE_4_DATA = DATA_INTERMEDIATE / "stage_4_veda_format"

# Scripts

STAGE_0_SCRIPTS = PREP_LOCATION / "scripts/stage_0_settings"
STAGE_1_SCRIPTS = PREP_LOCATION / "scripts/stage_1_prep_raw_data"
STAGE_2_SCRIPTS = PREP_LOCATION / "scripts/stage_2_baseyear"
STAGE_3_SCRIPTS = PREP_LOCATION / "scripts/stage_3_scenarios"
STAGE_4_SCRIPTS = PREP_LOCATION / "scripts/stage_4_veda_format"
