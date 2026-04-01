"""
Build residential space-heating availability-factor tables for VEDA.

This module is intended to replace the hand-maintained residential
space-heating AF inputs with a generated stage 4 output.

For now, the generated AF curve mirrors the residential space-heating
load-curve shares produced upstream from the RBS-based residential
load-curve workflow. The implementation is deliberately narrow so we
can swap the current manual files with minimal churn.
"""

from pathlib import Path

import pandas as pd
from prepare_times_nz.stage_0.stage_0_settings import BASE_YEAR
from prepare_times_nz.utilities.data_in_out import _save_data
from prepare_times_nz.utilities.filepaths import STAGE_2_DATA, STAGE_4_DATA

OUTPUT_LOCATION = Path(STAGE_4_DATA) / "scen_loadcurve"
OUTPUT_LOCATION.mkdir(parents=True, exist_ok=True)

LOAD_CURVE_DATA = Path(STAGE_2_DATA) / "settings/load_curves"

DEFAULT_CURVE_FILE = "residential_curves_ripple_50.csv"
SPACE_HEATING_END_USE = "Low Temperature Heat (<100 C), Space Heating"
SPACE_HEATING_COMMODITIES = ("JD-S_HEAT", "DD-S_HEAT")
SPACE_HEATING_PROCESS_SET = "RES*ELC*S_HEAT"

AF_ATTRIBUTE = "NCAP_AF"
AFA_ATTRIBUTE = "NCAP_AFA"
BASE_AF_YEAR = BASE_YEAR + 1
BASE_AFA_VALUE = 1.0
FUTURE_DEFAULT_VALUE = 5.0
FUTURE_DEFAULT_YEAR = 0
LIMIT_TYPE = "FX"


def save_output(df: pd.DataFrame, name: str, label: str) -> None:
    """Stage-4 wrapper for saving generated residential AF inputs."""
    _save_data(df, name=name, label=label, filepath=OUTPUT_LOCATION)


def load_space_heating_curve(curve_file: str = DEFAULT_CURVE_FILE) -> pd.DataFrame:
    """
    Load the upstream residential space-heating curve and collapse it to one row
    per timeslice.

    The stage-2 residential load-curve file contains duplicated space-heating
    curve shapes for joined and detached dwellings. We verify that those shapes
    match before reducing them to one AF value per timeslice.
    """

    path = LOAD_CURVE_DATA / curve_file
    df = pd.read_csv(path)

    df = df[
        (df["EndUse"] == SPACE_HEATING_END_USE)
        & (df["Commodity"].isin(SPACE_HEATING_COMMODITIES))
    ].copy()

    if df.empty:
        raise ValueError(f"No residential space-heating rows found in {path}")

    distinct_values = df.groupby("TimeSlice")["LoadCurve"].nunique()
    inconsistent = distinct_values[distinct_values > 1]
    if not inconsistent.empty:
        raise ValueError(
            "Residential space-heating curves differ across dwelling commodities "
            f"for timeslices: {', '.join(inconsistent.index.tolist())}"
        )

    df = (
        df.groupby("TimeSlice", as_index=False)
        .agg(AllRegions=("LoadCurve", "first"))
        .sort_values("TimeSlice")
        .reset_index(drop=True)
    )

    return df


def build_residential_space_heating_af(
    curve_file: str = DEFAULT_CURVE_FILE,
    process_set: str = SPACE_HEATING_PROCESS_SET,
    year: int = BASE_AF_YEAR,
    future_default_value: float = FUTURE_DEFAULT_VALUE,
    future_default_year: int = FUTURE_DEFAULT_YEAR,
) -> pd.DataFrame:
    """
    Build the generated replacement for the current manual NCAP_AF table.

    TODO:
    - Decide whether the AF curve should always mirror the 50% ripple curve.
    - Decide whether a future Transformation-specific AF curve is needed.
    - Decide whether a scalar adjustment should be retained on top of COM_FR.
    """

    df = load_space_heating_curve(curve_file=curve_file)
    df["Attribute"] = AF_ATTRIBUTE
    df["Pset_PN"] = process_set
    df["Year"] = year
    df["LimType"] = LIMIT_TYPE

    out = df[["Attribute", "TimeSlice", "Pset_PN", "AllRegions", "Year", "LimType"]]

    future_rows = out.copy()
    future_rows["AllRegions"] = future_default_value
    future_rows["Year"] = future_default_year

    return pd.concat([out, future_rows], ignore_index=True)


def build_residential_space_heating_afa_reset(
    process_set: str = SPACE_HEATING_PROCESS_SET,
    year: int = BASE_AF_YEAR,
    base_afa_value: float = BASE_AFA_VALUE,
    future_default_value: float = FUTURE_DEFAULT_VALUE,
    future_default_year: int = FUTURE_DEFAULT_YEAR,
) -> pd.DataFrame:
    """Build the companion NCAP_AFA reset table."""

    return pd.DataFrame(
        {
            "Attribute": [AFA_ATTRIBUTE, AFA_ATTRIBUTE],
            "Pset_PN": [process_set, process_set],
            "AllRegions": [base_afa_value, future_default_value],
            "Year": [year, future_default_year],
        }
    )


def main() -> None:
    """Generate residential space-heating AF and AFA reset tables."""

    af_df = build_residential_space_heating_af()
    afa_df = build_residential_space_heating_afa_reset()

    save_output(
        af_df,
        "residential_space_heating_af.csv",
        "Residential space-heating NCAP_AF",
    )
    save_output(
        afa_df,
        "residential_space_heating_afa_reset.csv",
        "Residential space-heating NCAP_AFA reset",
    )


if __name__ == "__main__":
    main()
