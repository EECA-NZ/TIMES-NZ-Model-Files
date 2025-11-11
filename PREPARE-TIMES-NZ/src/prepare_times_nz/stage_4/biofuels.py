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
    CONCORDANCES,
    EXTERNAL_DATA,
    STAGE_3_DATA,
    STAGE_4_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

biomass_prices = EXTERNAL_DATA / "scion" / "biomass_prices.csv"
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
                "MINWODWST05",  # wood processing residues
                "MINWODWST06",  # port bark
                "MINWODWST07",  # sawmill chip
                "MINWODWST08",  # shelterbelt turnover residuals
                "MINWODWST09",  # energy crops
                "MINAGRWST00",  # straw & stover residues
                "MINAGRWST01",  # orchard & viticulture residues
                "MINMNCWST00",  # municipal wood wastes
                "MINANMMNR00",  # animal manure
                "MINOILWST00",  # waste oil
                "MINOILWST01",  # tallow waste
                "MINWODSUPCUR00",  # current wood - pulp logs
                "MINWODSUPCUR01",  # current wood - a grade logs
                "MINWODSUPCUR02",  # current wood - k grade logs
                "MINWODSUPCUR03",  # current wood - douglas-fir production thinnings
                "MINWODSUPOSWOD",  # on-site wood residues
            ],
        },
        # --- Refining / processing (PRE / PJ / GWth) ---
        {
            "Sets": "PRE",
            "Tact": "PJ",
            "Tcap": "GWth",
            "TechName": [
                "REF_WODWST",  # Biogas from woody residues
                "REF_AGRWST",  # Biogas from agricultural residues
                "REF_ANMMNR",  # Biogas from animal manure
                "SUP_BIGNGA",  # Biogas upgrading to natural gas
                "CT_CWODPLT",  # Wood pellets production
                "CT_CWODETH",  # Ethanol from wood waste
                "CT_COILBDSL",  # Biodiesel from waste oils
                "CT_CWODDID",  # Drop-in diesel/jet from wood waste
            ],
        },
        # --- One processing tech with different capacity unit (PJa) ---
        {
            "Sets": "PRE",
            "Tact": "PJ",
            "Tcap": "PJa",
            "TechName": [
                "WSTWOD2WOD",  # Waste wood to fuel wood
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


def create_biofuel_supply_forecasts() -> pd.DataFrame:
    """Create base-year biofuel supply forecasts joined with prices and island mapping."""

    # --- Load datasets ---
    prices_df = pd.read_csv(biomass_prices)
    supply_df = pd.read_csv(biomass_supply_pj)
    region_map = pd.read_csv(region_island_map)

    logger.info(
        "Loaded prices_df: %d rows, columns=%s", len(prices_df), list(prices_df.columns)
    )
    logger.info(
        "Loaded supply_df: %d rows, columns=%s", len(supply_df), list(supply_df.columns)
    )
    logger.info(
        "Loaded region_map: %d rows, columns=%s",
        len(region_map),
        list(region_map.columns),
    )

    # --- Map Region to Island ---
    supply_df = supply_df.merge(region_map, on="Region", how="left")

    # --- Aggregate supply by BiomassType, Island, Year ---
    agg_supply = supply_df.groupby(["BiomassType", "Island", "Year"], as_index=False)[
        "Value"
    ].sum()

    logger.info("Unique BiomassTypes: %s", agg_supply["BiomassType"].unique()[:10])

    # --- Define BiomassType → TechName mapping ---
    biomass_to_tech = {
        "in-forest residues landings": "MINWODWST00",
        "in-forest residues ground-based cutover": "MINWODWST01",
        "in-forests residues hauler cutover": "MINWODWST01",
        "waste thinnings": "MINWODWST02",
        "pruning residues": "MINWODWST03",
        "production thinnings": "MINWODWST04",
        "wood processing residues": "MINWODWST05",
        "port bark": "MINWODWST06",
        "sawmill chip": "MINWODWST07",
        "shelterbelt turnover residuals": "MINWODWST08",
        "energy crops": "MINWODWST09",
        "straw and stover residues": "MINAGRWST00",
        "orchard and viticulture residues": "MINAGRWST01",
        "municipal wood wastes": "MINMNCWST00",
        "animal manure": "MINANMMNR00",
        "waste oil": "MINOILWST00",
        "tallow waste": "MINOILWST01",
        "pulp log": "MINWODSUPCUR00",
        "a grade logs": "MINWODSUPCUR01",
        "k grade logs": "MINWODSUPCUR02",
        "douglas-fir production thinnings": "MINWODSUPCUR03",
        "on-site wood residues": "MINWODSUPOSWOD",
    }

    # Normalize for consistent matching
    agg_supply["BiomassType"] = agg_supply["BiomassType"].str.strip().str.lower()
    biomass_to_tech = {k.lower(): v for k, v in biomass_to_tech.items()}

    agg_supply["TechName"] = agg_supply["BiomassType"].map(biomass_to_tech)

    logger.info(
        "TechName mapping applied: %d matched, %d missing",
        agg_supply["TechName"].notna().sum(),
        agg_supply["TechName"].isna().sum(),
    )

    # --- Pivot supply so each year becomes ACT_BND~YYYY column ---
    pivot_supply = agg_supply.pivot_table(
        index=["TechName", "Island"],
        columns="Year",
        values="Value",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    # Rename columns to ACT_BND~YYYY
    pivot_supply.columns = [
        f"ACT_BND~{c}" if isinstance(c, int) else c for c in pivot_supply.columns
    ]

    # --- Merge with biomass prices ---
    merged = pivot_supply.merge(prices_df, on="TechName", how="left")

    # --- Keep only COST~2023 (no cost per year columns) ---
    merged = merged.rename(columns={"Cost$perGJ": "COST~2023"})

    # --- Final tidy output ---
    year_cols = [c for c in merged.columns if c.startswith("ACT_BND~")]
    merged = merged[["TechName", "Comm-OUT", "Island", "COST~2023"] + year_cols]
    merged = merged.rename(columns={"Island": "Region"})

    logger.info("Created biofuel supply forecasts with %d rows.", len(merged))
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
