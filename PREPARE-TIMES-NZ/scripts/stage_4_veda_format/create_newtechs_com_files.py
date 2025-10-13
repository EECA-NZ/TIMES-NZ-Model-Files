"""
Executes building Veda files for new commercial techs
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_2.commercial.common import COMMERCIAL_ASSUMPTIONS
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import STAGE_4_DATA
from prepare_times_nz.utilities.logger_setup import logger

# ---------------------------------------------------------------------
# Constants & file paths
# ---------------------------------------------------------------------

OUTPUT_LOCATION = Path(STAGE_4_DATA) / "subres_com"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)


NEW_TECHS_FILE: Path = COMMERCIAL_ASSUMPTIONS / "new_techs.csv"

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
        }
    )

    for col in cfg.get("Columns", []):
        if col not in df.columns:
            df[col] = ""
    return df[cfg["Columns"]]


def create_newtech_process_parameters_df(cfg: dict) -> pd.DataFrame:
    """Get newtech parameters from coded assumptions (convert 2018 -> 2023 prices)."""
    df = pd.read_csv(NEW_TECHS_FILE)

    df["START"] = START

    if "INVCOST~2018" in df.columns:
        df["INVCOST"] = df["INVCOST~2018"]
    if "FIXOM~2018" in df.columns:
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


# -----------------------------------------------------------------------------
# MAIN – orchestrate every builder & write CSVs
# -----------------------------------------------------------------------------
def main() -> None:
    """Generates and exports TIMES-NZ commercial sector newt etchnologies
    definition and parameter tables."""

    processes = create_newtech_process_df(
        {"Columns": ["Sets", "TechName", "Tact", "Tcap"]}
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
                "AFA",
                "FLO_MARK~2030",
                "FLO_MARK~2050",
                "FLO_MARK~0",
            ]
        }
    )

    processes.to_csv(OUTPUT_LOCATION / "future_commercial_processes.csv", index=False)
    parameters.to_csv(OUTPUT_LOCATION / "future_commercial_parameters.csv", index=False)

    logger.info("New commercial technology files successfully generated.")


if __name__ == "__main__":
    main()
