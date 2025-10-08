"""
Some charts of the load curve inputs

Fairly scrappy
"""

# pylint: disable=import-outside-toplevel
import re
from itertools import product
from pathlib import Path

import pandas as pd
from plotnine import (
    aes,
    element_text,
    facet_wrap,
    geom_col,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_classic,
)
from prepare_times_nz.utilities.filepaths import ANALYSIS, ASSUMPTIONS, STAGE_2_DATA

OUTPUT_LOCATION = ANALYSIS / "results/load_curves"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

LOAD_CURVE_DATA = STAGE_2_DATA / "settings/load_curves"
COM_ASSUMPTIONS = Path(ASSUMPTIONS) / "commercial_demand"

TOTAL_CONSUMPTION = 39135  # for reference
BASE_YEAR = 2023

com_curves = pd.read_csv(
    COM_ASSUMPTIONS / "commercial_curves.csv",
)
yrfr = pd.read_csv(LOAD_CURVE_DATA / "yrfr.csv")
com_demand = pd.read_csv(STAGE_2_DATA / "commercial/baseyear_commercial_demand.csv")

commercial_elc = (
    com_demand[
        (com_demand["Fuel"] == "Electricity")
        & (com_demand["Variable"] == "InputEnergy")
    ]
    .groupby(["Year", "Sector", "CommodityOut"], as_index=False)["Value"]
    .sum()
)

commercial_elc["GWH"] = commercial_elc["Value"] * 277.77778  # PJ to GWh

# Restrict to base year once
elc_year = commercial_elc[commercial_elc["Year"] == BASE_YEAR].copy()
elc_year["CommodityOut"] = elc_year["CommodityOut"].astype(str)

com_total_by = elc_year[elc_year["Year"] == BASE_YEAR]


def sum_gwh_for_pattern(pattern_str: str, df_elc: pd.DataFrame) -> float:
    """Sum GWh where 'CommodityOut' matches Excel-like include patterns
    and is not in exact excludes. pattern_str: comma-separated tokens;
    '*' wildcard supported; '-EXACT' = exact exclude.
    '"""
    if "CommodityOut" not in df_elc.columns or (
        "GWH" not in df_elc.columns and "GWh" not in df_elc.columns
    ):
        return 0.0

    proc = df_elc["CommodityOut"].astype(str)
    gwh_col = "GWH" if "GWH" in df_elc.columns else "GWh"
    gwh = pd.to_numeric(df_elc[gwh_col], errors="coerce")

    parts = [p.strip() for p in str(pattern_str or "").split(",") if p.strip()]
    include_regexes, excludes = [], set()
    for part in parts:
        if part.startswith("-"):
            excludes.add(part[1:].strip())
        else:
            pat = re.escape(part).replace(r"\*", ".*")
            pat = re.sub(r"\\([-_/ ])", r"[-_/ ]?", pat)
            include_regexes.append(pat)

    if not include_regexes:
        return 0.0

    include_pat = f"^(?:{'|'.join(include_regexes)})$"
    mask = proc.str.contains(
        include_pat, regex=True, na=False, case=False
    ) & ~proc.isin(excludes)
    return float(gwh.where(mask).sum(skipna=True))


com_curves["Technology"] = com_curves["Technology"].astype(str)
com_curves["TotalDemand"] = com_curves["Technology"].apply(
    lambda s: sum_gwh_for_pattern(s, elc_year)
)

# Now compute MWh/GWh by timeslice
com_curves["GWh"] = com_curves["TotalDemand"] * com_curves["LoadCurve"]

# Merge yrfr (assumes it has TimeSlice and YRFR columns)
com_curves = com_curves.merge(yrfr, on=["TimeSlice"], how="left")
com_curves["HoursInSlice"] = com_curves["YRFR"] * 365 * 24
com_curves["AverageLoadGW"] = com_curves["GWh"] / com_curves["HoursInSlice"]

print(com_curves)


def gwh_by_sector_for_pattern(pattern_str: str, df_elc: pd.DataFrame) -> pd.Series:
    """
    Return sector-level GWh totals for commodities matching Excel-like patterns.
    pattern_str: comma-separated tokens; '*' wildcard supported; '-EXACT' = exact exclude.
    Requires columns: ['Sector', 'CommodityOut', 'GWH'] (or 'GWh').
    """
    # Column checks
    if "Sector" not in df_elc.columns or "CommodityOut" not in df_elc.columns:
        return pd.Series(dtype=float)
    gwh_col = (
        "GWH"
        if "GWH" in df_elc.columns
        else ("GWh" if "GWh" in df_elc.columns else None)
    )
    if gwh_col is None:
        return pd.Series(dtype=float)

    # Normalize
    commod = df_elc["CommodityOut"].astype(str)
    gwh = pd.to_numeric(df_elc[gwh_col], errors="coerce")

    # Parse Excel-like include/exclude pattern
    parts = [p.strip() for p in str(pattern_str or "").split(",") if p.strip()]
    include_regexes: list[str] = []
    excludes: set[str] = set()
    for part in parts:
        if part.startswith("-"):
            excludes.add(part[1:].strip())
        else:
            pat = re.escape(part)
            pat = pat.replace(r"\*", ".*")
            pat = re.sub(r"\\([-_/ ])", r"[-_/ ]?", pat)
            include_regexes.append(pat)

    if not include_regexes:
        return pd.Series(dtype=float)

    include_pat = f"^(?:{'|'.join(include_regexes)})$"
    mask = commod.str.contains(
        include_pat, regex=True, na=False, case=False
    ) & ~commod.isin(excludes)

    out = (
        pd.DataFrame({"Sector": df_elc["Sector"], "GWH": gwh})
        .loc[mask]
        .groupby("Sector", dropna=False)["GWH"]
        .sum(min_count=1)  # if all-NaN in a group, keep NaN rather than 0
        .fillna(0.0)  # and then standardize to 0.0
    )

    # Ensure a plain float Series
    out = out.astype(float)
    return out


# Expand com_curves rows into per-sector rows
rows: list[dict[str, float | int | str]] = []
for _, rec in com_curves.iterrows():
    by_sec = gwh_by_sector_for_pattern(rec["Technology"], elc_year)
    if by_sec.empty:
        continue
    for sector, sec_total_gwh in by_sec.items():
        gwh_slice = float(sec_total_gwh) * float(rec["LoadCurve"])
        hours = float(rec["YRFR"]) * 365 * 24
        avg_gw = gwh_slice / hours if hours else 0.0
        rows.append(
            {
                "Year": int(rec["Year"]),
                "TimeSlice": rec["TimeSlice"],
                "Technology": rec["Technology"],
                "Sector": sector,
                "LoadCurve": float(rec["LoadCurve"]),
                "TotalDemand": float(
                    sec_total_gwh
                ),  # sector-specific annual GWh for this Technology pattern
                "GWh": float(gwh_slice),
                "YRFR": float(rec["YRFR"]),
                "HoursInSlice": float(hours),
                "AverageLoadGW": float(avg_gw),
            }
        )

sector_tidy = pd.DataFrame(rows)

# ---------- Aggregate to Sector after Technology ----------
sector_by_slice = sector_tidy.groupby(
    ["Year", "TimeSlice", "Sector"], as_index=False
).agg(
    LoadCurve=("LoadCurve", "first"),  # constant per TimeSlice
    TotalDemand=("TotalDemand", "sum"),  # sum of sector demand across technologies
    GWh=("GWh", "sum"),
    YRFR=("YRFR", "first"),  # constant per TimeSlice
    HoursInSlice=("HoursInSlice", "first"),  # constant per TimeSlice
)
sector_by_slice["AverageLoadGW"] = (
    sector_by_slice["GWh"] / sector_by_slice["HoursInSlice"]
)

# --- Build a clean Season column from TimeSlice ---
dfp = sector_by_slice.copy()
dfp["TimeSlice"] = dfp["TimeSlice"].astype(str)
dfp["Season"] = dfp["TimeSlice"].str.split("-").str[0].str.strip()

season_order: list[str] = ["WIN", "SPR", "SUM", "FAL"]
dfp["Season"] = pd.Categorical(dfp["Season"], categories=season_order, ordered=True)

# Order TimeSlice for x-axis
day_order = ["WK", "WE"]
tod_order = ["P", "D", "N"]
codes_order = [
    "-".join([s, d, t]) for s, d, t in product(season_order, day_order, tod_order)
]
dfp["TimeSlice"] = pd.Categorical(
    dfp["TimeSlice"], categories=codes_order, ordered=True
)

# Order sectors (optional)
sector_order = (
    dfp.groupby("Sector")["TotalDemand"]
    .sum()
    .sort_values(ascending=False)
    .index.tolist()
)
dfp["Sector"] = pd.Categorical(dfp["Sector"], categories=sector_order, ordered=True)

# --- Define colours (keys must match Season values) ---
season_colors = {
    "WIN": "#56B4E9",  # light blue
    "SPR": "#009E73",  # green
    "SUM": "#E69F00",  # orange
    "FAL": "#D55E00",  # red/orange
}

# --- Build chart ---
chart = (
    ggplot(dfp, aes(x="TimeSlice", y="AverageLoadGW", fill="Season"))
    + geom_col()
    + facet_wrap("~Sector", ncol=3, scales="free_y")
    + theme_classic()
    + labs(
        title="Average Load by TimeSlice and Sector",
        x="TimeSlice",
        y="GW",
        fill="Season",
    )
    + theme(
        axis_text_x=element_text(rotation=90, ha="center", size=7),
        legend_position="bottom",
        figure_size=(16, 6),
    )
    + scale_fill_manual(values=season_colors, limits=season_order)
)

chart.save(OUTPUT_LOCATION / "commercial_load_by_sector_timeslice.png", dpi=300)
