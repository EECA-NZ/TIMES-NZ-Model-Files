"""Shared island reshaping and regional-share diagnostics."""

import re

import pandas as pd

from prepare_times_nz.utilities.logger_setup import logger

ROUND_TOL = 8  # round NI/SI for FP stability


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


def create_fuel_sector_checks(df_long: pd.DataFrame) -> pd.DataFrame:
    """Create a diagnostic table to review the resulting regional demand split.

    Sum demand across technologies and end uses for each sector and fuel, then
    return Sector, Fuel and NI_Share (NI demand divided by NI + SI demand).
    Zero totals produce a share of zero. Callers save this table for inspection;
    this function does not validate the shares or write files.
    """
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
    return shares


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


def _attach_detailed_sector_defaults(
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


def _attach_sector_defaults(
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


def _attach_fuel_overrides(
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


def calculate_generic_regional_splits(
    baseyear: pd.DataFrame,
    sector_splits: pd.DataFrame,
    fuel_overrides: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Split base-year demand into NI/SI rows without loading or saving files.

    Without fuel_overrides, match defaults by sector/fuel/technology, then
    sector/fuel, sector/technology, and finally sector alone. With an override
    table, use sector defaults and prefer matching fuel overrides.
    Retain existing validation, rounding,
    units and output column order, and remove explicit zero-demand rows.
    """
    if fuel_overrides is None:
        df = _attach_detailed_sector_defaults(baseyear, sector_splits)
    else:
        df = _attach_sector_defaults(baseyear, sector_splits)
        df = _attach_fuel_overrides(df, fuel_overrides)
        df["NIShareSector"] = df["NIShareOverride"].where(
            df["NIShareOverride"].notna(), df["NIShareSector"]
        )
    return tidy_long_island(compute_island_values(df))
