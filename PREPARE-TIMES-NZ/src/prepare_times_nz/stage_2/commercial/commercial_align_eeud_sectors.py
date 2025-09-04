"""
Align EEUD sectors for the TIMES-NZ commercial base-year dataset.

Pipeline:
1) Filter EEUD to Commercial and convert TJ -> PJ
2) Map EEUD sectors to TIMES sectors
3) Fill fully-missing tech/end-use rows using split tables
4) Apply lighting splits (Incandescent/Fluorescent/LED)
5) Checks and base-year output

Notes:
- Data centre demand is yet to be allocated.
- Outputs:
  - Preprocessing CSVs: <STAGE_2_DATA>/commercial/preprocessing
  - Checks/diagnostics: <STAGE_2_DATA>/commercial/checks/1_sector_alignment
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    DATA_RAW,
    STAGE_1_DATA,
    STAGE_2_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

# ----------------------------------------------------------------------------
# Configuration & constants
# ----------------------------------------------------------------------------
BASE_YEAR = 2023
group_cols = [
    "SectorGroup",
    "Sector",
    "SectorAnzsic",
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

# Be tolerant of Windows-encoded source CSVs
READ_OPTS = dict(encoding="cp1252", encoding_errors="replace")
MISSING_TOKENS = {"", "NA", "N/A", "NONE", "NULL", "UNKNOWN"}

# Locations
OUTPUT_LOCATION = Path(STAGE_2_DATA) / "commercial" / "preprocessing"
CHECKS_LOCATION = Path(STAGE_2_DATA) / "commercial" / "checks" / "1_sector_alignment"
CONCORDANCES = Path(DATA_RAW) / "concordances" / "commercial"
COMMERCIAL_ASSUMPTIONS = Path(ASSUMPTIONS) / "commercial_demand"

OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
CHECKS_LOCATION.mkdir(parents=True, exist_ok=True)

# Filenames (tweak if your repo uses different names)
EEUD_CSV = Path(STAGE_1_DATA) / "eeud" / "eeud.csv"
TIMES_EEUD_CATS = CONCORDANCES / "times_eeud_commercial_categories.csv"
SPLITS_FILE = (
    COMMERCIAL_ASSUMPTIONS / "fuel_splits_by_sector_enduse.csv"
)  # Sector, Fuel, Enduse, Share
LIGHT_SPLITS_FILE = COMMERCIAL_ASSUMPTIONS / "light_splits.csv"

# Output names
OUT_BASEYEAR = "1_times_eeud_alignment_baseyear.csv"
OUT_TIMESERIES_CHECK = "times_eeud_alignment_timeseries.csv"
OUT_DEFAULT_USES_CHECK = "default_fuel_uses.csv"


# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------


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
    return s.isna() | s.astype(str).str.strip().str.upper().isin(MISSING_TOKENS)


# ----------------------------------------------------------------------------
# I/O helpers
# ----------------------------------------------------------------------------
def save_output(df: pd.DataFrame, name: str) -> None:
    """Save DataFrame to the preprocessing output directory."""
    fp = OUTPUT_LOCATION / name
    logger.info("Saving output → %s", blue_text(fp))
    df.to_csv(fp, index=False)


def save_checks(df: pd.DataFrame, name: str, label: str) -> None:
    """Save diagnostic/check tables."""
    fp = CHECKS_LOCATION / name
    logger.info("Saving check (%s) → %s", label, blue_text(fp))
    df.to_csv(fp, index=False)


# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
def load_data() -> dict[str, pd.DataFrame | dict]:
    """Load inputs needed for commercial sector alignment."""
    data = {
        "eeud": pd.read_csv(EEUD_CSV, **READ_OPTS),
        "times_eeud_commercial_categories": pd.read_csv(TIMES_EEUD_CATS, **READ_OPTS),
    }
    return data


def _load_splits() -> pd.DataFrame:
    """
    Load the splits file and return a cleaned DataFrame with standardized column names.
    Handles BOM and validates required columns.
    """
    if not SPLITS_FILE.exists():
        raise FileNotFoundError(f"Splits file not found: {SPLITS_FILE}")

    splits = pd.read_csv(
        SPLITS_FILE,
        encoding="utf-8-sig",
        **{k: v for k, v in READ_OPTS.items() if k != "encoding"},
    )
    column_map = {_norm_header(col): col for col in splits.columns}

    required_columns = {"sector": None, "fuel": None, "share": None}
    optional_columns = {
        "enduse": None,
        "endusegroup": None,
        "technologygroup": None,
        "technology": None,
    }

    for key in required_columns:
        if key in column_map:
            required_columns[key] = column_map[key]

    for key in optional_columns:
        if key in column_map:
            optional_columns[key] = column_map[key]

    missing_columns = [key for key, value in required_columns.items() if value is None]
    if missing_columns:
        raise KeyError(
            f"Splits file missing required columns {missing_columns}. "
            f"Found: {list(splits.columns)}  File: {SPLITS_FILE}"
        )

    selected_columns = [
        required_columns["sector"],
        required_columns["fuel"],
        required_columns["share"],
    ]
    for key, value in optional_columns.items():
        if value:
            selected_columns.append(value)

    splits = splits[selected_columns].rename(
        columns={
            required_columns["sector"]: "Sector",
            required_columns["fuel"]: "Fuel",
            required_columns["share"]: "Share",
            optional_columns.get("enduse"): "EnduseSplit",
            optional_columns.get("endusegroup"): "EnduseGroupSplit",
            optional_columns.get("technologygroup"): "TechGroupSplit",
            optional_columns.get("technology"): "TechnologySplit",
        }
    )

    for col in [
        "Sector",
        "Fuel",
        "EnduseSplit",
        "EnduseGroup",
        "TechGroupSplit",
        "TechnologySplit",
    ]:
        if col in splits.columns:
            splits[col] = (
                splits[col]
                .astype(str)
                .str.replace("\ufeff", "", regex=False)
                .str.strip()
            )

    splits["Share"] = pd.to_numeric(splits["Share"], errors="coerce").fillna(0.0)
    return splits


def _load_light_splits() -> pd.DataFrame:
    """
    Load light_splits.csv and return normalized splits with shares summing to 1
    per (TechnologyGroup, EndUse, EnduseGroup, Fuel).
    Expected columns (case/spacing tolerant):
        TechnologyGroup, Technology, Fuel, Enduse, EnduseGroup, Share
    """
    if not LIGHT_SPLITS_FILE.exists():
        logger.info(
            "Lights split file not found → %s (skipping)", blue_text(LIGHT_SPLITS_FILE)
        )
        return pd.DataFrame()

    ls = pd.read_csv(
        LIGHT_SPLITS_FILE,
        encoding="utf-8-sig",
        **{k: v for k, v in READ_OPTS.items() if k != "encoding"},
    )

    cmap = {_norm_header(c): c for c in ls.columns}
    required = [
        "technologygroup",
        "technology",
        "fuel",
        "enduse",
        "endusegroup",
        "share",
    ]
    missing = [r for r in required if r not in cmap]
    if missing:
        raise KeyError(
            f"light_splits.csv missing columns {missing}. Found: {list(ls.columns)}  File: {LIGHT_SPLITS_FILE}"
        )

    ls = ls[
        [
            cmap["technologygroup"],
            cmap["technology"],
            cmap["fuel"],
            cmap["enduse"],
            cmap["endusegroup"],
            cmap["share"],
        ]
    ].rename(
        columns={
            cmap["technologygroup"]: "TechnologyGroup",
            cmap["technology"]: "TechnologyNew",
            cmap["fuel"]: "Fuel",
            cmap["enduse"]: "EndUse",
            cmap["endusegroup"]: "EnduseGroup",
            cmap["share"]: "Share",
        }
    )

    for col in ["TechnologyGroup", "TechnologyNew", "Fuel", "EndUse", "EnduseGroup"]:
        ls[col] = ls[col].astype(str).str.replace("\ufeff", "", regex=False).str.strip()
    ls["Share"] = pd.to_numeric(ls["Share"], errors="coerce").fillna(0.0)

    key = ["TechnologyGroup", "EndUse", "EnduseGroup", "Fuel"]
    ls["__sum"] = ls.groupby(key)["Share"].transform("sum")
    ls = ls[ls["__sum"] > 0].copy()
    ls["Share"] = ls["Share"] / ls["__sum"]
    ls = ls.drop(columns="__sum")

    return ls


# ----------------------------------------------------------------------------
# Transform helpers (commercial-focused)
# ----------------------------------------------------------------------------
def get_commercial_pj(df: pd.DataFrame) -> pd.DataFrame:
    """Filter EEUD to the commercial sector and convert Value to PJ (from TJ)."""
    df = df[df["SectorGroup"] == "Commercial"].copy()
    df["Unit"] = "PJ"
    df["Value"] = df["Value"] / 1e3  # TJ → PJ
    return df


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
    df[group_cols] = df[group_cols].fillna("NA")
    df = df.groupby(group_cols, as_index=False)[["Value"]].sum()
    return df


def split_na_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Split rows with NULL TechnologyGroup/Technology/EndUse/EnduseGroup
    using shares from the splits file (primarily keyed by Fuel).
    If Sector is missing on the row, take Sector from the split; otherwise keep it.
    """
    required_columns = [
        "Year",
        "Sector",
        "TechnologyGroup",
        "Technology",
        "EndUse",
        "EnduseGroup",
        "Fuel",
        "Unit",
        "Value",
    ]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise KeyError(f"Missing columns in working DataFrame: {missing}")

    for col in [
        "Sector",
        "Fuel",
        "EndUse",
        "EnduseGroup",
        "Technology",
        "TechnologyGroup",
    ]:
        df[col] = df[col].astype(str).str.replace("\ufeff", "", regex=False).str.strip()
        df.loc[is_missing_series(df[col]), col] = pd.NA

    to_split = (
        is_missing_series(df["TechnologyGroup"])
        & is_missing_series(df["Technology"])
        & is_missing_series(df["EndUse"])
        & is_missing_series(df["EnduseGroup"])
    )

    if not to_split.any():
        return df

    na_rows = (
        df[to_split].copy().reset_index(drop=False).rename(columns={"index": "_row"})
    )
    keep_rows = df[~to_split].copy()

    splits = _load_splits()
    if splits.empty:
        logger.warning("Splits file is empty: %s", SPLITS_FILE)
        return df

    merged = na_rows.merge(splits, on="Fuel", how="left", suffixes=("", "_split"))

    known_sector = ~is_missing_series(merged["Sector"])
    merged = merged[~known_sector | (merged["Sector"] == merged.get("Sector_split"))]

    merged["Share"] = pd.to_numeric(merged["Share"], errors="coerce").fillna(0.0)
    merged["__sum"] = merged.groupby("_row")["Share"].transform("sum")
    merged = merged[merged["__sum"] > 0]
    merged["Share"] = merged["Share"] / merged["__sum"]

    col_map = [
        ("EnduseSplit", "EndUse"),
        ("EnduseGroupSplit", "EnduseGroup"),
        ("TechGroupSplit", "TechnologyGroup"),
        ("TechnologySplit", "Technology"),
    ]
    for src, dst in col_map:
        if src in merged.columns:
            need = is_missing_series(merged[dst])
            merged.loc[need, dst] = merged.loc[need, src]

    if "Sector_split" in merged.columns:
        need = is_missing_series(merged["Sector"])
        merged.loc[need, "Sector"] = merged.loc[need, "Sector_split"]

    merged["Value"] = merged["Value"] * merged["Share"]

    wanted_cols = keep_rows.columns.tolist()
    merged = merged[wanted_cols]

    group_cols = [c for c in wanted_cols if c != "Value"]
    out = (
        pd.concat([keep_rows, merged], ignore_index=True)
        .groupby(group_cols, as_index=False)["Value"]
        .sum()
    )
    return out


def apply_light_splits(
    df: pd.DataFrame, *, base_technology: str = "Lights"
) -> pd.DataFrame:
    """
    Split rows where Technology == base_technology into specific lighting techs
    using light_splits.csv. Match on (TechnologyGroup, EndUse, EnduseGroup, Fuel).
    Applies across all sectors (add Sector to the key if you want sector-specific splits).
    """
    ls = _load_light_splits()
    if ls.empty:
        return df

    key = ["TechnologyGroup", "EndUse", "EnduseGroup", "Fuel"]

    mask = df["Technology"].astype(str).str.strip().eq(base_technology)
    if not mask.any():
        logger.info("No '%s' rows to split; skipping lights split", base_technology)
        return df

    to_split = df[mask].merge(ls[key + ["TechnologyNew", "Share"]], on=key, how="left")

    if to_split["Share"].isna().all():
        logger.warning("Lights split file loaded but no key matches found; skipping.")
        return df

    to_split = to_split[to_split["Share"].notna()].copy()

    to_split["Value"] = to_split["Value"] * to_split["Share"]
    to_split["Technology"] = to_split["TechnologyNew"]
    to_split = to_split.drop(columns=["TechnologyNew", "Share"])

    keep = df[~mask].copy()

    group_cols = [c for c in df.columns if c != "Value"]
    out = (
        pd.concat([keep, to_split], ignore_index=True)
        .groupby(group_cols, as_index=False)["Value"]
        .sum()
    )

    chk = (
        out[out["Technology"].str.startswith("Lights", na=False)]
        .groupby(
            ["TechnologyGroup", "Technology", "Fuel", "EndUse", "EnduseGroup"],
            as_index=False,
        )["Value"]
        .sum()
    )
    save_checks(chk, "lighting_split_totals.csv", "post-split lighting totals")

    return out


def filter_output_to_base_year(df: pd.DataFrame) -> pd.DataFrame:
    """Filter the DataFrame to the base year without dropping the Year column."""
    return df[df["Year"] == BASE_YEAR].copy()


def check_sector_demand_shares(df: pd.DataFrame, year: int = BASE_YEAR) -> None:
    """Write a quick check of commercial demand shares by sector."""
    tmp = (
        df[df["EndUse"] != "Feedstock"].copy() if "EndUse" in df.columns else df.copy()
    )
    tmp = tmp[tmp["Year"] == year]
    tmp = tmp.groupby(["Sector"], as_index=False)[["Value"]].sum()
    tmp["Total Demand"] = tmp["Value"].sum()
    tmp["Share of Commercial demand"] = tmp["Value"] / tmp["Value"].sum()
    save_checks(
        tmp, f"commercial_demand_shares_{year}.csv", f"commercial demand shares {year}"
    )


# ----------------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------------
def main() -> None:
    """Run the commercial EEUD sector alignment pipeline."""
    logger.info("Loading inputs…")
    data = load_data()

    logger.info("Filtering EEUD to Commercial and converting to PJ…")
    df = get_commercial_pj(data["eeud"])

    logger.info("Mapping EEUD sectors to TIMES sectors (commercial)…")
    df = add_times_categories(df, data["times_eeud_commercial_categories"])

    logger.info("Aggregating EEUD data…")
    df = aggregate_eeud(df)

    logger.info("Splitting fully-NA tech/enduse rows using sector×enduse shares…")
    df = split_na_rows(df)

    logger.info("Applying lighting technology splits (Incandescent/Fluorescent/LED)…")
    df = apply_light_splits(df, base_technology="Lights")

    logger.info("Writing checks (shares by sector)…")
    check_sector_demand_shares(df, year=BASE_YEAR)

    logger.info("Saving time-series alignment check…")
    save_checks(df, OUT_TIMESERIES_CHECK, "full EEUD timeseries (commercial)")

    logger.info("Filtering to base year and saving preprocessing output…")
    df_baseyear = filter_output_to_base_year(df)
    print("Final DataFrame columns:", df_baseyear.columns)
    save_output(df_baseyear, OUT_BASEYEAR)

    logger.info("Done.")


if __name__ == "__main__":
    main()
