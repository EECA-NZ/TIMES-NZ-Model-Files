"""Shared text cleaning, category mapping and aggregation for EEUD alignment."""

import pandas as pd

GROUP_COLS = [
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
    "Year",
    "Unit",
]

MISSING_TOKENS = {"", "NA", "N/A", "NONE", "NULL", "UNKNOWN"}


def _norm_header(header: str) -> str:
    """
    Normalize column headers by removing BOM, converting to lowercase,
    and replacing special characters with spaces.
    """
    return " ".join(
        header.replace("\ufeff", "")
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .split()
    )


def is_missing_series(s: pd.Series) -> pd.Series:
    """Identify nulls and case-insensitive missing tokens, ignoring whitespace."""
    return s.isna() | s.astype(str).str.strip().str.upper().isin(MISSING_TOKENS)


def add_times_categories(df: pd.DataFrame, times_map: pd.DataFrame) -> pd.DataFrame:
    """Map EEUD sectors to TIMES sectors using the provided category definitions."""
    cat = times_map.rename(columns={"EEUD": "Sector", "TIMES": "TIMES_Sector"})[
        ["Sector", "TIMES_Sector"]
    ]
    out = df.merge(cat, on="Sector", how="left")
    out["Sector"] = out["TIMES_Sector"].fillna(out["Sector"])
    out = out.drop(columns=["TIMES_Sector"])
    return out


def aggregate_eeud(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate EEUD data by relevant categories."""
    df[GROUP_COLS] = df[GROUP_COLS].fillna("NA")
    df = df.groupby(GROUP_COLS, as_index=False)[["Value"]].sum()
    return df
