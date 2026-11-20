"""
A common area for all filepaths and functions common to
 commercial baseyear processing submodules.


"""

from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_2_DATA,
)

# Constants ------------------------------------------------
BASE_YEAR = 2023
RUN_TESTS = False
CAP2ACT = 31.536

# Filepaths ------------------------------------------------


AG_ASSUMPTIONS = ASSUMPTIONS / "ag_forest_fish_demand"
AG_CONCORDANCES = CONCORDANCES / "ag_forest_fish"
AG_DATA_DIR = STAGE_2_DATA / "ag_forest_fish"

CHECKS_DIR = AG_DATA_DIR / "checks"
PREPROCESSING_DIR = AG_DATA_DIR / "preprocessing"

# Preprocessing names ---------------------------------------

PREPRO_DF_NAME_STEP1 = "1_times_eeud_alignment_baseyear.csv"
PREPRO_DF_NAME_STEP2 = "2_ag_forest_fish_regional_demand_split.csv"
PREPRO_DF_NAME_STEP3 = "3_times_baseyear_with_assumptions.csv"
PREPRO_DF_NAME_STEP4 = "4_times_baseyear_with_commodity_definitions.csv"


# I/O Functions ------------------------------------------------


def save_output(df, name, label, filepath=AG_DATA_DIR):
    """Save DataFrame output to the output location."""
    label = f"Saving output ({label})"
    _save_data(df=df, name=name, label=label, filepath=filepath)


def save_preprocessing(df, name, label, filepath=PREPROCESSING_DIR):
    """Save DataFrame output to the output location."""
    label = f"Saving preprocessing ({label})"
    _save_data(df=df, name=name, label=label, filepath=filepath)


def save_checks(df, name, label, filepath=CHECKS_DIR):
    """Save DataFrame output to the checks location."""
    label = f"Saving checking output ({label})"
    _save_data(df=df, name=name, label=label, filepath=filepath)
