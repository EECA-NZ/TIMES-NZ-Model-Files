import numpy as np
import pandas as pd
from prepare_times_nz.utilities.deflator import deflate_data
from prepare_times_nz.utilities.filepaths import (
    ASSUMPTIONS,
    CONCORDANCES,
    STAGE_1_DATA,
    STAGE_2_DATA,
)
from prepare_times_nz.utilities.logger_setup import blue_text, logger

BASE_YEAR = 2023
CAP2ACT = 31.536
RUN_TESTS = True


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
    cols=["Technology"],
    run_tests: bool = RUN_TESTS,
) -> pd.DataFrame:
    """Merge technology lifetime data into the main DataFrame."""
    df = df.merge(lifetimes, on=cols, how="left")
    if run_tests:
        check_missing_lifetimes(df)
    return df


def check_missing_efficiencies(df: pd.DataFrame, cols=["Technology", "Fuel"]) -> None:
    """Log warning for technologies missing efficiency data."""
    missing_eff = df[df["Efficiency"].isna()][cols].drop_duplicates()
    if not missing_eff.empty:
        logger.warning("Technologies with missing efficiency:")
        for _, row in missing_eff.iterrows():
            logger.warning("    %s", " | ".join(str(f"'{row[c]}'") for c in cols))


def add_efficiencies(
    df: pd.DataFrame, eff_data: pd.DataFrame, run_tests: bool = RUN_TESTS
) -> pd.DataFrame:
    """Merge efficiency data per fuel and technology into main DataFrame."""
    eff_data = eff_data[["Technology", "Fuel", "Efficiency"]]
    df = df.merge(eff_data, on=["Technology", "Fuel"], how="left")
    if run_tests:
        check_missing_efficiencies(df)
    df["Efficiency"] = df["Efficiency"].fillna(1)
    return df


def check_missing_capex(df: pd.DataFrame, cols=["Technology", "Fuel"]) -> None:
    """Log warning for technologies missing capital cost data."""
    missing_capex = df[df["CAPEX"].isna()][cols].drop_duplicates()
    if not missing_capex.empty:
        logger.warning("Processes with missing capital cost:")
        for _, row in missing_capex.iterrows():
            logger.warning("    %s", " | ".join(str(f"'{row[c]}'") for c in cols))


def add_capex(
    df: pd.DataFrame,
    capex_data: pd.DataFrame,
    cols=["Technology", "Fuel"],
    run_tests: bool = RUN_TESTS,
) -> pd.DataFrame:
    """Merge and deflate capital costs into main DataFrame."""
    capex_data = capex_data[cols + ["PriceBaseYear", "CAPEX"]]
    capex_data = deflate_data(
        capex_data, base_year=BASE_YEAR, variables_to_deflate=["CAPEX"]
    )
    df = df.merge(capex_data, on=cols, how="left")
    if run_tests:
        check_missing_capex(df, cols=cols)
    return df


def add_opex(
    df: pd.DataFrame,
    opex_data: pd.DataFrame,
    cols=["Technology", "Fuel"],
    run_tests: bool = RUN_TESTS,
) -> pd.DataFrame:
    """Merge and deflate capital costs into main DataFrame."""
    opex_data = opex_data[cols + ["PriceBaseYear", "OPEX"]]
    opex_data = deflate_data(
        opex_data, base_year=BASE_YEAR, variables_to_deflate=["OPEX"]
    )
    # drop the price base year variable. Should possible do this anyway?
    opex_data = opex_data.drop(columns="PriceBaseYear")
    df = df.merge(opex_data, on=cols, how="left")

    return df


def add_afa(df: pd.DataFrame, afa_data: pd.DataFrame) -> pd.DataFrame:
    """Merge Annual Full Availability (AFA) data into main DataFrame."""

    if "Sector" in afa_data.columns and "Technology" in afa_data.columns:
        keys = ["Sector", "EndUse", "Technology"]
    else:
        keys = ["EndUse"]

    afa_subset = afa_data[keys + ["AFA"]].drop_duplicates(subset=keys)
    return df.merge(afa_subset, on=keys, how="left")


def estimate_capacity(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate process capacity from energy input, efficiency, and AFA."""
    df["InputEnergy"] = df["Value"]
    df["OutputEnergy"] = df["InputEnergy"] * df["Efficiency"]
    df["Capacity"] = df["OutputEnergy"] / CAP2ACT / df["AFA"]
    return df
