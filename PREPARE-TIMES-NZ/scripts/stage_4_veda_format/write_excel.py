"""
Write Excel files in VEDA format.

This script reads the normalised TOML metadata produced in **Stage 0**,
pulls the data from either intermediate TOML files *or* CSVs in the repo,
and writes properly-tagged worksheets so VEDA can ingest them.
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd
from prepare_times_nz.excel_writers import (
    create_empty_workbook,
    dict_to_dataframe,
    strip_headers_from_tiny_df,
    write_data,
)
from prepare_times_nz.filepaths import DATA_INTERMEDIATE, PREP_LOCATION
from prepare_times_nz.helpers import clear_output
from prepare_times_nz.logger_setup import logger

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
METADATA_PATH = Path(DATA_INTERMEDIATE) / "stage_0_config" / "config_metadata.csv"
STAGE_0_CONFIG_DIR = Path(DATA_INTERMEDIATE) / "stage_0_config"

logger.info("Metadata location: %s", METADATA_PATH)


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def load_metadata() -> pd.DataFrame:
    """Read the metadata CSV generated in Stage 0."""
    return pd.read_csv(METADATA_PATH)


def get_source_dataframe(data_location: str, table_name: str) -> pd.DataFrame:
    """
    Return a DataFrame for *table_name* found at *data_location*.

    * If the location ends with **.toml** we load the normalised TOML from
      "data_intermediate/stage_0_config" and convert its "Data" dict.
    * If the location ends with **.csv** we read it relative to
      "PREP_LOCATION".
    """
    if data_location.endswith(".toml"):
        toml_path = STAGE_0_CONFIG_DIR / data_location
        with open(toml_path, "rb") as file_obj:
            toml_data = tomllib.load(file_obj)
        df_dict = toml_data[table_name]["Data"]
        return dict_to_dataframe(df_dict)

    if data_location.endswith(".csv"):
        csv_path = Path(PREP_LOCATION) / data_location
        return pd.read_csv(csv_path, dtype=str)

    logging.warning("Unrecognised data location type: %s", data_location)
    return pd.DataFrame()  # Fallback to an empty frame


def write_workbook(workbook: str, workbook_meta: pd.DataFrame) -> None:
    """
    Create *workbook* and write all its worksheets defined in *workbook_meta*.
    """
    worksheets = workbook_meta["SheetName"].unique()

    # ----------------------------------------------------------------------
    # Create an empty workbook shell with the expected worksheet names.
    # ----------------------------------------------------------------------
    create_empty_workbook(workbook, worksheets)

    # ----------------------------------------------------------------------
    # Iterate over worksheets, then over every table in that sheet.
    # ----------------------------------------------------------------------
    for worksheet in worksheets:
        worksheet_meta = workbook_meta[workbook_meta["SheetName"] == worksheet]
        start_row = 0  # keeps track of where to write the next table

        for row in worksheet_meta.itertuples():
            logger.info(
                "WorkBookName=%s | Sheet=%s | DataLocation=%s | Tag=%s",
                row.WorkBookName,
                worksheet,
                row.DataLocation,
                row.VedaTag,
            )

            # ------------------------------------------------------------------
            # Locate and read the data
            # ------------------------------------------------------------------
            df = get_source_dataframe(row.DataLocation, row.TableName)

            # Special handling for the two tiny SysSettings tables
            if workbook == "SysSettings" and row.TableName in {
                "StartYear",
                "ActivePDef",
            }:
                df = strip_headers_from_tiny_df(df)

            # UC_Sets may be NaN (float), so normalise that to an empty list
            uc_sets = (
                []
                if (isinstance(row.UC_Sets, float) and np.isnan(row.UC_Sets))
                else row.UC_Sets
            )

            # ------------------------------------------------------------------
            # Write the table
            # ------------------------------------------------------------------
            write_data(
                df,
                book_name=workbook,
                sheet_name=worksheet,
                tag=row.VedaTag,
                uc_set=uc_sets,
                startrow=start_row,
            )

            # ------------------------------------------------------------------
            # Increment start_row for the NEXT table (+3 blank lines as buffer)
            # ------------------------------------------------------------------
            start_row += len(df) + len(uc_sets) + 3


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main() -> None:
    """Entry-point when run as a script."""
    # Wipe the output folder – we're going to fill it in!

    clear_output()

    metadata = load_metadata()

    # Each unique workbook in the metadata becomes its own file
    for workbook in metadata["WorkBookName"].unique():
        workbook_meta = metadata[metadata["WorkBookName"] == workbook]
        write_workbook(workbook, workbook_meta)

    logger.info("Excel writing complete.")


# -----------------------------------------------------------------------------
# SCRIPT ENTRY-POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
