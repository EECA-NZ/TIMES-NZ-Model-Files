"""
Aggregate NIWA solar hourly profiles to TIMES-NZ timeslices.
"""

from __future__ import annotations

import pandas as pd
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import ASSUMPTIONS, STAGE_3_DATA

STATIC_RENEWABLE_CURVES_FILE = (
    ASSUMPTIONS / "electricity_generation/renewable_curves/RenewableCurves.csv"
)
SOLAR_ZONE_WEIGHTS_FILE = (
    ASSUMPTIONS / "electricity_generation/renewable_curves/SolarZoneWeights.csv"
)

OUTPUT_ROOT = STAGE_3_DATA / "electricity/solar_af"
HOURLY_DIR = OUTPUT_ROOT / "hourly"
SOLAR_AF_DIR = OUTPUT_ROOT / "timeslices"

SOLAR_AF_FILE = SOLAR_AF_DIR / "solar_availability_factors.csv"
SOLAR_AF_BY_ZONE_FILE = SOLAR_AF_DIR / "solar_availability_factors_by_zone.csv"
RENEWABLE_CURVES_FILE = STAGE_3_DATA / "electricity/renewable_curves.csv"

SOLAR_TECHS = {"SolarDistSmall", "SolarDistBifacial", "SolarTrack", "SolarFixed"}


def load_zone_weights() -> pd.DataFrame:
    """
    Load configured solar zone weights and normalize them within each island.
    """
    zone_weights = pd.read_csv(SOLAR_ZONE_WEIGHTS_FILE)
    required_cols = ["ZoneCode", "Region", "Island", "Weight"]
    missing_cols = set(required_cols).difference(zone_weights.columns)
    if missing_cols:
        missing = ", ".join(sorted(missing_cols))
        raise ValueError(
            f"Missing required columns in {SOLAR_ZONE_WEIGHTS_FILE}: {missing}"
        )

    zone_weights = zone_weights[required_cols].copy()
    if zone_weights["ZoneCode"].duplicated().any():
        duplicates = zone_weights.loc[
            zone_weights["ZoneCode"].duplicated(), "ZoneCode"
        ].tolist()
        raise ValueError(
            f"Duplicate ZoneCode entries in {SOLAR_ZONE_WEIGHTS_FILE}: {duplicates}"
        )

    zone_weights["Weight"] = pd.to_numeric(zone_weights["Weight"], errors="raise")
    if (zone_weights["Weight"] < 0).any():
        raise ValueError(
            f"Negative weights are not allowed in {SOLAR_ZONE_WEIGHTS_FILE}"
        )

    island_weight_totals = zone_weights.groupby("Island", as_index=False)[
        "Weight"
    ].sum()
    zero_weight_islands = island_weight_totals.loc[
        island_weight_totals["Weight"] <= 0, "Island"
    ].tolist()
    if zero_weight_islands:
        raise ValueError(
            "Configured solar zone weights must sum to a positive value for each island. "
            f"Invalid islands: {zero_weight_islands}"
        )

    zone_weights = zone_weights.merge(
        island_weight_totals.rename(columns={"Weight": "IslandWeightTotal"}),
        on="Island",
        how="left",
    )
    zone_weights["NormalizedWeight"] = (
        zone_weights["Weight"] / zone_weights["IslandWeightTotal"]
    )
    return zone_weights.sort_values(["Island", "ZoneCode"]).reset_index(drop=True)


def aggregate_zone_availability_factors(hourly: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate hourly zone output into TIMES-NZ availability factors.
    """
    grouped = hourly.groupby(
        ["Tech_TIMES", "Scenario", "ZoneCode", "Region", "Island", "TimeSlice"],
        as_index=False,
    ).agg(
        AvailabilityFactor=("generation_kw_per_kw", "mean"),
        HoursInTimeSlice=("generation_kw_per_kw", "size"),
    )

    return grouped.sort_values(["Tech_TIMES", "ZoneCode", "TimeSlice"]).reset_index(
        drop=True
    )


def aggregate_island_curves(
    zone_factors: pd.DataFrame, zone_weights: pd.DataFrame
) -> pd.DataFrame:
    """
    Collapse zone-level solar factors to the island granularity used by TIMES-NZ.
    """
    weighted = zone_factors.merge(
        zone_weights,
        on=["ZoneCode", "Region", "Island"],
        how="left",
        validate="many_to_one",
    )
    missing_weights = (
        weighted.loc[weighted["NormalizedWeight"].isna(), "ZoneCode"]
        .drop_duplicates()
        .tolist()
    )
    if missing_weights:
        raise ValueError(
            "Missing configured solar zone weights for zone codes: "
            f"{missing_weights}"
        )

    weighted["WeightedAvailability"] = (
        weighted["AvailabilityFactor"] * weighted["NormalizedWeight"]
    )
    island = weighted.groupby(
        ["Tech_TIMES", "TimeSlice", "Island"], as_index=False
    ).agg(
        WeightedAvailability=("WeightedAvailability", "sum"),
        WeightInTimeSlice=("NormalizedWeight", "sum"),
    )
    island["AvailabilityFactor"] = (
        island["WeightedAvailability"] / island["WeightInTimeSlice"]
    )
    island = island.pivot(
        index=["TimeSlice", "Tech_TIMES"],
        columns="Island",
        values="AvailabilityFactor",
    ).reset_index()

    island.columns.name = None
    island["NI"] = island["NI"].fillna(0.0)
    island["SI"] = island["SI"].fillna(0.0)
    return island[["TimeSlice", "Tech_TIMES", "NI", "SI"]].sort_values(
        ["Tech_TIMES", "TimeSlice"]
    )


def merge_solar_and_static_curves(
    solar_curves: pd.DataFrame, static_curves: pd.DataFrame
) -> pd.DataFrame:
    """
    Replace the static solar rows with generated NIWA-based solar rows.
    """
    static = static_curves.copy()
    if "TechCode" in static.columns:
        static = static.rename(columns={"TechCode": "Tech_TIMES"})

    static = static[~static["Tech_TIMES"].isin(SOLAR_TECHS)]
    merged = pd.concat([static, solar_curves], ignore_index=True)
    return merged.sort_values(["Tech_TIMES", "TimeSlice"]).reset_index(drop=True)


def build_solar_curves():
    """
    Aggregate hourly solar output to TIMES-NZ timeslices and merge with the
    non-solar renewable curve assumptions.
    """
    SOLAR_AF_DIR.mkdir(parents=True, exist_ok=True)
    RENEWABLE_CURVES_FILE.parent.mkdir(parents=True, exist_ok=True)

    hourly = pd.read_csv(
        HOURLY_DIR / "all_scenarios_hourly_long.csv", parse_dates=["Trading_Date"]
    )
    zone_factors = aggregate_zone_availability_factors(hourly)
    zone_weights = load_zone_weights()
    island_curves = aggregate_island_curves(zone_factors, zone_weights)
    static_curves = pd.read_csv(STATIC_RENEWABLE_CURVES_FILE)
    merged_curves = merge_solar_and_static_curves(island_curves, static_curves)

    _save_data(
        zone_factors,
        SOLAR_AF_BY_ZONE_FILE.name,
        "Zone-level solar availability factors",
        SOLAR_AF_BY_ZONE_FILE.parent,
    )
    _save_data(
        island_curves,
        SOLAR_AF_FILE.name,
        "Island-level solar availability factors",
        SOLAR_AF_FILE.parent,
    )
    _save_data(
        merged_curves,
        RENEWABLE_CURVES_FILE.name,
        "Renewable curves with generated solar availability factors",
        RENEWABLE_CURVES_FILE.parent,
    )


if __name__ == "__main__":
    build_solar_curves()
