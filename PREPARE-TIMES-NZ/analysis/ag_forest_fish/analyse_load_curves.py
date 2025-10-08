"""
Some charts of the load curve inputs

Fairly scrappy
"""

from __future__ import annotations

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

# pylint: disable=duplicate-code
from prepare_times_nz.utilities.filepaths import (
    ANALYSIS,
    ASSUMPTIONS,
    STAGE_2_DATA,
)

OUTPUT_LOCATION = ANALYSIS / "results/load_curves"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

LOAD_CURVE_DATA = STAGE_2_DATA / "settings/load_curves"
AG_ASSUMPTIONS = Path(ASSUMPTIONS) / "ag_forest_fish_demand"

BASE_YEAR = 2023

base_year_load_curve = pd.read_csv(LOAD_CURVE_DATA / "base_year_load_curve.csv")
ag_curves = pd.read_excel(
    AG_ASSUMPTIONS / "ag_curves.xlsx",
    engine="openpyxl",
    dtype={"Year": "Int64", "TimeSlice": str, "LoadCurve": float, "Technology": str},
)
yrfr = pd.read_csv(LOAD_CURVE_DATA / "yrfr.csv")
ag_demand = pd.read_csv(
    STAGE_2_DATA / "ag_forest_fish/baseyear_ag_forest_fish_demand.csv"
)


def _flexify(pattern: str) -> str:
    """
    Make a regex from an Excel-like pattern:
    - escape everything
    - '*' -> '.*'
    - any escaped separator ( -, _, space, / ) -> optional '[-_/ ]?'
    """
    pat = re.escape(pattern)
    pat = pat.replace(r"\*", ".*")
    # turn each escaped separator into an optional class
    pat = re.sub(r"\\([-_/ ])", r"[-_/ ]?", pat)
    return "^" + pat + "$"


def parse_excel_pattern(pattern_str: str) -> tuple[str, set[str]]:
    """
    Returns (include_regex, exclude_exact_set)
    Comma-separated list; items prefixed with '-' go to the exclude set.
    """
    parts = [p.strip() for p in (pattern_str or "").split(",") if p.strip()]
    include_regexes: list[str] = []
    exclude_values: set[str] = set()
    for p in parts:
        if p.startswith("-"):
            exclude_values.add(p[1:].strip())
        else:
            include_regexes.append(_flexify(p))
    include_regex = "|".join(include_regexes) if include_regexes else r"^$"
    return include_regex, exclude_values


def sum_gwh_for_pattern(pattern_str: str, df_elc: pd.DataFrame) -> float:
    """
    Sum GWh where 'Process' matches the include regex and is not in the exclude set.

    Args:
        pattern_str: Excel-like pattern (supports '*' and '-EXACT' excludes).
        df_elc: DataFrame with columns ['Process', 'GWH'].

    Returns:
        Total GWh (float) for matching rows.
    """
    inc_regex, excl = parse_excel_pattern(pattern_str)
    mask = df_elc["Process"].str.contains(
        inc_regex, regex=True, na=False, case=False
    ) & ~df_elc["Process"].isin(excl)
    return float(df_elc.loc[mask, "GWH"].sum())


ag_elc = (
    ag_demand[
        (ag_demand["Fuel"] == "Electricity") & (ag_demand["Variable"] == "InputEnergy")
    ]
    .groupby(["Year", "Sector", "Process"], as_index=False)["Value"]
    .sum()
)

PJ_TO_GWH = 1e6 / 3.6e3  # 277.777...
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

base_year_load_curve["TEST"] = base_year_load_curve["LoadCurve"].sum()
base_year_load_curve["TEST2"] = base_year_load_curve["Value"].sum()

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
dfp["TimeSlice"] = dfp["TimeSlice"].astype(str)
dfp["Season"] = dfp["TimeSlice"].str.split("-").str[0].str.strip()

season_order = ["WIN", "SPR", "SUM", "FAL"]
dfp["Season"] = pd.Categorical(dfp["Season"], categories=season_order, ordered=True)

day_order = ["WK", "WE"]
tod_order = ["P", "D", "N"]
codes_order = [
    "-".join([s, d, t]) for s, d, t in product(season_order, day_order, tod_order)
]
dfp["TimeSlice"] = pd.Categorical(
    dfp["TimeSlice"], categories=codes_order, ordered=True
)

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

chart.save(OUTPUT_LOCATION / "adcf_indc_load_by_technology_timeslice.png", dpi=300)
