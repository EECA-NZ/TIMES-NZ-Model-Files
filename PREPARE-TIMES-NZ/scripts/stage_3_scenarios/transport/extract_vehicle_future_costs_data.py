"""
extract_vehicle_future_costs_data.py

• Reads
      data_raw/external_data/nrel/NREL_vehicles_fuels_<year>.csv
      ↳ generate_vehicle_costs()  from extract_vehicle_costs_data.py
• Projects future purchase costs using NREL “Conservative” (transformation) and
  “Mid” (traditional) scenarios.
• Writes the result to
      data_intermediate/stage_1_internal_data/vehicle_costs/
          vehicle_costs_by_type_fuel_projected.csv
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_1.vehicle_costs import (
    CATEGORY_TO_VEHICLE_CLASS,
    COST_COLS,
)
from prepare_times_nz.utilities.filepaths import DATA_RAW, STAGE_1_DATA, STAGE_3_DATA
from prepare_times_nz.utilities.logger_setup import logger

# ──────────────────────────────────────────────────────────────── #
# Constants - all paths use pathlib for cross-platform consistency
# ──────────────────────────────────────────────────────────────── #
INPUT_LOCATION_NREL = Path(DATA_RAW) / "external_data" / "nrel"
INPUT_LOCATION_COSTS = Path(STAGE_1_DATA) / "vehicle_costs"
OUTPUT_LOCATION = Path(STAGE_3_DATA) / "transport"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────

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
    cost_df = pd.read_csv(INPUT_LOCATION_COSTS / "vehicle_costs_by_type_fuel_2023.csv")
    nrel_path = INPUT_LOCATION_NREL / f"NREL_vehicles_fuels_{year}.csv"

    cost_df["nrel_powertrain"] = cost_df.apply(
        lambda r: TECHNOLOGY_REMAP_COMBINED.get((r["fueltype"], r["technology"])),
        axis=1,
    )
    nrel_df = pd.read_csv(nrel_path, low_memory=False)
    return cost_df, nrel_df


def filter_nrel_data(nrel_df: pd.DataFrame, scenario: str) -> pd.DataFrame:
    """Filter nrel data based on scenario and metric"""
    out = nrel_df[
        (nrel_df["scenario"] == scenario)
        & (nrel_df["metric"] == "Vehicle Cost (2022$)")
    ].copy()
    # Ensure 'year' is numeric for the pivot/indices arithmetic
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    return out


def build_nrel_cost_pivot(filtered: pd.DataFrame) -> pd.DataFrame:
    """Create pivot tables from nrel data"""
    return filtered.pivot_table(
        index=["vehicle_class", "vehicle_powertrain"], columns="year", values="value"
    )


def compute_average_costs_by_category(pivot: pd.DataFrame):
    """Compute average costs by vehicle category and powertrain."""
    avg: dict[tuple[str, str], pd.Series] = {}
    # Drive directly off what is actually present in the NREL pivot:
    powertrains = pivot.index.get_level_values("vehicle_powertrain").unique()
    for category, vclasses in CATEGORY_TO_VEHICLE_CLASS.items():
        for powertrain in powertrains:
            subset = pivot.loc[
                pivot.index.get_level_values("vehicle_class").isin(vclasses)
                & (pivot.index.get_level_values("vehicle_powertrain") == powertrain)
            ]
            if not subset.empty:
                # Average across vehicle classes for each year
                avg[(category, powertrain)] = subset.mean(axis=0)
    return avg


def compute_cost_indices(avg_costs: dict, base_year: int):
    """Compute cost indices based on average costs."""
    indices = {}
    for key, series in avg_costs.items():
        # guard against missing base year or zero division
        base = series.get(base_year)
        if pd.notna(base) and base:
            indices[key] = series / base
    return indices


def apply_indices_to_costs(
    cost_df: pd.DataFrame, indices: dict, label: str
) -> pd.DataFrame:
    """Apply cost indices to the base cost DataFrame."""
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


def reshape_to_scenario_wide(df: pd.DataFrame, keep_cols: list[str]) -> pd.DataFrame:
    """
    Take a DataFrame that has wide projected columns like:
      transformation_cost_2025, ..., transformation_cost_2050,
      traditional_cost_2025, ..., traditional_cost_2050
    and return a stacked frame with:
      [<ids from keep_cols>], scenario, cost_2025, ..., cost_2050
    where scenario ∈ {"transformation", "traditional"}.
    """
    # ── normalise & dedupe ───────────────────────────────────────
    df = df.loc[:, ~df.columns.duplicated()].copy()
    df.columns = pd.Index(df.columns).map(str).map(str.strip)
    keep_cols = list(pd.Index(keep_cols).map(str).map(str.strip).unique())

    # ensure id columns exist
    missing_ids = [c for c in keep_cols if c not in df.columns]
    if missing_ids:
        raise KeyError(f"id_vars missing from cost_df: {missing_ids}")

    # find projected columns
    trans_cols = [c for c in df.columns if c.startswith("transformation_cost_")]
    trad_cols = [c for c in df.columns if c.startswith("traditional_cost_")]
    if not trans_cols and not trad_cols:
        raise ValueError(
            "No columns found (transformation_cost_* or traditional_cost_*)."
        )

    # helper to build a scenario block and rename "<scenario>_cost_YYYY" -> "cost_YYYY"
    def make_block(cols: list[str], scenario_label: str) -> pd.DataFrame:
        if not cols:
            # empty block with correct shape
            return pd.DataFrame(columns=keep_cols + ["scenario"])
        block = df[keep_cols + cols].copy()
        rename_map = {
            c: re.sub(r"^(?:transformation|traditional)_", "", c) for c in cols
        }
        block.rename(columns=rename_map, inplace=True)
        block.insert(len(keep_cols), "scenario", scenario_label)
        return block

    trans_block = make_block(trans_cols, "transformation")
    trad_block = make_block(trad_cols, "traditional")

    out = pd.concat([trans_block, trad_block], ignore_index=True)

    # order columns: ids, scenario, then cost_YYYY ascending
    cost_cols = sorted(
        [c for c in out.columns if re.fullmatch(r"cost_\d{4}", c)],
        key=lambda s: int(s.split("_")[1]),
    )
    out = out[keep_cols + ["scenario"] + cost_cols]

    # final dedupe/sanity
    out = out.loc[:, ~out.columns.duplicated()].copy()
    return out


# ════════════════════════════════════════════════════════════════
# main orchestrator
# ════════════════════════════════════════════════════════════════


def generate_future_costs(year: int) -> pd.DataFrame:
    """
    Generate future vehicle costs based on NREL data, producing a frame with:
      [<ids from COST_COLS>], scenario, cost_2025, ..., cost_2050
    scenario ∈ {"transformation", "traditional"}.
    Relies on the existing helpers in this module:
      load_data, filter_nrel_data, build_nrel_cost_pivot,
      compute_average_costs_by_category, compute_cost_indices, apply_indices_to_costs
    and constants: COST_COLS.
    """
    cost_df, nrel_df = load_data(year)

    # build projections for both scenarios → wide columns
    for scenario, label in [("Conservative", "transformation"), ("Mid", "traditional")]:
        filtered = filter_nrel_data(nrel_df, scenario)
        pivot = build_nrel_cost_pivot(filtered)
        avg = compute_average_costs_by_category(pivot)
        idx = compute_cost_indices(avg, base_year=year)
        cost_df = apply_indices_to_costs(cost_df, idx, label)

    # normalise/dedupe columns
    cost_df.columns = pd.Index(cost_df.columns).map(str).map(str.strip)
    cost_df = cost_df.loc[:, ~cost_df.columns.duplicated()].copy()

    # ids to keep + the projected columns we just created
    keep = list(pd.Index(list(COST_COLS)).map(str).map(str.strip).unique())
    missing = [c for c in keep if c not in cost_df.columns]
    if missing:
        raise KeyError(f"Missing base columns in cost_df: {missing}")

    projected = [
        c
        for c in cost_df.columns
        if c.startswith(("transformation_cost_", "traditional_cost_"))
    ]
    if not projected:
        raise ValueError("No projected columns found after applying indices.")

    # select and reshape to scenario-wide output
    cost_df = cost_df[keep + projected].copy()
    cost_df = reshape_to_scenario_wide(cost_df, keep_cols=keep)

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
