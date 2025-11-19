"""
Executes building Veda files for new commercial techs
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_2.commercial.common import (
    COMMERCIAL_ASSUMPTIONS,
    COMMERCIAL_CONCORDANCES,
)
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA
from prepare_times_nz.utilities.logger_setup import logger

# ---------------------------------------------------------------------
# Constants & file paths
# ---------------------------------------------------------------------

OUTPUT_LOCATION = Path(STAGE_4_DATA) / "subres_com"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)


NEW_TECHS_FILE: Path = COMMERCIAL_ASSUMPTIONS / "new_techs.csv"

NEW_TECHS = COMMERCIAL_CONCORDANCES / "tech_codes.csv"
NEW_TECHS_SECTOR = COMMERCIAL_CONCORDANCES / "sector_codes.csv"
NEW_TECHS_ENDUSE = COMMERCIAL_CONCORDANCES / "use_codes.csv"


# pylint: disable=duplicate-code
# ---------------------------------------------------------------------
# Modelling constants
# ---------------------------------------------------------------------
START = 2025
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"


def create_newtech_process_df(cfg: dict) -> pd.DataFrame:
    """Creates a DataFrame defining new commercial technologies."""
    tech_names = (
        pd.read_csv(NEW_TECHS_FILE, usecols=["TechName"])["TechName"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    df = pd.DataFrame(
        {
            "Sets": "DMD",
            "TechName": tech_names,
            "Tact": ACTIVITY_UNIT,
            "Tcap": CAPACITY_UNIT,
            "TsLvl": "DAYNITE",
        }
    )

    for col in cfg.get("Columns", []):
        if col not in df.columns:
            df[col] = ""
    return df[cfg["Columns"]]


def create_newtech_process_parameters_df(cfg: dict) -> pd.DataFrame:
    """Get newtech parameters from coded assumptions (convert 2018 -> 2023 prices in place)."""
    df = pd.read_csv(NEW_TECHS_FILE)

    # Preserve external context
    df["START"] = START
    # START for TechName C_EDU-WH-Cylinder-ELC is 2024
    # mask_2024 = df["TechName"].isin(["C_EDU-WH-Cylinder-ELC"])
    # df.loc[mask_2024, "START"] = 2024

    # Columns to convert from 2018 -> 2023 while keeping names unchanged
    to_convert = [
        c
        for c in ["INVCOST", "INVCOST~2030", "INVCOST~2050", "FIXOM"]
        if c in df.columns
    ]

    if to_convert:
        # Indicate the base year for the deflator and convert in place
        df["PriceBaseYear"] = 2018
        df = deflate_data(df, 2023, to_convert)

    # Ensure requested columns are present, fill missing with empty string
    requested_cols = cfg.get("Columns", list(df.columns))
    for col in requested_cols:
        if col not in df.columns:
            df[col] = ""

    return df[requested_cols]


def create_newtech_process_defintions(_cfg: dict) -> pd.DataFrame:
    """Create DataFrame defining new commercial technologies
    to patch in the app from commercial concordances."""

    process_cols = [
        "Process",
        "CommodityIn",
        "CommodityOut",
        "Sector",
        "EnduseGroup",
        "EndUse",
        "TechnologyGroup",
        "Technology",
    ]

    # Read tech names directly from NEW_TECHS_FILE
    combined = pd.read_csv(NEW_TECHS_FILE, usecols=["TechName", "Comm-In", "Comm-Out"])
    combined = combined.dropna().drop_duplicates()

    # Read concordances
    tech_map = pd.read_csv(NEW_TECHS)
    sector_map = pd.read_csv(NEW_TECHS_SECTOR)
    enduse_map = pd.read_csv(NEW_TECHS_ENDUSE)

    # Strip column names
    for d in [tech_map, sector_map, enduse_map]:
        d.columns = d.columns.str.strip()

    # --- Merge TIMES codes onto combined tech list ---
    df = combined.copy()
    df["Sector_TIMES"] = df["TechName"].str.split("-").str[0]
    df["EndUse_TIMES"] = df["TechName"].str.split("-").str[1]
    df["Technology_TIMES"] = df["TechName"].str.split("-").str[2]

    # --- Sector merge ---
    df = df.merge(sector_map[["Sector_TIMES", "Sector"]], on="Sector_TIMES", how="left")

    # --- Technology merge ---
    df = df.merge(
        tech_map[["Technology_TIMES", "Technology", "TechGroup"]],
        on="Technology_TIMES",
        how="left",
    )

    # --- EndUse merge ---
    df = df.merge(
        enduse_map[["EndUse_TIMES", "EndUse", "UseGroup"]],
        on="EndUse_TIMES",
        how="left",
    )

    # Rename TechName to Process and fix column names with hyphens
    df = df.rename(
        columns={
            "TechName": "Process",
            "Comm-In": "CommodityIn",
            "Comm-Out": "CommodityOut",
            "TechGroup": "TechnologyGroup",
            "UseGroup": "EnduseGroup",
        }
    )

    # Ensure all expected columns exist
    for col in process_cols:
        if col not in df.columns:
            df[col] = ""

    return df[process_cols]


# -----------------------------------------------------------------------------
# MAIN – orchestrate every builder & write CSVs
# -----------------------------------------------------------------------------
def main() -> None:
    """Generates and exports TIMES-NZ commercial sector newt etchnologies
    definition and parameter tables."""

    processes = create_newtech_process_df(
        {"Columns": ["Sets", "TechName", "Tact", "Tcap", "TsLvl"]}
    )

    parameters = create_newtech_process_parameters_df(
        {
            "Columns": [
                "TechName",
                "Comm-In",
                "Comm-Out",
                "START",
                "EFF",
                "EFF~2030",
                "EFF~2050",
                "LIFE",
                "INVCOST",
                "INVCOST~2030",
                "INVCOST~2050",
                "FIXOM",
                "AF",
                "FLO_MARK~2030",
                "FLO_MARK~2050",
                "FLO_MARK~0",
            ]
        }
    )

    process_definitions = create_newtech_process_defintions({})

    processes.to_csv(OUTPUT_LOCATION / "future_commercial_processes.csv", index=False)
    parameters.to_csv(OUTPUT_LOCATION / "future_commercial_parameters.csv", index=False)
    process_definitions.to_csv(
        OUTPUT_LOCATION / "future_commercial_process_definitions.csv", index=False
    )

    logger.info("New commercial technology files successfully generated.")


if __name__ == "__main__":
    main()
