"""
Build the TIMES-NZ Biofuel & Biomass Process Declarations table and

Creates a combined DataFrame of all biomass/biofuel technologies grouped
by Set, TechName, and Units (Tact, Tcap).

Outputs:
  - <STAGE_4_DATA>/biofuels/biofuel_process_declarations.csv

"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_3_DATA,
    STAGE_4_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

biomass_prices = ASSUMPTIONS / "biofuels" / "biomass_prices.csv"
recoverability = ASSUMPTIONS / "biofuels" / "recoverability_factors_by_resource.csv"
biomass_supply_pj = (
    STAGE_3_DATA / "biofuel" / "aggregated_regional_biomass_supply_projections.csv"
)
region_island_map = CONCORDANCES / "region_island_concordance.csv"

OUTPUT_DIR = Path(STAGE_4_DATA) / "base_year_pri"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGION_MAP = {}


# ----------------------------------------------------------------------------
# Save helper
# ----------------------------------------------------------------------------
def save_output(df: pd.DataFrame, output_path: Path) -> None:
    """Save output CSV with logging."""
    logger.info("Saving biofuel process declarations → %s", blue_text(output_path))
    df.to_csv(output_path, index=False)
    logger.info("Saved %d rows.", len(df))


# ----------------------------------------------------------------------------
# Define grouped technology declarations
# ----------------------------------------------------------------------------
def build_biofuel_processes() -> pd.DataFrame:
    """Construct grouped biomass/biofuel process declarations."""

    biofuel_groups = [
        # --- Primary biomass supply (MIN / PJ / PJa) ---
        {
            "Sets": "MIN",
            "Tact": "PJ",
            "Tcap": "PJa",
            "TechName": [
                "MINWODWST00",  # in-forests residues landings
                "MINWODWST01",  # in-forests residues hauler/ground-based cutover
                "MINWODWST02",  # waste thinnings
                "MINWODWST03",  # pruning residues
                "MINWODWST04",  # production thinnings
                "MINWODWST05",  # port bark
                "MINWODWST06",  # sawmill chip
                "MINWODWST07",  # shelterbelt turnover residuals
                "MINAGRWST00",  # straw & stover residues
                "MINAGRWST01",  # orchard & viticulture residues
                "MINMNCWST00",  # municipal wood wastes
                "MINMNCWST01",  # municipal solid wates & wastewater, and industrial wastewater
                "MINANMMNR00",  # animal manure
                "MINOILWST00",  # waste cooking oil
                "MINOILWST01",  # tallow waste
                "MINWODSUPCUR00",  # current wood - pulp logs
                "MINWODSUPCUR01",  # current wood - a grade logs
                "MINWODSUPCUR02",  # current wood - k grade logs
                "MINWODSUPCUR03",  # current wood - douglas-fir production thinnings
                "MINWODSUPOSWOD",  # wood processing residues (on-site wood residues)
            ],
        },
        {
            "Sets": "IMP",
            "Tact": "PJ",
            "Tcap": "PJa",
            "TechName": [
                "IMPSAF",  # Imported Sustainable Aviation Fuel
            ],
        },
        # --- Refining / processing (PRE / PJ / GWth) ---
        {
            "Sets": "PRE",
            "Tact": "PJ",
            "Tcap": "GWth",
            "TechName": [
                "REF_ANDGST",  # Biogas from woody residues, agricultural residues,
                # animal manure, municipal waste - Anaerobic Digestion (AD)
                "CT_CWODBPL",  # Black pellets production - torrefaction
                "CT_CWODETH",  # Ethanol from wood waste - gasification
                "CT_COILBDS",  # Biodiesel from tallow and oil waste, pyrolosis
                "CT_CWODDID",  # Drop-in diesel/jet from wood waste - pyrolysis,
                # hydrothermal liquefaction, or gasification
            ],
        },
        # --- One processing tech with different capacity unit (PJa) ---
        {
            "Sets": "PRE",
            "Tact": "PJ",
            "Tcap": "PJa",
            "TechName": [
                "WSTWOD2WOD",  # Waste wood to fuel wood for current wood
                # and  wood processing residues
            ],
        },
    ]

    records = []
    for group in biofuel_groups:
        for tech in group["TechName"]:
            records.append(
                {
                    "Sets": group["Sets"],
                    "TechName": tech,
                    "Tact": group["Tact"],
                    "Tcap": group["Tcap"],
                }
            )

    df = pd.DataFrame(records)
    return df


# pylint: disable=too-many-locals
def create_biofuel_supply_forecasts() -> pd.DataFrame:
    """Create base-year biofuel supply forecasts joined with prices and island mapping."""

    # --- Load datasets ---
    prices_df = pd.read_csv(biomass_prices)
    supply_df = pd.read_csv(biomass_supply_pj)
    region_map = pd.read_csv(region_island_map)
    recoverability_df = pd.read_csv(recoverability)
    recoverability_df.columns = recoverability_df.columns.str.strip()

    supply_df["Value"] = supply_df["Value"].astype(float)
    supply_df.loc[supply_df["Value"] <= 0, "Value"] = pd.NA

    # Map Region to Island
    supply_df = supply_df.merge(region_map, on="Region", how="left")

    # Aggregate supply (sum will stay NaN if all inputs were NaN)
    agg_supply = supply_df.groupby(["BiomassType", "Island", "Year"], as_index=False)[
        "Value"
    ].sum(min_count=1)

    # --- Mapping to TechName ---
    biomass_to_tech = {
        "in-forest residues landings": "MINWODWST00",
        "in-forest residues ground-based cutover": "MINWODWST01",
        "in-forests residues hauler cutover": "MINWODWST01",
        "waste thinnings": "MINWODWST02",
        "pruning residues": "MINWODWST03",
        "production thinnings": "MINWODWST04",
        "port bark": "MINWODWST05",
        "sawmill chip": "MINWODWST06",
        "shelterbelt turnover residuals": "MINWODWST07",
        "straw and stover residues": "MINAGRWST00",
        "orchard and viticulture residues": "MINAGRWST01",
        "municipal wood wastes": "MINMNCWST00",
        "municipal wastes": "MINMNCWST01",
        "animal manure": "MINANMMNR00",
        "waste oil": "MINOILWST00",
        "tallow waste": "MINOILWST01",
        "pulp log": "MINWODSUPCUR00",
        "a grade logs": "MINWODSUPCUR01",
        "k grade logs": "MINWODSUPCUR02",
        "douglas-fir production thinnings": "MINWODSUPCUR03",
        "wood processing residues": "MINWODSUPOSWOD",  # on-site wood residues
        "sustainable aviation fuel": "IMPSAF",
    }

    agg_supply["BiomassType"] = agg_supply["BiomassType"].str.strip().str.lower()
    biomass_to_tech = {k.lower(): v for k, v in biomass_to_tech.items()}
    agg_supply["TechName"] = agg_supply["BiomassType"].map(biomass_to_tech)

    # --- Pivot WITHOUT fill_value so missing stays NaN ---
    pivot_supply = agg_supply.pivot_table(
        index=["TechName", "Island"],
        columns="Year",
        values="Value",
        aggfunc="sum",
        dropna=False,  # missing remains missing
    ).reset_index()

    # Rename columns to ACT_BND~YYYY
    pivot_supply.columns = [
        f"ACT_BND~{c}" if isinstance(c, int) else c for c in pivot_supply.columns
    ]

    # --- Outer merge with prices ---
    merged = pivot_supply.merge(prices_df, on="TechName", how="outer")

    # Ensure Island exists even if only from prices_df
    if "Island" not in merged.columns:
        merged["Island"] = pd.NA

    merged = merged.rename(columns={"Cost$perGJ": "COST~2023"})

    # Identify ACT_BND columns
    year_cols = [c for c in merged.columns if c.startswith("ACT_BND~")]

    # Merge with main table
    merged = merged.merge(recoverability_df, on="TechName", how="left")

    # Multiply all ACT_BND columns by the recoverability factor
    for col in year_cols:
        merged[col] = merged[col] * merged["Recoverability  factor 1  (% of gross)"]

    # Clean up: Remove Recoverability column if not needed
    merged = merged.drop(columns=["Recoverability  factor 1  (% of gross)"])

    # --- Duplicate missing-island techs across NI & SI ---
    missing_island = merged[merged["Island"].isna()].copy()
    if not missing_island.empty:
        ni_rows = missing_island.copy()
        ni_rows["Island"] = "NI"

        si_rows = missing_island.copy()
        si_rows["Island"] = "SI"

        merged = merged[merged["Island"].notna()]
        merged = pd.concat([merged, ni_rows, si_rows], ignore_index=True)

    # Final tidy
    merged = merged.rename(columns={"Island": "Region"})
    merged = merged[["TechName", "Comm-OUT", "Region", "COST~2023"] + year_cols]

    # Identify year columns
    year_cols_upto_2053 = [c for c in year_cols if int(c.split("~")[1]) <= 2053]
    year_cols_from_2026_to_2053 = [
        c for c in year_cols if 2026 <= int(c.split("~")[1]) <= 2053
    ]

    # Constant supply overrides
    supply_constants_all_years = {
        "MINMNCWST01": {
            "NI": 1.721,
            "SI": 0.514,
        },  # split based on population 77% NI, 23% SI
        "MINANMMNR00": {
            "NI": 4.234,
            "SI": 3.326,
        },  # split based on total pigs and DC numbers 56% NI, 44% SI
    }

    supply_constants_from_2026 = {
        "MINOILWST00": {
            "NI": 0.180,
            "SI": 0.054,
        },  # split based on population 77% NI, 23% SI
        "MINOILWST01": {"NI": 0, "SI": 6.240},  # 100% in SI
    }

    # Apply constants
    for tech, region_vals in supply_constants_all_years.items():
        mask_tech = merged["TechName"] == tech

        # Apply separately for NI and SI rows
        for region, constant_value in region_vals.items():
            mask_region = merged["Region"] == region
            merged.loc[mask_tech & mask_region, year_cols_upto_2053] = constant_value

    # Apply constants for years >= 2026
    for tech, region_vals in supply_constants_from_2026.items():
        mask_tech = merged["TechName"] == tech

        for region, constant_value in region_vals.items():
            mask_region = merged["Region"] == region
            merged.loc[mask_tech & mask_region, year_cols_from_2026_to_2053] = (
                constant_value
            )

    # Replace remaining zeros only in ACT_BND columns
    merged[year_cols] = merged[year_cols].replace(0, pd.NA)

    return merged


# ----------------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------------
def main() -> None:
    """Entry point for biofuel process declaration generation."""
    logger.info("Building TIMES-NZ Biofuel Process Declarations…")

    df = build_biofuel_processes()
    logger.info("Constructed DataFrame with %d records.", len(df))
    logger.debug("Preview of data:\n%s", df.head())

    save_output(df, OUTPUT_DIR / "biofuel_supply_process_declarations.csv")
    logger.info("Biofuel process declaration generation complete.")

    logger.info("Building TIMES-NZ Biofuel supply forecasts…")

    df = create_biofuel_supply_forecasts()
    logger.info("Constructed DataFrame with %d records.", len(df))
    logger.debug("Preview of data:\n%s", df.head())

    save_output(df, OUTPUT_DIR / "biofuel_supply_forecasts.csv")
    logger.info("Biofuel supply forecasts generation complete.")


if __name__ == "__main__":
    main()
