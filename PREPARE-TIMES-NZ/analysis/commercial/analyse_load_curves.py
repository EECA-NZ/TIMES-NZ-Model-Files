"""
Some charts of the load curve inputs

Fairly scrappy
"""

from __future__ import annotations

import re
from itertools import product
from pathlib import Path
from typing import Iterable, Tuple

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

# pylint: disable=duplicate-code
from prepare_times_nz.utilities.filepaths import (
    ANALYSIS,
    ASSUMPTIONS,
    STAGE_2_DATA,
)

OUTPUT_LOCATION = ANALYSIS / "results/load_curves"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

LOAD_CURVE_DATA = STAGE_2_DATA / "settings/load_curves"
COM_ASSUMPTIONS = Path(ASSUMPTIONS) / "commercial_demand"

TOTAL_CONSUMPTION = 39135  # for reference
BASE_YEAR = 2023

com_curves = pd.read_excel(
    COM_ASSUMPTIONS / "commercial_curves.xlsx",
    engine="openpyxl",
    dtype={"Year": "Int64", "TimeSlice": str, "LoadCurve": float, "Technology": str},
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


def parse_excel_pattern(pattern_str: str) -> Tuple[str, set[str]]:
    """
    Convert an Excel-like pattern string into a regex + exclusion set.

    Example:
        'C_HLTH-*,-C_HLTH-SH,-C_HLTH-SC'
        → (include_regex, {'C_HLTH-SH', 'C_HLTH-SC'})

    '*' acts as a wildcard and '-' prefixes exact values to exclude.
    Returns:
        include_regex: regex string to match allowed values
        exclude_values: set of exact strings to exclude
    """
    parts = [p.strip() for p in (pattern_str or "").split(",") if p.strip()]
    include_regexes: list[str] = []
    exclude_values: set[str] = set()

    for part in parts:
        if part.startswith("-"):
            exclude_values.add(part[1:])  # exact match to exclude
        else:
            # Escape special chars, then allow '*' as wildcard
            regex = "^" + re.escape(part).replace(r"\*", ".*") + "$"
            include_regexes.append(regex)

    include_regex = "|".join(include_regexes) if include_regexes else r"^$"
    return include_regex, exclude_values


def sum_gwh_for_pattern(pattern_str: str, df_elc: pd.DataFrame) -> float:
    """
    Sum GWh in df_elc where 'CommodityOut' matches the include pattern and
    is not in the explicit exclude set derived from `pattern_str`.
    """
    inc_regex, excl = parse_excel_pattern(pattern_str)
    mask = df_elc["CommodityOut"].str.contains(
        inc_regex, regex=True, na=False
    ) & ~df_elc["CommodityOut"].isin(excl)
    return float(df_elc.loc[mask, "GWH"].sum())


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
    Return sector-level GWh totals for commodities matching `pattern_str`.

    Args:
        pattern_str: Excel-like include/exclude pattern.
        df_elc: DataFrame containing at least ['Sector', 'CommodityOut', 'GWH'].
    """
    inc_regex, excl = parse_excel_pattern(pattern_str)
    if inc_regex == r"^$":
        return pd.Series(dtype=float)
    mask = df_elc["CommodityOut"].str.contains(
        inc_regex, regex=True, na=False
    ) & ~df_elc["CommodityOut"].isin(excl)
    return df_elc.loc[mask].groupby("Sector")["GWH"].sum()


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
day_order: Iterable[str] = ["WK", "WE"]
tod_order: Iterable[str] = ["P", "D", "N"]
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
