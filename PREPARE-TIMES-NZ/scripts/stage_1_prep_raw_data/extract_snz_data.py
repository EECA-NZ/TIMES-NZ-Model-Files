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

from pathlib import Path

import pandas as pd
from prepare_times_nz.data_cleaning import rename_columns_to_pascal
from prepare_times_nz.filepaths import DATA_RAW, STAGE_1_DATA
from prepare_times_nz.logger_setup import logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INPUT_LOCATION = Path(DATA_RAW) / "external_data" / "statsnz"
OUTPUT_LOCATION = Path(STAGE_1_DATA) / "statsnz"

SNZ_CPI_FILE = INPUT_LOCATION / "cpi" / "cpi_infoshare.csv"
SNZ_CGPI_FILE = INPUT_LOCATION / "cgpi" / "cgpi_infoshare.csv"
SNZ_CENSUS_HEATING_FILE = INPUT_LOCATION / "census" / "dwelling_heating.csv"
SNZ_DWELLINGS_POP_FILE = INPUT_LOCATION / "census" / "population_by_dwelling.csv"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def save_file(df: pd.DataFrame, filename: str, label: str):
    """
    Saves the stats data and includes logging
    df: the df to write
    filename: the name of the file
    label: what to call this in the log
    Requires Path OUTPUT_LOCATION to be defined
    """
    if not filename.lower().endswith(".csv"):
        raise ValueError(f"Filename '{filename}' must end with '.csv'")

    output_file = OUTPUT_LOCATION / filename
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    logger.info("Wrote %s to %s", label, output_file)


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


def extract_price_index_data():
    """
    Loads, tidies, and saves the CPI and CGPI data
    Expects inputs in the SNZ_CPI_FILE and SNZ_CGPI_FILE locations
    Writes to output_location so this location needs to exist

    """
    cpi_df = load_raw_index(SNZ_CPI_FILE, "CPI_Index")
    cpi_df.columns = ["Year", "CPI_Index"]
    save_file(cpi_df, "cpi.csv", "CPI data")

    cgpi_df = load_raw_index(SNZ_CGPI_FILE, "CGPI_Index")
    cgpi_df.columns = ["Year", "CGPI_Index"]
    save_file(cgpi_df, "cgpi.csv", "CGPI data")


# Census data


def get_dwelling_heating_data(path: Path) -> pd.DataFrame:
    """Return the dataframe from raw census dwelling results
    Note: manual fixing of dwelling codes to dwelling names included here
    as these were not available in the main data
    Source found in raw_data/statsnz/readme.md
    """
    # load raw data
    df = pd.read_csv(path)
    # consistent name case
    df = rename_columns_to_pascal(df)
    # dwelling type/code mapping
    # CeDt is the SNZ label for the dwelling type code
    # no labels were provided in the extract so we manually map these
    dwelling_type_map = {
        "10": "Private dwelling not further defined",
        "11": "Separate house",
        "12": "Joined dwelling",
        "13": "Other private dwelling",
        "999": "Total - private dwelling type",
    }
    df["PrivateDwellingType"] = df["CeDt"].astype(str).map(dwelling_type_map)

    df = df[
        [
            "CensusYear",
            "Area",
            "MainTypesOfHeatingUsed",
            "PrivateDwellingType",
            "ObValue",
        ]
    ].copy()

    df = df.rename(columns={"ObValue": "Value"})

    return df


def get_population_by_dwelling(path: Path) -> pd.DataFrame:
    """
    Some mild cleaning of the ADE pop/dwellings data
    Reads from the filepath, returns df
    Source provided in data_raw/statsnz/readme.md
    """

    df = pd.read_csv(path)
    df = rename_columns_to_pascal(df)
    # strangely, this data has the correct dwelling type labels already
    df = df[
        [
            "CensusYear",
            "Area",
            "DwellingType",
            "ObValue",
        ]
    ].copy()
    df = df.rename(columns={"ObValue": "Value"})
    return df


def extract_census_data():
    """
    A wrapper for the census inputs and relevant mapping
    """
    # Census: Dwelling heating
    df = get_dwelling_heating_data(SNZ_CENSUS_HEATING_FILE)
    save_file(df, "dwelling_heating.csv", "dwelling heating data")

    # Census: Dwelling populations. Was cleaned manually, unfortunately.
    df = get_population_by_dwelling(SNZ_DWELLINGS_POP_FILE)
    save_file(df, "population_by_dwelling.csv", "dwelling population data")


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry-point for direct execution or programmatic import."""
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

    # Price indices
    extract_price_index_data()
    extract_census_data()


if __name__ == "__main__":
    main()
