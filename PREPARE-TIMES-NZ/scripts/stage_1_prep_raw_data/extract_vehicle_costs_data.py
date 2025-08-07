"""
extract_vehicle_costs_data.py

• Reads
      data_raw/eeca_data/tcoe/     vehicle_costs_<year>.xlsx
      data_raw/external_data/nrel/     NREL_vehicles_fuels_<year>.csv
• Builds long-form purchase + operation cost table
• Writes it to
      data_intermediate/stage_1_input_data/vehicle_costs/
"""

# ────────────────────────────────────────────────────────────────
# Imports
# ────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from prepare_times_nz.utilities.deflator import deflate_columns_rowwise
from prepare_times_nz.utilities.filepaths import DATA_RAW, STAGE_1_DATA

# ──────────────────────────────────────────────────────────────── #
# Logging
# ──────────────────────────────────────────────────────────────── #
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ──────────────────────────────────────────────────────────────── #
# Constants - all paths use pathlib for cross-platform consistency
# ──────────────────────────────────────────────────────────────── #
INPUT_LOCATION_MOT = Path(DATA_RAW) / "external_data" / "mot"
INPUT_LOCATION_KIWIRAIL = Path(DATA_RAW) / "external_data" / "kiwirail"
INPUT_LOCATION_MBIE = Path(DATA_RAW) / "external_data" / "mbie"
INPUT_LOCATION_EEUD = Path(DATA_RAW) / "eeca_data" / "eeud"
INPUT_LOCATION_TCOE = Path(DATA_RAW) / "eeca_data" / "tcoe"
INPUT_LOCATION_NREL = Path(DATA_RAW) / "external_data" / "nrel"

OUTPUT_LOCATION = Path(STAGE_1_DATA) / "vehicle_costs"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────
ALL_TECHS = [
    "Petrol ICE",
    "Diesel ICE",
    "Petrol Hybrid",
    "Diesel Hybrid",
    "Plug-in Hybrid",
    "Battery Electric",
    "Hydrogen Fuel Cell",
    "LPG",
    "Dual Fuel",
]

CATEGORY_TO_VEHICLE_CLASS = {
    "LPV": ["Compact", "Midsize", "Midsize SUV", "Small SUV"],
    "LCV": [
        "Pickup",
        "Class 2 Medium Van",
        "Class 3 Medium Pickup",
        "Class 3 Medium School",
        "Class 3 Medium Van",
    ],
    "Light Truck": [
        "Class 4 Medium Box",
        "Class 4 Medium Service",
        "Class 4 Medium StepVan",
        "Class 5 Medium Utility",
        "Class 6 Medium Box",
        "Class 6 Medium Construction",
        "Class 6 Medium StepVan",
    ],
    "Medium Truck": [
        "Class 7 Medium Box",
        "Class 7 Medium School",
        "Class 7 Tractor DayCab",
    ],
    "Heavy Truck": [
        "Class 8 Beverage DayCab",
        "Class 8 Drayage DayCab",
        "Class 8 Longhaul Sleeper",
        "Class 8 Regional DayCab",
        "Class 8 Vocational Heavy",
    ],
    "Bus": ["Class 8 Transit Heavy"],
}

TECH_TO_POWERTRAIN = {
    "Battery Electric": "Battery Electric",
    "Diesel Hybrid": "Diesel Hybrid",
    "Diesel ICE": "Diesel",
    "Dual Fuel": "Dual Fuel",
    "Hydrogen Fuel Cell": "Hydrogen Fuel Cell",
    "Petrol Hybrid": "Gasoline Hybrid",
    "Petrol ICE": "Gasoline",
    "Plug-in Hybrid": "Plug-in Hybrid",
    "LPG": "Natural Gas",
}

# Mapping from original fueltype to (fueltype, technology)
FUELTYPE_MAP = {
    "Battery Electric": ("Electricity", "BEV"),
    "Diesel Hybrid": ("Diesel", "ICE Hybrid"),
    "Diesel ICE": ("Diesel", "ICE"),
    "Dual Fuel": ("Petrol/LPG", "ICE"),
    "Hydrogen Fuel Cell": ("Hydrogen", "H2R"),
    "Petrol Hybrid": ("Petrol", "ICE Hybrid"),
    "Petrol ICE": ("Petrol", "ICE"),
    "Plug-in Hybrid": ("Petrol/Diesel/Electricity", "PHEV"),
    "LPG": ("LPG", "ICE"),
}

USD_TO_NZD = 1.68
MI_TO_KM = 1.60934
TCOE_BASEYEAR = 2025  # local EECA price sheet
NREL_BASEYEAR = 2022  # NREL cost vintage


# ════════════════════════════════════════════════════════════════
# Data-loading helpers
# ════════════════════════════════════════════════════════════════
def load_data(year: int):
    """Load EECA + NREL sources for *year* from the standard folders."""
    vehicle_costs_path = INPUT_LOCATION_TCOE / f"vehicle_costs_{year}.xlsx"
    nrel_costs_path = INPUT_LOCATION_NREL / f"NREL_vehicles_fuels_{year}.csv"

    try:
        vehicle_costs = pd.read_excel(vehicle_costs_path, sheet_name="AG_costs")
        nrel_costs = pd.read_csv(nrel_costs_path, low_memory=False)
    except Exception as exc:
        raise FileNotFoundError(f"Error loading data: {exc}") from exc

    return vehicle_costs, nrel_costs


# ════════════════════════════════════════════════════════════════
# NREL extraction helpers (logic unchanged, just pathlib args)
# ════════════════════════════════════════════════════════════════
def get_nrel_costs(nrel_df: pd.DataFrame, year: int, usd_to_nzd: float):
    """Extract NREL vehicle costs for a given year, converting to NZD."""
    subset = nrel_df[
        (nrel_df["scenario"] == "Conservative")
        & (nrel_df["metric"] == "Vehicle Cost (2022$)")
    ]
    pivot = subset.pivot_table(
        index=["vehicle_class", "vehicle_powertrain"],
        columns="year",
        values="value",
    )
    if year not in pivot.columns:
        raise ValueError(f"NREL data does not contain year {year}")
    return pivot[year] * usd_to_nzd


def get_nrel_operation_costs(
    nrel_df: pd.DataFrame,
    year: int,
    usd_to_nzd: float,
    mi_to_km: float,
):
    """Extract NREL operation costs for a given year, converting to NZD/km."""
    subset = nrel_df[
        (nrel_df["scenario"] == "Conservative")
        & (nrel_df["metric"] == "Discounted Maintenance and Repair Cost (2022$/mi)")
    ]
    pivot = subset.pivot_table(
        index=["vehicle_class", "vehicle_powertrain"],
        columns="year",
        values="value",
    )
    if year not in pivot.columns:
        raise ValueError(f"NREL data does not contain year {year}")
    return pivot[year] * usd_to_nzd / mi_to_km


# ════════════════════════════════════════════════════════════════
# Utility helper
# ════════════════════════════════════════════════════════════════
def ensure_full_coverage(df: pd.DataFrame, all_categories, all_techs):
    """Ensure that the DataFrame `df` has all categories and technologies.
    If a category or technology is missing, fill with NaN."""
    for tech in all_techs:
        if tech not in df.columns:
            df[tech] = np.nan
    for cat in all_categories:
        if cat not in df.index:
            df.loc[cat] = np.nan
    return df.sort_index()


# ════════════════════════════════════════════════════════════════
# Main orchestrator
# ════════════════════════════════════════════════════════════════
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def generate_vehicle_costs(year: int) -> pd.DataFrame:
    """
    Return tidy cost table with provenance for purchase **and** operation costs.
    EECA (TCOE) values override NREL when present.
    """
    vehicle_costs_raw, nrel_costs = load_data(year)

    # ───── 1. PURCHASE PRICE ──────────────────────────────
    price_df = vehicle_costs_raw.pivot_table(
        index="Category", columns="Technology", values="Purchase Price"
    )
    price_df = ensure_full_coverage(
        price_df, CATEGORY_TO_VEHICLE_CLASS.keys(), ALL_TECHS
    )
    price_src = pd.DataFrame("TCOE", index=price_df.index, columns=price_df.columns)

    nrel_price = get_nrel_costs(nrel_costs, year, USD_TO_NZD)

    for category in price_df.index:
        for tech in price_df.columns:
            if not pd.isna(price_df.at[category, tech]):
                continue  # keep local value
            vclasses = CATEGORY_TO_VEHICLE_CLASS.get(category, [])
            powertrain = TECH_TO_POWERTRAIN.get(tech)
            if not vclasses or powertrain is None:
                continue
            vals = [nrel_price.get((vc, powertrain), np.nan) for vc in vclasses]
            vals = [v for v in vals if not np.isnan(v)]
            if not vals:
                continue
            price_df.at[category, tech] = np.mean(vals)
            price_src.at[category, tech] = "NREL"

    price_long = (
        price_df.reset_index()
        .melt(
            id_vars="Category",
            var_name="Technology",
            value_name="cost_2023",
        )
        .dropna()
    )
    price_src_long = price_src.reset_index().melt(
        id_vars="Category", var_name="Technology", value_name="purchase_source"
    )
    price_long = price_long.merge(
        price_src_long, on=["Category", "Technology"], how="left"
    )
    price_long["purchase_baseyear"] = price_long["purchase_source"].map(
        {"TCOE": TCOE_BASEYEAR, "NREL": NREL_BASEYEAR}
    )

    # ───── 2. OPERATION COST ──────────────────────────────
    op_df = vehicle_costs_raw.pivot_table(
        index="Category", columns="Technology", values="Servicing + Tyres $/km"
    )
    op_df = ensure_full_coverage(op_df, CATEGORY_TO_VEHICLE_CLASS.keys(), ALL_TECHS)
    op_src = pd.DataFrame("TCOE", index=op_df.index, columns=op_df.columns)

    nrel_op = get_nrel_operation_costs(nrel_costs, year, USD_TO_NZD, MI_TO_KM)
    nrel_only_cats = ["Light Truck", "Medium Truck", "Heavy Truck", "Bus"]

    for category in op_df.index:
        for tech in op_df.columns:
            use_nrel = pd.isna(op_df.at[category, tech]) or category in nrel_only_cats
            if not use_nrel:
                continue
            vclasses = CATEGORY_TO_VEHICLE_CLASS.get(category, [])
            powertrain = TECH_TO_POWERTRAIN.get(tech)
            if not vclasses or powertrain is None:
                continue
            vals = [nrel_op.get((vc, powertrain), np.nan) for vc in vclasses]
            vals = [v for v in vals if not np.isnan(v)]
            if not vals:
                continue
            op_df.at[category, tech] = np.mean(vals)
            op_src.at[category, tech] = "NREL"

    op_long = (
        op_df.reset_index()
        .melt(
            id_vars="Category",
            var_name="Technology",
            value_name="operation_cost_2023",
        )
        .dropna()
    )
    op_src_long = op_src.reset_index().melt(
        id_vars="Category", var_name="Technology", value_name="operation_source"
    )
    op_long = op_long.merge(op_src_long, on=["Category", "Technology"], how="left")
    op_long["operation_baseyear"] = op_long["operation_source"].map(
        {"TCOE": TCOE_BASEYEAR, "NREL": NREL_BASEYEAR}
    )

    # ───── 3. COMBINE & FINAL TIDY ────────────────────────
    vehicle_costs = price_long.merge(
        op_long, on=["Category", "Technology"], how="outer"
    )

    vehicle_costs = vehicle_costs.rename(
        columns={"Category": "vehicletype", "Technology": "fueltype"}
    )
    vehicle_costs[["fueltype", "technology"]] = (
        vehicle_costs["fueltype"].map(FUELTYPE_MAP).apply(pd.Series)
    )
    vehicle_costs = vehicle_costs[
        [
            "vehicletype",
            "fueltype",
            "technology",
            "cost_2023",
            "operation_cost_2023",
            "purchase_source",
            "purchase_baseyear",
            "operation_source",
            "operation_baseyear",
        ]
    ]
    vehicle_costs.loc[vehicle_costs["vehicletype"] == "Motorbike", "vehicletype"] = (
        "Motorcycle"
    )

    # ───── 4. Deflate money columns → 2023 NZD─────
    # right before `return vehicle_costs`
    cpi_types = ["LPV", "LCV", "Motorcycle"]
    cgpi_types = ["Light Truck", "Medium Truck", "Heavy Truck", "Bus"]

    # Split DataFrame
    df_cpi = vehicle_costs[vehicle_costs["vehicletype"].isin(cpi_types)].copy()
    df_cgpi = vehicle_costs[vehicle_costs["vehicletype"].isin(cgpi_types)].copy()

    # Deflate with CPI
    if not df_cpi.empty:
        df_cpi = deflate_columns_rowwise(
            df_cpi,
            col_to_basecol={
                "cost_2023": "purchase_baseyear",
                "operation_cost_2023": "operation_baseyear",
            },
            target_year=2023,
            method="cpi",
        )

    # Deflate with CGPI
    if not df_cgpi.empty:
        df_cgpi = deflate_columns_rowwise(
            df_cgpi,
            col_to_basecol={
                "cost_2023": "purchase_baseyear",
                "operation_cost_2023": "operation_baseyear",
            },
            target_year=2023,
            method="cgpi",
        )

    # Combine back
    vehicle_costs = pd.concat([df_cpi, df_cgpi], ignore_index=True)

    return vehicle_costs


# ════════════════════════════════════════════════════════════════
# Main Script
# ════════════════════════════════════════════════════════════════
def main() -> None:
    """Generate long-form vehicle cost table."""
    logger.info("Starting vehicle costs extraction for 2023…")
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    year = 2023
    cost_df = generate_vehicle_costs(year)
    out_path = OUTPUT_LOCATION / f"vehicle_costs_by_type_fuel_{year}.csv"
    cost_df.to_csv(out_path, index=False)
    logger.info("cost data written to %s", out_path)


if __name__ == "__main__":
    main()
