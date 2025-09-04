"""
Common funtions to merge technology assumptions
to the dataframe
"""

from typing import Optional, Sequence

import pandas as pd
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.logger_setup import logger

BASE_YEAR = 2023
CAP2ACT = 31.536
# RUN_TESTS = True


def check_missing_lifetimes(df: pd.DataFrame) -> None:
    """Log warning for technologies missing lifetime data."""
    missing_techs = df[df["Life"].isna()]["Technology"].drop_duplicates()
    if not missing_techs.empty:
        logger.warning("The following technologies have no lifetimes:")
        for tech in missing_techs:
            logger.warning("    '%s'", tech)
        logger.warning("These will have infinite lifetimes in the model.")


def add_lifetimes(
    df: pd.DataFrame,
    lifetimes: pd.DataFrame,
    cols: Sequence[str] = ("Technology",),  # immutable default
    # run_tests: bool = RUN_TESTS,
) -> pd.DataFrame:
    """Merge technology lifetime data into the main DataFrame."""
    out = df.merge(lifetimes, on=list(cols), how="left")
    # if run_tests:
    #     check_missing_lifetimes(out)
    return out


def check_missing_efficiencies(
    df: pd.DataFrame,
    cols: Sequence[str] = ("Technology", "Fuel"),
) -> None:
    """Log warning for technologies missing efficiency data."""
    missing_eff = df[df["Efficiency"].isna()][list(cols)].drop_duplicates()
    if not missing_eff.empty:
        logger.warning("Technologies with missing efficiency:")
        for _, row in missing_eff.iterrows():
            formatted = " | ".join(f"'{row[c]}'" for c in cols)
            logger.warning("    %s", formatted)


def add_efficiencies(
    df: pd.DataFrame,
    eff_data: pd.DataFrame,  # run_tests: bool = RUN_TESTS
) -> pd.DataFrame:
    """Merge efficiency data per fuel and technology into main DataFrame."""
    eff_data = eff_data[["Technology", "Fuel", "Efficiency"]]
    df = df.merge(eff_data, on=["Technology", "Fuel"], how="left")
    # if run_tests:
    #     check_missing_efficiencies(df)
    df["Efficiency"] = df["Efficiency"].fillna(1)
    return df


def check_missing_capex(
    df: pd.DataFrame,
    cols: Sequence[str] = ("Technology", "Fuel"),
) -> None:
    """Log warning for processes/technologies missing capital cost data."""
    missing_capex = df[df["CAPEX"].isna()][list(cols)].drop_duplicates()
    if not missing_capex.empty:
        logger.warning("Processes with missing capital cost:")
        for _, row in missing_capex.iterrows():
            logger.warning("    %s", " | ".join(f"'{row[c]}'" for c in cols))


# Vectorized alternative (optional):
# if not missing_capex.empty:
#     logger.warning("Processes with missing capital cost:\n    %s",
#                    "\n    ".join(" | ".join(f"'{v}'" for v in r)
#                                 for r in missing_capex.to_numpy()))


# --- CAPEX / OPEX merge functions -------------------------------------------


def add_capex(
    df: pd.DataFrame,
    capex_data: pd.DataFrame,
    cols: Sequence[str] = ("Technology", "Fuel"),
    # run_tests: bool = RUN_TESTS,
) -> pd.DataFrame:
    """Merge and deflate CAPEX into the main DataFrame."""
    # Select only required columns from capex_data
    capex_sel = capex_data[list(cols) + ["PriceBaseYear", "CAPEX"]]
    capex_deflated = deflate_data(
        capex_sel, base_year=BASE_YEAR, variables_to_deflate=["CAPEX"]
    )
    out = df.merge(capex_deflated, on=list(cols), how="left")
    # if run_tests:
    #     check_missing_capex(out, cols=cols)
    return out


def add_opex(
    df: pd.DataFrame,
    opex_data: pd.DataFrame,
    cols: Sequence[str] = ("Technology", "Fuel"),
    # run_tests: bool = RUN_TESTS,  # kept for symmetry; not used here
) -> pd.DataFrame:
    """Merge and deflate OPEX into the main DataFrame."""
    opex_sel = opex_data[list(cols) + ["PriceBaseYear", "OPEX"]]
    opex_deflated = deflate_data(
        opex_sel, base_year=BASE_YEAR, variables_to_deflate=["OPEX"]
    ).drop(columns="PriceBaseYear")
    return df.merge(opex_deflated, on=list(cols), how="left")


# --- AFA merge (flexible keys) ----------------------------------------------


def add_afa(
    df: pd.DataFrame,
    afa_data: pd.DataFrame,
    preferred_keys: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """
    Merge Annual Full Availability (AFA) data into main DataFrame.

    - If preferred_keys is provided, use them (if present in both frames).
    - Else, use ["Sector","EndUse","Technology"] when available; fall back to ["EndUse"].
    """
    if preferred_keys:
        keys = [k for k in preferred_keys if k in df.columns and k in afa_data.columns]
        if not keys:
            raise KeyError(f"No valid join keys from preferred_keys: {preferred_keys}")
    else:
        if {"Sector", "EndUse", "Technology"}.issubset(afa_data.columns) and {
            "Sector",
            "EndUse",
            "Technology",
        }.issubset(df.columns):
            keys = ["Sector", "EndUse", "Technology"]
        elif "EndUse" in afa_data.columns and "EndUse" in df.columns:
            keys = ["EndUse"]
        else:
            raise KeyError("No compatible join keys between df and afa_data.")

    afa_subset = afa_data[list(keys) + ["AFA"]].drop_duplicates(subset=list(keys))
    return df.merge(afa_subset, on=list(keys), how="left")


def estimate_capacity(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate process capacity from energy input, efficiency, and AFA."""
    df["InputEnergy"] = df["Value"]
    df["OutputEnergy"] = df["InputEnergy"] * df["Efficiency"]
    df["Capacity"] = df["OutputEnergy"] / CAP2ACT / df["AFA"]
    return df
