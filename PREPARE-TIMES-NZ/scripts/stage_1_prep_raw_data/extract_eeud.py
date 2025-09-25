"""
Extract and clean EEUD (Energy End-Use Database) data for the TIMES-NZ
pre-processing pipeline.

Steps performed
---------------
1. Read the EEUD "Data" sheet from the raw Excel workbook.
2. Tidy column names, derive useful fields, and coerce values.
3. Write a CSV copy to "data_intermediate/stage_1_input_data/eeud".

This script is idempotent: it recreates its output each time it runs.

Run directly::

    python -m prepare_times_nz.stages.extract_eeud

or import :pyfunc:`main` from elsewhere in the project or tests.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd
from prepare_times_nz.utilities.data_cleaning import rename_columns_to_pascal
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, DATA_RAW, STAGE_1_DATA

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Constants and paths
# ---------------------------------------------------------------------------
EEUD_FILENAME: Final[str] = "Final EEUD Outputs 2017 - 2023 12032025.xlsx"

INPUT_DIR = Path(DATA_RAW) / "eeca_data" / "eeud"
OUTPUT_DIR = Path(STAGE_1_DATA) / "eeud"
OUTPUT_FILE = OUTPUT_DIR / "eeud.csv"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def read_eeud(source_dir: Path, filename: str) -> pd.DataFrame:
    """Read the EEUD *filename* from *source_dir* and return the raw Data sheet."""
    file_path = source_dir / filename
    logger.info("Reading EEUD workbook %s", file_path)
    return pd.read_excel(file_path, engine="openpyxl", sheet_name="Data")


def clean_eeud_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply standard cleaning and reshaping to the EEUD DataFrame."""
    # Standardise column names to PascalCase
    df = rename_columns_to_pascal(df)

    # Add Year column derived from the period end date
    df["Year"] = df["PeriodEndDate"].dt.year

    # Force EnergyValue to numeric, storing it in a generic Value column
    df["Value"] = pd.to_numeric(df["EnergyValue"], errors="coerce")

    # Add a Unit column (all TJ)
    df["Unit"] = "TJ"

    # Drop superseded columns
    df = df.drop(columns=["EnergyValue", "PeriodEndDate"])

    return df


def add_biomass_patch_to_eeud(df: pd.DataFrame) -> pd.DataFrame:
    """Add missing biomass demand to outputs"""

    # load patch
    patch_df = pd.read_csv(
        ASSUMPTIONS / "biomass_demand_patch/biomass_demand_patch.csv"
    )

    # identify key structure of input file
    current_years = df["Year"].drop_duplicates()
    eeud_cols = df.columns
    eeud_index = [col for col in eeud_cols if col not in ["Year", "Value"]]

    # use the above to pivot patch data
    patch_df = pd.melt(
        patch_df, id_vars=eeud_index, value_name="Value", var_name="Year"
    )

    # ensure the patch only has years in current eeud. Clarify years are int:
    patch_df["Year"] = patch_df["Year"].astype(int)
    # filter against EEUD years
    patch_df = patch_df[patch_df["Year"].isin(current_years)]
    # strict match column structure
    patch_df = patch_df[eeud_cols]

    # join
    df = pd.concat([df, patch_df])

    return df


# ---------------------------------------------------------------------------
# Main script execution
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry-point safe for import or CLI execution."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_df = read_eeud(INPUT_DIR, EEUD_FILENAME)
    tidy_df = clean_eeud_data(raw_df)
    # patched_df = add_biomass_patch_to_eeud(tidy_df)

    tidy_df.to_csv(OUTPUT_FILE, index=False)
    logger.info("EEUD data written to %s", OUTPUT_FILE)

    df = add_biomass_patch_to_eeud(tidy_df)

    print(df)


if __name__ == "__main__":
    main()
