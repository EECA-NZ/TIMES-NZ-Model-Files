"""
Commercial demand — Islandal (NI/SI) disaggregation using THREE inputs:

1) STAGE_2_DATA/commercial/preprocessing/1_times_eeud_alignment_baseyear.csv
   Required cols: Sector, Fuel, Unit, Value, [TechnologyGroup],
   [Technology], [EndUse], [EnduseGroup]

2) ASSUMPTIONS/commercial_demand/Islandal_splits_by_sector.csv
   Required cols: Sector, NI_Share   (sector default NI share in [0,1])

3) ASSUMPTIONS/commercial_demand/Islandal_splits_by_fuel.csv
   Required cols: Fuel, NI_Share     (override in [0,1])
   Optional:     Sector              (if present, overrides apply to (Sector, Fuel), else Fuel-only)

Rules:
- Prefer fuel override when present (e.g., Natural Gas / Geothermal = 1.0 → all NI).
- Otherwise use the sector default.
- NI = Value * NIShare ;  SI = Value - NI
- Output: long table with Island ∈ {NI, SI}

Outputs:
- STAGE_2_DATA/commercial/preprocessing/2_times_baseyear_Islandal_disaggregation.csv
- STAGE_2_DATA/commercial/checks/2_Island_disaggregation/fuel_sector_shares.csv
"""

from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_2_DATA
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# -----------------------------------------------------------------------------
# Locations
# -----------------------------------------------------------------------------
OUTPUT_DIR = Path(STAGE_2_DATA) / "commercial" / "preprocessing"
CHECKS_DIR = Path(STAGE_2_DATA) / "commercial" / "checks" / "2_Island_disaggregation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKS_DIR.mkdir(parents=True, exist_ok=True)

BASEYEAR_CSV = OUTPUT_DIR / "1_times_eeud_alignment_baseyear.csv"
SECTOR_SPLITS_CSV = (
    Path(ASSUMPTIONS) / "commercial_demand" / "regional_splits_by_sector.csv"
)
FUEL_OVERRIDES_CSV = (
    Path(ASSUMPTIONS) / "commercial_demand" / "regional_splits_by_fuel.csv"
)

ROUND_TOL = 8  # round NI/SI for FP stability


# -----------------------------------------------------------------------------
# Load inputs
# -----------------------------------------------------------------------------
def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data"""
    baseyear = pd.read_csv(BASEYEAR_CSV)
    sector = pd.read_csv(SECTOR_SPLITS_CSV)
    fuel = pd.read_csv(FUEL_OVERRIDES_CSV)
    return baseyear, sector, fuel


# -----------------------------------------------------------------------------
# Core helpers
# -----------------------------------------------------------------------------
def attach_sector_defaults(
    df: pd.DataFrame, sector_splits: pd.DataFrame
) -> pd.DataFrame:
    """Add NIShareSector (default NI share by Sector)."""
    req = {"Sector", "NI_Share"}
    missing = req - set(sector_splits.columns)
    if missing:
        raise KeyError(f"Sector splits file missing columns: {missing}")
    sector = sector_splits[["Sector", "NI_Share"]].rename(
        columns={"NI_Share": "NIShareSector"}
    )
    out = df.merge(sector, on="Sector", how="left")
    missing_sectors = out.loc[out["NIShareSector"].isna(), "Sector"].dropna().unique()
    if len(missing_sectors):
        logger.warning(
            "No sector default NI share for: %s", ", ".join(map(str, missing_sectors))
        )
    return out


def attach_fuel_overrides(
    df: pd.DataFrame, fuel_overrides: pd.DataFrame
) -> pd.DataFrame:
    """
    Add NIShareOverride from fuel overrides.
    If overrides has 'Sector', match on (Sector, Fuel); else match on Fuel only.
    """
    req = {"Fuel", "NI_Share"}
    if not req.issubset(fuel_overrides.columns):
        raise KeyError(
            "Fuel overrides file must have columns: Fuel, NI_Share [optional Sector]"
        )

    if "Sector" in fuel_overrides.columns:
        ov = fuel_overrides[["Sector", "Fuel", "NI_Share"]].rename(
            columns={"NI_Share": "NIShareOverride"}
        )
        keys = ["Sector", "Fuel"]
    else:
        ov = fuel_overrides[["Fuel", "NI_Share"]].rename(
            columns={"NI_Share": "NIShareOverride"}
        )
        keys = ["Fuel"]

    out = df.merge(ov, on=keys, how="left")

    # Log which fuels got overridden (useful to confirm NG/Geothermal = 1.0 NI)
    overridden = out.loc[
        out["NIShareOverride"].notna(), ["Sector", "Fuel", "NIShareOverride"]
    ]
    if not overridden.empty:
        ex = ", ".join(sorted(set(overridden["Fuel"].astype(str))))
        logger.info("Applied fuel overrides for fuels: %s", ex)
    else:
        logger.info("No fuel overrides matched any rows.")

    return out


def compute_island_values(df: pd.DataFrame) -> pd.DataFrame:
    """Prefer override when present; else sector default. Compute NI and SI."""
    df = df.copy()
    df["NIShare"] = df["NIShareOverride"].where(
        df["NIShareOverride"].notna(), df["NIShareSector"]
    )
    df["NIShare"] = pd.to_numeric(df["NIShare"], errors="coerce").clip(lower=0, upper=1)

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
        columns=["NIShareSector", "NIShareOverride", "NIShare"],
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
    """Apply sector splits and fuel overrides"""
    baseyear, sector_splits, fuel_overrides = load_inputs()
    logger.info(
        "Loaded inputs: %s rows base-year, %s sector splits, %s fuel overrides",
        len(baseyear),
        len(sector_splits),
        len(fuel_overrides),
    )

    df = (
        baseyear.pipe(attach_sector_defaults, sector_splits=sector_splits)
        .pipe(attach_fuel_overrides, fuel_overrides=fuel_overrides)
        .pipe(compute_island_values)
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
