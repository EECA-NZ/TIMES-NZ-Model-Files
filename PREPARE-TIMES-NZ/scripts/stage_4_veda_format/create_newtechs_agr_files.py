"""
Executes building Veda files for new commercial techs
"""

from __future__ import annotations

import tomllib
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

NEW_TECHS_STEADY: Path = AG_ASSUMPTIONS / "new_techs_steady.csv"
NEW_TECHS_SHIFT: Path = AG_ASSUMPTIONS / "new_techs_shift.csv"
NEW_TECHS_TOPOLOGY: Path = AG_ASSUMPTIONS / "future_tech_topology.toml"

NEW_TECHS = AG_CONCORDANCES / "tech_codes.csv"
NEW_TECHS_SECTOR = AG_CONCORDANCES / "sector_codes.csv"
NEW_TECHS_ENDUSE = AG_CONCORDANCES / "use_codes.csv"

# pylint: disable=duplicate-code
# ---------------------------------------------------------------------
# Modelling constants
# ---------------------------------------------------------------------
START = 2025
CAP2ACT = 31.536
ACTIVITY_UNIT = "PJ"
CAPACITY_UNIT = "GW"


def _read_source(source: Literal["steady", "shift"], usecols=None) -> pd.DataFrame:
    """Small helper to read the appropriate CSV."""
    path = NEW_TECHS_STEADY if source == "steady" else NEW_TECHS_SHIFT
    return pd.read_csv(path, usecols=usecols)


def _as_list(value) -> list[str]:
    """Normalise a scalar or TOML list without changing TIMES-code case."""
    values = value if isinstance(value, list) else [value]
    return [str(item).strip() for item in values]


def _topology_lookups() -> tuple[dict[str, str], set[str], set[tuple[str, str]]]:
    """Load the concordance-backed identifiers used to validate topology."""
    sector_codes = pd.read_csv(NEW_TECHS_SECTOR)
    enduse_codes = pd.read_csv(NEW_TECHS_ENDUSE)
    technology_codes = pd.read_csv(NEW_TECHS)
    return (
        dict(zip(sector_codes["Sector_TIMES"], sector_codes["Sector"])),
        set(enduse_codes["EndUse_TIMES"]),
        set(zip(technology_codes["Sector"], technology_codes["Technology_TIMES"])),
    )


def _expand_topology_entry(
    name: str,
    entry: dict,
    sector_lookup: dict[str, str],
    valid_enduses: set[str],
    valid_technologies: set[tuple[str, str]],
) -> list[dict[str, str]]:
    """Validate one topology entry and expand its sector/fuel combinations."""
    required = {"TechCode", "EndUse", "InputFuel", "Sectors"}
    missing = required.difference(entry)
    if missing:
        raise ValueError(
            f"Missing topology fields in [{name}]: {', '.join(sorted(missing))}"
        )

    end_use = str(entry["EndUse"])
    technology = str(entry["TechCode"])
    if end_use not in valid_enduses:
        raise ValueError(f"Unknown agriculture end-use code: {end_use}")

    output_template = entry.get(
        "CommodityOutTemplate", "{sector}-{technology}-{end_use}"
    )
    rows = []
    for sector in _as_list(entry["Sectors"]):
        if sector not in sector_lookup:
            raise ValueError(f"Unknown agriculture sector code: {sector}")
        if (sector_lookup[sector], technology) not in valid_technologies:
            raise ValueError(
                "Unknown agriculture technology code for sector: "
                f"{sector}/{technology}"
            )
        for fuel in _as_list(entry["InputFuel"]):
            values = {
                "sector": str(sector),
                "end_use": end_use,
                "technology": technology,
                "fuel": str(fuel),
            }
            rows.append(
                {
                    "TechName": "{sector}-{end_use}-{technology}-{fuel}".format(
                        **values
                    ),
                    "Comm-In": f"AGR{values['fuel']}",
                    "Comm-Out": output_template.format(**values),
                    "Sector_TIMES": values["sector"],
                    "EndUse_TIMES": values["end_use"],
                    "Technology_TIMES": values["technology"],
                }
            )
    return rows


def create_newtech_topology(config_file=NEW_TECHS_TOPOLOGY) -> pd.DataFrame:
    """Expand concordance-validated future-technology topology into TIMES rows."""
    with Path(config_file).open("rb") as file:
        config = tomllib.load(file)

    sector_lookup, valid_enduses, valid_technologies = _topology_lookups()
    rows: list[dict[str, str]] = []
    for name, entry in config.items():
        if name.lower().startswith("newtechs"):
            rows.extend(
                _expand_topology_entry(
                    name, entry, sector_lookup, valid_enduses, valid_technologies
                )
            )

    topology = pd.DataFrame(rows)
    if topology.empty or topology["TechName"].duplicated().any():
        raise ValueError("Future agriculture topology must contain unique technologies")
    return topology


def _parameters_with_topology(source: Literal["steady", "shift"]) -> pd.DataFrame:
    """Join scenario-dependent assumptions to the canonical process topology."""
    parameters = _read_source(source)
    if parameters["TechName"].duplicated().any():
        raise ValueError(f"Duplicate future agriculture parameters in {source}")

    topology = create_newtech_topology()
    expected = set(topology["TechName"])
    actual = set(parameters["TechName"])
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(
            f"Future agriculture {source} parameters disagree with topology; "
            f"missing={missing}, unexpected={unexpected}"
        )
    return topology.merge(parameters, on="TechName", how="left", validate="one_to_one")


def create_newtech_process_df(cfg: dict) -> pd.DataFrame:
    """
    Create scenario-independent declarations for future agriculture technologies.
    """
    tech_names = create_newtech_topology()["TechName"]

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
    cfg = {"Columns": [...], "Source": "steady" | "shift"}
    """
    source: Literal["steady", "shift"] = cfg.get("Source", "steady")
    df = _parameters_with_topology(source)

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

    combined = create_newtech_topology()

    # Read concordances
    tech_map = pd.read_csv(NEW_TECHS)
    sector_map = pd.read_csv(NEW_TECHS_SECTOR)
    enduse_map = pd.read_csv(NEW_TECHS_ENDUSE)

    # Strip column names
    for d in [tech_map, sector_map, enduse_map]:
        d.columns = d.columns.str.strip()

    df = combined.copy()

    # --- Sector merge ---
    df = df.merge(sector_map[["Sector_TIMES", "Sector"]], on="Sector_TIMES", how="left")

    # Technology codes can be sector-specific, so join on both identifiers.
    df = df.merge(
        tech_map[["Sector", "Technology_TIMES", "Technology", "TechGroup"]],
        on=["Sector", "Technology_TIMES"],
        how="left",
        validate="many_to_one",
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
    """Generate and export TIMES-NZ future agriculture technology tables."""

    # 1) Process topology is scenario-independent.
    processes = create_newtech_process_df(
        {
            "Columns": ["Sets", "TechName", "Tact", "Tcap", "TsLvl"],
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

    parameters_steady = create_newtech_process_parameters_df(
        {"Columns": shared_cols, "Source": "steady"}
    )
    parameters_shift = create_newtech_process_parameters_df(
        {"Columns": shared_cols, "Source": "shift"}
    )

    process_definitions = create_newtech_process_defintions({})

    # Write outputs
    processes.to_csv(OUTPUT_LOCATION / "future_agriculture_processes.csv", index=False)
    parameters_steady.to_csv(
        OUTPUT_LOCATION / "future_agriculture_parameters_steady.csv", index=False
    )
    parameters_shift.to_csv(
        OUTPUT_LOCATION / "future_agriculture_parameters_shift.csv",
        index=False,
    )
    process_definitions.to_csv(
        OUTPUT_LOCATION / "future_agriculture_process_definitions.csv", index=False
    )

    logger.info("New agriculture technology files successfully generated.")


if __name__ == "__main__":
    main()
