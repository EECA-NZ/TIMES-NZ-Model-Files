"""
Here we find the Electricity Authority (EA) Excel files, extract the
datasets and write them to the
"data_intermediate/stage_1_external_data/electricity_authority" folder.
This will include any EDGS assumptions we want to use and any official figures we want.
We also do some tidying/standardising here.

Outputs
-------
* "emi_md.parquet"               - half-hourly Generation_MD files (combined).
* "emi_gxp.parquet"              - half-hourly grid export node files (combined).
* "emi_distributed_solar.csv"    - tidy distributed-solar summary.
* "emi_nsp_concordances.csv"     - POC → region / zone / island concordance.

Run directly::

    python -m prepare_times_nz.stages.extract_ea_data
"""

from __future__ import annotations

import glob
import time
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, DATA_RAW, STAGE_1_DATA
from prepare_times_nz.utilities.logger_setup import logger

# Constants ------------------------------------------------------------

INPUT_LOCATION = Path(DATA_RAW) / "external_data" / "electricity_authority"
OUTPUT_LOCATION = Path(STAGE_1_DATA) / "electricity_authority"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

EMI_MD_FOLDER: Path = INPUT_LOCATION / "emi_md"
EMI_GXP_FOLDER: Path = INPUT_LOCATION / "emi_grid_export"
EMI_FLEET_FILE: Path = (
    INPUT_LOCATION / "emi_fleet_data" / "20230601_DispatchedGenerationPlant.csv"
)  # currently unused, retained for future work
EMI_NSP_TABLE: Path = (
    INPUT_LOCATION / "emi_nsp_table" / "20250308_NetworkSupplyPointsTable.csv"
)
EMI_DISTRIBUTED_SOLAR_DIR: Path = INPUT_LOCATION / "emi_distributed_solar"

TIME_OF_DAY_FILE = ASSUMPTIONS / "settings/time_of_day_types.csv"

# Functions ----------------------------------------


def convert_hour_to_timeofday(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function takes a dataframe with an hour variable
    and creates the Time_Of_Day variable.

    This uses an input assumptions file with
    "Hour" and "Time_Of_Day" variables

    We set default to night (this mostly just covers DST hours)

    """
    time_of_day_types = pd.read_csv(TIME_OF_DAY_FILE)
    # # we create a dict and map these rather than merging
    # its faster - saves ~4 seconds per run
    hour_to_time = dict(
        zip(time_of_day_types["Hour"], time_of_day_types["Time_Of_Day"])
    )
    df["Time_Of_Day"] = df["Hour"].map(hour_to_time)
    df["Time_Of_Day"] = df["Time_Of_Day"].fillna("N")

    return df


def convert_date_to_daytype(
    df: pd.DataFrame, date_col: str = "Trading_Date"
) -> pd.DataFrame:
    """
    This function creates a Day_Type variable based on the weekday:
      - 'WE-' for weekends,
      - 'WK-' for weekdays,
      - 'ERROR' otherwise (should not occur if date_col is valid).
    Assumes date_col is of datetime type.
    """
    # Ensure the column is datetime
    df[date_col] = pd.to_datetime(df[date_col])

    weekday = df[date_col].dt.weekday  # Monday=0, Sunday=6
    df["Day_Type"] = np.select(
        [weekday.isin([5, 6]), weekday.isin([0, 1, 2, 3, 4])],
        ["WE-", "WK-"],
        default="ERROR",
    )
    return df


def convert_date_to_season(
    df: pd.DataFrame, date_col: str = "Trading_Date"
) -> pd.DataFrame:
    """
    This function creates a Season variable based on the month:
      - 'SUM-' for Dec, Jan, Feb
      - 'FAL-' for Mar, Apr, May
      - 'WIN-' for Jun, Jul, Aug
      - 'SPR-' for Sep, Oct, Nov
    Assumes date_col is of datetime type.
    """
    df[date_col] = pd.to_datetime(df[date_col])
    month = df[date_col].dt.month

    df["Season"] = np.select(
        [
            month.isin([12, 1, 2]),
            month.isin([3, 4, 5]),
            month.isin([6, 7, 8]),
            month.isin([9, 10, 11]),
        ],
        ["SUM-", "FAL-", "WIN-", "SPR-"],
        default="ERROR",
    )
    return df


def create_timeslices(df: pd.DataFrame, date_col: str = "Trading_Date") -> pd.DataFrame:
    """
    This function takes a dataframe with a date and time variable
    and creates the TIMES Timeslice variable.
    It combines season, day type, and time of day
    to produce a single categorical variable.

    Parameters:
    - df: pd.DataFrame
    - hour_col: str, the name of the column with the hour
    - date_col: str, the name of the column with the date


    Returns:
    - pd.DataFrame with a new 'Timeslice' column
    """

    df = convert_hour_to_timeofday(df)
    df = convert_date_to_daytype(df, date_col)
    df = convert_date_to_season(df, date_col)
    df["TimeSlice"] = df["Season"] + df["Day_Type"] + df["Time_Of_Day"]
    df = df.drop(columns=["Season", "Day_Type", "Time_Of_Day"])

    return df


def add_timeslices_to_emi(
    df: pd.DataFrame, date_col: str = "Trading_Date", tp_col: str = "Trading_Period"
) -> pd.DataFrame:
    """
    Adds time-based features to an EMI dataframe:
    - Parses the date column
    - Extracts hour from 'Trading_Period'
    - Constructs the 'Timeslice' variable using season, day type, and time of day

    Assumes the Trading_Period values are like 'TP01', 'TP48', etc.
    """

    # Step 1: Ensure the date column is parsed as datetime
    df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d", errors="coerce")

    # Step 2: Extract numeric period from 'TPxx' format
    df["Trading_Time"] = (
        df[tp_col]
        .str.replace("TP", "", regex=False)
        .astype("Int32")  # nullable integer in case of missing values
    )

    # Step 3: Calculate hour as integer ((TP - 1) * 30 // 60)
    df["Hour"] = ((df["Trading_Time"] - 1) * 30) // 60

    # Step 4: Create the timeslice variable
    df = create_timeslices(df, date_col=date_col)

    return df


def combine_emi_files(csv_folder: Path) -> pd.DataFrame:
    """
    Load every "*.csv" in *csv_folder* and return a long-format DataFrame.
    Pivots expected the trading period variables (TP[_])
    """

    files = glob.glob(str(csv_folder / "*.csv"))
    if not files:
        logger.warning("No files found in %s", csv_folder)
        return pd.DataFrame()

    frames: List[pd.DataFrame] = []
    for file in files:
        logger.info("        Reading %s", Path(file).name)
        frames.append(pd.read_csv(file))

    emi_df = pd.concat(frames, ignore_index=True)

    # Identify trading-period columns (TP1 … TP48)
    tp_cols = [col for col in emi_df.columns if col.startswith("TP")]

    emi_df = pd.melt(
        emi_df,
        id_vars=emi_df.columns.difference(tp_cols),
        value_vars=tp_cols,
        var_name="Trading_Period",
        value_name="Value",
    )

    emi_df = add_timeslices_to_emi(emi_df)
    return emi_df


def get_gxp_demand(directory: Path) -> pd.DataFrame:
    """
    Load every "*.csv" in *directory* and return a combined DataFrame.
    Pivots expected the trading period variables (TP[_])
    """
    logger.info("Reading GXP demand data from %s", directory)
    df = combine_emi_files(directory)

    return df


def get_md_generation(directory: Path) -> pd.DataFrame:
    """
    Wraps combine_emi_files with a log statement
    """
    logger.info("Reading MD_Generation data from %s", directory)
    df = combine_emi_files(directory)

    return df


def read_distributed_solar(sector: str) -> pd.DataFrame:
    """
    Load a distributed-solar CSV for *sector* (Residential / Commercial / Industrial).
    The EA files live at https://www.emi.ea.govt.nz/Retail/Reports/GUEHMT.
    """
    filename = f"solar_{sector.lower()}.csv"
    path = EMI_DISTRIBUTED_SOLAR_DIR / filename
    logger.info("Reading %s solar data", sector)
    df = pd.read_csv(path, skiprows=12)
    df["Sector"] = sector
    return df


def tidy_distributed_solar() -> pd.DataFrame:
    """Return a cleaned DataFrame combining all distributed-solar sectors."""
    solar_df = pd.concat(
        [
            read_distributed_solar("Residential"),
            read_distributed_solar("Commercial"),
            read_distributed_solar("Industrial"),
        ],
        ignore_index=True,
    )

    # Drop columns we don’t currently use (fuel type retained for future battery split)
    solar_df = solar_df.drop(columns=["Region ID", "Capacity", "Fuel type"])

    solar_df = solar_df.rename(
        columns={
            "Avg. capacity installed (kW)": "avg_cap_kw",
            "Avg. capacity - new installations (kW)": "avg_cap_new_kw",
            "ICP count - new installations": "icp_count_new",
            "ICP uptake rate (%)": "icp_uptake_proportion",
            "Total capacity installed (MW)": "capacity_installed_mw",
            "ICP count": "icp_count",
            "Region name": "Region",
            "Month end": "Month",
        }
    )

    # Convert percentage and date
    solar_df["icp_uptake_proportion"] = solar_df["icp_uptake_proportion"] / 100
    solar_df["Month"] = pd.to_datetime(solar_df["Month"], dayfirst=True)

    return solar_df


def build_nsp_concordance(nsp_csv: Path) -> pd.DataFrame:
    """Create a POC → region / zone / island concordance table."""
    df = pd.read_csv(nsp_csv)
    df = df[df["Current flag"] == 1].copy()

    # Simple three-letter POC code
    df["POC"] = df["POC code"].str[:3]

    cols = ["POC", "Network reporting region", "Zone", "Island"]
    df = df[cols].drop_duplicates()
    df = df.rename(columns={"Network reporting region": "Network_reporting_region"})
    return df


# Execute --------------------------------------------------


def main() -> None:
    """Run all EA-data extraction steps."""
    # 1. Generation_MD
    md_df = get_md_generation(EMI_MD_FOLDER)
    if not md_df.empty:
        md_path = OUTPUT_LOCATION / "emi_md.parquet"
        md_df.to_parquet(md_path, engine="pyarrow")
        logger.info("Wrote Generation_MD parquet to %s", md_path)

    # 2. GXP demand

    start_time = time.time()

    gxp_df = get_gxp_demand(EMI_GXP_FOLDER)
    if not gxp_df.empty:
        gxp_path = OUTPUT_LOCATION / "emi_gxp.parquet"
        gxp_df.to_parquet(gxp_path, engine="pyarrow")
        logger.info("Wrote Generation_MD parquet to %s", gxp_path)

    end_time = time.time()
    elapsed = end_time - start_time
    logger.info("GXP Processing took %s seconds", round(elapsed, 2))

    # 2. Distributed solar
    solar_df = tidy_distributed_solar()
    solar_path = OUTPUT_LOCATION / "emi_distributed_solar.csv"
    solar_df.to_csv(solar_path, index=False)
    logger.info("Wrote distributed-solar CSV to %s", solar_path)

    # 3. NSP concordance
    nsp_df = build_nsp_concordance(EMI_NSP_TABLE)
    nsp_path = OUTPUT_LOCATION / "emi_nsp_concordances.csv"
    nsp_df.to_csv(nsp_path, index=False)
    logger.info("Wrote NSP concordance CSV to %s", nsp_path)


if __name__ == "__main__":
    main()
