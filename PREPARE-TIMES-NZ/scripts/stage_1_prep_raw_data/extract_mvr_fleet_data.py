"""
extract_mvr_fleet_data.py
Reads NZTA’s annual fleet CSV (Fleet-31Dec2023.csv) and returns a
vehicle-count table (vehicletype × custom_motive_group).

Typical use:
    from extract_mvr_fleet_data import generate_vehicle_counts
    vc = generate_vehicle_counts(2023)                   # <- Path implied
"""

from __future__ import annotations
import glob
import logging
from pathlib import Path
from typing import List

import pandas as pd

from prepare_times_nz.filepaths import DATA_RAW, STAGE_1_DATA

# ──────────────────────────────────────────────────────────────── #
# Logging
# ──────────────────────────────────────────────────────────────── #
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ──────────────────────────────────────────────────────────────── #
# Constants - all paths use pathlib for cross-platform consistency
# ──────────────────────────────────────────────────────────────── #
INPUT_LOCATION = Path(DATA_RAW) / "external_data" / "nzta"
OUTPUT_LOCATION = Path(STAGE_1_DATA) / "fleet_vkt_pj"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

NZTA_FILE: Path = INPUT_LOCATION / "Fleet-31Dec2023.csv"

# ────────────────────────────────────────────────────────────────
# Vehicle- and fuel-type classifications constants
# ────────────────────────────────────────────────────────────────
LCV = {"GOODS VAN/TRUCK/UTILITY", "MOTOR CARAVAN", "BUS"}
LPV = {"PASSENGER CAR/VAN"}
TRUCK = {"GOODS VAN/TRUCK/UTILITY", "MOTOR CARAVAN"}
MOTORCYCLE = {"MOTORCYCLE", "MOPED"}
BUS = {"BUS"}
EXCLUDED = {
    "AGRICULTURAL MACHINE", "ATV", "HIGH SPEED AGRICULTURAL VEHICLE",
    "MOBILE MACHINE", "TRACTOR", "TRAILER NOT DESIGNED FOR H/WAY USE",
    "TRAILER/CARAVAN", "SPECIAL PURPOSE VEHICLE",
}

BEV           = {"ELECTRIC"}
DIESEL_ICE    = {"DIESEL", "DIESEL HYBRID", "DIESEL ELECTRIC HYBRID"}
LPG_ICE       = {"LPG", "CNG"}
PETROL_HYBRID = {"PETROL HYBRID", "PETROL ELECTRIC HYBRID"}
PHEV          = {
    "PLUGIN PETROL HYBRID", "ELECTRIC [PETROL EXTENDED]",
    "PLUGIN DIESEL HYBRID", "ELECTRIC [DIESEL EXTENDED]",
}
PETROL_ICE    = {"PETROL", "OTHER", "ELECTRIC FUEL CELL HYDROGEN"}

MOTORCYCLE_PETROL_ICE = DIESEL_ICE | LPG_ICE | PETROL_ICE | PETROL_HYBRID | PHEV
MEDTR_PETROL_ICE      = PETROL_ICE | PETROL_HYBRID | PHEV
MEDTR_DIESEL_ICE      = DIESEL_ICE | LPG_ICE
HEVTR_DIESEL_ICE      = DIESEL_ICE | LPG_ICE | PETROL_ICE | PETROL_HYBRID | PHEV
VHEVTR_DIESEL_ICE     = HEVTR_DIESEL_ICE

# ────────────────────────────────────────────────────────────────
# Classification helpers
# ────────────────────────────────────────────────────────────────
def classify_vehicle(row: pd.Series) -> str:
    vehicle_type = str(row["VEHICLE_TYPE"]).strip().upper()
    gvm          = row["GROSS_VEHICLE_MASS"]

    if vehicle_type in LCV and gvm <= 3500:
        return "LCV"
    if vehicle_type in LPV and gvm <= 3500:
        return "LPV"
    if vehicle_type in TRUCK and gvm < 10_000:
        return "MedTr"
    if vehicle_type in TRUCK and gvm < 25_000:
        return "HevTr"
    if vehicle_type in TRUCK and gvm >= 25_000:
        return "VHevTr"
    if vehicle_type in MOTORCYCLE:
        return "Motorcycle"
    if vehicle_type in BUS and gvm > 3500:
        return "Bus"
    if vehicle_type in EXCLUDED:
        return "Excluded"
    return "NaN"

def assign_motive_group(row: pd.Series) -> str | None:
    mp = str(row["MOTIVE_POWER"]).strip().upper()
    vt = str(row["vehicletype"]).strip()

    if mp in BEV:
        return "BEV"
    if vt == "Motorcycle":
        return "Petrol_ICE" if mp in MOTORCYCLE_PETROL_ICE else None
    if vt == "MedTr":
        if mp in MEDTR_DIESEL_ICE:
            return "Diesel_ICE"
        if mp in MEDTR_PETROL_ICE:
            return "Petrol_ICE"
    if vt == "HevTr"  and mp in HEVTR_DIESEL_ICE:
        return "Diesel_ICE"
    if vt == "VHevTr" and mp in VHEVTR_DIESEL_ICE:
        return "Diesel_ICE"
    if mp in LPG_ICE:
        return "LPG_ICE"
    if mp in PETROL_HYBRID:
        return "Petrol_Hybrid"
    if mp in PETROL_ICE:
        return "Petrol_ICE"
    if mp in PHEV:
        return "PHEV"
    if mp in DIESEL_ICE:
        return "Diesel_ICE"
    return None

# ────────────────────────────────────────────────────────────────
# Data wrangling pipeline
# ────────────────────────────────────────────────────────────────
def process_vehicle_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
    df = df[df["VEHICLE_YEAR"] <= year].copy()
    df["vehicletype"]        = df.apply(classify_vehicle,    axis=1)
    df["custom_motive_group"] = df.apply(assign_motive_group, axis=1)
    return df

def generate_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby(["vehicletype", "custom_motive_group"])
              .size()
              .reset_index(name="vehicle_count"))

def generate_vehicle_counts(year: int,
                            directory: Path | str | None = None) -> pd.DataFrame:
    """
    Return a vehicle-count table for *year*.

    Parameters
    ----------
    year : int
        Cut-off year (≤ VEHICLE_YEAR).
    directory : Path | str | None, optional
        If given, overrides the default NZTA_DIR.
    """

    df         = pd.read_csv(NZTA_FILE, low_memory=False)
    df_proc    = process_vehicle_data(df, year)
    return generate_summary(df_proc)

# ────────────────────────────────────────────────────────────────
# Main script
# ────────────────────────────────────────────────────────────────

def main() -> None:
    """Generate and save vehicle-count summary for 2023."""
    logger.info("Starting vehicle-count extraction for 2023…")
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    vc = generate_vehicle_counts(2023)
    out_path = OUTPUT_LOCATION / "vehicle_counts_2023.csv"
    vc.to_csv(out_path, index=False)
    logger.info("Vehicle counts written to %s", out_path)

if __name__ == "__main__":
    main()