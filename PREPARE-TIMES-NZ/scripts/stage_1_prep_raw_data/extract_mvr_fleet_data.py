"""
extract_mvr_fleet_data.py
Reads NZTA’s annual fleet CSV (Fleet-31Dec2023.csv) and returns a
vehicle-count table (vehicletype × custom_motive_group).

Typical use:
    from extract_mvr_fleet_data import generate_vehicle_counts
    vc = generate_vehicle_counts(2023)                   # <- Path implied
"""

from __future__ import annotations

import logging
from pathlib import Path

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
    "AGRICULTURAL MACHINE",
    "ATV",
    "HIGH SPEED AGRICULTURAL VEHICLE",
    "MOBILE MACHINE",
    "TRACTOR",
    "TRAILER NOT DESIGNED FOR H/WAY USE",
    "TRAILER/CARAVAN",
    "SPECIAL PURPOSE VEHICLE",
}

BEV = {"ELECTRIC"}
DIESEL_ICE = {"DIESEL", "DIESEL HYBRID", "DIESEL ELECTRIC HYBRID"}
LPG_ICE = {"LPG", "CNG"}
PETROL_HYBRID = {"PETROL HYBRID", "PETROL ELECTRIC HYBRID"}
PHEV = {
    "PLUGIN PETROL HYBRID",
    "ELECTRIC [PETROL EXTENDED]",
    "PLUGIN DIESEL HYBRID",
    "ELECTRIC [DIESEL EXTENDED]",
}
PETROL_ICE = {"PETROL", "OTHER", "ELECTRIC FUEL CELL HYDROGEN"}

MOTORCYCLE_PETROL_ICE = DIESEL_ICE | LPG_ICE | PETROL_ICE | PETROL_HYBRID | PHEV
MEDTR_PETROL_ICE = PETROL_ICE | PETROL_HYBRID | PHEV
MEDTR_DIESEL_ICE = DIESEL_ICE | LPG_ICE
HEVTR_DIESEL_ICE = DIESEL_ICE | LPG_ICE | PETROL_ICE | PETROL_HYBRID | PHEV
VHEVTR_DIESEL_ICE = HEVTR_DIESEL_ICE


# ────────────────────────────────────────────────────────────────
# Classification helpers
# ────────────────────────────────────────────────────────────────


def classify_vehicle(row: pd.Series) -> str:
    """
    Classify a vehicle based on its type and gross vehicle mass (GVM).

    Parameters:
    -----------
    row : pd.Series
        A row from a DataFrame containing 'VEHICLE_TYPE' and 'GROSS_VEHICLE_MASS'.

    Returns:
    --------
    str
        One of the categories: "LCV", "LPV", "MedTr", "HevTr", "VHevTr",
        "Motorcycle", "Bus", "Excluded", or "NaN".
    """
    vehicle_type = str(row["VEHICLE_TYPE"]).strip().upper()
    gvm = row["GROSS_VEHICLE_MASS"]

    result = "NaN"

    if vehicle_type in LCV and gvm <= 3500:
        result = "LCV"
    elif vehicle_type in LPV and gvm <= 3500:
        result = "LPV"
    elif vehicle_type in TRUCK:
        if gvm < 10_000:
            result = "MedTr"
        elif gvm < 25_000:
            result = "HevTr"
        else:  # gvm >= 25_000
            result = "VHevTr"
    elif vehicle_type in MOTORCYCLE:
        result = "Motorcycle"
    elif vehicle_type in BUS and gvm > 3500:
        result = "Bus"
    elif vehicle_type in EXCLUDED:
        result = "Excluded"

    return result


# pylint: disable=too-many-branches
def assign_motive_group(row: pd.Series) -> str | None:
    """
    Assign a custom motive group label based on the vehicle's motive power and type.

    Parameters:
    -----------
    row : pd.Series
        A row from a DataFrame containing 'MOTIVE_POWER' and 'vehicletype'.

    Returns:
    --------
    str or None
        The assigned motive group, such as "BEV", "Petrol_ICE",
        "Diesel_ICE", etc., or None if no match is found.
    """
    mp = str(row["MOTIVE_POWER"]).strip().upper()
    vt = str(row["vehicletype"]).strip()

    result = None

    if mp in BEV:
        result = "BEV"
    elif vt == "Motorcycle":
        if mp in MOTORCYCLE_PETROL_ICE:
            result = "Petrol_ICE"
    elif vt == "MedTr":
        if mp in MEDTR_DIESEL_ICE:
            result = "Diesel_ICE"
        elif mp in MEDTR_PETROL_ICE:
            result = "Petrol_ICE"
    elif vt == "HevTr" and mp in HEVTR_DIESEL_ICE:
        result = "Diesel_ICE"
    elif vt == "VHevTr" and mp in VHEVTR_DIESEL_ICE:
        result = "Diesel_ICE"
    elif mp in LPG_ICE:
        result = "LPG_ICE"
    elif mp in PETROL_HYBRID:
        result = "Petrol_Hybrid"
    elif mp in PETROL_ICE:
        result = "Petrol_ICE"
    elif mp in PHEV:
        result = "PHEV"
    elif mp in DIESEL_ICE:
        result = "Diesel_ICE"

    return result


# ────────────────────────────────────────────────────────────────
# Data wrangling pipeline
# ────────────────────────────────────────────────────────────────
def process_vehicle_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Process the vehicle data to classify vehicles and assign motive groups."""
    df = df[df["VEHICLE_YEAR"] <= year].copy()
    df["vehicletype"] = df.apply(classify_vehicle, axis=1)
    df["custom_motive_group"] = df.apply(assign_motive_group, axis=1)
    return df


def generate_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Generate a summary of vehicle counts by type and motive group.
    Parameters."""
    return (
        df.groupby(["vehicletype", "custom_motive_group"])
        .size()
        .reset_index(name="vehicle_count")
    )


def generate_vehicle_counts(year: int) -> pd.DataFrame:
    """
    Return a vehicle-count table for *year*.

    Parameters
    ----------
    year : int
        Cut-off year (≤ VEHICLE_YEAR).
    directory : Path | str | None, optional
        If given, overrides the default NZTA_DIR.
    """

    df = pd.read_csv(NZTA_FILE, low_memory=False)
    df_proc = process_vehicle_data(df, year)
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
