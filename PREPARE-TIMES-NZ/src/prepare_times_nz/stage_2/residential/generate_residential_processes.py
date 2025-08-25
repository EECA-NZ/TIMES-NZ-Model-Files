from typing import List

import numpy as np
import pandas as pd
from prepare_times_nz.stage_2.common.add_times_codes import add_times_codes
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_1_DATA,
    STAGE_2_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
RUN_TESTS: bool = True

OUTPUT_LOCATION = STAGE_2_DATA / "residential/"
OUTPUT_LOCATION.mkdir(exist_ok=True)

INPUT_FILE = OUTPUT_LOCATION / "residential_demand_with_assumptions.csv"
OUTPUT_FILE = OUTPUT_LOCATION / "residential_demand_processes.csv"

RES_CONCORDANCES = CONCORDANCES / "residential"

# Concordance tables – loaded at import time so they are module‑level constants
USE_CODES = pd.read_csv(RES_CONCORDANCES / "use_codes.csv")
TECH_CODES = pd.read_csv(RES_CONCORDANCES / "tech_codes.csv")
DWELL_CODES = pd.read_csv(RES_CONCORDANCES / "dwellingtype_codes.csv")
FUEL_CODES = pd.read_csv(RES_CONCORDANCES / "fuel_codes.csv")

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------


RUN_TESTS = True


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


def main(input_file, output_file):
    """
    Loads input data, adds codes from concordances
    fails if concordances not written correctly (so adjust inputs as needed)
    Builds the process and commodity codes
    outputs original dataframe with new Process, CommodityIn, and CommodityOut fields
    saves to output location
    """

    df = pd.read_csv(input_file)
    df = define_residential_process_commodities(df)
    df.to_csv(output_file, index=False)
