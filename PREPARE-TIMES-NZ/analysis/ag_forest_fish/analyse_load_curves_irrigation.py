"""
Some charts of the load curve inputs

Fairly scrappy
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
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

AG_ASSUMPTIONS = Path(ASSUMPTIONS) / "ag_forest_fish_demand"
BASE_YEAR = 2023
PJ_TO_GWH = 1e6 / 3.6e3  # 277.777...

ag_curves = pd.read_csv(AG_ASSUMPTIONS / "ag_curves_irrigation.csv")
yrfr = pd.read_csv(AG_ASSUMPTIONS / "yrfr_season.csv")
ag_demand = pd.read_csv(
    STAGE_2_DATA / "ag_forest_fish/baseyear_ag_forest_fish_demand.csv"
)


def sum_gwh_for_pattern(pattern_str: str, df_elc: pd.DataFrame) -> float:
    """
    Sum GWh where 'Process' matches Excel-like include patterns and is not in exact excludes.
    pattern_str: comma-separated tokens; '*' wildcard supported; '-EXACT' = exact exclude.
    Example: 'IRG-*,-IRG-OLD,ALIVE-IRG*'
    """
    # Ensure required columns exist
    if "Process" not in df_elc.columns or (
        "GWH" not in df_elc.columns and "GWh" not in df_elc.columns
    ):
        return 0.0

    # Normalize columns
    proc = df_elc["Process"].astype(str)
    gwh_col = "GWH" if "GWH" in df_elc.columns else "GWh"
    gwh = pd.to_numeric(df_elc[gwh_col], errors="coerce")  # non-numeric → NaN

    # Parse pattern string into include regexes and exact excludes
    parts = [p.strip() for p in str(pattern_str or "").split(",") if p.strip()]
    include_regexes: list[str] = []
    excludes: set[str] = set()

    for part in parts:
        if part.startswith("-"):
            excludes.add(part[1:].strip())
        else:
            # Excel-like wildcard → regex, make separators optional (- _ space /)
            pat = re.escape(part)
            pat = pat.replace(r"\*", ".*")
            pat = re.sub(r"\\([-_/ ])", r"[-_/ ]?", pat)
            include_regexes.append(pat)

    # If nothing to include, return 0 instead of calling str.contains with empty pat
    if not include_regexes:
        return 0.0

    include_pat = f"^(?:{'|'.join(include_regexes)})$"

    mask = proc.str.contains(
        include_pat, regex=True, na=False, case=False
    ) & ~proc.isin(excludes)

    # Sum only the matching rows; NaNs are ignored
    return float(gwh.where(mask).sum(skipna=True))


ag_elc = (
    ag_demand[
        (ag_demand["Fuel"] == "Electricity") & (ag_demand["Variable"] == "InputEnergy")
    ]
    .groupby(["Year", "Sector", "Process"], as_index=False)["Value"]
    .sum()
)
ag_elc["GWH"] = ag_elc["Value"] * PJ_TO_GWH

# Restrict to base year once
elc_year = ag_elc[ag_elc["Year"] == BASE_YEAR].copy()
elc_year["Process"] = elc_year["Process"].astype(str)

ag_total_by = elc_year[elc_year["Year"] == BASE_YEAR]

ag_curves["Technology"] = ag_curves["Technology"].astype(str)
ag_curves["TotalDemand"] = ag_curves["Technology"].apply(
    lambda s: sum_gwh_for_pattern(s, elc_year)
)

# Now compute MWh/GWh by timeslice
ag_curves["GWh"] = ag_curves["TotalDemand"] * ag_curves["LoadCurve"]

# Merge yrfr (assumes it has TimeSlice and YRFR columns)
ag_curves = ag_curves.merge(yrfr, on=["TimeSlice"], how="left")
ag_curves["HoursInSlice"] = ag_curves["YRFR"] * 365 * 24
ag_curves["AverageLoadGW"] = ag_curves["GWh"] / ag_curves["HoursInSlice"]

print(ag_curves)

tech_by_slice = ag_curves.groupby(
    ["Year", "TimeSlice", "Technology"], as_index=False
).agg(
    GWh=("GWh", "sum"),
    YRFR=("YRFR", "first"),
    HoursInSlice=("HoursInSlice", "first"),
)
tech_by_slice["AverageLoadGW"] = tech_by_slice["GWh"] / tech_by_slice["HoursInSlice"]

# --- Season + ordering ---
dfp = tech_by_slice.copy()

# Parse season
dfp["TimeSlice"] = dfp["TimeSlice"].astype(str).str.strip()
dfp["Season"] = dfp["TimeSlice"].str.split("-").str[0].str.strip()

season_order = ["WIN", "SPR", "SUM", "FAL"]
dfp["Season"] = pd.Categorical(dfp["Season"], categories=season_order, ordered=True)

# IMPORTANT: your TimeSlice strings end with a trailing '-'
codes_order = [f"{s}-" for s in season_order]  # ["WIN-","SPR-","SUM-","FAL-"]
dfp["TimeSlice"] = pd.Categorical(
    dfp["TimeSlice"], categories=codes_order, ordered=True
)

# Guard against NaNs before plotting
cols_needed = ["AverageLoadGW", "TimeSlice", "Technology"]
dfp_plot = dfp.dropna(subset=cols_needed).copy()

# If you set limits manually anywhere, compute a finite upper bound
Y_MAX = (
    float(np.nanmax(dfp_plot["AverageLoadGW"].to_numpy(dtype=float)))
    if len(dfp_plot)
    else float("nan")
)
if not np.isfinite(Y_MAX):
    Y_MAX = 1.0  # safe default

# --- Colours (optional) ---
season_colors = {
    "WIN": "#56B4E9",
    "SPR": "#009E73",
    "SUM": "#E69F00",
    "FAL": "#D55E00",
}

# --- Plot: one panel per Technology (all sectors combined within each panel) ---
chart = (
    ggplot(dfp, aes(x="TimeSlice", y="AverageLoadGW", fill="Season"))
    + geom_col()
    + facet_wrap("~Technology", scales="free_y")
    + theme_classic()
    + labs(
        title="Average Load by TimeSlice and Technology (all sectors combined)",
        x="TimeSlice",
        y="GW",
        fill="Season",
    )
    + theme(
        axis_text_x=element_text(rotation=90, ha="center", size=7),
        legend_position="bottom",
        figure_size=(16, 8),
    )
    + scale_fill_manual(values=season_colors, limits=season_order)
)

chart.save(OUTPUT_LOCATION / "irg_load_by_technology_timeslice.png", dpi=300)
