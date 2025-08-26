"""
A common area for all filepaths and functions common to
 residential baseyear processing submodules


"""

from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_1_DATA,
    STAGE_2_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# Constants ------------------------------------------------
BASE_YEAR = 2023
RUN_TESTS = False
CAP2ACT = 31.536

# Filepaths ------------------------------------------------


RESIDENTIAL_ASSUMPTIONS = ASSUMPTIONS / "residential"
RESIDENTIAL_CONCORDANCES = CONCORDANCES / "residential"
RESIDENTIAL_DATA_DIR = STAGE_2_DATA / "residential"

CHECKS_DIR = RESIDENTIAL_DATA_DIR / "checks"
PREPROCESSING_DIR = RESIDENTIAL_DATA_DIR / "preprocessing"

# Preprocessing names ---------------------------------------

PREPRO_DF_NAME_STEP1 = "1_residential_sh_demand.csv"
PREPRO_DF_NAME_STEP2 = "2_residential_demand_by_island.csv"
PREPRO_DF_NAME_STEP3 = "3_residential_demand_with_assumptions.csv"
PREPRO_DF_NAME_STEP4 = "4_residential_demand_with_process_names.csv"


# DATA LOCATIONS --------------------------------------------

POP_DWELLING = STAGE_1_DATA / "statsnz/population_by_dwelling.csv"


# CONCORDANCES -----------------------------------------

ISLAND_FILE = CONCORDANCES / "region_island_concordance.csv"


# I/O Functions ------------------------------------------------


def _save_data(df, name, label, filepath: Path):
    """Save DataFrame output to the output location."""
    filepath.mkdir(parents=True, exist_ok=True)
    filename = f"{filepath}/{name}"
    logger.info("%s: %s", label, blue_text(filename))
    df.to_csv(filename, index=False, encoding="utf-8-sig")


def save_output(df, name, label, filepath=RESIDENTIAL_DATA_DIR):
    """Save DataFrame output to the output location."""
    label = f"Saving output ({label})"
    _save_data(df=df, name=name, label=label, filepath=filepath)


def save_preprocessing(df, name, label, filepath=PREPROCESSING_DIR):
    """Save DataFrame output to the output location."""
    label = f"Saving preprocessing ({label})"
    _save_data(df=df, name=name, label=label, filepath=filepath)


def save_checks(df, name, label, filepath=CHECKS_DIR):
    """Save DataFrame output to the checks location."""
    label = f"Saving checking output ({label})"
    _save_data(df=df, name=name, label=label, filepath=filepath)


# Population functions -----------------------------------------


def get_population_data(filepath=POP_DWELLING, base_year=BASE_YEAR):
    """Loads census pop/dwelling data
    Returns the df filtered to input baseyear

    IMPORTANT NOTE: this is not full dwelling/pop coverage
    So, we can use the shares of pop per dwelling type and region

    But we can't use the totals to imply total pop or dwellings

    It is best to instead apply these shares to actual pop/dwelling counts
    """

    df = pd.read_csv(filepath)
    df = df[df["CensusYear"] == base_year]

    return df


def clean_population_data(df):
    """
    Perform standard population cleaning and dwelling aggregation
    Input df of raw census data, output df

    Removes unnecessary regions
    Tidies region names
    Aggregates dwelling types to joined/detached
    """

    regions_to_exclude = [
        "Area Outside Region",  # ignore the Chathams
        "Total - New Zealand by regional council",
        "Total - New Zealand by health region/health district",
    ]

    dwelling_type_mapping = {
        "Other private dwelling": "Detached",
        "Private dwelling not further defined": "Detached",
        "Separate house": "Detached",
        "Joined dwelling": "Joined",
        "Total - private dwelling type": "Total",
    }

    df = df.copy()

    # Drop unwanted regions
    df = df.loc[~df["Area"].isin(regions_to_exclude)]

    # Remove trailing " Region" from area names
    df["Area"] = df["Area"].str.replace(r"\sRegion$", "", regex=True)

    # aggregate dwelling types
    df["DwellingType"] = df["DwellingType"].map(dwelling_type_mapping)
    group_cols = [col for col in df.columns if col != "Value"]
    df = df.groupby(group_cols, as_index=False)["Value"].sum()

    return df


def calculate_population_shares(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate overall population shares by (Area, DwellingType).
    """
    required = {"Area", "DwellingType", "Value"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    out = df.copy()

    total = out["Value"].sum()
    # Avoid divide-by-zero; will yield NaN shares if total == 0
    out["ShareOfPopulation"] = (
        out["Value"] / total if total != 0 else out["Value"] * float("nan")
    )

    return out[["Area", "DwellingType", "ShareOfPopulation"]]


def get_population_shares() -> pd.DataFrame:
    """orchestrates population sub-functions
    Loads/cleans data and returns the share of total population
    for each area and dwelling type as a df
    """
    pop_dwelling = get_population_data()
    pop_dwelling = clean_population_data(pop_dwelling)
    df = calculate_population_shares(pop_dwelling)
    return df


def add_islands(df, island_file=ISLAND_FILE):
    """
    Reads in the island concordance file to attach islands to
    an in input df with a "Area" variable
    Renames the island concordance "Region" variable to "Area"
    Returns the df with "Island"
    """

    ri_df = pd.read_csv(island_file)
    ri_df = ri_df.rename(columns={"Region": "Area"})
    df = pd.merge(df, ri_df, on="Area", how="left", validate="many_to_one")

    # Validate merge result
    if "Island" not in df.columns:
        raise KeyError("Merge failed to produce 'Island' column")

    return df
