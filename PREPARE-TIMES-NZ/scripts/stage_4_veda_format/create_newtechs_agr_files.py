"""
Executes building Veda files for new commercial techs
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
from prepare_times_nz.stage_2.ag_forest_fish.common import AG_ASSUMPTIONS
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA

# ---------------------------------------------------------------------
# Constants & file paths
# ---------------------------------------------------------------------
OUTPUT_LOCATION = Path(STAGE_4_DATA) / "subres_agr"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

NEW_TECHS_TRAD: Path = AG_ASSUMPTIONS / "new_techs_traditional.csv"
NEW_TECHS_TRANS: Path = AG_ASSUMPTIONS / "new_techs_transformation.csv"

# Choose which source drives the PROCESSES table: "trad" or "trans"
PROCESSES_SOURCE: Literal["trad", "trans"] = "trad"

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
        }
    )

    # Ensure requested columns exist and reorder
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

    # Add START column (not from CSV)
    df["START"] = START
    df["CAP2ACT"] = CAP2ACT

    # Seed baseline cost columns from 2018 columns if present
    if "INVCOST~2018" in df.columns and "INVCOST" not in df.columns:
        df["INVCOST"] = df["INVCOST~2018"]
    if "FIXOM~2018" in df.columns and "FIXOM" not in df.columns:
        df["FIXOM"] = df["FIXOM~2018"]

    # Only deflate variables that exist
    variables = [v for v in ["INVCOST", "FIXOM"] if v in df.columns]

    if variables:
        # Current values are in 2018 dollars
        df["PriceBaseYear"] = 2018

        # Deflate to 2023 dollars (target base year)
        df = deflate_data(df, 2023, variables)

        # Optional: keep explicit ~2023 columns for audit/outputs
        if "INVCOST" in variables:
            df["INVCOST~2023"] = df["INVCOST"]
        if "FIXOM" in variables:
            df["FIXOM~2023"] = df["FIXOM"]

    # Ensure requested columns exist and reorder
    requested_cols = cfg.get("Columns", list(df.columns))
    for col in requested_cols:
        if col not in df.columns:
            df[col] = ""

    return df[requested_cols]


# ---------------------------------------------------------------------
# MAIN – orchestrate every builder & write CSVs
# ---------------------------------------------------------------------
def main() -> None:
    """Generates and exports TIMES-NZ commercial sector new technologies tables."""

    # 1) Processes: from one chosen source (default: trad)
    processes = create_newtech_process_df(
        {
            "Columns": ["Sets", "TechName", "Tact", "Tcap"],
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
        "AFA",
        "CAP2ACT",
    ]

    parameters_trad = create_newtech_process_parameters_df(
        {"Columns": shared_cols, "Source": "trad"}
    )
    parameters_trans = create_newtech_process_parameters_df(
        {"Columns": shared_cols, "Source": "trans"}
    )

    # Write outputs
    processes.to_csv(OUTPUT_LOCATION / "future_agriculture_processes.csv", index=False)
    parameters_trad.to_csv(
        OUTPUT_LOCATION / "future_agriculture_parameters_traditional.csv", index=False
    )
    parameters_trans.to_csv(
        OUTPUT_LOCATION / "future_agriculture_parameters_transformation.csv",
        index=False,
    )

    print("New commercial technology files successfully generated.")


if __name__ == "__main__":
    main()
