"""
Build COM_FR VEDA load-curve input files for each sector and write per-sector CSVs.

Inputs (relative to prepare_times_nz project structure)
- Industry:    ASSUMPTIONS/industry_demand/load_curves_ind.csv
               (columns: TimeSlice, Attribute, Cset_CN, Cset_SET, Year, NI, SI)
- Residential: STAGE_2_DATA/settings/load_curves/residential_curves.csv
               (columns: Year, TimeSlice, LoadCurve)
- Agriculture: ASSUMPTIONS/ag_forest_fish_demand/ag_curves.csv
               ASSUMPTIONS/ag_forest_fish_demand/ag_curves_irrigation.csv
               ASSUMPTIONS/ag_forest_fish_demand/ag_curves_mpm.csv
               (columns: Year, TimeSlice, LoadCurve, Technology)
- Commercial:  ASSUMPTIONS/commercial_demand/commercial_curves.csv
               (columns: Year, TimeSlice, LoadCurve, Technology)

Output schema (all sectors)
[TimeSlice, Attribute, Cset_CN, Cset_SET, Year, NI, SI]

Notes
- Merge all agriculture curve files together before transforming.
- Agriculture charging mainly overnight, with seasonality matched to processes in each subsector;
  tractors may have different curves than other technologies.
- Save each sector to its own CSV in STAGE_4_DATA/scen_com_fr/.
"""

from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA, STAGE_4_DATA
from prepare_times_nz.utilities.logger_setup import logger

# ---------------------------------------------------------------------
# Constants & file paths
# ---------------------------------------------------------------------

OUTPUT_LOCATION = Path(STAGE_4_DATA) / "scen_com_fr"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

COM_ASSUMPTIONS = Path(ASSUMPTIONS) / "commercial_demand"
AG_ASSUMPTIONS = Path(ASSUMPTIONS) / "ag_forest_fish_demand"
INDUSTRY_ASSUMPTIONS = Path(ASSUMPTIONS) / "industry_demand"
LOAD_CURVE_DATA = Path(STAGE_2_DATA) / "settings/load_curves"

REQUIRED_COLS = ["TimeSlice", "Attribute", "Cset_CN", "Cset_SET", "Year", "NI", "SI"]

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def _coerce_and_order(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure required columns exist, coerce types, and order columns."""
    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[REQUIRED_COLS].copy()

    for col in ["TimeSlice", "Attribute", "Cset_CN", "Cset_SET"]:
        df[col] = df[col].astype("string").str.strip()

    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")

    for col in ["NI", "SI"]:
        maybe_num = pd.to_numeric(df[col], errors="coerce")
        df[col] = maybe_num.where(~maybe_num.isna(), df[col])

    return df.drop_duplicates().reset_index(drop=True)


def _from_loadcurve(
    df: pd.DataFrame, *, sector_default_cset_cn: str | None = None
) -> pd.DataFrame:
    """Transform (Year, TimeSlice, LoadCurve[, Commodity]) into COM_FR schema."""
    df = df.copy()
    df["Attribute"] = "COM_FR"
    df["Cset_SET"] = "DEM"
    df["NI"] = df["LoadCurve"]
    df["SI"] = df["LoadCurve"]
    if "Commodity" in df.columns:
        df["Cset_CN"] = df["Commodity"].astype("string").str.strip()
    elif "Technology" in df.columns:
        df["Cset_CN"] = df["Technology"].astype("string").str.strip()
    else:
        df["Cset_CN"] = sector_default_cset_cn or "SECTOR"

    out = df[["TimeSlice", "Attribute", "Cset_CN", "Cset_SET", "Year", "NI", "SI"]]
    return _coerce_and_order(out)


# ---------------------------------------------------------------------
# Sector builders
# ---------------------------------------------------------------------


def build_industry_df() -> pd.DataFrame:
    """Build industry load-curve table."""
    path = INDUSTRY_ASSUMPTIONS / "load_curves_ind.csv"
    logger.info("Reading industry curves from %s", path)
    df = pd.read_csv(path)
    df["Attribute"] = "COM_FR"
    df["Cset_SET"] = "DEM"
    if "NI" not in df.columns and "LoadCurve" in df.columns:
        df["NI"] = df["LoadCurve"]
        df["SI"] = df["LoadCurve"]
    return _coerce_and_order(df)


def build_residential_df() -> pd.DataFrame:
    """Build residential load-curve table."""
    path = LOAD_CURVE_DATA / "residential_curves.csv"
    logger.info("Reading residential curves from %s", path)
    return _from_loadcurve(pd.read_csv(path), sector_default_cset_cn="JD*,DD*")


def build_agriculture_df() -> pd.DataFrame:
    """Build agriculture load-curve table (merge base, irrigation, MPM)."""
    paths = [
        AG_ASSUMPTIONS / "ag_curves.csv",
        AG_ASSUMPTIONS / "ag_curves_irrigation.csv",
        AG_ASSUMPTIONS / "ag_curves_mpm.csv",
    ]
    for p in paths:
        logger.info("Reading agriculture curves from %s", p)
    frames = [pd.read_csv(p) for p in paths]
    return _from_loadcurve(pd.concat(frames, ignore_index=True))


def build_commercial_df() -> pd.DataFrame:
    """Build commercial load-curve table."""
    path = COM_ASSUMPTIONS / "commercial_curves.csv"
    logger.info("Reading commercial curves from %s", path)
    return _from_loadcurve(pd.read_csv(path))


# ---------------------------------------------------------------------
# MAIN – orchestrate builders & write outputs
# ---------------------------------------------------------------------


def main() -> None:
    """Generate and export COM_FR load-curve tables for each sector."""
    outputs = {
        "com_fr_industry.csv": build_industry_df(),
        "com_fr_residential.csv": build_residential_df(),
        "com_fr_agriculture.csv": build_agriculture_df(),
        "com_fr_commercial.csv": build_commercial_df(),
    }

    for filename, df in outputs.items():
        out_path = OUTPUT_LOCATION / filename
        df.to_csv(out_path, index=False)
        logger.info("Saved %s (%d rows)", out_path, len(df))

    logger.info("All COM_FR load-curve files successfully generated.")


if __name__ == "__main__":
    main()
