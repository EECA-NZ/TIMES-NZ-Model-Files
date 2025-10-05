"""
Align EEUD sectors for the TIMES-NZ agriculture, forestry and fishing base-year dataset.

Pipeline:
1) Filter EEUD to ag, forest, and fish and convert TJ -> PJ
2) Map EEUD sectors to TIMES sectors and make other adjustments
3) Fill fully-missing tech/end-use rows using split tables
4) Apply diesel off-road vehicle splits (Ute/tractor/truck/cable yarding/ground based)
5) Checks and base-year output

- Outputs:
  - Preprocessing CSVs: <STAGE_2_DATA>/ag_forest_fish/preprocessing
  - Checks/diagnostics: <STAGE_2_DATA>/ag_forest_fish/checks/1_sector_alignment
"""

from __future__ import annotations

import re
from collections.abc import Iterable
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

# Be tolerant of Windows-encoded source CSVs
READ_OPTS = {"encoding": "cp1252", "encoding_errors": "replace"}
MISSING_TOKENS = {"", "NA", "N/A", "NONE", "NULL", "UNKNOWN"}

# Locations
OUTPUT_LOCATION = Path(STAGE_2_DATA) / "ag_forest_fish" / "preprocessing"
CHECKS_LOCATION = (
    Path(STAGE_2_DATA) / "ag_forest_fish" / "checks" / "1_sector_alignment"
)
AG_CONCORDANCES = Path(DATA_RAW) / "concordances" / "ag_forest_fish"
AG_ASSUMPTIONS = Path(ASSUMPTIONS) / "ag_forest_fish_demand"


OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)
CHECKS_LOCATION.mkdir(parents=True, exist_ok=True)

# Filenames (tweak if your repo uses different names)
EEUD_CSV = Path(STAGE_1_DATA) / "eeud" / "eeud.csv"
TIMES_EEUD_CATS = AG_CONCORDANCES / "times_eeud_categories.csv"
MBIE_ENERGY_BALANCE = (
    Path(DATA_RAW) / "external_data" / "mbie" / "energy-balance-tables.xlsx"
)
LIVESTOCK_HORTICULTURE_IRRIGATION = (
    AG_ASSUMPTIONS / "livestock_horticulture_irrigation_patch.xlsx"
)
TECHNOLOGY_SPLITS = AG_ASSUMPTIONS / "technology_splits.csv"

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
    """For missing tokens"""
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
    """Load inputs needed for ag_forest_fish sector alignment."""
    mbie_raw = pd.read_excel(
        MBIE_ENERGY_BALANCE,
        sheet_name="2023",
        header=[0, 1, 2, 3, 4],
        engine="openpyxl",
    )
    # Flatten multi-index columns to strings
    mbie_raw.columns = [
        " ".join(
            [
                str(x).strip()
                for x in col
                if str(x).strip() != "" and str(x).strip() != "nan"
            ]
        )
        for col in mbie_raw.columns
    ]
    data = {
        "eeud": pd.read_csv(EEUD_CSV),
        "times_eeud_categories": pd.read_csv(TIMES_EEUD_CATS),
        "mbie_energy_balance": mbie_raw,
        "livestock_horticulture_irrigation_patch": pd.read_excel(
            LIVESTOCK_HORTICULTURE_IRRIGATION,
            sheet_name="TIMES_INPUT",
            engine="openpyxl",
        ),
    }
    return data


def _load_technology_splits() -> pd.DataFrame:
    """
    Load technology_splits.csv and return normalized splits with shares summing to 1
    per (Sector, FuelGroup, Fuel, TechnologyGroup, EnduseGroup, EndUse)
    Expected columns (case/spacing tolerant):
        Sector, FuelGroup, Fuel, TechnologyGroup, Technology, EnduseGroup, EndUse, Share
    """

    ls = pd.read_csv(
        TECHNOLOGY_SPLITS,
        encoding="utf-8-sig",
        **{k: v for k, v in READ_OPTS.items() if k != "encoding"},
    )

    cmap = {_norm_header(c): c for c in ls.columns}
    required = [
        "sector",
        "fuelgroup",
        "fuel",
        "technologygroup",
        "technology",
        "endusegroup",
        "enduse",
        "share",
    ]
    missing = [r for r in required if r not in cmap]
    if missing:
        raise KeyError(
            f"technology_splits.csv missing columns {missing}. "
            f"Found: {list(ls.columns)} File: {TECHNOLOGY_SPLITS}"
        )

    ls = ls[
        [
            cmap["sector"],
            cmap["fuelgroup"],
            cmap["fuel"],
            cmap["technologygroup"],
            cmap["technology"],
            cmap["endusegroup"],
            cmap["enduse"],
            cmap["share"],
        ]
    ].rename(
        columns={
            cmap["sector"]: "Sector",
            cmap["fuelgroup"]: "FuelGroup",
            cmap["fuel"]: "Fuel",
            cmap["technologygroup"]: "TechnologyGroup",
            cmap["technology"]: "TechnologyNew",
            cmap["endusegroup"]: "EnduseGroup",
            cmap["enduse"]: "EndUse",
            cmap["share"]: "Share",
        }
    )

    for col in [
        "Sector",
        "FuelGroup",
        "Fuel",
        "TechnologyGroup",
        "TechnologyNew",
        "EnduseGroup",
        "EndUse",
    ]:
        ls[col] = ls[col].astype(str).str.replace("\ufeff", "", regex=False).str.strip()
    ls["Share"] = pd.to_numeric(ls["Share"], errors="coerce").fillna(0.0)

    key = ["Sector", "FuelGroup", "Fuel", "TechnologyGroup", "EnduseGroup", "EndUse"]
    ls["__sum"] = ls.groupby(key)["Share"].transform("sum")
    ls = ls[ls["__sum"] > 0].copy()
    ls["Share"] = ls["Share"] / ls["__sum"]
    ls = ls.drop(columns="__sum")

    return ls


# ----------------------------------------------------------------------------
# Transform helpers (commercial-focused)
# ----------------------------------------------------------------------------
def get_ag_forest_fish_pj(df: pd.DataFrame) -> pd.DataFrame:
    """Filter EEUD to the ag_forest_fish sector and convert Value to PJ (from TJ)."""
    df = df[df["SectorGroup"] == "Agriculture, Forestry and Fishing"].copy()
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


# --- keep your existing find_col as a token-based search, but simplify it:
def find_col(cols, *keywords):
    """Return the first column whose name contains all keywords (case-insensitive)."""

    def norm(x):
        return str(x).lower().strip()

    for col in cols:
        name = norm(col)
        if all(norm(k) in name for k in keywords):
            return col
    raise KeyError(f"No column found for keywords: {keywords}")


def _find_row_index_by_label(df: pd.DataFrame, label: str) -> int:
    """Find first row index where ANY column equals the label (case-insensitive, trimmed)."""
    mask = df.apply(lambda c: c.astype(str).str.strip().str.lower() == label.lower())
    idx = mask.any(axis=1)
    if not idx.any():
        raise KeyError(f"Row not found for label: {label}")
    return df.index[idx][0]


def mbie_ag_forest_fish_energy(mbie_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a tiny reconciliation table of PJ by selected fuels using MBIE energy balance.
    Prints values so you can verify they match expectations.
    """
    df = mbie_df.copy()

    # --- locate target rows robustly
    ag_idx = _find_row_index_by_label(df, "Agriculture")
    fish_idx = _find_row_index_by_label(df, "Fishing")

    agriculture_row = df.loc[ag_idx]
    fishing_row = df.loc[fish_idx]

    # --- locate columns robustly
    coal_col = find_col(df.columns, "coal", "total")
    ng_col = find_col(df.columns, "natural gas", "total")
    geo_col = find_col(df.columns, "renewables", "geothermal")
    diesel_col = find_col(df.columns, "oil", "diesel")

    # --- extract values
    agriculture_coal_value = agriculture_row[coal_col]
    agriculture_natural_gas_value = agriculture_row[ng_col]
    agriculture_geo_value = agriculture_row[geo_col]
    fishing_diesel_value = fishing_row[diesel_col]

    # --- build output (add Year so downstream checks don't error)
    reconcil_direct_df = pd.DataFrame(
        [
            {
                "Year": BASE_YEAR,
                "Sector": "Fishing, Hunting and Trapping",
                "Fuel": "Diesel",
                "Value": fishing_diesel_value,
            },
            {
                "Year": BASE_YEAR,
                "Sector": "Indoor Cropping",
                "Fuel": "Coal",
                "Value": agriculture_coal_value,
            },
            {
                "Year": BASE_YEAR,
                "Sector": "Indoor Cropping",
                "Fuel": "Natural Gas",
                "Value": agriculture_natural_gas_value,
            },
            {
                "Year": BASE_YEAR,
                "Sector": "Indoor Cropping",
                "Fuel": "Geothermal",
                "Value": agriculture_geo_value,
            },
        ]
    )

    return reconcil_direct_df


def apply_mbie_reconciliation(df: pd.DataFrame, recon: pd.DataFrame) -> pd.DataFrame:
    """
    Replace values in df with MBIE reconciliation values from recon DataFrame.
    Matches on Year, Sector, and Fuel.
    """
    df = df.copy()
    for _, row in recon.iterrows():
        sector_key = row.get("Sector")
        fuel_key = row["Fuel"]
        year_key = row["Year"]
        mask = (
            (df["Sector"] == sector_key)
            & (df["Fuel"] == fuel_key)
            & (df["Year"] == year_key)
        )
        df.loc[mask, "Value"] = row["Value"]
    return df


def fill_indoor_cropping_geothermal(
    df: pd.DataFrame, recon: pd.DataFrame
) -> pd.DataFrame:
    """
    Ensure Indoor Cropping has a Geothermal row using the reconciled MBIE value.
    Pulls the value from `recon` rather than a free variable.
    """
    # Pull the geothermal value for Indoor Cropping from the reconciliation table
    mask = (
        (recon["Sector"] == "Indoor Cropping")
        & (recon["Fuel"] == "Geothermal")
        & (recon["Year"] == BASE_YEAR)
    )
    if not mask.any():
        raise ValueError(
            "Geothermal value for Indoor Cropping not found in reconciliation table."
        )

    agriculture_geo_value = float(recon.loc[mask, "Value"].iloc[0])

    # Add the row
    new_row = {
        "SectorGroup": "Agriculture, Forestry and Fishing",
        "Sector": "Indoor Cropping",
        "SectorANZSIC": "A0111, A0114, A0122",
        "FuelGroup": "Renewables",
        "Fuel": "Geothermal",
        "TechnologyGroup": "Heat/Cooling Devices",
        "Technology": "Direct Heat",
        "EnduseGroup": "Heating/Cooling",
        "EndUse": "Low Temperature Heat (<100 C), Space Heating",
        "Transport": "Non-Transport",
        "Year": BASE_YEAR,
        "Unit": "PJ",
        "Value": agriculture_geo_value,
    }

    out = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Drop any placeholder/NA geothermal row for the base year if present
    out = out[
        ~(
            (out["Sector"].fillna("NA") == "NA")
            & (out["Fuel"] == "Geothermal")
            & (out["Year"] == BASE_YEAR)
        )
    ]

    return out


def add_livestock_horticulture_irrigation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Append livestock/horticulture/irrigation rows from the Excel patch to df,
    drop overlapping rows from the original df
    then re-aggregate to collapse any duplicates.
    """
    # Read and normalize headers
    patch_df = pd.read_excel(
        LIVESTOCK_HORTICULTURE_IRRIGATION, sheet_name="TIMES_INPUT", engine="openpyxl"
    )
    patch_df.columns = patch_df.columns.str.strip()
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Ensure patch_df has all df columns
    missing_cols = [c for c in df.columns if c not in patch_df.columns]
    for c in missing_cols:
        if c == "Value":
            patch_df[c] = 0.0
        elif c == "Year":
            patch_df[c] = BASE_YEAR
        else:
            patch_df[c] = "NA"
    patch_df = patch_df[df.columns]

    # Identify key columns for "matching" rows
    key_cols = [c for c in df.columns if c not in ["Value"]]  # all except Value

    # Create a multi-index of keys for the patch rows
    patch_keys = patch_df[key_cols].drop_duplicates()

    # Build a boolean mask: keep rows in df that do NOT match any patch key
    df_no_dupes = df.merge(patch_keys, on=key_cols, how="left", indicator=True)
    df_no_dupes = df_no_dupes[df_no_dupes["_merge"] == "left_only"].drop(
        columns=["_merge"]
    )

    # Append patch rows
    out = pd.concat([df_no_dupes, patch_df], ignore_index=True)

    # Optional: re-aggregate just in case patch has duplicate keys internally
    out = out.groupby(key_cols, as_index=False, dropna=False)["Value"].sum()

    out = out[
        ~(
            (out["Sector"].fillna("NA") == "NA")
            | ((out["Sector"] == "Non-Dairy Agriculture") & (out["Year"] == BASE_YEAR))
        )
    ]

    return out


def apply_technology_splits(
    df: pd.DataFrame,
    *,
    base_technologies: (
        str | Iterable[str] | re.Pattern
    ) = "Internal Combustion Engine (Land Transport)",
) -> pd.DataFrame:
    """
    Split rows whose Technology matches ANY of `base_technologies` using technology_splits.csv.

    - `base_technologies` can be:
        * a single string,
        * an iterable of strings, or
        * a compiled regex (re.Pattern) for flexible matching.
    - Unmatched base-tech rows are kept unchanged (no demand loss).
    - Totals are conserved (within floating precision).
    """
    ls = _load_technology_splits()
    if ls.empty:
        return df

    # Normalizer
    def _norm(s: pd.Series) -> pd.Series:
        return s.astype(str).str.replace("\ufeff", "", regex=False).str.strip()

    # Build mask for multiple base technologies (strings or regex)
    if isinstance(base_technologies, re.Pattern):
        base_mask = _norm(df["Technology"]).str.contains(base_technologies)
    else:
        base_list = (
            [base_technologies]
            if isinstance(base_technologies, str)
            else list(base_technologies)
        )
        base_list = [str(t).strip() for t in base_list if str(t).strip()]
        base_mask = _norm(df["Technology"]).isin(base_list)

    if not base_mask.any():
        logger.info("No base-tech rows to split; skipping technology split")
        return df

    key = ["Sector", "FuelGroup", "Fuel", "TechnologyGroup", "EnduseGroup", "EndUse"]

    base_rows = df[base_mask].copy()
    keep_rows = df[~base_mask].copy()

    # Match splits (shares already normalized in _load_technology_splits)
    joined = base_rows.merge(ls[key + ["TechnologyNew", "Share"]], on=key, how="left")

    # 1) Keep unmatched base-tech rows as-is
    unmatched_rows = joined[~joined["Share"].notna()].drop(
        columns=["TechnologyNew", "Share"], errors="ignore"
    )

    # 2) Split matched rows
    split_rows = joined[joined["Share"].notna()].copy()
    split_rows["Value"] = split_rows["Value"] * split_rows["Share"]
    split_rows["Technology"] = split_rows["TechnologyNew"]
    split_rows = split_rows.drop(columns=["TechnologyNew", "Share"])

    # Combine and re-aggregate
    out = pd.concat([keep_rows, unmatched_rows, split_rows], ignore_index=True)
    out = out.groupby(
        [c for c in df.columns if c != "Value"], as_index=False, dropna=False
    )["Value"].sum()

    # Diagnostics: which base-tech rows were matched vs not matched
    diag = (
        joined.assign(
            Status=joined["Share"]
            .notna()
            .map({True: "MatchedSplit", False: "NoSplitFound"}),
            BaseTechnology=_norm(joined["Technology"]),
        )
        .groupby(["Status", "BaseTechnology"] + key, as_index=False)["Value"]
        .sum()
        .sort_values(["Status", "BaseTechnology"] + key)
    )
    try:
        save_checks(
            diag,
            "technology_split_match_diagnostics.csv",
            "split matches vs missing",
        )
    except (OSError, PermissionError, FileNotFoundError):
        # Ignore file/permission issues when writing diagnostics
        pass

    return out


def filter_output_to_base_year(df: pd.DataFrame) -> pd.DataFrame:
    """Filter the DataFrame to the base year without dropping the Year column."""
    return df[df["Year"] == BASE_YEAR].copy()


def check_sector_demand_shares(df: pd.DataFrame, year: int = BASE_YEAR) -> None:
    """Write a quick check of ag_forest_fish demand shares by sector."""
    tmp = (
        df[df["EndUse"] != "Irrigation"].copy() if "EndUse" in df.columns else df.copy()
    )
    tmp = tmp[tmp["Year"] == year]
    tmp = tmp.groupby(["Sector"], as_index=False)[["Value"]].sum()
    tmp["Total Demand"] = tmp["Value"].sum()
    tmp["Share of Ag_forest_fish demand"] = tmp["Value"] / tmp["Value"].sum()
    save_checks(
        tmp,
        f"ag_forest_fish_demand_shares_{year}.csv",
        f"ag_forest_fish demand shares {year}",
    )


# ----------------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------------
def main() -> None:
    """Run the ag/forestry/fishing EEUD → TIMES alignment pipeline and write outputs/checks."""
    logger.info("Loading inputs…")
    data = load_data()

    logger.info("Filtering EEUD to Ag_forest_fish and converting to PJ…")
    df = get_ag_forest_fish_pj(data["eeud"])

    logger.info("Mapping EEUD sectors to TIMES sectors (Ag_forest_fish)…")
    df = add_times_categories(df, data["times_eeud_categories"])

    logger.info("Aggregating EEUD data…")
    df = aggregate_eeud(df)

    logger.info("Reconciling MBIE data…")
    recon = mbie_ag_forest_fish_energy(data["mbie_energy_balance"])
    df = apply_mbie_reconciliation(df, recon)
    df = fill_indoor_cropping_geothermal(df, recon)

    logger.info("Adding Livestock, Horticulture and Irrigation demand…")
    df = add_livestock_horticulture_irrigation(df)

    logger.info("Applying technology splits (Ute/tractor/truck/CY/GB)…")
    df = apply_technology_splits(
        df,
        base_technologies=[
            "Internal Combustion Engine (Land Transport)",
            "Irrigation",
            "Hot Water Cylinder",
            "Refrigeration Systems",
            "Electric Motor",
        ],
    )

    logger.info("Writing checks (shares by sector)…")
    check_sector_demand_shares(df, year=BASE_YEAR)

    logger.info("Saving time-series alignment check…")
    save_checks(df, OUT_TIMESERIES_CHECK, "full EEUD timeseries (ag_forest_fish)")

    logger.info("Filtering to base year and saving preprocessing output…")
    df_baseyear = filter_output_to_base_year(df)
    print("Final DataFrame columns:", df_baseyear.columns)
    save_output(df_baseyear, OUT_BASEYEAR)

    logger.info("Done.")


if __name__ == "__main__":
    main()
