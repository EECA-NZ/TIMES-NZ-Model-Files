"""
Ok, so here we assign a TIMES code to define each process.

This should be a unique combination of sector, tech, fuel,
and use, GENERALLY speaking

What this means is that - because that is already the grain
of the data - users cannot swap techs for different output
requirements

Then the output commodity should be a unique combination of
sector, tech, and use

What this means, by default, is that because the commodity
is not defined by the fuel, any tech (regardless of fuel)
is able to provide it, so the model can choose different
fuels but not techs.

However, because the process is defined by the fuel, I
can't by default just put biomass in my coal boiler. I'd
need to buy a biomass boiler By default, we have no dual
fuel inputs

This covers the vast majority of our use cases. However,
it means that I can't swap between boilers, resistance
heaters, or heat pumps for my space heating. So we would
need to tweak that. There may be other areas we want to
tweak.

Current tweaks to default mapping:

1) Feedstock is not assigned the industry use of the fuel.
That's because this is combusted and contributes to energy
emissions
    - In reality, feedstock is either not combusted, or its
    combustion emissions contribute to IPPU, not energy
    emissions
2) Space heating is "technology agnostic"
    - This means any space heating demand could be met by
    resistance heaters, heat pumps, or whatever else we have.
    Process heating is more specific so we are not agnostic.

Assign TIMES process and commodity codes for each row of the
industry base-year data.

Default rules
-------------
* Process name  = Sector-Fuel-Technology-EndUse.
* Input  comm.  = IND-Fuel (combusted fuels).
* Output comm.  = Sector-Technology-EndUse.

Tweaks
------
1. Feedstock is **not** treated as an "IND" fuel commodity
   because its combustion belongs in IPPU emissions.
2. Space-heating demand is *technology agnostic* - any
   space-heating tech can meet it, so the output commodity
   drops the Technology element.

"""

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from __future__ import annotations

import os
from typing import List

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.csv_writers import save_dataframe_to_csv
from prepare_times_nz.utilities.filepaths import CONCORDANCES, STAGE_2_DATA
from prepare_times_nz.utilities.logger_setup import logger

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
RUN_TESTS: bool = True

OUTPUT_LOCATION = f"{STAGE_2_DATA}/industry/preprocessing"
CHECKS_LOCATION = f"{STAGE_2_DATA}/industry/checks/4_process_commodity_definitions"
os.makedirs(OUTPUT_LOCATION, exist_ok=True)
os.makedirs(CHECKS_LOCATION, exist_ok=True)

INDUSTRY_CONCORDANCES = f"{CONCORDANCES}/industry"

# Concordance tables – loaded at import time so they are module‑level constants
USE_CODES = pd.read_csv(f"{INDUSTRY_CONCORDANCES}/use_codes.csv")
TECH_CODES = pd.read_csv(f"{INDUSTRY_CONCORDANCES}/tech_codes.csv")
SECTOR_CODES = pd.read_csv(f"{INDUSTRY_CONCORDANCES}/sector_codes.csv")
FUEL_CODES = pd.read_csv(f"{INDUSTRY_CONCORDANCES}/fuel_codes.csv")

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------


def check_missing_times_codes(df: pd.DataFrame, varname: str) -> None:
    """Warn if any values lacked a TIMES code during a merge."""
    varname_times = f"{varname}_TIMES"
    missing = df[df[varname_times].isna()][[varname, varname_times]].drop_duplicates()

    if missing.empty:
        logger.info("Full %s code coverage found", varname)
        return

    logger.warning(
        "Warning: the following %d '%s' items have no TIMES code equivalent",
        len(missing),
        varname,
    )
    for _, row in missing.iterrows():
        logger.warning("        %s", row[varname])
    logger.warning(
        "This will lead to issues: please check the input concordance file and "
        "ensure you have full '%s' coverage",
        varname,
    )


def add_times_codes(
    df: pd.DataFrame, code_mapping: pd.DataFrame, varname: str
) -> pd.DataFrame:
    """Left‑join *code_mapping* onto *df* and (optionally) run coverage tests."""
    df = pd.merge(df, code_mapping, on=varname, how="left")
    if RUN_TESTS:
        check_missing_times_codes(df, varname)
    return df


def define_process_commodities(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``Process``, ``CommodityIn``, and ``CommodityOut`` columns to *df*."""
    original_columns: List[str] = list(df.columns)

    # Attach TIMES codes
    df = add_times_codes(df, USE_CODES, "EndUse")
    df = add_times_codes(df, TECH_CODES, "Technology")
    df = add_times_codes(df, SECTOR_CODES, "Sector")
    df = add_times_codes(df, FUEL_CODES, "Fuel")

    # Default naming rules
    df["Process"] = df[
        ["Sector_TIMES", "Fuel_TIMES", "Technology_TIMES", "EndUse_TIMES"]
    ].agg("-".join, axis=1)

    df["CommodityIn"] = "IND" + df[["Fuel_TIMES"]].agg("-".join, axis=1)
    df["CommodityOut"] = df[["Sector_TIMES", "Technology_TIMES", "EndUse_TIMES"]].agg(
        "-".join, axis=1
    )

    # Feedstock tweak – no industrial fuel commodity
    df["CommodityIn"] = np.where(
        df["EndUse"] == "Feedstock", df["Fuel_TIMES"], df["CommodityIn"]
    )
    logger.info("Adjusting feedstock to not use industrial fuel commodities")

    # Space‑heating tech‑agnostic tweak – drop Technology element
    df["CommodityOutTechAgnostic"] = df[["Sector_TIMES", "EndUse_TIMES"]].agg(
        "-".join, axis=1
    )
    df["CommodityOut"] = np.where(
        df["EndUse"] == "Low Temperature Heat (<100 C), Space Heating",
        df["CommodityOutTechAgnostic"],
        df["CommodityOut"],
    )
    logger.info("Allowing space‑heating demand to use any space‑heating technology")

    return df[["Process", "CommodityIn", "CommodityOut"] + original_columns]


def make_wide(df: pd.DataFrame) -> pd.DataFrame:
    """Convert long Value/Variable table to a wide format for inspection."""
    df["Variable"] = df["Variable"] + " (" + df["Unit"] + ")"
    df = df.drop("Unit", axis=1)

    id_cols = [c for c in df.columns if c not in ("Variable", "Value")]
    return df.pivot(index=id_cols, columns="Variable", values="Value").reset_index()


# ----------------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------------


def main() -> None:
    """Entrypoint for running the process/commodity definition stage."""
    # Input table
    df = pd.read_csv(f"{OUTPUT_LOCATION}/3_times_baseyear_with_assumptions.csv")

    # Transform
    df = define_process_commodities(df)

    # Save outputs
    save_dataframe_to_csv(
        df, OUTPUT_LOCATION, "4_times_baseyear_with_commodity_definitions.csv"
    )

    df_wide = make_wide(df)
    save_dataframe_to_csv(
        df_wide,
        CHECKS_LOCATION,
        "baseyear_with_commodities_wide.csv",
        label="data in wide format",
    )


# ----------------------------------------------------------------------------
# CLI guard
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
