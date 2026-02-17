"""
Build the TIMES-NZ Biofuel & Biomass Process Declarations table and

Creates a combined DataFrame of all biomass/biofuel technologies grouped
by Set, TechName, and Units (Tact, Tcap).

Creates base-year supply forecasts for these technologies by Island,
joined with prices and recoverability factors.

Adds an additional supply forecast scenario using the
alternative recoverability factor and higher growth of AD feedstock.

Outputs:
  - <STAGE_4_DATA>/biofuels/biofuel_process_declarations.csv

"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

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
# Common biomass to TechName mapping (module-level constant)
# ----------------------------------------------------------------------------
BIOMASS_TO_TECH = {
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
    "wood processing residues": "MINWODSUPOSWOD",
    "sustainable aviation fuel": "IMPSAF",
}


# ----------------------------------------------------------------------------
# Constant supply overrides (module-level)
# ----------------------------------------------------------------------------
SUPPLY_CONSTANTS_ALL_YEARS: dict[str, dict[str, float]] = {
    # split based on population 77% NI, 23% SI
    "MINMNCWST01": {"NI": 3.877, "SI": 1.158},
    # split based on total pigs and DC numbers 56% NI, 44% SI
    "MINANMMNR00": {"NI": 4.234, "SI": 3.326},
}

SUPPLY_CONSTANTS_FROM_2026: dict[str, dict[str, float]] = {
    # split based on population 77% NI, 23% SI
    "MINOILWST00": {"NI": 0.180, "SI": 0.054},
    # 100% in SI
    "MINOILWST01": {"NI": 0.0, "SI": 6.240},
}


# ----------------------------------------------------------------------------
# Helpers: constants + final tidy
# ----------------------------------------------------------------------------
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def apply_supply_constants(
    df: pd.DataFrame,
    *,
    region_col: str,
    year_prefix: str = "ACT_BND~",
    upto_year: int = 2053,
    constants_all_years: Mapping[str, Mapping[str, float]] | None = None,
    constants_from_year: int | None = None,
    constants_from_year_map: Mapping[str, Mapping[str, float]] | None = None,
) -> pd.DataFrame:
    """Apply constant overrides into ACT_BND~YYYY columns and replace 0 with NA."""
    out = df.copy()
    year_cols = [c for c in out.columns if c.startswith(year_prefix)]
    year_cols_upto = [c for c in year_cols if int(c.split("~")[1]) <= upto_year]

    if constants_all_years:
        for tech, region_vals in constants_all_years.items():
            mask_tech = out["TechName"] == tech
            for region, val in region_vals.items():
                mask_region = out[region_col] == region
                out.loc[mask_tech & mask_region, year_cols_upto] = val

    if constants_from_year and constants_from_year_map:
        year_cols_from = [
            c
            for c in year_cols
            if constants_from_year <= int(c.split("~")[1]) <= upto_year
        ]
        for tech, region_vals in constants_from_year_map.items():
            mask_tech = out["TechName"] == tech
            for region, val in region_vals.items():
                mask_region = out[region_col] == region
                out.loc[mask_tech & mask_region, year_cols_from] = val

    # Replace remaining zeros only in ACT_BND columns
    if year_cols:
        out[year_cols] = out[year_cols].replace(0, pd.NA)

    return out


def finalise_supply_forecast(
    df: pd.DataFrame,
    *,
    island_col: str = "Island",
    out_cols: tuple[str, ...] = ("TechName", "Comm-OUT", "Region", "COST~2023"),
) -> pd.DataFrame:
    """Rename Island->Region and keep a consistent column order."""
    out = df.copy()
    year_cols = [c for c in out.columns if c.startswith("ACT_BND~")]

    if island_col in out.columns:
        out = out.rename(columns={island_col: "Region"})

    keep = [c for c in out_cols if c in out.columns] + year_cols
    return out[keep]


# ----------------------------------------------------------------------------
# Common helper for supply forecast DataFrame
# ----------------------------------------------------------------------------
def build_bioenergy_supply_forecast_df(
    recoverability_col: str,
    *,
    return_long_format: bool = False,
    apply_custom_filtering: bool = False,
) -> pd.DataFrame:
    """
    Common logic for creating bioenergy supply forecast DataFrame.

    Args:
        recoverability_col: Which recoverability factor column to use.
        return_long_format: If True, returns long-format table with Island.
        apply_custom_filtering: If True, apply ACT_BND year filtering by TechName.
    """
    prices_df = pd.read_csv(biomass_prices)
    supply_df = pd.read_csv(biomass_supply_pj)
    region_map = pd.read_csv(region_island_map)
    recoverability_df = pd.read_csv(recoverability)

    recoverability_df.columns = recoverability_df.columns.str.strip()

    supply_df["Value"] = supply_df["Value"].astype(float)

    # Map Region to Island
    supply_df = supply_df.merge(region_map, on="Region", how="left")

    # Aggregate supply (sum will stay NaN if all inputs were NaN)
    agg_supply = supply_df.groupby(["BiomassType", "Island", "Year"], as_index=False)[
        "Value"
    ].sum(min_count=1)

    # Map BiomassType to TechName
    biomass_to_tech = {k.lower(): v for k, v in BIOMASS_TO_TECH.items()}
    agg_supply["BiomassType"] = (
        agg_supply["BiomassType"].astype(str).str.strip().str.lower()
    )
    agg_supply["TechName"] = agg_supply["BiomassType"].map(biomass_to_tech)

    # Pivot WITHOUT fill_value so missing stays NaN
    pivot_supply = agg_supply.pivot_table(
        index=["TechName", "Island"],
        columns="Year",
        values="Value",
        aggfunc="sum",
        dropna=False,
    ).reset_index()

    # Rename columns to ACT_BND~YYYY
    pivot_supply.columns = [
        f"ACT_BND~{c}" if isinstance(c, int) else c for c in pivot_supply.columns
    ]

    # Merge with prices (outer, so price-only techs are retained)
    merged = pivot_supply.merge(prices_df, on="TechName", how="outer")

    # Ensure Island exists even if only from prices_df
    if "Island" not in merged.columns:
        merged["Island"] = pd.NA

    # Standardise price column name
    merged = merged.rename(columns={"Cost$perGJ": "COST~2023"})

    # Merge recoverability factors
    merged = merged.merge(recoverability_df, on="TechName", how="left")

    # Multiply all ACT_BND columns by the selected recoverability factor
    year_cols = [c for c in merged.columns if c.startswith("ACT_BND~")]
    for col in year_cols:
        merged[col] = merged[col] * merged[recoverability_col]

    # Drop recoverability columns if present (avoid leaking into output)
    merged = merged.drop(
        columns=[
            c
            for c in [
                "Recoverability factor 1 (% of gross)",
                "Recoverability factor 2 (% of gross)",
            ]
            if c in merged.columns
        ],
        errors="ignore",
    )

    # Duplicate missing-island techs across NI & SI
    missing_island = merged[merged["Island"].isna()].copy()
    if not missing_island.empty:
        ni_rows = missing_island.copy()
        ni_rows["Island"] = "NI"
        si_rows = missing_island.copy()
        si_rows["Island"] = "SI"

        merged = merged[merged["Island"].notna()]
        merged = pd.concat([merged, ni_rows, si_rows], ignore_index=True)

    # Keep only ACT_BND~2024 for some TechNames, ACT_BND~2026 for others
    if apply_custom_filtering:
        act_bnd_cols = [c for c in merged.columns if c.startswith("ACT_BND~")]
        keep_year_by_tech = {
            "MINMNCWST00": 2024,
            "MINMNCWST01": 2024,
            "MINAGRWST00": 2024,
            "MINAGRWST01": 2024,
            "MINANMMNR00": 2024,
            "MINOILWST00": 2026,
            "MINOILWST01": 2026,
        }

        for tech, keep_year in keep_year_by_tech.items():
            keep_col = f"ACT_BND~{keep_year}"
            drop_cols = [c for c in act_bnd_cols if c != keep_col]
            merged.loc[merged["TechName"] == tech, drop_cols] = pd.NA

    if return_long_format:
        act_bnd_cols = [c for c in merged.columns if c.startswith("ACT_BND~")]
        melted = merged.melt(
            id_vars=["TechName", "Island"],
            value_vars=act_bnd_cols,
            var_name="YearCol",
            value_name="ACT_BND",
        )
        melted["Year"] = (
            melted["YearCol"].str.extract(r"ACT_BND~(\d+)").astype(float).astype(int)
        )
        melted = melted.dropna(subset=["ACT_BND"])

        return melted[["TechName", "Island", "Year", "ACT_BND"]].sort_values(
            ["TechName", "Year", "Island"]
        )

    return merged


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
                "MINWODWST00",
                "MINWODWST01",
                "MINWODWST02",
                "MINWODWST03",
                "MINWODWST04",
                "MINWODWST05",
                "MINWODWST06",
                "MINWODWST07",
                "MINAGRWST00",
                "MINAGRWST01",
                "MINMNCWST00",
                "MINMNCWST01",
                "MINANMMNR00",
                "MINOILWST00",
                "MINOILWST01",
                "MINWODSUPCUR00",
                "MINWODSUPCUR01",
                "MINWODSUPCUR02",
                "MINWODSUPCUR03",
                "MINWODSUPOSWOD",
            ],
        },
        {
            "Sets": "IMP",
            "Tact": "PJ",
            "Tcap": "PJa",
            "TechName": [
                "IMPSAF",
            ],
        },
        # --- Refining / processing (PRE / PJ / GWth) ---
        {
            "Sets": "PRE",
            "Tact": "PJ",
            "Tcap": "GWth",
            "TechName": [
                "CT_CWODBPL",
                "CT_CWODETH",
                "CT_COILBDS",
                "CT_CWODDID",
            ],
        },
        # --- One processing tech with different capacity unit (PJa) ---
        {
            "Sets": "PRE",
            "Tact": "PJ",
            "Tcap": "PJa",
            "TechName": [
                "REF_ANDGST",
                "BIG2BIM",
                "WSTWOD2WOD",
            ],
        },
    ]

    records: list[dict[str, str]] = []
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

    return pd.DataFrame(records)


def create_biofuel_supply_forecasts() -> pd.DataFrame:
    """Create base-year biofuel supply forecasts joined with prices and island mapping."""
    base = build_bioenergy_supply_forecast_df(
        recoverability_col="Recoverability factor 2 (% of gross)",
        return_long_format=False,
        apply_custom_filtering=True,  # <- ONLY here
    )

    # Apply constant supply overrides using shared module-level dicts
    base = apply_supply_constants(
        base,
        region_col="Island",
        constants_all_years=SUPPLY_CONSTANTS_ALL_YEARS,
        constants_from_year=2026,
        constants_from_year_map=SUPPLY_CONSTANTS_FROM_2026,
    )

    # Final tidy for wide output
    return finalise_supply_forecast(base, island_col="Island")


# ----------------------------------------------------------------------------
# Additional bioenergy supply forecasts
# ----------------------------------------------------------------------------
def create_additional_bioenergy_supply_forecasts() -> pd.DataFrame:
    """
    Output:
        TechName | Year | NI | SI | Attribute
    """

    # Build wide first (so we can apply constants easily)
    wide_base = build_bioenergy_supply_forecast_df(
        recoverability_col="Recoverability factor 1 (% of gross)",
        return_long_format=False,
        apply_custom_filtering=False,
    )

    # Apply the same constants
    wide_base = apply_supply_constants(
        wide_base,
        region_col="Island",
        constants_all_years=SUPPLY_CONSTANTS_ALL_YEARS,
        constants_from_year=2026,
        constants_from_year_map=SUPPLY_CONSTANTS_FROM_2026,
    )

    # Convert to long (TechName, Island, Year, ACT_BND)
    act_bnd_cols = [c for c in wide_base.columns if c.startswith("ACT_BND~")]
    long_df = wide_base.melt(
        id_vars=["TechName", "Island"],
        value_vars=act_bnd_cols,
        var_name="YearCol",
        value_name="ACT_BND",
    )
    long_df["Year"] = long_df["YearCol"].str.extract(r"ACT_BND~(\d+)").astype(int)
    long_df = long_df.drop(columns=["YearCol"]).dropna(subset=["ACT_BND"])

    # Pivot to NI/SI columns
    out = long_df.pivot_table(
        index=["TechName", "Year"],
        columns="Island",
        values="ACT_BND",
        aggfunc="sum",
        dropna=False,
    ).reset_index()

    out.columns.name = None
    for region in ("NI", "SI"):
        if region not in out.columns:
            out[region] = pd.NA

    out["Attribute"] = "ACT_BND"
    return out[["TechName", "Year", "NI", "SI", "Attribute"]].sort_values(
        ["TechName", "Year"]
    )


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

    df_forecast = create_biofuel_supply_forecasts()
    logger.info("Constructed DataFrame with %d records.", len(df_forecast))
    logger.debug("Preview of data:\n%s", df_forecast.head())

    save_output(df_forecast, OUTPUT_DIR / "biofuel_supply_forecasts.csv")
    logger.info("Biofuel supply forecasts generation complete.")

    logger.info("Building TIMES-NZ Additional Bioenergy supply forecasts…")

    df_additional = create_additional_bioenergy_supply_forecasts()
    logger.info("Constructed DataFrame with %d records.", len(df_additional))
    logger.debug("Preview of data:\n%s", df_additional.head())

    save_output(df_additional, OUTPUT_DIR / "additional_bioenergy_supply_forecasts.csv")
    logger.info("Additional bioenergy supply forecasts generation complete.")


if __name__ == "__main__":
    main()
