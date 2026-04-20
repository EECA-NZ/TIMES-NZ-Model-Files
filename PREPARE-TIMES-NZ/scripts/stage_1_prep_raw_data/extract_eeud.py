"""
Extract and clean EEUD (Energy End-Use Database) data for the TIMES-NZ
pre-processing pipeline.

Steps performed
---------------
1. Read the EEUD "Data" sheet from the raw Excel workbook.
2. Tidy column names, derive useful fields, and coerce values.
3. Add biomass patch assumptions for missing industrial/commercial demand
4. Write a CSV copy to "data_intermediate/stage_1_input_data/eeud".
5. Write an CSV copy of unpatched data to the same directory

This script is idempotent: it recreates its output each time it runs.

Run directly::

    python -m prepare_times_nz.stages.extract_eeud

or import :pyfunc:`main` from elsewhere in the project or tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd
from prepare_times_nz.utilities.data_cleaning import rename_columns_to_pascal
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, DATA_RAW, STAGE_1_DATA
from prepare_times_nz.utilities.logger_setup import logger

# ---------------------------------------------------------------------------
# Constants and paths
# ---------------------------------------------------------------------------
# EEUD_FILENAME: Final[str] = "Final EEUD Outputs 2017 - 2023 12032025.xlsx"
EEUD_FILENAME: Final[str] = "EEUD 2017 - 2024 FINAL 20032026.xlsx"

INPUT_DIR = Path(DATA_RAW) / "eeca_data" / "eeud"
OUTPUT_DIR = Path(STAGE_1_DATA) / "eeud"
SHEET_NAME = "Data"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def save_eeud(df, name):
    """_save_data wrapper"""
    _save_data(df, name, label="Saving EEUD", filepath=OUTPUT_DIR)


# pylint: disable=duplicate-code
def resolve_input_filename(source_dir: Path, filename: str) -> Path:
    """Return an EEUD input path, matching case-insensitively when needed."""
    exact_match = source_dir / filename
    if exact_match.exists():
        return exact_match

    filename_lower = filename.casefold()
    for candidate in source_dir.iterdir():
        if candidate.is_file() and candidate.name.casefold() == filename_lower:
            logger.info(
                "Resolved EEUD input %s to %s using case-insensitive match.",
                filename,
                candidate.name,
            )
            return candidate

    raise FileNotFoundError(f"Could not find EEUD input file: {source_dir / filename}")


def read_eeud(source_dir: Path, filename: str) -> pd.DataFrame:
    """Read the EEUD *filename* from *source_dir* and return the raw Data sheet."""
    file_path = resolve_input_filename(source_dir, filename)
    return pd.read_excel(file_path, engine="openpyxl", sheet_name=SHEET_NAME)


def clean_eeud_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply standard cleaning and reshaping to the EEUD DataFrame."""
    # Standardise column names to PascalCase

    df = df.rename(columns={"EnergyValue (Terrajoules)": "EnergyValue"})
    df = rename_columns_to_pascal(df)

    # Add Year column derived from the period end date
    df["Year"] = df["PeriodEndDate"].dt.year

    # Force EnergyValue to numeric, storing it in a generic Value column
    df["Value"] = pd.to_numeric(df["EnergyValue"], errors="coerce")

    # Add a Unit column (all TJ)
    df["Unit"] = "TJ"

    # Drop superseded columns
    df = df.drop(columns=["EnergyValue", "PeriodEndDate"])

    # Normalize residential labels that changed in the newer EEUD workbook
    geo_mask = (
        (df["Sector"] == "Residential")
        & (df["Fuel"] == "Geothermal")
        & (df["Technology"] == "Direct Heat")
        & (df["EndUse"] == "Low Temperature Heat (<100 C), Space Heating")
    )
    df.loc[geo_mask, "Technology"] = "Ground source heat pump"

    solar_mask = (
        (df["Sector"] == "Residential")
        & (df["Fuel"] == "Solar")
        & df["Technology"].isna()
    )
    df.loc[solar_mask, "TechnologyGroup"] = "Heat/Cooling Devices"
    df.loc[solar_mask, "Technology"] = "Solar hot water cylinder"
    df.loc[solar_mask, "EnduseGroup"] = "Heating/Cooling"
    df.loc[solar_mask, "EndUse"] = "Low Temperature Heat (<100 C), Water Heating"

    return df


def add_patch_to_eeud(df: pd.DataFrame, patch_filename) -> pd.DataFrame:
    """
    A generic function to add custom additional data to the EEUD
    This is for demand data that is exlcuded from the existing database
    CUrrently this is unallocated electricity demand and some industrial/commercial biomass
    """

    # load patch
    patch_df = pd.read_csv(ASSUMPTIONS / f"eeud_patches/{patch_filename}")

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

    patched_df = tidy_df.copy()
    patched_df = add_patch_to_eeud(patched_df, "biomass_demand_patch.csv")
    patched_df = add_patch_to_eeud(patched_df, "unallocated_demand_patch.csv")

    save_eeud(tidy_df, "eeud_no_patch.csv")
    save_eeud(patched_df, "eeud.csv")


if __name__ == "__main__":
    main()
