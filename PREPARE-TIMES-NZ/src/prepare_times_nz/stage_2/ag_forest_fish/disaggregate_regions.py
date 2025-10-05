"""
Ag, forest, and fish demand — Islandal (NI/SI) disaggregation using THREE inputs:

1) STAGE_2_DATA/ag_forest_fish/preprocessing/1_times_eeud_alignment_baseyear.csv
   Required cols: Sector, Fuel, Unit, Value, [TechnologyGroup],
   [Technology], [EndUse], [EnduseGroup]

2) ASSUMPTIONS/ag_forest_fish_demand/regional_splits.csv
   Required cols: Sector, Fuel, Technology, NI_Share   (sector default NI share in [0,1])

Outputs:
- STAGE_2_DATA/ag_forest_fish/preprocessing/2_times_baseyear_regional_disaggregation.csv
- STAGE_2_DATA/ag_forest_fish/checks/2_Regional_disaggregation/fuel_sector_shares.csv
"""

import re
from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# -----------------------------------------------------------------------------
# Locations
# -----------------------------------------------------------------------------
OUTPUT_DIR = Path(STAGE_2_DATA) / "ag_forest_fish" / "preprocessing"
CHECKS_DIR = (
    Path(STAGE_2_DATA) / "ag_forest_fish" / "checks" / "2_Regional_disaggregation"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKS_DIR.mkdir(parents=True, exist_ok=True)

BASEYEAR_CSV = OUTPUT_DIR / "1_times_eeud_alignment_baseyear.csv"
SPLITS_CSV = Path(ASSUMPTIONS) / "ag_forest_fish_demand" / "regional_splits.csv"

ROUND_TOL = 8  # round NI/SI for FP stability


# -----------------------------------------------------------------------------
# Load inputs
# -----------------------------------------------------------------------------
def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data"""
    baseyear = pd.read_csv(BASEYEAR_CSV)
    sector = pd.read_csv(SPLITS_CSV)
    return baseyear, sector


# -----------------------------------------------------------------------------
# Core helpers
# -----------------------------------------------------------------------------
def _clean_text_col(s: pd.Series) -> pd.Series:
    """Strip normal & non-breaking spaces; empty → NA; keep as pandas StringDtype."""
    s = s.astype("string")
    # Replace NBSP and other unicode spaces with normal space, then strip
    s = s.str.replace(r"\s+", " ", regex=True).str.replace("\u00a0", " ", regex=False)
    s = s.str.strip()
    return s.replace({"": pd.NA})


def _warn_dupes_layer(df_layer: pd.DataFrame, keys: list[str], label: str):
    dup = (
        df_layer.groupby(keys)["NI_Share"]
        .nunique(dropna=True)
        .reset_index(name="n_unique")
    )
    bad = dup[dup["n_unique"] > 1]
    if not bad.empty:
        logger.warning(
            "Conflicting NI_Share within %s for keys %s on %d groups; first value will be used.",
            label,
            keys,
            len(bad),
        )


def normalize_sector_splits(sector_splits: pd.DataFrame) -> pd.DataFrame:
    """Fix header whitespace, coerce empties to NaN, parse NI_Share to [0,1], dedupe per layer."""
    ss = sector_splits.copy()

    # Normalize column names (strip, squash whitespace, fix NBSP) and standardize keys
    def _norm_col(c: str) -> str:
        c = c.replace("\u00a0", " ")  # NBSP → space
        c = re.sub(r"\s+", " ", c).strip()  # collapse spaces
        return c

    ss.columns = [_norm_col(c) for c in ss.columns]

    rename_map = {}
    for c in ss.columns:
        low = c.lower()
        if low == "technology":
            rename_map[c] = "Technology"
        if low == "ni_share":
            rename_map[c] = "NI_Share"
        if low == "sector":
            rename_map[c] = "Sector"
        if low == "fuel":
            rename_map[c] = "Fuel"
    if rename_map:
        ss = ss.rename(columns=rename_map)

    req = {"Sector", "Fuel", "Technology", "NI_Share"}
    missing = req - set(ss.columns)
    if missing:
        raise KeyError(f"Splits file missing columns: {missing}")

    # Clean text columns
    ss["Sector"] = _clean_text_col(ss["Sector"])
    ss["Fuel"] = _clean_text_col(ss["Fuel"])
    ss["Technology"] = _clean_text_col(ss["Technology"])

    # Build layers
    exact = ss.dropna(subset=["Fuel", "Technology"])
    fuel_only = ss[ss["Fuel"].notna() & ss["Technology"].isna()]
    tech_only = ss[ss["Fuel"].isna() & ss["Technology"].notna()]
    sector_only = ss[ss["Fuel"].isna() & ss["Technology"].isna()]

    # Layer-aware conflict warnings
    _warn_dupes_layer(exact, ["Sector", "Fuel", "Technology"], "EXACT layer")
    _warn_dupes_layer(fuel_only, ["Sector", "Fuel"], "FUEL-ONLY layer")
    _warn_dupes_layer(tech_only, ["Sector", "Technology"], "TECH-ONLY layer")
    _warn_dupes_layer(sector_only, ["Sector"], "SECTOR-ONLY layer")

    # Deduplicate within each layer
    exact = exact.drop_duplicates(["Sector", "Fuel", "Technology"], keep="first")
    fuel_only = fuel_only.drop_duplicates(["Sector", "Fuel"], keep="first")
    tech_only = tech_only.drop_duplicates(["Sector", "Technology"], keep="first")
    sector_only = sector_only.drop_duplicates(["Sector"], keep="first")

    # Recombine
    ss = pd.concat([exact, fuel_only, tech_only, sector_only], ignore_index=True)
    return ss


def attach_sector_defaults(
    df: pd.DataFrame, sector_splits: pd.DataFrame
) -> pd.DataFrame:
    """
    Add NIShareSector by matching with a specificity hierarchy:
      1) Sector + Fuel + Technology
      2) Sector + Fuel           (split Technology is NaN)
      3) Sector + Technology     (split Fuel is NaN)
      4) Sector                  (split Fuel & Technology are NaN)
    """
    ss = normalize_sector_splits(sector_splits)

    exact = ss.dropna(subset=["Fuel", "Technology"])[
        ["Sector", "Fuel", "Technology", "NI_Share"]
    ].rename(columns={"NI_Share": "NIShare_exact"})

    fuel_only = ss[ss["Fuel"].notna() & ss["Technology"].isna()][
        ["Sector", "Fuel", "NI_Share"]
    ].rename(columns={"NI_Share": "NIShare_fuel"})

    tech_only = ss[ss["Fuel"].isna() & ss["Technology"].notna()][
        ["Sector", "Technology", "NI_Share"]
    ].rename(columns={"NI_Share": "NIShare_tech"})

    sector_only = ss[ss["Fuel"].isna() & ss["Technology"].isna()][
        ["Sector", "NI_Share"]
    ].rename(columns={"NI_Share": "NIShare_sector"})

    out = df.copy()

    # Clean df’s match columns the same way so NaNs align
    for col in ["Sector", "Fuel", "Technology"]:
        if col in out.columns:
            out[col] = _clean_text_col(out[col])

    out = out.merge(exact, on=["Sector", "Fuel", "Technology"], how="left")
    out = out.merge(fuel_only, on=["Sector", "Fuel"], how="left")
    out = out.merge(tech_only, on=["Sector", "Technology"], how="left")
    out = out.merge(sector_only, on="Sector", how="left")

    out["NIShareSector"] = (
        out["NIShare_exact"]
        .combine_first(out["NIShare_fuel"])
        .combine_first(out["NIShare_tech"])
        .combine_first(out["NIShare_sector"])
    ).astype(float)

    out.drop(
        columns=["NIShare_exact", "NIShare_fuel", "NIShare_tech", "NIShare_sector"],
        inplace=True,
    )

    # Final sanity
    out["NIShareSector"] = pd.to_numeric(out["NIShareSector"], errors="coerce").clip(
        0, 1
    )

    # Warnings for anything still missing
    missing_rows = out["NIShareSector"].isna()
    if missing_rows.any():
        miss = out.loc[missing_rows, ["Sector", "Fuel", "Technology"]].drop_duplicates()
        logger.warning(
            "No NI share found after all fallbacks for: %s",
            "; ".join(miss.astype(str).agg(",".join, axis=1).tolist()),
        )

    return out


def compute_island_values(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the values for each Island"""
    df = df.copy()
    df["NIShare"] = pd.to_numeric(df["NIShareSector"], errors="coerce").clip(0, 1)
    df["NI"] = (df["Value"] * df["NIShare"]).round(ROUND_TOL)
    df["SI"] = (df["Value"] - df["NI"]).round(ROUND_TOL).abs()
    return df


def tidy_long_island(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return tidy long table with Island ∈ {NI, SI}.
    Drops helper columns and the original total 'Value' to avoid melt collision.
    """
    df = df.copy()
    df.drop(
        columns=["NIShareSector", "NIShare"],
        inplace=True,
        errors="ignore",
    )
    df.drop(columns=["Value"], inplace=True, errors="ignore")  # avoid value_name clash

    id_cols = [c for c in df.columns if c not in {"NI", "SI"}]
    df_long = df.melt(
        id_vars=id_cols,
        value_vars=["NI", "SI"],
        var_name="Island",
        value_name="Value",
    )
    # Remove explicit zeros (e.g., SI for 100% NI fuels)
    df_long = df_long[df_long["Value"] != 0]

    # Optional: consistent column order if present
    # pylint:disable = duplicate-code
    order = [
        "SectorGroup",
        "Sector",
        "SectorANZSIC",
        "FuelGroup",
        "Fuel",
        "TechnologyGroup",
        "Technology",
        "EnduseGroup",
        "EndUse",
        "Transport",
        "Island",
        "Year",
        "Unit",
        "Value",
    ]

    df_long = df_long[[c for c in order if c in df_long.columns]]
    return df_long


# --- saving helpers ---
def save_output(df: pd.DataFrame, name: str) -> None:
    """Save DataFrame to the preprocessing output directory."""
    fp = OUTPUT_DIR / name
    logger.info("Saving output → %s", blue_text(str(fp)))
    df.to_csv(fp, index=False)


def save_checks(df: pd.DataFrame, name: str, label: str) -> None:
    """Save diagnostic/check tables."""
    fp = CHECKS_DIR / name
    logger.info("Saving check (%s) → %s", label, blue_text(str(fp)))
    df.to_csv(fp, index=False)


def save_checks_pivot(df_long: pd.DataFrame) -> None:
    """Simple check: fuel-by-sector NI share matrix."""
    wide = df_long.pivot_table(
        index=["Sector", "Fuel"],
        columns="Island",
        values="Value",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    if "NI" not in wide.columns:
        wide["NI"] = 0.0
    total = wide.get("NI", 0) + wide.get("SI", 0)
    shares = wide[["Sector", "Fuel"]].copy()
    shares["NI_Share"] = (wide["NI"] / total).where(total != 0, 0)
    save_checks(shares, "fuel_sector_shares.csv", "fuel × sector NI shares")


# -----------------------------------------------------------------------------
# Orchestration
# -----------------------------------------------------------------------------
def calculate_and_save() -> pd.DataFrame:
    """
    Run the full regional disaggregation pipeline:
    - Load base-year & sector split data
    - Attach NI/SI shares
    - Compute island values and save outputs/checks
    """
    baseyear, sector_splits = load_inputs()

    logger.info(
        "Loaded inputs: %s rows base-year, %s sector splits",
        len(baseyear),
        len(sector_splits),
    )

    df = baseyear.pipe(attach_sector_defaults, sector_splits=sector_splits).pipe(
        compute_island_values
    )

    df_long = tidy_long_island(df)
    save_output(df_long, "2_times_baseyear_regional_disaggregation.csv")
    save_checks_pivot(df_long)

    logger.info("Regional disaggregation complete: %s rows", len(df_long))
    return df_long


# -----------------------------------------------------------------------------
# Script entry
# -----------------------------------------------------------------------------
def main() -> None:
    """Run the calculations and save outputs"""
    calculate_and_save()


if __name__ == "__main__":
    main()
