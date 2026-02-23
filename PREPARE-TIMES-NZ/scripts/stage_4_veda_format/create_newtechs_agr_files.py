"""
Executes building Veda files for new commercial techs
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
from prepare_times_nz.stage_2.ag_forest_fish.common import (
    AG_ASSUMPTIONS,
    AG_CONCORDANCES,
)
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA
from prepare_times_nz.utilities.logger_setup import logger

# ---------------------------------------------------------------------
# Constants & file paths
# ---------------------------------------------------------------------
OUTPUT_LOCATION = Path(STAGE_4_DATA) / "subres_agr"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

NEW_TECHS_TRAD: Path = AG_ASSUMPTIONS / "new_techs_traditional.csv"
NEW_TECHS_TRANS: Path = AG_ASSUMPTIONS / "new_techs_transformation.csv"

NEW_TECHS = AG_CONCORDANCES / "tech_codes.csv"
NEW_TECHS_SECTOR = AG_CONCORDANCES / "sector_codes.csv"
NEW_TECHS_ENDUSE = AG_CONCORDANCES / "use_codes.csv"

# Choose which source drives the PROCESSES table: "trad" or "trans"
PROCESSES_SOURCE: Literal["trad", "trans"] = "trad"

# pylint: disable=duplicate-code
# ---------------------------------------------------------------------
# Modelling constants
# ---------------------------------------------------------------------
START = 2025
CAP2ACT = 31.536
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"


def _read_source(source: Literal["trad", "trans"], usecols=None) -> pd.DataFrame:
    """Small helper to read the appropriate CSV."""
    path = NEW_TECHS_TRAD if source == "trad" else NEW_TECHS_TRANS
    return pd.read_csv(path, usecols=usecols)


def create_newtech_process_df(cfg: dict) -> pd.DataFrame:
    """
    Creates a DataFrame defining new commercial technologies from the chosen source.
    cfg = {"Columns": [...], "Source": "trad" | "trans"}
    """
    source: Literal["trad", "trans"] = cfg.get("Source", "trad")
    tech_names = (
        _read_source(source, usecols=["TechName"])["TechName"]
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
    """
    Build new-tech parameters from the specified source,
    converting 2018 -> 2023 prices when present.
    cfg = {"Columns": [...], "Source": "trad" | "trans"}
    """
    source: Literal["trad", "trans"] = cfg.get("Source", "trad")
    df = _read_source(source)

    df["START"] = START
    df["CAP2ACT"] = CAP2ACT

    if "INVCOST~2018" in df.columns and "INVCOST" not in df.columns:
        df["INVCOST"] = df["INVCOST~2018"]
    if "FIXOM~2018" in df.columns and "FIXOM" not in df.columns:
        df["FIXOM"] = df["FIXOM~2018"]

    variables = [v for v in ["INVCOST", "FIXOM"] if v in df.columns]

    if variables:

        df["PriceBaseYear"] = 2018

        df = deflate_data(df, 2023, variables)

        if "INVCOST" in variables:
            df["INVCOST~2023"] = df["INVCOST"]
        if "FIXOM" in variables:
            df["FIXOM~2023"] = df["FIXOM"]

    requested_cols = cfg.get("Columns", list(df.columns))
    for col in requested_cols:
        if col not in df.columns:
            df[col] = ""

    return df[requested_cols]


def create_newtech_process_defintions(_cfg: dict) -> pd.DataFrame:
    """Create DataFrame defining new agriculture technologies
    to patch in the app from agriculture concordances."""

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
    combined = pd.read_csv(NEW_TECHS_TRAD, usecols=["TechName", "Comm-In", "Comm-Out"])
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
    parts = df["TechName"].str.split("-", expand=True)

    df["Sector_TIMES"] = parts[0].fillna("").astype(str)

    # Handle both 3-part (Sector-EndUse-Tech) and 4-part (Sector-EndUse-SubEndUse-Tech) formats
    # If 4 parts: EndUse is parts[1]-parts[2], Technology is parts[3]
    # If 3 parts: EndUse is parts[1], Technology is parts[2]
    def extract_enduse_tech(row_parts):
        if pd.isna(row_parts[3]):
            return (row_parts[1],)
        if pd.isna(row_parts[4]):
            return (
                row_parts[1],
                row_parts[2],
            )
        return f"{row_parts[1]}-{row_parts[2]}", row_parts[3]

    enduse_tech = parts.apply(extract_enduse_tech, axis=1, result_type="expand")
    df["EndUse_TIMES"] = enduse_tech[0].fillna("").astype(str)
    df["Technology_TIMES"] = enduse_tech[1].fillna("").astype(str)

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

    # remove exact duplicate process-definition rows
    df = df[process_cols].drop_duplicates().reset_index(drop=True)

    return df[process_cols]


# ---------------------------------------------------------------------
# MAIN – orchestrate every builder & write CSVs
# ---------------------------------------------------------------------
def main() -> None:
    """Generates and exports TIMES-NZ commercial sector new technologies tables."""

    # 1) Processes: from one chosen source (default: trad)
    processes = create_newtech_process_df(
        {
            "Columns": ["Sets", "TechName", "Tact", "Tcap", "TsLvl"],
            "Source": PROCESSES_SOURCE,
        }
    )

    # 2) Parameters: from BOTH sources, saved separately
    shared_cols = [
        "TechName",
        "Comm-In",
        "Comm-Out",
        "START",
        "EFF",
        "LIFE",
        "INVCOST",
        "INVCOST~2030",
        "INVCOST~2050",
        "FIXOM",
        "AF",
        "CAP2ACT",
    ]

    parameters_trad = create_newtech_process_parameters_df(
        {"Columns": shared_cols, "Source": "trad"}
    )
    parameters_trans = create_newtech_process_parameters_df(
        {"Columns": shared_cols, "Source": "trans"}
    )

    process_definitions = create_newtech_process_defintions({})

    # Write outputs
    processes.to_csv(OUTPUT_LOCATION / "future_agriculture_processes.csv", index=False)
    parameters_trad.to_csv(
        OUTPUT_LOCATION / "future_agriculture_parameters_traditional.csv", index=False
    )
    parameters_trans.to_csv(
        OUTPUT_LOCATION / "future_agriculture_parameters_transformation.csv",
        index=False,
    )
    process_definitions.to_csv(
        OUTPUT_LOCATION / "future_agriculture_process_definitions.csv", index=False
    )

    logger.info("New agriculture technology files successfully generated.")


if __name__ == "__main__":
    main()
