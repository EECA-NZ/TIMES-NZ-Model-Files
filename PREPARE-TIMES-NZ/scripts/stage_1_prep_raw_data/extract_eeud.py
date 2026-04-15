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

import tomllib
from pathlib import Path
from typing import Final

import pandas as pd
from prepare_times_nz.utilities.data_cleaning import rename_columns_to_pascal
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, DATA_RAW, STAGE_1_DATA
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# ---------------------------------------------------------------------------
# Constants and paths
# ---------------------------------------------------------------------------
EEUD_FILENAME: Final[str] = "Final EEUD Outputs 2017 - 2023 12032025.xlsx"

INPUT_DIR = Path(DATA_RAW) / "eeca_data" / "eeud"
OUTPUT_DIR = Path(STAGE_1_DATA) / "eeud"
MANUAL_REVISIONS_FILE = ASSUMPTIONS / "eeud_patches/manual_revisions.toml"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def save_eeud(df, name):
    """_save_data wrapper"""
    _save_data(df, name, label="Saving EEUD", filepath=OUTPUT_DIR)


def read_eeud(source_dir: Path, filename: str) -> pd.DataFrame:
    """Read the EEUD *filename* from *source_dir* and return the raw Data sheet."""
    file_path = source_dir / filename
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


def read_manual_eeud_revisions() -> list[dict]:
    """Read manual EEUD revision rules from disk."""
    if not MANUAL_REVISIONS_FILE.exists():
        logger.info("No manual EEUD revision file found at %s", MANUAL_REVISIONS_FILE)
        return []

    with open(MANUAL_REVISIONS_FILE, "rb") as file_obj:
        config = tomllib.load(file_obj)

    revisions = config.get("revision", [])
    if not revisions:
        logger.info(
            "No manual EEUD revisions defined in %s", MANUAL_REVISIONS_FILE.name
        )
    return revisions


def get_revision_conditions(revision: dict, revision_number: int) -> tuple[dict, float]:
    """Split a revision into filter conditions and target total."""
    if "Total" not in revision:
        raise ValueError(
            f"Manual EEUD revision #{revision_number} is missing required key 'Total'."
        )

    conditions = {key: value for key, value in revision.items() if key != "Total"}
    if not conditions:
        raise ValueError(
            f"Manual EEUD revision #{revision_number} must include at least one filter."
        )

    return conditions, float(revision["Total"])


def get_revision_mask(
    df: pd.DataFrame, conditions: dict, revision_number: int
) -> pd.Series:
    """Build a boolean mask for rows matched by one revision."""
    mask = pd.Series(True, index=df.index)
    for column, expected_value in conditions.items():
        if column not in df.columns:
            raise KeyError(
                f"Manual EEUD revision #{revision_number} refers to unknown column "
                f"'{column}'."
            )
        mask &= df[column] == expected_value
    return mask


def log_revision_result(summary: dict) -> None:
    """Log a summary of one manual EEUD revision."""
    absolute_change = summary["target_total"] - summary["current_total"]
    percentage_change = (
        0.0
        if summary["current_total"] == 0
        else (absolute_change / summary["current_total"]) * 100
    )
    logger.info(
        "Applied manual EEUD revision: Filters=%s ",
        blue_text(str(summary["conditions"])),
    )
    logger.info(
        "Old: %s TJ -> New: %s TJ",
        blue_text(round(summary["current_total"], 2)),
        blue_text(round(summary["target_total"], 2)),
    )
    logger.info(
        "Delta: %s TJ (%s%%)",
        blue_text(round(absolute_change, 2)),
        round(percentage_change, 4),
    )


def scale_revision_values(
    df: pd.DataFrame,
    mask: pd.Series,
    conditions: dict,
    target_total: float,
    revision_number: int,
) -> None:
    """Scale matching rows so their total equals the requested value."""
    matched_rows = df.loc[mask]
    if matched_rows.empty:
        raise ValueError(
            f"Manual EEUD revision #{revision_number} matched no rows: {conditions}"
        )

    current_total = matched_rows["Value"].sum()
    if pd.isna(current_total):
        raise ValueError(
            f"Manual EEUD revision #{revision_number} has NaN total for {conditions}"
        )

    if current_total == 0 and target_total != 0:
        raise ValueError(
            f"Manual EEUD revision #{revision_number} cannot scale zero total "
            f"to non-zero target for {conditions}"
        )

    scale_factor = 1.0 if current_total == 0 else target_total / current_total
    if current_total != 0:
        df.loc[mask, "Value"] = df.loc[mask, "Value"] * scale_factor

    log_revision_result(
        {
            "revision_number": revision_number,
            "conditions": conditions,
            "row_count": len(matched_rows),
            "current_total": current_total,
            "target_total": target_total,
            "scale_factor": scale_factor,
        }
    )


def manual_revision_to_eeud(df):
    """
    Apply manual total revisions from ``manual_revisions.toml`` to EEUD data.

    Each ``[[revision]]`` entry is treated as:
    - filters: every key except ``Total``
    - target total: ``Total``

    Matching rows are scaled proportionally so their summed ``Value`` equals the
    new total.
    """
    revisions = read_manual_eeud_revisions()
    if not revisions:
        return df

    revised_df = df.copy()

    for revision_number, revision in enumerate(revisions, start=1):
        conditions, target_total = get_revision_conditions(revision, revision_number)
        mask = get_revision_mask(revised_df, conditions, revision_number)
        scale_revision_values(
            revised_df,
            mask,
            conditions,
            target_total,
            revision_number,
        )

    return revised_df


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
    patched_df = manual_revision_to_eeud(patched_df)

    save_eeud(tidy_df, "eeud_no_patch.csv")
    save_eeud(patched_df, "eeud.csv")


if __name__ == "__main__":
    main()
