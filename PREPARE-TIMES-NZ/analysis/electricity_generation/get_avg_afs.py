"""Calculate weighted average renewable AF values by technology and island."""

from __future__ import annotations

import pandas as pd
from prepare_times_nz.utilities.filepaths import (
    ANALYSIS,
    ASSUMPTIONS,
    STAGE_2_DATA,
    STAGE_4_DATA,
)

RENEWABLE_CURVES = (
    ASSUMPTIONS / "electricity_generation/renewable_curves/RenewableCurves.csv"
)
FUTURE_TECH_ASSUMPTIONS = (
    ASSUMPTIONS / "electricity_generation/future_techs/TechnologyAssumptions.csv"
)
YRFR_CANDIDATES = [
    STAGE_2_DATA / "settings/load_curves/yrfr.csv",
    STAGE_4_DATA / "sys_settings/yrfr.csv",
]

OUTPUT_DIR = ANALYSIS / "electricity_generation/results"


def load_yrfr() -> pd.DataFrame:
    """Load YRFR and return columns: TimeSlice, YRFR."""
    for filepath in YRFR_CANDIDATES:
        if not filepath.exists():
            continue

        df = pd.read_csv(filepath)
        df.columns = df.columns.str.replace("\ufeff", "", regex=False)

        if {"TimeSlice", "YRFR"}.issubset(df.columns):
            return df[["TimeSlice", "YRFR"]].copy()

        if {"TimeSlice", "Attribute", "AllRegions"}.issubset(df.columns):
            df = df[df["Attribute"] == "YRFR"].copy()
            df = df.rename(columns={"AllRegions": "YRFR"})
            return df[["TimeSlice", "YRFR"]].copy()

    candidate_str = ", ".join(str(path) for path in YRFR_CANDIDATES)
    raise FileNotFoundError(f"Could not find usable YRFR file in: {candidate_str}")


def get_yrfr_weight(
    timeslice: str, yrfr_df: pd.DataFrame, exact_map: dict, season_map: dict
):
    """
    Resolve YRFR weight for a renewable-curve timeslice.

    Supports exact matches (e.g. 'WIN-WK-D') and coarser seasonal rows
    (e.g. 'SUM-') by summing matching detailed YRFR entries.
    """
    if timeslice in exact_map:
        return exact_map[timeslice]

    if timeslice.endswith("-"):
        season_key = timeslice.rstrip("-")
        if season_key in season_map:
            return season_map[season_key]

    prefix_sum = yrfr_df.loc[
        yrfr_df["TimeSlice"].str.startswith(timeslice), "YRFR"
    ].sum()
    if prefix_sum > 0:
        return prefix_sum

    return pd.NA


def calculate_weighted_avg_af() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (tech_region_avg, comparison_to_future_assumptions)."""
    curves = pd.read_csv(RENEWABLE_CURVES)
    yrfr = load_yrfr()

    curves.columns = curves.columns.str.replace("\ufeff", "", regex=False)
    yrfr.columns = yrfr.columns.str.replace("\ufeff", "", regex=False)

    curves = curves[["TimeSlice", "TechCode", "NI", "SI"]].copy()
    yrfr = yrfr[["TimeSlice", "YRFR"]].copy()

    exact_map = yrfr.set_index("TimeSlice")["YRFR"].to_dict()
    season_map = (
        yrfr.assign(Season=yrfr["TimeSlice"].str.split("-").str[0])
        .groupby("Season")["YRFR"]
        .sum()
        .to_dict()
    )

    curves["YRFR"] = curves["TimeSlice"].apply(
        get_yrfr_weight, args=(yrfr, exact_map, season_map)
    )

    curves_long = curves.melt(
        id_vars=["TimeSlice", "TechCode", "YRFR"],
        value_vars=["NI", "SI"],
        var_name="Region",
        value_name="AF",
    )

    curves_long = curves_long.dropna(subset=["AF", "YRFR"]).copy()
    curves_long["WeightedAFContribution"] = curves_long["AF"] * curves_long["YRFR"]

    tech_region_avg = (
        curves_long.groupby(["TechCode", "Region"], as_index=False)[
            ["WeightedAFContribution", "YRFR"]
        ]
        .sum()
        .rename(columns={"YRFR": "WeightUsed"})
    )
    tech_region_avg["WeightedAF"] = (
        tech_region_avg["WeightedAFContribution"] / tech_region_avg["WeightUsed"]
    )
    tech_region_avg = tech_region_avg.drop(columns="WeightedAFContribution")

    future_assumptions = pd.read_csv(FUTURE_TECH_ASSUMPTIONS)[
        ["Tech_TIMES", "AFA"]
    ].copy()
    future_assumptions = future_assumptions.rename(columns={"Tech_TIMES": "TechCode"})

    comparison = tech_region_avg.merge(future_assumptions, on="TechCode", how="left")
    comparison["WeightedAF_minus_AFA"] = comparison["WeightedAF"] - comparison["AFA"]

    return tech_region_avg


def main():
    """Script entrypoint."""

    tech_region_avg = calculate_weighted_avg_af()
    print(tech_region_avg.sort_values(["TechCode", "Region"]).to_string(index=False))


if __name__ == "__main__":
    main()
