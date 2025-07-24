"""
Pull and clean data from Stats NZ.

Currently only handles CPI, which is used later for a deflator
function.  Steps:

1. Read raw CPI data exported from Infoshare.
2. Drop descriptive rows and keep quarterly observations.
3. Build annual CPI series (Q4 values only) from 1990 onward.
4. Write the tidy CSV to "data_intermediate/stage_1_external_data/statsnz".
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from prepare_times_nz.filepaths import DATA_RAW, STAGE_1_DATA

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INPUT_LOCATION = Path(DATA_RAW) / "external_data" / "statsnz"
OUTPUT_LOCATION = Path(STAGE_1_DATA) / "statsnz"
SNZ_CPI_FILE = INPUT_LOCATION / "cpi" / "cpi_infoshare.csv"
SNZ_CGPI_FILE = INPUT_LOCATION / "cgpi" / "cgpi_infoshare.csv"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def load_raw_index(path: Path, value_name: str) -> pd.DataFrame:
    """Load and tidy a Stats NZ index file with periods as index and extra junk rows."""
    logger.debug("Reading index from %s", path)
    df = pd.read_csv(path, skiprows=1, index_col=0).reset_index()
    df.columns = ["Period", value_name]

    # Filter only rows that look like proper "1990Q1", "2001Q4", etc.
    df = df[df["Period"].str.match(r"^\d{4}Q[1-4]$", na=False)]

    df["Year"] = df["Period"].str[:4].astype(int)
    df["Quarter"] = df["Period"].str[-1].astype(int)
    df = df[(df["Year"] >= 1990) & (df["Quarter"] == 4)]

    return df[["Year", value_name]]


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry-point for direct execution or programmatic import."""
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

    logger.info("Processing Stats NZ CPI data")
    cpi_df = load_raw_index(SNZ_CPI_FILE, "CPI_Index")
    cpi_df.columns = ["Year", "CPI_Index"]
    cpi_output_file = OUTPUT_LOCATION / "cpi.csv"
    cpi_df.to_csv(cpi_output_file, index=False)
    logger.info("Wrote cleaned CPI data to %s", cpi_output_file)

    logger.info("Processing Stats NZ CGPI data")
    cgpi_df = load_raw_index(SNZ_CGPI_FILE, "CGPI_Index")
    cgpi_df.columns = ["Year", "CGPI_Index"]
    cgpi_output_file = OUTPUT_LOCATION / "cgpi.csv"
    cgpi_df.to_csv(cgpi_output_file, index=False)
    logger.info("Wrote cleaned CGPI data to %s", cgpi_output_file)


if __name__ == "__main__":
    main()
