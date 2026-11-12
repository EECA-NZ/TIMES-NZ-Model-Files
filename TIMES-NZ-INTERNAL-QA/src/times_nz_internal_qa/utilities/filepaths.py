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


# External location used by remaining analysis helpers
PREP_LOCATION = QA_LOCATION.parent / "PREPARE-TIMES-NZ"
PREP_STAGE_2 = PREP_LOCATION / "data_intermediate/stage_2_baseyear_data"

# For storing results
FINAL_DATA = DATA / "clean_results"

ANALYSIS = QA_LOCATION / "analysis"
ANALYSIS_RESULTS = ANALYSIS / "results"
