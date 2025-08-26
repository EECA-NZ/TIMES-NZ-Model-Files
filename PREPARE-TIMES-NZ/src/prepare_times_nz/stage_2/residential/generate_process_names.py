"""

Uses concordance defintions which map EEUD categories to TIMES codes 

Builds consistent process and commodity defintions based on these 

Also defines the topology: how technologies can meet different commodity needs
    for the sector


Uses the stage 3 input dataframe and a common codes module to attach codes 

codes are stored in residential concordances 

"""

from typing import List

import pandas as pd
from prepare_times_nz.stage_2.common.add_times_codes import add_times_codes
from prepare_times_nz.stage_2.residential.common import (
    PREPRO_DF_NAME_STEP3,
    PREPRO_DF_NAME_STEP4,
    PREPROCESSING_DIR,
    RESIDENTIAL_CONCORDANCES,
    RUN_TESTS,
    save_preprocessing,
)

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------


# Concordance tables – loaded at import time so they are module‑level constants
USE_CODES = pd.read_csv(RESIDENTIAL_CONCORDANCES / "use_codes.csv")
TECH_CODES = pd.read_csv(RESIDENTIAL_CONCORDANCES / "tech_codes.csv")
DWELL_CODES = pd.read_csv(RESIDENTIAL_CONCORDANCES / "dwellingtype_codes.csv")
FUEL_CODES = pd.read_csv(RESIDENTIAL_CONCORDANCES / "fuel_codes.csv")

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------


def define_residential_process_commodities(
    df: pd.DataFrame, run_tests=RUN_TESTS
) -> pd.DataFrame:
    """Add ``Process``, ``CommodityIn``, and ``CommodityOut`` columns to *df*."""
    original_columns: List[str] = list(df.columns)

    # Attach TIMES codes
    df = add_times_codes(df, USE_CODES, "EndUse", run_tests=run_tests)
    df = add_times_codes(df, TECH_CODES, "Technology", run_tests=run_tests)
    df = add_times_codes(df, DWELL_CODES, "DwellingType", run_tests=run_tests)
    df = add_times_codes(df, FUEL_CODES, "Fuel", run_tests=run_tests)

    # Default naming rules
    df["Process"] = "RES-" + df[
        ["DwellingType_TIMES", "Fuel_TIMES", "Technology_TIMES", "EndUse_TIMES"]
    ].agg("-".join, axis=1)

    df["CommodityIn"] = "RES" + df[["Fuel_TIMES"]].agg("-".join, axis=1)
    # NOTE: All output commodities are tech-agnostic in the residential sector
    df["CommodityOut"] = df[["DwellingType_TIMES", "EndUse_TIMES"]].agg(
        "-".join, axis=1
    )

    return df[["Process", "CommodityIn", "CommodityOut"] + original_columns]


def main():
    """
    Loads input data, adds codes from concordances
    fails if concordances not written correctly (so adjust inputs as needed)
    Builds the process and commodity codes
    outputs original dataframe with new Process, CommodityIn, and CommodityOut fields
    saves to output location
    """
    df = pd.read_csv(PREPROCESSING_DIR / PREPRO_DF_NAME_STEP3)
    df = define_residential_process_commodities(df)
    save_preprocessing(df, PREPRO_DF_NAME_STEP4, "Residential process data")
