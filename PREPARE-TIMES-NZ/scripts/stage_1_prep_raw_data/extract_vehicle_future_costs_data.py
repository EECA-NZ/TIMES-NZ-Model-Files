"""
extract_vehicle_future_costs_data.py

• Reads
      data_raw/external_data/nrel/NREL_vehicles_fuels_<year>.csv
      ↳ generate_vehicle_costs()  from extract_vehicle_costs_data.py
• Projects future purchase costs using NREL “Conservative” (tui) and
  “Mid” (kea) scenarios.
• Writes the result to
      data_intermediate/stage_1_internal_data/vehicle_costs/
          vehicle_costs_by_type_fuel_projected.csv
"""

from __future__ import annotations
import logging
from pathlib import Path

import numpy as np
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
INPUT_LOCATION_NREL = Path(DATA_RAW) / "external_data" / "nrel"

OUTPUT_LOCATION = Path(STAGE_1_DATA) / "vehicle_costs"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────
CATEGORY_TO_VEHICLE_CLASS = {
    'LPV': ['Compact', 'Midsize', 'Midsize SUV', 'Small SUV'],
    'LCV': ['Pickup', 'Class 2 Medium Van', 'Class 3 Medium Pickup', 'Class 3 Medium School', 'Class 3 Medium Van'],
    'Light Truck': [
        'Class 4 Medium Box', 'Class 4 Medium Service', 'Class 4 Medium StepVan',
        'Class 5 Medium Utility',
        'Class 6 Medium Box', 'Class 6 Medium Construction', 'Class 6 Medium StepVan'
    ],
    'Medium Truck': ['Class 7 Medium Box', 'Class 7 Medium School', 'Class 7 Tractor DayCab'],
    'Heavy Truck': [
        'Class 8 Beverage DayCab', 'Class 8 Drayage DayCab', 'Class 8 Longhaul Sleeper',
        'Class 8 Regional DayCab', 'Class 8 Vocational Heavy'
    ],
    'Bus': ['Class 8 Transit Heavy']
}

TECH_TO_POWERTRAIN = {
    'Battery Electric': 'Battery Electric',
    'Diesel Hybrid': 'Diesel Hybrid',
    'Diesel ICE': 'Diesel',
    'Dual Fuel': 'Dual Fuel',
    'Hydrogen Fuel Cell': 'Hydrogen Fuel Cell',
    'Petrol Hybrid': 'Gasoline Hybrid',
    'Petrol ICE': 'Gasoline',
    'Plug-in Hybrid': 'Plug-in Hybrid',
    'LPG': 'Natural Gas',
}

TECHNOLOGY_REMAP_COMBINED = {
    ("Electricity", "BEV"): "Battery Electric",
    ("Diesel", "ICE Hybrid"): "Diesel Hybrid",
    ("Petrol", "ICE Hybrid"): "Gasoline Hybrid",
    ("Diesel", "ICE"): "Diesel",
    ("Petrol", "ICE"): "Gasoline",
    ("LPG", "ICE"): "Natural Gas",
    ("Hydrogen", "H2R"): "Hydrogen Fuel Cell",
    ("Petrol/Diesel/Electricity", "PHEV"): "Plug-in Hybrid",
    ("Petrol/LPG", "ICE"): "Dual Fuel",
}

# ════════════════════════════════════════════════════════════════
# helper functions
# ════════════════════════════════════════════════════════════════
def load_data(year: int):
    """Generate base cost table and load matching NREL CSV."""
    cost_df = pd.read_csv(OUTPUT_LOCATION / "vehicle_costs_by_type_fuel_2023.csv")
    nrel_path = INPUT_LOCATION_NREL / f"NREL_vehicles_fuels_{year}.csv"

    cost_df["nrel_powertrain"] = cost_df.apply(
        lambda r: TECHNOLOGY_REMAP_COMBINED.get((r["fueltype"], r["technology"])),
        axis=1,
    )
    nrel_df = pd.read_csv(nrel_path, low_memory=False)
    return cost_df, nrel_df


def filter_nrel_data(nrel_df: pd.DataFrame, scenario: str) -> pd.DataFrame:
    return nrel_df[
        (nrel_df["scenario"] == scenario)
        & (nrel_df["metric"] == "Vehicle Cost (2022$)")
    ]


def build_nrel_cost_pivot(filtered: pd.DataFrame) -> pd.DataFrame:
    return filtered.pivot_table(
        index=["vehicle_class", "vehicle_powertrain"], columns="year", values="value"
    )


def compute_average_costs_by_category(pivot: pd.DataFrame):
    avg: dict[tuple[str, str], pd.Series] = {}
    for category, vclasses in CATEGORY_TO_VEHICLE_CLASS.items():
        for tech, powertrain in TECH_TO_POWERTRAIN.items():
            subset = pivot.loc[
                pivot.index.get_level_values("vehicle_class").isin(vclasses)
                & (pivot.index.get_level_values("vehicle_powertrain") == powertrain)
            ]
            if not subset.empty:
                avg[(category, powertrain)] = subset.mean(axis=0)
    return avg


def compute_cost_indices(avg_costs: dict, base_year: int):
    indices = {}
    for key, series in avg_costs.items():
        if base_year in series and pd.notna(series[base_year]) and series[base_year]:
            indices[key] = series / series[base_year]
    return indices


def apply_indices_to_costs(
    cost_df: pd.DataFrame, indices: dict, label: str
) -> pd.DataFrame:
    for (category, powertrain), idx_series in indices.items():
        mask = (cost_df["vehicletype"] == category) & (
            cost_df["nrel_powertrain"] == powertrain
        )
        for yr, idx in idx_series.items():
            if yr == 2023:
                continue
            col = f"{label}_cost_{yr}"
            cost_df.loc[mask, col] = cost_df.loc[mask, "cost_2023_nzd"] * idx
    return cost_df

# ════════════════════════════════════════════════════════════════
# main orchestrator
# ════════════════════════════════════════════════════════════════
def generate_future_costs(year: int) -> pd.DataFrame:
    cost_df, nrel_df = load_data(year)

    for scenario, label in [("Conservative", "tui"), ("Mid", "kea")]:
        filtered = filter_nrel_data(nrel_df, scenario)
        pivot = build_nrel_cost_pivot(filtered)
        avg = compute_average_costs_by_category(pivot)
        idx = compute_cost_indices(avg, base_year=year)
        cost_df = apply_indices_to_costs(cost_df, idx, label)

    keep = ["vehicletype", "fueltype", "technology", "cost_2023_nzd", "operation_cost_2023_nzd"]
    projected = [c for c in cost_df.columns if c.startswith(("tui_cost_", "kea_cost_"))]
    cost_df = cost_df[keep + projected]

    return cost_df

# ════════════════════════════════════════════════════════════════
# Main Script
# ════════════════════════════════════════════════════════════════
def main() -> None:
    """Generate projected vehicle costs."""
    logger.info("Starting vehicle costs extraction for 2023…")
    OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
    year = 2023
    future_cost_df = generate_future_costs(year)
    out_path = OUTPUT_LOCATION / f"vehicle_costs_by_type_fuel_projected_{year}.csv"
    future_cost_df.to_csv(out_path, index=False)
    logger.info("future cost data written to %s", out_path)

if __name__ == "__main__":
    main()
