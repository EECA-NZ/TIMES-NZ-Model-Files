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

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def load_raw_cpi(path: Path) -> pd.DataFrame:
    """Read CPI CSV downloaded from Stats NZ Infoshare (skip title row)."""
    logger.debug("Reading raw CPI from %s", path)
    return pd.read_csv(path, skiprows=1)  # first row is a title


def tidy_cpi(df: pd.DataFrame) -> pd.DataFrame:
    """Return an annual (Q4) CPI index from 1990 onward."""
    logger.debug("Tidying CPI dataframe")

    # Remove descriptive rows (empty 'All groups' cells)
    df = df[df["All groups"].notna()].copy()
    df.columns = ["Period", "CPI_Index"]

    # Year / quarter split
    df["Year"] = df["Period"].str[:4].astype(int)
    df["Quarter"] = df["Period"].str[-1].astype(int)

    # Keep Q4 observations only, from 1990 on
    df = df[(df["Year"] >= 1990) & (df["Quarter"] == 4)]

    # Final shape
    return df[["Year", "CPI_Index"]]


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry-point for direct execution or programmatic import."""
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

    logger.info("Processing Stats NZ CPI data")
    raw_cpi = load_raw_cpi(SNZ_CPI_FILE)
    tidy_df = tidy_cpi(raw_cpi)

    output_file = OUTPUT_LOCATION / "cpi.csv"
    tidy_df.to_csv(output_file, index=False)
    logger.info("Wrote cleaned CPI data to %s", output_file)


if __name__ == "__main__":
    main()
